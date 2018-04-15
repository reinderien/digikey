class Filter:
    def __init__(self, head, cell):
        self.title = head
        select = cell.find(name='select', recursive=False)
        self.field = select.attrs['name']
        self.options = {o.text.strip(): o.attrs['value']
                        for o in select.find_all(name='option')}


class CatSearch:
    def __init__(self, session, category):
        """
        k=             "Search within results" keyword (can appear more than once)
        pkeyword=      Previous keyword???
        quantity=0     Quantity of parts you expect to order
        ColumnSort=0
        page=1         1-based pagination index
        pageSize=25    pagination size

        stock=1        In Stock
        nstock=1       Normally Stocking
        newproducts=1  New products
        datasheet=1    Datasheet required
        photo=1        Photo required
        cad=1          EDA/CAD models required
        rohs=1         ROHS compliance required
        nonrohs=1      ROHS compliance disallowed

        Part status listbox
        pv1989=0       Active
               1       Obsolete
               2       Discontinued
               4       Last Time Buy
               7       Not for new designs
        """
        print('Initializing search for category %s...' %
              category.full_title)

        doc = session.get_doc(category.path + '?pageSize=0')
        headers = doc.find(id='appliedFilterHeaderRow')
        col_names = (e.text for e in headers.find_all(name='th'))
        filter_row = doc.find(name='tr', id='appliedFilterOptions')
        filter_cells = filter_row.find_all(name='td', class_='ptable-param')
        filters = (Filter(head, cell) for head, cell in zip(col_names, filter_cells))
        self.filters = {fil.title: fil for fil in filters}


class GroupSearch:
    pass


class GlobalSearch:
    pass
