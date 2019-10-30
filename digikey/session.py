from bs4 import BeautifulSoup
from http.cookiejar import parse_ns_headers
from locale import setlocale, LC_ALL
from pathlib import Path
from requests.cookies import RequestsCookieJar, MockRequest
from requests.models import Response
from typing import Union, Dict, TYPE_CHECKING
from urllib.parse import urljoin
import lzma
import pickle
import re

from .param import SHARED_PARAMS
from .search import Searchable

if TYPE_CHECKING:
    from .category import Category
    from .group import Group
    from .param import Param


class Session(Searchable):
    """
    This is the top-level object in a DigiKey usage scenario. Although it is re-entrant (if you
    select sensible cache filenames), you should generally only need one.
    """

    COOKIE_RE = re.compile(
        re.escape(r'setTimeout(function(){document.cookie="')
        + r'([^"]+)'
        + '"'
    )

    def __init__(
        self,
        country='US',
        short_lang='en',
        long_lang: str = None,
        tld: str = None,
        currency: str = None,
    ):
        """
        :param    country: Two-letter ("ISO 3166-1 alpha-2") country code; defaults to 'US'.
        :param short_lang: Two-letter ("ISO 639-1") language code; defaults to 'en'.
        :param  long_lang: Language + country ("RFC5646"); defaults to {short_lang}_{country}.
        :param        tld: Top-level domain suffix to 'digikey' hostname; defaults to 'com' if
                           country is US, or the country otherwise.
        :param   currency: ISO 4217 code. As a poor approximation, this defaults to {country} + 'D'.
        """
        from requests import Session as RSession
        self._rsession = RSession()

        self.country, self.short_lang, self.long_lang, self.tld, self.currency = \
            self._lang_defaults(country, short_lang, long_lang, tld, currency)
        self.base = 'https://www.digikey.' + self.tld
        self.set_locale()

        self._rsession.cookies.update({'SiteForCur': country,
                                       'cur': self.currency,
                                       'website#lang': self.long_lang})
        self._rsession.headers.update({'Accept-Language': '%s,%s;q=0.9' % (self.long_lang, self.short_lang),
                                       'Referer': self.base,
                                       'User-Agent': 'Mozilla/5.0'})
        self.groups: Dict[str, Group] = {}
        self.categories: Dict[str, Category] = {}
        self.shared_params: Dict[str, Param] = {}  # Not initialized until init_groups()

        super().__init__(session=self, title='All', path='products/' + self.short_lang)
        self._bake_cookies()

    @staticmethod
    def _lang_defaults(
            country: str,
            short_lang: str,
            long_lang: str,
            tld: str,
            currency: str) -> (
            str, str, str, str, str):
        # Some fairly poor guesses
        if not long_lang:
            long_lang = '%s-%s' % (short_lang, country)
        if not tld:
            tld = 'com' if country == 'US' else country.lower()
        if not currency:
            currency = country + 'D'
        return country, short_lang, long_lang, tld, currency

    def set_locale(self):
        setlocale(LC_ALL, f'{self.short_lang}_{self.country}.UTF8')

    @classmethod
    def _cache_defaults(
        cls,
        cache_dir: Union[Path, str] = None,
        country='US',
        short_lang='en',
        long_lang: str = None,
        tld: str = None,
        currency: str = None,
    ) -> (Path, Path):
        """
        Select cache dir and filename defaults.
        :param cache_dir: Cache dir name, or None. Will default to '.digikey'.
        :return: cache_dir, cache_file.
        """
        if not cache_dir:
            cache_dir = '.digikey'
        if not isinstance(cache_dir, Path):
            cache_dir = Path(cache_dir)

        country, short_lang, long_lang, tld, currency = cls._lang_defaults(
            country, short_lang, long_lang, tld, currency
        )
        cache_file = cache_dir / f'{short_lang}_{country}_{long_lang}_{tld}_{currency}.xz'
        return cache_dir, cache_file

    def _bake_cookies(self):
        resp = self._get_resp(self.path)
        cookie_match = self.COOKIE_RE.search(resp.text)
        if not cookie_match:
            print('No apparent initialization cookie')
            return

        attrs = parse_ns_headers([cookie_match[1]])

        jar: RequestsCookieJar = self._rsession.cookies
        req = MockRequest(resp.request)
        cookies = jar._cookies_from_attrs_set(attrs, req)
        for cookie in cookies:
            jar.set_cookie(cookie)

        print('Cookies set: ' + ', '.join(jar.keys()))

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
        for factory in SHARED_PARAMS:
            param = factory.get(doc)
            self.shared_params[param.name] = param

        super().init_params()
        for g in self.groups.values():
            g.init_params()

    def _get_resp(self, upath: str, qps: dict = None) -> Response:
        url = urljoin(self.base, upath)
        resp = self._rsession.get(url, params=qps)
        resp.raise_for_status()
        return resp

    def get_doc(self, upath: str, qps: dict = None) -> BeautifulSoup:
        """
        Use this session to GET a page at the given path.
        :param upath: Path component of the URL
        :param qps: Query parameters dict (optional)
        :return: A BeautifulSoup parser for the result.
        """
        resp = self._get_resp(upath, qps)
        return BeautifulSoup(resp.text, 'html.parser')

    def search(self, param_values: Dict[str, object]):
        """
        Search at the top level. Currently not implemented. todo.
        :param param_values: A dictionary of {param name: value}
        :return: Parts? Group counts? Haven't decided yet.
        """
        doc = super().search(param_values)
        # Might go to a category page, or to a group list
        raise NotImplemented()

    def serialize(self, cache_dir: Union[Path, str] = None):
        """
        Cache this object in the file at {cache_dir}/{cache_file} as given in the constructor.
        This will save metadata including:
        - Groups
        - Categories
        - Category search parameters for any categories upon which init_params has been called
        - Cookies
        - i18n settings (language, country, currency)

        The metadata are pickled and xz-compressed.

        :param  cache_dir: Place to store metadata cache. Defaults to '.digikey'.
        """
        cache_dir, cache_file = Session._cache_defaults(
            cache_dir,
            self.country, self.short_lang, self.long_lang, self.tld, self.currency
        )
        if not cache_dir.exists():
            cache_dir.mkdir()
        '''
        The session has references to both categories and groups
        Categories have references to params if init_params has been called
        '''
        with lzma.open(cache_file, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def try_deserialize(
        cls,
        cache_dir: Union[Path, str] = None,
        **kwargs
    ) -> ('Session', bool):
        """
        Try to load a Session instance from a cache file. The constructor is not called.
        :param cache_dir: Directory from which metadata are read. Defaults to '.digikey'.
        :param    kwargs: Locale arguments passed to the Session constructor.
        :return: A Session instance, if the cache exists, a new Session if the cache does not exist;
                 and a boolean - True if the session is new, False if cached.
        """
        cache_dir, cache_file = cls._cache_defaults(cache_dir, **kwargs)
        if not cache_file.is_file():
            return cls(**kwargs), True

        with lzma.open(cache_file, 'rb') as f:
            sess: Session = pickle.load(f)
        sess.set_locale()
        return sess, False
