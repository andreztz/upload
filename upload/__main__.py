import tornado.ioloop
from tornado.options import parse_command_line, define, options

from upload.app import make_app


define('port', default=8080, type=int, help="Port to listen on")
define('max_body_size', type=int, default=1024*1024*1024,
    help="Max accepted size of the http request body")

if __name__ == "__main__":
    parse_command_line()
    application = make_app()
    application.listen(8080, max_body_size=1024*1024*1024)
    tornado.ioloop.IOLoop.current().start()
