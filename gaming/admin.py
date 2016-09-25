from django.contrib import admin
from gaming.models import DiscordUser, Game, GameUser, Server, Role, GameSearch


class GameSearchAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    def cancel_searches(self, request, queryset):
        queryset.update(cancelled=True)
        self.message_user(request, 'All selected students were marked for refresh', level=messages.SUCCESS)

    get_display_name.short_description = 'Display Name'
    cancel_searches.short_description = 'Cancel selected Game Searches'

    fieldsets = [
        (None, {'fields': ['user', 'game', 'created_date', 'expire_date', 'cancelled',]}),
    ]

    date_hierarchy = 'created_date'
    list_display = ('get_display_name', 'created_date', 'expire_date', 'cancelled')
    list_display_links = ('get_display_name',)
    search_fields = ('user__user_id', 'game__name',)
    # readonly_fields = ('user', 'game')
    ordering = ('cancelled', '-created_date', '-expire_date')
    actions = ['cancel_searches']

admin.site.register(DiscordUser)
admin.site.register(Game)
admin.site.register(GameUser)
admin.site.register(Server)
admin.site.register(Role)
admin.site.register(GameSearch, GameSearchAdmin)
