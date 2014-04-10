import bson.errors
import bson.objectid
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
        print(result)
        self.redirect('/')


class DatabaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.db = self.settings['db']


class CounterHandler(DatabaseHandler):
    @gen.coroutine
    def get(self, object_id_string):
        try:
            object_id = bson.objectid.ObjectId(object_id_string)
        except bson.errors.InvalidId as e:
            self.finish(json_encode({'e': str(e)}))
            return

        try:
            counter = yield motor.Op(self.db.counters.find_one, {'_id': bson.objectid.ObjectId(object_id)})
            print(counter)
            if counter:
                self.finish(json_encode({'n': counter['n']}))
            else:
                self.finish(json_encode({'e': 'document with object_id %s does not exist' % object_id_string}))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))

    @gen.coroutine
    def post(self, object_id_string):
        try:
            object_id = bson.objectid.ObjectId(object_id_string)
        except bson.errors.InvalidId as e:
            self.finish(json_encode({'e': str(e)}))
            return

        try:
            result = yield motor.Op(self.db.counters.update, {'_id': object_id}, {'$inc': {'n': 1}})
            self.finish(json_encode(str(result)))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))


class CreateHandler(DatabaseHandler):
    @gen.coroutine
    def get(self):
        try:
            result = yield motor.Op(self.db.counters.insert, {'n': 0})
            self.finish(json_encode({'id': str(result)}))
        except Exception as e:
            self.finish(str(e))


class ResetHandler(DatabaseHandler):
    @gen.coroutine
    def get(self, object_id_string):
        try:
            object_id = bson.objectid.ObjectId(object_id_string)
        except bson.errors.InvalidId as e:
            self.finish(json_encode({'e': str(e)}))
            return

        try:
            result = yield motor.Op(self.db.counters.update, {'_id': object_id}, {'$set': {'n': 0}})
            self.finish(json_encode(str(result)))
        except Exception as e:
            self.finish(json_encode({'e': str(e)}))

