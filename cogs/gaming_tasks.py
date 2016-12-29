from discord.ext import commands
from discord.enums import ChannelType
from .utils import checks
import asyncio
import discord

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch, Channel, Task, Log, ChannelUser, ServerUser
from gaming.utils import logify_exception_info, logify_object, current_line


class GamingTasks:
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

    async def run_tasks(self):
        while not self.bot.is_closed:
            try:
                await asyncio.sleep(5)
                # print(timezone.now())
                print("Herro")

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
                            channel.created_date = c.created_at
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
                                for overwrite in c._permission_overwrites:
                                    try:
                                        user = DiscordUser.objects.get_or_create(user_id=overwrite.id)[0]
                                        created = ChannelUser.objects.get_or_create(channel=channel, user=user)[1]
                                        log_item.message += "  - {0.name} ({0.user_id}) is in channel. Created: {}".format(user, created)
                                    except Exception as e:
                                        log_item.message += "- Failed: {}\n{}\n".format(logify_exception_info(), e)
                                    log_item.message += "\n"
                            except Exception as e:
                                log_item.message += "- Failed:\n{}\n{}\n".format(logify_exception_info(), e)
                            finally:
                                log_item.message += "- Finished channel processing\n\n"
                        log_item.message += "\n"
                    except Exception as e:
                        log_item.message += "- Failed: {}\n{}\n".format(logify_exception_info(), e)
                    finally:
                        log_item.save()

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
            except asyncio.CancelledError as e:
                pass
            except Exception as e:
                log_item = Log.objects.create(message="- Error running task:\n{}{}\n".format(logify_exception_info(), e))
            finally:
                log_item.save()

    async def update_channels(self):
        for server in Server.objects.all():
            s = self.bot.get_server(server.server_id)
            log_item = Log.objects.create(message="Starting population of channel users for server {}\n\n".format(server))
            try:
                for c in s.channels:
                    if c.is_private or c.type == ChannelType.voice:
                        continue
                    channel, created = Channel.objects.get_or_create(channel_id=c.id, server=server)
                    channel.name = c.name
                    channel.created_date = c.created_at
                    channel.save()
            except Exception as e:
                log_item.message += "Error working on channels.\n{}\n{}\n".format(logify_exception_info(), e)
            finally:
                log_item.save()


def setup(bot):
    bot.add_cog(GamingTasks(bot))
