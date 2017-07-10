# -*- coding: utf-8 -*-
import requests
import os
import re
import time
import sys
import csv
import json

from multiprocessing import Pool

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
    temp_dict = {}
    for color in color_list:
        temp_list = []
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
    result = []
    i = 0
    l = len(items_link_list)
    printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
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
                # print(
                # ['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'], data['type']])
                result.append(
                    ['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'], data['type']])
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
    result = []
    i = 0
    l = len(items_link_list)
    printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)
    for link in items_link_list:
        r = session.get(link)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = soup.h1.text.strip()
        data['type'] = data['name'].split(' ')[1].capitalize() if len(data['name'].split(' ')) > 2 and \
                                                                  'new' not in data['name'].split(' ') \
            else data['name'].split(' ')[0].capitalize()
        if data['type'] == 'Блуза' or data['type'] == 'Кардиган' or data['type'] == 'Туника' or data['type'] == 'Платье':
            data['name'] = data['name'].split(' ')[2] if len(data['name'].split(' ')) > 2 and 'new' not in data[
                'name'].split(' ') else data['name'].split(' ')[1]
            price = soup.find('div', attrs={'id': 'catalog-item-description'})
            price = re.search(r'(\d+)', price.p.text.strip().replace(' ', ''))
            data['price'] = int(price.group(0)) * 2
            data['sizes_list'] = soup.find_all('option')
            data['sizes_list'] = [item.text for item in data['sizes_list']]
            # print('Прима ' + data['name'].lower(), data['sizes_list'], data['price'], data['type'])
            result.append(['Прима ' + data['name'], data['sizes_list'], data['price'], data['type']])
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
    data = {}
    result = []
    data['paginaton'] = soup.find_all('div', {'class': 'pagination'})
    data['paginaton'] = data['paginaton'][0].find_all('li')
    data['paginaton_url'] = [url]
    data['item_links'] = []
    items_link_list = []
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
        items_link_list = soup.find_all('div', {'class': 'product-about'})
        items_link_list = [item.find('div', attrs={'class': 'name'}).a.get('href') for item in items_link_list]
        i = 0
        l = len(items_link_list)
        printProgressBar(i, l, prefix='Wisell Parsing:',
                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for link in items_link_list:
            r = session.get(link)
            soup = BeautifulSoup(r.text, 'lxml')
            data['price'] = soup.find('span', attrs={'class': 'micro-price', 'itemprop': 'price'})
            data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
            data['price'] = int(data['price'].group(0)) * 2
            # if data['price'] > 2500:
            data['type'] = soup.find('h1').text.strip()
            data['name'] = soup.find('span', attrs={'itemprop': 'model'})
            data['name'] = data['name'].text
            sizes_list = soup.find_all('label', {'class': 'optid-13'})
            data['sizes_list'] = []
            for item in sizes_list:
                if r':n\a' not in item['title']:
                    data['sizes_list'].append(item.text.strip())
            print('Авигаль ' + data['name'], data['sizes_list'], data['price'], data['type'])
            result.append(['Авигаль ' + data['name'], data['sizes_list'], data['price'], data['type']])
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
    data = {}
    result = []
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
        data['item_links'] = soup.find_all('a', {'class': 'item_title'})
        data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
        i = 0
        l = len(data['item_links'])
        printProgressBar(i, l, prefix='Progress:',
                         suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for item_link in data['item_links']:
            r = requests.get(item_link, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
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
                            file.write('Нет в наличии на сайте Wisell: {}\n'.format(small_name.span.text))
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
                result.append(['Визель ' + data['name'], data['sizes_list'], data['price'], data['type']])
            elif len(data['small_sizes']) == 1:
                sizes_list = []
                for size in data['sizes_list']:
                    if int(size) > 46:
                        sizes_list.append(size)
                if len(sizes_list) != 0:
                    sizes_list.sort()
                    # print(['Визель ' + data['name'], sizes_list, data['price'], data['type']])
                    result.append(['Визель ' + data['name'], sizes_list, data['price'], data['type']])
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
    data = {}
    result = []
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
            except:
                print(item)
            # print([data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
            result.append(
                [data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Bigmoda Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
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
                    size_to_add = []
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
                            attributes = wcapi_conn.get('products/' + product_id).json()
                            # for attribute in attributes['attributes']:
                            #     if attribute['name'] == 'Размер':
                            #         if size not in attribute['options']:
                            #             attribute['options'].append(size)
                            #             wcapi_conn.put('products/' + product_id, attributes)
                            #             wcapi_conn.post('products/' + product_id + '/variations', data)
                            #         else:
                            #             wcapi_conn.post('products/' + product_id + '/variations', data)
                    if len(size_to_add) != 0:
                        with open('добавить удалить размеры.txt', 'a', encoding='utf-8') as file:
                            file.write('Добавить размеры: {}, {}, {}\n'.format(dress[0], size_to_add, dress[2]))
                    size_to_del = []
                    for size in bm_drs[1]:
                        if size not in dress[1]:
                            size_to_del.append(size)
                            # wcapi_conn.delete('products/' + product_id + '/variations/' + product_size_id[size])
                    if len(size_to_del) != 0:
                        with open('добавить удалить размеры.txt', 'a', encoding='utf-8') as file:
                            file.write('Удалить размеры: {}, {}, {}\n'.format(dress[0], size_to_del, dress[2]))
    return True


def krasa_parse(file_name):
    '''
    Parsing goods from krasa.csv
    :param file_name: str
    :return: list
    '''
    result = []
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
                    result.append([name, sizes_list, price, item_type])
                except AttributeError:
                    continue
    return result


def del_item(goods_data):
    '''
    Check availability goods on Bigmoda and supplier  
    :param goods_data: list
    :return: list
    '''
    names = [i[0] for i in goods_data]
    bm_names_dress = [i[0] for i in bigmoda_pages[0]]
    bm_names_blouse = [i[0] for i in bigmoda_pages[1]]
    bm_names_exc = [i[0] for i in bigmoda_pages[2]]
    for bm_dress in bm_names_dress:
        if bm_dress not in names and bm_dress not in bm_names_exc:
            data = {

            }
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_dress))
    for bm_blouse in bm_names_blouse:
        if bm_blouse not in names:
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_blouse))
    for name in goods_data:
        if (name not in bm_names_dress or name not in bm_names_blouse) and name not in bm_names_exc:
            data = {
                'name': '%s %s' % (name[3], name[0]),
                'type': 'variable',
                'status': 'private',
                'catalog_visibility': 'visible',
                'sku': '%s' % (name[0]),
                'regular_price': '%s' % (name[2]),
                'categories': [
                    {
                        'slug': '%s' % ('platya-bolshih-razmerov' if name[3] == 'Платье' or
                                                                     name[3] == 'Костюм' else 'bluzki-bolshih-razmerov'),
                        'name': '%s' % ('Платья больших размеров' if name[3] == 'Платье' or
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

                ]
            }
            product = wcapi.post('products', data).json()
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
    files = ['добавить удалить размеры.txt', 'добавить удалить карточки.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)

    wcapi = API(
        url='http://localhost',
        consumer_key='ck_beddec66bcfa5c091cf41b070048c118611ecc72',
        consumer_secret='cs_0241fad5f6c2d5e96e5bc321f146b1b3a85cbe5a',
        wp_api=True,
        version="wc/v2",
    )

    dress_pages = [  # novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/'),
        # novita_parse('http://novita-nsk.ru/shop/aktsii/'),
        # novita_parse('http://novita-nsk.ru/index.php?route=product/category&path=1_19'),
        # novita_parse('http://novita-nsk.ru/shop/yubki/'),
        primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'),
        # avigal_parse('http://avigal.ru/dress/'),
        #  wisell_parse('https://wisell.ru/catalog/platya/'),
        # krasa_parse('krasa.csv')
    ]
    # blouse_pages = [#novita_parse('http://novita-nsk.ru/shop/bluzy/'),
    #                 primalinea_parse('http://primalinea.ru/catalog/category/43/all/0'),
    #                 avigal_parse('http://avigal.ru/blouse-tunic/'),
    #                 wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')]
    # bigmoda_pages = [bigmoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/'),
    #                  bigmoda_parse('https://big-moda.com/product-category/bluzki-bolshih-razmerov/'),
    #                  bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')]
    # bigmoda_pages = [bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'),
    #                  bigmoda_parse('http://localhost/product-category/bluzki-bolshih-razmerov/'),
    #                  bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/')]
    # print(bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'))
    # print(bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/'))
    bigmoda_pages = [[['Краса 0083', ['52', '54', '56', '58', '60', '62', '64', '66'], '2500', '15542', {'60': '15551', '54': '15554', '58': '15552', '52': '15555', '66': '15548', '56': '15553', '64': '15549', '62': '15550'}], ['Краса П-0072', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13890', {'60': '13894', '54': '13897', '58': '13895', '52': '13898', '66': '13891', '56': '13896', '62': '13893', '64': '13892'}], ['Авигаль П-501-2', ['52', '54', '56', '58', '60', '62'], '2600', '15145', {'60': '15152', '54': '15147', '58': '15153', '52': '15148', '62': '15151', '56': '15146'}], ['Авигаль П-458-1', ['54', '56', '58', '60', '62', '64', '66'], '2400', '15738', {'60': '15739', '54': '15742', '58': '15741', '66': '15744', '62': '15740', '64': '15745', '56': '15743'}], ['Авигаль П-458', ['54', '56', '58', '60', '62', '64', '66'], '2400', '15727', {'60': '15731', '54': '15734', '58': '15732', '66': '15728', '62': '15730', '64': '15729', '56': '15733'}], ['Авигаль П-501', ['56', '58', '60', '62'], '2600', '15123', {'60': '15125', '62': '15124', '58': '15126', '56': '15127'}], ['Прима 4050', ['46', '48', '50', '52', '54', '56', '58', '60'], '1900', '14905', {'48': '14912', '52': '14910', '58': '14907', '60': '14906', '46': '14913', '50': '14911', '54': '14909', '56': '14908'}], ['Авигаль П-164-1', ['54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600', '15529', {'60': '15535', '54': '15538', '58': '15536', '66': '15532', '68': '15531', '56': '15537', '70': '15530', '62': '15534', '64': '15533'}], ['Авигаль П-164', ['54', '66', '68', '70'], '2600', '15516', {'68': '15518', '54': '15525', '70': '15517', '66': '15519'}], ['Авигаль П-011-1', ['54', '56', '58', '60', '62', '64', '66'], '3300', '15112', {'60': '15115', '54': '15118', '58': '15116', '66': '15119', '62': '15114', '64': '15113', '56': '15117'}], ['Визель П3-3584/3', ['48', '50', '52', '54', '56', '58', '60'], '3000', '15044', {'60': '15045', '54': '15048', '58': '15046', '48': '15051', '52': '15049', '50': '15050', '56': '15047'}], ['Визель П3-3576/5', ['48', '50', '52', '54', '56', '58', '60', '62'], '3000', '15015', {'48': '15023', '54': '15020', '58': '15018', '60': '15750', '52': '15021', '50': '15022', '62': '15016', '56': '15019'}], ['Новита 462 розовые цветы', ['48', '50', '52', '54', '56'], '3000', '14720', {'52': '14724', '50': '14725', '54': '14723', '48': '14726', '56': '14722'}], ['Краса П-0088', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14406', {'60': '14410', '54': '14413', '58': '14411', '52': '14414', '66': '14407', '56': '14412', '64': '14408', '62': '14409'}], ['Краса-0093', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600', '15556', {'60': '15560', '54': '15563', '58': '15561', '52': '15564', '66': '15557', '56': '15562', '64': '15558', '62': '15559'}], ['Авигаль П-229-3', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '14756', {'58': '14758', '72': '14765', '68': '14766', '74': '14767', '64': '14762', '60': '14761', '54': '14763', '52': '14760', '66': '14759', '70': '14768', '62': '14764', '56': '14757'}], ['Новита 408/1', ['50', '52', '54', '56', '58'], '2600', '12575', {'52': '12579', '50': '12580', '54': '12578', '58': '12576', '56': '12577'}], ['Новита 456/1', ['50', '52', '54', '56', '58'], '3100', '12098', {'52': '12102', '50': '12103', '54': '12101', '58': '12099', '56': '12100'}], ['Прима линия 4117', ['44', '46', '50', '52', '54', '56', '58', '60'], '3200', '15429', {'60': '15430', '54': '15433', '44': '15438', '58': '15431', '52': '15434', '50': '15435', '46': '15437', '56': '15432'}], ['Авигаль П-501-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600', '15130', {'60': '15138', '54': '15141', '58': '15139', '52': '15142', '66': '15135', '56': '15140', '64': '15136', '62': '15137'}], ['Новита 592 ромашки', ['48', '50', '52', '54', '56'], '2800', '14677', {'52': '14680', '50': '14681', '54': '14679', '48': '14682', '56': '14678'}], ['Новита 618', ['48', '50', '52', '54', '56'], '2800', '14643', {'52': '14646', '50': '14647', '54': '14645', '48': '14648', '56': '14644'}], ['Новита 610', ['48', '50', '52', '54', '56'], '2800', '14112', {'52': '14115', '50': '14116', '54': '14114', '48': '14117', '56': '14113'}], ['Новита 593', ['50', '52', '54', '56', '58', '60'], '3100', '12604', {'60': '12605', '54': '12608', '58': '12606', '52': '12609', '50': '12610', '56': '12607'}], ['Новита 444/1', ['48', '50', '52', '54', '56'], '3100', '12708', {'52': '12711', '48': '12713', '54': '12710', '50': '12712', '56': '12709'}], ['Новита 599', ['50', '52', '54', '56', '58'], '3300', '12662', {'52': '12666', '50': '12667', '54': '12665', '58': '12663', '56': '12664'}], ['Визель-П4-2571/3', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8758', {'48': '8765', '54': '8762', '58': '12029', '60': '12030', '52': '8763', '50': '8764', '56': '8761'}], ['Авигаль П-044-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2600', '15491', {'60': '15508', '54': '15511', '52': '15512', '58': '15509', '72': '15502', '68': '15504', '66': '15505', '70': '15503', '62': '15507', '64': '15506', '56': '15510'}], ['Новита 592', ['48', '50', '52', '54', '56'], '2800', '12064', {'52': '12067', '50': '12068', '54': '12066', '48': '12069', '56': '12065'}], ['Прима 2754-2', ['52', '54', '56', '58'], '4400', '10587', {'52': '10593', '54': '10592', '58': '10590', '56': '10591'}], ['Визель П4-3556/3', ['48', '50', '52', '54', '56', '58'], '3600', '9261', {'48': '12306', '54': '12303', '58': '12301', '52': '12304', '50': '12305', '56': '12302'}], ['Авигаль П-044', ['54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2600', '15476', {'60': '15483', '54': '15486', '58': '15484', '72': '15477', '68': '15479', '66': '15480', '70': '15478', '62': '15482', '64': '15481', '56': '15485'}], ['Прима линия 4104', ['66', '72', '74'], '4400', '15290', {'66': '15749', '74': '15291', '72': '15292'}], ['Новита 594 фуксия', ['48', '50', '52', '54', '56'], '3200', '14050', {'52': '14053', '50': '14054', '54': '14052', '48': '14055', '56': '14051'}], ['Краса П-0053', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13437', {'60': '13441', '54': '13444', '58': '13442', '52': '13445', '66': '13438', '56': '13443', '64': '13439', '62': '13440'}], ['Визель П2-3610/1', ['48', '50', '52', '54', '56'], '3400', '13138', {'52': '13143', '48': '13145', '54': '13142', '56': '13141', '50': '13144'}], ['Визель П2-3610/3', ['48', '50', '52', '54', '56', '58', '60'], '3400', '13123', {'60': '13124', '54': '13127', '58': '13125', '48': '13130', '52': '13128', '50': '13129', '56': '13126'}], ['Визель П3-3607/1', ['48', '50', '52', '54', '56', '58', '60'], '4000', '13068', {'48': '13076', '54': '13073', '58': '13071', '60': '15662', '52': '13074', '50': '13075', '56': '13072'}], ['Авигаль П-704-3', ['52', '54', '56', '58', '60', '62', '64', '66'], '2900', '12784', {'60': '12789', '54': '12792', '58': '12790', '52': '12793', '66': '12786', '62': '12788', '64': '12787', '56': '12791'}], ['Новита 608', ['46', '48', '50', '52', '54', '56'], '3000', '12647', {'48': '12652', '52': '12650', '46': '12653', '50': '12651', '54': '12649', '56': '12648'}], ['Новита 598/1', ['48', '50', '52'], '3400', '12636', {'52': '12638', '48': '12641', '50': '12640'}], ['Визель П3-3292/2', ['52', '54', '56', '58', '60'], '4000', '12494', {'52': '12499', '60': '12495', '54': '12498', '58': '12496', '56': '12497'}], ['Визель\xa0П3-3598/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '12479', {'60': '12480', '54': '12483', '58': '12481', '48': '12486', '52': '12484', '50': '12485', '56': '12482'}], ['Авигаль-П-464', ['52', '54', '56'], '3750', '12344', {'52': '12349', '54': '12348', '56': '12347'}], ['Авигаль-П-464-1', ['52', '54', '56', '58', '60'], '3750', '12334', {'52': '12339', '60': '12335', '54': '12338', '58': '12336', '56': '12337'}], ['Авигаль-П-084-1', ['50', '54'], '2700', '12285', {'50': '12290', '54': '12288'}], ['Новита 591', ['50', '52', '54', '56', '58'], '2600', '12055', {'52': '12059', '50': '12060', '54': '12058', '58': '12056', '56': '12057'}], ['Новита 583 вишневый', ['48', '50', '52', '54', '56'], '3200', '11997', {'52': '12000', '50': '12001', '54': '11999', '48': '12002', '56': '11998'}], ['Новита 581 синие цветы', ['50', '52'], '3300', '11989', {'52': '11992', '50': '11993'}], ['Визель П3-3232', ['52', '54', '56', '60'], '3400', '11883', {'52': '11887', '60': '11884', '54': '11886', '56': '11885'}], ['Визель П5-3347/2', ['46', '48', '52', '54', '56', '58'], '4400', '11862', {'48': '11869', '52': '11867', '58': '12507', '46': '12026', '54': '11866', '56': '11865'}], ['Новита 576 коралловый', ['48', '50', '52', '54', '56', '58'], '3000', '10983', {'48': '10989', '54': '10986', '58': '10984', '52': '10987', '50': '10988', '56': '10985'}], ['Авигаль-П-982', ['56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '10807', {'72': '15691', '60': '15697', '58': '15698', '66': '15694', '68': '15693', '74': '15690', '70': '15692', '62': '15696', '64': '15695', '56': '15699'}], ['Новита 568', ['48', '50', '54', '56'], '3200', '10256', {'48': '10260', '54': '10258', '56': '13005', '50': '10259'}], ['Новита 567', ['48', '50', '52', '54', '56'], '3300', '10246', {'52': '10249', '50': '10250', '54': '10248', '48': '10251', '56': '10247'}], ['Н/Д', ['52', '54', '56', '58'], '3800', '11829', {'52': '11834', '54': '11833', '58': '11831', '56': '11832'}], ['Визель-П3-3585/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11375', {'60': '11377', '54': '11380', '58': '11378', '48': '11383', '52': '11381', '50': '11382', '56': '11379'}], ['Новита 575 васильковый', ['48', '50', '52', '54'], '3000', '10973', {'52': '10977', '50': '10978', '54': '10976', '48': '10979'}], ['Новита 562', ['50', '52', '54', '56'], '3300', '9186', {'52': '9189', '50': '9190', '54': '9188', '56': '9187'}], ['Новита-538', ['50', '52', '54', '56'], '3000', '6185', {'52': '6189', '50': '11180', '54': '6188', '56': '6187'}], ['Авигаль-П-307', ['54', '58', '60', '62', '64'], '3600', '12324', {'60': '12327', '54': '12330', '64': '12325', '58': '12328', '62': '12326'}], ['Визель-П3-3232/1', ['52', '54', '56', '58', '60'], '3400', '12307', {'52': '12312', '60': '12308', '54': '12311', '58': '12309', '56': '12310'}], ['Новита-407с', ['50', '52', '54', '56'], '3100', '4217', {'52': '13033', '50': '13032', '54': '13034', '56': '13213'}], ['Визель П3-3603/1', ['48', '50', '52'], '3800', '13083', {'52': '13088', '48': '13090', '50': '13089'}], ['Авигаль П-449', ['56', '62', '64', '66'], '2600', '12753', {'66': '12756', '62': '12758', '64': '12757', '56': '12759'}], ['Авигаль-П-084', ['50', '52'], '2700', '12270', {'52': '12281', '50': '12282'}], ['Визель П3-3331/2', ['46', '48', '50', '52'], '4200', '11892', {'52': '11896', '48': '11898', '46': '11899', '50': '11897'}], ['Визель П4-3538/5', ['50', '52', '56'], '4600', '8485', {'52': '8488', '50': '9434', '56': '14139'}], ['Новита 548 электрик', ['48', '50', '52', '54', '56'], '3200', '7560', {'52': '7563', '50': '7564', '54': '7562', '48': '7565', '56': '7561'}], ['Новита-493/1', ['52', '54', '56', '58'], '3500', '5514', {'52': '5520', '54': '5519', '58': '5517', '56': '5518'}], ['Новита-530', ['52', '56'], '3300', '5493', {'52': '11369', '56': '5494'}], ['Визель-П4-2571/15', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12146', {'48': '12153', '54': '13268', '58': '13266', '60': '13265', '52': '13269', '50': '12152', '56': '13267'}], ['Новита 486', ['50', '52', '54', '56', '58'], '3000', '7435', {'52': '7439', '50': '7440', '54': '7438', '58': '7436', '56': '7437'}], ['Прима 2956', ['48', '50', '52', '54', '56', '58', '60', '62'], '3580', '6787', {'48': '6795', '54': '8175', '58': '6791', '60': '8177', '52': '8173', '50': '6794', '62': '8176', '56': '8174'}], ['Новита-522', ['50', '54', '56', '60'], '3000', '5302', {'60': '5305', '54': '5308', '50': '5310', '56': '5307'}], ['Авигаль П-229-2', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '14000', {'58': '14002', '72': '14009', '68': '14010', '74': '14011', '64': '14006', '60': '14005', '54': '14007', '52': '14004', '66': '14003', '70': '14012', '62': '14008', '56': '14001'}], ['Новита 565', ['50', '52', '54', '56'], '3400', '9204', {'52': '9207', '50': '9208', '54': '9206', '56': '9205'}], ['Новита 554 белая клетка', ['48', '50', '52', '54', '56', '58'], '3200', '8595', {'48': '8601', '54': '10287', '58': '8596', '52': '8599', '50': '8600', '56': '8597'}], ['Новита 429', ['50', '52', '54', '56'], '3100', '8569', {'52': '8572', '50': '14780', '54': '8571', '56': '8570'}], ['Новита 343', ['48', '50', '52', '54', '56'], '3200', '7620', {'52': '7623', '50': '7624', '54': '7622', '48': '7625', '56': '7621'}], ['Прима 2915', ['50', '52', '54', '56'], '3600', '7067', {'52': '7071', '50': '7072', '54': '15678', '56': '7069'}], ['Визель П5-3506/1', ['52', '54', '56', '58', '60'], '4000', '6099', {'52': '6105', '60': '6101', '54': '6104', '58': '6102', '56': '6103'}], ['Визель-П3-2337/6', ['50', '52', '54', '56', '58', '60'], '4200', '5989', {'60': '5996', '54': '5992', '58': '5990', '52': '5993', '50': '5994', '56': '5991'}], ['Авигаль П-445', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2900', '13587', {'60': '13593', '54': '13596', '58': '13594', '68': '13589', '52': '13597', '66': '13590', '70': '13588', '62': '13592', '64': '13591', '56': '13595'}], ['Краса П-0039', ['52', '54', '56', '58', '60', '62', '64'], '2400', '13520', {'60': '13524', '54': '13527', '58': '13525', '62': '13523', '64': '13522', '52': '13528', '56': '13526'}], ['Авигаль П-450', ['56', '60'], '2500', '12203', {'60': '12209', '56': '12208'}], ['Визель-П3-3465/3', ['48', '50', '52', '54', '56', '60'], '4400', '8721', {'60': '8722', '54': '8725', '48': '8728', '52': '8726', '50': '8727', '56': '8724'}], ['Прима 2960', ['50', '52', '54', '56', '58', '60', '62', '64'], '3840', '6480', {'60': '6483', '54': '6486', '58': '15100', '52': '6487', '50': '6488', '62': '6482', '64': '15098', '56': '15099'}], ['Новита-534', ['50', '52', '54', '56', '58', '60'], '3400', '6167', {'60': '6168', '54': '6171', '58': '6169', '52': '6172', '50': '6173', '56': '6170'}], ['Визель П4-3371/16', ['48', '50', '52', '54', '56', '58'], '3600', '6073', {'48': '6080', '54': '6077', '58': '6075', '52': '12547', '50': '6079', '56': '6076'}], ['Визель-П3-3468/4', ['54'], '3800', '4555', {'54': '12729'}], ['Новита 617', ['46', '48', '50', '52', '54', '56'], '2700', '14665', {'48': '14670', '54': '14667', '46': '14671', '52': '14668', '50': '14669', '56': '14666'}], ['Краса П-0063', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13423', {'60': '13432', '54': '13435', '58': '13433', '52': '13436', '66': '13429', '56': '13434', '64': '13430', '62': '13431'}], ['Краса П-0076', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13315', {'60': '13319', '54': '13322', '58': '13320', '62': '13318', '66': '15801', '64': '13317', '56': '13321'}], ['Краса П-0074', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13236', {'60': '13237', '54': '13239', '58': '13240', '52': '13238', '66': '13243', '62': '13244', '64': '13242', '56': '13241'}], ['Визель П4-3605/1', ['52', '58', '60'], '3600', '13197', {'52': '13202', '60': '15661', '58': '13199'}], ['Новита 597', ['48', '50', '52', '54', '56'], '2700', '12615', {'52': '12618', '50': '12619', '54': '12617', '48': '12620', '56': '12616'}], ['Новита 418', ['48', '50', '52', '54', '56'], '3100', '12586', {'52': '12589', '50': '12590', '54': '12588', '48': '12591', '56': '12587'}], ['Визель-П3-3293', ['54', '56'], '4000', '9622', {'54': '9626', '56': '9625'}], ['Визель П4-3539/1', ['56'], '5000', '8431', {'56': '12727'}], ['Визель П4-3539/3', ['48', '50', '58'], '5000', '8413', {'48': '12553', '58': '11252', '50': '12552'}], ['Новита 558', ['48', '50', '52'], '3100', '7918', {'52': '7921', '50': '7922', '48': '7923'}], ['Прима-2944', ['48', '50', '52', '54', '56', '58', '62', '64'], '4400', '6653', {'48': '6666', '54': '6663', '58': '6661', '52': '6664', '50': '6665', '62': '6659', '64': '6658', '56': '6662'}], ['Прима 2939', ['48', '50', '52', '54', '56', '58', '60', '62'], '3520', '6593', {'60': '6595', '54': '6598', '58': '6596', '48': '6601', '52': '6599', '50': '6600', '62': '6594', '56': '6597'}], ['Визель-П3-2337/4', ['48', '50', '52', '54', '56', '58', '60'], '4200', '5974', {'60': '5975', '54': '5978', '58': '5976', '48': '5981', '52': '5979', '50': '5980', '56': '5977'}], ['Новита-527', ['50', '52', '54', '56', '58'], '3200', '5483', {'52': '5487', '50': '5488', '54': '5486', '58': '5484', '56': '5485'}], ['Новита -520', ['48', '50', '52', '54', '56', '58'], '3100', '5311', {'48': '5317', '54': '5314', '58': '5312', '52': '5315', '50': '5316', '56': '5313'}], ['Визель-П3-3479/1', ['50', '52', '54', '56'], '4200', '4261', {'52': '4266', '50': '12730', '54': '14141', '56': '4264'}], ['Новита-509', ['50'], '3100', '3711', {'50': '3716'}], ['Новита-510', ['50', '52', '54', '56', '58'], '3300', '3669', {'52': '3673', '50': '3674', '54': '3672', '58': '3670', '56': '3671'}], ['Новита-506', ['48', '50', '52', '54', '56'], '3000', '3497', {'52': '3500', '50': '3501', '54': '3499', '48': '3502', '56': '3498'}], ['Авигаль П-104-1', ['54', '56', '58', '60', '62', '64', '66'], '2600', '15610', {'60': '15615', '54': '15618', '58': '15616', '66': '15612', '56': '15617', '64': '15613', '62': '15614'}], ['Авигаль П-611', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2500', '15571', {'72': '15572', '60': '15578', '54': '15581', '58': '15579', '66': '15575', '52': '15582', '68': '15574', '56': '15580', '70': '15573', '62': '15577', '64': '15576'}], ['Прима линия 4115', ['60', '62', '64', '66', '68', '70'], '3600', '15220', {'60': '15230', '68': '15226', '66': '15227', '70': '15225', '62': '15229', '64': '15228'}], ['Авигаль П-467-1', ['52', '54', '56', '58', '60', '62', '64'], '3200', '14857', {'60': '14858', '54': '14861', '58': '14859', '52': '14862', '62': '14863', '64': '14864', '56': '14860'}], ['Новита 605', ['48', '50', '52', '54', '56', '58'], '3200', '14697', {'48': '14703', '54': '14700', '58': '14698', '52': '14701', '50': '14702', '56': '14699'}], ['Новита 449/2', ['50', '52', '54', '56'], '2900', '14620', {'52': '14623', '50': '14624', '54': '14622', '56': '14621'}], ['Визель П3-3623/1', ['50', '52', '54', '56', '58', '60'], '3400', '14497', {'60': '14498', '54': '14501', '58': '14499', '52': '14502', '50': '14503', '56': '14500'}], ['Краса П-0089', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14391', {'60': '14395', '54': '14398', '58': '14396', '52': '14399', '66': '14392', '56': '14397', '64': '14393', '62': '14394'}], ['Краса ПБ-0012', ['54', '56', '58', '60', '62', '64'], '2400', '14196', {'60': '14200', '54': '14203', '58': '14201', '62': '14199', '64': '14198', '56': '14202'}], ['Авигаль П-229', ['54', '56', '60', '64', '66', '68', '70', '72', '74'], '2200', '13966', {'60': '13974', '54': '13977', '72': '13968', '68': '13970', '66': '13971', '74': '13967', '70': '13969', '64': '13972', '56': '13976'}], ['Авигаль П-305-3', ['50', '54', '64', '66', '68'], '2500', '13762', {'68': '13768', '50': '13771', '54': '13765', '64': '13766', '66': '13767'}], ['Краса П-0042', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13548', {'60': '13553', '54': '13556', '58': '13554', '52': '13557', '66': '13550', '56': '13555', '64': '13551', '62': '13552'}], ['Новита 596 кофейное', ['48', '50', '52'], '3400', '12683', {'52': '12685', '50': '12686', '48': '12687'}], ['Новита 596 белое', ['48', '50', '52', '56'], '3400', '12673', {'52': '13956', '50': '13957', '56': '13954', '48': '13958'}], ['Визель\xa0П3-3598/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '12465', {'60': '12466', '54': '12469', '58': '12467', '48': '12472', '52': '12470', '50': '12471', '56': '12468'}], ['Новита 594', ['48', '50', '52', '54', '56', '58'], '3200', '12073', {'48': '12079', '54': '12076', '58': '12074', '52': '12077', '50': '12078', '56': '12075'}], ['Авигаль-П-497', ['50', '52', '60'], '3360', '11960', {'52': '11965', '60': '11961', '50': '11966'}], ['Авигаль-П-326-1', ['52', '54', '56', '60', '62'], '2500', '11950', {'52': '11959', '60': '11955', '54': '11958', '62': '11954', '56': '11957'}], ['Визель П2-3311/1', ['48', '50', '52', '56'], '3800', '11915', {'52': '11920', '48': '11922', '56': '11918', '50': '14783'}], ['Визель П3-3494/1', ['48', '50', '52'], '3800', '11904', {'52': '11909', '50': '11910', '48': '11911'}], ['Авигаль-П-483-3', ['52', '54', '56', '62'], '2400', '11518', {'52': '11525', '54': '11524', '62': '11520', '56': '14939'}], ['Визель П3-3586/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11488', {'60': '11489', '54': '11492', '58': '11490', '48': '11495', '52': '11493', '50': '11494', '56': '11491'}], ['Авигаль-П-495-1', ['50', '52', '58'], '2500', '11329', {'52': '11334', '50': '11335', '58': '11331'}], ['Авигаль-П-702-1', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2400', '11267', {'60': '11280', '54': '11283', '68': '11276', '58': '11281', '50': '11285', '52': '11284', '66': '11277', '56': '11282', '70': '11275', '64': '11278', '62': '11279'}], ['Авигаль-П-400', ['50', '54', '60', '64'], '2400', '11228', {'60': '11231', '54': '11233', '64': '11229', '50': '11234'}], ['Авигаль-П-706', ['52', '54', '70', '72'], '2900', '11095', {'52': '11102', '54': '11101', '70': '11106', '72': '11105'}], ['Новита 577 бирюзовый', ['48', '50', '52', '54', '56', '58'], '3000', '10993', {'48': '10999', '54': '10996', '58': '10994', '52': '10997', '50': '10998', '56': '10995'}], ['Авигаль-П-488', ['52', '54', '56', '58', '66'], '2700', '10793', {'52': '10803', '66': '10796', '54': '10802', '58': '10798', '56': '10801'}], ['Визель-П3-3571/3', ['52', '54', '56', '58', '60'], '4400', '10665', {'52': '10670', '60': '10666', '54': '10669', '58': '10667', '56': '10668'}], ['Визель-П3-3567/1', ['48', '50', '52', '54', '56', '60'], '3600', '9744', {'60': '9745', '54': '9748', '48': '9751', '52': '9749', '50': '9750', '56': '9747'}], ['Визель П4-3561/1', ['52', '54', '56', '58', '60'], '3200', '9359', {'52': '9364', '60': '9360', '54': '9363', '58': '9361', '56': '9362'}], ['Новита 574 бежевый орнамент', ['46', '50', '52', '54', '56'], '2900', '9300', {'52': '9303', '50': '9304', '54': '9302', '46': '9306', '56': '9301'}], ['Новита 564', ['48', '50', '52', '54', '56'], '3300', '9195', {'52': '9198', '50': '9199', '54': '9197', '48': '9200', '56': '9196'}], ['Прима 2964', ['62', '64'], '3560', '9058', {'62': '9060', '64': '9059'}], ['Визель-П3-3080/1', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8746', {'60': '8747', '54': '8750', '58': '8748', '48': '8753', '52': '8751', '50': '8752', '56': '8749'}], ['Визель-П3-3540/1', ['50', '52', '58', '60'], '3400', '8680', {'52': '8685', '60': '8681', '58': '8682', '50': '8686'}], ['Новита 560', ['44', '46', '48', '50', '52', '54', '56'], '2800', '8518', {'48': '8523', '52': '8521', '44': '8525', '46': '8524', '50': '8522', '54': '10288', '56': '8519'}], ['Визель П4-3538/1', ['48', '50', '52', '54', '60'], '4600', '8462', {'52': '8467', '48': '12563', '54': '8466', '60': '13270', '50': '12562'}], ['Новита 326/1', ['48', '50', '52', '54', '56'], '3000', '7643', {'52': '7647', '50': '7648', '54': '7646', '48': '7649', '56': '7645'}], ['Новита 309', ['46', '48', '50', '52', '56'], '3200', '7610', {'52': '7613', '50': '7614', '48': '7615', '46': '7616', '56': '7611'}], ['Новита 518', ['50', '52', '56', '58'], '3200', '7427', {'52': '7431', '50': '7432', '58': '7428', '56': '14781'}], ['Новита 531 изумрудный', ['48', '50', '52', '54', '56', '58'], '3100', '7398', {'48': '7404', '54': '7401', '58': '9281', '52': '7402', '50': '7403', '56': '7400'}], ['Новита 542', ['48', '50', '54', '56', '58'], '3200', '6886', {'48': '6892', '50': '6891', '54': '6889', '58': '6887', '56': '6888'}], ['Прима 2875', ['52', '54', '58', '62', '64', '66', '68', '70'], '4400', '6775', {'54': '6782', '58': '6780', '68': '13948', '52': '6783', '66': '6776', '70': '13947', '62': '6778', '64': '6777'}], ['Прима 2876', ['48', '52', '56', '58', '60', '62'], '4200', '6749', {'48': '6759', '58': '6754', '60': '6753', '52': '12402', '62': '6752', '56': '6755'}], ['Прима 2961', ['52', '54', '56', '58', '60', '62', '64', '66'], '3840', '6627', {'60': '6631', '54': '6634', '58': '6632', '52': '6635', '66': '6628', '56': '6633', '64': '6629', '62': '6630'}], ['Прима 2925', ['48', '50', '52'], '3240', '6615', {'52': '6620', '50': '6621', '48': '6622'}], ['Новита-528', ['54', '56', '58'], '3300', '5503', {'54': '5506', '58': '5504', '56': '5505'}], ['Со-ЮНОНА ПРИНТ НА ЧЕРНОМ', ['60'], '3790', '5044', {'60': '9646'}], ['Визель-П4-3469/1', ['56'], '4000', '4426', {'56': '13274'}], ['Новита-242', ['56'], '4000', '4426', {'56': '13274'}], ['Новита-393В', ['56'], '3000', '4200', {'56': '4202'}], ['Олеся-24019-1', ['56'], '3400', '4113', {'56': '12138'}], ['Новита-441', ['48', '50', '52', '54', '56'], '3100', '3703', {'52': '3706', '50': '3707', '54': '3705', '48': '3708', '56': '3704'}], ['Новита-492', ['50'], '3100', '3070', {'50': '9647'}], ['Новита-503', ['48', '50', '52', '54', '56'], '3000', '3043', {'52': '3049', '50': '3050', '54': '3048', '48': '3051', '56': '3047'}], ['Олеся-27026-1', ['50', '52'], '3700', '2741', {'52': '2745', '50': '2746'}], ['Джетти-Б005-1', ['50', '52'], '3700', '2741', {'52': '2745', '50': '2746'}], ['ЕО-27014-1', ['50'], '3780', '1893', {'50': '1902'}], ['ЕО-27018-1', ['52'], '3385', '1873', {'52': '1877'}], ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '3200', '1795', {'52': '9640', '62': '9641'}], ['Авигаль П-905-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700', '15714', {'60': '15718', '54': '15715', '58': '15722', '68': '15723', '52': '15716', '66': '15721', '62': '15719', '64': '15720', '56': '15717'}], ['Авигаль П-905', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700', '15701', {'60': '15706', '54': '15709', '58': '15707', '68': '15702', '52': '15710', '66': '15703', '62': '15705', '64': '15704', '56': '15708'}], ['Авигаль П-104-4', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600', '15641', {'60': '15649', '54': '15644', '58': '15642', '68': '15647', '66': '15648', '62': '15645', '64': '15643', '56': '15646'}], ['Авигаль П-104-3', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600', '15632', {'60': '15637', '54': '15638', '58': '15640', '68': '15635', '66': '15636', '62': '15633', '64': '15639', '56': '15634'}], ['Авигаль П-104-2', ['54', '56', '60', '62', '66', '68'], '2600', '15621', {'60': '15623', '54': '15622', '68': '15628', '66': '15629', '62': '15626', '56': '15627'}], ['Авигаль П-611-1', ['54', '56', '58', '60', '62', '64', '66'], '2500', '15585', {'60': '15600', '54': '15603', '58': '15601', '66': '15597', '56': '15602', '64': '15598', '62': '15599'}], ['Новита-607', ['50', '52', '54', '56'], '2800', '15467', {'52': '15470', '50': '15471', '54': '15469', '56': '15468'}], ['Прима линия 4130', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '4200', '15411', {'58': '15415', '60': '15414', '68': '15423', '72': '15421', '64': '15412', '48': '15420', '54': '15417', '66': '15424', '52': '15418', '50': '15419', '70': '15422', '62': '15413', '56': '15416'}], ['Прима линия 4129', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '4200', '15393', {'58': '15401', '72': '15394', '68': '15396', '64': '15398', '48': '15406', '60': '15400', '54': '15403', '66': '15397', '52': '15404', '50': '15405', '70': '15395', '62': '15399', '56': '15402'}], ['Прима линия 4140', ['64', '66'], '4400', '15378', {'66': '15387', '64': '15388'}], ['Прима линия 4139', ['48', '50', '56', '58', '60', '62', '64', '66'], '4400', '15360', {'48': '15374', '60': '15370', '58': '15371', '50': '15373', '66': '15367', '56': '15372', '62': '15369', '64': '15368'}], ['Прима линия 4116', ['60', '62', '64', '66', '68', '70'], '4400', '15349', {'60': '15355', '66': '15352', '68': '15351', '70': '15350', '62': '15354', '64': '15353'}], ['Прима линия 4103', ['68', '70', '72', '74'], '4400', '15340', {'68': '15343', '74': '15680', '70': '15342', '72': '15341'}], ['Прима линия 4108', ['64', '66', '68', '70', '72'], '4400', '15331', {'68': '15334', '66': '15335', '70': '15333', '64': '15336', '72': '15332'}], ['Прима линия 4098', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2400', '15313', {'58': '15322', '72': '15315', '68': '15317', '74': '15314', '64': '15319', '48': '15327', '60': '15321', '54': '15324', '50': '15326', '52': '15325', '66': '15318', '70': '15316', '62': '15320', '56': '15323'}], ['Прима линия 4096', ['66', '68', '70', '72', '74'], '2400', '15304', {'68': '15308', '66': '15309', '74': '15305', '70': '15307', '72': '15306'}], ['Новита 606 красное', ['48', '50', '52', '54'], '3000', '15280', {'52': '15282', '50': '15283', '54': '15281', '48': '15284'}], ['Новита 606 фиолетовое', ['48', '50', '52', '54'], '3000', '15271', {'52': '15273', '50': '15274', '54': '15272', '48': '15275'}], ['Новита 622', ['48', '50', '52', '54', '56'], '2900', '15259', {'52': '15262', '50': '15263', '54': '15261', '48': '15264', '56': '15260'}], ['Новита 614', ['50', '52', '54', '56', '58'], '3100', '15248', {'52': '15252', '50': '15253', '54': '15251', '58': '15249', '56': '15250'}], ['Новита 620', ['48', '50', '52', '54', '56'], '3000', '15237', {'52': '15240', '50': '15241', '54': '15239', '48': '15242', '56': '15238'}], ['Прима линия 4112', ['52', '54', '56', '58'], '3600', '15212', {'52': '15216', '54': '15215', '58': '15213', '56': '15214'}], ['Прима линия 4084', ['54', '56', '58', '60', '62', '64', '66'], '3000', '15200', {'60': '15207', '54': '15204', '58': '15202', '66': '15201', '62': '15206', '64': '15205', '56': '15203'}], ['Прима линия 4085', ['54', '56', '58', '60', '62', '64', '66'], '3000', '15189', {'60': '15195', '54': '15192', '58': '15190', '66': '15196', '62': '15194', '64': '15193', '56': '15191'}], ['Прима линия 4086', ['48', '50', '52', '54', '56', '58'], '3000', '15179', {'48': '15185', '54': '15182', '58': '15180', '52': '15183', '50': '15184', '56': '15181'}], ['Прима линия 4021', ['54', '58', '60', '62'], '4400', '15169', {'60': '15170', '54': '15173', '62': '15175', '58': '15171'}], ['Прима 4020', ['52', '54', '56', '58', '60', '62'], '4400', '15158', {'60': '15160', '54': '15163', '58': '15161', '52': '15164', '62': '15159', '56': '15162'}], ['Авигаль П-011', ['54', '56', '58', '60', '62', '64', '66'], '3300', '15101', {'60': '15105', '54': '15108', '58': '15106', '66': '15102', '56': '15107', '64': '15103', '62': '15104'}], ['Визель П3-3630/2', ['48', '52', '54', '56', '58', '60', '62'], '3400', '15074', {'60': '15076', '54': '15079', '58': '15077', '48': '15082', '52': '15080', '62': '15075', '56': '15078'}], ['Визель П3-3630/1', ['48', '50', '52', '54', '56', '58', '60', '62'], '3400', '15058', {'60': '15060', '54': '15063', '58': '15061', '48': '15066', '52': '15064', '50': '15065', '62': '15059', '56': '15062'}], ['Визель П3-3640/1', ['48', '50', '52', '54', '56', '58', '60'], '4200', '15031', {'60': '15032', '54': '15035', '58': '15033', '48': '15038', '52': '15036', '50': '15037', '56': '15034'}], ['Визель П3-3195/2', ['48', '50', '52', '54', '56', '58', '60'], '4200', '15001', {'60': '15002', '54': '15005', '58': '15003', '48': '15008', '52': '15006', '50': '15007', '56': '15004'}], ['Визель П4-3635/1', ['48', '50', '52', '54', '56', '58', '60'], '3400', '14987', {'60': '14988', '54': '14991', '58': '14989', '48': '14994', '52': '14992', '50': '14993', '56': '14990'}], ['Визель П4-3637/3', ['48', '50', '52', '54', '56', '58', '60'], '4400', '14974', {'48': '14981', '54': '14978', '58': '14976', '60': '14975', '52': '14979', '50': '14980', '56': '14977'}], ['Визель П4-3638/3', ['48', '50', '52', '54', '56', '58', '60'], '3800', '14959', {'48': '14963', '54': '14961', '58': '14960', '60': '14966', '52': '14965', '50': '14964', '56': '14962'}], ['Визель П4-3638/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '14944', {'48': '14951', '54': '14948', '58': '14946', '60': '14945', '52': '14949', '50': '14950', '56': '14947'}], ['Прима 4052', ['46', '48', '50', '52', '54', '56'], '2580', '14894', {'48': '14900', '52': '14898', '46': '14901', '50': '14899', '54': '14897', '56': '14896'}], ['Авигаль П-467', ['52', '54', '56', '58', '60', '62', '64'], '3200', '14846', {'60': '14849', '54': '14852', '58': '14850', '52': '14853', '62': '14848', '64': '14847', '56': '14851'}], ['Новита 602', ['48', '50', '52', '54', '56'], '2600', '14731', {'52': '14734', '50': '14735', '54': '14733', '48': '14736', '56': '14732'}], ['Новита 578 красный', ['48', '50', '52', '54', '56', '58'], '3000', '14709', {'48': '14715', '54': '14712', '58': '14710', '52': '14713', '50': '14714', '56': '14711'}], ['Новита 455/1', ['48', '50', '52', '54', '56'], '3000', '14655', {'52': '14658', '50': '14659', '54': '14657', '48': '14660', '56': '14656'}], ['Новита 619', ['48', '50', '52', '54', '56'], '2800', '14630', {'52': '14633', '50': '14634', '54': '14632', '48': '14635', '56': '14631'}], ['Новита 595', ['48', '50', '52', '54'], '2900', '14611', {'52': '14613', '50': '14614', '54': '14612', '48': '14615'}], ['Новита 375 бежевый орнамент', ['50', '52', '54', '56', '58', '60'], '2900', '14599', {'60': '14600', '54': '14603', '58': '14601', '52': '14604', '50': '14605', '56': '14602'}], ['Авигаль П-062-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2700', '14574', {'60': '14580', '54': '14583', '58': '14581', '68': '14576', '52': '14584', '66': '14577', '70': '14575', '62': '14579', '64': '14578', '56': '14582'}], ['Авигаль П-062', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2700', '14560', {'60': '14566', '54': '14569', '58': '14567', '68': '14562', '52': '14570', '66': '14563', '70': '14561', '62': '14565', '64': '14564', '56': '14568'}], ['Авигаль П-548-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '14549', {'60': '14553', '54': '14556', '58': '14554', '52': '14557', '66': '14550', '56': '14555', '64': '14551', '62': '14552'}], ['Авигаль П-548', ['52', '54', '56', '58', '60', '62', '64'], '3700', '14536', {'60': '14540', '54': '14543', '58': '14541', '62': '14539', '64': '14538', '52': '14544', '56': '14542'}], ['Визель П3-3620/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14468', {'60': '14469', '54': '14472', '58': '14470', '48': '14475', '52': '14473', '50': '14474', '56': '14471'}], ['Краса П-0085', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14451', {'60': '14455', '54': '14458', '58': '14456', '52': '14459', '66': '14452', '56': '14457', '64': '14453', '62': '14454'}], ['Краса П-0086', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14436', {'60': '14440', '54': '14443', '58': '14441', '52': '14444', '66': '14437', '56': '14442', '64': '14438', '62': '14439'}], ['Краса П-0087', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14421', {'60': '14425', '54': '14428', '58': '14426', '52': '14429', '66': '14422', '56': '14427', '64': '14423', '62': '14424'}], ['Визель\xa0П3-3616/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14289', {'60': '14290', '54': '14293', '58': '14291', '48': '14296', '52': '14294', '50': '14295', '56': '14292'}], ['Визель П3-3616/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14276', {'60': '14277', '54': '14280', '58': '14278', '48': '14283', '52': '14281', '50': '14282', '56': '14279'}], ['Визель П2-3617/5', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14263', {'48': '14269', '54': '14266', '58': '14264', '60': '14270', '52': '14267', '50': '14268', '56': '14265'}], ['Визель П2-3617/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14249', {'48': '14255', '54': '14252', '58': '14250', '60': '14256', '52': '14253', '50': '14254', '56': '14251'}], ['Визель П2-3617/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14236', {'60': '14237', '54': '14240', '58': '14238', '48': '14243', '52': '14241', '50': '14242', '56': '14239'}], ['Краса ПБ-0010', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14220', {'60': '14224', '54': '14227', '58': '14225', '52': '14228', '66': '14221', '56': '14226', '64': '14222', '62': '14223'}], ['Краса ПБ-0011', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14208', {'60': '14212', '54': '14215', '58': '14213', '52': '14216', '66': '14209', '56': '14214', '64': '14210', '62': '14211'}], ['Краса ПБ-0016', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '14157', {'60': '14158', '54': '14163', '58': '14159', '52': '14164', '50': '14165', '62': '14160', '64': '14161', '56': '14162'}], ['Краса ПБ-0017', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '14144', {'60': '14147', '54': '14150', '58': '14148', '52': '14151', '50': '14152', '62': '14146', '64': '14145', '56': '14149'}], ['Новита 600 мятный', ['48', '50', '52', '54', '56'], '3300', '14071', {'52': '14073', '48': '14075', '54': '14072', '56': '14076', '50': '14074'}], ['Новита 600 голубой', ['48', '50', '52', '54', '56'], '3300', '14060', {'52': '14063', '50': '14064', '54': '14062', '48': '14065', '56': '14061'}], ['Новита 583 кремово-розовый', ['48', '50', '52', '54', '56'], '3200', '14040', {'52': '14043', '50': '14044', '54': '14042', '48': '14045', '56': '14041'}], ['Авигаль П-229-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2200', '13983', {'58': '13985', '72': '13992', '68': '13994', '74': '13993', '64': '13989', '60': '13988', '54': '13990', '52': '13987', '66': '13986', '70': '13995', '62': '13991', '56': '13984'}], ['Краса ПБ-0020', ['52', '54', '56', '58', '60'], '2400', '13852', {'52': '13860', '60': '13856', '54': '13859', '58': '13857', '56': '13858'}], ['Краса ПБ-0024', ['56', '58', '60', '62', '64', '66'], '2400', '13807', {'60': '13811', '58': '13812', '66': '13808', '56': '13813', '64': '13809', '62': '13810'}], ['Авигаль П-305-2', ['54', '56', '60', '62', '64', '66', '68'], '2500', '13746', {'60': '13755', '54': '13758', '68': '13751', '66': '13752', '56': '13757', '62': '13754', '64': '13753'}], ['Авигаль П-305-1', ['54', '56', '58', '60'], '2500', '13734', {'60': '13739', '54': '13742', '58': '13740', '56': '13741'}], ['Авигаль П-305', ['54', '56', '58', '60', '62', '64', '66', '68'], '2500', '13722', {'60': '13727', '54': '13730', '58': '13728', '66': '13724', '68': '13723', '56': '13729', '62': '13726', '64': '13725'}], ['Краса П-0035', ['52', '54', '56', '58', '60', '62'], '2400', '13661', {'60': '13663', '54': '13666', '58': '13664', '52': '13667', '62': '13662', '56': '13665'}], ['Краса П-0033', ['56', '58', '60', '62', '64', '66'], '2400', '13634', {'60': '13638', '58': '13639', '66': '13635', '56': '13640', '64': '13636', '62': '13637'}], ['Краса П-0037', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13621', {'60': '13625', '54': '13628', '58': '13626', '52': '13629', '66': '13622', '56': '13627', '62': '13624', '64': '13623'}], ['Авигаль П-445-1', ['52', '54', '56', '58', '60', '62', '66', '68', '70'], '2900', '13602', {'60': '13605', '54': '13608', '58': '13606', '68': '13611', '52': '13609', '66': '13612', '70': '13610', '62': '13604', '56': '13607'}], ['Краса П-0049', ['52', '54', '56', '58'], '2400', '13504', {'52': '13512', '54': '13511', '58': '13509', '56': '13510'}], ['Краса П-0060', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13489', {'60': '13494', '54': '13497', '58': '13495', '52': '13498', '66': '13491', '56': '13496', '64': '13492', '62': '13493'}], ['Краса П-0052', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13476', {'60': '13479', '54': '13482', '58': '13480', '52': '13483', '66': '13484', '62': '13478', '64': '13477', '56': '13481'}], ['Краса П-0061', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13463', {'60': '13467', '54': '13470', '58': '13468', '52': '13471', '66': '13464', '56': '13469', '64': '13465', '62': '13466'}], ['Краса П-0050', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13449', {'60': '13453', '54': '13456', '58': '13454', '52': '13457', '66': '13450', '56': '13455', '64': '13451', '62': '13452'}], ['Краса П-0057', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13409', {'60': '13413', '54': '13416', '58': '13414', '52': '13417', '66': '13410', '56': '13415', '64': '13411', '62': '13412'}], ['Краса П-0064', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '13396', {'60': '13399', '54': '13402', '58': '13400', '62': '13398', '50': '13404', '64': '13397', '52': '13403', '56': '13401'}], ['Краса П-0055', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13369', {'60': '13373', '54': '13376', '58': '13374', '52': '13377', '66': '13370', '56': '13375', '64': '13371', '62': '13372'}], ['Краса П-0078', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13343', {'60': '13347', '54': '13350', '58': '13348', '52': '13351', '66': '13344', '56': '13349', '64': '13345', '62': '13346'}], ['Визель П3-3615/1', ['52', '54', '56', '58', '60'], '3600', '13175', {'52': '13180', '60': '13176', '54': '13179', '58': '13177', '56': '13178'}], ['Визель П2-3609/1', ['50', '52', '54', '56', '58', '60'], '3400', '13050', {'60': '15664', '54': '13054', '58': '15663', '52': '13055', '50': '13056', '56': '13053'}], ['Визель П3-3240', ['48', '50', '52', '54', '56', '58'], '3600', '13037', {'48': '13044', '54': '13041', '58': '13039', '52': '13042', '50': '13043', '56': '13040'}], ['Авигаль П-704', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2900', '12800', {'60': '12806', '54': '12802', '58': '12805', '68': '12804', '52': '12803', '66': '12809', '62': '12807', '64': '12808', '56': '12801'}], ['Авигаль П-446', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600', '12768', {'60': '12774', '54': '12777', '58': '12775', '68': '12770', '52': '12778', '66': '12771', '56': '12776', '70': '12769', '62': '12773', '64': '12772'}], ['Новита 461', ['48', '50', '52'], '3100', '12595', {'52': '12596', '50': '12597', '48': '12598'}], ['Визель П3-3596/3', ['48', '50', '52', '54', '56', '58', '60'], '4000', '12436', {'60': '12437', '54': '12440', '58': '12438', '48': '12443', '52': '12441', '50': '12442', '56': '12439'}], ['Визель П3-3479/5', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12417', {'48': '14130', '54': '14127', '58': '14125', '60': '14124', '52': '14128', '50': '14129', '56': '14126'}], ['Визель П3-3479/3', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12405', {'48': '12409', '54': '14133', '58': '12407', '60': '12406', '52': '14134', '50': '12408', '56': '14132'}], ['Авигаль-П-409-1', ['52', '54'], '3360', '12388', {'52': '12391', '54': '12390'}], ['Авигаль-П-127', ['52', '54', '56'], '2600', '12362', {'52': '14742', '54': '12367', '56': '12366'}], ['Прима 4035', ['48', '54'], '3780', '12173', {'48': '12181', '54': '12178'}], ['Новита 589 зеленый', ['48', '50', '52', '54', '56'], '3000', '12046', {'52': '12049', '50': '12050', '54': '12048', '48': '12051', '56': '12047'}], ['Новита 588 желтый', ['48', '50', '52', '54', '56', '58'], '3200', '12036', {'48': '12042', '54': '12039', '58': '12037', '52': '12040', '50': '12041', '56': '12038'}], ['Новита 587 дымчато-сиреневый', ['48', '50', '52', '54', '56', '58'], '3200', '12016', {'48': '12022', '54': '12019', '58': '12017', '52': '12020', '50': '12021', '56': '12018'}], ['Новита 587 дымчато-розовый', ['48', '50', '52', '54', '58'], '3200', '12006', {'52': '12010', '50': '12011', '54': '12009', '58': '12007', '48': '12012'}], ['Новита 581 белые цветы', ['50', '52', '54', '56'], '3300', '11981', {'52': '11987', '50': '11988', '54': '11986', '56': '11985'}], ['Авигаль-П-506-2', ['54', '56', '58', '60', '62', '64', '66'], '2900', '11970', {'60': '11974', '54': '11977', '58': '11975', '66': '11971', '56': '11976', '64': '11972', '62': '11973'}], ['Авигаль-П-700-1', ['54', '56', '58', '64', '66'], '3700', '11941', {'66': '11942', '54': '11947', '64': '11943', '58': '11945', '56': '11946'}], ['Авигаль-П-327-1', ['52', '54', '56', '58'], '2200', '11931', {'52': '11938', '54': '11937', '58': '14938', '56': '11936'}], ['Визель П4-3350/2', ['48', '50', '52', '54', '56'], '4200', '11874', {'52': '11876', '48': '11878', '54': '11875', '56': '14784', '50': '11877'}], ['Визель П3-3494/3', ['48', '50', '52', '54'], '3800', '11851', {'52': '11856', '48': '11858', '54': '11855', '50': '11857'}], ['Авигаль-П-264-1', ['56', '58', '60', '62', '64', '66'], '3300', '11810', {'60': '11811', '58': '11815', '66': '11814', '56': '11816', '64': '11813', '62': '11812'}], ['Авигаль-П-264-2', ['50', '52', '54', '56', '58', '60', '62', '64', '66'], '3300', '11793', {'60': '11802', '54': '11805', '58': '11803', '50': '11807', '52': '11806', '66': '11799', '56': '11804', '62': '11801', '64': '11800'}], ['Авигаль-П-264-3', ['58', '62', '64', '66'], '3300', '11785', {'66': '11786', '62': '11788', '58': '11789', '64': '11787'}], ['Авигаль-П-871-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '11773', {'60': '11777', '54': '11774', '58': '11776', '52': '11778', '66': '11781', '62': '11780', '64': '11779', '56': '11775'}], ['Авигаль-П-871', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '11761', {'60': '11765', '54': '11768', '58': '11766', '52': '11769', '66': '11762', '62': '11764', '64': '11763', '56': '11767'}], ['Авигаль-П-867-1', ['52', '54', '56', '58', '60', '62', '64'], '3200', '11568', {'60': '11572', '54': '11575', '58': '11573', '62': '11571', '64': '11570', '52': '11576', '56': '11574'}], ['Авигаль-П-867', ['52', '54', '56', '58', '60', '62', '64'], '3200', '11555', {'60': '11559', '54': '11562', '58': '11560', '62': '11558', '64': '11557', '52': '11563', '56': '11561'}], ['Авигаль-П-893-1', ['50', '52', '54', '56', '58', '60', '62'], '3300', '11542', {'60': '11545', '54': '11548', '58': '11546', '52': '11549', '50': '11550', '62': '11544', '56': '11547'}], ['Авигаль-П-893', ['50', '52', '54', '56', '58', '60', '62'], '3300', '11530', {'60': '11533', '54': '11536', '58': '11534', '52': '11537', '50': '11538', '62': '11532', '56': '11535'}], ['Авигаль-П-709', ['52', '54', '62', '64', '66', '68'], '2200', '11504', {'54': '11513', '66': '11507', '52': '11514', '68': '11506', '62': '11509', '64': '11508'}], ['Визель П3-3584/1', ['48', '50', '52', '54', '60'], '3000', '11404', {'52': '11409', '48': '11411', '54': '11408', '60': '15667', '50': '11410'}], ['Визель П3-3585/3', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11390', {'60': '11391', '54': '11394', '58': '11392', '48': '11397', '52': '11395', '50': '11396', '56': '11393'}], ['Авигаль-П-705', ['52', '54', '56', '60'], '2200', '11351', {'52': '11356', '60': '11353', '54': '11355', '56': '11354'}], ['Авигаль-П-705-1', ['52', '54', '56', '58', '60', '62'], '2200', '11340', {'60': '11343', '54': '11346', '58': '11344', '52': '11347', '62': '11342', '56': '11345'}], ['Авигаль-П-869-2', ['50', '52', '54', '60', '62'], '2900', '11316', {'52': '11320', '50': '11322', '54': '11321', '62': '11323', '60': '11318'}], ['Авигаль-П-869-1', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900', '11304', {'60': '11308', '54': '11311', '58': '11309', '52': '11310', '50': '11312', '62': '11305', '64': '11307', '56': '11306'}], ['Авигаль-П-869', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900', '11292', {'60': '11295', '54': '11298', '58': '11296', '52': '11299', '50': '11300', '56': '11297', '62': '11294', '64': '11293'}], ['Авигаль-П-702', ['52', '54', '56', '58', '60', '62'], '2400', '11256', {'60': '11258', '54': '11261', '58': '11259', '52': '11262', '62': '11257', '56': '11260'}], ['Авигаль-П-270-3', ['52', '54'], '2500', '11213', {'52': '11224', '54': '14745'}], ['Авигаль-П-270', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500', '11198', {'60': '11204', '54': '11207', '58': '11205', '68': '11202', '52': '11208', '66': '11201', '70': '11199', '62': '11203', '64': '11200', '56': '11206'}], ['Авигаль-П-270-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500', '11184', {'60': '11190', '54': '11193', '58': '11191', '66': '11187', '52': '11194', '68': '11186', '70': '11185', '62': '11189', '64': '11188', '56': '11192'}], ['Новита 590 цветная абстракция', ['48', '50', '52', '54', '56'], '3200', '11169', {'52': '11172', '50': '11173', '54': '11171', '48': '11174', '56': '11170'}], ['Новита 584 мятный', ['48', '50', '52', '54', '56'], '2580', '11149', {'52': '11152', '50': '11153', '54': '11151', '48': '11154', '56': '11150'}], ['Новита 582 синий орнамент', ['48', '50', '52', '54', '56'], '3100', '11137', {'52': '11140', '50': '11141', '54': '11139', '48': '11142', '56': '11138'}], ['Новита 580 изумрудный', ['50', '52', '54', '56'], '3000', '11127', {'52': '11135', '50': '11136', '54': '11134', '56': '11133'}], ['Авигаль-П-706-3', ['52', '56', '72', '74'], '2900', '11111', {'52': '11118', '72': '11121', '74': '11120', '56': '11112'}], ['Авигаль-П-706-1', ['52', '54', '56', '58', '60', '62', '64', '68', '70', '72', '74'], '2900', '11068', {'60': '11087', '54': '11090', '58': '11088', '72': '11081', '52': '11091', '68': '11083', '74': '11080', '70': '11082', '62': '11086', '64': '11085', '56': '11089'}], ['Авигаль-П-706-2', ['54', '56', '66', '72'], '2900', '11050', {'66': '11057', '54': '11063', '72': '11055', '56': '11062'}], ['Авигаль-П-503', ['50', '52', '54', '56', '58', '60', '62', '64'], '2960', '11039', {'60': '11045', '54': '11048', '58': '11046', '52': '11049', '50': '11041', '62': '11044', '64': '11043', '56': '11047'}], ['Новита 579 полоска', ['48', '50', '52', '54', '56'], '3100', '11011', {'52': '11014', '50': '11015', '54': '11013', '48': '11016', '56': '11012'}], ['Авигаль-П-503-1', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66'], '2960', '10916', {'60': '10921', '54': '10924', '58': '10922', '48': '10927', '52': '10925', '66': '10918', '50': '10926', '62': '10920', '64': '10919', '56': '10923'}], ['Авигаль-П-100-1', ['52', '54', '56', '58', '60', '62', '64'], '2500', '10905', {'60': '10908', '54': '10906', '58': '10907', '52': '10909', '62': '10911', '64': '10912', '56': '10910'}], ['Авигаль-П-100', ['52', '54', '56', '58', '60', '62', '64'], '2500', '10894', {'60': '10897', '54': '10900', '58': '10898', '52': '10901', '62': '10896', '64': '10895', '56': '10899'}], ['Авигаль-П-488-1', ['52', '54', '58', '60', '62', '66'], '2700', '10779', {'60': '10785', '54': '10788', '58': '10786', '52': '10789', '66': '10782', '62': '10784'}], ['Прима 2754-4', ['52', '54', '56', '58', '60', '62', '64'], '4400', '10575', {'60': '10578', '54': '10581', '58': '10579', '52': '10582', '62': '10577', '64': '10576', '56': '10580'}], ['Прима 2856', ['56', '58', '60', '62', '64', '68'], '3400', '10551', {'60': '15776', '58': '15096', '68': '10553', '56': '15681', '64': '10554', '62': '15095'}], ['Прима 4018', ['52', '54', '56', '60', '62', '64', '66', '68'], '3200', '10524', {'60': '10528', '54': '10530', '52': '10531', '62': '10527', '64': '15774', '56': '10529'}], ['Прима 4001', ['44', '46', '48', '50', '52'], '5800', '10479', {'46': '15682', '48': '10483', '52': '10486', '44': '10488', '50': '10484'}], ['Новита 566', ['50', '52', '54', '56'], '3100', '10237', {'52': '13249', '50': '10242', '54': '10240', '56': '10239'}], ['Визель-П4-2571/9', ['48', '50', '52', '54', '56', '58', '60'], '4200', '9806', {'60': '9807', '54': '9810', '58': '9808', '48': '9813', '52': '9811', '50': '9812', '56': '9809'}], ['Визель-П4-2571/13', ['48', '50', '52', '54', '56', '58', '60'], '4200', '9774', {'48': '9787', '54': '9784', '58': '9782', '60': '9781', '52': '9785', '50': '9786', '56': '9783'}], ['Визель-П4-2571/11', ['48', '50', '52', '54'], '4200', '9760', {'52': '9765', '48': '9767', '54': '9764', '50': '9766'}], ['Визель-П5-3506/8', ['48', '50', '52', '54', '56', '58', '60'], '3800', '9727', {'60': '9728', '54': '9731', '58': '9729', '48': '9734', '52': '9732', '50': '9733', '56': '9730'}], ['Визель-П5-3506/6', ['48', '50', '52', '54', '56', '58', '60'], '3800', '9711', {'60': '9712', '54': '9715', '58': '9713', '48': '9718', '52': '9716', '50': '9717', '56': '9714'}], ['Визель-П5-3506/4', ['54', '56', '58', '60'], '3800', '9698', {'60': '9699', '54': '9702', '58': '9700', '56': '9701'}], ['Визель-П5-3506/10', ['52', '56', '58'], '3800', '9682', {'52': '9687', '58': '9684', '56': '9685'}], ['Визель-П3-3557/1', ['50', '52', '54'], '4000', '9668', {'52': '9679', '50': '9680', '54': '9678'}], ['Визель-П5-3563/1', ['48', '50', '52', '54', '56', '58'], '4200', '9570', {'48': '9577', '54': '9574', '58': '9572', '52': '9575', '50': '9576', '56': '9573'}], ['Визель П4-3559/1', ['48', '50', '52', '54', '56', '58', '60'], '3400', '9372', {'60': '9373', '54': '9376', '58': '9374', '48': '9379', '52': '9377', '50': '9378', '56': '9375'}], ['Новита 573', ['48', '50', '54', '56'], '3200', '9291', {'48': '9296', '50': '9295', '54': '9293', '56': '9292'}], ['Новита 569', ['48', '50', '52', '54', '56'], '3000', '9283', {'52': '9286', '48': '9288', '54': '9285', '50': '9287', '56': '9284'}], ['Прима 2982', ['52', '54', '56', '58'], '3520', '9070', {'52': '9074', '54': '9073', '58': '9071', '56': '9072'}], ['Визель-П4-2571/5', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8771', {'60': '8772', '54': '8775', '58': '8773', '48': '8778', '52': '8776', '50': '8777', '56': '8774'}], ['Новита 556', ['50', '52', '54', '56'], '3100', '8633', {'52': '14778', '50': '14779', '54': '8636', '56': '8635'}], ['Визель П4-3423/5', ['52', '54', '56', '58'], '3320', '8496', {'52': '8501', '54': '8500', '58': '8498', '56': '8499'}], ['Прима 2662', ['46', '48', '50', '54', '56'], '4200', '8390', {'46': '15684', '50': '14747', '54': '8392', '48': '15683', '56': '8391'}], ['Прима 2977', ['48', '50', '52', '54', '56', '58'], '3580', '8197', {'48': '8203', '54': '8200', '58': '8198', '52': '8201', '50': '8202', '56': '8199'}], ['Новита 485/1', ['50', '52', '54', '56', '58'], '3300', '7629', {'52': '7639', '50': '7640', '54': '7638', '58': '7636', '56': '7637'}], ['Новита 547', ['48', '50', '52', '54'], '3200', '7602', {'52': '7605', '50': '7606', '54': '7604', '48': '7607'}], ['Новита 401', ['48', '50', '52', '54', '56'], '2600', '7443', {'52': '7446', '50': '7447', '54': '7445', '48': '7448', '56': '7444'}], ['Новита 355/1 морская волна', ['46', '48', '52', '56'], '3100', '7369', {'46': '7371', '48': '7370', '52': '7374', '56': '7372'}], ['Новита 355/1 розовая пудра', ['46', '50'], '3100', '7360', {'46': '7366', '50': '13961'}], ['Прима 2874', ['52', '56', '60', '62', '64', '66', '68', '70'], '4400', '7041', {'60': '7046', '68': '13941', '52': '13945', '66': '13942', '56': '13944', '70': '13940', '62': '7045', '64': '7044'}], ['Прима 2877', ['48', '54', '56', '58'], '4200', '7029', {'48': '7036', '54': '7033', '58': '7031', '56': '12401'}], ['Новита 550', ['48', '50', '52', '54', '56'], '3100', '6931', {'52': '6934', '50': '6935', '54': '6933', '48': '6936', '56': '6932'}], ['Прима 2906', ['44', '46', '54', '56', '58', '64'], '3200', '6741', {'54': '9034', '44': '7290', '58': '7283', '46': '7289', '64': '7280', '56': '9033'}], ['Прима 2898', ['48', '50', '52', '54', '62'], '3600', '6729', {'52': '6734', '48': '6736', '54': '6733', '62': '11758', '50': '6735'}], ['Прима 2935', ['48', '50', '52', '54', '56', '58'], '3640', '6605', {'48': '6610', '54': '8562', '58': '8564', '52': '8561', '50': '6609', '56': '8563'}], ['Новита 526', ['44', '46', '52'], '2800', '6366', {'46': '6371', '52': '6368', '44': '6372'}], ['Новита-321 алый', ['54'], '3000', '6152', {'54': '6154'}], ['Новита-519', ['48', '50'], '3100', '5522', {'48': '5527', '50': '5526'}], ['Новита-529', ['50', '52', '54', '56'], '3100', '5467', {'52': '5470', '50': '5471', '54': '5469', '56': '5468'}], ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '3499', '5011', {'66': '9645'}], ['Визель-П2-3477/1', ['52', '54', '58'], '3800', '4493', {'52': '4498', '54': '4497', '58': '4495'}], ['Новита-516', ['50', '52', '54', '56', '58'], '3100', '4192', {'52': '4196', '50': '4197', '54': '4195', '58': '4193', '56': '4194'}], ['Новита-334', ['48', '50', '52', '54', '56', '58'], '3200', '4152', {'48': '4158', '54': '4155', '58': '4153', '52': '4156', '50': '4157', '56': '4154'}], ['Новита-345/1', ['48', '50', '52', '54', '56'], '3000', '3742', {'52': '3745', '50': '3746', '54': '3744', '48': '3747', '56': '3743'}], ['Новита-496', ['50', '52', '54', '56', '58'], '3200', '3719', {'52': '3723', '50': '3724', '54': '3722', '58': '3720', '56': '3721'}], ['Новита-511', ['50', '52', '54', '56'], '3200', '3662', {'52': '3665', '50': '3666', '54': '3664', '56': '3663'}], ['Олеся-28001-1', ['54', '56'], '3360', '3462', {'54': '3465', '56': '7297'}], ['Новита-408', ['50', '58'], '3000', '3399', {'50': '11372', '58': '3400'}], ['Джетти-Б092-2', ['54'], '2640', '2287', {'54': '2290'}], ['Джетти-Б092-4', ['54'], '2640', '2280', {'54': '2283'}], ['Джетти-Б163-4', ['58'], '2400', '2213', {'58': '9658'}], ['Со-СЕВАСТЬЯНА оригами', ['52'], '4000', '2096', {'52': '9639'}], ['ЕО-24042-1', ['54'], '3700', '1865', {'54': '1870'}], ['JБ-Б165-1', ['56'], '3100', '1784', {'56': '1792'}], ['JБ-Б201-2', ['60'], '2900', '1699', {'60': '9656'}]], [['Визель-М3-3149/14', ['48', '50', '52', '54', '56', '58', '60'], '1700', '7888', {'60': '14785', '54': '14788', '58': '14786', '48': '14791', '52': '14789', '50': '14790', '56': '14787'}], ['Новита 604 голубые цветы', ['48', '50', '52'], '1580', '13022', {'52': '13027', '48': '13024', '50': '13025'}], ['Новита 604', ['48', '52', '54'], '1580', '12658', {'52': '12705', '48': '12707', '54': '12704'}], ['Новита 557', ['48', '50', '52', '54', '56'], '2600', '8642', {'52': '8645', '50': '8646', '54': '8644', '48': '8647', '56': '8643'}], ['Визель М4-3225/9', ['54', '56', '60'], '3000', '11474', {'60': '11479', '54': '12541', '56': '12540'}], ['Новита 026 серые цветы', ['50', '52', '54', '56', '58'], '1500', '9120', {'52': '9124', '50': '9125', '54': '9123', '58': '9121', '56': '9122'}], ['Визель-М4-3338', ['48', '50', '52', '54', '56', '58', '60'], '2160', '8970', {'60': '8971', '54': '8974', '58': '8972', '48': '8977', '52': '8975', '50': '8976', '56': '8973'}], ['Новита 487 серый', ['50', '52', '54', '56'], '2100', '8587', {'52': '8590', '50': '8591', '54': '8589', '56': '8588'}], ['Визель-М4-3406/1', ['48', '50', '52', '54', '56'], '3000', '4950', {'52': '8181', '48': '4957', '54': '4954', '56': '4953', '50': '4956'}], ['Новита 505/1', ['48', '50', '52', '54', '56'], '2600', '9170', {'52': '9173', '50': '9174', '54': '9172', '48': '9175', '56': '9171'}], ['Визель-М4-2796/8', ['52', '58', '60'], '2160', '8948', {'52': '12142', '60': '8949', '58': '8950'}], ['Визель-М3-3473/3', ['48', '50', '52', '54', '56', '58', '60'], '2600', '8921', {'48': '12550', '54': '8928', '58': '8926', '60': '8925', '52': '8922', '50': '8923', '56': '8927'}], ['Визель-М3-3475/5', ['48', '50', '52', '54', '56', '58'], '2400', '4853', {'48': '4860', '54': '4857', '58': '4855', '52': '4858', '50': '12558', '56': '4856'}], ['Новита 616', ['48', '50', '52', '54', '56'], '1300', '14688', {'52': '14691', '50': '14692', '54': '14690', '48': '14693', '56': '14689'}], ['Визель М4-3264/3', ['48', '50', '52'], '3000', '14332', {'52': '14337', '50': '14338', '48': '14339'}], ['Новита 609', ['48', '50', '52', '54', '56'], '1600', '14103', {'52': '14106', '50': '14107', '54': '14105', '48': '14108', '56': '14104'}], ['Визель-М4-2796/10', ['52', '54', '56', '58', '60'], '2160', '8960', {'52': '8965', '60': '8961', '54': '8964', '58': '8962', '56': '8963'}], ['Визель-М4-3548/3', ['48', '50', '52', '54', '56', '58', '60'], '2400', '8853', {'60': '8854', '54': '8857', '58': '8855', '48': '8860', '52': '8858', '50': '8859', '56': '8856'}], ['Визель-М4-3548/1', ['48', '50', '52', '54', '56', '58', '60'], '2400', '8838', {'60': '8839', '54': '8842', '58': '8840', '48': '8845', '52': '8843', '50': '8844', '56': '8841'}], ['Прима 2938', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68'], '2760', '8267', {'48': '8278', '54': '8275', '68': '8269', '58': '8273', '60': '8272', '52': '8276', '50': '8277', '66': '8270', '62': '8271', '64': '9029', '56': '8274'}], ['Визель-М5-3390/1', ['50', '52', '54', '56', '58'], '2600', '7898', {'52': '7903', '50': '12564', '54': '7902', '58': '7900', '56': '7901'}], ['Новита-611', ['48', '50', '52', '54', '56', '58'], '1500', '15753', {'48': '15762', '54': '15759', '58': '15757', '52': '15760', '50': '15761', '56': '15758'}], ['Авигаль Т-118-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '1960', '14830', {'60': '14835', '54': '14833', '58': '14834', '68': '14838', '52': '14831', '66': '14839', '70': '14840', '62': '14836', '64': '14837', '56': '14832'}], ['Авигаль Т-118', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '1960', '14816', {'60': '14822', '62': '14821', '54': '14825', '58': '14823', '68': '14818', '52': '14826', '66': '14819', '70': '14817', '64': '14820', '56': '14824'}], ['Визель М4-3247/3', ['52', '54', '56', '58', '60'], '2600', '14524', {'52': '14529', '60': '14525', '54': '14528', '58': '14526', '56': '14527'}], ['Визель М4-3247/5', ['52', '54', '56', '58', '60'], '2600', '14512', {'52': '14517', '60': '14513', '54': '14516', '58': '14514', '56': '14515'}], ['Визель М3-3149/20', ['52', '54', '56', '58', '60'], '1500', '14378', {'52': '14383', '60': '14379', '54': '14382', '58': '14380', '56': '14381'}], ['Визель М4-3627/3', ['48', '50', '52', '54', '56', '58', '60'], '2600', '14361', {'48': '14363', '54': '14367', '58': '14365', '60': '14364', '52': '14368', '50': '14362', '56': '14366'}], ['Визель М4-3264/7', ['48', '50', '52', '54', '56', '58', '60'], '3000', '14318', {'60': '14319', '54': '14322', '58': '14320', '48': '14325', '52': '14323', '50': '14324', '56': '14321'}], ['Визель М4-3263/1', ['48', '50', '52', '54', '56', '58', '60'], '2800', '14304', {'60': '14305', '54': '14308', '58': '14306', '48': '14311', '52': '14309', '50': '14310', '56': '14307'}], ['Новита 189 цветы на сером', ['50', '56', '58'], '1600', '14029', {'50': '14034', '58': '14030', '56': '14031'}], ['Новита 189 розовые цветы', ['48', '50', '52', '54', '56', '58'], '1600', '14017', {'48': '14025', '54': '14022', '58': '14020', '52': '14023', '50': '14024', '56': '14021'}], ['Новита 604 красные цветы', ['48', '50', '52', '54', '56'], '1580', '13013', {'52': '13016', '48': '13018', '54': '13015', '50': '13017', '56': '13014'}], ['Авигаль-Т-067-1', ['54', '56', '58', '62'], '2000', '12379', {'54': '12384', '62': '12380', '58': '12382', '56': '12383'}], ['Визель М4-3345/9', ['48', '50', '52', '54', '56', '58', '60'], '3000', '11459', {'48': '11466', '54': '15665', '58': '11461', '60': '15666', '52': '11464', '50': '11465', '56': '11462'}], ['Визель М5-3536/5', ['48', '50', '52', '54', '56', '58', '60'], '3000', '11431', {'60': '11432', '54': '11435', '58': '11433', '48': '11438', '52': '11436', '50': '11437', '56': '11434'}], ['Визель М5-3580/1', ['52', '58', '60'], '2600', '10386', {'52': '10391', '60': '10387', '58': '10388'}], ['Визель-М4-3449/5', ['48', '50', '52', '54', '56', '58', '60'], '2300', '9899', {'60': '9900', '54': '9903', '58': '9901', '48': '9906', '52': '9904', '50': '9905', '56': '9902'}], ['Визель-М4-3449/3', ['50', '52', '54', '58', '60'], '2300', '9886', {'52': '9891', '60': '9887', '54': '9890', '58': '9888', '50': '9892'}], ['Визель-М3-3147/9', ['48', '50', '52', '54', '56', '58', '60'], '1500', '9862', {'60': '9863', '54': '9866', '58': '9864', '48': '9869', '52': '9867', '50': '9868', '56': '9865'}], ['Визель-М5-3564/1', ['48', '50', '52', '54', '56', '58', '60'], '2700', '9848', {'60': '9849', '54': '9852', '58': '9850', '48': '9855', '52': '9853', '50': '9854', '56': '9851'}], ['Визель-М4-3569/1', ['48', '50', '52', '54', '56', '58', '60'], '2800', '9822', {'60': '9823', '54': '9826', '58': '9824', '48': '9829', '52': '9827', '50': '9828', '56': '9825'}], ['Новита 026 цветы на бежевом', ['50', '52', '54', '56'], '1500', '9128', {'52': '9132', '50': '9133', '54': '9131', '56': '9130'}], ['Новита 026 цветы', ['50', '52', '54', '56', '58'], '1500', '9104', {'52': '9108', '50': '9109', '54': '9107', '58': '9105', '56': '9106'}], ['Визель-М4-2796/6', ['48', '50', '52', '54', '56', '58', '60'], '2160', '8936', {'60': '8937', '54': '8940', '58': '8938', '48': '8943', '52': '8941', '50': '8942', '56': '8939'}], ['Визель-М3-3473/1', ['52', '54', '56'], '2600', '8908', {'52': '8913', '54': '8912', '56': '8911'}], ['Визель-М5-3554/3', ['48', '50', '52', '54', '56', '58', '60'], '2260', '8894', {'60': '8895', '54': '8898', '58': '8896', '48': '8901', '52': '8899', '50': '8900', '56': '8897'}], ['Визель-М5-3358/11', ['52', '54', '56', '58', '60'], '2800', '8812', {'52': '8817', '60': '8813', '54': '8816', '58': '8814', '56': '8815'}], ['Визель-М5-3358/13', ['52', '56', '58', '60'], '2800', '8798', {'52': '8803', '60': '8799', '58': '8800', '56': '8801'}], ['Новита 120 серые цветы', ['46', '48', '50', '52', '54', '56'], '1400', '8540', {'48': '8545', '52': '8543', '46': '8546', '50': '11368', '54': '8542', '56': '11367'}], ['Прима 2870', ['48', '50', '52', '54', '56'], '2980', '8295', {'52': '11755', '48': '8299', '54': '11756', '56': '11754', '50': '8298'}], ['Прима 2763', ['52', '54', '56', '58'], '2200', '8283', {'52': '8290', '54': '8289', '58': '8287', '56': '8288'}], ['Визель-М3-3149/12', ['52', '54', '56', '58', '60'], '1700', '7876', {'52': '7881', '60': '13273', '54': '7880', '58': '7878', '56': '7879'}], ['Визель-М5-3536/1', ['52', '54', '56', '58', '60'], '3000', '7863', {'52': '7868', '60': '7864', '54': '7867', '58': '7865', '56': '7866'}], ['Визель-М3-3475/3', ['48', '50', '52', '54', '56', '58', '60'], '2400', '4840', {'60': '4841', '54': '4844', '58': '4842', '48': '4847', '52': '4845', '50': '4846', '56': '4843'}]], [['Визель-П3-3468/4', ['54'], '3800', '4555', {'54': '12729'}], ['Новита-509', ['50'], '3100', '3711', {'50': '3716'}], ['Визель-П4-3469/1', ['56'], '4000', '4426', {'56': '13274'}], ['Новита-242', ['56'], '4000', '4426', {'56': '13274'}], ['Новита-393В', ['56'], '3000', '4200', {'56': '4202'}], ['Олеся-24019-1', ['56'], '3400', '4113', {'56': '12138'}], ['Новита-492', ['50'], '3100', '3070', {'50': '9647'}], ['Олеся-27026-1', ['50', '52'], '3700', '2741', {'52': '2745', '50': '2746'}], ['Джетти-Б005-1', ['50', '52'], '3700', '2741', {'52': '2745', '50': '2746'}], ['ЕО-27014-1', ['50'], '3780', '1893', {'50': '1902'}], ['ЕО-27018-1', ['52'], '3385', '1873', {'52': '1877'}], ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '3200', '1795', {'52': '9640', '62': '9641'}], ['Новита-321 алый', ['54'], '3000', '6152', {'54': '6154'}], ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '3499', '5011', {'66': '9645'}], ['Визель-Др5-152/1', ['60'], '2640', '3941', {'60': '9778'}], ['Визель-Кн5-96/1', ['50'], '3200', '3915', {'50': '3917'}], ['Олеся-28001-1', ['54', '56'], '3360', '3462', {'54': '3465', '56': '7297'}], ['Джетти-Б092-2', ['54'], '2640', '2287', {'54': '2290'}], ['Джетти-Б092-4', ['54'], '2640', '2280', {'54': '2283'}], ['Джетти-Б163-4', ['58'], '2400', '2213', {'58': '9658'}], ['Со-СЕВАСТЬЯНА оригами', ['52'], '4000', '2096', {'52': '9639'}], ['ЕО-24042-1', ['54'], '3700', '1865', {'54': '1870'}], ['JБ-Б165-1', ['56'], '3100', '1784', {'56': '1792'}], ['JБ-Б201-2', ['60'], '2900', '1699', {'60': '9656'}]]]
    goods_data = []
    for site in dress_pages:
        compare_dress(site, bigmoda_pages[0], bigmoda_pages[1], wcapi)
        for dress in site:
            goods_data.append(dress)
        # for site in blouse_pages:
        #     compare_dress(site, bigmoda_pages[1], bigmoda_pages[2])
    del_item(goods_data)