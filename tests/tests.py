import os
import sys
import json

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
    for collection in sync_db.collection_names(include_system_collections=False):
        sync_db.drop_collection(collection)


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
            self.http_client.fetch(self.get_url(name), self.stop, body="123", method='POST')
            response = self.wait()
            response.rethrow()
            self.assertEqual(response.code, 201)
            self.assertTrue(
                response.headers['Location'].startswith(name),
                "response.headers['Location'] did not start with %s" % name)

    def increment_counter_test(self):
        self.http_client.fetch(self.get_url('/counters/'), self.stop, body="123", method='POST')
        response = self.wait()
        location = response.headers['Location']
        times_to_inc = 100
        for i in range(times_to_inc):
            self.http_client.fetch(self.get_url(location), self.stop, body="123", method='POST')
            self.wait()

        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        response = self.wait()
        counter_value = json.loads(response.body.decode('utf-8'))['n']
        self.assertEqual(counter_value, times_to_inc)

    def increment_counter_by_different_values_test(self):
        self.http_client.fetch(self.get_url('/counters/'), self.stop, body="123", method='POST')
        response = self.wait()
        location = response.headers['Location']
        times_to_inc = 10
        prev_counter_value = 0
        for i in range(times_to_inc):
            self.http_client.fetch(self.get_url(location + '/' + str(i)), self.stop, body="123", method='POST')
            self.wait()
            self.http_client.fetch(self.get_url(location), self.stop, method='GET')
            response = self.wait()
            counter_value = json.loads(response.body.decode('utf-8'))['n']
            self.assertEqual(counter_value, prev_counter_value + i)
            prev_counter_value = counter_value



