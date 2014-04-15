import os

import motor
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options, parse_command_line

from handlers import CounterHandler, CreateHandler, ResetHandler

define("port", default=8888, help="run on the given port", type=int)
define("mongodb_hosts", default="127.0.0.1:27017", type=str,
       help="host names for mongodb replica set")
define("mongodb_replica", default="foo", type=str,
       help="mongodb replica set name")
define("mongodb_db", default="test_db", type=str,
       help="mongodb database name")


def main():
    parse_command_line()
    application = tornado.web.Application(
        [
            (r'/([\w]{1,128})/', CreateHandler),
            (r'/([\w]{1,128})/([a-zA-Z0-9]{24})/?([0-9]+)?', CounterHandler),
            (r'/([\w]{1,128})/([a-zA-Z0-9]{24})/reset', ResetHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "../templates"),
    )

    server = tornado.httpserver.HTTPServer(application)
    server.bind(options.port)
    server.start(0)

    db = motor.MotorReplicaSetClient(options.mongodb_hosts,
                                     replicaSet=options.mongodb_replica).open_sync()[options.mongodb_db]

    application.settings['db'] = db
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()