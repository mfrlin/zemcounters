import bson.errors
import bson.objectid
from bson.json_util import dumps
import motor
from tornado import gen
from tornado.escape import json_encode
from tornado.web import RequestHandler


class TestHandler(RequestHandler):
    @gen.coroutine
    def get(self):
        db = self.settings['db']
        document = yield motor.Op(db.counters.find_one, {'_id': "test_object"})
        self.render("index.html", counter=str(document))

    @gen.coroutine
    def post(self):
        db = self.settings['db']
        result = yield motor.Op(db.counters.update, {'_id': "test_object"}, {'$inc': {'n': 1}}, upsert=True)
        self.redirect('/')


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
                self.finish(json_encode({'e': str(exc)}))
                return
        super().write_error(status_code, **kwargs)


class CounterHandler(CounterIDHandler):
    @gen.coroutine
    def get(self, collection, counter_id, *args):
        object_id = self.get_object_id(counter_id)
        try:
            counter = yield motor.Op(self.db[collection].find_one, {'_id': bson.objectid.ObjectId(object_id)})
            print(counter)
            if counter:
                self.finish(json_encode({'n': counter['n']}))
            else:
                self.finish(json_encode({'e': 'document with object_id %s does not exist' % counter_id}))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))

    @gen.coroutine
    def post(self, collection, counter_id, n):
        object_id = self.get_object_id(counter_id)
        try:
            if not n or not int(n):
                n = 1
            result = yield motor.Op(self.db[collection].update, {'_id': object_id}, {'$inc': {'n': int(n)}})
            self.finish(json_encode(str(result)))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))


class CreateHandler(DatabaseHandler):
    @gen.coroutine
    def get(self, collection):
        try:
            result = yield motor.Op(self.db[collection].insert, {'n': 0})
            self.finish(json_encode({'id': str(result)}))
        except Exception as e:
            self.finish(str(e))


class ResetHandler(CounterIDHandler):
    @gen.coroutine
    def get(self, collection, counter_id):
        object_id = self.get_object_id(counter_id)
        try:
            result = yield motor.Op(self.db[collection].update, {'_id': object_id}, {'$set': {'n': 0}})
            self.finish(dumps(result))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))

