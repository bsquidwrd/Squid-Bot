import random
import string

from django.db import models
from django.db.models.aggregates import Count
from django.utils import timezone
from django.utils.functional import lazy
from django.core.urlresolvers import reverse

from gaming.utils import logify_exception_info


class DiscordUser(models.Model):
    """
    Used to represent a User on Discord

    user_id : Required[str]
        A unique string to represent the User on Discord (The User ID)
    name : Optional[str]
        The users Discord Username
    bot : Optional[bool]
        Whether or not the user is a bot
    avatar_url : Optional[str]
        The URL a users avatar can be found
    """
    user_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000)
    bot = models.BooleanField(default=False)
    avatar_url = models.CharField(max_length=4000, blank=True, null=True)

    def __str__(self):
        display_name = self.user_id
        if self.name:
            display_name = '{} ({})'.format(self.name, 'Bot' if self.bot else 'User')
        return display_name

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = DiscordUser.objects.get(pk=self.pk)
            for field in self._meta.get_fields():
                try:
                    old_value = getattr(original, field.name)
                    new_value = getattr(self, field.name)
                    if old_value != new_value:
                        DiscordUserHistory.objects.create(user=self, old_value=old_value, new_value=new_value, field_modified=field.name)
                except Exception as e:
                    pass
        super().save(*args, **kwargs)

    def get_icon(self):
        """
        Returns the URL used for a Users Avatar
        """
        return self.avatar_url

    def get_url(self):
        """
        Returns a link to view the User in the webapp
        """
        return reverse('user', args=[self.user_id])

    class Meta:
        verbose_name = "Discord User"
        verbose_name_plural = "Discord Users"


class DiscordUserHistory(models.Model):
    """
    Track changes made to a DiscordUser
    """
    USER_ID_FIELD = 'user_id'
    USERNAME_FIELD = 'name'
    BOT_FIELD = 'bot'
    AVATAR_URL_FIELD = 'avatar_url'
    FIELDS_TO_CHANGE = (
        (USER_ID_FIELD, USER_ID_FIELD),
        (USERNAME_FIELD, USERNAME_FIELD),
        (BOT_FIELD, BOT_FIELD),
        (AVATAR_URL_FIELD, AVATAR_URL_FIELD),
    )
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey('DiscordUser')
    field_modified = models.CharField(max_length=4000, choices=FIELDS_TO_CHANGE)
    old_value = models.CharField(max_length=4000)
    new_value = models.CharField(max_length=4000)

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        verbose_name = 'Discord User History'
        verbose_name_plural = 'Discord User Histories'


class Game(models.Model):
    """
    Used to represent a Game on Discord

    name : Required[str]
        A unique string to represent the Game
    url : Optional[str]
        The URL provided when the game was gotten from Discord (usually blank)
    """
    name = models.CharField(max_length=4000)
    url = models.URLField(blank=True, null=True, default="")

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"


class GameUser(models.Model):
    """
    Associates users to a game that they've played

    user : Required[:class:`gaming.models.DiscordUser`]
        The DiscordUser in question
    game : Required[:class:`gaming.models.Game`]
        The Game in question
    """
    user = models.ForeignKey('DiscordUser')
    game = models.ForeignKey('Game')

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.game))

    class Meta:
        verbose_name = "Game User"
        verbose_name_plural = "Game Users"


class Server(models.Model):
    """
    Represents a Server/Guild on DiscordUser

    owner : Optional[:class:`gaming.models.DiscordUser`]
        The owner of the Server
    server_id : Required[str]
        The Server ID on Discord
    name : Optional[str]
        The name of the server
    icon : Optional[str]
        The current icon hash for the server
    """
    owner = models.ForeignKey('DiscordUser', blank=True, null=True)
    server_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000, blank=True, null=True, default="")
    icon = models.CharField(max_length=4000, blank=True, null=True)

    def __str__(self):
        display_name = '{}'.format(self.server_id)
        if self.name:
            display_name = '{} ({})'.format(self.name, self.server_id)
        return display_name

    def get_url(self):
        """
        Returns a link to the Server page on the webapp
        """
        return reverse('server', args=[self.server_id])

    def get_icon(self):
        """
        Returns the URL for the server icon
        """
        return "https://cdn.discordapp.com/icons/{}/{}.jpg".format(self.server_id, self.icon)

    class Meta:
        verbose_name = "Server"
        verbose_name_plural = "Servers"


class Role(models.Model):
    server = models.ForeignKey('Server')
    role_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000)

    def __str__(self):
        return '{} ({})'.format(self.name, str(self.server))

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"


class Channel(models.Model):
    """
    Represents a Channel on Discord

    server : Required[:class:`gaming.models.Server`]
        The Server this Channel is associated with
    user : Optional[:class:`gaming.models.DiscordUser`]
        The DiscordUser this channel was created for (ex: Private Channel)
    game : Optional[:class:`gaming.models.Game`]
        The Game associated with this Channel
    channel_id : Required[str]
        The Channel ID as assigned from Discord to this Channel
    name : Required[str]
        The name of this Channel
    created_date : Required[timestamp]
        When the Channel was created
    expire_date : Optional[timestamp]
        When the Channel expires (ex: Game Channel expires after x minutes)
    private : Optional[bool]
        If the Channel is a Private Channel (ex: A Channel created for a specific DiscordUser)
    deleted : Optional[bool]
        If the Channel has been deleted from the Server
    game_channel = Optional[bool]
        If the Channel is a associated with a Game
    warning_sent = Option[bool]
        This is used if the Channel is a Game Channel and is a place to store whether or not a warning was sent stating the Channel is going to be deleted soon
    """
    server = models.ForeignKey('Server')
    user = models.ForeignKey('DiscordUser', blank=True, null=True)
    game = models.ForeignKey('Game', blank=True, null=True)
    channel_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000)
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(blank=True, null=True)
    private = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    game_channel = models.BooleanField(default=False)
    warning_sent = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if not self.pk and not self.expire_date and not self.private and not self.game_channel:
            self.expire_date = timezone.now() + timedelta(minutes=15)
        super(Channel, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"


class ChannelUser(models.Model):
    """
    Stores the association of a DiscordUser to a Channel

    channel : Required[:class:`gaming.models.Channel`]
        The Channel in question
    user : Required[:class:`gaming.models.DiscordUser`]
        The User in question
    """
    channel = models.ForeignKey('Channel')
    user = models.ForeignKey('DiscordUser')

    def __str__(self):
        return '{} - {}'.format(self.channel, self.user)

    class Meta:
        verbose_name = "Channel User"
        verbose_name_plural = "Channel Users"


class Message(models.Model):
    """
    Represents a Message on DiscordUser

    server : Required[:class:`gaming.models.Server`]
        The Server on which the Message was sent
    channel : Required[:class:`gaming.models.Channel`]
        The Channel in which the Message was sent
    user : Required[:class:`gaming.models.DiscordUser`]
        The User who sent the Message
    parent : Optional[:class:`gaming.models.Message`]
        If the Message was edited, this represents the "before"
    attachments : Optional[:class:`gaming.models.Attachment`]
        The Attachments associated with this Message (ex: A picture was sent)
    timestamp : Required[timestamp]
        The date and time the Message was sent
    content : Required[str]
        The Message content
    message_id : Required[str]
        The ID assigned by Discord to this Message
    deleted : Optional[bool]
        Whether or not the Message has been deleted
    """
    server = models.ForeignKey('Server')
    channel = models.ForeignKey('Channel')
    user = models.ForeignKey('DiscordUser')
    parent = models.ForeignKey('Message', blank=True, null=True)
    attachments = models.ManyToManyField('Attachment')
    timestamp = models.DateTimeField()
    content = models.TextField()
    message_id = models.CharField(max_length=4000)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.timestamp, self.user, self.channel, self.server)


class Attachment(models.Model):
    """
    Represents an Attachment object that was sent through DiscordUser

    server : Required[:class:`gaming.models.Server`]
        The Server on which the Attachment was sent
    channel : Required[:class:`gaming.models.Channel`]
        The Channel in which the Attachment was sent
    user : Required[:class:`gaming.models.DiscordUser`]
        The User who sent the Attachment
    attachment_id : Required[str]
        The ID assigned to this Attachment by Discord
    url : Required[url]
        The URL to which the Attachment was uploaded
    timestamp : Required[timestamp]
        The date and time the Attachment was uploaded
    """
    server = models.ForeignKey('Server')
    channel = models.ForeignKey('Channel')
    user = models.ForeignKey('DiscordUser')
    attachment_id = models.CharField(max_length=4000)
    url = models.URLField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.timestamp, self.user, self.channel, self.server)


class GameSearch(models.Model):
    """
    Represents a Search for a Game

    user : Required[:class:`gaming.models.DiscordUser`]
        The User searching for a Game
    game : Required[:class:`gaming.models.Game`]
        The Game the User is searching for
    created_date : Optional[timestamp]
        When the Search was started
    expire_date : Optional[timestamp]
        When the Search expires
    cancelled : Optional[bool]
        Whether or not the Search has been cancelled
    game_found : Option[bool]
        Whether or not the Search was successful and the User found a Game
    """
    user = models.ForeignKey('DiscordUser')
    game = models.ForeignKey('Game')
    # server = models.ForeignKey('Server')
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(default=timezone.now)
    cancelled = models.BooleanField(default=False)
    game_found = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.game))

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if not self.pk:
            self.expire_date = timezone.now() + timedelta(minutes=15)
        super(GameSearch, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Game Search"
        verbose_name_plural = "Game Searches"


class ServerUser(models.Model):
    """
    Represents a User to Server relationship

    user : Required[:class:`gaming.models.DiscordUser`]
        The User in question
    server : Required[:class:`gaming.models.Server`]
        The Server in question
    """
    user = models.ForeignKey('DiscordUser')
    server = models.ForeignKey('Server')

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.server))

    class Meta:
        verbose_name = "Server User"
        verbose_name_plural = "Server Users"


class Quote(models.Model):
    """
    Quotes to track as requested by any user

    user : Required[:class:`gaming.models.DiscordUser`]
        The User who said the thing
    server : Required[:class:`gaming.models.Server`]
        The Server in which the User said this
    added_by : Required[:class:`gaming.models.DiscordUser`]
        Who added the Quote
    message : Required[str]
        What the User said
    timestamp : Required[timestamp]
        When the Quote was created
    """
    quote_id = models.CharField(blank=True, null=True, max_length=50)
    user = models.ForeignKey('DiscordUser')
    server = models.ForeignKey('Server')
    added_by = models.ForeignKey('DiscordUser', related_name='added_by')
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '{0.server} - {0.user} {0.added_by}'.format(self)

    def generate_quote_id(self, save=True):
        """
        Used to generate a unique ID for this Quote

        Called by a signal if no quote_id is specified (recommended)

        If an error occurs generating an ID, a Log will be created with the exception information
        """
        try:
            if self.quote_id is None or self.quote_id == '':
                self.quote_id = self.generate_id()
                if save:
                    self.save()
            return True
        except Exception as e:
            print(e)
            Log.objects.create(message="{}\nError generating quote id.\n\nException:\n{}".format(logify_exception_info(), e))
            return False

    def generate_id(self):
        quote_id = random_key(10)
        if self.__class__.objects.filter(quote_id=quote_id).count() >= 1:
            quote_id = self.generate_id()
        return quote_id

    @classmethod
    def random_quote(cls, server=None):
        """
        Returns a random quote
        """
        quotes = cls.objects.all()
        if server is not None:
            quotes.filter(server=server)
        count = quotes.count()
        random_index = random.randint(0, count - 1)
        return quotes[random_index]

    class Meta:
        verbose_name = "Quote"
        verbose_name_plural = "Quotes"


class Task(models.Model):
    """
    Represents a Task that needs to be compelted
    Ex: Add a User to a Game Channel on Server join

    user : Required[:class:`gaming.models.DiscordUser`]
        The User that the Task is to be run for
    server : Required[:class:`gaming.models.Server`]
        The Server that the Task should be run on
    game : Optional[:class:`gaming.models.Game`]
        The Game associated with this Task
    channel : Optional[:class:`gaming.models.Channel`]
        The Channel associated with this Task
    task : Required[str]
        The type of Task to perform
    task_info : Optional[str]
        Any additinal information needed to perform this Task

        .. note::
            **Task Types**

            - ATG: Add to a game
    created_date : Optional[timestamp]
        When the Task was created
    expire_date : Optional[timestamp] Default: 15 minutes after `created_date`
        When the Task expires if it hasn't been completed yet
    cancelled : Optional[bool]
        Whether or not the Task has been cancelled
    completed : Optional[bool]
        Whether or not the Task has been completed
    """
    ADD_TO_GAME_CHAT = 'ATG'
    TASK_TYPES = (
        (ADD_TO_GAME_CHAT, 'Add to a game'),
    )

    user = models.ForeignKey('DiscordUser')
    server = models.ForeignKey('Server')
    game = models.ForeignKey('Game', blank=True, null=True)
    channel = models.ForeignKey('Channel', blank=True, null=True)
    task = models.CharField(max_length=4000, choices=TASK_TYPES)
    task_info = models.CharField(max_length=4000, blank=True, null=True)
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(default=timezone.now)
    cancelled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if not self.pk:
            self.expire_date = timezone.now() + timedelta(minutes=15)
        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        return '{} - {} - {}'.format(self.task, self.user, self.server)


class Log(models.Model):
    """
    Used to Log any and every action taken by the bot

    timestamp : Optional[timestamp]
        The date and time the Log was created
    message_token : Optional[str]
        A unique token to represent this Log (Makes searching for a specific log easy)
    message : Required[str]
        The actions taken that are being logged
    email : Optional[bool]
        Whether or not an email should be sent from the Log being created to the Admins
        NOTE: The moment this is marked True and saved, an email will be sent immediately!
    subject : Optional[str]
        The subject of the email if one is to be sent out. If nothing is specified, a generic one will be generated.
    body : Optional[str]
        the body of the email if one is to be sent out. If nothing is specified, a generic one will be generated.
    """
    timestamp = models.DateTimeField(default=timezone.now)
    message_token = models.CharField(blank=True, null=True, max_length=50)
    message = models.TextField(default="")
    email = models.BooleanField(default=False)
    subject = models.CharField(max_length=4000, blank=True, null=True, default=None)
    body = models.CharField(max_length=4000, blank=True, null=True, default=None)

    def __str__(self):
        return "[%s] - %s" % (self.timestamp, self.message_token)

    def generate_log_token(self, save=True):
        """
        Used to generate a unique token for this Log

        Called by a signal if no message_token is specified (recommended)

        If an error occurs generating a token, a new Log will be created with the exception information and a token of "ERROR_GENERATING_LOG_TOKEN"
        """
        try:
            if self.message_token is None or self.message_token == '':
                self.message_token = self.generate_token()
                if save:
                    self.save()
            return True
        except Exception as e:
            print(e)
            self.__class__.objects.create(message="{}\nError generating log token.\n\nException:\n{}".format(logify_exception_info(), e), message_token="ERROR_GENERATING_LOG_TOKEN")
            return False

    def random_key(self, length=50):
        key = ''
        for i in range(length):
            key += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        return key

    def generate_token(self):
        token_key = random_key()
        if self.__class__.objects.filter(message_token=token_key).count() >= 1:
            token_key = self.generate_token()
        return token_key

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'


def random_key(length=50):
    key = ''
    for i in range(length):
        key += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
    return key
