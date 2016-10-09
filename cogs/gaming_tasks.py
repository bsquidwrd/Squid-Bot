from discord.ext import commands
from .utils import checks
import asyncio
import discord

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


def setup(bot):
    loop = asyncio.get_event_loop()
    task = loop.create_task(GamingTasks.run_tasks(bot))
    bot.add_cog(GamingTasks(bot, task))
