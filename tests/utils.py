import lxml.etree

from PIL import Image


def is_xml_file(path):
    """
    Check if the file is a valid XML document

    :returns: True if file can be parsed as XML, False otherwise
    """
    try:
        lxml.etree.parse(str(path))
        return True
    except lxml.etree.ParseError:
        return False


def is_image_file(path):
    """
    Check if the file is a valid image file

    :returns: True if file is an image file, False otherwise
    """
    try:
        Image.open(str(path))
        return True
    except IOError:
        return False
