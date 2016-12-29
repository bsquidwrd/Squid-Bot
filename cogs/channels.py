import os
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
from datetime import datetime, timedelta
import discord
from .utils import checks

import web.wsgi
from django.utils import timezone
from django.db import models
from gaming.models import DiscordUser, Server, Channel, ServerUser

class PrivateChannel:
    """
    Used to create Private Channels for Users when requested
    """
    def __init__(self, bot):
        self.bot = bot
        self.populate_info()
        super().__init__()

    def __unload(self):
        """Called when the cog is unloaded"""
        pass

    # Class methods
    def populate_info(self):
        for server in self.bot.servers:
            self.get_server(server)
            for user in server.members:
                if user.bot:
                    continue
                self.get_user(user)
                self.get_server_user(user, server)

    def get_user(self, member):
        """
        Get a :class:`gaming.models.DiscordUser` object for the member
        """
        # Returns a DiscordUser object after getting or creating the user
        # Does not do anything for a bot user
        if member.bot:
            return False
        return DiscordUser.objects.get_or_create(user_id=member.id, defaults={'name': member.name})[0]

    def get_server(self, discord_server):
        """
        Get a :class:`gaming.models.Server` object for the discord_server
        """
        return Server.objects.get_or_create(server_id=discord_server.id, defaults={'name': discord_server.name})[0]

    def get_server_user(self, member, discord_server):
        """
        Get a :class:`gaming.models.ServerUser` object for the member and discord_server
        """
        user = self.get_user(member)
        server = self.get_server(discord_server)
        return ServerUser.objects.get_or_create(user=user, server=server)

    def get_channel(self, dchannel, user, server):
        """
        Get a :class:`gaming.models.Channel` object for the dchannel, user and server
        """
        return Channel.objects.get_or_create(channel_id=dchannel.id, user=user, server=server, private=True, defaults={'name': dchannel.name})[0]
    # End methods

    # Events
    async def on_ready(self):
        """
        When the cog is ready, populate all the information it will need like Servers and Users
        """
        self.populate_info()

    async def on_member_join(self, member):
        """
        When a member joins a server, make sure they have a :class:`gaming.models.DiscordUser` object
        """
        self.get_user(member)

    async def on_member_remove(self, member):
        pass

    async def on_member_update(self, before, after):
        """
        When a member does something that causes this even to be thrown, make sure they have a :class:`gaming.models.DiscordUser` object
        """
        self.get_user(after)
    # End Events

    # Commands
    @commands.command(name='private', pass_context=True)
    async def create_private_channel(self, ctx, *args):
        """
        Creates a private channel that you control!
        """
        dserver = ctx.message.server
        duser = ctx.message.author
        server = self.get_server(dserver)
        user = self.get_user(duser)
        if not user:
            return
        try:
            channel = Channel.objects.get(user=user, server=server, private=True)
            dchannel = self.bot.get_channel(channel.channel_id)
            if dchannel:
                await self.bot.say("Looks like you already have a channel {}, which is {}".format(duser.mention, dchannel.mention), delete_after=30)
            else:
                message = "Channel ID {} was in my Database but is no longer on the Server {}".format(str(channel), str(channel.server))
                channel.delete()
                raise Channel.DoesNotExist(message)
        except Channel.DoesNotExist as e:
            everyone = discord.PermissionOverwrite(read_messages=False, send_messages=False, connect=False)
            user_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True, manage_channels=True)
            dchannel = await self.bot.create_channel(dserver, user.name.replace(" ", "_"), (dserver.default_role, everyone), (dserver.me, user_perms), (ctx.message.author, user_perms))
            self.get_channel(dchannel, user, server)
            formatted_message = """
Welcome to your private channel!
You can add and remove people from this and the associated voice channel as you please.
If you need any help, please refer to https://support.discordapp.com/hc/en-us/articles/206029707-How-do-I-set-up-Permissions-
Specifically, take a look at the section labeled "Specific channel permissions"

Currently you, myself and the Server Admins are able to see this channel.

Please make sure you still follow the rules that apply to the `{0.name}` server
""".format(server)
            msg = await self.bot.send_message(dchannel, formatted_message)
            await self.bot.pin_message(msg)
            await self.bot.say("Your channel has been created {}! Please go to {} to learn more.".format(duser.mention, dchannel.mention), delete_after=30)
    # End Commands

    # Errors
    # @create_private_channel.error
    # async def create_private_channel_error(self, error, ctx):
    #     if type(error) is commands.BadArgument:
    #         await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(PrivateChannel(bot))
