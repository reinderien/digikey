from .category import Category
from .search import Searchable


class Group(Searchable):
    """
    DigiKey currently has 46 product groups. They are searchable. Groups contain categories. Even
    though the list of groups is fairly well-known, make no assumptions; scrape it rather than hard-
    coding it. At least we cache these.
    """

    def __init__(self, session, elm):
        """
        This constructor should only be called internally to Group.
        :param session: The session, for requests.
        :param elm: The <h2> associated with this group.
        """
        super().__init__(session=session, title=elm.text, path=elm.find(name='a').attrs['href'])
        self.categories = {c.short_title: c for c in self._get_categories(elm)}
        self.size = sum(c.size for c in self.categories.values())

    def _get_categories(self, group_elm):
        """
        Initialize the categories for this group via scraping.
        :param group_elm: The group's <h2>
        :return: A generator of all categories for this group
        """
        ul = next(e for e in group_elm.next_siblings if e.name == 'ul')
        for cat_item in ul.find_all(name='li'):
            yield Category(self.session, self, cat_item)

    @staticmethod
    def get_all(session):
        """
        Get all groups.
        :param session: The session to use for requests.
        :return: A generator of all groups for the session.
        """
        print('Initializing category list...')
        doc = session.get_doc(session.path)
        group_heads = doc.select('div#productIndexList > h2')
        if not group_heads:
            raise ValueError('Failed to find product index list.')

        for group_head in group_heads:
            yield Group(session, group_head)

    def search(self, param_values):
        """
        Search the whole group. Currently not implemented. todo.
        :param param_values: Dict of search parameters.
        :return: Not decided yet?
        """
        doc = super().search(param_values)
        # Might go to a category page, or to a category list
        raise NotImplemented()
