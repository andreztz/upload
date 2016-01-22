import os.path

import tornado.web
from tornado.web import url, StaticFileHandler, Application

from upload.progress import Pending, PendingHandler
from upload.web import MainHandler


def make_app():
    pending = Pending()
    application = Application([
        url(r"/", MainHandler, {'pending': pending}, name='upload'),
        url(r'/static/(.*)', StaticFileHandler, {'path': 'static'}),
        url(r'/pending', PendingHandler, {'pending': pending})
    ], debug=True, template_path='templates')
    return application
