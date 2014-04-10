import os

import motor
import tornado.httpserver
import tornado.ioloop
from tornado.options import define, options, parse_command_line

from handlers import TestHandler, CounterHandler, CreateHandler, ResetHandler

define("port", default=8888, help="run on the given port", type=int)


def main():
    parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', TestHandler),
            (r'/counters/?', CreateHandler),
            (r'/counters/([a-zA-Z0-9]+)/?', CounterHandler),
            (r'/counters/([a-zA-Z0-9]+)/reset/?', ResetHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
    )

    server = tornado.httpserver.HTTPServer(application)
    server.bind(options.port)
    server.start(0)

    db = motor.MotorReplicaSetClient(replicaSet='foo').open_sync().test_db

    application.settings['db'] = db
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()