from itertools import chain


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

    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

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

    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return (value is None) or (isinstance(value, int) and value >= 0)


class MultiParam(Param):
    """
    Search parameter that can take multiple string values. Requests does the magic of converting
    this to k=v1&k=v2&k=v3...
    """

    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        if value is None:
            return True   # None means unspecified; this is fine
        try:
            iter(value)   # Try converting this to iter; if it's iterable...
            return True   # then it's fine
        except TypeError:
            return False  # not iterable, not fine


class ROHSParam(BoolParam):
    """
    This actually controls two QPs: rohs (True) and nonrohs (False).
    """

    def __init__(self, title='ROHS-Compliant', name='rohs', default=None):
        super().__init__(title, name, default)

    def update_qps(self, qps, value=None):
        if value is None:
            value = self.default
        if value is None:
            return
        name = self.name
        if not value:
            name = 'non' + name
        qps[name] = '1'


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
SHARED_PARAMS = (BoolParam('In Stock', 'stock', True),
                 BoolParam('Normally Stocking', 'nstock'),
                 BoolParam('New Products', 'newproducts'),
                 BoolParam('Datasheet Available', 'datasheet'),
                 BoolParam('Photo Available', 'photo'),
                 BoolParam('CAD Model Available', 'cad'),
                 ROHSParam(),  # title, etc. baked in
                 UIntParam('Quantity', 'quantity', 1),
                 MultiParam('Keywords', 'k'))


class Searchable:
    """
    Top-level parent class for all searchable areas in DigiKey.
    """

    def __init__(self, session, title, path):
        """
        :param session: session object, to use for requests
        :param title: title string, to use during status output
        :param path: URL path portion associated with this searchable area
        """
        self.session, self.title, self.path = session, title, path
        self.params = None

    def init_params(self):
        """
        Initialize parameter information for this area. _get_addl_params() is called on the child,
        which may require a GET.
        """
        self.params = {p.title: p for p in
                       chain(SHARED_PARAMS, self._get_addl_params())}

    def search(self, param_values):
        """
        :param param_values: A dictionary of {param name: value}. Each value must be valid for its
                             parameter.
        :return: A BeautifulSoup document for the search results. It's up to children to override
                 this and translate the document into an iterable of search results.
        """
        print('Searching in %s...' % self.title)

        bad_keys = set(param_values.keys()) - set(self.params.keys())
        if bad_keys:
            raise ValueError('Bad parameter keys: ' + ','.join(bad_keys))

        qps = {}
        for param_title, param in self.params.items():
            value = param_values.get(param_title)
            if not param.validate(value):
                raise ValueError('"%s" is not a valid value for %s %s' %
                                 (str(value), type(param).__name__, param.title))
            param.update_qps(qps, value)
        return self.session.get_doc(self.path, qps)

    def _get_addl_params(self):
        """
        Get additional parameters applicable to this search area. By default, the parent simply
        returns an empty tuple.
        :return: An iterable of k-v tuples representing any parameters other than those in
                 SHARED_PARAMS.
        """
        return ()
