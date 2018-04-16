from itertools import chain


class Param:
    def __init__(self, title, name, default=None):
        self.title, self.name, self.default = title, name, default

    def validate(self, value):
        return True

    def update_qps(self, qps, value=None):
        if not value:
            value = self.default
        if value is not None:
            qps[self.name] = str(value)


class BoolParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return value in (None, 0, 1)


class UIntParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return (value is None) or (isinstance(value, int) and value >= 0)


class MultiParam(Param):
    def __init__(self, title, name, default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        if value is None:
            return True
        try:
            iter(value)
            return True
        except TypeError:
            return False


class ROHSParam(Param):
    def __init__(self, title='ROHS-Compliant', name='rohs', default=None):
        super().__init__(title, name, default)

    def validate(self, value):
        return value in ('y', 'n', None)

    def update_qps(self, qps, value=None):
        if not value:
            value = self.default
        if value == 'y':
            name = self.name
        elif value == 'n':
            name = 'non' + self.name
        else:
            return
        qps[name] = '1'


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
                 ROHSParam(),
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
        return ()
