import json
import uuid

from tornado.websocket import WebSocketHandler


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


class PendingHandler(WebSocketHandler):
    def initialize(self, pending):
        self._pending = pending

    def open(self):
        upload_id = self.get_argument('id', uuid.uuid4().hex)
        listener = self._pending.get_listener(upload_id)
        listener.register_callback(self._progress)

    def _progress(self, data):
        self.write_message(json.dumps(data))
