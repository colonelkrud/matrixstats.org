from django.contrib import admin
from django.utils.safestring import mark_safe

from room_stats.models import Room
from room_stats.models import Tag
from room_stats.models import DailyMembers
from room_stats.models import ServerStats
from room_stats.models import Category

class RoomAdmin(admin.ModelAdmin):
    def logo(self, obj):
        if obj.avatar_url is '':
            return ""
        path = obj.avatar_url.replace(
            'mxc://',
            'https://matrix.org/_matrix/media/v1/thumbnail/'
        )
        img = "<img src='%s?method=crop&height=30&width=30'/>" % (
            path,
        )
        return mark_safe(img)
    logo.short_description = "logo"


    list_display = ('logo', 'members_count', 'name', 'topic', 'is_public_readable', 'is_guest_writeable', 'updated_at')
    ordering = ('-members_count', )


class DailyMembersAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'date','members_count')

class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')

class ServerStatsAdmin(admin.ModelAdmin):
    list_display = ('latency', 'date')

class CategoryAdmin(admin.ModelAdmin):
    def image_preview(self, obj):
        style = "max-width: 100px;"
        return mark_safe("<img src='/static/%s' style='%s'/>" %  (obj.image.name, style))
    image_preview.short_description = 'Image'

    def rooms_count(self, obj):
        return obj.room_set.count()

    list_display = ('image_preview', 'name', 'rooms_count')

admin.site.register(Room, RoomAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(DailyMembers, DailyMembersAdmin)
admin.site.register(ServerStats, ServerStatsAdmin)
admin.site.register(Category, CategoryAdmin)

