import os
import re
import urllib.request
import urllib.parse
from pypairtree.pairtree import get_pair_path


class SystemMethodsException(Exception):
    """Base exception for aubrey system methods"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value)


# Locates the file on the systems
def get_file_system(meta_id, file_path, location_tuple):
    system_path = None
    file_location = None

    # Loop through possible locations for files
    for file_system in location_tuple:
        # if the system is local to this server
        if re.compile(r'^file://').search(file_system, 0) is not None:
            absolute_path = file_system.replace('file:/', '')
            # if the file name starts with file://, change it to start
            # with just a /
            if file_path.startswith('file://'):
                local_file_path = get_complete_filepath(meta_id, file_path, file_system)[6:]
            else:
                local_file_path = file_path
            # if the file exists on the local server, and isn't an html file
            if os.path.exists(local_file_path):
                system_path = local_file_path
                file_location = absolute_path
                break
        # if the system is on another server
        elif re.compile(r'^https?://').search(file_system, 0) is not None:
            try:
                # if the file name starts with file:// or /, change it
                # to start with no beginning slashes
                if file_path.startswith('file://'):
                    http_file_path = get_file_path(meta_id, file_path)
                else:
                    http_file_path = file_path
                # Separate the host and the path
                scheme, host, system_path = urllib.parse.urlsplit(file_system)[:3]
                # Join the system and file path
                raw_path = urllib.parse.urljoin(system_path, http_file_path[1:])
                # Quote the url path (helps with spaces and special characters)
                path = urllib.parse.quote(raw_path)
                if host != '' and path != '':
                    # Check if file exists on the server
                    url = '%s://%s%s' % (scheme, host, path)
                    headers = {'Host': host}
                    request = urllib.request.Request(url, headers=headers)
                    request.get_method = lambda: 'HEAD'
                    status_code = urllib.request.urlopen(request, timeout=3).getcode()
                else:
                    system_path = None
                # if the file exists, return the necessary data
                if status_code == 200:
                    system_path = '%s://%s%s' % (scheme, host, path)
                    file_location = file_system
                    break
                else:
                    system_path = None
            except Exception:
                pass
    # returns the file name
    return system_path, file_location


def get_file_path(meta_id, file_name):
    """ Determine a file path on a file system based on the file name and meta-id """
    # Create the pair path
    meta_path = get_pair_path(meta_id)
    # Get only parts of the file_name we need
    stripped_regex = re.compile(r'^file:/?/(web/?.+)').search(file_name, 0)
    if stripped_regex is not None:
        stripped_filename = stripped_regex.group(1)
    else:
        raise SystemMethodsException("Can't recognize the file name: %s" % (file_name))
    # join the base filename to the paired web path to create the file path
    file_path = os.path.join(meta_path, stripped_filename)

    return file_path


# get_static_file
def get_complete_filepath(meta_id, file_name, file_system):
    """ Create a file path and concatenate it with a file system
         to create the complete file path
         based on the file name and meta-id
    """
    file_path = get_file_path(meta_id, file_name)
    # join the file system and file path
    completed_filename = "%s%s" % (file_system, file_path[1:])

    return completed_filename


def open_system_file(file_name):
    """ Open and return a file handle either on the file system or
         over http depending on the file name
    """
    # open the file over http
    if re.compile(r'^https?://').search(file_name, 0) is not None:
        valid_url = create_valid_url(file_name)
        try:
            return urllib.request.urlopen(valid_url)
        except Exception:
            return get_other_system(valid_url)
    # open it over the file system
    else:
        return open(file_name, 'rb')


def open_args_system_file(file_name):
    """Creates a valid url with arguments added (ex. ?start=123)"""
    # open the file over http
    if re.compile(r'^https?://').search(file_name, 0) is not None:
        valid_url = create_valid_url(file_name)
        args = urllib.parse.urlsplit(file_name)[3]
        arg_url = "%s?%s" % (valid_url, args)
        return urllib.request.urlopen(arg_url)
    else:
        raise SystemMethodsException("Invalid url: %s" % (file_name))


def create_valid_url(file_name):
    """Creates a valid url from the given url"""
    # Separate the host and the path
    scheme, host, raw_path = urllib.parse.urlsplit(file_name)[:3]
    # Make sure that the filename isn't being parsed improperly
    if urllib.parse.urlsplit(file_name)[4] == '':
        # quote the path to fix special characters
        path = urllib.parse.quote(raw_path)
    # The path was split up by a bad character
    else:
        # Get the broken off part of the path
        broken_path = urllib.parse.urlsplit(file_name)[4]
        # Create the bad character locating regex
        bad_regex = re.compile(re.escape(raw_path)+r'([\W]+)'+re.escape(broken_path)+r'$')
        # If the bad character(s) are found
        if bad_regex.search(file_name, 0) is not None:
            bad_char = bad_regex.search(file_name, 0).group(1)
        else:
            bad_char = ''
        # Combine the broken path into one and quote it
        path = urllib.parse.quote("%s%s%s" % (raw_path, bad_char, broken_path))
    # Join the system and file path
    return "%s://%s%s" % (scheme, host, path)


def open_file_range(file_name, range_tuple):
    """Open a url file, but only a certain range of bytes"""
    # open the file over http
    if re.compile(r'^https?://').search(file_name, 0) is not None:
        headers = {'Range': "bytes=%s-%s" % range_tuple}
        valid_url = create_valid_url(file_name)
        req = urllib.request.Request(valid_url, None, headers)
        try:
            return urllib.request.urlopen(req)
        except Exception:
            raise SystemMethodsException("Specified Range (%s,%s) not valid." % range_tuple)
    # open it over the file system
    else:
        return None


def get_other_system(failed_url):
    """Takes a file that failed to give a response
        and tries to locate it via Django settings
    """
    # Determine meta/static servers locations
    try:
        from django.conf import settings
    except Exception:
        from aubreylib import METADATA_LOCATIONS, STATIC_FILE_LOCATIONS
    else:
        try:
            METADATA_LOCATIONS = settings.METADATA_LOCATIONS
            STATIC_FILE_LOCATIONS = settings.STATIC_FILE_LOCATIONS
        except Exception:
            from aubreylib import METADATA_LOCATIONS, STATIC_FILE_LOCATIONS
    # Combine the metadata locations with static locations
    all_locations = METADATA_LOCATIONS + STATIC_FILE_LOCATIONS
    # Determine the host
    host = urllib.parse.urlsplit(failed_url)[1]
    # Try to find file on metadata/static servers
    for metadata_location in all_locations:
        replacement_host = urllib.parse.urlsplit(metadata_location)[1]
        new_url = failed_url.replace(host, replacement_host)
        try:
            return urllib.request.urlopen(new_url, timeout=3)
        except Exception:
            pass
    raise SystemMethodsException("Can't locate file: %s" % (failed_url))
