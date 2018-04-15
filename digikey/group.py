from .category import Category


class Group:
    def __init__(self, elm):
        self.title = elm.text

        self.path = elm.find(name='a').attrs['href']
        self.name, self.code = self.path.split('/')[-2:]
        self.categories = {c.title: c for c in self._get_categories(elm)}
        self.size = sum(c.size for c in self.categories.values())

    def _get_categories(self, group_elm):
        ul = next(e for e in group_elm.next_siblings if e.name == 'ul')
        for cat_item in ul.find_all(name='li'):
            yield Category(self, cat_item)

    @staticmethod
    def get_all(session):
        print('Initializing category list...')
        doc = session.get_doc('products/' + session.short_lang)
        products = doc.find(name='div', id='productIndexList')
        group_heads = products.find_all(name='h2', recursive=False)
        for group_head in group_heads:
            yield Group(group_head)
