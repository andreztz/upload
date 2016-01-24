Upload
======

Like `python -m http.server` (`python -m SimpleHTTPServer`), but for uploads.

Simply run `python -m upload`, and this will run a webserver that will accept
uploaded files and store them in the cwd.

To run the tests, clone this repository, install the requirements
from requirements.txt into your virtualenv, and simply do `py.test` in
the project directory.

TODO
----
* UI: after uploading a file, show some kind of confirmation...
* add some mechanism from programmatic uploads
* add to PyPI?
