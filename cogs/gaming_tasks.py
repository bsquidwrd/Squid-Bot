from discord.ext import commands
from .utils import checks
import asyncio
import discord

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch, Channel


class GamingTasks:
    def __init__(self, bot, task):
        self.bot = bot
        self.task = task

    def __unload(self):
        self.task.cancel()

    @asyncio.coroutine
    def run_tasks(bot):
        while True:
            yield from asyncio.sleep(15)
            channels = Channel.objects.filter(private=False, expire_date__lte=timezone.now(), deleted=False)
            if channels.count() >= 1:
                for channel in channels:
                    try:
                        c = bot.get_channel(channel.channel_id)
                        yield from bot.delete_channel(c)
                    except Exception as e:
                        # Channel no longer exists on server
                        print(e)
                    finally:
                        channel.deleted = True
                        channel.save()
                    yield from asyncio.sleep(1)
            else:
                # No channels found to be deleted
                pass

def setup(bot):
    loop = asyncio.get_event_loop()
    task = loop.create_task(GamingTasks.run_tasks(bot))
    bot.add_cog(GamingTasks(bot, task))
