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

from upload.progress import Pending, PendingHandler
from upload.web import MainHandler

def make_app():
    pending = Pending()
    application = tornado.web.Application([
        url(r"/", MainHandler, {'pending': pending}, name='upload'),
        url(r'/static/(.*)', StaticFileHandler, {'path': 'static'}),
        url(r'/pending', PendingHandler, {'pending': pending})
    ], debug=True, template_path='templates')
    return application
