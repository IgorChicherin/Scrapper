import time
import re

import requests
from bs4 import BeautifulSoup

from progress_bar import printProgressBar


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
