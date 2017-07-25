import time
import re

import requests
import progressbar
from bs4 import BeautifulSoup

from progress_bar import printProgressBar


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
        bar = progressbar.ProgressBar(
            maxval=l,
            widgets=[
                'Wisell Parsing: ',
                progressbar.Bar(left='|', marker='█', right='|'),
                progressbar.Percentage(),
                ' [%s of %s] Complete ' % (j, len(data['paginaton_url'])),
                progressbar.AdaptiveETA()
            ]
        )
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
                        bar.update(i)
                    continue
                data['price'] = soup.find('span', attrs={'class': 'price_val'})
                data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
                data['price'] = int(data['price'].group(0))
                if data['price'] < 1800:
                    i += 1
                    # printProgressBar(i, l, prefix='Wisell Parsing:',
                    #                  suffix='[{} of {}] Complete '.format(j, len(data['paginaton_url'])), length=50)
                    bar.update(i)
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
                                bar.update(i)
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
                        result.append(
                            ['Визель ' + data['name'], sizes_list, data['price'], data['type'], data['is_new']])
            except AttributeError:
                with open('errors.txt', 'a', encoding='utf-8') as err_file:
                    err_file.write('Ошибка в карточке: %s \n' % (item_link))
                continue
            except IndexError:
                continue
            time.sleep(0.1)
            i += 1
            bar.update(i)
        j += 1
    return result
