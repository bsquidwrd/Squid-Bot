import asyncio
import datetime
import discord
from discord.ext import commands
import pytz

from .utils import checks
from .utils import logify_exception_info, logify_object

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Server, Channel, Log, Message


class MessageLog:
    def __init__(self, bot):
        self.bot = bot

    def __unload(self):
        pass

    def get_server(self, server):
        """
        Returns a Server object after getting or creating the server
        """
        return Server.objects.get_or_create(server_id=server.id, defaults={'name': server.name})[0]

    def get_user(self, member):
        """
        Returns a DiscordUser object after getting or creating the user
        Does not create users for Bots
        """
        return DiscordUser.objects.get_or_create(user_id=member.id, defaults={'name': member.name, 'bot': member.bot})[0]

    def get_server_user(self, user, server):
        return ServerUser.objects.get_or_create(user=user, server=server)[0]

    def get_channel(self, channel):
        if channel.is_private:
            return False
        else:
            return Channel.objects.get_or_create(channel_id=channel.id, server=self.get_server(channel.server), defaults={'name': channel.name})[0]

    async def on_message(self, message):
        """ Logs the message sent """
        user = self.get_user(message.author)
        server = self.get_server(message.server)
        channel = self.get_channel(message.channel)

        if user and server and channel:
            timestamp = pytz.utc.localize(message.timestamp)
            Message.objects.get_or_create(message_id=message.id, content=message.content, server=server, user=user, channel=channel, timestamp=timestamp)


def setup(bot):
    bot.add_cog(MessageLog(bot))
