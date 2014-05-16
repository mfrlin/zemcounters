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


class TestHandlers(TestHandlerBase):
    def test_create_counters_in_different_collections(self):
        test_names = ['/counters/', '/random/', '/123_a/']
        for name in test_names:
            self.http_client.fetch(self.get_url(name), self.stop, body="123", method='POST')
            response = self.wait()
            response.rethrow()
            self.assertEqual(response.code, 201)
            self.assertTrue(
                response.headers['Location'].startswith(name),
                "response.headers['Location'] did not start with %s" % name)

    def test_increment_counter(self):
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

    def test_increment_counter_by_different_values(self):
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

    def test_reset_counter(self):
        self.http_client.fetch(self.get_url('/counters/'), self.stop, body="123", method='POST')
        response = self.wait()
        location = response.headers['Location']
        for i in range(23):
            self.http_client.fetch(self.get_url(location + '/' + str(i)), self.stop, body="123", method='POST')
            self.wait()

        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        response = self.wait()
        counter_value = json.loads(response.body.decode('utf-8'))['n']
        self.assertNotEqual(counter_value, 0)

        self.http_client.fetch(self.get_url(location + '/reset'), self.stop, body="123", method='POST')
        self.wait()
        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        response = self.wait()
        counter_value = json.loads(response.body.decode('utf-8'))['n']
        self.assertEqual(counter_value, 0)

    def test_404_on_counter_not_found(self):
        location = '/fakecounterdir/fakecountername12345678'

        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        request = self.wait()
        self.assertEqual(request.code, 404)

        self.http_client.fetch(self.get_url(location), self.stop, method='POST', body='123')
        request = self.wait()
        self.assertEqual(request.code, 404)

        self.http_client.fetch(self.get_url(location+'/12'), self.stop, method='POST', body='123')
        request = self.wait()
        self.assertEqual(request.code, 404)

        self.http_client.fetch(self.get_url(location+'/reset'), self.stop, method='POST', body='123')
        request = self.wait()
        self.assertEqual(request.code, 404)

        self.http_client.fetch(self.get_url(location), self.stop, method='DELETE')
        request = self.wait()
        self.assertEqual(request.code, 404)

    def test_delete_counter(self):
        self.http_client.fetch(self.get_url('/counters/'), self.stop, body="123", method='POST')
        response = self.wait()
        location = response.headers['Location']
        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        response = self.wait()
        self.assertEqual(response.code, 200)

        self.http_client.fetch(self.get_url(location), self.stop, method='DELETE')
        response = self.wait()
        self.assertEqual(response.code, 200)

        self.http_client.fetch(self.get_url(location), self.stop, method='GET')
        response = self.wait()
        self.assertEqual(response.code, 404)




