from discord.ext import commands
from .utils import checks
from .utils.formats import logify_exception_info, logify_object
import asyncio
import discord

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch, Channel, Task, Log, ChannelUser


class GamingTasks:
    def __init__(self, bot, task):
        self.bot = bot
        self.task = task

    def __unload(self):
        self.task.cancel()

    @asyncio.coroutine
    def run_tasks(bot):
        while True:
            yield from asyncio.sleep(5)
            channels = Channel.objects.filter(private=False, game_channel=True, expire_date__lte=timezone.now(), deleted=False)
            if channels.count() >= 1:
                for channel in channels:
                    if channel is None:
                        continue
                    channel_log = Log(message='Deleting channel {}\n\n'.format(channel))
                    try:
                        c = yield from bot.get_channel(channel.channel_id)
                        if c is not None:
                            try:
                                yield from bot.delete_channel(c)
                                channel_log.message += '- Success'
                            except Exception as e:
                                channel_log.message += '- Failure\n\n{}'.format(logify_exception_info(e))
                    except Exception as e:
                        # Channel no longer exists on server
                        channel_log.message += '- Failure\n\n{}'.format(logify_exception_info(e))
                    finally:
                        channel.deleted = True
                        channel.save()
                    channel_log.save()
                    yield from asyncio.sleep(1)
            else:
                # No channels found to be deleted
                pass


            for server in Server.objects.all():
                # This will be to populate Channels and Users
                server_log = Log.objects.creaate(message="")
                try:
                    channels = Channel.objects.filter(server=server, deleted=False)
                    server_log.message += "- Found channels:\n{}\n\n".format(logify_object(channels))
                    for channel in channels:
                        try:
                            server_log.message += "Running for channel {}\n".format(channel)
                            c = self.bot.get_channel(channel.channel_id)
                            if c is None:
                                server_log.message += "- Channel is not found, marking as deleted\n"
                                c.deleted = True
                                c.save()
                                continue
                            user_ids = [su.user.pk for su in ServerUser.objects.filter(server=server)]
                            server_log.message += "  - Users found for this channel: {}\n".format(user_ids)
                            for user in DiscordUser.objects.filter(pk__in=user_ids):
                                try:
                                    server_log.message += "    - Working on user {}\n".format(user)
                                    perms = c.permissions_for(discord.User(id=user.user_id))
                                    server_log.message += "      - Perms: {}\n".format(perms)
                                    cu, cu_created = ChannelUser.objects.get_or_create(channel=channel, user=user)
                                    server_log.message += "        - CU, Created: {},{}\n".format(cu, cu_created)
                                    if not cu_created:
                                        if not perms.read_messages and not perms.send_messages:
                                            server_log.message += "      - Read Messages: {} - Send Messages: {}\n".format(perms.read_messages, perms.send_messages)
                                            cu.delete()
                                except Exception as e:
                                    server_log.message += "- Failed: {}\n".format(logify_exception_info(e))
                                server_log.message += "\n"
                        except Exception as e:
                            server_log.message += "- Failed: {}\n".format(logify_exception_info(e))
                    server_log.message += "\n"
                except Exception as e:
                    server_log.message += "- Failed: {}\n".format(logify_exception_info(e))
                server_log.save()


            tasks = Task.objects.filter(cancelled=False, completed=False, expire_date__lte=timezone.now())
            if tasks.count() >= 1:
                for task in tasks:
                    task_log = Log(message='Running task for {} at {}\n'.format(task.user, timezone.now()))
                    if task.task == Task.ADD_TO_GAME_CHAT:
                        try:
                            user = DiscordUser.objects.get(pk=task.user.pk)
                            game = Game.objects.get(pk=task.game.pk)
                            channel = Channel.objects.get(pk=task.channel.pk)
                            task_log.message += 'Game: {}\nChannel: {}\nUser: {}\nTask:\n{}\n\n'.format(user, game, channel, logify_object(task))
                        except Game.DoesNotExist as e:
                            task_log.message += 'Error finding game for task.\n{}'.format(logify_exception_info(e))
                        except Channel.DoesNotExist as e:
                            task_log.message += 'Error finding channel for game {}\n{}'.format(game, logify_exception_info(e))
                        except Exception as e:
                            task_log.message += 'Unknown error happened\n{}'.format(logify_exception_info(e))
                    else:
                        # Not really a task for some reason
                        task_log.message += 'I don\'t recognize the task \'{}\'...'.format()
                    task_log.save()


def setup(bot):
    loop = asyncio.get_event_loop()
    task = loop.create_task(GamingTasks.run_tasks(bot))
    bot.add_cog(GamingTasks(bot, task))
