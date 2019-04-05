import mock
import pytest

from aubreylib import system


class TestGetFileSystem():

    location_tuple = ('file://disk2/',
                      'http://unt.edu/disk2/',
                      'http://unt.edu',
                      'https://unt.edu/disk3/')

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
    @mock.patch('urllib.request.urlopen')
    def test_file_at_http_url(self, mocked_urlopen, mocked_exists):
        """Locate a file on another server via http URL."""
        mocked_urlopen.return_value.getcode.return_value = 200
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                '/me/ta/pt/hx/metapthx/web/4.jpg',
                                                self.location_tuple)
        expected = ('http://unt.edu/disk2/me/ta/pt/hx/metapthx/web/4.jpg',
                    'http://unt.edu/disk2/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('urllib.request.urlopen')
    def test_file_at_https_url(self, mocked_urlopen, mocked_exists):
        """Locate a file on another server via https URL."""
        # Respond with Success for location_tuple https URL only.
        http_responses = [404, 404, 200]
        mocked_urlopen.return_value.getcode.side_effect = http_responses
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                '/me/ta/pt/hx/metapthx/web/4.jpg',
                                                self.location_tuple)
        expected = ('https://unt.edu/disk3/me/ta/pt/hx/metapthx/web/4.jpg',
                    'https://unt.edu/disk3/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('urllib.request.urlopen')
    def test_file_at_http_with_file_in_path(self, mocked_urlopen, mocked_exists):
        """Locate a file on another server via http URL when file path
        starts with 'file://'.
        """
        mocked_urlopen.return_value.getcode.return_value = 200
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                'file://web/4.jpg',
                                                self.location_tuple)
        expected = ('http://unt.edu/disk2/me/ta/pt/hx/metapthx/web/4.jpg',
                    'http://unt.edu/disk2/')
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('urllib.request.urlopen')
    def test_file_system_with_empty_path(self, mocked_urlopen, mocked_exists):
        """Test http:// location with an '' (empty) `path`."""
        # Respond with Not Found for the first location_tuple URL tried,
        # so the URL with no path will be tried.
        mocked_urlopen.return_value.getcode.return_value = 404
        mocked_exists.return_value = False
        path, location = system.get_file_system('metapthx',
                                                '',
                                                self.location_tuple)
        expected = (None, None)
        assert (path, location) == expected

    @mock.patch('os.path.exists')
    @mock.patch('urllib.request.urlopen')
    def test_file_not_found(self, mocked_urlopen, mocked_exists):
        """Test file not found on any given system."""
        mocked_urlopen.return_value.getcode.return_value = 404
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

    @pytest.mark.parametrize('url', [
        'http://example.com/pth/f.jpg',
        'https://example.com/pth/f.jpg'
    ])
    @mock.patch('urllib.request.urlopen')
    def test_open_system_file_via_url(self, mocked_urlopen, url):
        """Test return value comes from urlopen call."""
        mocked_urlopen.return_value = expected = 'file'
        file_obj = system.open_system_file(url)
        assert file_obj == expected

    @mock.patch('urllib.request.urlopen')
    @mock.patch('aubreylib.system.get_other_system')
    def test_open_system_file_http_other_system(self,
                                                mocked_other_system,
                                                mocked_urlopen):
        """Test return value comes from get_other_system call."""
        mocked_urlopen.side_effect = Exception()
        mocked_other_system.return_value = expected = 'file'
        file_obj = system.open_system_file('http://example.com/pth/f.jpg')
        assert file_obj == expected

    @mock.patch('builtins.open')
    def test_open_system_file_local(self, mocked_open):
        """Test return value comes from local location."""
        mocked_open.return_value = expected = 'file'
        file_obj = system.open_system_file('/pth/f.jpg')
        assert file_obj == expected


class TestOpenArgsSystemFile():

    @pytest.mark.parametrize('url', [
        'http://example.com/pth/f.jpg?start=123',
        'https://example.com/pth/f.jpg?start=123'
    ])
    @mock.patch('urllib.request.urlopen')
    def test_open_args_system_file_returns_file(self, mocked_urlopen, url):
        """Test a valid URL results in a returned object."""
        mocked_urlopen.return_value = expected = 'file'
        file_obj = system.open_args_system_file(url)
        assert file_obj == expected
        # Verify urlopen argument had query string.
        mocked_urlopen.assert_called_once_with(url)

    def test_open_args_system_file_raises_exception(self):
        """Test an invalid URL raises exception."""
        with pytest.raises(system.SystemMethodsException):
            system.open_args_system_file('/bad/url')


class TestCreateValidUrl():

    def test_create_valid_url_encodes_url(self):
        """Test url is encoded when not split improperly."""
        url = system.create_valid_url('http://ex.com/path,/sdf')
        assert url == 'http://ex.com/path%2C/sdf'

    @pytest.mark.parametrize('original, expected', [
        ('http://ex.com/path#01/seg', 'http://ex.com/path%2301/seg'),
        ('https://ex.com/path#01/seg', 'https://ex.com/path%2301/seg'),
    ])
    def test_create_valid_url_fixes_and_encodes_url(self, original, expected):
        """Test url is put back together correctly and percent
        encoded after urlsplit improperly identifies a fragment.
        """
        url = system.create_valid_url(original)
        assert url == expected


class TestOpenFileRange():

    @pytest.mark.parametrize('url', [
        'http://example.com/path',
        'https://example.com/path'
    ])
    @mock.patch('urllib.request.urlopen')
    @mock.patch('urllib.request.Request')
    def test_open_file_range(self, MockedRequest, _, url):
        """Test the HTTP request is made with supplied range."""
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
    @mock.patch('urllib.request.urlopen')
    def test_get_other_system_finds_no_file(self, mocked_urlopen):
        """Test not finding file raises exception."""
        mocked_urlopen.side_effect = Exception()
        with pytest.raises(system.SystemMethodsException):
            system.get_other_system('http://example.com/disk1/noexist')
        assert mocked_urlopen.call_count == 2

    @mock.patch('aubreylib.METADATA_LOCATIONS', ('http://url.com/disk2',))
    @mock.patch('aubreylib.STATIC_FILE_LOCATIONS', ('http://url2.com/disk2',))
    @mock.patch('urllib.request.urlopen')
    def test_get_other_system_finds_file(self, mocked_urlopen):
        """Test file is returned using tuple-supplied locations."""
        mocked_urlopen.return_value = expected = 'file'
        file_obj = system.get_other_system('http://example.com/disk1/noexist')
        assert file_obj == expected
        mocked_urlopen.assert_called_once_with('http://url.com/disk1/noexist', timeout=3)
