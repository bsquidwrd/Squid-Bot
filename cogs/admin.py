from discord.ext import commands
from .utils import checks
import discord
import inspect

import datetime
from collections import Counter
from django.conf import settings
from gaming import utils


def get_current_commit():
    """
    Returns the current version the bot is running
    """
    import os
    import subprocess
    git_dir = "{}/.git".format(settings.BASE_DIR)
    if os.name == 'nt':
        git_dir = "{}\\.git".format(settings.BASE_DIR)
    return subprocess.check_output(["git", "--git-dir={}".format(git_dir), "rev-parse", "--verify", "HEAD", "--short"]).decode("utf-8")


class Admin:
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_owner()
    async def load(self, *, module : str):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(hidden=True)
    @checks.is_owner()
    async def unload(self, *, module : str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(name='reload', hidden=True)
    @checks.is_owner()
    async def _reload(self, *, module : str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code : str):
        """Evaluates code."""
        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'server': ctx.message.server,
            'channel': ctx.message.channel,
            'author': ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await self.bot.say(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await self.bot.say(python.format(result))

    @commands.command(name='purge', pass_context=True, hidden=True)
    async def purge_command(self, ctx, *, messages_to_purge: int = 100):
        """
        Purge up to 100 chat messages
        """
        if ctx.message.author.id != ctx.message.server.owner.id:
            await self.bot.say("Only the server owner can do that!")
        else:
            try:
                await self.bot.purge_from(ctx.message.channel, limit=int(messages_to_purge))
                await self.bot.say('\N{OK HAND SIGN}')
            except Exception as e:
                print(e)
                await self.bot.say('Looks like an error occurred. Please have my owner check the logs.')

    @commands.command(name='version', pass_context=True, hidden=True)
    async def version_command(self, ctx):
        """
        Print the version of the bot currently running
        """
        member = ctx.message.server.get_member(self.bot.user.id)
        current_commit = get_current_commit()
        commit_url = member.game.url + '/commit/' + current_commit
        msg = await self.bot.send_message(ctx.message.channel, 'I am currently running on commit `{}`\n\n{}'.format(current_commit, commit_url))

def setup(bot):
    bot.add_cog(Admin(bot))
