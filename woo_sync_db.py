import time


def compare_dress(parse_list, bigmoda_dresses, bigmoda_exc, wcapi_conn):
    '''
    Compare avaliability sizes supplier and site customer, and add or delete sizes on site
    :param parse_list: list
    :param bigmoda_dresses: list
    :param bigmoda_exc: list
    :param wcapi_conn: woocommerce API object
    :return: boolean
    '''
    for dress in parse_list:
        if dress not in bigmoda_exc:
            for bm_drs in bigmoda_dresses:
                product_id = bm_drs[3]
                product_size_id = bm_drs[4]
                if dress[0] == bm_drs[0]:
                    size_to_add = list()
                    for size in dress[1]:
                        if size not in bm_drs[1]:
                            size_to_add.append(size)
                            data = {
                                'description': '',
                                'regular_price': str(dress[2]),
                                'tax_status': 'taxable',
                                'tax_class': '',
                                'attributes': [
                                    {
                                        "id": 1,
                                        "name": "Размер",
                                        "option": size
                                    }
                                ],
                            }
                            attributes = wcapi_conn.get('products/%s' % (product_id)).json()
                            for attribute in attributes['attributes']:
                                if attribute['name'] == 'Размер':
                                    if size not in attribute['options']:
                                        attribute['options'].append(size)
                                        wcapi_conn.put('products/%s' % (product_id), attributes)
                                        wcapi_conn.post('products/%s/variations' % (product_id), data)
                                    else:
                                        wcapi_conn.post('products/%s/variations' % (product_id), data)
                    if len(size_to_add) != 0:
                        with open('добавить удалить размеры.txt', 'a', encoding='utf-8') as file:
                            file.write('Добавить размеры: {}, {}, {}\n'.format(dress[0], size_to_add, dress[2]))
                    size_to_del = list()
                    for size in bm_drs[1]:
                        if size not in dress[1]:
                            size_to_del.append(size)
                            try:
                                wcapi_conn.delete('products/%s/variations/%s' % (product_id, product_size_id[size]))
                            except KeyError:
                                print('Ошибка: С товаром %s с размером %s что то не так' % (bm_drs[0], size))
                    if len(size_to_del) != 0:
                        with open('добавить удалить размеры.txt', 'a', encoding='utf-8') as file:
                            file.write('Удалить размеры: {}, {}, {}\n'.format(dress[0], size_to_del, dress[2]))
    return True


def del_item(goods_data, bigmoda_pages, wcapi_conn):
    '''
    Check availability goods on Bigmoda and supplier, then publish or delete goods
    :param goods_data: list
    :param wcapi_conn: woocommerce API object
    :return: list
    '''
    names = [i[0] for i in goods_data]
    bm_names_dress = [i[0] for i in bigmoda_pages[0]]
    bm_names_blouse = [i[0] for i in bigmoda_pages[1]]
    bm_names_exc = [i[0] for i in bigmoda_pages[2]]
    woo_items = _get_woo_items_id(wcapi_conn)
    for bm_dress in bigmoda_pages[0]:
        if bm_dress[0] not in names and bm_dress[0] not in bm_names_exc:
            for size, size_id in bm_dress[4].items():
                wcapi_conn.delete('products/%s/variations/%s' % (bm_dress[3], size_id))
            data = {
                'status': 'private',
                'catalog_visibility': 'hidden'
            }
            wcapi_conn.put('products/%s' % (bm_dress[3]), data)
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_dress[0]))
    for bm_blouse in bigmoda_pages[1]:
        if bm_blouse[0] not in names and bm_blouse[0] not in bm_names_exc:
            for size, size_id in bm_blouse[4].items():
                wcapi_conn.delete('products/%s/variations/%s' % (bm_blouse[3], size_id))
            data = {
                'status': 'private',
                'catalog_visibility': 'hidden'
            }
            wcapi_conn.put('products/%s' % (bm_blouse[3]), data)
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_blouse[0]))
    for name in goods_data:
        if name[0] not in bm_names_dress and name[0] not in bm_names_blouse and name[0] not in bm_names_exc:
            if name[4] is True:
                if name[0].split(' ')[0] == 'Краса':
                    chart_id = '13252'
                elif name[0].split(' ')[0] == 'Новита':
                    chart_id = '3046'
                elif name[0].split(' ')[0] == 'Авигаль':
                    chart_id = '10850'
                elif name[0].split(' ')[0] == 'Прима':
                    chart_id = '6381'
                else:
                    chart_id = '3769'
                data = {
                    'name': '%s %s' % (name[3], name[0]),
                    'type': 'variable',
                    'status': 'private',
                    'catalog_visibility': 'hidden',
                    'sku': '%s' % (name[0]),
                    'regular_price': '%s' % (name[2]),
                    'categories': [
                        {
                            'slug': '%s' % ('platya-bolshih-razmerov'
                                            if name[3] == 'Платье' or
                                               name[3] == 'Костюм' else 'bluzki-bolshih-razmerov'),
                            'name': '%s' % ('Платья больших размеров'
                                            if name[3] == 'Платье' or
                                               name[3] == 'Костюм' else 'Блузки больших размеров'),
                            'id': '%i' % (11 if name[3] == 'Платье' or name[3] == 'Костюм' else 16)
                        }
                    ],
                    'attributes': [
                        {
                            'position': 0,
                            'name': 'Цвет',
                            'visible': False,
                            'options': ['Мультиколор'],
                            'id': 2,
                            'variation': False
                        },
                        {
                            'position': 1,
                            'name': 'Размер',
                            'visible': True,
                            'options': name[1],
                            'id': 1,
                            'variation': True
                        },
                        {
                            'position': 2,
                            'name': 'Состав',
                            'visible': False,
                            'options': ['Полиэстер'],
                            'id': 3,
                            'variation': False
                        }

                    ],
                    'meta_data': [
                        {
                            'key': 'prod-chart',
                            'value': '%s' % (chart_id),
                        }
                    ]
                }
                product = wcapi_conn.post('products', data).json()
                if 'message' in product and product['message'] == 'Неверный или дублированный артикул.':
                    for size in name[1]:
                        data = {
                            'description': '',
                            'regular_price': '%s' % (name[2]),
                            'tax_status': 'taxable',
                            'tax_class': '',
                            'attributes': [
                                {
                                    "id": 1,
                                    "name": "Размер",
                                    "option": size
                                }
                            ],
                        }
                        wcapi_conn.post('products/%s/variations' % (product['data']['resource_id']), data).json()
                    wcapi_conn.put('products/%s' % (product['data']['resource_id']),
                                   data={'status': 'publish', 'catalog_visibility': 'visible'}).json()
                else:
                    for size in name[1]:
                        data = {
                            'description': '',
                            'regular_price': '%s' % (name[2]),
                            'tax_status': 'taxable',
                            'tax_class': '',
                            'attributes': [
                                {
                                    "id": 1,
                                    "name": "Размер",
                                    "option": size
                                }
                            ],
                        }
                        wcapi_conn.post('products/%s/variations' % (product['id']), data)
                with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                    file.write('Добавить карточку: {} {} {}\n'.format(name[0], name[1], name[2]))
            else:
                for item in woo_items:
                    if item[0] == name[0]:
                        item_id = item[1]
                        search_res = wcapi_conn.get('products/%s' % (item_id)).json()
                        with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                            file.write('Добавить карточку: {} {} {}\n'.format(name[0], name[1], name[2]))
                        for attribute in search_res['attributes']:
                            if attribute['name'] == 'Размер':
                                for size in name[1]:
                                    data = {
                                        'description': '',
                                        'regular_price': str(name[2]),
                                        'tax_status': 'taxable',
                                        'tax_class': '',
                                        'attributes': [
                                            {
                                                "id": 1,
                                                "name": "Размер",
                                                "option": size
                                            }
                                        ],
                                    }
                                    if size not in attribute['options']:
                                        attribute['options'].append(size)
                                        wcapi_conn.put('products/%s' % (search_res['id']), search_res)
                                        wcapi_conn.post('products/%s/variations' % (search_res['id']), data)
                                    else:
                                        wcapi_conn.post('products/%s/variations' % (search_res['id']), data)
                        wcapi_conn.put('products/%s' % (search_res['id']),
                                       data={'status': 'publish', 'catalog_visibility': 'visible'})

    return goods_data


def _get_woo_items_id(wcapi_conn):
    '''
    Create list of woocommerce goods with ID
    :param wcapi_conn: woocommerce API object
    :return: list
    '''
    result = list()
    for page in range(1, 1000):
        q = wcapi_conn.get('products/?page=%s' % (page)).json()
        if list(q):
            for item in q:
                if item['id']:
                    result.append([item['sku'], item['id']])
        else:
            break
        time.sleep(1)
    return result
