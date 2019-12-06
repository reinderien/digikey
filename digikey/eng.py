import re

POS_CHARS = 'kMGTPEZY'
NEG_CHARS = 'mμnpfazy'


def si_to_int(s: str, base: int=1000):
    match = re.search(r'(\d+)(\D)', s)
    x, pre = match.groups()
    x = int(x)

    try:
        exp = 1 + POS_CHARS.lower().index(pre.lower())
    except ValueError:
        return x

    return x*base**exp
