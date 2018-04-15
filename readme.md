Existing Work
-------------

[DigiGlass](https://github.com/mplewis/digiglass) - Python, uses BeautifulSoup scraping

[python-digikey](https://github.com/forrestv/python-digikey) - Python, uses BeautifulSoup scraping

[ApiClient](https://github.com/digikey/ApiClient) - "Official" C# API client

[OctoPart](https://octopart.com/api/home) - Non-DigiKey-specific, includes Digikey support

Design Thoughts
---------------

There is an official API, but (1) it's rate-limited, and (2) it requires the registration of a publicly reachable
redirect URL for OAuth, even though searching should not require authentication.

