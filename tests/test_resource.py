import pytest

from aubreylib.resource import get_author_citation_string


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
        citation_string = get_author_citation_string({'creator': creators})

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
        citation_string = get_author_citation_string({'creator': creators})

        assert citation_string == expected
