from discord.ext import commands
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
    def __init__(self, bot, task):
        self.bot = bot
        self.task = task

    def __unload(self):
        self.task.cancel()

    @asyncio.coroutine
    def run_tasks(bot):
        while True:
            try:
                yield from asyncio.sleep(5)

                channels = Channel.objects.filter(private=False, game_channel=True, expire_date__lte=timezone.now(), deleted=False)
                if channels.count() >= 1:
                    log_item = Log.objects.create(message="Running task to prune channels:\n{}\n\n".format(logify_object(channels)))
                    for channel in channels:
                        if channel is None:
                            continue
                        log_item.message += 'Deleting channel {}\n\n'.format(channel)
                        try:
                            c = yield from bot.get_channel(channel.channel_id)
                            if c is not None:
                                try:
                                    yield from bot.delete_channel(c)
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
                        yield from asyncio.sleep(1)
                    log_item.save()
                else:
                    # No channels found to be deleted
                    pass

                for server in Server.objects.all():
                    # This will be to populate Channels and Users
                    s = bot.get_server(server.server_id)
                    log_item = Log.objects.create(message="Starting population of channel users for server {}\n\n".format(server))
                    try:
                        channels = Channel.objects.filter(server=server, deleted=False)
                        log_item.message += "Found channels:\n{}\n\n".format(logify_object(channels))
                        for channel in channels:
                            try:
                                log_item.message += "Running for channel {}\n".format(channel)
                                c = bot.get_channel(channel.channel_id)
                                if c.is_default:
                                    log_item.message += "- Channel is default channel, skipping...\n"
                                    continue
                                if c is None:
                                    log_item.message += "- Channel is not found, marking as deleted\n"
                                    c.deleted = True
                                    c.save()
                                    continue
                                user_ids = [su.user.pk for su in ServerUser.objects.filter(server=server)]
                                log_item.message += "  - Users found for this server, qualified for this channel: {}\n".format(user_ids)
                                for user in DiscordUser.objects.filter(pk__in=user_ids):
                                    try:
                                        log_item.message += "    - Working on user {}\n".format(user)
                                        perms = c.overwrites_for(discord.User(id=user.user_id))
                                        log_item.message += "      - Perms: {}\n".format(perms)
                                        cu, cu_created = ChannelUser.objects.get_or_create(channel=channel, user=user)
                                        log_item.message += "        - CU, Created: {},{}\n".format(cu, cu_created)
                                        if not cu_created:
                                            if not perms.read_messages and not perms.send_messages:
                                                log_item.message += "      - Read Messages: {} - Send Messages: {}\n".format(perms.read_messages, perms.send_messages)
                                                cu.delete()
                                    except Exception as e:
                                        log_item.message += "- Failed: {}\n{}\n".format(logify_exception_info(), e)
                                    log_item.message += "\n"
                            except Exception as e:
                                log_item.message += "- Failed:\n{}\n{}\n".format(logify_exception_info(), e)
                            finally:
                                log_item.message += "- Finished channel processing\n"
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
            except Exception as e:
                log_item = Log.objects.create(message="- Error running task:\n{}{}\n".format(logify_exception_info(), e))
            finally:
                log_item.save()


def setup(bot):
    loop = asyncio.get_event_loop()
    task = loop.create_task(GamingTasks.run_tasks(bot))
    bot.add_cog(GamingTasks(bot, task))
