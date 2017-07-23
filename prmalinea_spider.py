import time
import re

import requests
from bs4 import BeautifulSoup

from progress_bar import printProgressBar


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
                result.append(
                    ['Прима ' + data['name'], data['sizes_list'], data['price'], data['type'], data['is_new']])
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
