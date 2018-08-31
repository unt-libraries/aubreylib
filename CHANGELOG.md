Change Log
==========

1.2.0
-----

* Added transcriptions data to ResourceObject instances.
* Fixed flake8 failures dealing with bare excepts. Now those excepts catch all Exception instances.


1.1.0
-----

* Added supplying of dimensions to ResourceObject instances when available.
* Added prevention of system hanging on HEAD and GET requests when target server is down.
* Corrected Python version in requirements.


1.0.1
-----

* Added support for https-schemed URLs. [#4](https://github.com/unt-libraries/aubreylib/issues/4).
* Updated minimum required version of pyuntl to 1.0.1. [#5](https://github.com/unt-libraries/aubreylib/issues/5)
* Fixed flake8 failures. [#3](https://github.com/unt-libraries/aubreylib/issues/3).
* Added tests for aubreylib/system.py.


1.0.0
-----

* Initial release.
