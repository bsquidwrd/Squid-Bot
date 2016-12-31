import os
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from .utils import checks

import web.wsgi
from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils import timezone
from gaming.models import DiscordUser, Server, ServerUser, Quote, Log
from gaming.utils import logify_exception_info, logify_object, paginate


class Quotes:
    """
    Log Quotes of Users
    """
    def __init__(self, bot):
        self.bot = bot

    def __unload(self):
        """Called when the cog is unloaded"""
        pass

    # Class methods
    def get_server(self, server):
        """
        Returns a :class:`gaming.models.Server` object after getting or creating the server
        """
        s, created = Server.objects.get_or_create(server_id=server.id)
        try:
            s.name = server.name
            s.icon = server.icon
            s.owner = self.get_user(server.owner)
            s.save()
            Log.objects.create(message="s: {0}\ncreated: {1}\nname: {0.name}\nicon: {0.icon}\nowner: {0.owner}".format(s, created))
        except Exception as e:
            Log.objects.create(message="Error trying to get Server object for server {}.\n{}".format(s, logify_exception_info()))
        finally:
            s.save()
            return s

    def get_user(self, member):
        """
        Returns a :class:`gaming.models.DiscordUser` object after getting or creating the user
        Does not create users for Bots
        """
        u, created = DiscordUser.objects.get_or_create(user_id=member.id)
        try:
            u.name = member.name
            u.bot = member.bot
            avatar_url = member.avatar_url
            if avatar_url is None or avatar_url == "":
                avatar_url = member.default_avatar_url
            u.avatar_url = avatar_url
            Log.objects.create(message="u: {0}\ncreated: {1}\nname: {0.name}\navatar_url: {0.avatar_url}\nbot: {0.bot}".format(u, created))
        except Exception as e:
            Log.objects.create(message="Error trying to get DiscordUser object for member: {}.\n{}".format(u, logify_exception_info()))
        finally:
            u.save()
            return u

    def get_server_user(self, member, discord_server):
        """
        Get a :class:`gaming.models.ServerUser` object for the member and discord_server
        """
        user = self.get_user(member)
        server = self.get_server(discord_server)
        return ServerUser.objects.get_or_create(user=user, server=server)[0]

    def beautify_quote(self, quote):
        """
        .. todo:: Implement beautify_quote to return a "pretty" form of the quote
        """
        return quote.message

    def beautify_quotes(self, user):
        """
        .. todo:: Implement beautify_quotes to return a "pretty" form of quotes from this user
        """
        return "\n".join([q.message for q in Quote.objects.filter(user=user)])
    # End class methods

    # Events
    async def on_ready(self):
        """
        Bot is loaded, populate information that is needed for this cog
        """
        pass

    async def on_member_join(self, member):
        """
        A new member has joined, make sure there are instance of :class:`gaming.models.Server` and :class:`gaming.models.DiscordUser` for this event
        """
        server = self.get_server(member.server)
        user = self.get_user(member)

    async def on_member_update(self, before, after):
        """
        This is to populate games and users automatically
        """
        server = self.get_server(after.server)
        user = self.get_user(after)
        self.get_server_user(user, server)

    # End Events

    # Commands
    @commands.command(name='quote', pass_context=True, hidden=True)
    @checks.is_owner()
    async def quote_command(self, ctx, *args):
        """
        Quote everything!

        Add a quote: ?quote add <@user> <quote>

        Retrieve all quotes for a user: ?quote user <@user>

        Get a specific quote: ?quote get <id>

        Get a random quote: ?quote random

        Get information for a quote: ?quote info <id>
        """
        server = self.get_server(ctx.message.server)
        user = self.get_user(ctx.message.author)
        message = ctx.message.content.strip().split(" ")[1::]
        mentions = ctx.message.mentions

        action = message[0].strip().lower()

        if action == "add":
            """
            Create a quote for a specific :class:`gaming.models.DiscordUser` on :class:`gaming.models.Server`
            """
            quote_user = None
            if len(mentions) == 0:
                await self.bot.say("{}, You must mention the User in the command!".format(ctx.message.author.mention), delete_after=30)
                return
            elif len(mentions) == 1:
                quote_user = self.get_user(mentions[0])
            else:
                await self.bot.say("{}, Please only mention one User for this Quote".format(ctx.message.author.mention), delete_after=30)
                return

            content = " ".join(message[2::])
            try:
                quote = Quote.objects.create(timestamp=timezone.now(), user=quote_user, added_by=user, server=server, message=content)
                await self.bot.say("{0}, Your quote was create successfully! The Quote ID is `{1}`\nYou can use this to reference it in the future by typing `?quote get {1}`".format(ctx.message.author.mention, quote.quote_id), delete_after=30)
            except Exception as e:
                log_item = Log.objects.create(message="{}\nError creating Quote\n{}\nquote_user: {}\nuser: {}\nserver: {}\nmessage: {}\nmentions: {}".format(logify_exception_info(), e, quote_user, user, server, message, mentions))
                await self.bot.say("{}, There was an error when trying to create your Quote. Please contact my Owner with the following code: `{}`".format(ctx.message.author.mention, log_item.message_token), delete_after=30)
                return

        elif action == "user":
            """
            Return all quotes for a specific user
            """
            quote_user = None
            if len(mentions) == 0:
                await self.bot.say("{}, You must mention the User in the command!".format(ctx.message.author.mention), delete_after=30)
                return
            elif len(mentions) == 1:
                quote_user = self.get_user(mentions[0])
            else:
                await self.bot.say("{}, Please only mention one User for this Quote".format(ctx.message.author.mention), delete_after=30)
                return
            await self.bot.say("{}".format(self.beautify_quotes(quote_user)), delete_after=60)

        elif action == "random":
            """
            Return a random Quote
            """
            quote = Quote.random_quote()
            await self.bot.say("{}".format(self.beautify_quote(quote)), delete_after=60)

        elif action == "get":
            """
            Try to get a specific Quote based on the ID passed
            """
            quote_id = message[1].strip()
            try:
                quote = Quote.objects.get(quote_id=quote_id)
                await self.bot.say("{}".format(self.beautify_quote(quote)), delete_after=60)
            except Quote.DoesNotExist as e:
                await self.bot.say("{}, I'm sorry but I can't find a quote with the ID `{}`".format(ctx.message.author.mention, quote_id), delete_after=30)
            except Exception as e:
                log_item = Log.objects.create(message="{}\nError retrieving Quote\n{}\nquote_id: {}".format(logify_exception_info(), e, quote_id))
                await self.bot.say("{}, There was an error when trying to create your Quote. Please contact my Owner with the following code: `{}`".format(ctx.message.author.mention, log_item.message_token), delete_after=30)

        elif action == "info":
            """
            Return the information about a specific quote
            """
            quote_id = message[1].strip()
            try:
                quote = Quote.objects.get(quote_id=quote_id)
                pretty_datetime = quote.timestamp.strftime("%Y-%m-%d at %H:%M:%S UTC")
                await self.bot.say("Date Created: `{}`\nUser: `{}`\nAdded By: `{}`\nMessage:\n```{}```\n".format(pretty_datetime, quote.user.name, quote.added_by.name, quote.message), delete_after=60)
            except Quote.DoesNotExist as e:
                await self.bot.say("{}, I'm sorry but I can't find a quote with the ID `{}`".format(ctx.message.author.mention, quote_id), delete_after=30)
            except Exception as e:
                log_item = Log.objects.create(message="{}\nError retrieving Quote\n{}\nquote_id: {}".format(logify_exception_info(), e, quote_id))
                await self.bot.say("{}, There was an error when trying to create your Quote. Please contact my Owner with the following code: `{}`".format(ctx.message.author.mention, log_item.message_token), delete_after=30)

        else:
            await self.bot.say("{}: I didn't quite understand your command, please run `?help quote` to learn how to use this command.".format(ctx.message.author.mention), delete_after=30)
        await self.bot.delete_message(ctx.message)
    # End Commands

    # Errors
    @quote_command.error
    async def quote_command_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Quotes(bot))
