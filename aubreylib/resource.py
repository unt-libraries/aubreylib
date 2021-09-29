import os
import re
from io import BytesIO
import datetime
import urllib.request
import json
from lxml import etree
from aubreylib.system import get_file_system, open_system_file, get_pair_path
from aubreylib import VIEW_TYPE_MIMETYPES, EMAIL_REGEX
from pyuntl.untldoc import untlxml2pydict, untldict2py
from pyuntl.util import untldict_normalizer


class ResourceObjectException(Exception):
    """Base exception for the Resource object creation"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)


def get_mets_record_system(meta_id, pair_path, metadata_locations):
    """ Find the system that the METS file is on, and return the file, and the
         metadata system path """

    # Add the METS filename to the pair path
    resource_path = os.path.join(pair_path, meta_id + '.mets.xml')
    # Locate the system the mets file is on, and the mets file itself
    mets_filename, metadata_system = get_file_system(
        meta_id,
        resource_path,
        metadata_locations,
    )

    if mets_filename is None or metadata_system is None:
        raise ResourceObjectException("Mets file could not be located on " +
                                      "any system. meta-id: %s, pair-path: %s"
                                      % (meta_id, pair_path))
    else:
        return mets_filename, metadata_system


def get_desc_metadata(metadata_filename, metadata_type):
    """ Get the descriptive metadata for the object """
    # Open and read the metadata file into a BytesIO filehandle
    metadata_filehandle = open_system_file(metadata_filename)
    metadata_stringfile = BytesIO(metadata_filehandle.read())
    if metadata_type == 'UNTL':
        # Get the untl descriptive metadata dictionary
        desc_metadata = untlxml2pydict(metadata_stringfile)
        normalize_required = {
            'subject': ['LCSH', 'UNTL-BS'],
        }
        # Normalize the values in the untl dictionary
        normalized_metadata = untldict_normalizer(
            desc_metadata,
            normalize_required,
        )
        return normalized_metadata
    else:
        raise ResourceObjectException("Not a supported descriptive " +
                                      "metadata type.")


def get_getCopy_data(getCopy_url, meta_id):
    """Get the getCopy data for the object"""
    # Create the url for the record
    record_url = "%s%s/" % (getCopy_url, meta_id)
    # Try returning the getCopy data
    try:
        return json.loads(urllib.request.urlopen(record_url).read())
    except Exception:
        # Otherwise, return an empty dictionary
        return {}


def get_author_citation_string(desc_MD):
    """Build author citation string up to six names"""
    author_citation_string = ""
    creator_list = desc_MD.get('creator', [])
    names = []
    for creator_item in creator_list:
        creator_content = creator_item.get('content', {})
        # verify creator_item has a content dictionary
        if isinstance(creator_content, dict):
            creator_type = creator_content.get('type', '')
            if creator_type == 'per':
                names.append(creator_content.get('name', '').strip())
            elif not names and creator_type in ('org', ''):
                # first given creator is 'org' or '', that's enough for us
                author_citation_string = creator_content.get(
                    'name', '').strip()
                break
        # we only want six names at most
        if len(names) > 6:
            # build author_citation_string now, since we know the length
            author_citation_string = '; '.join(names[:6]) + ' et al.'
            names = None
            break
    # if there were 'per' types less than seven, build author string
    if names:
        if len(names) == 1:
            author_citation_string = names[0]
        else:
            author_citation_string = '; '.join(
                names[:-1]) + ' & ' + names[-1]
    return author_citation_string


def get_dimensions_data(mets_file):
    """Return the JSON dimensions file path if it exists."""
    dimensions_file = mets_file.replace('.mets.xml', '.json')
    try:
        return json.load(open_system_file(dimensions_file))
    except Exception:
        return None


def get_transcriptions_data(meta_id, resource_type, transcriptions_server_url):
    """Return the JSON transcriptions structure if it exists. Only for sounds and videos."""
    if resource_type not in ['sound', 'video'] or not transcriptions_server_url:
        return {}
    transcriptions_url = '{}/{}/'.format(transcriptions_server_url.rstrip('/'), meta_id)
    try:
        return json.loads(urllib.request.urlopen(transcriptions_url).read())
    except Exception:
        # Otherwise, return an empty dictionary
        return {}


class ResourceObject:

    def __init__(self, identifier, metadataLocations, staticFileLocations,
                 mimetypeIconsPath, use, **kwargs):
        """
        identifier can either be an absolute path to a mets.xml file, or a
        meta_id.  In the latter case, it will derive the path from the meta_id
        """
        self.metadataLocations = metadataLocations
        self.staticFileLocations = staticFileLocations
        self.use = use
        getCopy_url = kwargs.get('getCopy_url', None)

        # if the identifier is a filename, use that.  Otherwise treat it as
        # a meta_id
        if identifier.endswith(".mets.xml"):
            self.mets_filename = identifier
            # self.metadata_file = identifier
            self.meta_id = os.path.split(identifier)[1].split(".")[0]
            self.pair_path = get_pair_path(self.meta_id)
            self.metadata_system = None
        else:
            self.meta_id = identifier
            # Get the pair path for the digital object
            self.pair_path = get_pair_path(self.meta_id)
            # Determine the location of the resource and the filename
            # of the resource's record
            self.mets_filename, self.metadata_system = get_mets_record_system(
                self.meta_id,
                self.pair_path,
                metadataLocations
            )
        # Get dimensions data
        self.dimensions = get_dimensions_data(self.mets_filename)
        # If a getCopy url was given
        if getCopy_url:
            self.getCopy_data = get_getCopy_data(getCopy_url, self.meta_id)
        else:
            self.getCopy_data = {}
        # Open the METS document
        try:
            mets_filehandle = open_system_file(self.mets_filename)
        except Exception:
            raise ResourceObjectException("Could not open the Mets " +
                                          "document: %s" % (self.meta_id))
        # Parse the mets document
        parsed_mets = etree.parse(mets_filehandle)
        # Close the mets file
        mets_filehandle.close()
        # Get the acp last modification date (useful for ETag hashes)
        self.get_acp_last_modification_date(parsed_mets)
        # Get Metadata File
        self.get_metadata_file(parsed_mets)
        # Get the descriptive metadata
        self.desc_MD = get_desc_metadata(self.metadata_file,
                                         self.metadata_type)
        # Get transcriptions data
        resource_type = self.desc_MD.get('resourceType')
        if resource_type:
            resource_type = resource_type[0].get('content')
        else:
            resource_type = None
        self.transcriptions = get_transcriptions_data(
            meta_id=self.meta_id,
            resource_type=resource_type,
            transcriptions_server_url=kwargs.get('transcriptions_server_url'),
        )
        # Get the fileSets within the fileSec
        self.get_structMap(parsed_mets)
        # Get the embargo information, if it exists
        self.get_embargo()
        # Get the author citation string
        self.author_citation_string = get_author_citation_string(self.desc_MD)
        self.completeness = untldict2py(self.desc_MD).completeness

    def get_metadata_file(self, parsed_mets):
        md_xpath = parsed_mets.getroot().xpath(
            'dmdSec/mdRef',
        )
        # Make sure the mdRef was defined in the METS file
        if len(md_xpath) > 0:
            mdRef = md_xpath[0]
        else:
            raise ResourceObjectException("Descriptive metadata not defined " +
                                          "in the METS file.")
        for attribs, value in mdRef.attrib.items():
            if re.compile(r'\{[\w\W]*\}href').search(attribs, 0) is not None:
                self.xlink_namespace = re.compile(
                    r'(\{[\w\W]*\})href').search(attribs, 0).group(1)
                desc_metadata_name = os.path.basename(value)
            elif attribs == 'MDTYPE':
                if value != 'OTHER':
                    self.metadata_type = value
            elif attribs == 'OTHERMDTYPE':
                self.metadata_type = value

        if not hasattr(self, 'metadata_type'):
            raise ResourceObjectException("Could not determine the type of " +
                                          "the descriptive metadata file.")

        # Get the metadata file from the system, if relevent
        if self.metadata_system is not None:
            resource_path = os.path.join(self.pair_path, desc_metadata_name)
            self.metadata_file = self.metadata_system + resource_path[1:]
        # otherwise try to find the file locally
        elif self.mets_filename is not None:
            pathPart = os.path.split(self.mets_filename)[0]
            resource_path = os.path.join(pathPart, desc_metadata_name)
            self.metadata_file = resource_path

        if not hasattr(self, 'metadata_file'):
            raise ResourceObjectException("Could not retrieve the " +
                                          "descriptive metadata file.")

    def get_acp_last_modification_date(self, parsed_mets):
        """Set the acp_modification_date if we get it, or None otherwise."""
        metsHdr = parsed_mets.getroot().xpath('metsHdr')
        if metsHdr:
            self.acp_modification_date = metsHdr[0].attrib.get('LASTMODDATE')
        else:
            self.acp_modification_date = None

    # Grabs the structMap portion of the mets xml file
    def get_structMap(self, parsed_mets):
        root = parsed_mets.getroot()
        structMap_xpath = root.xpath(
            './/structMap',
        )
        # Make sure the structMap exists in the METS file
        if len(structMap_xpath) > 0:
            structMap = structMap_xpath[0]
        else:
            raise ResourceObjectException("\"structMap\" not found in " +
                                          "METS file.")
        fileSec_xpath = root.xpath(
            './/fileSec',
        )
        # Make sure the fileSec exists in the METS file
        if len(fileSec_xpath) > 0:
            fileSec = fileSec_xpath[0]
        else:
            raise ResourceObjectException("\"fileSec\" not found in METS " +
                                          "file.")
        # Create an index for files within the fileSec file_ID --> file_group
        file_index = {}
        for file_group in fileSec:
            for file_item in file_group:
                file_index[file_item.get('ID')] = file_group
        # Get thumbnail
        self.thumbnail(fileSec, structMap)
        # Get square
        self.square(fileSec, structMap)
        # Get medium
        self.medium(fileSec, structMap)
        # Get METS files Manifestations->FileSets->FilePointers
        self.get_manifestations(fileSec, structMap, file_index)

    def thumbnail(self, fileSec, structMap):
        """Get the thumbnail filename, mimetype, and system file lives on"""
        thumbnail_dict = self.get_image_data('thumbnail', fileSec, structMap)
        self.thumbnail_mimetype = thumbnail_dict['image_mimetype']
        self.thumbnail_filename = thumbnail_dict['image_filename']
        self.files_system = thumbnail_dict['files_system']

    def square(self, fileSec, structMap):
        """Get the square image for the object"""
        square_dict = self.get_image_data('square', fileSec, structMap)
        self.square_mimetype = square_dict['image_mimetype']
        self.square_filename = square_dict['image_filename']

    def medium(self, fileSec, structMap):
        """Get the medium image for the object"""
        medium_dict = self.get_image_data('medium', fileSec, structMap)
        self.medium_mimetype = medium_dict['image_mimetype']
        self.medium_filename = medium_dict['image_filename']

    def get_primary_fileSet(self, thumbnail, structMap):
        """ Gets the primary fileSet of the object """
        for fptr in thumbnail:
            thumbnail_id = fptr.get('FILEID')
            break
        manifestations = structMap.xpath(
            './/div[@TYPE=\"manifestation\"]',
        )
        for manifest in manifestations:
            thumbnail_ptr = manifest.xpath(
                ".//fptr[@FILEID=\"%s\"]" % (thumbnail_id),
            )
            if len(thumbnail_ptr) != 0:
                self.primary_fileSet = thumbnail_ptr[0].getparent()\
                    .get('ORDER')
                self.primary_manifestation = manifest.get('ORDER')
                break

    def get_image_data(self, size_name, fileSec, structMap):
        """Based on the size name, return the file information dictionary"""
        found_image_xpath = structMap.xpath(
            ".//div[@TYPE=\"%s\"]" % (size_name),
        )
        # Make sure the image exists in the METS file structMap
        if len(found_image_xpath) > 0:
            found_image = found_image_xpath[0]
        else:
            found_image = None
            # Get the first fileSet
            first_fileset = self.get_first_fileSet(structMap)
        # if an image exists for the manifestation
        if found_image is not None:
            self.get_primary_fileSet(found_image, structMap)
            if size_name != 'medium':
                use_number = self.use[size_name]
            else:
                use_number = self.use['med_res']
            file_dict = self.get_fileSet_file(found_image, fileSec, use_number)
            image_dict = {
                'image_mimetype': file_dict['file_mimetype'],
                'image_filename': file_dict['file_name'],
                'files_system': file_dict['files_system'],
            }
        # else if we've been able to determine the first fileSet
        elif first_fileset is not None:
            self.get_primary_fileSet(first_fileset, structMap)
            file_dict = self.get_fileSet_file(
                first_fileset, fileSec, self.use['high_res'])
            self.get_mimetype_icon(file_dict['file_mimetype'])
            image_dict = {
                'image_mimetype': None,
                'image_filename': None,
                'files_system': file_dict['files_system'],
            }
        else:
            raise ResourceObjectException("The first fileSet was not found " +
                                          "in the METS file.")

        if image_dict['files_system'] is None:
            raise ResourceObjectException("Location of static files " +
                                          "could not be determined. METS " +
                                          "%s div." % (size_name))
        return image_dict

    def get_fileSet_file(self, fileSet, fileSec, use_type):
        """Gets the mimetype, filename, and file system location of a file"""
        fileSet_file_dict = {
            'file_mimetype': None,
            'file_name': None,
            'files_system': None,
        }
        fileSet_dict = self.get_file_pointers(fileSet, fileSec)
        for ptr in fileSet_dict['file_ptrs']:
            if ptr.get("USE") == str(use_type):
                file_name = ptr.get('flocat')
                # Get the file_system that static content is on if
                # not already found
                if getattr(self, 'files_system', None) is None:
                    stripped_name, files_system = get_file_system(
                        self.meta_id,
                        file_name,
                        self.staticFileLocations,
                    )
                else:
                    files_system = self.files_system
                fileSet_file_dict = {
                    'file_mimetype': ptr.get("MIMETYPE"),
                    'file_name': file_name,
                    'files_system': files_system,
                }
                return fileSet_file_dict
        return fileSet_file_dict

    def get_mimetype_icon(self, file_mimetype):
        self.thumbnail_icon_mimetype = file_mimetype

    def get_first_fileSet(self, structMap):
        """Gets the first fileSet div in the StructMap"""
        first_fileset_xpath = structMap.xpath(
            './/div[@TYPE=\"fileSet\"][@ORDER=\"1\"]',
        )
        # Make sure the first fileset exists in the METS file
        if len(first_fileset_xpath) > 0:
            return first_fileset_xpath[0]
        else:
            raise ResourceObjectException("The first fileSet was not " +
                                          "found in the METS file.")

    # Creates a manifestation dictionary, indexed by ORDER
    def get_manifestations(self, fileSec, structMap, file_index):
        self.manifestation_dict = {}
        self.manifestation_view_types = {}
        self.manifestation_labels = {}
        manifestations = structMap.xpath(
            './/div[@TYPE=\"manifestation\"]',
        )
        for manifest in manifestations:
            # Get the manifestation order number
            manifest_num = int(manifest.get("ORDER", '1'))
            # Get the fileSet dictionary and manifestation view type
            manifest_data = self.get_fileSets(manifest, fileSec, file_index)
            self.manifestation_dict[manifest_num] = manifest_data

    # Creates the fileSet dictionary, indexed by ORDER
    def get_fileSets(self, manifest, fileSec, file_index):
        manifest_num = int(manifest.get("ORDER", '1'))
        manifestation_dict = {}
        multiple_pdfs = False
        # See if the pdf dict has value already
        if not getattr(self, 'pdf_dict', None):
            self.pdf_dict = {}
        manifest_view_type = ''
        for fileSet in manifest:
            # Get the fileSet order number
            fileSet_num = int(fileSet.get("ORDER", '1'))
            # Get the transcriptions data (if any) for this fileSet
            fileSet_transcriptions = self.transcriptions.get(str(manifest_num), {}).get(
                str(fileSet_num), [])
            # Get the file pointers and fileSet view type
            fileSet_data = self.get_file_pointers(fileSet, fileSec, file_index)
            # Add the transcriptions (if any) to the file_ptrs list.
            fileSet_data['file_ptrs'].extend(fileSet_transcriptions)
            # Create the fileSet data dictionary
            manifestation_dict[fileSet_num] = {
                'file_ptrs': fileSet_data['file_ptrs'],
                'order_label': fileSet.get("ORDERLABEL"),
                'label': fileSet.get("LABEL"),
                'fileSet_view_type': fileSet_data['fileSet_view_type'],
                'zoom': fileSet_data['zoom'],
                'has_vtt_captions': self.has_vtt_type(fileSet_transcriptions, 'captions'),
                'has_vtt_subtitles': self.has_vtt_type(fileSet_transcriptions, 'subtitles'),
                'has_vtt_descriptions': self.has_vtt_type(fileSet_transcriptions, 'descriptions'),
                'has_vtt_chapters': self.has_vtt_type(fileSet_transcriptions, 'chapters'),
                'has_vtt_thumbnails': self.has_vtt_type(fileSet_transcriptions, 'thumbnails'),
                'has_vtt_metadata': self.has_vtt_type(fileSet_transcriptions, 'metadata'),
            }
            # If the manifestation doesn't have a view
            # type (return as a regular file)
            if manifest_view_type == '':
                manifest_view_type = fileSet_data['fileSet_view_type']
            # if one of the fileSets doesn't match the other fileSets
            # view types
            elif manifest_view_type != fileSet_data['fileSet_view_type']:
                # The manifestation has no specific view type
                manifest_view_type = VIEW_TYPE_MIMETYPES[None]
            # If a main pdf file was found for the first time, store
            # the information
            if fileSet_data['pdf'] and len(self.pdf_dict) == 0 and\
                    not multiple_pdfs:
                self.pdf_dict = {
                    'manifestation': manifest_num,
                    'fileSet': fileSet_num,
                    'filename': fileSet_data['pdf'],
                }
            # otherwise if there is more than one pdf in this manifestation
            elif fileSet_data['pdf'] and len(self.pdf_dict) > 0 \
                    and self.pdf_dict['manifestation'] == manifest_num:
                # No single representative pdf exists, so empty the pdf dict
                self.pdf_dict = {}
                multiple_pdfs = True
        self.manifestation_view_types[manifest_num] = manifest_view_type
        self.manifestation_labels[manifest_num] = manifest.get("LABEL", None)
        return manifestation_dict

    def has_vtt_type(self, transcriptions_list, vtt_type):
        for transcription_dict in transcriptions_list:
            if transcription_dict.get('vtt_kind') == vtt_type:
                return True
        return False

    # Gets the file pointers from the given fileset
    # (searches for the fileset starting from the fileSec node or fileGrp node)
    # Slowest part of getting the resource object
    def get_file_pointers(self, fileset, fileSec, file_index=None):
        # get the first file id file from the fileSec
        for fptr in fileset:
            first_file = fptr
            break
        # If the function was passed a index of the file's groups
        if file_index is not None:
            # get the group from the file index with FILEID as the key
            file_group = file_index[first_file.get('FILEID')]
        else:
            # Look up the file with xpath using the file id
            ptrs = fileSec.xpath(
                './/file[@ID=\"' + first_file.get('FILEID') + '\"]',
            )
            # get the group that first file is in
            file_group = ptrs[0].getparent()
        # Loop through the file group and return all the file objects
        file_ptrs = []
        fileSet_view_type = ''
        zoom = False
        pdf = None
        for ptr_file in file_group:
            file_dict = {}
            ignore_ptr_field = [
                'ID',
                'CHECKSUMTYPE',
                'CHECKSUM',
                'CREATED',
                'OWNERID',
            ]
            # Loop through file attributes and keep the ones that matter
            for key, value in ptr_file.attrib.items():
                if key == 'SIZE':
                    if ptr_file.get('USE') == str(self.use['high_res']):
                        file_dict[key] = value
                elif key not in ignore_ptr_field:
                    file_dict[key] = value
            # Get the file location
            for flocat in ptr_file:
                file_dict['flocat'] = flocat.get(self.xlink_namespace + 'href')
                break
            # Get the height/width
            if self.dimensions is not None:
                file_dimensions = self.dimensions.get(file_dict['flocat'])
                if file_dimensions is not None:
                    file_dict.update(file_dimensions)
            # if it is the main fileSet file
            if ptr_file.get('USE') == str(self.use['high_res']):
                # Get the file pointer view type
                ptr_view_type = VIEW_TYPE_MIMETYPES.get(
                    file_dict.get('MIMETYPE', None),
                    VIEW_TYPE_MIMETYPES[None],
                )
                # Determine if this is a pdf fileSet
                if 'pdf' in file_dict.get('MIMETYPE', '') and\
                        'pdf' in file_dict.get('flocat', ''):
                    pdf = os.path.basename(file_dict['flocat'])
                # If the fileSet doesn't have a view type
                # (return as a regular file)
                if fileSet_view_type == '':
                    fileSet_view_type = ptr_view_type
                # if one of the file pointers doesn't match the
                # other file pointers' view types
                elif fileSet_view_type != ptr_view_type:
                    # The manifestation has no specific view type
                    fileSet_view_type = VIEW_TYPE_MIMETYPES[None]
            # See if the object has zoom capabilities
            elif ptr_file.get('USE') == str(self.use['zoom']):
                zoom = True
            file_ptrs.append(file_dict)
        # Create the fileSet dictionary
        fileSet_dict = {
            'file_ptrs': file_ptrs,
            'fileSet_view_type': fileSet_view_type,
            'zoom': zoom,
            'pdf': pdf,
        }
        return fileSet_dict

    def get_embargo(self):
        """Get the embargo data (if it exists): embargo (True/False),
            Embargo Until date (2011-04-12), repository admin contact
            (dict with 'name' and 'email'), author contact list
            (list of dicts with 'name' and 'email')
        """
        self.embargo_info = {
            'embargo': False,
            'embargo_until_date': None,
            'repository_admin_contact': {},
            'author_contact_list': [],
        }
        # Get the list of date fields
        date_list = self.desc_MD.get('date', [])
        # Loop through the date fields list
        for date_item in date_list:
            # if there is a date field with a qualifier of embargoUntil
            if date_item.get('qualifier', None) == 'embargoUntil':
                # Has an embargo date
                # set it to true until it's determined if it's expired
                self.embargo_info['embargo'] = True
                # Get the date from the content
                date_string = date_item.get('content', None)
                # Try to parse out the date
                try:
                    embargo_date = datetime.datetime.strptime(
                        date_string, "%Y-%m-%d")
                except Exception:
                    pass
                else:
                    self.embargo_info['embargo_until_date'] = date_string
                    # Determine if the embargo is still effective,
                    # based on today's date
                    if embargo_date.date() <= datetime.date.today():
                        self.embargo_info['embargo'] = False
                    else:
                        self.embargo_info['embargo'] = True
                # Set the default repository contact
                default_contact = {
                    'name': 'Repository Administrator',
                    'email': 'untrepository@unt.edu',
                }
                # Try to get the repository admin dictionary from settings
                # otherwise use the default
                try:
                    from django.conf import settings
                    self.embargo_info['repository_admin_contact'] =\
                        getattr(
                            settings,
                            'REPOSITORY_ADMIN_DICT',
                            default_contact,
                        )
                except Exception:
                    self.embargo_info['repository_admin_contact'] =\
                        default_contact
                # Attempt to get the author e-mails from the creator field
                creator_list = self.desc_MD.get('creator', [])
                # Loop through the creator fields list
                for creator_item in creator_list:
                    creator_content = creator_item.get('content', {})
                    # if there is a creator field is a dictionary
                    if isinstance(creator_content, dict):
                        creator_info = creator_content.get('info', '')
                        # Perform an e-mail search within the author info
                        email_result = re.compile(EMAIL_REGEX).search(
                            creator_info, 0)
                        # Check and see if there is an e-mail in the info
                        if email_result is not None:
                            creator_email = email_result.group(0)
                            creator_name = creator_content.get('name',
                                                               'No Name ' +
                                                               'Listed')
                            self.embargo_info['author_contact_list'].append(
                                {'name': creator_name, 'email': creator_email}
                            )
