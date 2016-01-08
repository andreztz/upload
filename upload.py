import os.path
import uuid
from StringIO import StringIO

from multipart import MultipartParser
import tornado.ioloop
import tornado.web
from tornado.web import url, StaticFileHandler
from tornado.options import parse_command_line


class ReceivedPart(object):
    def __init__(self):
        self.headers = {}
        self._sink = None

    @property
    def filename(self):
        disposition_header = self.headers.get('content-disposition')
        content_disposition, opts = parse_header_options(disposition_header)
        try:
            filename = opts['filename']
        except KeyError:
            return None
        else:
            return filename.strip('"\'')

    @property
    def is_file(self):
        return self.filename is not None

    @property
    def sink(self):
        if self._sink is None:
            if self.is_file:
                self._sink = open(os.path.join('uploaded', self.filename), 'w')
            else:
                self._sink = StringIO()
        return self._sink

    def data_received(self, data):
        self.sink.write(data)

    def finish(self):
        self.sink.close()


class FormDataReceiver(object):
    def __init__(self, boundary, **kwargs):
        self.parser = MultipartParser(boundary, {
            'on_part_begin': self.on_part_begin,
            'on_part_data': self.on_part_data,
            'on_part_end': self.on_part_end,
            'on_header_field': self.on_header_field,
            'on_header_value': self.on_header_value,
            'on_header_end': self.on_header_end,
            'on_headers_finished': self.on_headers_finished
        })
        self._parts_received = []
        self._current = None
        self._current_header = ''
        self._current_header_value = ''

    def data_received(self, data):
        self.parser.write(data)

    def finish(self):
        pass

    def on_part_begin(self):
        self._current = ReceivedPart()
        self._parts_received.append(self._current)

    def on_part_data(self, data, start, end):
        self._current.data_received(data[start:end])

    def on_part_end(self):
        self._current.finish()

    def on_header_field(self, data, start, end):
        self._current_header += data[start:end]

    def on_header_value(self, data, start, end):
        self._current_header_value += data[start:end]

    def on_header_end(self):
        header = self._current_header.lower()
        value = self._current_header_value
        self._current.headers[header] = value
        self._current_header = ''
        self._current_header_value = ''

    def on_headers_finished(self):
        pass


class DumpingReceiver(object):
    pass


def parse_header_options(header):
    if not header:
        return None, {}
    parts = header.split(';')
    content_type, opts = parts[0].lower(), parts[1:]
    options = {k.strip(): v
        for k, sep, v in
        (option.partition('=') for option in opts)
    }
    return content_type, options

@tornado.web.stream_request_body
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, pending):
        self._pending = pending

    def data_received(self, data):
        self.receiver.data_received(data)

    def prepare(self):
        print 'headers', dict(self.request.headers)
        content_type_header = self.request.headers.get('content-type')
        content_type, opts = parse_header_options(content_type_header)
        receiver_class = {
            'multipart/form-data': FormDataReceiver,
        }.get(content_type, DumpingReceiver)
        self.receiver = receiver_class(**opts)

    def post(self):
        self.receiver.finish()
        self.get()

    def get(self):
        new_id = uuid.uuid4().hex
        self.render('index.html', new_id=new_id)

class Pending(object):
    pass

def make_app():
    pending = Pending()
    application = tornado.web.Application([
        url(r"/", MainHandler, {'pending': pending}, name='upload'),
        url(r'/static/(.*)', StaticFileHandler, {'path': 'static'})
    ], debug=True, template_path='templates')
    return application

if __name__ == "__main__":
    parse_command_line()
    application = make_app()
    application.listen(8080, max_body_size=1024*1024*1024)
    tornado.ioloop.IOLoop.current().start()
