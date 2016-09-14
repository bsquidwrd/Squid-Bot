from discord.ext import commands
from discord.ext.commands import Bot
from datetime import datetime
import discord
from .utils import checks
from .utils.data import Data


class Gaming:
    """Gaming functions like looking for a game etc."""

    def __init__(self, bot):
        self.bot = bot
        self.data = Data('gaming.db')
        from .utils.gaming_utils import GamingUtils
        self.utils = GamingUtils(bot=bot, gaming=self)

    def __unload(self):
        """Called when the cog is unloaded. Makes sure data is saved correctly"""
        self.data.close_connection()

    # Events
    async def on_member_join(self, member):
        await self.utils.user_add(member)

    async def on_member_remove(self, member):
        await self.utils.user_remove(member)

    async def on_member_update(self, before, after):
        if before.game:
            member = before
        else:
            member = after
        if member.game:
            await self.utils.game_add(member.game)
    # End Events

    # Commands
    @commands.command(name='games', pass_context=True)
    async def list_games(self, ctx, *, game_search_key: str = None):
        """Get a list of all the games"""
        if game_search_key:
            try:
                game_search_key = int(game_search_key)
                games = await self.utils.game_find_by_id(game_search_key)
            except:
                games = await self.utils.game_find_by_name(game_search_key)
        else:
            games = await self.utils.game_get_all()
        want_to_play_message = 'Want to play a game with people? Type `{}lfg <game number>` to start looking.'.format(ctx.prefix)
        message_to_send = '{}\n'.format(await self.utils.game_beautify(games))
        if len(games) >= 1:
            message_to_send += '\n{}'.format(want_to_play_message)
        await self.bot.say(message_to_send)

    @commands.command(name='lfg', pass_context=True)
    async def looking_for_game(self, ctx, *, game_search_key: str = None):
        """Used when users want to play a game with others"""
        games = []
        if game_search_key:
            try:
                game_search_key = int(game_search_key)
                games = await self.utils.game_find_by_id(game_search_key)
            except:
                games = await self.utils.game_find_by_name(game_search_key)
        if len(games) == 1:
            game = games[0]
            if await self.utils.search_user_add(ctx.message.author, game):
                await self.bot.say("You've been added to the search queue for {}!".format(game['name']))
        elif len(games) > 1:
            pass
        else:
            formatted_message = 'People looking for games:\n'
            for user in await self.utils.user_get_all():
                formatted_message += '{}:\n'.format(user['name'])
                for item in user:
                    if item == 'name':
                        continue
                    formatted_message += '    {}: {}\n'.format(item, user[item])
            await self.bot.say(formatted_message)

    @commands.command(name='lfgremove', pass_context=True)
    async def looking_for_game_remove(self, ctx, *, gameID: int = None):
        """Used when users want to stop looking for a game"""
        await self.utils.user_remove(ctx.message.author)
        await self.bot.say('You have been removed from the queue for the game')

    @commands.command(name='lfgpurge', pass_context=True, hidden=True)
    @checks.admin_or_permissions()
    async def looking_for_game_purge(self, ctx, *args):
        channel = ctx.message.channel
        await self.reset_users()
        await self.bot.say(':exclamation: **Users have been purged**')
    # End Commands

    # Errors
    @looking_for_game.error
    async def looking_for_game_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Gaming(bot))
