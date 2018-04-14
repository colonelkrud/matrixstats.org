import requests
import json
import django
import os
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrix_stats.settings.dev")
django.setup()

from matrix_bot.utils import serialize, critical, prettify
from room_stats.models import Server
from matrix_bot.resources import rs, rds

from matrix_bot.login import login
from matrix_bot.registration import continue_registration, update_profile
from matrix_bot.join import join
from matrix_bot.sync import sync
from matrix_bot.statistics import get_unique_messages, get_unique_members, get_active_rooms

def handle_server_instance(server_id):
    """ Check the server instance for uncompleted registration
    and finish it if neccessary"""
    server = Server.objects.get(pk=server_id)
    if server.status == 'a':
        verify_server_existence(server)
    if server.status == 'c':
        continue_registration(server)


def verify_server_existence(server):
    """ Check the server existance and set the status accordingly"""
    response_data, response_code = None, None
    server.last_response_code = -1
    try:
        r = rs.get(server.api(suffix="/_matrix/client/versions"))
        response_data = r.json()
        response_code = r.status_code
    except json.decoder.JSONDecodeError as ex:
        server.last_response_data = serialize(ex)
        server.status = 'u'
    except requests.exceptions.RequestException as ex:
        server.last_response_data = serialize(ex)
        server.status = 'u'
    except ex:
        server.last_response_data = serialize(ex)
        server.status = 'u'
        critical(ex)
    else:
        server.last_response_data = response_data
        server.last_response_code = response_code
        if response_code == 200 and "versions" in response_data:
            server.status = 'c'
        elif r.status_code >= 400:
            server.status = 'u'
        else:
            server.status = 'n'
    server.save(update_fields=['last_response_data', 'last_response_code', 'status'])


class MatrixHomeserver():
    def __init__(self, server_id):
        self.server = Server.objects.get(pk=server_id)
        self.rs = rs
        self.rds = rds
        self._in_transaction = False

    def _prefixed(self, key):
        """ Expand redis key with server name """
        return "%s__%s" % (self.server.hostname, key)

    def _open_transaction(self):
        """ Open redis pipeline """
        self._in_transaction = True
        self._transaction = self.rds.pipeline()

    def _commit_transaction(self):
        """ Execute redis pipeline """
        self._in_transaction = False
        self._transaction.execute()

    def _scan_keys(self, glob='*'):
        """ Search redis keys by pattern """
        n = 0
        keys = []
        while(True):
            n, k = self.rds.scan(n, match=self._prefixed(glob))
            keys.extend(k)
            if n == 0:
                break
        return keys

    def _cache(self, glob='*', expand=False):
        """ Display keys (and values) by pattern (debug only) """
        keys = self.rds.keys(self._prefixed(glob))
        if not expand:
            keys = [k.decode() for k in keys]
            keys.sort()
            print(prettify(keys))
            return
        result = {}
        for key in keys:
            result[key.decode()] = [
                self.rds.get(key).decode(),
                self.rds.ttl(key)
            ]
        print(prettify(result))

    def _from_cache(self, key):
        """ Get server-related data from redis """
        return self.rds.get(self._prefixed(key))

    def _to_cache(self, key=None, value=None, expire=None, **kwargs):
        """ Set server-related data to redis """
        target = self._transaction if self._in_transaction else self.rds
        if key and value:
            return target.set(self._prefixed(key), value, ex=expire)
        else:
            result = []
            for key in kwargs:
                result.append(target.set(self._prefixed(key), kwargs[key], ex=expire))
            return result

    def _to_set(self, key, value, expire=None):
        target = self._transaction if self._in_transaction else self.rds
        target.sadd(self._prefixed(key), value)
        if expire:
            target.expire(self._prefixed(key), expire)

    def _count_set(self, key):
        return self.rds.scard(key)

    def _get_access_token(self):
        """ Get access_token or obtain it if possible """
        access_token = (
            self.server.data.get('access_token') or
            self._from_cache('access_token') or
            self.login()
        )
        return str(access_token)

    def api_call(self, method, path, data=None, json=None, suffix=None, auth=True, headers={}, cache_errors=True, cache_timeout=60*60*24):
        """ Performs an API call to homeserver.
        Last response data can be cached, if required.
        """
        suffix = suffix or "/_matrix/client/r0"
        url = "https://%s%s%s" % (self.server.hostname, suffix, path)
        if auth:
            access_token = self._get_access_token()
            headers['Authorization'] = 'Bearer %s' % access_token
        response = rs.request(method=method, url=url, data=data, json=json, headers=headers)
        if cache_errors and response.status_code != 200:
            now = datetime.datetime.now().strftime("%Y-%m-%d+%H:%m")
            self._to_cache(**{
                'response__%s__%s__%s' % (now, response.status_code, path): response.json(),
            }, expire=cache_timeout)
        return response

    def login(self):
        return login(self)

    def register(self, username=None, password=None):
        return continue_registration(self, username, password)

    def update_profile(self, visible_name=None, avatar_path=None):
        return update_profile(self, visible_name, avatar_path)

    def join(self, room_id):
        return join(self, room_id)

    def sync(self, filter_obj={}, since=None):
        return sync(self, filter_obj, since)

    def get_unique_messages(self, room_id, datestr):
        return get_unique_messages(self, room_id, datestr)

    def get_unique_members(self, room_id, datestr):
        return get_unique_members(self, room_id, datestr)

    def get_active_rooms(self, datestr):
        return get_active_rooms(self, datestr)

