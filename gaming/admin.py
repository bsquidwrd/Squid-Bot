from django.contrib import admin
from gaming.models import *


class DiscordUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['user_id', 'name', 'bot', 'avatar_url',]}),
    ]

    list_display = ('get_display_name', 'user_id', 'name',)
    list_display_links = ('get_display_name',)
    search_fields = ('user_id', 'name',)


class GameAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['name', 'url',]}),
    ]

    list_display = ('get_display_name', 'name', 'url',)
    list_display_links = ('get_display_name',)
    search_fields = ('name', 'url',)


class GameUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['user', 'game',]}),
    ]

    list_display = ('get_display_name',)
    list_display_links = ('get_display_name',)
    search_fields = ('user__name', 'user__user_id', 'game__name',)
    raw_id_fields = ('user', 'game',)


class ServerAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['server_id', 'name', 'owner', 'icon',]}),
    ]

    list_display = ('get_display_name', 'server_id', 'name',)
    list_display_links = ('get_display_name',)
    search_fields = ('server_id', 'name',)
    raw_id_fields = ('owner',)


class RoleAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['server', 'role_id', 'name',]}),
    ]

    list_display = ('get_display_name', 'role_id', 'name',)
    list_display_links = ('get_display_name',)
    search_fields = ('server__server_id', 'role_id', 'name',)
    raw_id_fields = ('server',)


class GameSearchAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    def cancel_searches(self, request, queryset):
        queryset.update(cancelled=True)
        self.message_user(request, 'All selected searches have been cancelled', level=messages.SUCCESS)

    get_display_name.short_description = 'Display Name'
    cancel_searches.short_description = 'Cancel selected Game Searches'

    fieldsets = [
        (None, {'fields': ['user', 'game', 'created_date', 'expire_date', 'cancelled',]}),
    ]

    date_hierarchy = 'created_date'
    list_display = ('get_display_name', 'created_date', 'expire_date', 'cancelled',)
    list_display_links = ('get_display_name',)
    search_fields = ('user__user_id', 'user__name', 'game__name',)
    # readonly_fields = ('user', 'game')
    ordering = ('cancelled', '-created_date', '-expire_date')
    actions = ['cancel_searches']
    raw_id_fields = ('user', 'game',)


class ServerUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['user', 'server',]}),
    ]

    list_display = ('get_display_name',)
    list_display_links = ('get_display_name',)
    search_fields = ('user__name', 'user__user_id', 'server__server_id', 'server__name',)
    raw_id_fields = ('server','user',)


class ChannelAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['name', 'channel_id', 'server', 'user', 'game', 'created_date', 'expire_date', 'private', 'deleted', 'game_channel','warning_sent',]}),
    ]

    date_hierarchy = 'created_date'
    list_display = ('get_display_name', 'server', 'user', 'game', 'created_date', 'expire_date', 'private', 'deleted', 'game_channel')
    list_display_links = ('get_display_name',)
    search_fields = ('name', 'channel_id', 'user__name', 'user__user_id', 'server__server_id', 'server__name', 'game__name', 'game__url',)
    ordering = ('deleted', 'private', '-created_date', '-expire_date', 'name', 'channel_id')
    raw_id_fields = ('server', 'user', 'game',)


class ChannelUserAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    fieldsets = [
        (None, {'fields': ['channel', 'user',]}),
    ]

    list_display = ('get_display_name',)
    list_display_links = ('get_display_name',)
    search_fields = ('channel__channel_id', 'channel__name', 'user__user_id', 'user__name',)
    raw_id_fields = ('user', 'channel',)


class TaskAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    date_hierarchy = 'created_date'
    list_display = ('get_display_name', 'created_date', 'expire_date', 'cancelled', 'completed')
    list_display_links = ('get_display_name',)
    search_fields = ['user__name', 'user__user_id', 'server__name', 'server__server_id']
    ordering = ['-created_date']
    fieldsets = [
        (None, {'fields': ['server', 'user', 'task', 'created_date', 'expire_date', 'cancelled', 'completed']}),
        ('Task Information', {'fields': ['task_info', 'game', 'channel']}),
    ]
    raw_id_fields = ('server', 'user',)


class LogAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    date_hierarchy = 'timestamp'
    list_display = ('get_display_name', 'timestamp', 'message_token', 'message')
    list_display_links = ('get_display_name',)
    search_fields = ['message_token', 'message']
    ordering = ['-timestamp']
    fieldsets = [
        (None, {'fields': ['timestamp', 'message_token', 'email', 'subject', 'body', 'message']}),
    ]
    readonly_fields = ('timestamp', 'message_token',)


class MessageAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    def get_content(self, obj):
        extra = ''
        if len(obj.content) > 50:
            extra = '...'
        return '{}{}'.format(obj.content[:50], extra)

    date_hierarchy = 'timestamp'
    list_display = ('get_display_name', 'timestamp', 'message_id', 'get_content')
    list_display_links = ('get_display_name',)
    search_fields = ['server__server_id', 'server__name', 'channel__channel_id', 'channel__name', 'user__user_id', 'user__name', 'content', 'message_id']
    ordering = ['-timestamp']
    fieldsets = [
        (None, {'fields': ['timestamp', 'message_id', 'server', 'channel', 'user', 'parent', 'deleted', 'content', 'attachments',]}),
    ]
    raw_id_fields = ('server', 'channel', 'user', 'parent',)
    filter_horizontal = ('attachments',)


class AttachmentAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    date_hierarchy = 'timestamp'
    list_display = ('get_display_name', 'timestamp', 'server', 'channel', 'user')
    list_display_links = ('get_display_name',)
    search_fields = ['server__server_id', 'server__name', 'channel__channel_id', 'channel__name', 'user__user_id', 'user__name',]
    ordering = ['-timestamp']
    fieldsets = [
        (None, {'fields': ['timestamp', 'server', 'channel', 'user', 'url',]}),
    ]
    raw_id_fields = ('server', 'channel', 'user',)


admin.site.register(DiscordUser, DiscordUserAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(GameUser, GameUserAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(GameSearch, GameSearchAdmin)
admin.site.register(ServerUser, ServerUserAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChannelUser, ChannelUserAdmin)
admin.site.register(Attachment, AttachmentAdmin)
