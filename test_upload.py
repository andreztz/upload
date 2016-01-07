from upload import parse_header_options, MainHandler, Pending
import pytest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, url
from mock import patch, mock_open


@pytest.mark.parametrize('header,expected', [
    ('text/html', ('text/html', {})),
    ('text/html; charset=utf-8', ('text/html', {'charset': 'utf-8'})),
    ('a/b; x=y; z=v', ('a/b', {'x': 'y', 'z': 'v'})),
])
def test_parse_header_options(header, expected):
    assert parse_header_options(header) == expected

class TestUploadHandler(AsyncHTTPTestCase):
    def get_app(self):
        pending = Pending()
        application = Application([
            url(r"/", MainHandler, {'pending': pending}, name='upload'),
        ], debug=True, template_path='templates')
        return application

    def test_saves_file(self):
        m = mock_open()
        with patch('upload.open', m, create=True):
            response = self.fetch('/?id=1234', method='POST',
                headers={"Content-Type": 'multipart/form-data; boundary=AaB03x'},
                body='\r\n'.join([
                    '--AaB03x',
                    'Content-Disposition: file; filename="foo.txt"',
                    'Content-Type: text/plain',
                    '',
                    'foo1',
                    'foo2',
                    '--AaB03x--'
                ]))

        written_data = ''.join(args[0] for _, args, _ in m().write.mock_calls)
        assert written_data == 'foo1\r\nfoo2'
