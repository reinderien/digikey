from itertools import chain


class Param:
    def __init__(self, title, name, default=None):
        self.title, self.name, self.default = title, name, default

    def validate(self, value):
        return True


class BoolParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return value in (None, 0, 1)


class UIntParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return isinstance(value, int) and value >= 0


class MultiParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        try:
            iter(value)
            return True
        except TypeError:
            return False


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
SHARED_PARAMS = (BoolParam('In Stock', 'stock', 1),
                 BoolParam('Normally Stocking', 'nstock'),
                 BoolParam('New Products', 'newproducts'),
                 BoolParam('Datasheet Available', 'datasheet'),
                 BoolParam('Photo Available', 'photo'),
                 BoolParam('CAD Model Available', 'cad'),
                 BoolParam('ROHS-compliant', 'rohs'),
                 BoolParam('Non-ROHS-compliant', 'nonrohs'),
                 UIntParam('Quantity', 'quantity'),
                 MultiParam('Keywords', 'k'))


class Searchable:
    def __init__(self, session, title, path):
        self.session, self.title, self.path = session, title, path
        self.params = None

    def init_params(self):
        self.params = {p.title: p for p in
                       chain(SHARED_PARAMS, self._get_addl_params())}

    def search(self, param_values):
        """
        :param param_values: A dictionary of {param object: value}
        :return:
        """
        print('Searching in %s...' % self.title)

        qps = {}
        for param, val in param_values.items():
            assert(isinstance(param, Param))
            if not param.validate(val):
                raise ValueError('"%s" is not a valid value for %s %s' %
                                 (str(val), type(param).__name__, param.title))
            qps[param.name] = str(val)
        return self.session.get_doc(self.path, qps)

    def _get_addl_params(self):
        return ()
