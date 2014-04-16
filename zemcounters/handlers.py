import bson.errors
import bson.objectid
from tornado import gen
from tornado.web import RequestHandler


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
    def get(self, collection, counter_id, *args):
        object_id = self.get_object_id(counter_id)
        try:
            counter = yield self.db[collection].find_one({'_id': bson.objectid.ObjectId(object_id)})
            if counter:
                self.finish({'n': counter['n']})
            else:
                self.finish({'err': 'document with object_id %s does not exist' % counter_id})
        except Exception as e:
            self.finish({'err': str(e)})

    @gen.coroutine
    def post(self, collection, counter_id, n):
        object_id = self.get_object_id(counter_id)
        try:
            if not n or not int(n):
                n = 1
            result = yield self.db[collection].update({'_id': object_id}, {'$inc': {'n': int(n)}})
            self.finish({'resp': result['updatedExisting']})
        except Exception as e:
            self.finish({'err': str(e)})


class CreateHandler(DatabaseHandler):
    @gen.coroutine
    def post(self, collection):
        try:
            print(self.db)
            object_id = yield self.db[collection].insert({'n': 0})
            print("after")
            self.set_status(201)
            self.set_header('Location', '/%s/%s' % (collection, object_id))
            self.finish({})
        except Exception as e:
            self.finish({'err': str(e)})


class ResetHandler(CounterIDHandler):
    @gen.coroutine
    def get(self, collection, counter_id):
        object_id = self.get_object_id(counter_id)
        try:
            result = yield self.db[collection].update({'_id': object_id}, {'$set': {'n': 0}})
            self.finish({'resp': result['updatedExisting']})
        except Exception as e:
            self.finish({'err': str(e)})

