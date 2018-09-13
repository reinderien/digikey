import re
from bs4 import NavigableString
from itertools import count
from .attr import update as update_attr
from .param import Param, Filter, SharedParamFactory
from .search import Searchable


class SortParam(Param):
    """
    Search parameter controlling result order. Value is of the form (t, dirn) where t is any of the
    column titles, and dirn is either True (ascending) or False (descending).
    """

    rex_sort = re.compile(r'sort\(([0-9\-]+)\);')

    def __init__(self, heads, title, doc, default=None):
        """
        :param     doc: BeautifulSoup doc of the filter page
        :param default: None, or ('col', bool)
        """
        super().__init__(title=title, name='ColumnSort', default=default)

        # Dict of {title: code}
        self.by = {}

        table = doc.find(name='table', id='productTable')
        cells = table.select('thead#tblhead > tr:nth-of-type(2) > td')

        for head, cell in zip(heads, cells):
            # Take the first (ascending) button only.
            button = cell.find(name='button', class_='ps-sortButtons')
            if not button:
                continue
            img = button.find(name='img', class_='nonsorted')
            _, _, dirn = img.attrs['src'].rpartition('/')
            assert(dirn.startswith('up'))

            code = int(SortParam.rex_sort.search(button.attrs['onclick'])[1])
            assert(code > 0)
            self.by[head] = code

    def validate(self, value):
        if value is None:
            return True
        if not isinstance(value, tuple) or len(value) != 2:
            return False
        by, dirn = value
        return by in self.by and isinstance(dirn, bool)

    def update_qps(self, qps, value=None):
        if value is None:
            value = self.default
        title, dirn = value
        code = self.by[title]
        if not dirn:
            code = -code
        qps[self.name] = code


class Category(Searchable):
    """
    Category is a subdivision of a group. Currently there are 898 categories in total. Searching
    within a category is the most common operation, due to the powerful filtration interface.
    """

    rex_count = re.compile(r'\((\d+)')
    rex_page = re.compile(r'(\d+)/(\d+)$')

    def __init__(self, session, group, elm):
        """
        :param session: The digikey.session to use for requests
        :param   group: The parent group object
        :param     elm: The <li> corresponding to the category in the product index
        """
        a = elm.find(name='a', recursive=False)
        self.short_title = a.text
        self.group = group
        self.heads = ()  # Initialized during _get_addl_params
        super().__init__(session=session, path=a.attrs['href'],
                         title='%s/%s' % (group.title, self.short_title))

        for child in elm.children:
            if isinstance(child, NavigableString):
                match = Category.rex_count.search(child)
                if match:
                    self.size = int(match[1])
                    break

    def _get_addl_params(self):
        print('Initializing search for category %s...' % self.title)

        doc = self.session.get_doc(self.path, {'pageSize': 1})

        # This has changed quite recently - it's now a set of divs instead of a table
        filter_div = doc.find(name='div', class_='filters-group')
        headers = filter_div.find_all(name='span', class_='filters-headline')
        cells = filter_div.find_all(name='select', class_='filter-selectors')
        prod_table = doc.find(name='table', id='productTable')

        datasheet_head = SharedParamFactory.label_from(doc, 'datasheet')
        self.heads = tuple(Category.get_heads(prod_table, datasheet_head))

        status_head = self._get_part_status_head(doc)
        price_head = Category._get_price_head(doc)
        sort_head = Category._get_sort_head(doc)

        filters = [SortParam(self.heads, sort_head, doc, default=(price_head, True))]
        for head, cell in zip(headers, cells):
            title = head.text
            filt = Filter(title, cell)
            if title == status_head:
                # '0' is hard-coded because 'Active' is not language-independent
                filt.default = {next(k for k,v in filt.options.items() if v=='0')}
            filters.append(filt)
        return filters

    def _get_part_status_head(self, doc):
        """
        Get the language-variant 'Part Status' heading string
        :param doc: The BS4 doc for the filter page
        :return: The part status heading string appropriate for session.short_lang
        """
        table = doc.find(name='table', id='productTable')
        result_cells = table.select('tbody#lnkPart > tr:nth-of-type(1) > td')
        for head, cell in zip(self.heads, result_cells):
            span = cell.find(name='span', id='part-status')
            if span:
                return head

    @classmethod
    def _get_price_head(cls, doc):
        th = doc.select('table#productTable > thead > '
                        'tr:nth-of-type(1) > th.th-unitPrice')[0]
        return cls._title_from_price_head(th)

    @staticmethod
    def _title_from_price_head(th):
        # leave out the whitespace and currency.
        return th.text.splitlines()[1].strip()

    @staticmethod
    def _get_sort_head(doc):
        """
        This one is trickier. There's no clear Sort Order text on the page; only
        Ascending/Descending in the up/down image alt.
        :param doc: The BS4 doc object to scrape.
        :return: A reasonable title for sort order. Currently it will take the form
                 Ascending/Descending (in the configured language).
        """
        imgs = doc.select('button.ps-sortButtons > img.sorted')
        alts = (i.attrs['alt'] for i in imgs[:2])
        return '/'.join(alts)

    @classmethod
    def get_heads(cls, table, datasheet_head):
        """
        :param          table: The results <table> elm containing filters
        :param datasheet_head: The datasheet header text, passed because the header in place is image-only
        :return:               A generator of all filter heading strings
        """
        for th in table.select('thead#tblhead > tr:nth-of-type(1) > th'):
            css_cls = th.attrs['class'][0]
            if css_cls == 'th-datasheet':
                head = datasheet_head  # this is shown as an image, no text.
            elif 'th-unitPrice' in css_cls:
                head = cls._title_from_price_head(th)
            else:
                head = th.text.strip()
            yield head

    def _get_parts(self, table, filter_qty, qty):
        """
        :param      table: The <table> elm containing search results
        :param filter_qty: Bool, whether to filter out rows with invalid min qtys
        :param        qty: The quantity in the request, to compare with min qty
        :return:           A generator of all parts returned
        """
        for tr in table.select('tbody#lnkPart > tr'):
            part = {}
            cells = tr.find_all(name='td', recursive=False)
            for head, td in zip(self.heads, cells):
                cls, upd = update_attr(head, td)
                if filter_qty and cls == 'tr-minQty' and qty is not None:
                    min_qty = next(iter(upd.values()))
                    if min_qty > qty:  # yes, this happens, and it's silly
                        break
                part.update(upd)
            else:
                yield part

    def search(self, param_values, filter_qty=True):
        """
        Search this category. Calls super() to do the param and request work.
        :param param_values: A dict of {'param_title': value}
        :param   filter_qty: Bool, whether to filter out rows with invalid min qtys
        :return:             A generator of the resulting parts.
        """

        qty_param = self.session.shared_params['quantity']
        qty_name, qty = qty_param.qp_kv(param_values.get(qty_param.title))

        for page in count(1):
            doc = super().search(param_values, {'page': page})
            table = doc.select('table#productTable')[0]
            yield from self._get_parts(table, filter_qty, qty)

            page_text = doc.select('span.current-page')[0].text.strip()
            this_page, size = Category.rex_page.search(page_text).groups()
            this_page, size = int(this_page), int(size)
            assert(this_page == page)
            if page >= size:
                break
