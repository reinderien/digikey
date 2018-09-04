class Param:
    """
    Top-level parent class for search parameters.
    """

    def __init__(self, title, name, default=None):
        """
        :param   title: Human-legible parameter title
        :param    name: Internal name
        :param default: Default value for this parameter
        """
        self.title, self.name, self.default = title, name, default

    def validate(self, value):
        """
        Validate this parameter. 'None' should be acceptable and indicates 'unspecified'. No
        exception should be thrown from this method. This method is overridden in other parameter
        child classes.
        :param value: The value of this parameter to verify.
        :return: Boolean, whether value is valid. This parent will always return True.
        """
        return True

    def update_qps(self, qps, value=None):
        """
        Given a dictionary of query parameters, add the value for this param.
        :param qps: Dict of query parameters to be passed to Requests
        :param value: Value to add. Will only be added if not None.
        """
        if value is None:
            value = self.default
        if value is not None:
            qps[self.name] = str(value)


class BoolParam(Param):
    """
    Boolean search parameter. Internally maps (False, True) to (0, 1).
    """

    def validate(self, value):
        return value in (None, False, True)

    def update_qps(self, qps, value=None):
        if value is None:
            value = self.default
        if value is not None:
            qps[self.name] = 1 if value else 0


class UIntParam(Param):
    """
    Unsigned integer search parameter.
    """

    def validate(self, value):
        return (value is None) or (isinstance(value, int) and value >= 0)


class MultiParam(Param):
    """
    Search parameter that can take multiple string values. Requests does the magic of converting
    this to k=v1&k=v2&k=v3...
    """

    def validate(self, value):
        if value is None:
            return True  # None means unspecified; this is fine
        try:
            iter(value)  # Try converting this to iter; if it's iterable...
            return True  # then it's fine
        except TypeError:
            return False  # not iterable, not fine


class ROHSParam(BoolParam):
    """
    This actually controls two QPs: rohs (True) and nonrohs (False).
    """

    def update_qps(self, qps, value=None):
        if value is None:
            value = self.default
        if value is None:
            return
        name = self.name
        if not value:
            name = 'non' + name
        qps[name] = '1'


class Filter(MultiParam):
    """
    A multi-valued filter parameter represented as a set. The set of allowed values is
    represented as a dict of {title: internal val}.
    """

    def __init__(self, head, cell, default=None):
        """
        :param    head: The head elm from the filter table
        :param    cell: The cell elm from the filter table
        :param default: Set of default values for this filter, or None
        """
        select = cell.find(name='select', recursive=False)
        self.options = {o.text.strip(): o.attrs['value']
                        for o in select.find_all(name='option', recursive=False)}
        self.option_titles = set(self.options.keys())
        super().__init__(title=head, name=select.attrs['name'], default=default)
        # todo - deal with min/max selection

    def validate(self, value):
        if value is None:
            return True
        return isinstance(value, set) and not (value - self.option_titles)

    def update_qps(self, qps, value=None):
        if value is None:
            value = self.default
        if value:
            qps[self.name] = {self.options[v] for v in value}


"""
List of well-known params:

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


class SharedParamFactory:
    def __init__(self, get_title, T, name, default=None):
        self.T, self.name, self.get_title, self.default = T, name, get_title, default

    def get(self, doc):
        title = self.get_title(doc)
        return self.T(title, self.name, self.default)

    @staticmethod
    def label_from(doc, name):
        return doc.find('label', attrs={'for': name}).text.strip()

    @classmethod
    def checkbox(cls, name, default=None, T=BoolParam):
        def inner(doc):
            return cls.label_from(doc, name)

        return cls(inner, T, name, default)

    @classmethod
    def media_checkbox(cls, name, default=None):
        def inner(doc):
            head = doc.select('div#f2 > div.filters-group-chkbxs > '
                              'div:nth-of-type(2) '
                              'li.advfilterheading')[0].text.strip()
            label = cls.label_from(doc, name)
            return '%s - %s' % (head, label)

        return cls(inner, BoolParam, name, default)

    @classmethod
    def quantity(cls):
        def inner(doc):
            # This is bad - parse 'Quantity' out of 'Enter Quantity'
            # This is definitely wrong for some languages
            qty = doc.find('input', id='qty').attrs['placeholder']
            if ' ' in qty:
                return qty.rsplit(' ', maxsplit=1)[-1]
            return qty
        return cls(inner, UIntParam, 'quantity', 1)


SPF = SharedParamFactory
SHARED_PARAMS = (SPF.checkbox('stock', True),
                 SPF.checkbox('nstock'),
                 SPF.checkbox('newproducts'),
                 SPF.media_checkbox('datasheet'),
                 SPF.media_checkbox('photo'),
                 SPF.media_checkbox('cad'),
                 SPF.checkbox('rohs', T=ROHSParam),
                 SPF.quantity())