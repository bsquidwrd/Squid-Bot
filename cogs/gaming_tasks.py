from discord.ext import commands
from .utils import checks
from .utils.formats import logify_exception_info, logify_object
import asyncio
import discord

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch, Channel, Task, Log


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
            channels = Channel.objects.filter(private=False, expire_date__lte=timezone.now(), deleted=False)
            if channels.count() >= 1:
                for channel in channels:
                    if channel is None:
                        continue
                    channel_log = Log(message='Deleting channel {}\n\n'.format(channel))
                    try:
                        c = bot.get_channel(channel.channel_id)
                        if c is not None:
                            try:
                                yield from bot.delete_channel(c)
                                channel_log.message += '- Succes'
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
