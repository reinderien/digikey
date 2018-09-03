Existing Work
-------------

[DigiGlass](https://github.com/mplewis/digiglass) - Python, uses BeautifulSoup scraping

[python-digikey](https://github.com/forrestv/python-digikey) - Python, uses BeautifulSoup scraping

[ApiClient](https://github.com/digikey/ApiClient) - "Official" C# API client

[OctoPart](https://octopart.com/api/home) - Non-DigiKey-specific, includes Digikey support

Design Thoughts
---------------

There is an official API, but (1) it's rate-limited, and (2) it requires the registration of a
publicly reachable redirect URL for OAuth, even though searching should not require authentication.

There are other implementations of BS-based scraping, but what the heck, I'll try my own; it's fun.

DigiKey Architecture
--------------------

Content is hierarchical: Groups are the top level; currently there are 46. Within groups are 
categories; currently there are 898.

There are three levels that are searchable - the top ("session"), a group, and a category. Parsing
results is slightly complex because, depending on context, you might get back a list of categories,
the component filter interface, or the page for a single component. Searching within a category
using the component filter requires that the parameters be first initialized by scraping a blank
search.

Some basic information, such as the group and category lists, should be cached. This is 500kB+
when pickled, 100kB+ compressed.