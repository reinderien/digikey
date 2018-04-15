import re
from bs4 import NavigableString


class Category:
    rex_count = re.compile(r'\((\d+)')

    def __init__(self, group, elm):
        a = elm.find(name='a', recursive=False)
        self.title = a.text
        self.group = group
        self.path = a.attrs['href']
        self.name, self.code = self.path.split('/')[-2:]
        self.full_title = '%s/%s' % (group.title, self.title)

        for child in elm.children:
            if isinstance(child, NavigableString):
                match = Category.rex_count.search(child)
                if match:
                    self.size = int(match.group(1))
                    break
