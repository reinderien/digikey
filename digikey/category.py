from bs4 import NavigableString
from .search import MultiParam, Searchable


class Filter(MultiParam):
    def __init__(self, head, cell):
        select = cell.find(name='select', recursive=False)
        self.options = {o.text.strip(): o.attrs['value']
                        for o in select.find_all(name='option')}
        self.option_titles = set(self.options.keys())
        super().__init__(title=head, name=select.attrs['name'])
        # todo - deal with min/max selection

    def validate(self, value):
        return isinstance(value, set) and not (value - self.option_titles)


class Category(Searchable):
    import re
    rex_count = re.compile(r'\((\d+)')

    def __init__(self, session, group, elm):
        a = elm.find(name='a', recursive=False)
        self.short_title = a.text
        self.group = group
        super().__init__(session=session, path=a.attrs['href'],
                         title='%s/%s' % (group.title, self.short_title))

        for child in elm.children:
            if isinstance(child, NavigableString):
                match = Category.rex_count.search(child)
                if match:
                    self.size = int(match.group(1))
                    break

    def _get_addl_params(self):
        print('Initializing search for category %s...' % self.title)

        doc = self.session.get_doc(self.path + '?pageSize=0')
        headers = doc.find(id='appliedFilterHeaderRow')
        col_names = (e.text for e in headers.find_all(name='th'))
        filter_row = doc.find(name='tr', id='appliedFilterOptions')
        filter_cells = filter_row.find_all(name='td', class_='ptable-param')
        return (Filter(head, cell) for head, cell in zip(col_names, filter_cells))
