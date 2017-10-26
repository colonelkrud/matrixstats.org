import json
import re
import os
import requests
from datetime import datetime, timedelta
from django.db import transaction

from room_stats.models import Room, DailyMembers, Tag

class MatrixClientError(Exception):
    pass

class MatrixClientTimeoutError(MatrixClientError):
    pass

class MatrixClient:
    def __init__(self, server, username=None, password=None, token=None):
        self.server = server
        self.username = username
        self.password = password
        self.token = token

    def __get_url(self, path):
        return "%s%s" % (self.server, path)

    def get_token(self):
        return self.token if self.token else self.login()

    def login(self, username=None, password=None):
        username = username or self.username
        password = password or self.password
        payload = {
            'user': username,
            'password': password,
            'type': 'm.login.password',
        }
        r = requests.post(
            self.__get_url('/login'),
            json=payload
        )
        if r.status_code == 200:
            self.token = r.json()['access_token']
            return self.token
        else:
            raise MatrixClientException(r.text)

    def get(self, path, params={}):
        params['access_token'] = self.get_token()
        r = requests.get(
            self.__get_url(path),
            params=params
        )
        if r.status_code == 200:
            return r.json()
        else:
            raise MatrixClientException(r.text)

    def get_public_rooms(self, timeout=30, chunk_size=2000, limit=None, args={}):
        upper_time_bound = datetime.now() + timedelta(seconds=timeout)
        if limit and limit <= chunk_size:
            args['limit'] = limit
        else:
            args['limit'] = chunk_size
        rooms = []
        next_chunk = None
        while True:
            if next_chunk:
                args['since'] = next_chunk
            data = self.get('/publicRooms', args)
            rooms.extend(data.get('chunk'))
            next_chunk = data.get('next_batch', None)
            if next_chunk is None:
                break
            if limit and len(rooms) >= limit:
                break
            if datetime.now() > upper_time_bound:
                raise MatrixClientTimeoutException()
        return rooms




# @transaction.atomic
# def update_rooms():
#     date = datetime.now().strftime("%d%m%y")
#     f = open('room_stats/matrix-rooms-%s.json' % date, 'r')
#     rooms = json.loads(f.read())['chunk']
#     print("Rooms found: %s" % len(rooms))
#     for room in rooms:
#         r = Room(
#             id=room['room_id'],
#             name=room.get('name',''),
#             aliases=", ".join(room.get('aliases', [])),
#             topic=room.get('topic',''),
#             members_count=room['num_joined_members'],
#             avatar_url=room.get('avatar_url', ''),
#             is_public_readable=room['world_readable'],
#             is_guest_writeable=room['guest_can_join']
#         )
#         r.save()


# def daily_stats_to_file():
#     TOKEN = os.environ.get("MATRIX_TOKEN", "")
#     date = datetime.now().strftime("%d%m%y")
#     c = MatrixClient("https://matrix.org/_matrix/client/r0", token=TOKEN)
#     result = c.api("/publicRooms")
#     f = open('room_stats/matrix-rooms-%s.json' % date, 'w')
#     f.write(json.dumps(result))
#     f.close()

def get_all_rooms_to_file(filename, limit=None):
    rooms = []
    username = os.environ.get("MATRIX_USERNAME")
    password = os.environ.get("MATRIX_PASSWORD")
    token = os.environ.get("MATRIX_TOKEN")
    c = MatrixClient("https://matrix.org/_matrix/client/r0",
                     username, password, token)
    rooms = c.get_public_rooms(limit=limit)
    f = open(filename, 'w')
    f.write(json.dumps(rooms))
    f.close()

@transaction.atomic
def update_rooms_from_file(filename):
    f = open(filename, 'r')
    rooms = json.loads(f.read())
    print("Rooms found: %s" % len(rooms))
    for room in rooms:
        r = Room(
            id=room['room_id'],
            name=room.get('name',''),
            aliases=", ".join(room.get('aliases', [])),
            topic=room.get('topic',''),
            members_count=room['num_joined_members'],
            avatar_url=room.get('avatar_url', ''),
            is_public_readable=room['world_readable'],
            is_guest_writeable=room['guest_can_join']
        )
        r.save()


@transaction.atomic
def update_tags():
    # clear previous relations
    Tag.objects.all().delete()
    hashtag = re.compile("#\w+")
    rooms = Room.objects.filter(members_count__gt=5, topic__iregex=r'#\w+')
    tags = []
    for room in rooms:
        room_tags = hashtag.findall(room.topic)
        for tag in room_tags:
            linked_tag = Tag(
                id=tag[1:],
            )
            linked_tag.save()
            linked_tag.rooms.add(room)


@transaction.atomic
def update_daily_members():
    rooms = Room.objects.all()
    daily_members_list = []
    for room in rooms:
        dm = DailyMembers(
            room_id=room.id,
            members_count=room.members_count
        )
        dm.save()


def update():
    date = datetime.now().strftime("%d%m%y")
    filename = "room_stats/matrix-rooms-%s.json" % date

    get_all_rooms_to_file(filename)
    update_rooms_from_file(filename)

    update_tags()
    update_daily_members()

