import mock
from upload.progress import ProgressListener


def test_fires_callbacks_data_received():
    progress = ProgressListener(upload_id='foo')

    cb = mock.Mock()
    progress.register_callback(cb)
    progress.data_received(42)

    assert len(cb.mock_calls) == 1

    _, call_args, call_kwargs = cb.mock_calls[0]
    state = call_args[0]

    assert not state['files']
    assert state['total'] == [42, None]


def test_fires_callbacks_filepart():
    progress = ProgressListener(upload_id='foo')

    cb = mock.Mock()
    progress.register_callback(cb)
    progress.file_part_received('file.txt', 42, 150)

    assert len(cb.mock_calls) == 1

    _, call_args, call_kwargs = cb.mock_calls[0]
    state = call_args[0]

    assert 'file.txt' in state['files']
    assert state['files']['file.txt'] == [42, 150]

