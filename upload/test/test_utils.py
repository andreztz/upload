import pytest

from upload.util import parse_header_options


@pytest.mark.parametrize('header,expected', [
    ('text/html', ('text/html', {})),
    ('text/html; charset=utf-8', ('text/html', {'charset': 'utf-8'})),
    ('a/b; x=y; z=v', ('a/b', {'x': 'y', 'z': 'v'})),
])
def test_parse_header_options(header, expected):
    assert parse_header_options(header) == expected
