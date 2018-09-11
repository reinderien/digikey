from os import path, mkdir
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import lzma
import pickle
from .param import SHARED_PARAMS
from .search import Searchable


class Session(Searchable):
    """
    This is the top-level object in a DigiKey usage scenario. Although it is re-entrant (if you
    select sensible cache filenames), you should generally only need one.
    """

    def __init__(self, country='US', short_lang='en', long_lang=None, tld=None, currency=None,
                 cache_dir=None, cache_file=None):
        """
        :param    country: Two-letter ("ISO 3166-1 alpha-2") country code; defaults to 'US'.
        :param short_lang: Two-letter ("ISO 639-1") language code; defaults to 'en'.
        :param  long_lang: Language + country ("RFC5646"); defaults to {short_lang}_{country}.
        :param        tld: Top-level domain suffix to 'digikey' hostname; defaults to 'com' if
                           country is US, or the country otherwise.
        :param   currency: ISO 4217 code. As a poor approximation, this defaults to {country} + 'D'.
        :param  cache_dir: Place to store metadata cache. Defaults to '.digikey'.
        :param cache_file: Name of metadata cache file. Defaults to 'session.pickle.xz'.
        """
        from requests import Session as RSession
        self._rsession = RSession()

        # Some fairly poor guesses
        if not long_lang:
            long_lang = '%s_%s' % (short_lang, country)
        if not tld:
            tld = 'com' if country == 'US' else country.lower()
        if not currency:
            currency = country + 'D'

        self.country, self.short_lang, self.long_lang, self.tld, self.currency = \
            country, short_lang, long_lang, tld, currency
        self.base = 'https://www.digikey.' + tld

        self._rsession.cookies.update({'SiteForCur': country,
                                       'cur': currency,
                                       'website#lang': long_lang})
        self._rsession.headers.update({'Accept-Language': '%s,%s;q=0.9' % (long_lang, short_lang),
                                       'Referer': self.base,
                                       'User-Agent': 'Mozilla/5.0'})
        self.categories = {}
        self.groups = {}
        self.cache_dir, self.cache_file = Session._cache_defaults(cache_dir, cache_file)
        self.shared_params = ()  # Not initialized until init_groups()
        super().__init__(session=self, title='All', path='products/' + short_lang)

    @staticmethod
    def _cache_defaults(cache_dir, cache_file):
        """
        Select cache dir and filename defaults.
        :param cache_dir: Cache dir name, or None. Will default to '.digikey'.
        :param cache_file: Cache filename, or None. Will default to 'session.pickle.xz'.
        :return: cache_dir, cache_file.
        """
        if not cache_dir:
            cache_dir = '.digikey'
        if not cache_file:
            cache_file = 'session.pickle.xz'
        cache_file = path.join(cache_dir, cache_file)
        return cache_dir, cache_file

    def init_groups(self):
        """
        Initialize groups and their categories based on some scraping.
        """
        from .group import Group

        self.groups = {g.title: g for g in Group.get_all(self)}
        self.categories = {c.title: c for g in self.groups.values()
                           for c in g.categories.values()}
        self.init_params()

    def init_params(self):
        """
        Initializes search parameters - in this case, both for the session and its groups. This
        depends on there being at least one category already scraped.
        """
        first_cat = next(iter(self.categories.values()))

        # k needed to get the 'deapplySearch' section
        doc = self.get_doc(first_cat.path, {'pageSize': 1, 'k': 'R'})
        self.shared_params = tuple(f.get(doc) for f in SHARED_PARAMS)

        super().init_params()
        for g in self.groups.values():
            g.init_params()

    def get_doc(self, upath, qps=None):
        """
        Use this session to GET a page at the given path.
        :param upath: Path component of the URL
        :param qps: Query parameters dict (optional)
        :return: A BeautifulSoup parser for the result.
        """
        url = urljoin(self.base, upath)
        resp = self._rsession.get(url, params=qps)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')

    def search(self, param_values):
        """
        Search at the top level. Currently not implemented. todo.
        :param param_values: A dictionary of {param name: value}
        :return: Parts? Group counts? Haven't decided yet.
        """
        doc = super().search(param_values)
        # Might go to a category page, or to a group list
        raise NotImplemented()

    def serialize(self):
        """
        Cache this object in the file at {cache_dir}/{cache_file} as given in the constructor.
        This will save metadata including:
        - Groups
        - Categories
        - Category search parameters for any categories upon which init_params has been called
        - Cookies
        - i18n settings (language, country, currency)

        The metadata are pickled and xz-compressed.
        """
        if not path.isdir(self.cache_dir):
            mkdir(self.cache_dir)
        '''
        The session has references to both categories and groups
        Categories have references to params if init_params has been called
        '''
        with lzma.open(self.cache_file, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def try_deserialize(cache_dir=None, cache_file=None):
        """
        Try to load a Session instance from a cache file. The constructor is not called.
        :param  cache_dir: Directory from which metadata are read. Defaults to '.digikey'.
        :param cache_file: Name of metadata cache file. Defaults to 'session.pickle.xz'.
        :return: A Session instance, if the cache exists. None if the cache does not exist.
        """
        cache_dir, cache_file = Session._cache_defaults(cache_dir, cache_file)
        if path.isfile(cache_file):
            print('Restoring cached session...')
            with lzma.open(cache_file, 'rb') as f:
                return pickle.load(f)
