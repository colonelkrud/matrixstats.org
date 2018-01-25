from datetime import datetime, timedelta
from django.utils import timezone

from django.db import models

class Room(models.Model):
    id = models.CharField(max_length=511, primary_key=True)
    name = models.TextField(blank=True, null=True)
    aliases = models.TextField(blank=True, null=True)
    topic = models.TextField(blank=True, null=True)
    members_count = models.IntegerField()
    avatar_url = models.TextField(blank=True, null=True)
    is_public_readable = models.BooleanField()
    is_guest_writeable = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "(%s) %s" % (self.members_count, self.name)

class DailyMembers(models.Model):
    id = models.CharField(max_length=511, primary_key=True, editable=False)
    room_id = models.CharField(max_length=511, db_index=True)
    members_count = models.IntegerField()
    date = models.DateField(default=datetime.now, editable=False, db_index=True)#auto_now=True)

    def save(self):
        self.id = "%s-%s" % ( self.room_id, self.date.strftime("%Y%m%d"))
        super(DailyMembers, self).save()

    class Meta:
        verbose_name_plural = "Daily Members"

class Tag(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    rooms = models.ManyToManyField(Room)
    updated_at = models.DateTimeField(auto_now=True)

class ServerStats(models.Model):
    server = models.CharField(max_length=255)
    latency = models.IntegerField()
    date = models.DateTimeField(default=datetime.now)

class Category(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    pass

