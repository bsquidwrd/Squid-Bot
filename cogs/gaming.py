import os
import asyncio
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

class Gaming:
    def __init__(self, bot):
        self.bot = bot
        self.populate_info()
        super().__init__()

    def __unload(self):
        """Called when the cog is unloaded"""
        pass

    # Class methods
    async def game_beautify(self, games, reserve=0, page=0, available=True):
        """
        Return a message of all games ready for displaying all pretty like
        """
        formatted_message = '**No games are currently in the database!\nStart playing some games to make the database better**'
        try:
            if len(games) == 0:
                games = Game.objects.all()

            formatted_message = ''
            if available:
                formatted_message += '\n**Available games**\n'
            for game in games:
                if isinstance(game, GameSearch):
                    game = Game.objects.get(pk=game.pk)
                current_searches = self.get_game_searches(game=game)
                formatted_message += '{0.pk}: `{0.name}` {1} people searching\n'.format(game, current_searches.count())
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[page]

    async def game_user_beautify(self, game, user, reserve=0, page=0):
        """
        Return a message of all users who play a specific game ready for displaying all pretty like
        """
        formatted_message = '**Nobody has played `{0.name}`, be the first by starting to play now!**'.format(game)
        try:
            game_users = GameUser.objects.filter(game=game).exclude(user=user)
            if game_users.count() >= 1:
                formatted_message = 'The following people have played `{1.name}`:\n```'.format(game_users.count(), game)
                for gu in game_users:
                    u = gu.user
                    formatted_message += '\n{0}'.format(u.name)
                formatted_message += '```'
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[page]

    def populate_info(self):
        for server in self.bot.servers:
            Server.objects.get_or_create(server_id=server.id, defaults={'name': server.name})
            for user in server.members:
                DiscordUser.objects.get_or_create(user_id=user.id, defaults={'name': user.name})

    def create_user(self, member):
        # Returns a DiscordUser object after getting or creating the user
        return DiscordUser.objects.get_or_create(user_id=member.id, defaults={'name': member.name})[0]

    def create_game_search(self, user, game):
        created = False
        game_searches = self.get_game_searches(user=user, game=game)
        if game_searches.count() >= 1:
            game_search = game_searches[0]
        else:
            game_search = GameSearch.objects.create(user=user, game=game)
            created = True
        return (game_search, created)

    def get_game_searches(self, user=None, game=None):
        game_searches = GameSearch.objects.filter(cancelled=False, expire_date__gte=timezone.now())
        if isinstance(user, DiscordUser):
            game_searches = game_searches.filter(user=user)
        if isinstance(game, Game):
            game_searches = game_searches.filter(game=game)
        return game_searches.order_by('-pk')

    # Events
    async def on_ready(self):
        self.populate_info()

    async def on_member_join(self, member):
        self.create_user(member)

    async def on_member_remove(self, member):
        pass

    async def on_member_update(self, before, after):
        """This is to populate games and users automatically"""
        user = self.create_user(after)
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
    async def list_games(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """Get a list of all the games
        Example: !games over p2"""
        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        if game_search_key:
            try:
                game_search_key = int(game_search_key)
                games = Game.objects.get(pk=game_search_key)
            except:
                games = Game.objects.filter(name__icontains=game_search_key)
        else:
            games = Game.objects.all()
        want_to_play_message = 'Want to play a game with people? Type `{}help lfg` to learn how to start searching.'.format(ctx.prefix)
        message_to_send = '{}'.format(await self.game_beautify(games, page=page))
        if len(games) >= 1:
            message_to_send += '{}'.format(want_to_play_message)
        await self.bot.say(message_to_send, delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='lfg', pass_context=True)
    async def looking_for_game(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """Used when users want to play a game with others
        Example: !lfg overwatch"""
        user = self.create_user(ctx.message.author)
        games = [game for game in Game.objects.all()]

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        game_search = False
        created = False

        if game_search_key:
            current_searches = self.get_game_searches(user=user)
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
            temp_message = '{0.message.author.mention}: Which game did you want to search for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
            formatted_games = await self.game_beautify(games, reserve=len(temp_message), page=page)
            final_message = '{}{}'.format(temp_message, formatted_games)
            question_message = await self.bot.say(final_message)
            time_ran_out = False
            gameIDs = [game.pk for game in games]
            def check(msg):
                try:
                    return int(msg.content.strip()) in gameIDs
                except:
                    return False
            msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
            if isinstance(msg, discord.Message):
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
                await self.bot.delete_message(msg)
            await self.bot.delete_message(question_message)

        if created and game_search:
            await self.bot.say("{0.message.author.mention}: You've been added to the search queue for `{1.name}`!".format(ctx, game), delete_after=30)
        elif game_search:
            await self.bot.say("{1.message.author.mention}: You're already in the queue for `{0.name}`. If you would like to stop looking for this game, type {1.prefix}lfgstop {0.pk}".format(game, ctx), delete_after=30)
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out `{0.message.author.mention}`. Please re-run the command and try again.'.format(ctx), delete_after=30)
        else:
            await self.bot.say("{0.message.author.mention}: I didn't quite understand your response, please run the command again.".format(ctx), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='lfgstop', pass_context=True)
    async def looking_for_game_remove(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """Stop searching for a game"""
        user = self.create_user(ctx.message.author)
        games_removed = []

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

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
            for search in self.get_game_searches(user=user):
                game_pks.append(search.game.pk)
            games = Game.objects.filter(pk__in=game_pks).order_by('pk')
        game_removed = 'All Games'
        games = games.order_by('pk')

        if games.count() == 1:
            game = games[0]
            game_search = self.get_game_searches(user=user, game=game)
            games_removed = [search.game for search in game_search]
            game_search.update(cancelled=True)
            game_search_cancelled = True
        else:
            game_searches = self.get_game_searches(user=user)
            games = []
            for game in game_searches:
                if game.game not in games:
                    games.append(game.game)
            if len(games) >= 1:
                temp_message = '{0.message.author.mention}: Which game would you like to stop searching for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
                formatted_games = await self.game_beautify(games, page=page)
                final_message = '{}{}'.format(temp_message, formatted_games)
                question_message = await self.bot.say(final_message)
                gameIDs = [game.pk for game in games]
                def check(msg):
                    try:
                        return int(msg.content.strip()) in gameIDs
                    except:
                        return False
                msg = False
                msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
                if isinstance(msg, discord.Message):
                    try:
                        content = msg.content.strip()
                        try:
                            game_pk = int(content)
                            possible_game = Game.objects.filter(pk=game_pk)
                        except:
                            possible_game = Game.objects.filter(name__icontains=game_pk)
                        if possible_game.count() == 1:
                            game = possible_game[0]
                            game_searches = self.get_game_searches(user=user, game=game)
                            game_searches.update(cancelled=True)
                            games_removed = [game]
                            game_search_cancelled = True
                    except Exception as e:
                        print(e)
                    await self.bot.delete_message(msg)
                await self.bot.delete_message(question_message)
            else:
                no_game_searches = True

        if game_search_cancelled:
            await self.bot.say("{0.message.author.mention}: You've stopped searching for the following game(s):\n{1}".format(ctx, await self.game_beautify(games_removed, available=False)), delete_after=30)
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out {0.message.author.mention}. Please re-run the command and try again.'.format(ctx), delete_after=30)
        elif no_game_searches:
            await self.bot.say('It doesn\'t look like you\'re currently searching for any games {0.message.author.mention}.\nIf you would like to start, type {0.prefix}lfg'.format(ctx), delete_after=30)
        else:
            await self.bot.say("I didn't quite understand your response {0.message.author.mention}, please run the command again.".format(ctx), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='whoplays', pass_context=True)
    async def who_plays(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """Used when users want to play a game with others"""
        user = self.create_user(ctx.message.author)
        games = Game.objects.all()

        time_ran_out = False

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        if game_search_key:
            current_searches = self.get_game_searches(user=user)
            current_searches_games = [search.game for search in current_searches]
            try:
                possible_games = Game.objects.filter(pk=int(game_search_key))
            except:
                possible_games = Game.objects.filter(name__icontains=game_search_key)
            games = possible_games
        if games.count() == 1:
            game = games[0]
            game_search, created = self.create_game_search(user, game)
        else:
            msg = False
            temp_message = '{0.message.author.mention}: Which game did you want to search for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
            formatted_games = await self.game_beautify(games, reserve=len(temp_message), page=page)
            final_message = '{}{}'.format(temp_message, formatted_games)
            question_message = await self.bot.say(final_message)
            gameIDs = [game.pk for game in games]
            def check(msg):
                try:
                    return int(msg.content.strip()) in gameIDs
                except:
                    return False
            msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
            if isinstance(msg, discord.Message):
                try:
                    content = msg.content.strip()
                    try:
                        game_pk = int(content)
                        possible_game = Game.objects.filter(pk=game_pk)
                    except:
                        possible_game = Game.objects.filter(name__icontains=content)
                    if possible_game.count() == 1:
                        game = possible_game[0]
                except Exception as e:
                    print(e)
                await self.bot.delete_message(msg)
            else:
                time_ran_out = True
            await self.bot.delete_message(question_message)

        if game:
            temp_message = '{0.message.author.mention}\n'.format(ctx)
            await self.bot.say('{}{}'.format(temp_message, await self.game_user_beautify(game, user, reserve=len(temp_message), page=page)), delete_after=30)
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out {0.message.author.mention}. Please re-run the command and try again.'.format(ctx), delete_after=30)
        else:
            await self.bot.say("{0.message.author.mention}: I didn't quite understand your response, please run the command again.".format(ctx), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='lfgpurge', pass_context=True, hidden=True)
    @checks.is_owner()
    async def looking_for_game_purge(self, ctx, *args):
        game_searches = self.get_game_searches()
        question_message = await self.bot.say('\n**Are you sure you want to cancel all active game searches?**\nActive Searches: `{}`.'.format(game_searches.count()))
        def check(msg):
            try:
                return msg.content.strip().lower() == "yes"
            except:
                return False
        msg = False
        msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=30)
        if isinstance(msg, discord.Message):
            game_searches.update(cancelled=True)
            for server in self.bot.servers:
                cancelled_message = ':exclamation: LFG: **All active Searches have been cancelled by {} at {}**'.format(ctx.message.author.name, timezone.now())
                cmsg = await self.bot.send_message(server.default_channel, cancelled_message, delete_after=30)
            await self.bot.delete_message(msg)
        await self.bot.delete_message(question_message)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='halp', pass_context=True, hidden=True)
    @checks.is_owner()
    async def halp_command(self, ctx, *args):
        """
        Halp is my testing command
        """
        server = ctx.message.server
        everyone = discord.PermissionOverwrite(read_messages=False)
        mine = discord.PermissionOverwrite(read_messages=True)
        channel = await self.bot.create_channel(server, 'secret', (server.default_role, everyone), (server.me, mine))
        minutes_to_wait = 5
        for i in range(0, minutes_to_wait):
            msg = await self.bot.send_message(channel, "This channel has {} minutes to live...".format(minutes_to_wait - (i+1)))
            await asyncio.sleep(60)
            await self.bot.delete_message(msg)
        await self.bot.delete_channel(channel)

    @commands.command(name='purge', pass_context=True, hidden=True)
    async def purge_command(self, ctx, *args):
        """
        Purge 100 chat messages
        """
        if ctx.message.author.id != ctx.message.server.owner.id:
            await self.bot.say("Only the server owner can do that!")
        else:
            try:
                await self.bot.purge_from(ctx.message.channel)
                await self.bot.say('\N{OK HAND SIGN}')
            except Exception as e:
                await self.bot.say('Looks like an error occurred. Please have my owner check the logs.')


    # End Commands

    # Errors
    @looking_for_game.error
    async def looking_for_game_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Gaming(bot))
