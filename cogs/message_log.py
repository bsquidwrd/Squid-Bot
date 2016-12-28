import asyncio
import datetime
import discord
from discord.ext import commands
import pytz

from .utils import checks

import web.wsgi
from django.utils import timezone
from django.db import models
from django.utils import timezone
from gaming.models import DiscordUser, Server, Channel, Log, Message, Attachment
from gaming.utils import logify_exception_info, logify_object


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
            m = Message.objects.get_or_create(message_id=message.id, content=message.content, server=server, user=user, channel=channel, timestamp=timestamp)[0]
            if len(message.attachments) >= 1:
                for a in message.attachments:
                    attachment = Attachment.objects.get_or_create(attachment_id=a['id'], url=a['url'], timestamp=timestamp, user=user, channel=channel, server=server)[0]
                    m.attachments.add(attachment)
            m.save()

    async def on_message_edit(self, before, after):
        """ Update the message that's been edited """
        if before.content == after.content:
            # The event is thrown for when Discord loads an image preview
            # So this is here to prevent two messages of the same exact info
            return
        message = after
        user = self.get_user(message.author)
        server = self.get_server(message.server)
        channel = self.get_channel(message.channel)

        if user and server and channel:
            timestamp = pytz.utc.localize(message.timestamp)
            parent = Message.objects.get_or_create(message_id=before.id, content=before.content, server=server, user=user, channel=channel, timestamp=timestamp)[0]
            Message.objects.get_or_create(message_id=message.id, content=message.content, server=server, user=user, channel=channel, timestamp=timestamp, parent=parent)

    async def on_message_delete(self, message):
        """ Mark a message as deleted """
        user = self.get_user(message.author)
        server = self.get_server(message.server)
        channel = self.get_channel(message.channel)

        if user and server and channel:
            m = Message.objects.filter(message_id=message.id)
            m.update(deleted=True)


def setup(bot):
    bot.add_cog(MessageLog(bot))
