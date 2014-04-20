import time

import bson.errors
import bson.objectid
import pymongo.errors
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler


FAILOVER_TRIES = 40
FAILOVER_SLEEP = 0.25


class DatabaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.db = self.settings['db']


class CounterIDHandler(DatabaseHandler):
    def get_object_id(self, counter_id):
        return bson.objectid.ObjectId(counter_id)

    def write_error(self, status_code, **kwargs):
        if 'exc_info' in kwargs:
            typ, exc, tb = kwargs['exc_info']
            if isinstance(exc, bson.errors.InvalidId):
                self.finish({'err': str(exc)})
                return
        super().write_error(status_code, **kwargs)


class CounterHandler(CounterIDHandler):
    @gen.coroutine
    def get(self, collection, counter_id):
        object_id = self.get_object_id(counter_id)
        counter = yield self.db[collection].find_one({'_id': bson.objectid.ObjectId(object_id)})
        if counter:
            self.finish({'n': counter['n']})
        else:
            self.finish({'err': 'document with object_id %s does not exist' % counter_id})

    @gen.coroutine
    def increment_counter(self, collection, object_id, n):
        for i in range(FAILOVER_TRIES):
            try:
                result = yield self.db[collection].update({'_id': object_id}, {'$inc': {'n': int(n)}})
                return result
            except pymongo.errors.AutoReconnect:
                loop = IOLoop.instance()
                yield gen.Task(loop.add_timeout, time.time() + FAILOVER_SLEEP)

    @gen.coroutine
    def post(self, collection, counter_id, n):
        object_id = self.get_object_id(counter_id)
        if not n or not int(n):
            n = 1
        result = yield self.increment_counter(collection, object_id, n)
        self.finish({'resp': result['updatedExisting']})


class CreateHandler(DatabaseHandler):
    @gen.coroutine
    def create_counter(self, collection, data):
        for i in range(FAILOVER_TRIES):
            try:
                yield self.db[collection].insert(data)
                break
            except pymongo.errors.AutoReconnect:
                loop = IOLoop.instance()
                yield gen.Task(loop.add_timeout, time.time() + FAILOVER_SLEEP)
            except pymongo.errors.DuplicateKeyError:
                break
        else:
            raise Exception("Can't create new counter.")

    @gen.coroutine
    def post(self, collection):
        object_id = bson.objectid.ObjectId()
        data = {
            '_id': object_id,
            'n': 0
        }
        yield self.create_counter(collection, data)
        self.set_status(201)
        self.set_header('Location', '/%s/%s' % (collection, str(object_id)))
        self.finish({})


class ResetHandler(CounterIDHandler):
    @gen.coroutine
    def reset_counter(self, collection, object_id):
        for i in range(FAILOVER_TRIES):
            try:
                result = yield self.db[collection].update({'_id': object_id}, {'$set': {'n': 0}})
                return result
            except pymongo.errors.AutoReconnect:
                loop = IOLoop.instance()
                yield gen.Task(loop.add_timeout, time.time() + FAILOVER_SLEEP)

    @gen.coroutine
    def get(self, collection, counter_id):
        object_id = self.get_object_id(counter_id)
        result = yield self.reset_counter(collection, object_id)
        self.finish({'resp': result['updatedExisting']})
