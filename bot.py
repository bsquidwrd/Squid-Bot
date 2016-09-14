from discord.ext import commands
import discord
import credentials
from cogs.utils import checks
import datetime, re
import asyncio
import copy
import logging
import traceback
import sys
import os
from collections import Counter


debug_mode = os.getenv('SQUID_BOT_DEBUG_MODE', True)
if not isinstance(debug_mode, bool):
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

github_url = 'https://github.com/bsquidwrd/Squid-Bot'

description = """
Hello! I am a bot written by bsquidwrd with a backbone from Danny.
Find out more on GitHub: {0}
""".format(github_url)

initial_extensions = [
    'cogs.admin',
    'cogs.buttons',
]

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
bot_start_time = datetime.datetime.utcnow()

if debug_mode:
    log_filename = 'squid_bot.log'
else:
    logs_dir = 'logs\{0}\{1}'.format(bot_start_time.strftime('%Y'), bot_start_time.strftime('%m'))
    if not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)
    log_filename = '{0}\squid_bot.{1}.log'.format(logs_dir, bot_start_time.strftime('%Y-%m-%d.%H-%M-%S'))

handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
log.addHandler(handler)

help_attrs = dict(hidden=True)

prefix = ['?', '!', '\N{HEAVY EXCLAMATION MARK SYMBOL}']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('Debug: ' + str(debug_mode))
    print('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\nDebug: {1}\n------'.format(bot, str(debug_mode)))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time
    squid_bot_game = discord.Game(name=bot.user.name, url=github_url, type=0)
    await bot.change_status(game=squid_bot_game, idle=False)


@bot.event
async def on_resumed():
    print('resumed...')


@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)

    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)


@bot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def do(ctx, times : int, *, command):
    """Repeats a command a specified number of times."""
    msg = copy.copy(ctx.message)
    msg.content = command
    for i in range(times):
        await bot.process_commands(msg)


@bot.command()
async def changelog():
    """Gives a URL to the current bot changelog."""
    await bot.say(github_url)


@bot.command(hidden=True)
@checks.is_owner()
async def restart():
    """Restarts the bot"""
    await bot.say(':wave:')
    await bot.close()


def load_credentials():
    return credentials.load_credentials()


if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    credentials = load_credentials()
    bot.client_id = credentials['client_id']
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    bot.run(credentials['token'])
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
