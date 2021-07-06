import dataclasses
import datetime
import enum
import hashlib
import heapq
import json
import os
import sqlite3
import sys
import time

import requests


config_hash = None
config_success = None


class CronFlag(enum.Enum):
    stop = enum.auto()


@dataclasses.dataclass
class HeimdallItem:
    name: str
    image_url: str
    url: str
    color: str

    @staticmethod
    def from_dict(d):
        return HeimdallItem(name=d['name'], image_url=d['image_url'], url=d['url'], color=d['color'])


def install_apps():
    global config_hash, config_success

    app_config_root = os.environ['HEIMDALL_SIDECAR_CONFIG_PATH']
    app_config_file = os.path.join(app_config_root, 'apps.json')
    with open(app_config_file, 'r') as in_f:
        app_config_data = in_f.read()

    config_hash_test_digest = hashlib.sha256()
    config_hash_test_digest.update(app_config_data.encode('utf-8'))
    config_hash_test = config_hash_test_digest.hexdigest()

    if config_hash is None or config_success is None or config_hash != config_hash_test:
        app_config = [HeimdallItem.from_dict(item) for item in json.loads(app_config_data)]
        config_hash = config_hash_test
        config_success = None
    else:
        return

    try:
        print('Installing new items', file=sys.stderr)

        heimdall_db_file = '/config/www/app.sqlite'
        assert os.path.isfile(heimdall_db_file)

        db = sqlite3.connect(heimdall_db_file)
        for app in app_config:
            heimdall_try_install(db, app)

        db.commit()
        config_success = True

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)


def heimdall_try_install(db: sqlite3.Connection, app: HeimdallItem):
    '''
    e.g.
    | id | title  | colour  | icon             | url                     | description                                                               | pinned | order | deleted_at | created_at          | updated_at          | type | user_id | class                            |
    | 1  | Deluge | #161b1f | icons/deluge.png | http://deluge.k8s.local | {"enabled":true,"override_url":"http:\/\/deluge","password":"cirno9ball"} | 1      | 0     |            | 2021-07-06 01:40:28 | 2021-07-06 01:40:28 | 0    | 1       | \App\SupportedApps\Deluge\Deluge |
    '''
    print(f'Installing {app.name} with url {app.url}', file=sys.stderr)

    cur = db.cursor()
    cur.execute('SELECT id FROM items WHERE title = ?', (app.name,))
    res = cur.fetchall()
    if res:
        print(f'Res is {res}')
        print(f'Already found {app.name}, skipping', file=sys.stderr)
        return

    if app.image_url:
        ext = app.image_url.split('.')[-1]
        image_key = f'icons/{app.name.lower()}.{ext}'
        image_fpath = f'/config/www/{image_key}'

        image_r = requests.get(app.image_url)
        with open(image_fpath, 'wb') as out_f:
            out_f.write(image_r.content)
    else:
        if os.path.isfile(f'/config/www/icons/{app.name.lower()}.svg'):
            image_key = f'icons/{app.name.lower()}.svg'
        elif os.path.isfile(f'/config/www/icons/{app.name.lower()}.png'):
            image_key = f'icons/{app.name.lower()}.png'
        else:
            image_key = None

    cur.execute(
        'INSERT INTO items (title, colour, icon, url, pinned, description, created_at, updated_at, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (app.name, app.color, image_key, app.url, 1, '{}', datetime.datetime.now(), datetime.datetime.now(), 0)
    )
    cur.execute('SELECT id FROM items WHERE title = ?', (app.name,))
    item_id = cur.fetchall()[0][0]
    cur.execute('INSERT INTO item_tag (item_id, tag_id) VALUES (?, ?)', (item_id, 0))  # ???
    print(f'Installed {app.name}', file=sys.stderr)


def cycle_background():
    pass


def cron(tab):
    _epsilon = datetime.timedelta(seconds=0.1)

    now = datetime.datetime.now()
    intervals = [
        (now, interval, fn)
        for fn, interval in tab
    ]
    schedule = []
    for item in sorted(intervals):
        heapq.heappush(schedule, item)

    while True:
        wakeup = datetime.datetime.now()
        sched, interval, fn = heapq.heappop(schedule)
        wait = (sched - wakeup).total_seconds()
        if wait > 0:
            time.sleep(wait)
        res = fn()
        if res != CronFlag.stop:
            heapq.heappush(schedule, (sched + interval, interval, fn))


def main():
    cron([
        (install_apps, datetime.timedelta(seconds=60)),
        (cycle_background, datetime.timedelta(days=1)),
    ])


if __name__ == '__main__':
    main()
