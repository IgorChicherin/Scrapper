# -*- coding: utf-8 -*-
import requests
import os
import re
from bs4 import BeautifulSoup
import time
import sys


def create_sizes_dict(color_list, sizes_list, sizes_accepted):
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
        data['name'] = re.search(r'(?<=№)(\d+/\d+)|(\d+)', soup.h1.text.strip()).group(0)
        colors = soup.find_all('td', {'class': 'col-color'})
        data['color_list'] = [color.text.strip() for color in colors if color.text.strip() != 'Цвет/размер']
        data['sizes_list'] = soup.find_all('td', {'class': 'inv'})
        data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
        data['color_size'] = {color: data['sizes_list'].copy() for color in data['color_list']}
        data['sizes_accepted'] = soup.find_all('td', {'class': 'tdforselect'})
        data['sizes_accepted'] = ['disabled' if 'disabled' in size_accepted['class'] else 'enabled' for size_accepted in
                                  data['sizes_accepted']]
        data['price'] = soup.find('div', {'class': 'value'}).text.replace(',', '').split('.')
        data['price'] = data['price'][0]
        color_size_tags = create_sizes_dict(data['color_list'], data['sizes_list'], data['sizes_accepted'])
        for key, value in color_size_tags.items():
            for item in range(len(value)):
                if value[item] == 'disabled':
                    data['color_size'][key].pop(color_size_tags[key].index(value[item]))
        for key in data['color_size']:
                # print(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price']])
                result.append(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price']])
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
        data['name'] = data['name'].split(' ')[2] if len(data['name'].split(' ')) > 2 and \
                                                     'new' not in data['name'].split(' ') else data['name'].split(' ')[
            1]
        price = soup.find('div', attrs={'id': 'catalog-item-description'})
        price = re.search(r'(\d+)', price.p.text.strip().replace(' ', ''))
        data['price'] = int(price.group(0)) * 2
        data['sizes_list'] = soup.find_all('option')
        data['sizes_list'] = [item.text for item in data['sizes_list']]
        # print('Прима ' + data['name'].lower(), data['sizes_list'], data['price'])
        result.append(['Прима ' + data['name'], data['sizes_list'], data['price']])
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
    data['paginaton_url'] = []
    data['item_links'] = []
    items_link_list = []
    for page in data['paginaton']:
        try:
            link = page.a.text
        except AttributeError:
            continue
        if page.a.get('href') not in data['paginaton_url']:
            data['paginaton_url'].append(page.a.get('href'))
        for link in data['paginaton_url']:
            items_link_list = soup.find_all('a', {'class': 'hover-image'})
            items_link_list = [item.get('href') for item in items_link_list]
            i = 0
            l = len(items_link_list)
            printProgressBar(i, l, prefix='Progress:', suffix='Complete', length=50)
            for link in items_link_list:
                r = session.get(link)
                soup = BeautifulSoup(r.text, 'lxml')
                data['price'] = soup.find('span', attrs={'class': 'micro-price', 'itemprop': 'price'})
                data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
                data['price'] = int(data['price'].group(0)) * 2
                if data['price'] > 2500:
                    data['name'] = soup.find('span', attrs={'itemprop': 'model'})
                    data['name'] = data['name'].text
                    sizes_list = soup.find_all('label', {'class': 'optid-13'})
                    data['sizes_list'] = []
                    for item in sizes_list:
                        if r':n\a' not in item['title']:
                            data['sizes_list'].append(item.text.strip())
                    # print('Авигаль ' + data['name'], data['sizes_list'], data['price'])
                    result.append(['Авигаль ' + data['name'], data['sizes_list'], data['price']])
                time.sleep(0.1)
                i += 1
                printProgressBar(i, l, prefix='Avigal Parsing:', suffix='Complete', length=50)
    return result


def wisell_parse(url):
    '''
    Parsing Wisell Site
    :param url: str
    :return: list
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    data = {}
    result = []
    data['paginaton'] = soup.find_all('div', {'class': 'page_navi'})
    pagination_links = data['paginaton'][0].find_all('a', {'class': 'menu_link'})
    data['paginaton'] = [item.get('href') for item in pagination_links]
    data['paginaton_url'] = [url]
    for link in data['paginaton']:
        if 'https://wisell.ru' + link not in data['paginaton_url']:
            data['paginaton_url'].append('https://wisell.ru' + link)
    j = 1
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'item_title'})
        data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
        # i = 0
        # l = len(data['item_links'])
        # printProgressBar(i, l, prefix='Progress:',
        #                  suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        for item_link in data['item_links']:
            r = requests.get(item_link)
            soup = BeautifulSoup(r.text, 'lxml')
            data['price'] = soup.find('span', attrs={'class': 'price_val'})
            data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
            data['price'] = int(data['price'].group(0))
            if data['price'] < 1800:
                # i += 1
                # printProgressBar(i, l, prefix='Wisell Parsing:',
                #                  suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                continue
            data['name'] = soup.find('li', attrs={'class': 'item_lost'})
            data['name'] = data['name'].span.text
            data['sizes_list'] = soup.find_all('ul', {'class': 'size_list'})
            data['sizes_list'] = data['sizes_list'][0].find_all('li', {'class': 'check_item'})
            data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
            data['sizes_list'].pop(0)
            data['sizes_list'].pop(-1)
            data['small_sizes'] = soup.find('ul', attrs={'id': 'size-interval-tabs'}).findAll('li')
            if data['small_sizes'][0]['data-url'] != '' and len(data['small_sizes']) > 1:
                data['small_sizes'] = 'https://wisell.ru' + data['small_sizes'][0]['data-url']
                r = requests.get(data['small_sizes'])
                soup = BeautifulSoup(r.text, 'lxml')
                small_name = soup.find('li', attrs={'class': 'item_lost'})
                if small_name.span.text != data['name']:
                    data['name'] = data['name'] + ' ' + small_name.span.text
                    small_sizes_list = soup.find_all('ul', {'class': 'size_list'})
                    small_sizes_list = small_sizes_list[0].find_all('li', {'class': 'check_item'})
                    small_sizes_list = [size.text.strip() for size in small_sizes_list]
                    small_sizes_list.pop(0)
                    small_sizes_list.pop(-1)
                    for size in small_sizes_list:
                        if size not in data['sizes_list'] and int(size) > 46:
                            data['sizes_list'].append(size)
                print(data['name'], data['sizes_list'], data['price'])
                result.append(['Визель ' + data['name'], data['sizes_list'], data['price']])
            elif len(data['small_sizes']) == 1:
                sizes_list = []
                for size in data['sizes_list']:
                    if int(size) > 46:
                        sizes_list.append(size)
                if len(sizes_list) != 0:
                    print(data['name'], sizes_list, data['price'])
                    result.append(['Визель ' + data['name'], sizes_list, data['price']])
            # print(['Визель ' + data['name'], data['sizes_list'], data['price']])
        #     time.sleep(0.1)
        #     i += 1
        #     printProgressBar(i, l, prefix='Wisell Parsing:',
        #                      suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        # j += 1
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
    last_page = int(re.search(r'(?<=page/)(\d+)', data['paginaton_url'].pop(-1)).group(0))
    pagination_link = url + 'page/'
    data['paginaton_url'] = [pagination_link + str(link) for link in range(2, last_page + 1)]
    data['paginaton_url'].insert(0, url)
    j = 1
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
            data['name'] = soup.find('span', {'class': 'sku'}).text
            data['price'] = soup.find('meta', {'itemprop': 'price'})
            data['price'] = data['price']['content']
            data['sizes_list'] = soup.find('div', {'class': 'ivpa_attribute'}, {'class': 'ivpa_text'})
            data['sizes_list'] = data['sizes_list'].find_all('span', {'class': 'ivpa_term'})
            data['sizes_list'] = [item.text.strip() for item in data['sizes_list']]
            # print(data['name'], data['sizes_list'], data['price'])
            result.append([data['name'], data['sizes_list'], data['price']])
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Bigmoda Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
    return result


def compare_dress(parse_list, bigmoda_dresses, bigmoda_exc):
    # TODO не работает удалить добавить карточку
    '''
    Compare avaliability supplier and site customer
    :param parse_list: list
    :param bigmoda_dresses: list
    :param bigmoda_exc: list
    :return: boolean
    '''
    for dress in parse_list:
        if dress not in bigmoda_exc:
            for bm_drs in bigmoda_dresses:
                bm_name = bm_drs[0].split(' ')
                if (len(bm_name) > 2) and ('Новита' not in bm_name[0]) and (dress[0] == bm_name[1]):
                    size_to_add = []
                    for bm_drs2 in parse_list:
                        if bm_drs2[0] == bm_name[2]:
                            for size in bm_drs2[1]:
                                if (size not in bm_drs[1]) and (int(size) > 46):
                                    size_to_add.append(size)
                    for size in dress[1]:
                        if size not in bm_drs[1]:
                            size_to_add.append(size)
                    if len(size_to_add) != 0:
                        with open('res.txt', 'a', encoding='utf-8') as file:
                            file.write('Добавить размеры: {}, {}, {}\n'.format(dress[0], size_to_add, dress[2]))
                    size_to_del = []
                    for drs in parse_list:
                        if drs[0] == bm_name[1]:
                            for size in bm_drs[1]:
                                for drs2 in parse_list:
                                    if drs2[0] == bm_name[2] and size not in drs[1] and size not in drs2[1]:
                                        size_to_del.append(size)
                    if len(size_to_del) != 0:
                        with open('res.txt', 'a', encoding='utf-8') as file:
                            file.write('Удалить размеры: {}, {}, {}\n'.format(dress[0], size_to_del, dress[2]))
                else:
                    if dress[0] == bm_drs[0]:
                        size_to_add = []
                        for size in dress[1]:
                            if size not in bm_drs[1]:
                                size_to_add.append(size)
                        if len(size_to_add) != 0:
                            with open('res.txt', 'a', encoding='utf-8') as file:
                                file.write('Добавить размеры: {}, {}, {}\n'.format(dress[0], size_to_add, dress[2]))
                        size_to_del = []
                        for size in bm_drs[1]:
                            if size not in dress[1]:
                                size_to_del.append(size)
                        if len(size_to_del) != 0:
                            with open('res.txt', 'a', encoding='utf-8') as file:
                                file.write('Удалить размеры: {}, {}, {}\n'.format(dress[0], size_to_del, dress[2]))
    # for cmp in bigmoda_dresses:
    #     cmp_name = cmp[0].split(' ')
    #     if len(cmp_name) > 1:
    #         if cmp[0] not in parse_list[0]:
    #             with open('res.txt', 'a', encoding='utf-8') as file:
    #                 file.write('Добавить карточку: {}, {}, {}\n'.format(cmp[0], cmp[1], cmp[2]))
    #     elif (len(bm_name) > 2) and ('Новита' not in cmp_name[0]):
    #         if 'Визель ' + cmp_name[1] not in parse_list[0]:
    #             with open('res.txt', 'a', encoding='utf-8') as file:
    #                 file.write('Добавить карточку: {}, {}, {}\n'.format(cmp[0], cmp[1], cmp[2]))
    return True


def del_item(goods_data):
    names = [i[0] for i in goods_data]
    bm_names = [i[0] for i in bigmoda_dresses]
    for bm_dress in bigmoda_dresses:
            if bm_dress[0] not in names:
                if 'Визель' in bm_dress[0]:
                    bm_name = bm_dress[0].split(' ')
                    if bm_name[1] not in names:
                        with open('res.txt', 'a', encoding='utf-8') as file:
                            file.write('Удалить карточку: {}\n'.format(bm_dress[0]))
                with open('res.txt', 'a', encoding='utf-8') as file:
                    file.write('Удалить карточку: {}\n'.format(bm_dress[0]))
    for name in goods_data:
        goods_name = name[0].split(' ')
        if len(goods_name) == 1:
            if name[0] not in bm_names:
                print(name[0])
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
    files = ['res.txt', 'delete.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    # novita_dresses = novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
    # with open('novita.txt', 'w', encoding='utf-8') as file:
    #     file.write(str(novita_dresses))
    # primalinea_dresses = primalinea_parse('http://primalinea.ru/catalog/category/42/all/0')
    # avigal_dresses = avigal_parse('http://avigal.ru/dress/')
    wisell_dresses = wisell_parse('https://wisell.ru/catalog/platya/')
    # with open('wisell.txt', 'w', encoding='utf-8') as file:
    #     file.write(str(wisell_dresses))
    # novita_blouse = novita_parse('http://novita-nsk.ru/shop/bluzy/')
    # primalinea_blouse = primalinea_parse('http://primalinea.ru/catalog/category/43/all/0')
    # avigal_blouse = avigal_parse('http://avigal.ru/blouse-tunic/')
    # wisell_blouse = wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')
    # bigmoda_dresses = bigmoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/')
    # with open('bigmoda.txt', 'w', encoding='utf-8') as file:
    #     file.write(str(bigmoda_dresses))
    bigmoda_dresses = [['Краса П-0083', ['52', '54', '56', '58', '60', '62', '64', '66'], '2500'], ['Краса П-0072', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-647', ['50', '52', '54', '56', '58', '60', '62', '64'], '2700'], ['Новита 578 васильковый', ['48', '50', '52', '54', '56', '58'], '3000'], ['Визель П4-3192/3 П4-3192/2', ['48', '50', '52', '54', '56', '58', '60', '62'], '3200'], ['Визель П3-2596/3 П3-2596/2', ['48', '50', '52', '54', '56', '58', '60', '62'], '2800'], ['Новита 575 васильковый', ['50', '52', '54', '56', '58'], '3000'], ['Новита 605 город', ['48', '50', '52', '54', '56', '58'], '3200'], ['Новита 618 сине-желтый', ['48', '50', '52', '54', '56'], '2800'], ['Краса П-0088', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-445', ['52', '60', '64', '66', '68', '70'], '2900'], ['Визель П4-3605/1 П4-3605', ['52', '56', '60'], '3600'], ['Новита 581 синие цветы', ['50', '52', '54', '56'], '3300'], ['Визель П4-2571/3 П4-2571/2', ['48', '50', '52', '54', '56', '58', '60'], '4000'], ['Краса П-0093', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600'], ['Авигаль П-164-1', ['54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600'], ['Авигаль П-229-3', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500'], ['Прима 4117', ['50', '52', '54'], '3200'], ['Новита 408/1 цветы', ['50', '52', '54', '56', '58'], '2600'], ['Новита 456/1 кофейный', ['50', '52', '54', '56', '58'], '3100'], ['Авигаль П-458-1', ['54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-458', ['54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-164', ['54', '68', '70'], '2600'], ['Авигаль П-501-2', ['52', '54', '56', '58', '60'], '2600'], ['Авигаль П-501-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600'], ['Авигаль П-501', ['56', '58', '60', '62'], '2600'], ['Авигаль П-011-1', ['54', '56', '58', '60', '62', '64', '66'], '3300'], ['Визель П3-3584/3 П3-3584/2', ['48', '50', '52', '54', '56', '58', '60'], '3000'], ['Визель П3-3576/5 П3-3576/4', ['48', '50', '52', '54', '56', '58', '60', '62'], '3000'], ['Прима 4050', ['46', '48', '50', '52', '54', '56', '58', '60'], '1900'], ['Новита 462 розовые цветы', ['48', '50', '52', '54', '56'], '3000'], ['Новита 592 ромашки', ['48', '50', '52', '54', '56'], '2800'], ['Новита 610 зеленый', ['48', '50', '52', '54', '56'], '2800'], ['Новита 593 св. бежевый', ['52', '54', '56', '58'], '3100'], ['Новита 444/1 синие цветы', ['48', '50', '52', '54', '56'], '3100'], ['Новита 599 мятный', ['50', '52', '54', '56'], '3300'], ['Авигаль П-044-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2600'], ['Авигаль П-044', ['54', '56', '58', '60', '62', '70'], '2600'], ['Визель П2-3610/1 П2-3610', ['48', '50', '52', '54', '56', '58', '60'], '3400'], ['Новита 592 розы фуксия', ['48', '50', '52', '54', '56'], '2800'], ['Прима 2754-2', ['52', '54', '56', '58'], '4400'], ['Визель П4-3556/3 П4-3556/2', ['48', '50', '52', '54', '56', '58'], '3600'], ['Новита 594 фуксия', ['48', '50', '52', '54', '56'], '3200'], ['Краса П-0053', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Визель П2-3610/3 П2-3610/2', ['48', '50', '52', '54', '56', '58', '60'], '3400'], ['Визель П3-3607/1 П3-3607', ['48', '50', '52', '54', '56', '58', '60'], '4000'], ['Авигаль П-704-3', ['52', '54', '56', '58', '60', '62', '64', '66'], '2900'], ['Новита 608 бежевый', ['46', '48', '50', '54', '56'], '3000'], ['Визель П3-3292/2', ['52', '54', '56', '58', '60'], '4000'], ['Визель\xa0П3-3598/1 П3-3598', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Авигаль П-464', ['52', '54', '56'], '3750'], ['Авигаль П-464-1', ['52', '54', '56', '58', '60'], '3750'], ['Авигаль П-084-1', ['50', '54'], '2700'], ['Новита 591 цветы на сером', ['50', '52', '54', '56', '58'], '2600'], ['Визель П3-3232', ['52', '54', '56', '60'], '3400'], ['Визель П5-3347/2 П5-3347', ['46', '48', '52', '54', '56', '58', '60'], '4400'], ['Новита 576 коралловый', ['48', '50', '52', '54', '56'], '3000'], ['Авигаль П-982', ['56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500'], ['Новита 567 синий орнамент', ['48', '50', '52', '54', '56'], '3300'], ['Визель П2-3311/3 П2-3311/2', ['52', '54', '56', '58'], '3800'], ['Визель П3-3585/1 П3-3585', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Новита 562 серо-зеленый', ['50', '52', '54'], '3300'], ['Новита 538 дымчато-розовый', ['50', '52', '54', '56'], '3000'], ['Авигаль П-307', ['54', '58', '60', '62', '64'], '3600'], ['Визель П3-3232/1', ['52', '54', '56', '58'], '3400'], ['Новита 407 синий', ['50', '52', '54', '56', '60'], '3100'], ['Авигаль П-084', ['50', '52'], '2700'], ['Визель П3-3331/2', ['46', '48', '50', '52'], '4200'], ['Визель П4-3538/5 П4-3538/4', ['48', '50', '52', '54', '56', '58', '60'], '4600'], ['Новита 548 электрик', ['48', '50', '52', '54', '56'], '3200'], ['Новита 493/1 серый', ['52', '54', '56', '58'], '3500'], ['Новита 530 розовая пудра', ['52', '56'], '3300'], ['Авигаль П-229-2', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500'], ['Визель П3-3603/1 П3-3603', ['48', '50', '52'], '3800'], ['Визель П4-2571/15 П4-2571/14', ['48', '50', '52', '54', '56', '58', '60'], '4400'], ['Новита 486 капучино', ['50', '52', '54', '56', '58'], '3000'], ['Прима 2956', ['48', '50', '52', '54', '56', '58', '60', '62'], '3580'], ['Новита 522 шоколад', ['50', '54', '56', '60'], '3000'], ['Новита 565 серо-розовый', ['50', '52', '54', '56'], '3400'], ['Новита 554 белая клетка', ['48', '50', '54', '58'], '3200'], ['Новита 429 горчичный', ['50', '52', '54', '56'], '3100'], ['Новита 343 антрацит', ['48', '50', '52', '54', '56'], '3200'], ['Прима 2915', ['50', '52', '54', '56'], '3600'], ['Визель П5-3506/1', ['52', '54', '56', '58', '60'], '4000'], ['Визель П3-2337/6 П3-2337/5', ['50', '52', '54', '56', '58', '60'], '4200'], ['Краса П-0039', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-450', ['56', '60'], '2500'], ['Визель П3-3465/3 П3-3465/2', ['48', '50', '52', '54', '56', '60'], '4400'], ['Прима 2960', ['50', '52', '54', '56', '58', '60', '62', '64'], '3840'], ['Новита 534 темно-розовый', ['50', '52', '54', '56', '58', '60'], '3400'], ['Визель П4-3371/16 П4-3371/15', ['48', '50', '52', '54', '56', '58'], '3600'], ['Визель П3-3468/4', ['54'], '2000'], ['Новита 617 полоска', ['46', '48', '50', '52', '54', '56'], '2700'], ['Авигаль П-229', ['54', '56', '60', '64', '66', '68', '70', '72', '74'], '2200'], ['Краса П-0063', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0076', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0074', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Новита 597 мятный', ['48', '50', '52', '54', '56'], '2700'], ['Новита 418 т. синий', ['48', '50', '52', '54', '56'], '3100'], ['Визель П3-3293', ['54', '56'], '4000'], ['Визель П4-3539/3 П4-3539/2', ['48', '50', '52', '54', '56', '58'], '5000'], ['Новита 558 горчичный', ['48', '50', '52'], '3100'], ['Прима 2944', ['48', '50', '52', '54', '56', '58', '62', '64'], '4400'], ['Прима 2939', ['48', '50', '52', '54', '56', '58', '60', '62'], '3520'], ['Визель П3-2337/4 П3-2337/3', ['48', '50', '52', '54', '56', '58', '60'], '4200'], ['Новита 527 синий', ['50', '52', '54', '56', '58'], '3200'], ['Новита 520 клетка', ['48', '50', '52', '54', '56', '58'], '3100'], ['Визель П3-3479/1 П3-3479', ['50', '52', '54', '56'], '4200'], ['Новита 510', ['50', '52', '54', '56', '58'], '3300'], ['Новита 506', ['48', '50', '52', '54', '56'], '3000'], ['Новита 492', ['50'], '2000'], ['ЕО-27018-1', ['52'], '2000'], ['Авигаль П-647-1', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2700'], ['Авигаль П-104-2', ['54', '56', '60', '66', '68'], '2600'], ['Авигаль П-104-1', ['56', '58', '66'], '2600'], ['Авигаль П-611-1', ['54', '56', '58', '60'], '2500'], ['Авигаль П-611', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2500'], ['Прима 4115', ['60', '62', '64', '66', '68', '70'], '3600'], ['Авигаль П-467-1', ['52', '54', '56', '58', '60', '62', '64'], '3200'], ['Новита 619 зеленая клетка', ['48', '50', '52', '54', '56'], '2800'], ['Новита 449/2 цветы на синем', ['50', '52', '54', '56'], '2900'], ['Авигаль П-062', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700'], ['Визель П3-3623/1 П3-3623', ['48', '50', '52', '54', '56', '58', '60'], '3400'], ['Краса П-0089', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса ПБ-0012', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-305-3', ['50', '54', '64', '66', '68'], '2500'], ['Авигаль П-305-2', ['54', '56', '60', '62', '64', '66', '68'], '2500'], ['Краса П-0042', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0055', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-446', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600'], ['Новита 596 кофейное', ['48', '50', '52'], '3400'], ['Новита 596 белое', ['48', '50', '52', '56'], '3400'], ['Визель\xa0П3-3598/3 П3-3598/2', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Новита 594 лимонный', ['48', '50', '52', '54', '56', '58'], '3200'], ['Авигаль П-497', ['50', '52', '60'], '3360'], ['Авигаль П-326-1', ['52', '54', '56', '60', '62'], '2500'], ['Авигаль П-327-1', ['52', '54', '56'], '2200'], ['Авигаль П-483-3', ['52', '54', '56', '62'], '2400'], ['Визель П3-3586/1 П3-3586', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Авигаль П-495-1', ['50', '52', '58'], '2500'], ['Авигаль П-702-1', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2400'], ['Авигаль П-400', ['50', '54', '60', '64'], '2400'], ['Авигаль П-706', ['52', '54', '70', '72'], '2900'], ['Новита 577 бирюзовый', ['48', '50', '52', '54', '56', '58'], '3000'], ['Авигаль П-488', ['52', '54', '56', '58', '66'], '2700'], ['Визель П3-3571/3 П3-3571/2', ['52', '54', '56', '58', '60'], '4400'], ['Визель П4-2571/13 П4-2571/12', ['48', '50', '52', '54', '56', '58', '60'], '4200'], ['Визель П3-3567/1 П3-3567', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П4-3561/1 П4-3561', ['52', '56', '60'], '3200'], ['Новита 574 бежевый орнамент', ['46', '48', '50', '52', '54', '56'], '2900'], ['Новита 564 черный', ['48', '50', '52', '54', '56'], '3300'], ['Прима 2964', ['54', '64'], '3560'], ['Новита 560', ['44', '46', '48', '50', '52', '54', '56'], '2800'], ['Визель П4-3538/1 П4-3538', ['48', '50', '52', '54', '56', '58', '60'], '4600'], ['Новита 326/1 синие розы', ['48', '50', '52', '54', '56'], '3000'], ['Новита 309 графитовый', ['46', '48', '50', '52', '56'], '3200'], ['Новита 518 синий орнамент', ['50', '52', '58'], '3200'], ['Новита 531 изумрудный', ['48', '50', '52', '54', '56', '58'], '3100'], ['Новита 542 бордовый', ['48', '50', '54', '56', '58'], '3200'], ['Прима 2875', ['52', '54', '58', '62', '64', '66', '68', '70'], '4400'], ['Прима 2876', ['52', '56', '58', '60', '62'], '4200'], ['Прима 2961', ['52', '54', '56', '58', '60', '62', '64', '66'], '3840'], ['Прима 2925', ['48', '50', '52'], '3240'], ['Новита 528 сиреневый', ['54', '56', '58'], '3300'], ['Со-ЮНОНА ПРИНТ НА ЧЕРНОМ', ['60'], '2600'], ['Новита 242 шоколад', ['58', '60', '62'], '3200'], ['Новита 393В серо-коричневый', ['56'], '2000'], ['Олеся-24019-1', ['56'], '2000'], ['Новита 441', ['48', '50', '52', '54', '56'], '3100'], ['Новита 503', ['48', '50', '52', '54', '56'], '3000'], ['Олеся-27026-1', ['50', '52'], '2000'], ['Джетти-Б005-1', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66'], '0'], ['ЕО-27014-1', ['50'], '2000'], ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '2000'], ['Авигаль П-980-3', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2900'], ['Авигаль П-980-2', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2900'], ['Авигаль П-980-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2900'], ['Авигаль П-980', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2900'], ['Новита 612 сине-бирюзовый', ['46', '48', '54'], '3100'], ['Новита 613 белый', ['48', '50'], '2800'], ['Новита 613 бежевый', ['48', '50', '52', '54', '56'], '2800'], ['Новита 624 цветы на синем', ['48', '50', '52', '54', '56'], '3400'], ['Новита 624 цветы на голубом', ['48', '50', '52', '54', '56'], '3400'], ['Визель П3-3586/3 П3-3586/2', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Визель П3-3643/1 П3-3643', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П4-3227/7 П4-3227/6', ['48', '50', '52', '54', '56', '58', '60', '62'], '3000'], ['Визель П3-2596/5 П3-2596/4', ['48', '50', '52', '54', '56', '58', '60', '62'], '2800'], ['Новита 625 терракотовый', ['48', '50', '52', '54', '56'], '3400'], ['Авигаль П-905-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700'], ['Авигаль П-905', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700'], ['Авигаль П-104-4', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600'], ['Авигаль П-104-3', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600'], ['Новита 607 зеленый', ['50', '52', '54', '56'], '2800'], ['Прима 4130', ['48', '50', '52', '54', '68', '70', '72'], '4200'], ['Прима 4129', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '4200'], ['Прима 4140', ['64', '66'], '4400'], ['Прима 4139', ['48', '50', '56', '58', '60', '62', '64', '66'], '4400'], ['Прима 4116', ['64', '66', '68', '70'], '4400'], ['Прима 4103', ['68', '70', '72', '74'], '4400'], ['Прима 4108', ['68', '70', '72'], '4400'], ['Прима 4098', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2400'], ['Прима 4096', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '72', '74'], '2400'], ['Новита 606 красный', ['48', '50', '52', '54'], '3000'], ['Новита 606 фиолетовый', ['48', '50', '54'], '3000'], ['Новита 622 орнамент на синем', ['48', '50', '52', '54', '56'], '2900'], ['Новита 614 серые цветы', ['50', '52', '54', '56', '58'], '3100'], ['Новита 620 горох на синем', ['48', '50', '52', '54', '56'], '3000'], ['Прима 4084', ['54', '56', '58', '60', '62', '64', '66'], '3000'], ['Прима 4085', ['54', '56', '58', '60', '62', '64', '66'], '3000'], ['Прима 4086', ['48', '54'], '3000'], ['Прима 4021', ['54', '58', '60', '62'], '4400'], ['Прима 4020', ['52', '60', '62'], '4400'], ['Авигаль П-011', ['54', '56', '58', '60', '62', '64', '66'], '3300'], ['Визель П3-3630/3 П3-3630/2', ['56', '58', '60', '62'], '3400'], ['Визель П3-3630/1 П3-3630', ['48', '50', '52', '54', '56', '58', '60', '62'], '3400'], ['Визель П3-3640/1 П3-3640', ['48', '50', '52', '54', '56', '58', '60'], '4200'], ['Визель П3-3195/2 П3-3195/1', ['48', '50', '52', '54', '56', '58', '60'], '4200'], ['Визель П4-3635/1 П4-3635', ['48', '50', '52', '54', '56', '58', '60', '62'], '3400'], ['Визель П4-3637/3 П4-3637/2', ['48', '50', '52', '54', '56', '60'], '4400'], ['Визель П4-3638/3 П4-3638/2', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Визель П4-3638/1 П4-3638', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Прима 4052', ['46', '48', '50', '52', '54', '56'], '2580'], ['Авигаль П-467', ['52', '54', '56', '58', '60', '62'], '3200'], ['Новита 602 шляпки', ['48', '50', '52', '54', '56'], '2600'], ['Новита 578 красный', ['48', '50', '52', '54', '56'], '3000'], ['Новита 455/1 синие цветы', ['48', '50', '52', '54', '56'], '3000'], ['Новита 595 полоска', ['48', '50', '52', '54'], '2900'], ['Новита 375 бежевый орнамент', ['50', '52', '54', '58', '60'], '2900'], ['Авигаль П-062-1', ['52', '54', '56', '58', '60', '64', '66', '68'], '2700'], ['Авигаль П-548-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700'], ['Авигаль П-548', ['52', '54', '60', '62', '66'], '3700'], ['Визель П3-3620/1 П3-3620', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Краса П-0085', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0086', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0087', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Визель\xa0П3-3616/3 П3-3616/2', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П3-3616/1 П3-3616', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П2-3617/5 П2-3617/4', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П2-3617/3 П2-3617/2', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Визель П2-3617/1 П2-3617', ['48', '50', '52', '54', '56', '58', '60'], '3600'], ['Краса ПБ-0010', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса ПБ-0011', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса ПБ-0016', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400'], ['Краса ПБ-0017', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400'], ['Новита 600 мятный', ['48', '50', '52', '54', '56'], '3300'], ['Новита 600 голубой', ['48', '50', '52', '54', '56'], '3300'], ['Новита 583 кремово-розовый', ['50', '52', '54', '56'], '3200'], ['Авигаль П-229-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2200'], ['Краса ПБ-0020', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса ПБ-0024', ['56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-305-1', ['54', '56', '58', '60'], '2500'], ['Авигаль П-305', ['54', '56', '58', '60', '62', '64', '66', '68'], '2500'], ['Краса П-0035', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0033', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0037', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Авигаль П-445-1', ['52', '54', '56', '64', '68', '70'], '2900'], ['Краса П-0049', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0060', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0052', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0061', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0050', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0057', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Краса П-0064', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400'], ['Краса П-0078', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400'], ['Визель П3-3615/1', ['52', '54', '56', '58', '60'], '3600'], ['Визель П2-3609/1 П2-3609', ['52', '54', '56', '58'], '3400'], ['Визель П3-3240 П3-3240/1', ['48', '50', '52', '54', '56', '58'], '3600'], ['Авигаль П-704', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2900'], ['Новита 461 зеленый', ['48', '50', '52'], '3100'], ['Визель П3-3596/3 П3-3596/2', ['48', '50', '52', '54', '56', '58', '60'], '4000'], ['Визель П3-3479/5 П3-3479/4', ['48', '50', '52', '54', '56', '58', '60'], '4400'], ['Визель П3-3479/3 П3-3479/2', ['48', '50', '52', '54', '56', '58', '60'], '4400'], ['Авигаль П-409-1', ['52', '54'], '3360'], ['Авигаль П 127', ['52', '54', '56'], '2600'], ['Прима 4035', ['48', '54'], '3780'], ['Новита 589 зеленый', ['48', '50', '52', '54', '56'], '3000'], ['Новита 588 желтый', ['48', '50', '52', '54', '56', '58'], '3200'], ['Новита 587 дымчато-сиреневый', ['48', '50', '52', '54', '56', '58'], '3200'], ['Новита 581 белые цветы', ['50', '52', '54', '56'], '3300'], ['Авигаль П-506-2', ['54', '56', '58', '60', '62', '64', '66'], '2900'], ['Авигаль П-700-1', ['54', '56', '58', '64', '66'], '3700'], ['Визель П4-3350/2 П4-3350', ['48', '50', '52', '54', '56'], '4200'], ['Авигаль П-264-1', ['56', '58', '60', '62', '64', '66'], '3300'], ['Авигаль П-264-2', ['50', '52', '54', '56', '58', '60', '62', '64', '66'], '3300'], ['Авигаль П-264-3', ['58', '62', '64', '66'], '3300'], ['Авигаль П-871-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700'], ['Авигаль П-871', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700'], ['Авигаль П-867-1', ['52', '54', '56', '58', '60', '62', '64'], '3200'], ['Авигаль П-867', ['52', '54', '56', '58', '60', '62', '64'], '3200'], ['Авигаль П-893-1', ['50', '52', '54', '56', '58', '60', '62'], '3300'], ['Авигаль П-893', ['50', '52', '54', '56', '58', '60', '62'], '3300'], ['Авигаль П-709', ['52', '54', '62', '64', '66', '68'], '2200'], ['Визель П3-3584/1 П3-3584', ['48', '50', '52', '54', '60'], '3000'], ['Визель П3-3585/3 П3-3585/2', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Авигаль П-705', ['52', '54', '56', '60'], '2200'], ['Авигаль П-705-1', ['52', '54', '56', '58', '60', '62'], '2200'], ['Авигаль П-869-2', ['50', '52', '54', '60', '62'], '2900'], ['Авигаль П-869-1', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900'], ['Авигаль П-869', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900'], ['Авигаль П-702', ['52', '54', '56', '58', '60', '62'], '2400'], ['Авигаль П-270-3', ['52', '54'], '2500'], ['Авигаль П-270', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500'], ['Авигаль П-270-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500'], ['Новита 590 цветная абстракция', ['48', '50', '52', '54', '56'], '3200'], ['Новита 584 мятный', ['48', '50', '52', '54', '56'], '2580'], ['Новита 582 синий орнамент', ['48', '52', '54', '56'], '3100'], ['Авигаль П-706-3', ['52', '56', '72', '74'], '2900'], ['Авигаль П-706-1', ['52', '54', '56', '58', '60', '62', '64', '68', '70', '72', '74'], '2900'], ['Авигаль П-706-2', ['54', '56', '66', '72'], '2900'], ['Авигаль П-503', ['50', '52', '54', '56', '58', '60', '62', '64'], '2960'], ['Новита 579 полоска', ['48', '50', '52', '54', '56'], '3100'], ['Авигаль П-503-1', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66'], '2960'], ['Авигаль П-100-1', ['52', '54', '56', '58', '60', '62', '64'], '2500'], ['Авигаль П-100', ['52', '54', '56', '58', '60', '62', '64'], '2500'], ['Авигаль П-488-1', ['52', '54', '58', '60', '62', '66'], '2700'], ['Авигаль П-100-1', ['52', '54', '56', '58', '60', '62', '64'], '2500'], ['Авигаль П-100', ['52', '54', '56', '58', '60', '62', '64'], '2500'], ['Авигаль П-488-1', ['52', '54', '58', '60', '62', '66'], '2700'], ['Прима 2754-4', ['52', '54', '56', '58', '60', '62', '64'], '4400'], ['Прима 2856', ['56', '58', '64', '68'], '3400'], ['Прима 4018', ['52', '54', '56', '58', '60', '62', '64'], '3200'], ['Прима 4001', ['44', '46', '48', '50', '52'], '5800'], ['Новита 566', ['50', '52', '54', '56'], '3100'], ['Визель П4-2571/9 П4-2571/8', ['48', '50', '52', '54', '56', '58', '60'], '4200'], ['Визель П4-2571/11 П4-2571/10', ['48', '50', '52', '54', '58'], '4200'], ['Визель П5-3506/8 П5-3506/7', ['50', '52', '54', '56', '58', '60'], '3800'], ['Визель П5-3506/6 П5-3506/5', ['48', '50', '52', '54', '56', '58', '60'], '3800'], ['Визель П5-3506/4', ['54', '56', '58', '60'], '3800'], ['Визель П5-3506/10 П5-3506/9', ['52', '56', '58'], '3800'], ['Новита 573 терракотовый', ['48', '50', '56'], '3200'], ['Новита 569 коричневый', ['48', '50', '52', '54', '56'], '3000'], ['Прима 2982', ['56', '58'], '3520'], ['Визель П4-2571/5 П4-2571/4', ['48', '50', '52', '54', '56', '58', '60'], '4000'], ['Новита 556 цветы на мятном', ['50', '52', '54', '56'], '3100'], ['Прима 2662', ['46', '48', '50', '54', '56'], '4200'], ['Прима 2977', ['48', '50', '52', '54', '56', '58'], '3580'], ['Новита 355/1 морская волна', ['46', '48', '52', '56'], '3100'], ['Новита 355/1 розовая пудра', ['46', '50'], '3100'], ['Прима 2874', ['54', '56', '60', '62', '64', '66', '68', '70'], '4400'], ['Прима 2877', ['54', '56', '58', '62'], '4200'], ['Новита 550 розы', ['48', '50', '52', '54', '56'], '3100'], ['Прима 2906', ['44', '46', '54', '56', '58', '62', '64'], '3200'], ['Прима 2898', ['48', '50', '52', '54', '62'], '3600'], ['Прима 2935', ['48', '50', '52', '54', '56', '58'], '3640'], ['Новита 526 синий', ['44', '46', '48', '50'], '2800'], ['Новита 321 алый', ['48', '50', '54', '56'], '2000'], ['Новита 519 черный', ['48', '50'], '3100'], ['Новита 529 золотой узор', ['50', '52', '54', '56'], '3100'], ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '2000'], ['Визель П2-3477/1', ['52', '54', '58'], '3800'], ['Визель П4-3469/1', ['56'], '2000'], ['Новита 516 какао', ['50', '52', '54', '56', '58'], '3100'], ['Новита 334', ['48', '50', '52', '54', '56', '58'], '3200'], ['Новита 345/1', ['48', '50', '52', '54', '56'], '3000'], ['Новита 496', ['50', '52', '54', '56', '58'], '3200'], ['Новита 509', ['50'], '2000'], ['Новита 511', ['50', '52', '54', '56'], '3200'], ['Олеся-28001-1', ['54', '56'], '2000'], ['Новита 408', ['50', '58'], '3000'], ['Джетти Б092-2', ['54'], '2000'], ['Джетти-Б092-4', ['54'], '2000'], ['Джетти Б163-4', ['58'], '2000'], ['Со-СЕВАСТЬЯНА оригами', ['52'], '2000'], ['ЕО-24042-1', ['54'], '2000'], ['JБ-Б165-1', ['56'], '2000'], ['JБ-Б201-2', ['60'], '2000']]
    # bigmoda_blouse = bigmoda_parse('https://big-moda.com/product-category/bluzki-bolshih-razmerov/')
    # bigmoda_exc = bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')
    # with open('bigmoda_exc.txt', 'w', encoding='utf-8') as file:
    #     file.write(str(bigmoda_exc))
    bigmoda_exc = [['Визель П3-3468/4', ['54'], '2000'], ['Новита 492', ['50'], '2000'], ['ЕО-27018-1', ['52'], '2000'], ['Новита 242 шоколад', ['54', '56', '58', '60', '62'], '3200'], ['Новита 393В серо-коричневый', ['56'], '2000'], ['Олеся-24019-1', ['56'], '2000'], ['Олеся-27026-1', ['50', '52'], '2000'], ['Джетти-Б005-1', ['48', '50', '56'], '0'], ['ЕО-27014-1', ['50'], '2000'], ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '2000'], ['Новита 321 алый', ['48', '50', '54', '56'], '2000'], ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '2000'], ['Визель П4-3469/1', ['56'], '2000'], ['Визель Др5-152/1', ['60'], '2000'], ['Визель Кн5-96/1', ['50'], '2000'], ['Новита 509', ['50'], '2000'], ['Олеся-28001-1', ['54', '56'], '2000'], ['Джетти Б092-2', ['54'], '2000'], ['Джетти-Б092-4', ['54'], '2000'], ['Джетти Б163-4', ['58'], '2000'], ['Со-СЕВАСТЬЯНА оригами', ['52'], '2000'], ['ЕО-24042-1', ['54'], '2000'], ['JБ-Б165-1', ['56'], '2000'], ['JБ-Б201-2', ['60'], '2000']]
    # compare_dress(novita_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(primalinea_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(avigal_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(wisell_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(novita_blouse, bigmoda_dresses, bigmoda_exc)
    # compare_dress(primalinea_blouse, bigmoda_dresses, bigmoda_exc)
    # compare_dress(avigal_blouse, bigmoda_dresses, bigmoda_exc)
    # compare_dress(wisell_blouse, bigmoda_dresses, bigmoda_exc)
    # goods_data = []
    # for dress in novita_dresses:
    #     goods_data.insert(-1, dress)
    # goods_data.insert(-1, novita_dresses)
    # goods_data.insert(-1, primalinea_dresses)
    # for dress in avigal_dresses:
    #     goods_data.insert(-1,dress )
    # for dress in wisell_dresses:
    #     goods_data.insert(-1, dress)
    # goods_data.insert(-1, novita_blouse)
    # goods_data.insert(-1, primalinea_blouse)
    # goods_data.insert(-1, avigal_blouse)
    # goods_data.insert(-1, wisell_blouse)
    # del_item(goods_data)