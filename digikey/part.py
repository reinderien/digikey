from typing import Iterable

from .attr import Attr


class Part:
    def __init__(self, attrs: Iterable[Attr]):
        self.attrs = tuple(attrs)
        self.attrs_by_name = {attr.NAME: attr
                              for attr in self.attrs
                              if attr.NAME}

    @property
    def vendor(self) -> str:
        return self.attrs_by_name['vendor'].value

    @property
    def dk_part_no(self) -> str:
        return self.attrs_by_name['dkPartNumber'].number

    @property
    def mfg_part_no(self) -> str:
        return self.attrs_by_name['mfgPartNumber'].value

    @property
    def description(self) -> str:
        return self.attrs_by_name['description'].value

    def __str__(self):
        return f'{self.vendor} {self.mfg_part_no} - {self.description}'
