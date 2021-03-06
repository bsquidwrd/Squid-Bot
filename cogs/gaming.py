import os
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from .utils import checks

import web.wsgi
from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils import timezone
from gaming.models import DiscordUser, Game, GameUser, Server, ServerUser, Role, GameSearch, Channel, Task, Log, ChannelUser
from gaming.utils import logify_exception_info, logify_object, paginate


class Gaming:
    """
    The base of everything this bot project is made for
    """
    def __init__(self, bot):
        self.bot = bot

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
            if not isinstance(games, dict):
                tmp_games = Game.objects.filter(pk__in=[g.pk for g in games])
                games = self.map_games(tmp_games)
            if len(games) == 0:
                games = self.map_games(Game.objects.all())

            formatted_message = ''
            if available:
                formatted_message += '\n**Available games**\n'
            for i in games:
                game = games[i]
                if game is None:
                    continue
                if isinstance(game, GameSearch):
                    game = Game.objects.get(pk=game.pk)
                current_searches = self.get_game_searches(game=game)
                formatted_message += '{0}: `{1.name}` {2} people searching\n'.format(i, game, current_searches.count())
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[page]

    async def game_user_beautify(self, game, server, user, reserve=0, page=0):
        """
        Return a message of all users who play a specific game ready for displaying all pretty like
        """
        formatted_message = '**It doesn\'t look like anyone has played `{0.name}`, be one of the first by starting to play now!**'.format(game)
        try:
            user_pks = [s.user.pk for s in ServerUser.objects.filter(server=server)]
            game_users = GameUser.objects.filter(game=game, user__pk__in=user_pks).exclude(user=user)
            if game_users.count() >= 1:
                formatted_message = 'The following people have played `{1.name}`:\n```'.format(game_users.count(), game)
                for gu in game_users:
                    u = gu.user
                    formatted_message += '\n{0}'.format(u.name)
                formatted_message += '```'
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[page]

    def get_server(self, server):
        """
        Returns a :class:`gaming.models.Server` object after getting or creating the server
        """
        return Server.objects.get(server_id=server.id)

    def get_user(self, member):
        """
        Returns a :class:`gaming.models.DiscordUser` object after getting or creating the user
        Does not create users for Bots
        """
        return DiscordUser.objects.get(user_id=member.id)

    def get_server_user(self, user, server):
        return ServerUser.objects.get(user=user, server=server)

    def create_game_search(self, user, game):
        """ Create a GameSearch object for a user if one does not exist or isn't active """
        created = False
        game_searches = self.get_game_searches(user=user, game=game)
        if game_searches.count() >= 1:
            game_search = game_searches[0]
        else:
            game_search = GameSearch.objects.create(user=user, game=game)
            created = True
        return (game_search, created)

    def get_game_searches(self, user=None, game=None, server=None):
        """
        Get :class:`gaming.models.GameSearch` for the specified user and/or game. If none provided, return all
        """
        game_searches = GameSearch.objects.filter(cancelled=False, game_found=False, expire_date__gte=timezone.now())
        if isinstance(user, DiscordUser):
            game_searches = game_searches.filter(user=user)
        if isinstance(game, Game):
            game_searches = game_searches.filter(game=game)
        if isinstance(server, Server):
            server_users = ServerUser.objects.filter(server=server)
            user_ids = [u.user.pk for u in server_users]
            game_searches = game_searches.filter(user__pk__in=user_ids)
        return game_searches.order_by('created_date')

    def order_games(self, games):
        """ Takes a QuerySet of Game """
        if isinstance(games, list):
            games = Game.objects.filter(pk__in=[g.pk for g in games])
        # Order the games by the number of players who play it
        return games.annotate(user_count=Count('gameuser')).filter(user_count__gte=3).order_by('-user_count')

    def map_games(self, games):
        """ Maps games to a number from highest played to lowest played """
        games = self.order_games(games)
        game_map = {}
        for i, game in enumerate(games):
            game_map[i+1] = game
        return game_map

    def get_game_channels(game):
        if not isinstance(game, Game):
            return False
        return Channel.objects.annotate(num_users=Count('channeluser')).filter(
            game=game,
            private=False,
            game_channel=True,
            deleted=False,
            expire_date__gte=timezone.now(),
            num_users__lte=4
        ).order_by('-expire_date', '-num_users')

    async def create_game_channel(self, ctx, game, searches=None):
        """
        Creates/Gets a :class:`gaming.models.Channel` for the selected :class:`gaming.models.Game`

        Returns an instance of :class:`gaming.models.Channel`
        """
        server = ctx.message.server
        mserver = Server.objects.get(server_id=server.id)

        if searches is None:
            searches = self.get_game_searches(game=game)[:5]

        everyone = discord.PermissionOverwrite(read_messages=False, send_messages=False)
        user_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await self.bot.create_channel(server, game.name, (server.default_role, everyone), (server.me, user_perms))
        mchannel = Channel.objects.create(server=mserver, channel_id=channel.id, name=channel.name, expire_date=(timezone.now() + timedelta(minutes=15)))

        for search in searches:
            await self.bot.edit_channel_permissions(channel, channel.server.get_member(search.user.user_id), user_perms)
            search.game_found = True
            search.save()
        time_to_delete = mchannel.expire_date.strftime("%Y-%m-%d %H:%M")
        msg = await self.bot.send_message(channel, "This channel will be deleted at {} UTC ({} minutes from creation.)".format(time_to_delete, 15))
        await self.bot.pin_message(msg)
        return mchannel

    # Events
    async def on_ready(self):
        """
        Bot is loaded, do stuff that needs to be done
        """
        pass

    async def on_member_join(self, member):
        """
        A new member has joined
        """
        pass

    async def on_member_remove(self, member):
        """
        A member has been kicked/banned or has left a server
        """
        pass

    async def on_member_update(self, before, after):
        """
        A member has been updated somehow
        """
        pass
    # End Events

    # Commands
    @commands.command(name='games', pass_context=True)
    async def list_games(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """Get a list of all the games
        Example: ?games over p2"""
        server = self.get_server(self.get_server(ctx.message.server))
        user = self.get_user(self.get_user(ctx.message.author))
        if not user or user.bot:
            return

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
        games = self.map_games(games)
        message_to_send = '{}\n'.format(await self.game_beautify(games, page=page))
        await self.bot.say(message_to_send, delete_after=30)
        await self.bot.delete_message(ctx.message)

    @checks.is_owner()
    @commands.command(name='lfg', pass_context=True)
    async def looking_for_game(self, ctx, game_search_key: str = None, page_number: str = None):
        """Used when users want to play a game with others
        Example: ?lfg overwatch"""
        user = self.get_user(ctx.message.author)
        games = [game for game in Game.objects.all()]
        server = self.get_server(ctx.message.server)

        log_item = Log.objects.create(message="Log item for {} on {} searching for {}".format(user, server, game_search_key))

        if not user or user.bot:
            return

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        game_search = False
        created = False
        create_search = False

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
        else:
            games = self.map_games(games)
            msg = False
            temp_message = '{0.message.author.mention}: Which game did you want to search for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
            formatted_games = await self.game_beautify(games, reserve=len(temp_message), page=page)
            final_message = '{}{}'.format(temp_message, formatted_games)
            question_message = await self.bot.say(final_message)
            time_ran_out = False
            gameIDs = games.keys()
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
                        possible_game = Game.objects.filter(pk=games[int(content)].pk)
                    except:
                        possible_game = Game.objects.filter(name__icontains=content)
                    if possible_game.count() == 1:
                        game = possible_game[0]
                except Exception as e:
                    log_item.message += '- Failed\n\n{}'.format(logify_exception_info())
                await self.bot.delete_message(msg)
            else:
                time_ran_out = True
            await self.bot.delete_message(question_message)

        if isinstance(game, Game):
            """
            .. todo:: Ask the user if they want to join a currently (non-full) game group
            or if they want to start their own search
            Somehow limit the number of people per group to 5 (or some other good number)
            """
            current_searches = self.get_game_searches(game=game)
            current_game_channels = self.get_game_channels(game=game)
            game_channel = None

            for channel in current_game_channels:
                c = await self.bot.get_channel(channel.channel_id)
                if c is None:
                    channel.deleted = True
                    channel.save()
                    continue
                if channel.num_users > 5:
                    continue
                else:
                    game_channel = channel
                    break

            if current_searches.count() == 0:
                create_search = True
            else:
                msg = False
                temp_message = '{0.message.author.mention}: There is a group with less than 5 people for {1.name}, would you like to join them?\n_Please only type in `yes` or `no`_\n_You have 30 seconds to respond_\n'.format(ctx, game)
                question_message = await self.bot.say(temp_message)
                time_ran_out = False
                def yesno_check(msg):
                    try:
                        return msg.content.strip().lower() in ['yes', 'no']
                    except:
                        return False
                msg = await self.bot.wait_for_message(author=ctx.message.author, check=yesno_check, timeout=30)
                if isinstance(msg, discord.Message):
                    try:
                        log_item.message += "Response from user about joining existing group: '{}'\n".format(message.content)
                        content = msg.content.strip().lower()
                        if content == 'yes':
                            # Put the user with the group already found
                            pass
                        elif content == 'no':
                            # They said no, so start a new search
                            create_search = True
                        else:
                            raise Exception("Content is not equal to yes/no")
                    except Exception as e:
                        log_item.message += '- Failed\n\n{}'.format(logify_exception_info())
                    await self.bot.delete_message(msg)
                else:
                    time_ran_out = True
                await self.bot.delete_message(question_message)

        if create_search:
            game_search, created = self.create_game_search(user, game)
        log_item.message += "game_search: {0}\ncreated: {1}\ngame_found: {2}\ntime_ran_out: {3}\ncreate_search: {4}\n".format(game_search, created, game_found, time_ran_out, create_search)
        log_item.save()

        if created and game_search:
            await self.bot.say("{0.message.author.mention}: You've been added to the search queue for `{1.name}`!".format(ctx, game), delete_after=30)
        elif game_found:
            await self.bot.say("{0.message.author.mention}: You've been added to the current group `{1.name}`!".format(ctx, game), delete_after=30)
        elif game_search:
            await self.bot.say("{0.message.author.mention}: You're already in the queue for `{1.name}`. If you would like to stop looking for this game, type {0.prefix}lfgstop {1.name}".format(ctx, gaame), delete_after=30)
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out `{0.message.author.mention}`. Please re-run the command and try again.'.format(ctx), delete_after=30)
        else:
            await self.bot.say("{0.message.author.mention}: I didn't quite understand your response, please run the command again.".format(ctx), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='lfgstop', pass_context=True)
    async def looking_for_game_remove(self, ctx, *, game_search_key: str = None, page_number: str = None):
        """
        Stop searching for a game
        """
        user = self.get_user(ctx.message.author)
        server = self.get_server(ctx.message.server)
        games_removed = []

        log_item = Log.objects.create(message="Log item for {} on {} trying to stop searching for {}".format(user, server, game_search_key))

        if not user or user.bot:
            return

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        game_search_cancelled = False
        time_ran_out = False
        no_game_searches = False

        if game_search_key:
            games = Game.objects.filter(name__icontains=game_search_key)
        else:
            game_pks = []
            for search in self.get_game_searches(user=user):
                game_pks.append(search.game.pk)
            games = Game.objects.filter(pk__in=game_pks)
        game_removed = 'All Games'
        games = self.order_games(games)

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
                games = self.map_games(games)
                temp_message = '{0.message.author.mention}: Which game would you like to stop searching for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
                formatted_games = await self.game_beautify(games, page=page)
                final_message = '{}{}'.format(temp_message, formatted_games)
                question_message = await self.bot.say(final_message)
                gameIDs = games.keys()
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
                            possible_game = Game.objects.filter(pk=games[int(content)].pk)
                        except:
                            possible_game = Game.objects.filter(name__icontains=game_pk)
                        if possible_game.count() == 1:
                            game = possible_game[0]
                            game_searches = self.get_game_searches(user=user, game=game)
                            game_searches.update(cancelled=True)
                            games_removed = [game]
                            game_search_cancelled = True
                    except Exception as e:
                        log_item.message += '- Failed\n\n{}'.format(logify_exception_info())
                    await self.bot.delete_message(msg)
                await self.bot.delete_message(question_message)
            else:
                no_game_searches = True
        log_item.save()

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
        """
        See who has played a certain game in the past
        """
        user = self.get_user(ctx.message.author)
        server = self.get_server(ctx.message.server)
        games = Game.objects.all()

        log_item = Log.objects.create(message="Log item for {} on {} searching for {}".format(user, server, game_search_key))

        if not user or user.bot:
            return

        time_ran_out = False
        game = False

        page = 0
        if page_number:
            if page_number.lower().startswith('p'):
                page = int(page_number[1::]) - 1

        if game_search_key:
            current_searches = self.get_game_searches(user=user, server=server)
            current_searches_games = [search.game for search in current_searches]
            try:
                possible_games = Game.objects.filter(pk=int(game_search_key))
            except:
                possible_games = Game.objects.filter(name__icontains=game_search_key)
            games = possible_games
        games = self.map_games(games)
        if len(games) == 1:
            game = games[1]
            game_search, created = self.create_game_search(user, game)
        else:
            msg = False
            temp_message = '{0.message.author.mention}: Which game did you want to search for?\n_Please only type in the number next to the game_\n_You have 30 seconds to respond_\n'.format(ctx)
            formatted_games = await self.game_beautify(games, reserve=len(temp_message), page=page)
            final_message = '{}{}'.format(temp_message, formatted_games)
            question_message = await self.bot.say(final_message)
            gameIDs = games.keys()
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
                        possible_game = Game.objects.filter(pk=games[int(content)].pk)
                    except:
                        possible_game = Game.objects.filter(name__icontains=content)
                    if possible_game.count() == 1:
                        game = possible_game[0]
                except Exception as e:
                    log_item.message += '- Failed\n\n{}'.format(logify_exception_info())
                await self.bot.delete_message(msg)
            else:
                time_ran_out = True
            await self.bot.delete_message(question_message)
        log_item.save()

        if game:
            temp_message = '{0.message.author.mention}\n'.format(ctx)
            await self.bot.say('{}{}'.format(temp_message, await self.game_user_beautify(game, server, user, reserve=len(temp_message), page=page)), delete_after=30)
        elif time_ran_out:
            await self.bot.say('Whoops... looks like your time ran out {0.message.author.mention}. Please re-run the command and try again.'.format(ctx), delete_after=30)
        else:
            await self.bot.say("{0.message.author.mention}: I didn't quite understand your response, please run the command again.".format(ctx), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='lfgpurge', pass_context=True, hidden=True)
    @checks.is_owner()
    async def looking_for_game_purge(self, ctx, *args):
        """
        Cancel all current :class:`gaming.models.GameSearch`
        """
        game_searches = self.get_game_searches()
        question_message = await self.bot.say('\n**Are you sure you want to cancel all active game searches?**\nActive Searches: `{}`.'.format(game_searches.count()))
        def check(msg):
            try:
                return msg.content.strip().lower() == "yes"
            except:
                return False
        msg = False
        msg = await self.bot.wait_for_message(author=ctx.message.author, check=check, timeout=15)
        if isinstance(msg, discord.Message):
            game_searches.update(cancelled=True)
            for server in self.bot.servers:
                cancelled_message = '**All active Searches have been cancelled by {} at {}**'.format(ctx.message.author.name, timezone.now().strftime("%Y-%m-%d %H:%M"))
                cmsg = await self.bot.send_message(server.default_channel, cancelled_message)
            await self.bot.delete_message(msg)
        await self.bot.delete_message(question_message)
        await self.bot.delete_message(ctx.message)

    @commands.command(name='halp', pass_context=True, hidden=True)
    @checks.is_owner()
    async def halp_command(self, ctx, *args):
        """
        Halp is my testing command
        """
        await self.bot.say("Halp requested!")
    # End Commands

    # Errors
    @looking_for_game.error
    async def looking_for_game_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Gaming(bot))
