import os
import sys

import motor
import pymongo.errors
import tornado.testing
import tornado.ioloop

#  Importing app from zemcounters.server
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../zemcounters'))
sys.path.append(APP_ROOT)
from server import application

db = motor.MotorReplicaSetClient('localhost', replicaSet='foo')['test_db']
application.settings['db'] = db

sync_db = pymongo.MongoReplicaSetClient(replicaSet='foo')['test_db']


def clear_db():
    for collection in sync_db.collection_names():
        try:
            sync_db.drop_collection(collection)
        except pymongo.errors.OperationFailure:  # we can't drop system namespaces like indexes etc
            pass


class TestHandlerBase(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return application

    def setUp(self):
        clear_db()
        super().setUp()

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()


class TestCreateHandler(TestHandlerBase):
    def create_counters_in_different_collections_test(self):
        test_names = ['/counters/', '/random/', '/123_a/']
        for name in test_names:
            #response = self.fetch(name, body="123", method='POST')
            self.http_client.fetch(self.get_url(name), self.stop, body="123", method='POST')
            response = self.wait()
            response.rethrow()
            self.assertEqual(response.code, 201)
            self.assertTrue(
                response.headers['Location'].startswith(name),
                "response.headers['Location'] did not start with %s" % name)