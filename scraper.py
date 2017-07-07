# -*- coding: utf-8 -*-
import requests
import os
import re
import time
import sys
import csv

import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

from bs4 import BeautifulSoup
from selenium import webdriver

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
        data['name'] = re.search(r'(?<=№)(\d+/\d+)|(?<=№)(\d+)', soup.h1.text.strip()).group(0)
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
                # print(data['name'], data['sizes_list'], data['price'])
                result.append(['Визель ' + data['name'], data['sizes_list'], data['price']])
            elif len(data['small_sizes']) == 1:
                sizes_list = []
                for size in data['sizes_list']:
                    if int(size) > 46:
                        sizes_list.append(size)
                if len(sizes_list) != 0:
                    # print(data['name'], sizes_list, data['price'])
                    result.append(['Визель ' + data['name'], sizes_list, data['price']])
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
            data['product_id'] = re.search(r'(\d+)', soup.find('div', attrs={'class': 'product'})['id']).group(0)
            sizes_id = re.findall(r'(?<="variation_id":)(\d+)',
                                  soup.find('div', attrs={'id': 'ivpa-content'})['data-variations'])

            sizes_key = re.findall(r'(?<="attribute_pa_size":)"(\d+)"',
                                   soup.find('div', attrs={'id': 'ivpa-content'})['data-variations'])
            data['product_size_id'] = dict(zip(sizes_key, sizes_id))
            # print([data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
            result.append(
                [data['name'], data['sizes_list'], data['price'], data['product_id'], data['product_size_id']])
            time.sleep(0.1)
            i += 1
            printProgressBar(i, l, prefix='Bigmoda Parsing:',
                             suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
        j += 1
    return result


def compare_dress(parse_list, bigmoda_dresses, bigmoda_exc, chromedriver):
    '''
    Compare avaliability sizes supplier and site customer
    :param parse_list: list
    :param bigmoda_dresses: list
    :param bigmoda_exc: list
    :param chromedriver: selenium driver
    :return: boolean
    '''
    for dress in parse_list:
        if dress not in bigmoda_exc:
            for bm_drs in bigmoda_dresses:
                if dress[0] == bm_drs[0]:
                    size_to_add = []
                    chromedriver.get('http://localhost/wp-admin/post.php?post=' + bm_drs[3] + '&action=edit')
                    time.sleep(1)
                    driver.find_element_by_xpath('//*[@id="woocommerce-product-data"]/div/div/ul/li[5]/a').click()
                    driver.find_element_by_xpath('//*[@id="product_attributes"]/div[2]/div[1]/h3').click()
                    time.sleep(1)
                    sizes_input = driver.find_element_by_name('attribute_values[0]')
                    len_sizes = str(sizes_input.get_attribute('value')).split('|')
                    len_sizes = [size.strip() for size in len_sizes]
                    attr = str(sizes_input.get_attribute('value'))
                    count = 0
                    for size in len_sizes:
                        if size not in bm_drs[1]:
                            attr = attr + ' | ' + size
                            count += 1
                    if count != 0:
                        for item in range(len(str(sizes_input.get_attribute('value')))):
                            sizes_input.send_keys('\b')
                        sizes_input.send_keys(attr)
                        driver.find_element_by_xpath('//*[@id="product_attributes"]/div[3]/button').click()
                    time.sleep(3)
                    for size in dress[1]:
                        if size not in bm_drs[1]:
                            size_to_add.append(size)
                            time.sleep(1)
                            driver.find_element_by_xpath(
                                '//*[@id="woocommerce-product-data"]/div/div/ul/li[6]/a').click()
                            time.sleep(3)
                            driver.find_element_by_xpath('//*[@id="variable_product_options_inner"]/div[2]/a').click()
                            time.sleep(2)
                            size_selects = driver.find_elements_by_xpath(
                                '//*[@id="variable_product_options_inner"]/div[3]/div')

                            for size_select in size_selects:
                                size_select = size_select.find_element_by_xpath('//select')
                                options_size_select = size_select.find_elements_by_tag_name('option')
                                for option in options_size_select:
                                    if option.get_attribute('selected') is None:
                                        if option.get_attribute('value') == size:
                                            option.click()
                            driver.find_element_by_xpath('//*[@id="variable_product_options_inner"]/div[4]/button[1]').click()
                            time.sleep(3)
                    if len(size_to_add) != 0:
                        with open('добавить удалить размеры.txt', 'a', encoding='utf-8') as file:
                            file.write('Добавить размеры: {}, {}, {}\n'.format(dress[0], size_to_add, dress[2]))
                    size_to_del = []
                    for size in bm_drs[1]:
                        if size not in dress[1]:
                            size_to_del.append(size)
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
                    # print(name, sizes_list, price)
                    result.append([name, sizes_list, price])
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
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_dress))
    for bm_blouse in bm_names_blouse:
        if bm_blouse not in names:
            with open('добавить удалить карточки.txt', 'a', encoding='utf-8') as file:
                file.write('Удалить карточку: {}\n'.format(bm_blouse))
    for name in goods_data:
        if (name not in bm_names_dress or name not in bm_names_blouse) and name not in bm_names_exc:
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
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get('http://localhost/wp-admin/')
    driver.set_page_load_timeout(30)
    driver.find_element_by_id('user_login').send_keys('olegsent')
    time.sleep(0.1)
    driver.find_element_by_id('user_pass').send_keys('dW#h$x*^EnGOpLhH')
    driver.find_element_by_id('wp-submit').click()


    dress_pages = [  # novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/'),
        # novita_parse('http://novita-nsk.ru/shop/aktsii/'),
        # novita_parse('http://novita-nsk.ru/index.php?route=product/category&path=1_19'),
        # novita_parse('http://novita-nsk.ru/shop/yubki/'),
        # primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'),
        # avigal_parse('http://avigal.ru/dress/'), wisell_parse('https://wisell.ru/catalog/platya/'),
        # krasa_parse('krasa.csv')
         ]
    # blouse_pages = [novita_parse('http://novita-nsk.ru/shop/bluzy/'),
    #                 primalinea_parse('http://primalinea.ru/catalog/category/43/all/0'),
    #                 avigal_parse('http://avigal.ru/blouse-tunic/'),
    #                 wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')]
    # bigmoda_pages = [bigmoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/'),
    #                  bigmoda_parse('https://big-moda.com/product-category/bluzki-bolshih-razmerov/'),
    #                  bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')]
    # bigmoda_pages = [bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'),
                     # bigmoda_parse('http://localhost/product-category/bluzki-bolshih-razmerov/'),
                     # bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/')]
    # print(bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'))
    # print(bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/'))

    goods_data = []
    for site in dress_pages:
        compare_dress(site, [['Краса 0083', ['52', '54', '56', '58', '60', '62', '64', '66'], '2500', '15542', {'60': '15551', '58': '15552', '66': '15548', '64': '15549', '52': '15555', '56': '15553', '62': '15550', '54': '15554'}], ['Краса П-0072', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13890', {'64': '13892', '54': '13897', '66': '13891', '60': '13894', '52': '13898', '56': '13896', '62': '13893', '58': '13895'}], ['Авигаль П-501-2', ['52', '54', '56', '58', '60', '62'], '2600', '15145', {'60': '15152', '54': '15147', '52': '15148', '56': '15146', '62': '15151', '58': '15153'}], ['Авигаль П-458-1', ['54', '56', '58', '60', '62', '64', '66'], '2400', '15738', {'60': '15739', '54': '15769', '66': '15744', '64': '15745', '56': '15743', '62': '15740', '58': '15741'}], ['Авигаль П-458', ['54', '56', '58', '60', '62', '64', '66'], '2400', '15727', {'60': '15731', '54': '15734', '66': '15728', '64': '15729', '56': '15733', '62': '15730', '58': '15732'}], ['Авигаль П-501', ['56', '58', '60', '62'], '2600', '15123', {'56': '15127', '60': '15125', '62': '15124', '58': '15126'}], ['Прима 4050', ['46', '48', '50', '52', '54', '56', '58', '60'], '1900', '14905', {'46': '14913', '60': '14906', '58': '14907', '50': '14911', '52': '14910', '56': '14908', '48': '14912', '54': '14909'}], ['Авигаль П-164-1', ['54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600', '15529', {'56': '15537', '64': '15533', '58': '15536', '66': '15532', '60': '15535', '68': '15531', '70': '15530', '62': '15534', '54': '15538'}], ['Авигаль П-164', ['54', '66', '68', '70'], '2600', '15516', {'66': '15519', '68': '15518', '70': '15517', '54': '15525'}], ['Авигаль П-011-1', ['54', '56', '58', '60', '62', '64', '66'], '3300', '15112', {'60': '15115', '54': '15118', '66': '15119', '64': '15113', '56': '15117', '62': '15114', '58': '15116'}], ['Визель П3-3584/3', ['48', '50', '52', '54', '56', '58', '60'], '3000', '15044', {'48': '15051', '60': '15045', '58': '15046', '50': '15050', '52': '15049', '56': '15047', '54': '15048'}], ['Визель П3-3576/5', ['48', '50', '52', '54', '56', '58', '60', '62'], '3000', '15015', {'48': '15023', '60': '15750', '54': '15020', '50': '15022', '52': '15021', '56': '15019', '62': '15016', '58': '15018'}], ['Новита 462 розовые цветы', ['48', '50', '52', '54', '56'], '3000', '14720', {'50': '14725', '52': '14724', '56': '14722', '54': '14723', '48': '14726'}], ['Краса П-0088', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14406', {'60': '14410', '58': '14411', '66': '14407', '64': '14408', '52': '14414', '56': '14412', '62': '14409', '54': '14413'}], ['Краса-0093', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600', '15556', {'60': '15560', '58': '15561', '66': '15557', '64': '15558', '52': '15564', '56': '15562', '62': '15559', '54': '15563'}], ['Авигаль П-229-3', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '14756', {'74': '14767', '58': '14758', '66': '14759', '72': '14765', '68': '14766', '56': '14757', '62': '14764', '60': '14761', '54': '14763', '64': '14762', '70': '14768', '52': '14760'}], ['Новита 408/1', ['50', '52', '54', '56', '58'], '2600', '12575', {'50': '12580', '52': '12579', '56': '12577', '58': '12576', '54': '12578'}], ['Новита 456/1', ['50', '52', '54', '56', '58'], '3100', '12098', {'50': '12103', '52': '12102', '56': '12100', '58': '12099', '54': '12101'}], ['Прима линия 4117', ['44', '46', '50', '52', '54', '56', '58', '60'], '3200', '15429', {'46': '15437', '60': '15430', '58': '15431', '50': '15435', '52': '15434', '56': '15432', '44': '15438', '54': '15433'}], ['Авигаль П-501-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '2600', '15130', {'60': '15138', '58': '15139', '66': '15135', '64': '15136', '52': '15142', '56': '15140', '62': '15137', '54': '15141'}], ['Новита 592 ромашки', ['48', '50', '52', '54', '56'], '2800', '14677', {'50': '14681', '52': '14680', '56': '14678', '54': '14679', '48': '14682'}], ['Новита 618', ['48', '50', '52', '54', '56'], '2800', '14643', {'50': '14647', '52': '14646', '56': '14644', '54': '14645', '48': '14648'}], ['Новита 610', ['48', '50', '52', '54', '56'], '2800', '14112', {'50': '14116', '52': '14115', '56': '14113', '54': '14114', '48': '14117'}], ['Новита 593', ['50', '52', '54', '56', '58', '60'], '3100', '12604', {'60': '12605', '58': '12606', '50': '12610', '52': '12609', '56': '12607', '54': '12608'}], ['Новита 444/1', ['48', '50', '52', '54', '56'], '3100', '12708', {'50': '12712', '52': '12711', '48': '12713', '56': '12709', '54': '12710'}], ['Новита 599', ['50', '52', '54', '56', '58'], '3300', '12662', {'50': '12667', '52': '12666', '56': '12664', '58': '12663', '54': '12665'}], ['Визель-П4-2571/3', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8758', {'48': '8765', '60': '12030', '54': '8762', '50': '8764', '52': '8763', '56': '8761', '58': '12029'}], ['Авигаль П-044-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2600', '15491', {'52': '15512', '56': '15510', '60': '15508', '54': '15511', '68': '15504', '66': '15505', '72': '15502', '64': '15506', '70': '15503', '62': '15507', '58': '15509'}], ['Новита 592', ['48', '50', '52', '54', '56'], '2800', '12064', {'50': '12068', '52': '12067', '56': '12065', '54': '12066', '48': '12069'}], ['Прима 2754-2', ['52', '54', '56', '58'], '4400', '10587', {'52': '10593', '56': '10591', '54': '10592', '58': '10590'}], ['Визель П4-3556/3', ['48', '50', '52', '54', '56', '58'], '3600', '9261', {'48': '12306', '54': '12303', '50': '12305', '52': '12304', '56': '12302', '58': '12301'}], ['Авигаль П-044', ['54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2600', '15476', {'70': '15478', '60': '15483', '58': '15484', '68': '15479', '66': '15480', '72': '15477', '64': '15481', '56': '15485', '62': '15482', '54': '15486'}], ['Прима линия 4104', ['66', '72', '74'], '4400', '15290', {'66': '15749', '72': '15292', '74': '15291'}], ['Новита 594 фуксия', ['48', '50', '52', '54', '56'], '3200', '14050', {'50': '14054', '52': '14053', '56': '14051', '54': '14052', '48': '14055'}], ['Краса П-0053', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13437', {'60': '13441', '58': '13442', '66': '13438', '64': '13439', '52': '13445', '56': '13443', '62': '13440', '54': '13444'}], ['Визель П2-3610/1', ['48', '50', '52', '54', '56'], '3400', '13138', {'50': '13144', '52': '13143', '48': '13145', '56': '13141', '54': '13142'}], ['Визель П2-3610/3', ['48', '50', '52', '54', '56', '58', '60'], '3400', '13123', {'48': '13130', '60': '13124', '58': '13125', '50': '13129', '52': '13128', '56': '13126', '54': '13127'}], ['Визель П3-3607/1', ['48', '50', '52', '54', '56', '58', '60'], '4000', '13068', {'48': '13076', '60': '15662', '54': '13073', '50': '13075', '52': '13074', '56': '13072', '58': '13071'}], ['Авигаль П-704-3', ['52', '54', '56', '58', '60', '62', '64', '66'], '2900', '12784', {'60': '12789', '54': '12792', '66': '12786', '64': '12787', '52': '12793', '56': '12791', '62': '12788', '58': '12790'}], ['Новита 608', ['46', '48', '50', '52', '54', '56'], '3000', '12647', {'46': '12653', '54': '12649', '50': '12651', '52': '12650', '56': '12648', '48': '12652'}], ['Новита 598/1', ['48', '50', '52'], '3400', '12636', {'50': '12640', '52': '12638', '48': '12641'}], ['Визель П3-3292/2', ['52', '54', '56', '58', '60'], '4000', '12494', {'52': '12499', '56': '12497', '60': '12495', '58': '12496', '54': '12498'}], ['Визель\xa0П3-3598/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '12479', {'48': '12486', '60': '12480', '58': '12481', '50': '12485', '52': '12484', '56': '12482', '54': '12483'}], ['Авигаль-П-464', ['52', '54', '56'], '3750', '12344', {'52': '12349', '56': '12347', '54': '12348'}], ['Авигаль-П-464-1', ['52', '54', '56', '58', '60'], '3750', '12334', {'52': '12339', '56': '12337', '60': '12335', '58': '12336', '54': '12338'}], ['Авигаль-П-084-1', ['50', '54'], '2700', '12285', {'50': '12290', '54': '12288'}], ['Новита 591', ['50', '52', '54', '56', '58'], '2600', '12055', {'50': '12060', '52': '12059', '56': '12057', '58': '12056', '54': '12058'}], ['Новита 583 вишневый', ['48', '50', '52', '54', '56'], '3200', '11997', {'50': '12001', '52': '12000', '56': '11998', '54': '11999', '48': '12002'}], ['Новита 581 синие цветы', ['50', '52'], '3300', '11989', {'50': '11993', '52': '11992'}], ['Визель П3-3232', ['52', '54', '56', '60'], '3400', '11883', {'52': '11887', '56': '11885', '60': '11884', '54': '11886'}], ['Визель П5-3347/2', ['46', '48', '52', '54', '56', '58'], '4400', '11862', {'46': '12026', '54': '11866', '52': '11867', '56': '11865', '48': '11869', '58': '12507'}], ['Новита 576 коралловый', ['48', '50', '52', '54', '56', '58'], '3000', '10983', {'48': '10989', '58': '10984', '50': '10988', '52': '10987', '56': '10985', '54': '10986'}], ['Авигаль-П-982', ['56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '10807', {'74': '15690', '60': '15697', '58': '15698', '72': '15691', '66': '15694', '64': '15695', '68': '15693', '56': '15699', '62': '15696', '70': '15692'}], ['Новита 568', ['48', '50', '54', '56'], '3200', '10256', {'50': '10259', '48': '10260', '56': '13005', '54': '10258'}], ['Новита 567', ['48', '50', '52', '54', '56'], '3300', '10246', {'50': '10250', '52': '10249', '56': '10247', '54': '10248', '48': '10251'}], ['Н/Д', ['52', '54', '56', '58'], '3800', '11829', {'52': '11834', '56': '11832', '58': '11831', '54': '11833'}], ['Визель-П3-3585/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11375', {'48': '11383', '60': '11377', '58': '11378', '50': '11382', '52': '11381', '56': '11379', '54': '11380'}], ['Новита 575 васильковый', ['48', '50', '52', '54'], '3000', '10973', {'50': '10978', '52': '10977', '48': '10979', '54': '10976'}], ['Новита 562', ['50', '52', '54', '56'], '3300', '9186', {'50': '9190', '52': '9189', '56': '9187', '54': '9188'}], ['Новита-538', ['50', '52', '54', '56'], '3000', '6185', {'50': '11180', '52': '6189', '56': '6187', '54': '6188'}], ['Авигаль-П-307', ['54', '58', '60', '62', '64'], '3600', '12324', {'64': '12325', '62': '12326', '60': '12327', '58': '12328', '54': '12330'}], ['Визель-П3-3232/1', ['52', '54', '56', '58', '60'], '3400', '12307', {'52': '12312', '56': '12310', '60': '12308', '58': '12309', '54': '12311'}], ['Новита-407с', ['50', '52', '54', '56'], '3100', '4217', {'50': '13032', '52': '13033', '56': '13213', '54': '13034'}], ['Визель П3-3603/1', ['48', '50', '52'], '3800', '13083', {'50': '13089', '52': '13088', '48': '13090'}], ['Авигаль П-449', ['56', '62', '64', '66'], '2600', '12753', {'66': '12756', '56': '12759', '64': '12757', '62': '12758'}], ['Авигаль-П-084', ['50', '52'], '2700', '12270', {'50': '12282', '52': '12281'}], ['Визель П3-3331/2', ['46', '48', '50', '52'], '4200', '11892', {'50': '11897', '52': '11896', '48': '11898', '46': '11899'}], ['Визель П4-3538/5', ['50', '52', '56'], '4600', '8485', {'50': '9434', '52': '8488', '56': '14139'}], ['Новита 548 электрик', ['48', '50', '52', '54', '56'], '3200', '7560', {'50': '7564', '52': '7563', '56': '7561', '54': '7562', '48': '7565'}], ['Новита-493/1', ['52', '54', '56', '58'], '3500', '5514', {'52': '5520', '56': '5518', '58': '5517', '54': '5519'}], ['Новита-530', ['52', '56'], '3300', '5493', {'52': '11369', '56': '5494'}], ['Визель-П4-2571/15', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12146', {'48': '12153', '60': '13265', '54': '13268', '50': '12152', '52': '13269', '56': '13267', '58': '13266'}], ['Новита 486', ['50', '52', '54', '56', '58'], '3000', '7435', {'50': '7440', '52': '7439', '56': '7437', '58': '7436', '54': '7438'}], ['Прима 2956', ['48', '50', '52', '54', '56', '58', '60', '62'], '3580', '6787', {'48': '6795', '60': '8177', '54': '8175', '50': '6794', '52': '8173', '56': '8174', '62': '8176', '58': '6791'}], ['Новита-522', ['50', '54', '56', '60'], '3000', '5302', {'50': '5310', '56': '5307', '60': '5305', '54': '5308'}], ['Авигаль П-229-2', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2500', '14000', {'74': '14011', '58': '14002', '66': '14003', '72': '14009', '68': '14010', '56': '14001', '62': '14008', '60': '14005', '54': '14007', '64': '14006', '70': '14012', '52': '14004'}], ['Новита 565', ['50', '52', '54', '56'], '3400', '9204', {'50': '9208', '52': '9207', '56': '9205', '54': '9206'}], ['Новита 554 белая клетка', ['48', '50', '52', '54', '56', '58'], '3200', '8595', {'48': '8601', '54': '10287', '50': '8600', '52': '8599', '56': '8597', '58': '8596'}], ['Новита 429', ['50', '52', '54', '56'], '3100', '8569', {'50': '14780', '52': '8572', '56': '8570', '54': '8571'}], ['Новита 343', ['48', '50', '52', '54', '56'], '3200', '7620', {'50': '7624', '52': '7623', '56': '7621', '54': '7622', '48': '7625'}], ['Прима 2915', ['50', '52', '54', '56'], '3600', '7067', {'50': '7072', '52': '7071', '56': '7069', '54': '15678'}], ['Визель П5-3506/1', ['52', '54', '56', '58', '60'], '4000', '6099', {'52': '6105', '56': '6103', '60': '6101', '54': '6104', '58': '6102'}], ['Визель-П3-2337/6', ['50', '52', '54', '56', '58', '60'], '4200', '5989', {'60': '5996', '54': '5992', '50': '5994', '52': '5993', '56': '5991', '58': '5990'}], ['Авигаль П-445', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2900', '13587', {'56': '13595', '60': '13593', '54': '13596', '52': '13597', '66': '13590', '64': '13591', '68': '13589', '70': '13588', '62': '13592', '58': '13594'}], ['Краса П-0039', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13520', {'60': '13524', '58': '13525', '66': '13521', '64': '13522', '52': '13528', '56': '13526', '62': '13523', '54': '13527'}], ['Авигаль П-450', ['56', '60'], '2500', '12203', {'56': '12208', '60': '12209'}], ['Визель-П3-3465/3', ['48', '50', '52', '54', '56', '60'], '4400', '8721', {'48': '8728', '60': '8722', '54': '8725', '50': '8727', '52': '8726', '56': '8724'}], ['Прима 2960', ['50', '52', '54', '56', '58', '60', '62', '64'], '3840', '6480', {'60': '6483', '54': '6486', '50': '6488', '64': '15098', '52': '6487', '56': '15099', '62': '6482', '58': '15100'}], ['Новита-534', ['50', '52', '54', '56', '58', '60'], '3400', '6167', {'60': '6168', '58': '6169', '50': '6173', '52': '6172', '56': '6170', '54': '6171'}], ['Визель П4-3371/16', ['48', '50', '52', '54', '56', '58'], '3600', '6073', {'48': '6080', '54': '6077', '50': '6079', '52': '12547', '56': '6076', '58': '6075'}], ['Визель-П3-3468/4', ['54'], '2000', '4555', {'54': '12729'}], ['Новита 617', ['46', '48', '50', '52', '54', '56'], '2700', '14665', {'46': '14671', '48': '14670', '54': '14667', '50': '14669', '52': '14668', '56': '14666'}], ['Краса П-0063', ['52', '54', '56', '58', '60', '62', '64'], '2400', '13423', {'60': '13431', '58': '13432', '64': '13429', '52': '13435', '56': '13433', '62': '13430', '54': '13434'}], ['Краса П-0076', ['52', '54', '56', '58', '60', '62', '64'], '2400', '13315', {'60': '13319', '58': '13320', '64': '13317', '52': '13323', '56': '13321', '62': '13318', '54': '13322'}], ['Краса П-0074', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13236', {'60': '13237', '54': '13239', '66': '13243', '64': '13242', '52': '13238', '56': '13241', '62': '13244', '58': '13240'}], ['Визель П4-3605/1', ['52', '58', '60'], '3600', '13197', {'52': '13202', '60': '15661', '58': '13199'}], ['Новита 597', ['48', '50', '52', '54', '56'], '2700', '12615', {'50': '12619', '52': '12618', '56': '12616', '54': '12617', '48': '12620'}], ['Новита 418', ['48', '50', '52', '54', '56'], '3100', '12586', {'50': '12590', '52': '12589', '56': '12587', '54': '12588', '48': '12591'}], ['Визель-П3-3293', ['54', '56'], '4000', '9622', {'56': '9625', '54': '9626'}], ['Визель П4-3539/1', ['56'], '5000', '8431', {'56': '12727'}], ['Визель П4-3539/3', ['48', '50', '58'], '5000', '8413', {'50': '12552', '48': '12553', '58': '11252'}], ['Новита 558', ['48', '50', '52'], '3100', '7918', {'50': '7922', '52': '7921', '48': '7923'}], ['Прима-2944', ['48', '50', '52', '54', '56', '58', '62', '64'], '4400', '6653', {'48': '6666', '64': '6658', '54': '6663', '50': '6665', '52': '6664', '56': '6662', '62': '6659', '58': '6661'}], ['Прима 2939', ['48', '50', '52', '54', '56', '58', '60', '62'], '3520', '6593', {'48': '6601', '60': '6595', '54': '6598', '50': '6600', '52': '6599', '56': '6597', '62': '6594', '58': '6596'}], ['Визель-П3-2337/4', ['48', '50', '52', '54', '56', '58', '60'], '4200', '5974', {'48': '5981', '60': '5975', '58': '5976', '50': '5980', '52': '5979', '56': '5977', '54': '5978'}], ['Новита-527', ['50', '52', '54', '56', '58'], '3200', '5483', {'50': '5488', '52': '5487', '56': '5485', '58': '5484', '54': '5486'}], ['Новита -520', ['48', '50', '52', '54', '56', '58'], '3100', '5311', {'48': '5317', '58': '5312', '50': '5316', '52': '5315', '56': '5313', '54': '5314'}], ['Визель-П3-3479/1', ['50', '52', '54', '56'], '4200', '4261', {'50': '12730', '52': '4266', '56': '4264', '54': '14141'}], ['Новита-509', ['50'], '2000', '3711', {'50': '3716'}], ['Новита-510', ['50', '52', '54', '56', '58'], '3300', '3669', {'50': '3674', '52': '3673', '56': '3671', '58': '3670', '54': '3672'}], ['Новита-506', ['48', '50', '52', '54', '56'], '3000', '3497', {'50': '3501', '52': '3500', '56': '3498', '54': '3499', '48': '3502'}], ['Авигаль П-104-1', ['54', '56', '58', '60', '62', '64', '66'], '2600', '15610', {'64': '15613', '54': '15618', '66': '15612', '60': '15615', '56': '15617', '62': '15614', '58': '15616'}], ['Авигаль П-611', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '2500', '15571', {'58': '15579', '56': '15580', '64': '15576', '54': '15581', '72': '15572', '66': '15575', '60': '15578', '52': '15582', '70': '15573', '68': '15574', '62': '15577'}], ['Прима линия 4115', ['60', '62', '64', '66', '68', '70'], '3600', '15220', {'64': '15228', '66': '15227', '60': '15230', '68': '15226', '70': '15225', '62': '15229'}], ['Авигаль П-467-1', ['52', '54', '56', '58', '60', '62', '64'], '3200', '14857', {'60': '14858', '58': '14859', '64': '14864', '52': '14862', '56': '14860', '62': '14863', '54': '14861'}], ['Новита 605', ['48', '50', '52', '54', '56', '58'], '3200', '14697', {'48': '14703', '58': '14698', '50': '14702', '52': '14701', '56': '14699', '54': '14700'}], ['Новита 449/2', ['50', '52', '54', '56'], '2900', '14620', {'50': '14624', '52': '14623', '56': '14621', '54': '14622'}], ['Визель П3-3623/1', ['50', '52', '54', '56', '58', '60'], '3400', '14497', {'60': '14498', '58': '14499', '50': '14503', '52': '14502', '56': '14500', '54': '14501'}], ['Краса П-0089', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14391', {'60': '14395', '58': '14396', '66': '14392', '64': '14393', '52': '14399', '56': '14397', '62': '14394', '54': '14398'}], ['Краса ПБ-0012', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14196', {'60': '14200', '58': '14201', '66': '14197', '64': '14198', '52': '14204', '56': '14202', '62': '14199', '54': '14203'}], ['Авигаль П-229', ['54', '56', '60', '64', '66', '68', '70', '72', '74'], '2200', '13966', {'74': '13967', '64': '13972', '54': '13977', '72': '13968', '66': '13971', '60': '13974', '68': '13970', '56': '13976', '70': '13969'}], ['Авигаль П-305-3', ['50', '54', '64', '66', '68'], '2500', '13762', {'50': '13771', '66': '13767', '68': '13768', '64': '13766', '54': '13765'}], ['Краса П-0042', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13548', {'60': '13553', '58': '13554', '66': '13550', '64': '13551', '52': '13557', '56': '13555', '62': '13552', '54': '13556'}], ['Новита 596 кофейное', ['48', '50', '52'], '3400', '12683', {'50': '12686', '52': '12685', '48': '12687'}], ['Новита 596 белое', ['48', '50', '52', '56'], '3400', '12673', {'50': '13957', '52': '13956', '48': '13958', '56': '13954'}], ['Визель\xa0П3-3598/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '12465', {'48': '12472', '60': '12466', '58': '12467', '50': '12471', '52': '12470', '56': '12468', '54': '12469'}], ['Новита 594', ['48', '50', '52', '54', '56', '58'], '3200', '12073', {'48': '12079', '58': '12074', '50': '12078', '52': '12077', '56': '12075', '54': '12076'}], ['Авигаль-П-497', ['50', '52', '60'], '3360', '11960', {'50': '11966', '52': '11965', '60': '11961'}], ['Авигаль-П-326-1', ['52', '54', '56', '60', '62'], '2500', '11950', {'52': '11959', '56': '11957', '60': '11955', '62': '11954', '54': '11958'}], ['Визель П2-3311/1', ['48', '50', '52', '56'], '3800', '11915', {'50': '14783', '52': '11920', '48': '11922', '56': '11918'}], ['Визель П3-3494/1', ['48', '50', '52'], '3800', '11904', {'50': '11910', '52': '11909', '48': '11911'}], ['Авигаль-П-483-3', ['52', '54', '56', '62'], '2400', '11518', {'52': '11525', '56': '14939', '54': '11524', '62': '11520'}], ['Визель П3-3586/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11488', {'48': '11495', '60': '11489', '58': '11490', '50': '11494', '52': '11493', '56': '11491', '54': '11492'}], ['Авигаль-П-495-1', ['50', '52', '58'], '2500', '11329', {'50': '11335', '52': '11334', '58': '11331'}], ['Авигаль-П-702-1', ['50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2400', '11267', {'50': '11285', '56': '11282', '64': '11278', '58': '11281', '68': '11276', '66': '11277', '60': '11280', '52': '11284', '70': '11275', '62': '11279', '54': '11283'}], ['Авигаль-П-400', ['50', '54', '60', '64'], '2400', '11228', {'50': '11234', '60': '11231', '64': '11229', '54': '11233'}], ['Авигаль-П-706', ['52', '54', '70', '72'], '2900', '11095', {'72': '11105', '52': '11102', '70': '11106', '54': '11101'}], ['Новита 577 бирюзовый', ['48', '50', '52', '54', '56', '58'], '3000', '10993', {'48': '10999', '58': '10994', '50': '10998', '52': '10997', '56': '10995', '54': '10996'}], ['Авигаль-П-488', ['52', '54', '56', '58', '66'], '2700', '10793', {'66': '10796', '52': '10803', '56': '10801', '58': '10798', '54': '10802'}], ['Визель-П3-3571/3', ['52', '54', '56', '58', '60'], '4400', '10665', {'52': '10670', '56': '10668', '60': '10666', '58': '10667', '54': '10669'}], ['Визель-П3-3567/1', ['48', '50', '52', '54', '56', '60'], '3600', '9744', {'48': '9751', '60': '9745', '54': '9748', '50': '9750', '52': '9749', '56': '9747'}], ['Визель П4-3561/1', ['52', '54', '56', '58', '60'], '3200', '9359', {'52': '9364', '56': '9362', '60': '9360', '58': '9361', '54': '9363'}], ['Новита 574 бежевый орнамент', ['46', '50', '52', '54', '56'], '2900', '9300', {'50': '9304', '52': '9303', '56': '9301', '54': '9302', '46': '9306'}], ['Новита 564', ['48', '50', '52', '54', '56'], '3300', '9195', {'50': '9199', '52': '9198', '56': '9196', '54': '9197', '48': '9200'}], ['Прима 2964', ['62', '64'], '3560', '9058', {'64': '9059', '62': '9060'}], ['Визель-П3-3080/1', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8746', {'48': '8753', '60': '8747', '58': '8748', '50': '8752', '52': '8751', '56': '8749', '54': '8750'}], ['Визель-П3-3540/1', ['50', '52', '58', '60'], '3400', '8680', {'50': '8686', '52': '8685', '60': '8681', '58': '8682'}], ['Новита 560', ['44', '46', '48', '50', '52', '54', '56'], '2800', '8518', {'46': '8524', '54': '10288', '50': '8522', '52': '8521', '44': '8525', '56': '8519', '48': '8523'}], ['Визель П4-3538/1', ['48', '50', '52', '54', '60'], '4600', '8462', {'50': '12562', '52': '8467', '48': '12563', '60': '13270', '54': '8466'}], ['Новита 326/1', ['48', '50', '52', '54', '56'], '3000', '7643', {'50': '7648', '52': '7647', '56': '7645', '54': '7646', '48': '7649'}], ['Новита 309', ['46', '48', '50', '52', '56'], '3200', '7610', {'50': '7614', '52': '7613', '56': '7611', '48': '7615', '46': '7616'}], ['Новита 518', ['50', '52', '56', '58'], '3200', '7427', {'50': '7432', '52': '7431', '56': '14781', '58': '7428'}], ['Новита 531 изумрудный', ['48', '50', '52', '54', '56', '58'], '3100', '7398', {'48': '7404', '54': '7401', '50': '7403', '52': '7402', '56': '7400', '58': '9281'}], ['Новита 542', ['48', '50', '54', '56', '58'], '3200', '6886', {'50': '6891', '56': '6888', '58': '6887', '48': '6892', '54': '6889'}], ['Прима 2875', ['52', '54', '58', '62', '64', '66', '68', '70'], '4400', '6775', {'64': '6777', '54': '6782', '68': '13948', '66': '6776', '52': '6783', '70': '13947', '62': '6778', '58': '6780'}], ['Прима 2876', ['48', '52', '56', '58', '60', '62'], '4200', '6749', {'48': '6759', '60': '6753', '58': '6754', '52': '12402', '56': '6755', '62': '6752'}], ['Прима 2961', ['52', '54', '56', '58', '60', '62', '64', '66'], '3840', '6627', {'60': '6631', '58': '6632', '66': '6628', '64': '6629', '52': '6635', '56': '6633', '62': '6630', '54': '6634'}], ['Прима 2925', ['48', '50', '52'], '3240', '6615', {'50': '6621', '52': '6620', '48': '6622'}], ['Новита-528', ['54', '56', '58'], '3300', '5503', {'56': '5505', '58': '5504', '54': '5506'}], ['Со-ЮНОНА ПРИНТ НА ЧЕРНОМ', ['60'], '2600', '5044', {'60': '9646'}], ['Визель-П4-3469/1', ['56'], '2000', '4426', {'56': '13274'}], ['Новита-242', ['48', '50', '52', '54', '56', '58', '60'], '0', '4208', {}], ['Новита-393В', ['56'], '2000', '4200', {'56': '4202'}], ['Олеся-24019-1', ['56'], '2000', '4113', {'56': '12138'}], ['Новита-441', ['48', '50', '52', '54', '56'], '3100', '3703', {'50': '3707', '52': '3706', '56': '3704', '54': '3705', '48': '3708'}], ['Новита-492', ['50'], '2000', '3070', {'50': '9647'}], ['Новита-503', ['48', '50', '52', '54', '56'], '3000', '3043', {'50': '3050', '52': '3049', '56': '3047', '54': '3048', '48': '3051'}], ['Олеся-27026-1', ['50', '52'], '2000', '2741', {'50': '2746', '52': '2745'}], ['Джетти-Б005-1', ['46', '50', '52', '54', '56'], '0', '2303', {}], ['ЕО-27014-1', ['50'], '2000', '1893', {'50': '1902'}], ['ЕО-27018-1', ['52'], '2000', '1873', {'52': '1877'}], ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '2000', '1795', {'52': '9640', '62': '9641'}], ['Авигаль П-905-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700', '15714', {'60': '15718', '54': '15715', '68': '15723', '66': '15721', '64': '15720', '52': '15716', '56': '15717', '62': '15719', '58': '15722'}], ['Авигаль П-905', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2700', '15701', {'60': '15706', '54': '15709', '68': '15702', '66': '15703', '64': '15704', '52': '15710', '56': '15708', '62': '15705', '58': '15707'}], ['Авигаль П-104-4', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600', '15641', {'60': '15649', '54': '15644', '66': '15648', '64': '15643', '68': '15647', '56': '15646', '62': '15645', '58': '15642'}], ['Авигаль П-104-3', ['54', '56', '58', '60', '62', '64', '66', '68'], '2600', '15632', {'60': '15637', '54': '15638', '66': '15636', '64': '15639', '68': '15635', '56': '15634', '62': '15633', '58': '15640'}], ['Авигаль П-104-2', ['54', '56', '60', '62', '66', '68'], '2600', '15621', {'60': '15623', '54': '15622', '66': '15629', '68': '15628', '56': '15627', '62': '15626'}], ['Авигаль П-611-1', ['54', '56', '58', '60', '62', '64', '66'], '2500', '15585', {'60': '15600', '58': '15601', '66': '15597', '64': '15598', '56': '15602', '62': '15599', '54': '15603'}], ['Новита-607', ['50', '52', '54', '56'], '2800', '15467', {'50': '15471', '52': '15470', '56': '15468', '54': '15469'}], ['Прима линия 4130', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '4200', '15411', {'48': '15420', '58': '15415', '66': '15424', '72': '15421', '68': '15423', '56': '15416', '62': '15413', '50': '15419', '60': '15414', '54': '15417', '64': '15412', '70': '15422', '52': '15418'}], ['Прима линия 4129', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72'], '4200', '15393', {'48': '15406', '58': '15401', '66': '15397', '72': '15394', '68': '15396', '56': '15402', '62': '15399', '50': '15405', '60': '15400', '54': '15403', '64': '15398', '70': '15395', '52': '15404'}], ['Прима линия 4140', ['64', '66'], '4400', '15378', {'66': '15387', '64': '15388'}], ['Прима линия 4139', ['48', '50', '56', '58', '60', '62', '64', '66'], '4400', '15360', {'50': '15373', '48': '15374', '64': '15368', '58': '15371', '66': '15367', '60': '15370', '56': '15372', '62': '15369'}], ['Прима линия 4116', ['60', '62', '64', '66', '68', '70'], '4400', '15349', {'64': '15353', '66': '15352', '60': '15355', '68': '15351', '70': '15350', '62': '15354'}], ['Прима линия 4103', ['68', '70', '72', '74'], '4400', '15340', {'74': '15680', '72': '15341', '68': '15343', '70': '15342'}], ['Прима линия 4108', ['64', '66', '68', '70', '72'], '4400', '15331', {'66': '15335', '72': '15332', '68': '15334', '70': '15333', '64': '15336'}], ['Прима линия 4098', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2400', '15313', {'74': '15314', '58': '15322', '66': '15318', '72': '15315', '68': '15317', '56': '15323', '62': '15320', '50': '15326', '48': '15327', '60': '15321', '54': '15324', '64': '15319', '70': '15316', '52': '15325'}], ['Прима линия 4096', ['66', '68', '70', '72', '74'], '2400', '15304', {'66': '15309', '72': '15306', '68': '15308', '74': '15305', '70': '15307'}], ['Новита 606 красное', ['48', '50', '52', '54'], '3000', '15280', {'50': '15283', '52': '15282', '48': '15284', '54': '15281'}], ['Новита 606 фиолетовое', ['48', '50', '52', '54'], '3000', '15271', {'50': '15274', '52': '15273', '48': '15275', '54': '15272'}], ['Новита 622', ['48', '50', '52', '54', '56'], '2900', '15259', {'50': '15263', '52': '15262', '56': '15260', '54': '15261', '48': '15264'}], ['Новита 614', ['50', '52', '54', '56', '58'], '3100', '15248', {'50': '15253', '52': '15252', '56': '15250', '58': '15249', '54': '15251'}], ['Новита 620', ['48', '50', '52', '54', '56'], '3000', '15237', {'50': '15241', '52': '15240', '56': '15238', '54': '15239', '48': '15242'}], ['Прима линия 4112', ['52', '54', '56', '58'], '3600', '15212', {'52': '15216', '56': '15214', '58': '15213', '54': '15215'}], ['Прима линия 4084', ['54', '56', '58', '60', '62', '64', '66'], '3000', '15200', {'60': '15207', '54': '15204', '66': '15201', '64': '15205', '56': '15203', '62': '15206', '58': '15202'}], ['Прима линия 4085', ['54', '56', '58', '60', '62', '64', '66'], '3000', '15189', {'60': '15195', '54': '15192', '66': '15196', '64': '15193', '56': '15191', '62': '15194', '58': '15190'}], ['Прима линия 4086', ['48', '50', '52', '54', '56', '58'], '3000', '15179', {'48': '15185', '58': '15180', '50': '15184', '52': '15183', '56': '15181', '54': '15182'}], ['Прима линия 4021', ['54', '58', '60', '62'], '4400', '15169', {'62': '15175', '60': '15170', '54': '15173', '58': '15171'}], ['Прима 4020', ['52', '54', '56', '58', '60', '62'], '4400', '15158', {'60': '15160', '54': '15163', '52': '15164', '56': '15162', '62': '15159', '58': '15161'}], ['Авигаль П-011', ['54', '56', '58', '60', '62', '64', '66'], '3300', '15101', {'60': '15105', '58': '15106', '66': '15102', '64': '15103', '56': '15107', '62': '15104', '54': '15108'}], ['Визель П3-3630/2', ['48', '52', '54', '56', '58', '60', '62'], '3400', '15074', {'48': '15082', '60': '15076', '54': '15079', '52': '15080', '56': '15078', '62': '15075', '58': '15077'}], ['Визель П3-3630/1', ['48', '50', '52', '54', '56', '58', '60', '62'], '3400', '15058', {'48': '15066', '60': '15060', '54': '15063', '50': '15065', '52': '15064', '56': '15062', '62': '15059', '58': '15061'}], ['Визель П3-3640/1', ['48', '50', '52', '54', '56', '58', '60'], '4200', '15031', {'48': '15038', '60': '15032', '54': '15035', '50': '15037', '52': '15036', '56': '15034', '58': '15033'}], ['Визель П3-3195/2', ['48', '50', '52', '54', '56', '58', '60'], '4200', '15001', {'48': '15008', '60': '15002', '54': '15005', '50': '15007', '52': '15006', '56': '15004', '58': '15003'}], ['Визель П4-3635/1', ['48', '50', '52', '54', '56', '58', '60'], '3400', '14987', {'48': '14994', '60': '14988', '58': '14989', '50': '14993', '52': '14992', '56': '14990', '54': '14991'}], ['Визель П4-3637/3', ['48', '50', '52', '54', '56', '58', '60'], '4400', '14974', {'48': '14981', '60': '14975', '54': '14978', '50': '14980', '52': '14979', '56': '14977', '58': '14976'}], ['Визель П4-3638/3', ['48', '50', '52', '54', '56', '58', '60'], '3800', '14959', {'48': '14963', '60': '14966', '54': '14961', '50': '14964', '52': '14965', '56': '14962', '58': '14960'}], ['Визель П4-3638/1', ['48', '50', '52', '54', '56', '58', '60'], '3800', '14944', {'48': '14951', '60': '14945', '58': '14946', '50': '14950', '52': '14949', '56': '14947', '54': '14948'}], ['Прима 4052', ['46', '48', '50', '52', '54', '56'], '2580', '14894', {'46': '14901', '48': '14900', '54': '14897', '50': '14899', '52': '14898', '56': '14896'}], ['Авигаль П-467', ['52', '54', '56', '58', '60', '62', '64'], '3200', '14846', {'60': '14849', '58': '14850', '64': '14847', '52': '14853', '56': '14851', '62': '14848', '54': '14852'}], ['Новита 602', ['48', '50', '52', '54', '56'], '2600', '14731', {'50': '14735', '52': '14734', '56': '14732', '54': '14733', '48': '14736'}], ['Новита 578 красный', ['48', '50', '52', '54', '56', '58'], '3000', '14709', {'48': '14715', '58': '14710', '50': '14714', '52': '14713', '56': '14711', '54': '14712'}], ['Новита 455/1', ['48', '50', '52', '54', '56'], '3000', '14655', {'50': '14659', '52': '14658', '56': '14656', '54': '14657', '48': '14660'}], ['Новита 619', ['48', '50', '52', '54', '56'], '2800', '14630', {'50': '14634', '52': '14633', '56': '14631', '54': '14632', '48': '14635'}], ['Новита 595', ['48', '50', '52', '54'], '2900', '14611', {'50': '14614', '52': '14613', '48': '14615', '54': '14612'}], ['Новита 375 бежевый орнамент', ['50', '52', '54', '56', '58', '60'], '2900', '14599', {'60': '14600', '58': '14601', '50': '14605', '52': '14604', '56': '14602', '54': '14603'}], ['Авигаль П-062-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2700', '14574', {'56': '14582', '60': '14580', '54': '14583', '52': '14584', '66': '14577', '64': '14578', '68': '14576', '70': '14575', '62': '14579', '58': '14581'}], ['Авигаль П-062', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2700', '14560', {'56': '14568', '60': '14566', '54': '14569', '52': '14570', '66': '14563', '64': '14564', '68': '14562', '70': '14561', '62': '14565', '58': '14567'}], ['Авигаль П-548-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '14549', {'60': '14553', '58': '14554', '66': '14550', '64': '14551', '52': '14557', '56': '14555', '62': '14552', '54': '14556'}], ['Авигаль П-548', ['52', '54', '56', '58', '60', '62', '64'], '3700', '14536', {'60': '14540', '58': '14541', '64': '14538', '52': '14544', '56': '14542', '62': '14539', '54': '14543'}], ['Визель П3-3620/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14468', {'48': '14475', '60': '14469', '58': '14470', '50': '14474', '52': '14473', '56': '14471', '54': '14472'}], ['Краса П-0085', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14451', {'60': '14455', '58': '14456', '66': '14452', '64': '14453', '52': '14459', '56': '14457', '62': '14454', '54': '14458'}], ['Краса П-0086', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14436', {'60': '14440', '58': '14441', '66': '14437', '64': '14438', '52': '14444', '56': '14442', '62': '14439', '54': '14443'}], ['Краса П-0087', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14421', {'60': '14425', '58': '14426', '66': '14422', '64': '14423', '52': '14429', '56': '14427', '62': '14424', '54': '14428'}], ['Визель\xa0П3-3616/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14289', {'48': '14296', '60': '14290', '58': '14291', '50': '14295', '52': '14294', '56': '14292', '54': '14293'}], ['Визель П3-3616/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14276', {'48': '14283', '60': '14277', '58': '14278', '50': '14282', '52': '14281', '56': '14279', '54': '14280'}], ['Визель П2-3617/5', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14263', {'48': '14269', '60': '14270', '54': '14266', '50': '14268', '52': '14267', '56': '14265', '58': '14264'}], ['Визель П2-3617/3', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14249', {'48': '14255', '60': '14256', '54': '14252', '50': '14254', '52': '14253', '56': '14251', '58': '14250'}], ['Визель П2-3617/1', ['48', '50', '52', '54', '56', '58', '60'], '3600', '14236', {'48': '14243', '60': '14237', '58': '14238', '50': '14242', '52': '14241', '56': '14239', '54': '14240'}], ['Краса ПБ-0010', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14220', {'60': '14224', '58': '14225', '66': '14221', '64': '14222', '52': '14228', '56': '14226', '62': '14223', '54': '14227'}], ['Краса ПБ-0011', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '14208', {'60': '14212', '58': '14213', '66': '14209', '64': '14210', '52': '14216', '56': '14214', '62': '14211', '54': '14215'}], ['Краса ПБ-0016', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '14157', {'60': '14158', '54': '14163', '50': '14165', '64': '14161', '52': '14164', '56': '14162', '62': '14160', '58': '14159'}], ['Краса ПБ-0017', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '14144', {'64': '14145', '58': '14148', '50': '14152', '60': '14147', '52': '14151', '56': '14149', '62': '14146', '54': '14150'}], ['Новита 600 мятный', ['48', '50', '52', '54', '56'], '3300', '14071', {'50': '14074', '52': '14073', '48': '14075', '56': '14076', '54': '14072'}], ['Новита 600 голубой', ['48', '50', '52', '54', '56'], '3300', '14060', {'50': '14064', '52': '14063', '56': '14061', '54': '14062', '48': '14065'}], ['Новита 583 кремово-розовый', ['48', '50', '52', '54', '56'], '3200', '14040', {'50': '14044', '52': '14043', '56': '14041', '54': '14042', '48': '14045'}], ['Авигаль П-229-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70', '72', '74'], '2200', '13983', {'74': '13993', '58': '13985', '66': '13986', '72': '13992', '68': '13994', '56': '13984', '62': '13991', '60': '13988', '54': '13990', '64': '13989', '70': '13995', '52': '13987'}], ['Краса ПБ-0020', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13852', {'60': '13856', '58': '13857', '66': '13853', '64': '13854', '52': '13860', '56': '13858', '62': '13855', '54': '13859'}], ['Краса ПБ-0024', ['56', '58', '60', '62', '64', '66'], '2400', '13807', {'60': '13811', '58': '13812', '66': '13808', '64': '13809', '56': '13813', '62': '13810'}], ['Авигаль П-305-2', ['54', '56', '60', '62', '64', '66', '68'], '2500', '13746', {'60': '13755', '54': '13758', '66': '13752', '64': '13753', '68': '13751', '56': '13757', '62': '13754'}], ['Авигаль П-305-1', ['54', '56', '58', '60'], '2500', '13734', {'56': '13741', '60': '13739', '58': '13740', '54': '13742'}], ['Авигаль П-305', ['54', '56', '58', '60', '62', '64', '66', '68'], '2500', '13722', {'60': '13727', '58': '13728', '66': '13724', '64': '13725', '68': '13723', '56': '13729', '62': '13726', '54': '13730'}], ['Краса П-0035', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13661', {'60': '13663', '54': '13666', '66': '13668', '64': '13669', '52': '13667', '56': '13665', '62': '13662', '58': '13664'}], ['Краса П-0033', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13634', {'60': '13638', '58': '13639', '66': '13635', '64': '13636', '52': '13642', '56': '13640', '62': '13637', '54': '13641'}], ['Краса П-0037', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13621', {'64': '13623', '58': '13626', '66': '13622', '60': '13625', '52': '13629', '56': '13627', '62': '13624', '54': '13628'}], ['Авигаль П-445-1', ['52', '54', '56', '58', '60', '62', '66', '68', '70'], '2900', '13602', {'70': '13610', '60': '13605', '54': '13608', '68': '13611', '66': '13612', '52': '13609', '56': '13607', '62': '13604', '58': '13606'}], ['Краса П-0049', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13504', {'60': '13508', '58': '13509', '66': '13505', '64': '13506', '52': '13512', '56': '13510', '62': '13507', '54': '13511'}], ['Краса П-0060', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13489', {'60': '13494', '58': '13495', '66': '13491', '64': '13492', '52': '13498', '56': '13496', '62': '13493', '54': '13497'}], ['Краса П-0052', ['52', '54', '56', '58', '60', '62', '64'], '2400', '13476', {'60': '13479', '54': '13482', '64': '13477', '52': '13483', '56': '13481', '62': '13478', '58': '13480'}], ['Краса П-0061', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13463', {'60': '13467', '58': '13468', '66': '13464', '64': '13465', '52': '13471', '56': '13469', '62': '13466', '54': '13470'}], ['Краса П-0050', ['56', '58', '60', '62', '64', '66'], '2400', '13449', {'60': '13453', '58': '13454', '66': '13450', '64': '13451', '56': '13455', '62': '13452'}], ['Краса П-0057', ['52', '54', '56', '58'], '2400', '13409', {'52': '13413', '56': '13411', '58': '13410', '54': '13412'}], ['Краса П-0064', ['50', '52', '54', '56', '58', '60', '62', '64'], '2400', '13396', {'60': '13399', '58': '13400', '50': '13404', '64': '13397', '52': '13403', '56': '13401', '62': '13398', '54': '13402'}], ['Краса П-0055', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13369', {'60': '13373', '58': '13374', '66': '13370', '64': '13371', '52': '13377', '56': '13375', '62': '13372', '54': '13376'}], ['Краса П-0078', ['52', '54', '56', '58', '60', '62', '64', '66'], '2400', '13343', {'60': '13347', '58': '13348', '66': '13344', '64': '13345', '52': '13351', '56': '13349', '62': '13346', '54': '13350'}], ['Визель П3-3615/1', ['52', '54', '56', '58', '60'], '3600', '13175', {'52': '13180', '56': '13178', '60': '13176', '58': '13177', '54': '13179'}], ['Визель П2-3609/1', ['50', '52', '54', '56', '58', '60'], '3400', '13050', {'60': '15664', '54': '13054', '50': '13056', '52': '13055', '56': '13053', '58': '15663'}], ['Визель П3-3240', ['48', '50', '52', '54', '56', '58'], '3600', '13037', {'48': '13044', '58': '13039', '50': '13043', '52': '13042', '56': '13040', '54': '13041'}], ['Авигаль П-704', ['52', '54', '56', '58', '60', '62', '64', '66', '68'], '2900', '12800', {'60': '12806', '54': '12802', '68': '12804', '66': '12809', '64': '12808', '52': '12803', '56': '12801', '62': '12807', '58': '12805'}], ['Авигаль П-446', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2600', '12768', {'70': '12769', '64': '12772', '58': '12775', '66': '12771', '60': '12774', '68': '12770', '56': '12776', '54': '12777', '62': '12773', '52': '12778'}], ['Новита 461', ['48', '50', '52'], '3100', '12595', {'50': '12597', '52': '12596', '48': '12598'}], ['Визель П3-3596/3', ['48', '50', '52', '54', '56', '58', '60'], '4000', '12436', {'48': '12443', '60': '12437', '58': '12438', '50': '12442', '52': '12441', '56': '12439', '54': '12440'}], ['Визель П3-3479/5', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12417', {'48': '14130', '60': '14124', '58': '14125', '50': '14129', '52': '14128', '56': '14126', '54': '14127'}], ['Визель П3-3479/3', ['48', '50', '52', '54', '56', '58', '60'], '4400', '12405', {'48': '12409', '60': '12406', '54': '14133', '50': '12408', '52': '14134', '56': '14132', '58': '12407'}], ['Авигаль-П-409-1', ['52', '54'], '3360', '12388', {'52': '12391', '54': '12390'}], ['Авигаль-П-127', ['52', '54', '56'], '2600', '12362', {'52': '14742', '56': '12366', '54': '12367'}], ['Прима 4035', ['48', '54'], '3780', '12173', {'48': '12181', '54': '12178'}], ['Новита 589 зеленый', ['48', '50', '52', '54', '56'], '3000', '12046', {'50': '12050', '52': '12049', '56': '12047', '54': '12048', '48': '12051'}], ['Новита 588 желтый', ['48', '50', '52', '54', '56', '58'], '3200', '12036', {'48': '12042', '58': '12037', '50': '12041', '52': '12040', '56': '12038', '54': '12039'}], ['Новита 587 дымчато-сиреневый', ['48', '50', '52', '54', '56', '58'], '3200', '12016', {'48': '12022', '58': '12017', '50': '12021', '52': '12020', '56': '12018', '54': '12019'}], ['Новита 587 дымчато-розовый', ['48', '50', '52', '54', '58'], '3200', '12006', {'50': '12011', '52': '12010', '48': '12012', '58': '12007', '54': '12009'}], ['Новита 581 белые цветы', ['50', '52', '54', '56'], '3300', '11981', {'50': '11988', '52': '11987', '56': '11985', '54': '11986'}], ['Авигаль-П-506-2', ['54', '56', '58', '60', '62', '64', '66'], '2900', '11970', {'60': '11974', '58': '11975', '66': '11971', '64': '11972', '56': '11976', '62': '11973', '54': '11977'}], ['Авигаль-П-700-1', ['54', '56', '58', '64', '66'], '3700', '11941', {'66': '11942', '56': '11946', '64': '11943', '58': '11945', '54': '11947'}], ['Авигаль-П-327-1', ['52', '54', '56', '58'], '2200', '11931', {'52': '11938', '56': '11936', '54': '11937', '58': '14938'}], ['Визель П4-3350/2', ['48', '50', '52', '54', '56'], '4200', '11874', {'50': '11877', '52': '11876', '48': '11878', '56': '14784', '54': '11875'}], ['Визель П3-3494/3', ['48', '50', '52', '54'], '3800', '11851', {'50': '11857', '52': '11856', '48': '11858', '54': '11855'}], ['Авигаль-П-264-1', ['56', '58', '60', '62', '64', '66'], '3300', '11810', {'64': '11813', '58': '11815', '66': '11814', '60': '11811', '56': '11816', '62': '11812'}], ['Авигаль-П-264-2', ['50', '52', '54', '56', '58', '60', '62', '64', '66'], '3300', '11793', {'50': '11807', '64': '11800', '58': '11803', '66': '11799', '60': '11802', '52': '11806', '56': '11804', '62': '11801', '54': '11805'}], ['Авигаль-П-264-3', ['58', '62', '64', '66'], '3300', '11785', {'66': '11786', '64': '11787', '62': '11788', '58': '11789'}], ['Авигаль-П-871-1', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '11773', {'60': '11777', '54': '11774', '66': '11781', '64': '11779', '52': '11778', '56': '11775', '62': '11780', '58': '11776'}], ['Авигаль-П-871', ['52', '54', '56', '58', '60', '62', '64', '66'], '3700', '11761', {'60': '11765', '54': '11768', '66': '11762', '64': '11763', '52': '11769', '56': '11767', '62': '11764', '58': '11766'}], ['Авигаль-П-867-1', ['52', '54', '56', '58', '60', '62', '64'], '3200', '11568', {'60': '11572', '58': '11573', '64': '11570', '52': '11576', '56': '11574', '62': '11571', '54': '11575'}], ['Авигаль-П-867', ['52', '54', '56', '58', '60', '62', '64'], '3200', '11555', {'60': '11559', '58': '11560', '64': '11557', '52': '11563', '56': '11561', '62': '11558', '54': '11562'}], ['Авигаль-П-893-1', ['50', '52', '54', '56', '58', '60', '62'], '3300', '11542', {'60': '11545', '54': '11548', '50': '11550', '52': '11549', '56': '11547', '62': '11544', '58': '11546'}], ['Авигаль-П-893', ['50', '52', '54', '56', '58', '60', '62'], '3300', '11530', {'60': '11533', '54': '11536', '50': '11538', '52': '11537', '56': '11535', '62': '11532', '58': '11534'}], ['Авигаль-П-709', ['52', '54', '62', '64', '66', '68'], '2200', '11504', {'64': '11508', '54': '11513', '66': '11507', '68': '11506', '62': '11509', '52': '11514'}], ['Визель П3-3584/1', ['48', '50', '52', '54', '60'], '3000', '11404', {'50': '11410', '52': '11409', '48': '11411', '60': '15667', '54': '11408'}], ['Визель П3-3585/3', ['48', '50', '52', '54', '56', '58', '60'], '3800', '11390', {'48': '11397', '60': '11391', '58': '11392', '50': '11396', '52': '11395', '56': '11393', '54': '11394'}], ['Авигаль-П-705', ['52', '54', '56', '60'], '2200', '11351', {'52': '11356', '56': '11354', '60': '11353', '54': '11355'}], ['Авигаль-П-705-1', ['52', '54', '56', '58', '60', '62'], '2200', '11340', {'60': '11343', '54': '11346', '52': '11347', '56': '11345', '62': '11342', '58': '11344'}], ['Авигаль-П-869-2', ['50', '52', '54', '60', '62'], '2900', '11316', {'50': '11322', '52': '11320', '60': '11318', '54': '11321', '62': '11323'}], ['Авигаль-П-869-1', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900', '11304', {'60': '11308', '54': '11311', '50': '11312', '64': '11307', '52': '11310', '56': '11306', '62': '11305', '58': '11309'}], ['Авигаль-П-869', ['50', '52', '54', '56', '58', '60', '62', '64'], '2900', '11292', {'60': '11295', '58': '11296', '50': '11300', '64': '11293', '52': '11299', '56': '11297', '62': '11294', '54': '11298'}], ['Авигаль-П-702', ['52', '54', '56', '58', '60', '62'], '2400', '11256', {'60': '11258', '54': '11261', '52': '11262', '56': '11260', '62': '11257', '58': '11259'}], ['Авигаль-П-270-3', ['52', '54'], '2500', '11213', {'52': '11224', '54': '14745'}], ['Авигаль-П-270', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500', '11198', {'70': '11199', '60': '11204', '54': '11207', '68': '11202', '66': '11201', '64': '11200', '52': '11208', '56': '11206', '62': '11203', '58': '11205'}], ['Авигаль-П-270-1', ['52', '54', '56', '58', '60', '62', '64', '66', '68', '70'], '2500', '11184', {'56': '11192', '60': '11190', '54': '11193', '52': '11194', '66': '11187', '64': '11188', '68': '11186', '70': '11185', '62': '11189', '58': '11191'}], ['Новита 590 цветная абстракция', ['48', '50', '52', '54', '56'], '3200', '11169', {'50': '11173', '52': '11172', '56': '11170', '54': '11171', '48': '11174'}], ['Новита 584 мятный', ['48', '50', '52', '54', '56'], '2580', '11149', {'50': '11153', '52': '11152', '56': '11150', '54': '11151', '48': '11154'}], ['Новита 582 синий орнамент', ['48', '50', '52', '54', '56'], '3100', '11137', {'50': '11141', '52': '11140', '56': '11138', '54': '11139', '48': '11142'}], ['Новита 580 изумрудный', ['50', '52', '54', '56'], '3000', '11127', {'50': '11136', '52': '11135', '56': '11133', '54': '11134'}], ['Авигаль-П-706-3', ['52', '56', '72', '74'], '2900', '11111', {'74': '11120', '72': '11121', '52': '11118', '56': '11112'}], ['Авигаль-П-706-1', ['52', '54', '56', '58', '60', '62', '64', '68', '70', '72', '74'], '2900', '11068', {'58': '11088', '74': '11080', '60': '11087', '54': '11090', '64': '11085', '72': '11081', '52': '11091', '56': '11089', '62': '11086', '68': '11083', '70': '11082'}], ['Авигаль-П-706-2', ['54', '56', '66', '72'], '2900', '11050', {'66': '11057', '72': '11055', '56': '11062', '54': '11063'}], ['Авигаль-П-503', ['50', '52', '54', '56', '58', '60', '62', '64'], '2960', '11039', {'60': '11045', '54': '11048', '50': '11041', '64': '11043', '52': '11049', '56': '11047', '62': '11044', '58': '11046'}], ['Новита 579 полоска', ['48', '50', '52', '54', '56'], '3100', '11011', {'50': '11015', '52': '11014', '56': '11012', '54': '11013', '48': '11016'}], ['Авигаль-П-503-1', ['48', '50', '52', '54', '56', '58', '60', '62', '64', '66'], '2960', '10916', {'50': '10926', '48': '10927', '60': '10921', '54': '10924', '66': '10918', '64': '10919', '52': '10925', '56': '10923', '62': '10920', '58': '10922'}], ['Авигаль-П-100-1', ['52', '54', '56', '58', '60', '62', '64'], '2500', '10905', {'60': '10908', '54': '10906', '64': '10912', '52': '10909', '56': '10910', '62': '10911', '58': '10907'}], ['Авигаль-П-100', ['52', '54', '56', '58', '60', '62', '64'], '2500', '10894', {'60': '10897', '54': '10900', '64': '10895', '52': '10901', '56': '10899', '62': '10896', '58': '10898'}], ['Авигаль-П-488-1', ['52', '54', '58', '60', '62', '66'], '2700', '10779', {'60': '10785', '54': '10788', '66': '10782', '52': '10789', '62': '10784', '58': '10786'}], ['Прима 2754-4', ['52', '54', '56', '58', '60', '62', '64'], '4400', '10575', {'60': '10578', '58': '10579', '64': '10576', '52': '10582', '56': '10580', '62': '10577', '54': '10581'}], ['Прима 2856', ['56', '58', '60', '62', '64', '68'], '3400', '10551', {'64': '10553', '58': '15096', '60': '15095', '68': '10552', '56': '15681', '62': '10554'}], ['Прима 4018', ['52', '54', '56', '60', '62', '64'], '3200', '10524', {'60': '10529', '54': '10531', '64': '10527', '52': '10532', '56': '10530', '62': '10528'}], ['Прима 4001', ['44', '46', '48', '50', '52'], '5800', '10479', {'46': '15682', '50': '10484', '52': '10486', '44': '10488', '48': '10483'}], ['Новита 566', ['50', '52', '54', '56'], '3100', '10237', {'50': '10242', '52': '13249', '56': '10239', '54': '10240'}], ['Визель-П4-2571/9', ['48', '50', '52', '54', '56', '58', '60'], '4200', '9806', {'48': '9813', '60': '9807', '54': '9810', '50': '9812', '52': '9811', '56': '9809', '58': '9808'}], ['Визель-П4-2571/13', ['48', '50', '52', '54', '56', '58', '60'], '4200', '9774', {'48': '9787', '60': '9781', '54': '9784', '50': '9786', '52': '9785', '56': '9783', '58': '9782'}], ['Визель-П4-2571/11', ['48', '50', '52', '54'], '4200', '9760', {'50': '9766', '52': '9765', '48': '9767', '54': '9764'}], ['Визель-П5-3506/8', ['48', '50', '52', '54', '56', '58', '60'], '3800', '9727', {'48': '9734', '60': '9728', '58': '9729', '50': '9733', '52': '9732', '56': '9730', '54': '9731'}], ['Визель-П5-3506/6', ['48', '50', '52', '54', '56', '58', '60'], '3800', '9711', {'48': '9718', '60': '9712', '58': '9713', '50': '9717', '52': '9716', '56': '9714', '54': '9715'}], ['Визель-П5-3506/4', ['54', '56', '58', '60'], '3800', '9698', {'56': '9701', '60': '9699', '58': '9700', '54': '9702'}], ['Визель-П5-3506/10', ['52', '56', '58'], '3800', '9682', {'52': '9687', '56': '9685', '58': '9684'}], ['Визель-П3-3557/1', ['50', '52', '54'], '4000', '9668', {'50': '9680', '52': '9679', '54': '9678'}], ['Визель-П5-3563/1', ['48', '50', '52', '54', '56', '58'], '4200', '9570', {'48': '9577', '58': '9572', '50': '9576', '52': '9575', '56': '9573', '54': '9574'}], ['Визель П4-3559/1', ['48', '50', '52', '54', '56', '58', '60'], '3400', '9372', {'48': '9379', '60': '9373', '58': '9374', '50': '9378', '52': '9377', '56': '9375', '54': '9376'}], ['Новита 573', ['48', '50', '54', '56'], '3200', '9291', {'50': '9295', '56': '9292', '54': '9293', '48': '9296'}], ['Новита 569', ['48', '50', '52', '54', '56'], '3000', '9283', {'50': '9287', '52': '9286', '48': '9288', '56': '9284', '54': '9285'}], ['Прима 2982', ['52', '54', '56', '58'], '3520', '9070', {'52': '9074', '56': '9072', '54': '9073', '58': '9071'}], ['Визель-П4-2571/5', ['48', '50', '52', '54', '56', '58', '60'], '4000', '8771', {'48': '8778', '60': '8772', '58': '8773', '50': '8777', '52': '8776', '56': '8774', '54': '8775'}], ['Новита 556', ['50', '52', '54', '56'], '3100', '8633', {'50': '14779', '52': '14778', '56': '8635', '54': '8636'}], ['Визель П4-3423/5', ['52', '54', '56', '58'], '3320', '8496', {'52': '8501', '56': '8499', '58': '8498', '54': '8500'}], ['Прима 2662', ['46', '48', '50', '54', '56'], '4200', '8390', {'50': '14747', '48': '15683', '56': '8391', '54': '8392', '46': '15684'}], ['Прима 2977', ['48', '50', '52', '54', '56', '58'], '3580', '8197', {'48': '8203', '58': '8198', '50': '8202', '52': '8201', '56': '8199', '54': '8200'}], ['Новита 485/1', ['50', '52', '54', '56', '58'], '3300', '7629', {'50': '7640', '52': '7639', '56': '7637', '54': '7638', '58': '7636'}], ['Новита 547', ['48', '50', '52', '54'], '3200', '7602', {'50': '7606', '52': '7605', '48': '7607', '54': '7604'}], ['Новита 401', ['48', '50', '52', '54', '56'], '2600', '7443', {'50': '7447', '52': '7446', '56': '7444', '54': '7445', '48': '7448'}], ['Новита 355/1 морская волна', ['46', '48', '52', '56'], '3100', '7369', {'52': '7374', '46': '7371', '56': '7372', '48': '7370'}], ['Новита 355/1 розовая пудра', ['46', '50'], '3100', '7360', {'50': '13961', '46': '7366'}], ['Прима 2874', ['52', '56', '60', '62', '64', '66', '68', '70'], '4400', '7041', {'70': '13940', '64': '7044', '68': '13941', '66': '13942', '60': '7046', '52': '13945', '56': '13944', '62': '7045'}], ['Прима 2877', ['48', '54', '56', '58'], '4200', '7029', {'48': '7036', '56': '12401', '54': '7033', '58': '7031'}], ['Новита 550', ['48', '50', '52', '54', '56'], '3100', '6931', {'50': '6935', '52': '6934', '56': '6932', '54': '6933', '48': '6936'}], ['Прима 2906', ['44', '46', '54', '56', '58', '64'], '3200', '6741', {'46': '7289', '64': '7280', '54': '9034', '44': '7290', '56': '9033', '58': '7283'}], ['Прима 2898', ['48', '50', '52', '54', '62'], '3600', '6729', {'50': '6735', '52': '6734', '48': '6736', '54': '6733', '62': '11758'}], ['Прима 2935', ['48', '50', '52', '54', '56', '58'], '3640', '6605', {'48': '6610', '54': '8562', '50': '6609', '52': '8561', '56': '8563', '58': '8564'}], ['Новита 526', ['44', '46', '52'], '2800', '6366', {'46': '6371', '52': '6368', '44': '6372'}], ['Новита-321 алый', ['54'], '2000', '6152', {'54': '6154'}], ['Новита-519', ['48', '50'], '3100', '5522', {'50': '5526', '48': '5527'}], ['Новита-529', ['50', '52', '54', '56'], '3100', '5467', {'50': '5471', '52': '5470', '56': '5468', '54': '5469'}], ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '2000', '5011', {'66': '9645'}], ['Визель-П2-3477/1', ['52', '54', '58'], '3800', '4493', {'52': '4498', '58': '4495', '54': '4497'}], ['Новита-516', ['50', '52', '54', '56', '58'], '3100', '4192', {'50': '4197', '52': '4196', '56': '4194', '58': '4193', '54': '4195'}], ['Новита-334', ['48', '50', '52', '54', '56', '58'], '3200', '4152', {'48': '4158', '58': '4153', '50': '4157', '52': '4156', '56': '4154', '54': '4155'}], ['Новита-345/1', ['48', '50', '52', '54', '56'], '3000', '3742', {'50': '3746', '52': '3745', '56': '3743', '54': '3744', '48': '3747'}], ['Новита-496', ['50', '52', '54', '56', '58'], '3200', '3719', {'50': '3724', '52': '3723', '56': '3721', '58': '3720', '54': '3722'}], ['Новита-511', ['50', '52', '54', '56'], '3200', '3662', {'50': '3666', '52': '3665', '56': '3663', '54': '3664'}], ['Олеся-28001-1', ['54', '56'], '2000', '3462', {'56': '7297', '54': '3465'}], ['Новита-408', ['50', '58'], '3000', '3399', {'50': '11372', '58': '3400'}], ['Джетти-Б092-2', ['54'], '2000', '2287', {'54': '2290'}], ['Джетти-Б092-4', ['54'], '2000', '2280', {'54': '2283'}], ['Джетти-Б163-4', ['58'], '2000', '2213', {'58': '9658'}], ['Со-СЕВАСТЬЯНА оригами', ['52'], '2000', '2096', {'52': '9639'}], ['ЕО-24042-1', ['54'], '2000', '1865', {'54': '1870'}], ['JБ-Б165-1', ['56'], '2000', '1784', {'56': '1792'}], ['JБ-Б201-2', ['60'], '2000', '1699', {'60': '9656'}]],
                      [['Визель-П3-3468/4', ['54'], '2000', '4555', {'54': '12729'}],
                       ['Новита-509', ['50'], '2000', '3711', {'50': '3716'}],
                       ['Визель-П4-3469/1', ['56'], '2000', '4426', {'56': '13274'}],
                       ['Новита-242', ['48', '50', '52', '54', '56', '58', '60'], '0', '4208', {}],
                       ['Новита-393В', ['56'], '2000', '4200', {'56': '4202'}],
                       ['Олеся-24019-1', ['56'], '2000', '4113', {'56': '12138'}],
                       ['Новита-492', ['50'], '2000', '3070', {'50': '9647'}],
                       ['Олеся-27026-1', ['50', '52'], '2000', '2741', {'50': '2746', '52': '2745'}],
                       ['Джетти-Б005-1', ['48', '50', '52', '54', '56', '58', '60'], '0', '2303', {}],
                       ['ЕО-27014-1', ['50'], '2000', '1893', {'50': '1902'}],
                       ['ЕО-27018-1', ['52'], '2000', '1873', {'52': '1877'}],
                       ['СО-ЖЮЛИ нежная орхидея', ['52', '62'], '2000', '1795', {'52': '9640', '62': '9641'}],
                       ['Новита-321 алый', ['54'], '2000', '6152', {'54': '6154'}],
                       ['Со-ДОРОФЕЯ БУТЫЛОЧНЫЙ', ['66'], '2000', '5011', {'66': '9645'}],
                       ['Визель-Др5-152/1', ['60'], '2000', '3941', {'60': '9778'}],
                       ['Визель-Кн5-96/1', ['50'], '2000', '3915', {'50': '3917'}],
                       ['Олеся-28001-1', ['54', '56'], '2000', '3462', {'56': '7297', '54': '3465'}],
                       ['Джетти-Б092-2', ['54'], '2000', '2287', {'54': '2290'}],
                       ['Джетти-Б092-4', ['54'], '2000', '2280', {'54': '2283'}],
                       ['Джетти-Б163-4', ['58'], '2000', '2213', {'58': '9658'}],
                       ['Со-СЕВАСТЬЯНА оригами', ['52'], '2000', '2096', {'52': '9639'}],
                       ['ЕО-24042-1', ['54'], '2000', '1865', {'54': '1870'}],
                       ['JБ-Б165-1', ['56'], '2000', '1784', {'56': '1792'}],
                       ['JБ-Б201-2', ['60'], '2000', '1699', {'60': '9656'}]], driver)
        # for dress in site:
        #     goods_data.append(dress)
    # for site in blouse_pages:
    #     compare_dress(site, bigmoda_pages[1], bigmoda_pages[2])
    # del_item(goods_data)
