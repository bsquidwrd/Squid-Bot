from discord.ext import commands
from .utils import checks
import asyncio
import discord
import datetime

import web.wsgi
from django.utils import timezone
from django.db import models
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
            yield from asyncio.sleep(30)
            channels = Channel.objects.filter(private=Faalse, expire_date__lte=datetime.datetime.now())
            for channel in channels:
                try:
                    c = yield from self.bot.get_channel(channel.channel_id)
                    yield from self.bot.delete_channel(c)
                except Exception as e:
                    # Channel no longer exists on server
                    pass
                finally:
                    channel.deleted = True
                    channel.save()

def setup(bot):
    loop = asyncio.get_event_loop()
    task = loop.create_task(GamingTasks.run_tasks(bot))
    bot.add_cog(GamingTasks(bot, task))
