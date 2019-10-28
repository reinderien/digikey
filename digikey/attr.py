import re
from locale import atoi, atof
from typing import Type, Dict

from bs4.element import Tag


class Attr:
    NAME: str = None

    def __init__(self, title: str):
        # name ignored because we usually have a meaningful static one
        self.title = title


class BasicAttr(Attr):
    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        self.value = td.text.strip()


class DefaultAttr(BasicAttr):
    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(name, title, td)
        self.name = name


class CompareAttr(Attr):
    NAME = 'compareParts'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        # todo


class DatasheetAttr(Attr):
    NAME = 'datasheet'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        links = td.select('a.lnkDatasheet')
        if links:
            self.link = links[0].attrs.get('href').strip()
        else:
            self.link = None


class ImageAttr(Attr):
    NAME = 'image'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        img = td.find('img')
        if 'NoPhoto' in img.attrs.get('src', ''):
            self.value: str = None
        else:
            self.value = img.attrs.get('zoomimg')


class PartNoAttr(Attr):
    NAME = 'dkPartNumber'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)

        link = td.find('a', recursive=False)
        self.link = link.attrs['href']
        self.number = link.text.strip()

        rohs = td.find('img', class_='rohs-foilage')
        if rohs:
            self.rohs = rohs.attrs['alt']
        else:
            self.rohs = None


class MfgPartNoAttr(BasicAttr):
    NAME = 'mfgPartNumber'


class VendorAttr(BasicAttr):
    NAME = 'vendor'


class DescriptionAttr(BasicAttr):
    NAME = 'description'


class AbstractDesktopAttr(Attr):
    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        sp = td.find('span', class_='desktop')
        self.value = sp.text.strip()


class QtyAvailAttr(AbstractDesktopAttr):
    NAME = 'qtyAvailable'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(name, title, td)
        parts = self.value.split('-')
        value, self.availability = (p.strip() for p in parts)
        self.value = atoi(value)


class PriceAttr(Attr):
    NAME = 'unitPrice'
    CURR_RE = re.compile(r'^(\D+?)\s*(\d+.*)$')

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        text = td.find('span').find(text=True, recursive=False)
        self.curr, value = self.CURR_RE.match(text.strip()).groups()
        self.value = atof(value)


class MinQtyAttr(AbstractDesktopAttr):
    NAME = 'minQty'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(name, title, td)

        parts = self.value.split()
        self.value = atoi(parts[0])

        if len(parts) > 1:
            self.stock_title = parts[1]
        else:
            self.stock_title: str = None


class PackagingAttr(Attr):
    NAME = 'packaging'

    def __init__(self, name: str, title: str, td: Tag):
        super().__init__(title)
        self.value = td.find(text=True, recursive=False).strip()


class SeriesAttr(BasicAttr):
    NAME = 'series'


_attrs: Dict[str, Type[Attr]] = {T.NAME: T for T in (
    CompareAttr,
    DatasheetAttr,
    ImageAttr,
    PartNoAttr,
    MfgPartNoAttr,
    VendorAttr,
    DescriptionAttr,
    QtyAvailAttr,
    PriceAttr,
    MinQtyAttr,
    PackagingAttr,
    SeriesAttr,
)}


def update(head: str, td: Tag) -> Attr:
    """
    Update a developing part dictionary based on a cell from the product table
    :param head: The head string from the <th>
    :param   td: The <td> from the product table
    :return      The applicable CSS class, and the dictionary with kvs to update.
    """

    cls: str = td.attrs['class'][0]
    if cls.startswith('tr-'):
        name = cls.split('-', 1)[1]
    else:
        name = None

    attr_t = _attrs.get(name, DefaultAttr)
    return attr_t(name, head, td)
