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

class Channel(models.Model):
    server = models.ForeignKey('Server')
    user = models.ForeignKey('DiscordUser')
    channel_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"

class ServerUser(models.Model):
    user = models.ForeignKey('DiscordUser')
    server = models.ForeignKey('Server')

    def __str__(self):
        return '{} - {}'.format(str(self.user), str(self.server))

    class Meta:
        verbose_name = "Server User"
        verbose_name_plural = "Server Users"
