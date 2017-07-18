import os
import re
import time
import sys
import csv

import requests

from bs4 import BeautifulSoup
from woocommerce import API


def _create_sizes_dict(color_list, sizes_list, sizes_accepted):
    '''
    Create dict of color and sizes of item
    :param color_list: list
    :param sizes_list: list
    :param sizes_accepted: list
    :return: dict
    '''
    i = 0
    temp_dict = dict()
    for color in color_list:
        temp_list = list()
        for item in sizes_accepted[i:i + len(sizes_list)]:
            temp_list.append(item)
            res = {color: temp_list}
            temp_dict.update(res)
        i += len(sizes_list)
    return temp_dict


def novita_parse(url):
    '''
    Parsing Novita Site
    :param url: str
    :return: list
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('div', {'class': 'name'})
    result = list()
    i = 0
    l = len(items_link_list)
    printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = dict()
        try:
            data['name'] = re.search(r'(?<=№)(\d+/\d+)|(?<=№)(\d+)', soup.h1.text.strip()).group(0)
            data['type'] = soup.h1.text.strip().split(' ')
            if 'Акция' in data['type'] and '\'Одна' not in data['type'] and '50%' not in data['type']:
                data['type'] = data['type'][2]
            elif '50%' in data['type']:
                data['type'] = data['type'][4]
            elif '\'Одна' in data['type']:
                data['type'] = data['type'][4]
            else:
                data['type'] = data['type'][0]
            if data['type'] == 'Платье' or data['type'] == 'Блузка' or data['type'] == 'Туника':
                colors = soup.find_all('td', {'class': 'col-color'})
                data['color_list'] = [color.text.strip() for color in colors if color.text.strip() != 'Цвет/размер']
                data['sizes_list'] = soup.find_all('td', {'class': 'inv'})
                data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
                data['color_size'] = {color: data['sizes_list'].copy() for color in data['color_list']}
                data['sizes_accepted'] = soup.find_all('td', {'class': 'tdforselect'})
                data['sizes_accepted'] = ['disabled' if 'disabled' in size_accepted['class'] else 'enabled' for
                                          size_accepted in
                                          data['sizes_accepted']]
                data['price'] = soup.find('div', {'class': 'value'}).text.replace(',', '').split('.')
                data['price'] = data['price'][0]
                color_size_tags = _create_sizes_dict(data['color_list'], data['sizes_list'], data['sizes_accepted'])
                for key, value in color_size_tags.items():
                    for item in range(len(value)):
                        if value[item] == 'disabled':
                            data['color_size'][key].pop(color_size_tags[key].index(value[item]))
                for key in data['color_size']:
                    # print(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'], data['type']])
                    result.append(
                        ['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'],
                         data['type'], False])
        except AttributeError:
            with open('errors.txt', 'a', encoding='utf-8') as err_file:
                err_file.write('Ошибка в карточке: %s \n' % (link))
            i += 1
            printProgressBar(i, l, prefix='Novita Parsing:', suffix='Complete', length=50)
            continue
        time.sleep(0.1)
        i += 1
        printProgressBar(i, l, prefix='Novita Parsing:', suffix='Complete', length=50)

    return result


def primalinea_parse(url):
    '''
    Parsing Primalinea Site
    :param url: str
    :return: list
    '''
    session = requests.Session()
    payload = {'login_name': 'mail@big-moda.com'}
    r = session.post('http://primalinea.ru/customers/login', payload)
    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('a', {'class': 'catalog-item-link'})
    items_link_list = [item.get('href') for item in items_link_list]
    result = list()
    i = 0
    l = len(items_link_list)
    printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)
    for link in items_link_list:
        r = session.get(link)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = dict()
        try:
            data['is_new'] = soup.find('div', attrs={'id': 'catalog-item-tags'}).find('a').text.strip()
            if data['is_new'] == 'Новинки':
                data['is_new'] = True
            else:
                data['is_new'] = False
        except AttributeError:
            data['is_new'] = False
        try:
            data['name'] = soup.h1.text.strip()
            data['type'] = data['name'].split(' ')[1].capitalize() if len(data['name'].split(' ')) > 2 and \
                                                                      'new' not in data['name'].split(' ') \
                else data['name'].split(' ')[0].capitalize()
            if data['type'] == 'Блуза' or data['type'] == 'Кардиган' or data['type'] == 'Туника' or data[
                'type'] == 'Платье':
                data['name'] = data['name'].split(' ')[2] if len(data['name'].split(' ')) > 2 and 'new' not in data[
                    'name'].split(' ') else data['name'].split(' ')[1]
                price = soup.find('div', attrs={'id': 'catalog-item-description'})
                price = re.search(r'(\d+)', price.p.text.strip().replace(' ', ''))
                data['price'] = int(price.group(0)) * 2
                data['sizes_list'] = soup.find_all('option')
                data['sizes_list'] = [item.text for item in data['sizes_list']]
                # print('Прима ' + data['name'].lower(), data['sizes_list'], data['price'], data['type'])
                result.append(['Прима ' + data['name'], data['sizes_list'], data['price'], data['type'], data['is_new']])
        except AttributeError:
            with open('errors.txt', 'a', encoding='utf-8') as err_file:
                err_file.write('Ошибка в карточке: %s \n' % (link))
            i += 1
            printProgressBar(i, l, prefix='Primalinea Parsing:', suffix='Complete', length=50)
            continue
        time.sleep(0.1)
        i += 1
        printProgressBar(i, l, prefix='Primalinea Parsing:', suffix='Complete', length=50)
    return result


def avigal_parse(url):
    '''
    Parsing Avigal Site
    :param url: str
    :return: list
    '''
    session = requests.Session()
    payload = {'email': 'Bigmoda.com@gmail.com', 'password': '010101'}
    r = session.post('http://avigal.ru/login/', payload)
    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    data = dict()
    result = list()
    data['paginaton'] = soup.find_all('div', {'class': 'pagination'})
    data['paginaton'] = data['paginaton'][0].find_all('li')
    data['paginaton_url'] = [url]
    data['item_links'] = list()
    items_link_list = list()
    j = 1
    for page in data['paginaton']:
        try:
            page.a.text
        except AttributeError:
            continue
        if page.a.get('href') not in data['paginaton_url']:
            data['paginaton_url'].append(page.a.get('href'))
    for link in data['paginaton_url']:
        r = session.get(link)
        soup = BeautifulSoup(r.text, 'lxml')
        data['is_new'] = soup.find('div', {'class': 'sticker-novelty'})
        if data['is_new']:
            data['is_new'] = True
        else:
            data['is_new'] = False
        items_link_list = soup.find_all('div', {'class': 'product-about'})
        items_link_list = [item.find('div', attrs={'class': 'name'}).a.get('href') for item in items_link_list]
        i = 0
        l = len(items_link_list)
        printProgressBar(i, l, prefix='Avigal Parsing:',
                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for link in items_link_list:
            r = session.get(link)
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                data['price'] = soup.find('span', attrs={'class': 'micro-price', 'itemprop': 'price'})
                data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
                data['price'] = int(data['price'].group(0)) * 2
                # if data['price'] > 2500:
                data['type'] = soup.find('h1').text.strip()
                data['name'] = soup.find('span', attrs={'itemprop': 'model'})
                data['name'] = data['name'].text
                sizes_list = soup.find_all('label', {'class': 'optid-13'})
                data['sizes_list'] = list()
                for item in sizes_list:
                    if r':n\a' not in item['title']:
                        data['sizes_list'].append(item.text.strip())
                # print('Авигаль ' + data['name'], data['sizes_list'], data['price'], data['type'])
                result.append(
                    ['Авигаль ' + data['name'], data['sizes_list'], data['price'], data['type'], data['is_new']])
            except AttributeError:
                with open('errors.txt', 'a', encoding='utf-8') as err_file:
                    err_file.write('Ошибка в карточке: %s \n' % (link))
                i += 1
                printProgressBar(i, l, prefix='Avigal Parsing:',
                                 suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                continue
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Avigal Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
    return result


def wisell_parse(url):
    '''
    Parsing Wisell Site
    :param url: str
    :return: list
    '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    data = dict()
    result = list()
    last = False
    data['paginaton_url'] = [url]
    while last == False:
        data['paginaton'] = soup.find_all('div', {'class': 'page_navi'})
        pagination_links = data['paginaton'][0].find_all('a', {'class': 'menu_link'})
        if pagination_links[-1].text == 'Следующая':
            r = requests.get('https://wisell.ru' + pagination_links[-1].get('href'))
            soup = BeautifulSoup(r.text, 'lxml')
            data['paginaton'] = soup.find_all('div', {'class': 'page_navi'})
            pagination_links = data['paginaton'][0].find_all('a', {'class': 'menu_link'})
            data['paginaton'] = [item.get('href') for item in pagination_links]
            for link in data['paginaton']:
                if 'https://wisell.ru' + link not in data['paginaton_url']:
                    data['paginaton_url'].append('https://wisell.ru' + link)
        else:
            last = True
    j = 1
    for page in data['paginaton_url']:
        r = requests.get(page, headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        try:
            data['is_new'] = soup.find('span', {'class': 'label_item'}).text
            if data['is_new'] and data['is_new'] == 'Новинка':
                data['is_new'] = True
            else:
                data['is_new'] = False
        except AttributeError:
            data['is_new'] = False
        data['item_links'] = soup.find_all('a', {'class': 'item_title'})
        data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
        i = 0
        l = len(data['item_links'])
        printProgressBar(i, l, prefix='Progress:',
                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for item_link in data['item_links']:
            r = requests.get(item_link, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                data['name'] = soup.find('li', attrs={'class': 'item_lost'})
                data['name'] = data['name'].span.text
                data['type'] = soup.find('h1').text.split(' ')[0]
                if soup.h2.text == 'Нет в наличии':
                    with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                        file.write('Нет в наличии на сайте Wisell: {}\n'.format(data['name']))
                        i += 1
                        printProgressBar(i, l, prefix='Wisell Parsing:',
                                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                    continue
                data['price'] = soup.find('span', attrs={'class': 'price_val'})
                data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
                data['price'] = int(data['price'].group(0))
                if data['price'] < 1800:
                    i += 1
                    printProgressBar(i, l, prefix='Wisell Parsing:',
                                     suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                    continue
                data['sizes_list'] = soup.find_all('ul', {'class': 'size_list'})
                data['sizes_list'] = data['sizes_list'][0].find_all('li', {'class': 'check_item'})
                data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
                data['sizes_list'].pop(0)
                data['sizes_list'].pop(-1)
                data['small_sizes'] = soup.find('ul', attrs={'id': 'size-interval-tabs'}).findAll('li')
                if data['small_sizes'][0]['data-url'] != '' and len(data['small_sizes']) > 1:
                    data['small_sizes'] = 'https://wisell.ru' + data['small_sizes'][0]['data-url']
                    r = requests.get(data['small_sizes'], headers=headers)
                    soup = BeautifulSoup(r.text, 'lxml')
                    small_name = soup.find('li', attrs={'class': 'item_lost'})
                    if small_name.span.text != data['name']:
                        if soup.h2.text == 'Нет в наличии':
                            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                                file.write('Не прошла синхронизация на сайте Wisell: {}\n'.format(small_name.span.text))
                                i += 1
                                printProgressBar(i, l, prefix='Wisell Parsing:',
                                                 suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])),
                                                 length=50)
                            continue
                        data['name'] = data['name'] + ' ' + small_name.span.text
                        small_sizes_list = soup.find_all('ul', {'class': 'size_list'})
                        small_sizes_list = small_sizes_list[0].find_all('li', {'class': 'check_item'})
                        small_sizes_list = [size.text.strip() for size in small_sizes_list]
                        small_sizes_list.pop(0)
                        small_sizes_list.pop(-1)
                        for size in small_sizes_list:
                            if size not in data['sizes_list'] and int(size) > 46:
                                data['sizes_list'].append(size)
                    data['sizes_list'].sort()
                    # print(['Визель ' + data['name'], data['sizes_list'], data['price'], data['type']])
                    result.append(
                        ['Визель ' + data['name'], data['sizes_list'], data['price'], data['type'], data['is_new']])
                elif len(data['small_sizes']) == 1:
                    sizes_list = list()
                    for size in data['sizes_list']:
                        if int(size) > 46:
                            sizes_list.append(size)
                    if len(sizes_list) != 0:
                        sizes_list.sort()
                        # print(['Визель ' + data['name'], sizes_list, data['price'], data['type']])
                        result.append(['Визель ' + data['name'], sizes_list, data['price'], data['type'], data['is_new']])
            except AttributeError:
                with open('errors.txt', 'a', encoding='utf-8') as err_file:
                    err_file.write('Ошибка в карточке: %s \n' % (item_link))
                continue
            except IndexError:
                continue
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Wisell Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
    return result


def bigmoda_parse(url):
    '''
    Parsing Bigmoda Site
    :param url: str
    :return: list
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    data = dict()
    result = list()
    data['paginaton_url'] = soup.find_all('a', {'class': 'page-numbers'})
    data['paginaton_url'] = [link.get('href') for link in data['paginaton_url'] if link.text != '→']
    if len(data['paginaton_url']) != 0:
        last_page = int(re.search(r'(?<=page/)(\d+)', data['paginaton_url'].pop(-1)).group(0))
        pagination_link = url + 'page/'
        data['paginaton_url'] = [pagination_link + str(link) for link in range(2, last_page + 1)]
    data['paginaton_url'].insert(0, url)
    j = 1
    # with Pool(10):
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'woocommerce-LoopProduct-link'})
        data['item_links'] = [item.get('href') for item in data['item_links']]
        i = 0
        l = len(data['item_links'])
        printProgressBar(i, l, prefix='Bigmoda Parsing:',
                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for item in data['item_links']:
            r = requests.get(item)
            soup = BeautifulSoup(r.text, 'lxml')
            try:
                data['name'] = soup.find('span', {'class': 'sku'}).text
                data['price'] = soup.find('p', {'class': 'price'}).span.text.split('.')[0].replace(',', '')
                data['sizes_list'] = soup.find('div', {'class': 'ivpa_attribute'}, {'class': 'ivpa_text'})
                data['sizes_list'] = data['sizes_list'].find_all('span', {'class': 'ivpa_term'})
                data['sizes_list'] = [item.text.strip() for item in data['sizes_list']]
                data['product_id'] = re.search(r'(\d+)', soup.find('div', attrs={'class': 'product'})['id']).group(0)
                sizes_id = re.findall(r'(?<="variation_id":)(\d+)',
                                      soup.find('div', attrs={'id': 'ivpa-content'})['data-variations'])

                sizes_key = re.findall(r'(?<="attribute_pa_size":)"(\d+)"',
                                       soup.find('div', attrs={'id': 'ivpa-content'})['data-variations'])
                data['product_size_id'] = dict(zip(sizes_key, sizes_id))

                # print([data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
                result.append(
                    [data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
            except AttributeError:
                with open('errors.txt', 'a', encoding='utf-8') as err_file:
                    err_file.write('Ошибка в карточке: %s \n' % (item))
                i += 1
                printProgressBar(i, l, prefix='Bigmoda Parsing:',
                                 suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                continue
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Bigmoda Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
    return result


def krasa_parse(file_name):
    '''
    Parsing goods from krasa.csv
    :param file_name: str
    :return: list
    '''
    result = list()
    with open(file_name) as csvfile:
        reader = csv.reader(csvfile, dialect='excel', delimiter=';')
        for row in reader:
            if 'последние экземпляры' in row[0]:
                break
            if ('Наименование' or '') not in row[0]:
                try:
                    name = 'Краса ' + re.search(r'(П-\d+|ПБ-\d+|Р-\d+|РБ-\d+)', row[0]).group(0)
                    price = re.search(r'(\d+)', row[1].strip().replace(' ', '')).group(0)
                    price = 2400 if int(price) < 1200 else int(price) * 2
                    sizes = row[2].split('-')
                    sizes_list = [str(size) for size in range(int(sizes[0]), int(sizes[1]) + 1) if size % 2 == 0]
                    item_type = name.split(' ')[1].split('-')[0]
                    if item_type == 'П' or item_type == 'ПБ':
                        item_type = 'Платье'
                    elif item_type == 'Р' or item_type == 'РБ':
                        item_type = 'Блузка'
                    # print([name, sizes_list, price, item_type])
                    result.append([name, sizes_list, price, item_type, True])
                except AttributeError:
                    continue
    return result


def compare_dress(parse_list, bigmoda_dresses, bigmoda_exc, wcapi_conn):
    '''
    Compare avaliability sizes supplier and site customer
    :param parse_list: list
    :param bigmoda_dresses: list
    :param bigmoda_exc: list
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


def del_item(goods_data, wcapi_conn):
    '''
    Check availability goods on Bigmoda and supplier  
    :param goods_data: list
    :return: list
    '''
    names = [i[0] for i in goods_data]
    bm_names_dress = [i[0] for i in bigmoda_pages[0]]
    bm_names_blouse = [i[0] for i in bigmoda_pages[1]]
    bm_names_exc = [i[0] for i in bigmoda_pages[2]]

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
        if (name[0] not in bm_names_dress and name[0] not in bm_names_blouse) and name[0] not in bm_names_exc and name[
            4] is True:
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
                        'slug': '%s' % ('platya-bolshih-razmerov' if name[3] == 'Платье' or
                                                                     name[
                                                                         3] == 'Костюм' else 'bluzki-bolshih-razmerov'),
                        'name': '%s' % ('Платья больших размеров' if name[3] == 'Платье' or
                                                                     name[
                                                                         3] == 'Костюм' else 'Блузки больших размеров'),
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
            product = wcapi.post('products', data).json()
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
                    wcapi.post('products/%s/variations' % (product['id']), data)
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Добавить карточку: {} {} {}\n'.format(name[0], name[1], name[2]))
    return goods_data


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    try:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
        # print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
        sys.stdout.flush()
    except ZeroDivisionError:
        pass

    # Print New Line on Complete
    if iteration == total:
        os.system('cls')


if __name__ == '__main__':
    files = ['добавить удалить размеры.txt', 'добавить удалить карточки.txt', 'errors.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)

    with open('keys.txt', 'r') as file:
        keys = [line.strip() for line in file]

    consumer_key = keys[0]
    consumer_secret = keys[1]

    wcapi = API(
        url='http://localhost',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        wp_api=True,
        version="wc/v2",
    )

    dress_pages = [novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/'),
                   novita_parse('http://novita-nsk.ru/shop/aktsii/'),
                   novita_parse('http://novita-nsk.ru/index.php?route=product/category&path=1_19'),
                   novita_parse('http://novita-nsk.ru/shop/yubki/'),
                   primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'),
                   avigal_parse('http://avigal.ru/dress/'),
                   wisell_parse('https://wisell.ru/catalog/platya/'),
                   krasa_parse('krasa.csv')
                   ]
    blouse_pages = [novita_parse('http://novita-nsk.ru/shop/bluzy/'),
                    primalinea_parse('http://primalinea.ru/catalog/category/43/all/0'),
                    avigal_parse('http://avigal.ru/blouse-tunic/'),
                    wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')]
    # bigmoda_pages = [bigmoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/'),
    #                  bigmoda_parse('https://big-moda.com/product-category/bluzki-bolshih-razmerov/'),
    #                  bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')]
    bigmoda_pages = [bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'),
                     bigmoda_parse('http://localhost/product-category/bluzki-bolshih-razmerov/'),
                     bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/')]

    goods_data = list()
    for site in dress_pages:
        compare_dress(site, bigmoda_pages[0], bigmoda_pages[1], wcapi)
        for dress in site:
            goods_data.append(dress)
        for site in blouse_pages:
            compare_dress(site, bigmoda_pages[1], bigmoda_pages[2], wcapi)
    del_item(goods_data, wcapi)
