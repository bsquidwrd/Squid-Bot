from django.contrib import admin
from privatechannel.models import DiscordUser, ServerUser, Server, Channel

admin.site.register(DiscordUser)
admin.site.register(Server)
admin.site.register(ServerUser)
admin.site.register(Channel)
