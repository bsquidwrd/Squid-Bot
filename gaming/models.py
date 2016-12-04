import random
import string

from django.db import models
from django.utils import timezone


class DiscordUser(models.Model):
    user_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000)
    bot = models.BooleanField(default=False)

    def __str__(self):
        display_name = self.user_id
        if self.name:
            display_name = '{} ({})'.format(self.name, 'Bot' if self.bot else 'User')
        return display_name

    class Meta:
        verbose_name = "Discord User"
        verbose_name_plural = "Discord Users"


class Game(models.Model):
    name = models.CharField(max_length=4000)
    url = models.URLField(blank=True, null=True, default="")

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"


class GameUser(models.Model):
    user = models.ForeignKey('DiscordUser')
    game = models.ForeignKey('Game')

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.game))

    class Meta:
        verbose_name = "Game User"
        verbose_name_plural = "Game Users"


class Server(models.Model):
    owner = models.ForeignKey('DiscordUser', blank=True, null=True)
    server_id = models.CharField(max_length=4000, unique=True)
    name = models.CharField(max_length=4000, blank=True, null=True, default="")
    icon = models.CharField(max_length=4000, blank=True, null=True)

    def __str__(self):
        display_name = '{}'.format(self.server_id)
        if self.name:
            display_name = '{} ({})'.format(self.name, self.server_id)
        return display_name

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
    channel = models.ForeignKey('Channel')
    user = models.ForeignKey('DiscordUser')

    def __str__(self):
        return '{} - {}'.format(self.channel, self.user)

    class Meta:
        verbose_name = "Channel User"
        verbose_name_plural = "Channel Users"


class Message(models.Model):
    server = models.ForeignKey('Server')
    channel = models.ForeignKey('Channel')
    user = models.ForeignKey('DiscordUser')
    timestamp = models.DateTimeField()
    content = models.TextField()
    message_id = models.CharField(max_length=4000)

    def __str__(self):
        return '{} - {} - {} - {}'.format(self.timestamp, self.user, self.channel, self.server)


class GameSearch(models.Model):
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
    user = models.ForeignKey('DiscordUser')
    server = models.ForeignKey('Server')

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.server))

    class Meta:
        verbose_name = "Server User"
        verbose_name_plural = "Server Users"


class Task(models.Model):
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
    timestamp = models.DateTimeField(default=timezone.now)
    message_token = models.CharField(blank=True, null=True, max_length=50)
    message = models.TextField(default="")
    email = models.BooleanField(default=False)
    subject = models.CharField(max_length=4000, blank=True, null=True, default=None)
    body = models.CharField(max_length=4000, blank=True, null=True, default=None)

    def __str__(self):
        return "[%s] - %s" % (self.timestamp, self.message_token)

    def generate_log_token(self, save=True):
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
        token_key = self.random_key()
        if len(self.__class__.objects.filter(message_token=token_key)) >= 1:
            token_key = self.generate_token()
        return token_key

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'
