import time

import bson
import bson.objectid
import bson.errors
import tornado.escape
from tornado.websocket import WebSocketHandler
from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from tornado import gen


class TailHandler(WebSocketHandler):
    listeners = {}

    def open(self, counter_id):
        self.subscriptions = []
        if counter_id:
            cid = counter_id.decode('utf-8')
            self.subscriptions.append(cid)
            TailHandler.listeners.setdefault(cid, set()).add(self)

    def on_message(self, message):
        """Sockets can subscribe to more than one object_id.
        Sending {'<counter_id>': 's'} subscribes and {'<counter_id>': 'u'} un subscribes."""
        try:
            parsed = tornado.escape.json_decode(message)
        except:
            parsed = {}

        actions = {
            's': self.subscribe,
            'u': self.un_subscribe,
        }
        for key in parsed:
            actions.get(parsed[key], lambda x: None)(key)

    def on_close(self):
        for sub in self.subscriptions:
            self.un_subscribe(sub)

    def subscribe(self, counter_id):
        try:
            bson.objectid.ObjectId(counter_id)
        except bson.errors.InvalidId:
            return

        self.subscriptions.append(counter_id)
        TailHandler.listeners.setdefault(counter_id, set()).add(self)

    def un_subscribe(self, counter_id):
        TailHandler.listeners.get(counter_id, set()).discard(self)
        if not TailHandler.listeners.get(counter_id, 1):
            del TailHandler.listeners[counter_id]


def handle_update(obj):
    try:
        object_id = str(obj['o2']['_id'])
        n = int(obj['o']['$set']['n'])
    except KeyError:
        # TODO: real logging
        print(obj)
        return

    for socket in TailHandler.listeners.get(object_id, []):
        socket.write({'id': object_id, 'n': n})


def handle_delete(obj):
    try:
        object_id = str(obj['o'])
    except KeyError:
        # TODO: real logging
        print(obj)
        return

    for socket in TailHandler.listeners.get(object_id, []):
        socket.write(socket.write({'id': object_id, 'd': 1}))
        socket.subscriptions.discard(object_id)

    del TailHandler.listeners[object_id]


@gen.coroutine
def start_stream(db):
    print("start stream")
    oplog = db['oplog.rs']
    now = bson.Timestamp(int(time.time()), 1)
    cursor = oplog.find({'ts': {'$gte': now}}, tailable=True, await_data=True)
    while True:
        if not cursor.alive:
            # While collection is empty, tailable cursor dies immediately
            loop = IOLoop.instance()
            now = bson.Timestamp(int(time.time()), 1)
            yield gen.Task(loop.add_timeout, time.time() + 0.5)
            cursor = oplog.find({'ts': {'$gte': now}}, tailable=True, await_data=True)

        if (yield cursor.fetch_next):
            obj = cursor.next_object()
            actions = {
                'u': handle_update,
                'd': handle_delete,
            }
            actions.get(obj['op'], lambda x: None)(obj)


class TestSocketHandler(RequestHandler):
    def get(self):
        self.render("index.html")
