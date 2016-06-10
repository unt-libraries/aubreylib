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

    @mock.patch('os.path.exists')
    @mock.patch('httplib.HTTP')
    def test_file_system_with_empty_path(self, MockedHTTP, mocked_exists):
        """Test http:// location with an '' (empty) `path`."""
        MockedHTTP.return_value.getreply.return_value = (200, '', '')
        mocked_exists.return_value = False
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
                                                ('http://unt.edu',))
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
