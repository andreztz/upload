import pytest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, url
from mock import patch, mock_open

from upload.receiver import HeadersGatherer, _choose_input, ReceivedFile, DescriptionField


def test_receive_headers():
    receiver = HeadersGatherer()
    field = 'Content-Type'
    value = 'text/plain'

    receiver.on_header_field(field, 0, len(field))
    receiver.on_header_value(value, 0, len(value))
    receiver.on_header_end()

    assert len(receiver) == 1
    assert receiver['content-type'] == 'text/plain'


@pytest.mark.parametrize('disposition,options,expected', [
    ('form-data', {'filename': 'foo'}, (None, ReceivedFile))
])
def test_choose_input(disposition, options, expected):
    input_name, input_class = _choose_input(disposition, options)
    expected_name, expected_class = expected
    assert input_name == expected_name
    assert expected_class is input_class


def test_received_file_name_conflict():
    preexisting = {'file.txt', 'file.txt.1'}

    def disallow_preexisting(filename, mode):
        if 'x' in mode:
            if filename in preexisting:
                err = OSError()
                err.errno = 17
                raise err

    with patch('upload.receiver.open', side_effect=disallow_preexisting) as m:
        received = ReceivedFile('file.txt')

    tried_filenames = [args[0] for name, args, kwargs in m.mock_calls]
    assert any(filename not in preexisting for filename in tried_filenames)

def test_received_file_no_conflict():
    with patch('upload.receiver.open') as m:
        received = ReceivedFile('notused.txt')

    assert len(m.mock_calls) == 1
    assert m.call_args[0][0] == 'notused.txt'

