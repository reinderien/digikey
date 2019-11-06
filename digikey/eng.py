import re

POS_CHARS = 'kMGTPEZY'
NEG_CHARS = 'mμnpfazy'


def iec_to_int(s: str):
    match = re.search(r'(\d+)(.*)B', s)
    x, pre = match.groups()
    x = int(x)

    try:
        exp = 1 + POS_CHARS.lower().index(pre.lower())
    except ValueError:
        return x

    return x*2**(10 * exp)
