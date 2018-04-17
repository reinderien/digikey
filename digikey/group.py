from .category import Category
from .search import Searchable


class Group(Searchable):
    def __init__(self, session, elm):
        super().__init__(session=session, title=elm.text, path=elm.find(name='a').attrs['href'])
        super().init_params()
        self.categories = {c.title: c for c in self._get_categories(elm)}
        self.size = sum(c.size for c in self.categories.values())

    def _get_categories(self, group_elm):
        ul = next(e for e in group_elm.next_siblings if e.name == 'ul')
        for cat_item in ul.find_all(name='li'):
            yield Category(self.session, self, cat_item)

    @staticmethod
    def get_all(session):
        print('Initializing category list...')
        doc = session.get_doc(session.path)
        group_heads = doc.select('div#productIndexList > h2')
        for group_head in group_heads:
            yield Group(session, group_head)

    def search(self, param_values):
        doc = super().search(param_values)
        # Might go to a category page, or to a category list
        raise NotImplemented()
