from discord.ext import commands
from datetime import datetime
import discord
from .utils import checks
from .utils.config import Config


class Gaming:
    """Gaming functions like looking for a game etc."""


    def __init__(self, bot):
        self.bot = bot
        self.config = Config('gaming.json', loop=bot.loop, load_later=True)


    async def populate_users(self):
        if (self.config.get('users')) is None:
            await self.config.put('users', [])
            return self.config.get('users')


    async def get_users_looking(self, formatted=True):
        users = self.config.get('users')
        if users is None:
            users = await self.populate_users()
        if formatted is False:
            return users

        if len(users) >= 1:
            formatted_message = '**The following users are looking for games:**\n'
            for user in users:
                u = discord.User(id=user)
                formatted_message += '{}\n'.format(u.mention)
        else:
            formatted_message = '**There are currently no users looking for games**'
        return formatted_message


    @commands.command(name='lfg', pass_context=True)
    async def looking_for_game(self, ctx, *, game: str = None):
        """Used when users want to play a game with others"""

        channel = ctx.message.channel

        if game is None:
            await self.bot.send_message(channel, await self.get_users_looking(formatted=True))
        else:
            user = ctx.message.author
            users = self.config.get('users')
            if users is None:
                users = await self.populate_users()

            if not (user.id in users):
                users.append(user.id)
                user = await self.config.put('users', users)
            await self.bot.send_message(channel, "Your request to play `{}` has been noted...".format(game.title()))


    @commands.command(name='lfgpurge', pass_context=True, hidden=True)
    @checks.admin_or_permissions()
    async def looking_for_game_purge(self, ctx, *args):
        channel = ctx.message.channel
        # await self.config.remove('users')
        await self.config.put('users', [])
        await self.bot.send_message(channel, "**Users have been purged**")


    @looking_for_game.error
    async def looking_for_game_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)


def setup(bot):
    bot.add_cog(Gaming(bot))
