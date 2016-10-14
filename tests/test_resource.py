#!/usr/bin/env python

import pytest
from mock import mock_open, patch

from aubreylib import resource


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


class TestGetDimensionsFilename:

    @patch('os.path.exists')
    def test_get_dimensions_filename_exists(self, mock_exists):
        """Verify filename is returned when file exists."""
        mock_exists.return_value = True
        filename = resource.get_dimensions_filename('/some/path/meta1234.mets.xml')
        assert filename == '/some/path/meta1234.json'

    @patch('os.path.exists')
    def test_get_dimensions_filename_absent(self, mock_exists):
        """Verify None is returned when file does not exist."""
        mock_exists.return_value = False
        filename = resource.get_dimensions_filename('/some/path/meta1234.mets.xml')
        assert filename is None


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
            assert returned_json == None
