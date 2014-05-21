import os

import motor
import tornado.httpserver
import tornado.ioloop
import tornado.web
from pymongo.read_preferences import ReadPreference
from tornado.options import define, options, parse_command_line

from handlers import CounterHandler, CreateHandler, ResetHandler
import tailer

define("port", default=8888, help="run on the given port", type=int)
define("mongodb_hosts", default="127.0.0.1:27017", type=str,
       help="host names for mongodb replica set")
define("mongodb_replica", default="foo", type=str,
       help="mongodb replica set name")
define("mongodb_db", default="test_db", type=str,
       help="mongodb database name")

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
)

application = tornado.web.Application(
    [
        (r'/([\w]{1,128})/', CreateHandler),
        (r'/([\w]{1,128})/([a-zA-Z0-9]{24})/?([0-9]+)?', CounterHandler),
        (r'/([\w]{1,128})/([a-zA-Z0-9]{24})/reset', ResetHandler),
        (r'/tail/([0-9]+)', tailer.TailHandler),
        (r'/test-socket', tailer.TestSocketHandler),
    ],
    **settings)


def main():
    parse_command_line()
    server = tornado.httpserver.HTTPServer(application)
    server.bind(options.port)
    server.start(0)

    conn = motor.MotorReplicaSetClient(
        options.mongodb_hosts,
        replicaSet=options.mongodb_replica
    )

    db = conn[options.mongodb_db]
    db.read_preference = ReadPreference.PRIMARY_PREFERRED
    application.settings['db'] = db

    local_db = conn['local']
    tailer.start_stream(local_db)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()