from django.contrib import admin
from django.contrib import messages

from privatechannel.models import DiscordUser, ServerUser, Server, Channel


class DiscordUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['user_id', 'name',]}),
    ]

    list_display = ('get_display_name', 'user_id', 'name',)
    list_display_links = ('get_display_name',)
    search_fields = ('user_id', 'name',)


class ServerAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['server_id', 'name',]}),
    ]

    list_display = ('get_display_name', 'server_id', 'name',)
    list_display_links = ('get_display_name',)
    search_fields = ('server_id', 'name',)


class ChannelAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['channel_id', 'name', 'created_date', 'server', 'user',]}),
    ]

    date_hierarchy = 'created_date'
    list_display = ('get_display_name', 'channel_id', 'name', 'server', 'user',)
    list_display_links = ('get_display_name',)
    search_fields = ('server__server_id', 'user__user_id', 'channel_id', 'user__name',)


class ServerUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['user', 'server',]}),
    ]

    list_display = ('get_display_name', 'user', 'server',)
    list_display_links = ('get_display_name',)
    search_fields = ('user__user_id', 'user__name', 'server__server_name', 'server__name',)

admin.site.register(DiscordUser, DiscordUserAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(ServerUser, ServerUserAdmin)
admin.site.register(Channel, ChannelAdmin)
