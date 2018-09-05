#!/usr/bin/env python

import os
import pytest
import urllib2
from mock import mock_open, patch, MagicMock

from aubreylib import resource, USE


def generate_creator_list(num_creators, creator_type, name):
    return [
        {'content': {'type': creator_type, 'name': name}}
        for _ in range(num_creators)
    ]


class TestGetAuthorCitationString():

    @pytest.mark.parametrize('creator_type, name', [
        ('org', 'An, Org'),
        ('', 'Un, Known')
    ])
    def test_first_creator_not_person(self, creator_type, name):
        creators = generate_creator_list(1, creator_type, name)
        creators.append(generate_creator_list(3, 'per', 'Some, One'))
        citation_string = resource.get_author_citation_string({'creator': creators})

        assert citation_string == name

    @pytest.mark.parametrize('num_pers, num_orgs, num_unknown, expected', [
        (2, 1, 0, 'Some, One & Some, One'),
        (1, 2, 1, 'Some, One'),
        (4, 0, 3, 'Some, One; Some, One; Some, One & Some, One'),
        (8, 4, 1, 'Some, One; Some, One; Some, One; Some, One; Some, One; Some, One et al.'),
    ])
    def test_several_creators(self, num_pers, num_orgs, num_unknown, expected):
        creators = generate_creator_list(num_pers, 'per', 'Some, One')
        creators += generate_creator_list(num_orgs, 'org', 'An, Org')
        creators += generate_creator_list(num_unknown, '', 'Un, Known')
        citation_string = resource.get_author_citation_string({'creator': creators})

        assert citation_string == expected


class TestGetDimensionsData:

    @patch('os.path.exists')
    @patch('json.load')
    def test_get_dimensions_data_exists(self, mock_load, mock_exists):
        """Check that data is returned when file is found."""
        mock_exists.return_value = True
        mock_load.return_value = {}
        with patch('__builtin__.open', mock_open()):
            returned_json = resource.get_dimensions_data('/fake/file.mets.xml')
            assert returned_json == {}

    @patch('os.path.exists')
    def test_get_dimensions_data_absent(self, mock_exists):
        """Check None is returned if dimensions file does not exist."""
        mock_exists.return_value = False
        with patch('__builtin__.open', mock_open()):
            returned_json = resource.get_dimensions_data('/fake/file.mets.xml')
            assert returned_json is None


class TestGetTranscriptionsData:

    @pytest.mark.parametrize('resource_type', [
        '',
        None,
        'text',
    ])
    def test_get_transcriptions_data_wrong_resource_type(self, resource_type):
        result = resource.get_transcriptions_data('metadc123', resource_type, 'http://example.com')
        assert result == {}

    @pytest.mark.parametrize('url', [
        '',
        None,
    ])
    def test_no_transcriptions_server_url(self, url):
        result = resource.get_transcriptions_data('metadc123', 'text', url)
        assert result == {}

    @pytest.mark.parametrize('url', [
        'http://example.com',
        'http://example.com/',
    ])
    @patch('urllib2.urlopen')
    def test_no_double_slash(self, mock_urlopen, url):
        mock_urlopen.return_value = '{}'
        resource.get_transcriptions_data('metadc123', 'video', url)
        mock_urlopen.assert_called_once_with('http://example.com/metadc123/')

    @patch('urllib2.urlopen')
    def test_catches_urlopen_exceptions(self, mock_urlopen):
        mock_urlopen.side_effect = [
            urllib2.HTTPError,
            ValueError,
            TypeError,
            AttributeError,
        ]
        for i in range(4):
            result = resource.get_transcriptions_data('metadc123', 'video', 'bad_url')
            assert result == {}

    @patch('json.loads')
    @patch('urllib2.urlopen')
    def test_catches_loads_exceptions(self, mock_urlopen, mock_loads):
        mock_loads.side_effect = [
            ValueError,
            TypeError,
        ]
        mock_urlopen.return_value = ''
        for i in range(2):
            result = resource.get_transcriptions_data('metadc123', 'video', 'bad_json')
            assert result == {}

    @patch('urllib2.urlopen')
    def test_returns_expected_data(self, mock_urlopen):
        mock_urlopen.return_value = MagicMock(read=lambda: '{"some": "data"}')
        result = resource.get_transcriptions_data('metadc123', 'video', 'http://example.com')
        assert result == {'some': 'data'}


class TestResourceObject:

    @patch.object(resource.ResourceObject, 'get_fileSet_file')
    def testResourceObjectDimensions(self, mocked_fileSet_file):
        """Verifies file heights and widths are added to file_ptrs."""
        mocked_fileSet_file.return_value = {'file_mimetype': '',
                                            'file_name': '',
                                            'files_system': ''}

        # Use the METs file from our test data to make resource object.
        current_directory = os.path.dirname(os.path.abspath(__file__))
        mets_path = '{0}/data/metapth12434.mets.xml'.format(current_directory)

        ro = resource.ResourceObject(identifier=mets_path, metadataLocations=[],
                                     staticFileLocations=[],
                                     mimetypeIconsPath='', use=USE)
        # Check dimensions appear for image.
        with_dimensions_data = {'MIMETYPE': 'image/jpeg',
                                u'width': 1500,
                                'USE': '1',
                                u'height': 1154,
                                'flocat': 'file://web/pf_b-229.jpg',
                                'SIZE': '444455'}
        assert with_dimensions_data in ro.manifestation_dict[1][1]['file_ptrs']

        # Check dimensions do not appear for text file.
        no_dimensions_data = {'MIMETYPE': 'text/plain',
                              'USE': '4',
                              'flocat': 'file://web/pf_b-229.txt'}
        assert no_dimensions_data in ro.manifestation_dict[1][1]['file_ptrs']

    @patch('aubreylib.resource.get_transcriptions_data')
    @patch.object(resource.ResourceObject, 'get_fileSet_file')
    def testResourceObjectTranscriptions(self, mocked_fileSet_file,
                                         mocked_get_transcriptions_data):
        """Verifies accurate transcriptions data is provided."""
        mocked_fileSet_file.return_value = {'file_mimetype': '',
                                            'file_name': '',
                                            'files_system': ''}
        expected_transcription_data = {
            'MIMETYPE': 'text/vtt',
            'SIZE': 3618,
            'USE': 'vtt',
            'flocat': 'http://example.com/over/there',
            'language': 'eng',
            'vtt_kind': 'captions',
        }
        mocked_get_transcriptions_data.return_value = {
            '1': {
                '1': [
                    expected_transcription_data
                ]
            }
        }

        # Use the METs file from our test data to make resource object.
        current_directory = os.path.dirname(os.path.abspath(__file__))
        mets_path = '{0}/data/metapth12434.mets.xml'.format(current_directory)

        ro = resource.ResourceObject(identifier=mets_path, metadataLocations=[],
                                     staticFileLocations=[], mimetypeIconsPath='', use=USE,
                                     transcriptions_server_url='http://example.com')

        mocked_get_transcriptions_data.assert_called_once_with(
            meta_id='metapth12434', resource_type='image_photo',
            transcriptions_server_url='http://example.com')
        assert expected_transcription_data in ro.manifestation_dict[1][1]['file_ptrs']

        # Check all the 'has_vtt...' values.
        # This record does have captions.
        assert ro.manifestation_dict[1][1]['has_vtt_captions']
        # No other types of transcriptions exist for this record.
        assert not ro.manifestation_dict[1][1]['has_vtt_subtitles']
        assert not ro.manifestation_dict[1][1]['has_vtt_descriptions']
        assert not ro.manifestation_dict[1][1]['has_vtt_chapters']
        assert not ro.manifestation_dict[1][1]['has_vtt_thumbnails']
        assert not ro.manifestation_dict[1][1]['has_vtt_metadata']

    @patch.object(resource.ResourceObject, 'get_fileSet_file')
    @patch('aubreylib.resource.get_desc_metadata')
    def testResourceObjectEmptyDescMD(self, mocked_get_desc_metadata, mocked_fileSet_file):
        """Tests that a ResourceObject can instantiate with missing descriptive metadata keys."""
        mocked_get_desc_metadata.return_value = {}
        mocked_fileSet_file.return_value = {'file_mimetype': '',
                                            'file_name': '',
                                            'files_system': ''}
        current_directory = os.path.dirname(os.path.abspath(__file__))
        mets_path = '{0}/data/metapth12434.mets.xml'.format(current_directory)

        resource.ResourceObject(identifier=mets_path, metadataLocations=[],
                                staticFileLocations=[], mimetypeIconsPath='', use=USE,
                                transcriptions_server_url='http://example.com')
