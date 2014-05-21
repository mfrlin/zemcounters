import time

import bson

from tornado.websocket import WebSocketHandler
from tornado.web import RequestHandler
from tornado.ioloop import IOLoop
from tornado import gen


class TailHandler(WebSocketHandler):
    listeners = {}

    def open(self, counter_id):
        cid = counter_id.decode('utf-8')
        self.subscriptions = [cid]
        TailHandler.listeners.setdefault(cid, set()).add(self)

    def on_message(self, message):
        """Sockets can subscribe to more than one object_id."""

        if len(message) != 24:  # bogus namespace
            return
        self.subscriptions.append(message)
        TailHandler.listeners.setdefault(message, set()).add(self)

    def on_close(self):
        for sub in self.subscriptions:
            TailHandler.listeners.get(sub, set()).discard(self)
            if not TailHandler.listeners.get(sub, 1):
                del TailHandler.listeners[sub]


def handle_update(obj):
    try:
        object_id = str(obj['o2']['_id'])
        n = int(obj['o']['$set']['n'])
    except KeyError as e:
        # TODO: real logging
        print(obj)
        return

    for socket in TailHandler.listeners.get(object_id, []):
        socket.write({'_id': object_id, 'n': n})


def handle_delete(obj):
    try:
        object_id = str(obj['o'])
    except KeyError as e:
        # TODO: real logging
        print(obj)
        return

    for socket in TailHandler.listeners.get(object_id, []):
        socket.write(socket.write({'_id': object_id, 'd': 1}))
        socket.subscription.discard(object_id)
        if not socket.subscriptions:
            socket.close()

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
