import uuid

import tornado.web

from upload.receiver import FormDataReceiver, DumpingReceiver
from upload.util import parse_header_options


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
