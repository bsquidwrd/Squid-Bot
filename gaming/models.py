from django.db import models
from django.utils import timezone


class DiscordUser(models.Model):
    user_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        display_name = self.user_id
        if self.name:
            display_name = '{} ({})'.format(self.name, self.user_id)
        return display_name

    class Meta:
        verbose_name = "Discord User"
        verbose_name_plural = "Discord Users"


class Game(models.Model):
    name = models.CharField(max_length=255)
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
    server_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True, default="")

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
    role_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return '{} ({})'.format(self.name, str(self.server))

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"


class Channel(models.Model):
    server = models.ForeignKey('Server')
    user = models.ForeignKey('DiscordUser', blank=True, null=True)
    channel_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    private = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    def save(self, *args, **kwargs):
        from datetime import timedelta
        if not self.id:
            self.expire_date = timezone.now() + timedelta(minutes=15)
        super(Channel, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"


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
        if not self.id:
            self.expire_date = timezone.now() + timedelta(minutes=30)
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
