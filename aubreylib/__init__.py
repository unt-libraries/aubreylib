#Resource Representation reference dictionary (METS USE)
USE = {
    'high_res': 1,
    'thumbnail': 2,
    'med_res': 3,
    'ocr': 4,
    'bounding_box': 5,
    'transcription': 6,
    'translation': 7,
    'zoom': 8,
    'cdx': 9,
    'square':10,
}

#View method for mimetypes
VIEW_TYPE_MIMETYPES = {
    'image/png': 'image',
    'image/jpeg': 'image',
    'image/gif': 'image',
    'image/bmp': 'image',
    'image/jpeg': 'image',
    'application/pdf': 'file',
    'image/tiff': 'file',
    'application/octet-stream': 'file',
    'audio/mpeg': 'audio',
    'audio/mpeg3': 'audio',
    'text/html': 'html',
    'text/plain': 'text',
    'text/xml': 'xml',
    'application/zip': 'file',
    'video/x-flv': 'video',
    'video/mp4': 'video',
    None: 'file',
}

EMAIL_REGEX = r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}'

#Metadata location tuple. Used to specify potential source systems for metadata files.
METADATA_LOCATIONS = ()

#Static file location tuple. Used to specify potential source systems for static files.
STATIC_FILE_LOCATIONS = ()
