# coding: utf-8

"""Infrastructure for notifying the clients of upload progress

The JS upload client will connect to the WebSocketHandler defined in
this module, register with a ProgressListener, and wait for progress
notifications.

Uploads update their progress by calling the file_part_received or
data_received methods on a ProgressListener.

Note: for this to work, there needs to be a way to figure out which
websocket connection corresponds to which upload. For this, both the
websocket connection, and the upload, use urls containing a server-generated
id in the querystring.
"""


import json
import uuid

from tornado.websocket import WebSocketHandler


class ProgressListener(object):
    """Passes through progress notifications

    When received a content-length, set the .length attribute on this.
    When received some data, call data_received with the length of the
    received part.
    When received part of a file with a known filename, eg. as part
    of a multipart/form-data message, call the file_part_received method.

    This will then notify the callbacks that were registered via the
    register_callback method.
    """
    # XXX debounce the notifications
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
        """Notify of receiving a file part, most likely in a multipart message

        Args:
            filename (str): the name of the file transmitted, if known
            count (int): length of the received fragment
            total (int): total length of the file, if known
        """
        # note, total is usually only sent when uploading from the js app;
        # otherwise there's no way to know how long the parts of a multipart
        # message will be
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
    """Controller/container for getting ProgressListeners for a given id"""
    # note: this approach isn't multiprocess-friendly; if we ever wanted that,
    # ProgressListeners would need to communicate over some sort of external
    # message bus
    def __init__(self):
        self._listeners = {}

    def get_listener(self, upload_id):
        """Get a ProgressListener for this upload. It might or might not be
        already existing, already connected, etc.

        Args:
            upload_id (str): the server-generated id for the upload
        Returns:
            ProgressListener
        """
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
