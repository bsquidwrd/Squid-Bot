from discord.ext import commands
from discord.enums import ChannelType
from .utils import checks
import asyncio
import discord

import web.wsgi
from django.utils import timezone
from django.db import models
import pytz
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch, Channel, Task, Log, ChannelUser, ServerUser
from gaming.utils import logify_exception_info, logify_object, current_line


class Tasks:
    """
    Runs misc tasks

    bot : Required[str]
        The bot instance that is currently running

    - Creates a :class:`gaming.models.Channel` object for every Channel in the Server
    - Creates a :class:`gaming.models.Server` object for every Server the bot is a part of
    - Creates a :class:`gaming.models.DiscordUser` object for every User on each Server the bot is a part of
    - Associates a :class:`gaming.models.Channel` with every :class:`gaming.models.DiscordUser` that has access
    - Processes :class:`gaming.models.Task` that are pending
    """
    def __init__(self, bot):
        self.bot = bot
        self.task_runner = bot.loop.create_task(self.run_tasks())

    def __unload(self):
        self.task_runner.cancel()

    def populate_info(self):
        """ Populate all users and servers """
        for server in self.bot.servers:
            s = self.get_server(server)
            for user in server.members:
                u = self.get_user(user)
                self.get_server_user(u, s)

    def get_server(self, server):
        """
        Returns a :class:`gaming.models.Server` object after getting or creating the server
        """
        s, created = Server.objects.get_or_create(server_id=server.id)
        try:
            s.name = server.name
            s.icon = server.icon
            s.owner = self.get_user(server.owner)
            s.save()
            Log.objects.create(message="s: {0}\ncreated: {1}\nname: {0.name}\nicon: {0.icon}\nowner: {0.owner}".format(s, created))
        except Exception as e:
            Log.objects.create(message="Error trying to get Server object for server {}.\n{}".format(s, logify_exception_info()))
        finally:
            s.save()
            return s

    def get_user(self, member):
        """
        Returns a :class:`gaming.models.DiscordUser` object after getting or creating the user
        Does not create users for Bots
        """
        u, created = DiscordUser.objects.get_or_create(user_id=member.id)
        try:
            u.name = member.name
            u.bot = member.bot
            avatar_url = member.avatar_url
            if avatar_url is None or avatar_url == "":
                avatar_url = member.default_avatar_url
            u.avatar_url = avatar_url
            Log.objects.create(message="u: {0}\ncreated: {1}\nname: {0.name}\navatar_url: {0.avatar_url}\nbot: {0.bot}".format(u, created))
        except Exception as e:
            Log.objects.create(message="Error trying to get DiscordUser object for member: {}.\n{}".format(u, logify_exception_info()))
        finally:
            u.save()
            return u

    def get_server_user(self, user, server):
        return ServerUser.objects.get_or_create(user=user, server=server)[0]

    async def on_ready(self):
        """
        Bot is loaaded, populate information that is needed for everything
        """
        self.populate_info()

    async def on_member_join(self, member):
        """
        A new member has joined, make sure there are instance of :class:`gaming.models.Server` and :class:`gaming.models.DiscordUser` for this event
        """
        server = self.get_server(member.server)
        user = self.get_user(member)

    async def on_member_remove(self, member):
        """
        A member has been kicked/banned or has left a server, deleted their instances of :class:`gaming.models.ServerUser`
        """
        server = self.get_server(member.server)
        user = self.get_user(member)
        server_users = ServerUser.objects.filter(user=user, server=server)
        log_item = Log(message="Deleting ServerUser objects for {}\n\n".format(user))
        for server_user in server_users:
            try:
                server_user.delete()
                delete_message = "- Deleted user {} for server {}".format(user, server)
            except Exception as e:
                delete_message = "- Could not delete user {} for server {}\n{}".format(user, server, e)
            log_item.message += "{}\n".format(delete_message)
        log_item.save()

    async def on_member_update(self, before, after):
        """
        This is to populate games and users automatically
        """
        server = self.get_server(after.server)
        user = self.get_user(after)
        server_user = self.get_server_user(user=user, server=server)
        if not user or after.bot:
            return
        if before.game:
            member = before
        else:
            member = after
        game = member.game
        if game is None:
            return
        possible_games = Game.objects.filter(name=game.name.strip())
        if possible_games.count() == 0:
            game = Game.objects.create(name=game.name.strip(), url=game.url)
            GameUser.objects.get_or_create(user=user, game=game)
        elif possible_games.count() == 1:
            game = possible_games[0]
            GameUser.objects.get_or_create(user=user, game=game)

    async def run_tasks(self):
        try:
            while not self.bot.is_closed:
                await self.run_scheduled_tasks()
                await self.prune_channels()
                await self.update_channels()
                await asyncio.sleep(60)
        except asyncio.CancelledError as e:
            pass

    async def prune_channels(self):
        channels = Channel.objects.filter(private=False, game_channel=True, expire_date__lte=timezone.now(), deleted=False)
        if channels.count() >= 1:
            log_item = Log.objects.create(message="Running task to prune channels:\n{}\n\n".format(logify_object(channels)))
            for channel in channels:
                if channel is None:
                    continue
                log_item.message += 'Deleting channel {}\n\n'.format(channel)
                try:
                    c = await self.bot.get_channel(channel.channel_id)
                    if c is not None:
                        try:
                            await self.bot.delete_channel(c)
                            log_item.message += '- Success'
                        except Exception as e:
                            log_item.message += '- Failure\n\n{}{}\n'.format(logify_exception_info(), e)
                except Exception as e:
                    # Channel no longer exists on server
                    log_item.message += '- Failure\n\n{}{}\n'.format(logify_exception_info(), e)
                finally:
                    channel.deleted = True
                    channel.save()
                log_item.message += "\n\n"
                await asyncio.sleep(1)
            log_item.save()
        else:
            # No channels found to be deleted
            pass

    async def update_channels(self):
        for server in Server.objects.all():
            # This will be to populate Channels and Users
            s = self.bot.get_server(server.server_id)
            log_item = Log.objects.create(message="Starting population of channel users for server {}\n\n".format(server))
            try:
                for c in s.channels:
                    if c.is_private or c.type == ChannelType.voice:
                        continue
                    channel, created = Channel.objects.get_or_create(channel_id=c.id, server=server)
                    channel.name = c.name
                    channel.created_date = pytz.timezone('UTC').localize(c.created_at)
                    channel.save()
                channels = Channel.objects.filter(server=server, deleted=False)
                log_item.message += "Found channels:\n{}\n\n".format(logify_object(channels))
                for channel in channels:
                    try:
                        log_item.message += "Running for channel {}\n".format(channel)
                        c = self.bot.get_channel(channel.channel_id)
                        if c.is_default:
                            log_item.message += "- Channel is default channel, skipping...\n"
                            continue
                        if c is None:
                            log_item.message += "- Channel is not found, marking as deleted\n"
                            c.deleted = True
                            c.save()
                            continue
                    except Exception as e:
                        log_item.message += "- Failed:\n{}\n{}\n".format(logify_exception_info(), e)
                    finally:
                        log_item.message += "- Finished channel processing\n\n"
                log_item.message += "\n"
            except Exception as e:
                log_item.message += "- Failed: {}\n{}\n".format(logify_exception_info(), e)
            finally:
                log_item.save()

    async def run_scheduled_tasks(self):
        tasks = Task.objects.filter(cancelled=False, completed=False, expire_date__lte=timezone.now())
        for task in tasks:
            log_item.message += 'Running task for {} at {}\n'.format(task.user, timezone.now())
            if task.task == Task.ADD_TO_GAME_CHAT:
                try:
                    user = DiscordUser.objects.get(pk=task.user.pk)
                    game = Game.objects.get(pk=task.game.pk)
                    channel = Channel.objects.get(pk=task.channel.pk)
                    log_item.message += 'Game: {}\nChannel: {}\nUser: {}\nTask PK: {}\n\n'.format(user, game, channel, task.pk)
                except Game.DoesNotExist as e:
                    log_item.message += '- Error finding game for task.\n{}{}\n'.format(logify_exception_info(), e)
                except Channel.DoesNotExist as e:
                    log_item.message += '- Error finding channel for game {}\n{}{}\n'.format(game, logify_exception_info(), e)
                except Exception as e:
                    log_item.message += '- Unknown error happened\n{}{}\n'.format(logify_exception_info(), e)
            else:
                # Not really a task for some reason
                log_item.message += '- I don\'t recognize the task type \'{}\'...'.format()
            log_item.message += '- Finished processing task\n'
            log_item.save()


def setup(bot):
    bot.add_cog(Tasks(bot))
