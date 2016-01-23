from collections import Mapping
import json
import uuid
from six import StringIO

from multipart import MultipartParser

from upload.util import parse_header_options


class ReceivedPart(object):
    """Store incoming field data

    FormDataReceiver will pass data for one field to ReceivedPart implementors.

    Examine header options passed as kwargs to __init__, choose where to store
    the incoming data, and write it when received a part in the data_received
    method.
    """
    def __init__(self):
        self._sink = self.get_sink()

    def get_sink(self):
        raise NotImplementedError()

    def data_received(self, data):
        """
        """
        self._sink.write(data)

    def finish(self):
        self._sink.close()


class ReceivedFile(ReceivedPart):
    """A ReceivedPart that stores incoming data in a disk file

    Args:
        filename (str): the name to save the file as.
            If it already exists, a uuid4 will be added to the name.
    """
    def __init__(self, filename):
        self._filename = filename
        self._original_filename = filename
        super(ReceivedFile, self).__init__()

    def get_sink(self):
        # XXX maybe parametrize if you should be able to overwrite files?
        while True:
            try:
                return open(self._filename, 'wx')
            except OSError as e:
                self._filename = '%s.%s' % (self._original_filename, uuid.uuid4().hex)

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
    """A ReceivedPart to store json data

    Used for the filesize description field sent from the js uploader app
    """
    def get_data(self):
        return json.loads(self._sink.getvalue())


class HeadersGatherer(Mapping):
    """Gather incoming header data into a mapping.

    This exposes 3 methods that are to be used as python-multipart's callbacks:
    on_header_field, on_header_value, on_header_end.

    At any point use this as a mapping to access received headers.
    """
    def __init__(self):
        self._current_header = b''
        self._current_header_value = b''
        self.headers = {}

    # the start/end parameters are as expected by python-multipart;
    # these methods need to slice the data themselves
    def on_header_field(self, data, start, end):
        self._current_header += data[start:end]

    def on_header_value(self, data, start, end):
        self._current_header_value += data[start:end]

    def on_header_end(self):
        header = self._current_header.decode('latin-1').lower()
        value = self._current_header_value.decode('latin-1')
        self.headers[header] = value
        self._current_header = b''
        self._current_header_value = b''

    def __getitem__(self, k):
        return self.headers[k.lower()]

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

    def clear(self):
        self.headers = {}


def _choose_input(disposition, options):
    """Examine the content-disposition and value, and choose the fieldname, and
    field class to parse the incoming data.

    Args:
        disposition (str): content-disposition as retrieved from the header
        options (dict):

    Returns:
        (tuple): tuple containing
            input_name (str): name of the field we're processing
            receiver : pass the incoming data into this for storage

    """
    input_name = options.pop('name', None)
    field_class = {
        'upload': ReceivedFile,
        'filesize': DescriptionField
    }.get(input_name)
    if field_class is None and 'filename' in options:
        field_class = ReceivedFile
    return (input_name, field_class(**options))


class FormDataReceiver(object):
    """Handle incoming multipart/form-data, and route it to storage classes.

    This is the main data receiver, to be used from within a RequestHandler.
    Keep pushing incoming multipart data into its data_received method, and
    remember to call finish() when done.

    Args:
        listener (ProgressListener): the listener to be notified
            of upload progress
        boundary (str): multipart mimetype boundary
    """
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
        if self._current is not None:
            self._current.finish()
            self._current = None

    def on_headers_finished(self):
        disposition_header = self.headers['content-disposition']
        disposition, options = parse_header_options(disposition_header)
        if disposition == 'form-data':
            self._current_name, self._current = _choose_input(disposition, options)
            self._parts_received[input_name] = self._current


class DumpingReceiver(object):
    """A receiver for data other than multipart/form-data.

    Probably will be useful in the future for `$ curl -X POST -d @file` uploads
    """
    # XXX make this actually store the data, and update the listener
    def __init__(self, listener):
        self._listener = listener
        self.length = None
        self._received_bytes = 0

    def data_received(self, data):
        pass

    def finish(self):
        pass
