import lxml.etree

from PIL import Image


def is_xml_file(path):
    try:
        lxml.etree.parse(str(path))
        return True
    except lxml.etree.ParseError:
        return False


def is_image_file(path):
    try:
        Image.open(str(path))
        return True
    except IOError:
        return False
