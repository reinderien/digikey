from locale import atoi


def update_attr(head, td):
    return {head: td.text.strip()}


def update_compare(head, td):
    return {}


def update_datasheet(head, td):
    return {head: td.select('a.lnkDatasheet')[0].attrs.get('href').strip()}


def update_image(head, td):
    img = td.find('img')
    if 'NoPhoto' in img.attrs.get('src', ''):
        return {}
    return {head: img.attrs.get('zoomimg')}


def update_partno(head, td):
    d = update_attr(head, td)
    link = td.find('a', recursive=False)
    d['Link'] = link.attrs['href']  # todo - lang-dependent
    return d


def update_desktop(head, td):
    sp = td.find('span', class_='desktop')
    return {head: sp.text.strip()}


def update_price(head, td):
    text = td.find('span').find(text=True, recursive=False)
    return {head: text.strip()}


def update_minqty(head, td):
    d = update_desktop(head, td)
    d[head] = atoi(d[head])
    return d


def update_packaging(head, td):
    text = td.find(text=True, recursive=False)
    return {head: text.strip()}


attrs = {'tr-compareParts': update_compare,
         'tr-datasheet':    update_datasheet,
         'tr-image':        update_image,
         'tr-dkPartNumber': update_partno,
         'tr-qtyAvailable': update_desktop,
         'tr-unitPrice':    update_price,
         'tr-minQty':       update_minqty,
         'tr-packaging':    update_packaging}


def update(head, td):
    """
    Update a developing part dictionary based on a cell from the product table
    :param head: The head string from the <th>
    :param   td: The <td> from the product table
    :return      The applicable CSS class, and the dictionary with kvs to update.
    """

    cls = td.attrs['class'][0]
    attr = attrs.get(cls, update_attr)
    return cls, attr(head, td)
