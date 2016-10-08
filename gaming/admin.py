from django.contrib import admin
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch


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

admin.site.register(DiscordUser, DiscordUserAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(GameUser, GameUserAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(GameSearch, GameSearchAdmin)
