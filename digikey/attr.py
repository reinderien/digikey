def update_attr(part, head, td):
    part[head] = td.text.strip()


def update_compare(part, head, td):
    pass


def update_datasheet(part, head, td):
    part[head] = td.select('a.lnkDatasheet')[0].attrs.get('href').strip()


def update_image(part, head, td):
    img = td.find('img')
    if 'NoPhoto' not in img.attrs.get('src', ''):
        part[head] = img.attrs.get('zoomimg')


def update_partno(part, head, td):
    update_attr(part, head, td)
    link = td.find('a', recursive=False)
    part['Link'] = link.attrs['href']  # todo - lang-dependent


def update_desktop(part, head, td):
    sp = td.find('span', class_='desktop')
    part[head] = sp.text.strip()


def update_price(part, head, td):
    text = td.find('span').find(text=True, recursive=False)
    part[head] = text.strip()


def update_packaging(part, head, td):
    text = td.find(text=True, recursive=False)
    part[head] = text.strip()


attrs = {'tr-compareParts': update_compare,
         'tr-datasheet':    update_datasheet,
         'tr-image':        update_image,
         'tr-dkPartNumber': update_partno,
         'tr-qtyAvailable': update_desktop,
         'tr-unitPrice':    update_price,
         'tr-minQty':       update_desktop,
         'tr-packaging':    update_packaging}


def update(part, head, td):
    """
    Update a developing part dictionary based on a cell from the product table
    :param part: The part dictionary to be updated based on this cell
    :param head: The head string from the <th>
    :param   td: The <td> from the product table
    """

    cls = td.attrs['class'][0]
    attr = attrs.get(cls, update_attr)
    attr(part, head, td)
