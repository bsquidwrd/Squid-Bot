import os
from discord.ext import commands
from discord.ext.commands import Bot
from datetime import datetime
import discord
from .utils import checks
from .utils.data import Data

import web.wsgi
from django.utils import timezone
from django.db import models
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch

DISCORD_MSG_CHAR_LIMIT = 2000

def paginate(content, *, length=DISCORD_MSG_CHAR_LIMIT, reserve=0):
    """
    Split up a large string or list of strings into chunks for sending to discord.
    """
    if type(content) == str:
        contentlist = content.split('\n')
    elif type(content) == list:
        contentlist = content
    else:
        raise ValueError("Content must be str or list, not %s" % type(content))

    chunks = []
    currentchunk = ''

    for line in contentlist:
        if len(currentchunk) + len(line) < length - reserve:
            currentchunk += line + '\n'
        else:
            chunks.append(currentchunk)
            currentchunk = ''

    if currentchunk:
        chunks.append(currentchunk)

    return chunks

class GamingUtils:
    def __init__(self):
        pass

    async def game_beautify(self, games, reserve=0):
        """
        Return a message of all games ready for displaying all pretty like
        """
        formatted_message = '**No games are currently in the database!\nStart playing some games to make the database better**'
        try:
            if len(games) == 0:
                games = Game.objects.all()

            formatted_message = '\n**Available games**\n'
            for game in games:
                if isinstance(game, GameSearch):
                    game = Game.objects.get(pk=game.pk)
                formatted_message += '`{0}:` {1}\n'.format(game.pk, game.name)
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[0]


    ####################
    # Search Utilities #
    ####################
    async def search_beautify(self, user, game, reserve=0):
        """
        Return a message of all user searches ready for displaying all pretty like
        """
        # Todo: How to filter all users and games people are searching based on params passed in
        if users:
            users = await self.search_user(users)
        elif games:
            if len(game) > 1:
                active_searches = GameSearch.objects.filter(cancelled=False, expire_date__gte=timezone.now())
                users = active_searches.filter(game__in=[game.pk])
            else:
                users = active_searches.filter(game=game, cancelled=False, expire_date__gte=timezone.now())

        if formatted is False:
            return users

        if len(users) >= 1:
            formatted_message = '' #'**The following users are looking for games:**\n'
            for user in users:
                formatted_message += '{}\n'.format(user.name)
        else:
            formatted_message = '**There are currently no users looking for games**'
        return paginate(formatted_message, reserve=reserve)[0]


class Gaming(GamingUtils):
    def __init__(self, bot):
        self.bot = bot
        for server in self.bot.servers:
            Server.objects.get_or_create(server_id=server.id, defaults={'name': server.name})
            for user in server.members:
                DiscordUser.objects.get_or_create(user_id=user.id, defaults={'name': user.name})
        super().__init__()

    def __unload(self):
        """Called when the cog is unloaded"""
        pass

    # Class methods
    def create_user(self, member):
        return DiscordUser.objects.get_or_create(user_id=member.id, defaults={'name': member.name})

    def create_game_search(self, user, game):
        created = False
        game_searches = GameSearch.objects.filter(user=user, game=game, expire_date__gte=timezone.now(), cancelled=False)
        if game_searches.count() >= 1:
            game_search = game_searches[0]
        else:
            game_search = GameSearch.objects.create(user=user, game=game)
            created = True
        return (game_search, created)

    # Events
    async def on_member_join(self, member):
        self.create_user(member)

    async def on_member_remove(self, member):
        GameSearch.objects.filter(user=user, cancelled=False, expire_date__gte=timezone.now()).update(cancelled=True)

    async def on_member_update(self, before, after):
        """This is to populate games and users automatically"""
        user, created = self.create_user(after)
        if before.game:
            member = before
        else:
            member = after
        game = member.game
        possible_games = Game.objects.filter(name=game.name.strip())
        if possible_games.count() == 0:
            game = Game.objects.create(name=game.name.strip(), url=game.url)
            GameUser.objects.get_or_create(user=user, game=game)
        elif possible_games.count() == 1:
            game = possible_games[0]
            GameUser.objects.get_or_create(user=user, game=game, defaults={'user': user, 'game': game})
    # End Events

    # Commands
    @commands.command(name='games', pass_context=True)
    async def list_games(self, ctx, *, game_search_key: str = None):
        """Get a list of all the games"""
        if game_search_key:
            try:
                game_search_key = int(game_search_key)
                games = Game.objects.get(pk=game_search_key)
            except:
                games = Game.objects.filter(name__icontains=game_search_key)
        else:
            games = Game.objects.all()
        want_to_play_message = 'Want to play a game with people? Type `{}lfg <game_number OR game_name>` to start looking.'.format(ctx.prefix)
        message_to_send = '{}'.format(await self.game_beautify(games))
        if len(games) >= 1:
            message_to_send += '{}'.format(want_to_play_message)
        await self.bot.say(message_to_send)

    @commands.command(name='lfg', pass_context=True)
    async def looking_for_game(self, ctx, *, game_search_key: str = None):
        """Used when users want to play a game with others"""
        user = self.create_user(ctx.message.author)[0]
        games = [game for game in Game.objects.all()]

        game_search = False
        created = False

        if game_search_key:
            current_searches = GameSearch.objects.filter(user=user, cancelled=False, expire_date__gte=timezone.now())
            current_searches_games = [search.game for search in current_searches]
            games = []
            try:
                possible_games = Game.objects.filter(pk=int(game_search_key))
            except:
                possible_games = Game.objects.filter(name__icontains=game_search_key)
            for game in possible_games:
                if game not in current_searches_games:
                    if game not in games:
                        games.append(game)
        if len(games) == 1:
            game = games[0]
            game_search, created = self.create_game_search(user, game)
        else:
            msg = False
            temp_message = 'Which game did you want to search for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'
            formatted_games = await self.game_beautify(games, reserve=len(temp_message))
            final_message = '{}{}'.format(temp_message, formatted_games)
            await self.bot.say(final_message, delete_after=30)
            time_ran_out = False
            gameIDs = [game.pk for game in games]
            def check(msg):
                try:
                    return int(msg.content.strip()) in gameIDs
                except:
                    return False
            msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
            if msg:
                try:
                    content = msg.content.strip()
                    try:
                        game_pk = int(content)
                        possible_game = Game.objects.filter(pk=game_pk)
                    except:
                        possible_game = Game.objects.filter(name__icontains=content)
                    if possible_game.count() == 1:
                        game = possible_game[0]
                        game_search, created = self.create_game_search(user, game)
                except Exception as e:
                    print(e)

        if created and game_search:
            await self.bot.say("You've been added to the search queue for `{0.name}`!".format(game))
        elif game_search:
            await self.bot.say("You're already in the queue for `{0.name}`. If you would like to stop looking for this game, type {1.prefix}lfgstop {0.pk}".format(game, ctx))
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out `{}`. Please re-run the command and try again.'.format(ctx.message.author.mention), delete_after=30)
        else:
            await self.bot.say("I didn't quite understand your response, please run the command again.")

    @commands.command(name='lfgstop', pass_context=True)
    async def looking_for_game_remove(self, ctx, *, game_search_key: str = None):
        """Starts searching for a game to play with others"""
        user = self.create_user(ctx.message.author)[0]
        games_removed = []

        game_search_cancelled = False
        time_ran_out = False
        no_game_searches = False

        if game_search_key:
            try:
                games = Game.objects.filter(pk=int(game_search_key))
            except:
                games = Game.objects.filter(name__icontains=game_search_key)
        else:
            game_pks = []
            for search in GameSearch.objects.filter(user=user, cancelled=False, expire_date__gte=timezone.now()):
                game_pks.append(search.game.pk)
            games = Game.objects.filter(pk__in=game_pks)
        game_removed = 'All Games'

        if games.count() == 1:
            game = games[0]
            game_search = GameSearch.objects.filter(user=user, game=game, cancelled=False, expire_date__gte=timezone.now())
            games_removed = [search.game for search in game_search]
            game_search.update(cancelled=True)
            game_search_cancelled = True
        else:
            game_searches = GameSearch.objects.filter(user=user, cancelled=False, expire_date__gte=timezone.now())
            games = []
            for game in game_searches:
                if game.game not in games:
                    games.append(game.game)
            if len(games) >= 1:
                temp_message = 'Which game would you like to stop searching for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'
                formatted_games = await self.game_beautify(games)
                final_message = '{}{}'.format(temp_message, formatted_games)
                await self.bot.say(final_message, delete_after=30)
                gameIDs = [game.pk for game in games]
                def check(msg):
                    try:
                        return int(msg.content.strip()) in gameIDs
                    except:
                        return False
                msg = False
                msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
                if msg:
                    try:
                        content = msg.content.strip()
                        try:
                            game_pk = int(content)
                            possible_game = Game.objects.filter(pk=game_pk)
                        except:
                            possible_game = Game.objects.filter(name__icontains=game_pk)
                        if possible_game.count() == 1:
                            game = possible_game[0]
                            game_searches = GameSearch.objects.filter(user=user, game=game, cancelled=False, expire_date__gte=timezone.now())
                            game_searches.update(cancelled=True)
                            games_removed = [game]
                            game_search_cancelled = True
                    except Exception as e:
                        print(e)
            else:
                no_game_searches = True

        if game_search_cancelled:
            await self.bot.say("You've stopped searching for the following game(s):\n{}".format(await self.game_beautify(games))
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out {}. Please re-run the command and try again.'.format(ctx.message.author.mention), delete_after=30)
        elif no_game_searches:
            await self.bot.say('It doesn\t look like you\'re currently searching for any games.\nIf you would like to start, type {0.prefix}lfg'.format(ctx))
        else:
            await self.bot.say("I didn't quite understand your response, please run the command again.")

    @commands.command(name='lfgpurge', pass_context=True, hidden=True)
    @checks.is_owner()
    async def looking_for_game_purge(self, ctx, *args):
        game_searches = GameSearch.objects.filter(cancelled=False, expire_date__gte=timezone.now())
        await self.bot.say('\n**Are you sure you want to cancel all active game searches?**\n```There are currently `{}` active searches.```'.format(game_searches.count()), delete_after=30)
        def check(msg):
            try:
                return msg.content.strip().lower() == "yes"
            except:
                return False
        msg = False
        msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
        if msg:
            game_searches.update(cancelled=True)
            for server in self.bot.servers:
                cancelled_message = ':exclamation: **All active Searches have been cancelled by {} at {}**'.format(ctx.message.author.name, timezone.now())
                await self.bot.send_message(server.default_channel, cancelled_message)

    @commands.command(name='halp', pass_context=True, hidden=True)
    @checks.is_owner()
    async def halp_command(self, ctx, *args):
        """
        Halp is my testing command
        """
        print("Rawr")
        await self.bot.say('Please type something that starts with "hello"')
        def check(msg):
            return msg.content.lower().startswith('hello')
        msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
        if msg:
            content = msg.content.strip()
            await self.bot.send_message(msg.channel, 'You said:\n{}'.format(content))
        else:
            await self.bot.say('Whoops... looks like your time ran out {}. Please re-run the command and try again.'.format(ctx.message.author.mention))
    # End Commands

    # Errors
    @looking_for_game.error
    async def looking_for_game_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Gaming(bot))
