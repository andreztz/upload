import os.path
import uuid
from StringIO import StringIO

from multipart import MultipartParser
import tornado.ioloop
import tornado.web
from tornado.web import url, StaticFileHandler
from tornado.options import parse_command_line

from tornado.gen import coroutine, sleep, Future
from tornado.web import asynchronous
import json
from tornado.websocket import WebSocketHandler


from upload.app import make_app
if __name__ == "__main__":
    parse_command_line()
    application = make_app()
    application.listen(8080, max_body_size=1024*1024*1024)
    tornado.ioloop.IOLoop.current().start()
