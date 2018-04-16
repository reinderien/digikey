from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .search import Searchable


class Session(Searchable):
    def __init__(self, country='US', short_lang='en', long_lang=None, tld=None, currency=None):
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
        super().__init__(session=self, title='All', path='products/' + short_lang)
        super().init_params()

    def init_groups(self):
        from .group import Group

        self.groups = {g.title: g for g in Group.get_all(self)}
        self.categories = {c.title: c for g in self.groups.values()
                           for c in g.categories.values()}

    def get_doc(self, path, qps=None):
        url = urljoin(self.base, path)
        resp = self._rsession.get(url, params=qps)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
