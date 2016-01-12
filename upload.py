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



class ReceivedPart(object):
    def __init__(self):
        self._sink = self.get_sink()

    def get_sink(self):
        raise NotImplementedError()

    def data_received(self, data):
        self._sink.write(data)

    def finish(self):
        self._sink.close()


class ReceivedFile(ReceivedPart):
    def __init__(self, filename):
        self._filename = filename
        self._sink = open(filename, 'w')

    def data_received(self, data):
        self._sink.write(data)

    def finish(self):
        self._sink.close()


class ReceivedField(ReceivedPart):
    def get_sink(self):
        return StringIO()

    def finish(self):
        pass

class DescriptionField(ReceivedField):
    def get_data(self):
        return json.loads(self._sink.getvalue())

from collections import Mapping
class HeadersGatherer(Mapping):
    def __init__(self):
        self._current_header = ''
        self._current_header_value = ''
        self.headers = {}

    def on_header_field(self, data, start, end):
        self._current_header += data[start:end]

    def on_header_value(self, data, start, end):
        self._current_header_value += data[start:end]

    def on_header_end(self):
        header = self._current_header.lower()
        value = self._current_header_value
        self.headers[header] = value
        self._current_header = ''
        self._current_header_value = ''

    def __getitem__(self, k):
        return self.headers[k]

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

    def clear(self):
        self.headers = {}

class FormDataReceiver(object):
    def __init__(self, listener, boundary, **kwargs):
        self._listener = listener
        self.headers = HeadersGatherer()
        self.parser = MultipartParser(boundary, {
            'on_part_begin': self.on_part_begin,
            'on_part_data': self.on_part_data,
            'on_part_end': self.on_part_end,
            'on_header_field': self.headers.on_header_field,
            'on_header_value': self.headers.on_header_value,
            'on_header_end': self.headers.on_header_end,
            'on_headers_finished': self.on_headers_finished
        })
        self._parts_received = {}
        self._current = None
        self._current_name = None

    def data_received(self, data):
        self.parser.write(data)

    def finish(self):
        self._listener.finish()

    def on_part_begin(self):
        self.headers.clear()

    def on_part_data(self, data, start, end):
        if self._current is not None:
            self._current.data_received(data[start:end])

        total = None
        if self._current_name == 'upload' and 'filesize' in self._parts_received:
            desc = self._parts_received['filesize'].get_data()
            filename = self._current._filename
            total = desc[filename]
            self._listener.file_part_received(filename, end-start, total)

    def on_part_end(self):
        self._current.finish()
        self._current = None

    def on_headers_finished(self):
        disposition_header = self.headers['content-disposition']
        disposition, options = parse_header_options(disposition_header)
        if disposition == 'form-data':
            input_name = options.pop('name')
            field_class = {
                'upload': ReceivedFile,
                'filesize': DescriptionField
            }.get(input_name)
            self._current = field_class(**options)
            self._current_name = input_name
            self._parts_received[input_name] = self._current


class NotifyingFormDataReceiver(FormDataReceiver):
    def __init__(self, upload_id, *args, **kwargs):
        self.id = upload_id

class DumpingReceiver(object):
    def __init__(self, listener):
        self._listener = listener
        self.length = None
        self._received_bytes = 0


def parse_header_options(header):
    if not header:
        return None, {}
    parts = header.split(';')
    content_type, opts = parts[0].lower(), parts[1:]
    options = {k.strip(): v.strip('"')
        for k, sep, v in
        (option.partition('=') for option in opts)
    }
    return content_type, options

from tornado.gen import coroutine, sleep, Future
from tornado.web import asynchronous
import json
from tornado.websocket import WebSocketHandler


class PendingHandler(WebSocketHandler):
    def initialize(self, pending):
        self._pending = pending

    def open(self):
        upload_id = self.get_argument('id', uuid.uuid4().hex)
        listener = self._pending.get_listener(upload_id)
        listener.register_callback(self._progress)

    def _progress(self, data):
        self.write_message(json.dumps(data))


@tornado.web.stream_request_body
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, pending):
        self._pending = pending

    def data_received(self, data):
        self.receiver.data_received(data)

    def prepare(self):
        content_type_header = self.request.headers.get('content-type')
        content_type, opts = parse_header_options(content_type_header)
        receiver_class = {
            'multipart/form-data': FormDataReceiver,
        }.get(content_type, DumpingReceiver)

        upload_id = self.get_argument('id', uuid.uuid4().hex)
        try:
            length = int(self.request.headers['content-length'])
        except (ValueError, KeyError):
            pass
        listener = self._pending.get_listener(upload_id)
        self.receiver = receiver_class(listener, **opts)

    def post(self):
        self.receiver.finish()
        self.get()

    def get(self):
        new_id = uuid.uuid4().hex
        self.render('index.html', new_id=new_id)


class ProgressListener(object):
    def __init__(self, upload_id):
        self.id = upload_id
        self.length = None
        self._received_bytes = 0
        self._callbacks = set()
        self._files = {}

    def data_received(self, count):
        self._received_bytes += count
        self._run_callbacks()

    def file_part_received(self, filename, count, total):
        if filename not in self._files:
            self._files[filename] = [count, total]
        else:
            self._files[filename][0] += count
        self._run_callbacks()

    def register_callback(self, cb):
        self._callbacks.add(cb)

    def unregister_callback(self, cb):
        self._callbacks.remove(cb)

    def get_current_data(self):
        return {
            'total': [self._received_bytes, self.length],
            'files': self._files
        }

    def _run_callbacks(self):
        data = self.get_current_data()
        for cb in self._callbacks:
            cb(data)

    def finish(self):
        self._files = {}


class Pending(object):
    def __init__(self):
        self._listeners = {}

    def get_listener(self, upload_id):
        return self._listeners.setdefault(upload_id, ProgressListener(upload_id))


def make_app():
    pending = Pending()
    application = tornado.web.Application([
        url(r"/", MainHandler, {'pending': pending}, name='upload'),
        url(r'/static/(.*)', StaticFileHandler, {'path': 'static'}),
        url(r'/pending', PendingHandler, {'pending': pending})
    ], debug=True, template_path='templates')
    return application


if __name__ == "__main__":
    parse_command_line()
    application = make_app()
    application.listen(8080, max_body_size=1024*1024*1024)
    tornado.ioloop.IOLoop.current().start()
