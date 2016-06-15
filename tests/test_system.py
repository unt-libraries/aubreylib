import mock
import pytest

from aubreylib import system


class TestGetFileSystem():

    location_tuple = ('file://disk2/',
                      'http://unt.edu/disk2/')

    @mock.patch('os.path.exists')
    def test_file_local_to_server(self, mocked_exists):
        """Locate a file when file_system starts with 'file://'"""
        mocked_exists.return_value = True
        path, location = system.get_file_system('metapthx',
                                                'web/4.jpg',
                                                self.location_tuple)
        expected = ('web/4.jpg', '/disk2/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    def test_file_local_to_server_file_in_path(self, mocked_exists):
        """Locate a system file when system and path both start
        with 'file://'
        """
        mocked_exists.return_value = True
        path, location = system.get_file_system('metapthx',
                                                'file://web/4.jpg',
                                                self.location_tuple)
        expected = ('/disk2/me/ta/pt/hx/metapthx/web/4.jpg', '/disk2/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('httplib.HTTP')
    def test_file_at_http_url(self, MockedHTTP, mocked_exists):
        """Locate a file on another server via http URL."""
        MockedHTTP.return_value.getreply.return_value = (200, '', '')
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                '/me/ta/pt/hx/metapthx/web/4.jpg',
                                                self.location_tuple)
        expected = ('http://unt.edu/disk2/me/ta/pt/hx/metapthx/web/4.jpg',
                    'http://unt.edu/disk2/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('httplib.HTTP')
    def test_file_at_http_with_file_in_path(self, MockedHTTP, mocked_exists):
        """Locate a file on another server via http URL when file path
        starts with 'file://'.
        """
        MockedHTTP.return_value.getreply.return_value = (200, '', '')
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                'file://web/4.jpg',
                                                self.location_tuple)
        expected = ('http://unt.edu/disk2/me/ta/pt/hx/metapthx/web/4.jpg',
                    'http://unt.edu/disk2/')
        assert (path, location) == expected

    @mock.patch('httplib.HTTP')
    def test_file_system_with_empty_path(self, MockedHTTP):
        """Test http:// location with an '' (empty) `path`."""
        MockedHTTP.return_value.getreply.return_value = (200, '', '')
        path, location = system.get_file_system('metapthx',
                                                '',
                                                ('http://unt.edu',))
        expected = (None, None)
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('httplib.HTTP')
    def test_file_not_found(self, MockedHTTP, mocked_exists):
        """Test file not found on any given system."""
        MockedHTTP.return_value.getreply.return_value = (404, '', '')
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                'web/4.jpg',
                                                self.location_tuple)
        expected = (None, None)
        assert (path, location) == expected


class TestGetFilePath():

    def test_get_file_path(self):
        """Test correct creation of file path."""
        file_path = system.get_file_path('metapth', 'file://web/01_tif/4.jpg')
        expected_path = '/me/ta/pt/h/metapth/web/01_tif/4.jpg'
        assert file_path == expected_path

    def test_get_file_path_raises_exception(self):
        """Test invalid file name raises SystemMethodsException."""
        with pytest.raises(system.SystemMethodsException):
            system.get_file_path('metapthx', '/web/01_tif/4.jpg')


class TestGetCompleteFilePath():

    def test_get_complete_filepath(self):
        """Test correct generation of the complete file path."""
        complete_path = system.get_complete_filepath('metapthx',
                                                     'file://web/4.jpg',
                                                     'http://unt.edu/disk2/')
        expected_path = 'http://unt.edu/disk2/me/ta/pt/hx/metapthx/web/4.jpg'
        assert complete_path == expected_path


class TestOpenSystemFile():

    @mock.patch('urllib2.urlopen')
    def test_open_system_file_http(self, mocked_urlopen):
        """Test return value comes from urlopen call."""
        mocked_urlopen.return_value = expected = 'file'
        file_obj = system.open_system_file('http://example.com/pth/f.jpg')
        assert file_obj == expected

    @mock.patch('urllib2.urlopen')
    @mock.patch('aubreylib.system.get_other_system')
    def test_open_system_file_http_other_system(self,
                                                mocked_other_system,
                                                mocked_urlopen):
        """Test return value comes from get_other_system call."""
        mocked_urlopen.side_effect = Exception()
        mocked_other_system.return_value = expected = 'file'
        file_obj = system.open_system_file('http://example.com/pth/f.jpg')
        assert file_obj == expected

    @mock.patch('__builtin__.open')
    def test_open_system_file_local(self, mocked_open):
        """Test return value comes from local location."""
        mocked_open.return_value = expected = 'file'
        file_obj = system.open_system_file('/pth/f.jpg')
        assert file_obj == expected


class TestOpenArgsSystemFile():

    @mock.patch('urllib2.urlopen')
    def test_open_args_system_file_returns_file(self, mocked_urlopen):
        """Test a valid URL results in a returned object."""
        mocked_urlopen.return_value = expected = 'file'
        url_with_args = 'http://example.com/pth/f.jpg?start=123'
        file_obj = system.open_args_system_file(url_with_args)
        assert file_obj == expected
        mocked_urlopen.assert_called_once_with(url_with_args)

    def test_open_args_system_file_raises_exception(self):
        """Test an invalid URL raises exception."""
        with pytest.raises(system.SystemMethodsException):
            system.open_args_system_file('/bad/url')


class TestCreateValidUrl():

    def test_create_valid_url_encodes_url(self):
        """Test url is encoded when not split improperly."""
        url = system.create_valid_url('http://ex.com/path,/sdf')
        assert url == 'http://ex.com/path%2C/sdf'

    def test_create_valid_url_fixes_and_encodes_url(self):
        """Test url is put back together correctly and percent
        encoded after urlsplit improperly identifies a fragment.
        """
        url = system.create_valid_url('http://ex.com/path#01/seg')
        assert url == 'http://ex.com/path%2301/seg'


class TestOpenFileRange():

    @mock.patch('urllib2.urlopen')
    @mock.patch('urllib2.Request')
    def test_open_file_range(self, MockedRequest, _):
        """Test the HTTP request is made with supplied range."""
        url = 'http://example.com/path'
        system.open_file_range(url, (0, 10))
        MockedRequest.assert_called_once_with(url,
                                              None,
                                              {'Range': 'bytes=0-10'})

    def test_open_file_range_with_non_url(self):
        """Test result with file_name that is not a URL."""
        file_obj = system.open_file_range('/this/is/local', (0, 10))
        assert file_obj is None


class TestGetOtherSystem():

    @mock.patch('aubreylib.METADATA_LOCATIONS', ('http://url.com/disk2',))
    @mock.patch('aubreylib.STATIC_FILE_LOCATIONS', ('http://url2.com/disk2',))
    @mock.patch('urllib2.urlopen')
    def test_get_other_system_finds_no_file(self, mocked_urlopen):
        """Test not finding file raises exception."""
        mocked_urlopen.side_effect = Exception()
        with pytest.raises(system.SystemMethodsException):
            system.get_other_system('http://example.com/disk1/noexist')
        assert mocked_urlopen.call_count == 2

    @mock.patch('aubreylib.METADATA_LOCATIONS', ('http://url.com/disk2',))
    @mock.patch('aubreylib.STATIC_FILE_LOCATIONS', ('http://url2.com/disk2',))
    @mock.patch('urllib2.urlopen')
    def test_get_other_system_finds_file(self, mocked_urlopen):
        """Test file is returned using tuple-supplied locations."""
        mocked_urlopen.return_value = expected = 'file'
        file_obj = system.get_other_system('http://example.com/disk1/noexist')
        assert file_obj == expected
        mocked_urlopen.assert_called_once_with('http://url.com/disk1/noexist')
