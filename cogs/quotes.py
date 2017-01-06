import os
import asyncio
from datetime import timedelta
import discord
from django.db.models.query import QuerySet
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
        return s

    def get_user(self, member):
        """
        Returns a :class:`gaming.models.DiscordUser` object after getting or creating the user
        Does not create users for Bots
        """
        u, created = DiscordUser.objects.get_or_create(user_id=member.id)
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
        Return a "pretty" form of the quote
        """
        formatted_message = '**No quote was found!\n Type `?help quote` to find out how to create a Quote**'
        try:
            if not isinstance(quote, Quote):
                raise Exception("Quote passed is not an instance of Quote. It is {}".format(type(quote)))
            pretty_datetime = quote.timestamp.strftime("%Y-%m-%d at %H:%M:%S UTC")
            formatted_message = "Quote ID: `{}`\n```{}``` ~ {} {}\n".format(quote.quote_id, quote.message, quote.user.name, pretty_datetime)
        except Exception as e:
            pass
        return formatted_message


    def beautify_quotes(self, quotes, reserve=0, page=0):
        """
        Return a "pretty" form of multiple quotes
        """
        formatted_message = '**No quotes were found!\n Type `?help quote` to find out how to create a Quote**'
        try:
            if not isinstance(quotes, QuerySet):
                raise Exception("Quotes passed are not of type QuerySet. It is {}".format(type(quotes)))
            if quotes.count() == 0:
                raise Exception("No quotes were passed")
            formatted_message = ""
            for quote in quotes:
                formatted_message += "\n{}".format(self.beautify_quote(quote))
        except Exception as e:
            pass
        return paginate(formatted_message, reserve=reserve)[page]
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
        pass

    async def on_member_update(self, before, after):
        """
        This is to populate games and users automatically
        """
        pass
    # End Events

    # Commands
    @commands.group(name="quote", pass_context=True)
    @checks.is_personal_server()
    async def quote_command(self, ctx):
        """
        Quote everything!
        """
        if ctx.invoked_subcommand is None:
            await self.bot.say("{}: I didn't quite understand your command, please run `?help quote` to learn how to use this command.".format(ctx.message.author.mention), delete_after=30)
        await self.bot.delete_message(ctx.message)

    @quote_command.command(name="add", pass_context=True)
    @checks.is_personal_server()
    async def quote_add_command(self, ctx, user : discord.Member, *, message : str):
        """
        Create a quote for a specific User
        """
        quote_user = self.get_user(user)
        server = self.get_server(ctx.message.server)
        user = self.get_user(ctx.message.author)
        content = message.strip()
        try:
            quote = Quote.objects.create(timestamp=timezone.now(), user=quote_user, added_by=user, server=server, message=content)
            await self.bot.say("{0}, Your quote was create successfully!\nThe Quote ID is `{1}`\nYou can use this to reference it in the future by typing `?quote get {1}`".format(ctx.message.author.mention, quote.quote_id), delete_after=30)
        except Exception as e:
            log_item = Log.objects.create(message="{}\nError creating Quote\n{}\nquote_user: {}\nuser: {}\nserver: {}\nmessage: {}\nmentions: {}".format(logify_exception_info(), e, quote_user, user, server, message, mentions))
            await self.bot.say("{}, There was an error when trying to create your Quote. Please contact my Owner with the following code: `{}`".format(ctx.message.author.mention, log_item.message_token), delete_after=30)

    @quote_command.command(name="get", pass_context=True)
    @checks.is_personal_server()
    async def quote_get_command(self, ctx, quote_id : str):
        """
        Get a specific Quote based on quote_id
        """
        server = self.get_server(ctx.message.server)
        user = self.get_user(ctx.message.author)
        message = ctx.message.content.strip().split(" ")[1::]
        mentions = ctx.message.mentions
        quote_id = quote_id.strip()
        try:
            quote = Quote.objects.get(quote_id=quote_id.strip())
            await self.bot.say("{}".format(self.beautify_quote(quote)))
        except Quote.DoesNotExist as e:
            await self.bot.say("{}, I'm sorry but I can't find a quote with the ID `{}`".format(ctx.message.author.mention, quote_id), delete_after=30)
        except Exception as e:
            log_item = Log.objects.create(message="{}\nError retrieving Quote\n{}\nquote_id: {}".format(logify_exception_info(), e, quote_id))
            await self.bot.say("{}, There was an error when trying to get your Quote. Please contact my Owner with the following code: `{}`".format(ctx.message.author.mention, log_item.message_token), delete_after=30)

    @quote_command.command(name="user", pass_context=True)
    @checks.is_personal_server()
    async def quote_user_command(self, ctx, user : discord.Member, page : int = 0):
        """
        Return all quotes for a specific user
        """
        quote_user = self.get_user(user)
        quotes = Quote.objects.filter(user=quote_user)
        await self.bot.say("{}".format(self.beautify_quotes(quotes, page=page)))

    @quote_command.command(name="random", pass_context=False)
    @checks.is_personal_server()
    async def quote_random_command(self):
        """
        Return a random Quote
        """
        await self.bot.say("{}".format(self.beautify_quote(Quote.random_quote())))
    # End Commands

    # Errors
    @quote_command.error
    async def quote_command_error(self, error, ctx):
        if type(error) is commands.BadArgument:
            await self.bot.say(error)
    # End Errors


def setup(bot):
    bot.add_cog(Quotes(bot))
