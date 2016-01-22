from upload.progress import Pending
from upload.web import MainHandler
import pytest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, url
from mock import patch, mock_open


class TestUploadHandler(AsyncHTTPTestCase):
    def get_app(self):
        pending = Pending()
        application = Application([
            url(r"/", MainHandler, {'pending': pending}, name='upload'),
        ], debug=True, template_path='templates')
        return application

    def test_curl_one_file(self):
        m = mock_open()
        with patch('upload.receiver.open', m, create=True):
            response = self.fetch('/?id=1234', method='POST',
                headers={"Content-Type": 'multipart/form-data; boundary=------------------------587eec1383ff18ed'},
                body='\r\n'.join([
                   '--------------------------587eec1383ff18ed',
                   'Content-Disposition: form-data; name="file1"; filename="file.txt"',
                   'Content-Type: text/plain',
                   '',
                   '1\n2\n\n',
                   '--------------------------587eec1383ff18ed--\r\n'
                ]))

        written_data = ''.join(args[0] for _, args, _ in m().write.mock_calls)
        assert written_data == '1\n2\n\n'


    def test_browser_without_stats(self):
        m = mock_open()
        with patch('upload.receiver.open', m, create=True):
            response = self.fetch('/?id=1234', method='POST',
                headers={"Content-Type": 'multipart/form-data; boundary=----WebKitFormBoundaryxacDBowAZ6IziYCN'},
                body='\r\n'.join([
                    '------WebKitFormBoundaryxacDBowAZ6IziYCN',
                    'Content-Disposition: form-data; name="upload"; filename="file.txt"',
                    'Content-Type: text/plain',
                    '',
                    '1\n2\n\n',
                    '------WebKitFormBoundaryxacDBowAZ6IziYCN--'
                ]))

        written_data = ''.join(args[0] for _, args, _ in m().write.mock_calls)
        assert written_data == '1\n2\n\n'

    def test_browser_without_js(self):
        m = mock_open()
        with patch('upload.receiver.open', m, create=True):
            response = self.fetch('/?id=1234', method='POST',
                headers={"Content-Type": 'multipart/form-data; boundary=---------------------------936672268170469130233155377'},
                body='\r\n'.join([
                    '-----------------------------936672268170469130233155377',
                    'Content-Disposition: form-data; name="upload"; filename="file.txt"',
                    'Content-Type: text/plain',
                    '',
                    '1\n2\n\n',
                    '-----------------------------936672268170469130233155377--',
                ]))

        written_data = ''.join(args[0] for _, args, _ in m().write.mock_calls)
        assert written_data == '1\n2\n\n'
