from itertools import chain


class Searchable:
    """
    Top-level parent class for all searchable areas in DigiKey.
    """

    def __init__(self, session, title, path):
        """
        :param session: session object, to use for requests
        :param   title: title string, to use during status output
        :param    path: URL path portion associated with this searchable area
        """
        self.session, self.title, self.path = session, title, path
        self.params = None

    def init_params(self):
        """
        Initialize parameter information for this area. _get_addl_params() is called on the child,
        which may require a GET.
        """
        self.params = {p.title: p for p in
                       chain(self.session.shared_params.values(), self._get_addl_params())}

    def search(self, param_values, extra_qps=None):
        """
        :param param_values: A dictionary of {param name: value}. Each value must be valid for its
                             parameter.
        :param    extra_qps: A dictionary of extra query parameters (simple strings, not Params)
        :return:             A BeautifulSoup document for the search results. It's up to children to
                             override this and translate the document into an iterable of search
                             results.
        """
        print('Searching in %s...' % self.title)

        bad_keys = set(param_values.keys()) - set(self.params.keys())
        if bad_keys:
            raise ValueError('Bad parameter keys: ' + ','.join(bad_keys))

        if extra_qps:
            qps = dict(extra_qps)
        else:
            qps = {}
        for param_title, param in self.params.items():
            value = param_values.get(param_title)
            if not param.validate(value):
                raise ValueError('"%s" is not a valid value for %s %s' %
                                 (str(value), type(param).__name__, param.title))
            k, v = param.qp_kv(value)
            if k:
                qps[k] = v
        return self.session.get_doc(self.path, qps)

    def _get_addl_params(self):
        """
        Get additional parameters applicable to this search area. By default, the parent simply
        returns an empty tuple.
        :return: An iterable of k-v tuples representing any parameters other than those in
                 SHARED_PARAMS.
        """
        return ()
