import requests
import os
import re
from bs4 import BeautifulSoup
import time
import sys


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
    j = 0
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'image_block'})
        data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
        data['item_links'].pop(0)
        # i = 0
        # l = len(data['item_links'])
        # printProgressBar(i, l, prefix='Progress:',
        #                  suffix='[{} of {}]Complete '.format(j, len(data['paginaton_url']) - 1), length=50)
    # data['item_links'] = ['https://wisell.ru/catalog/platya/k4-3646-1/']
        for item_link in data['item_links']:
            r = requests.get(item_link)
            soup = BeautifulSoup(r.text, 'lxml')
            data['price'] = soup.find('span', attrs={'class': 'price_val'})
            data['price'] = re.search(r'(\d+)', data['price'].text.strip().replace(' ', ''))
            data['price'] = int(data['price'].group(0))
            if data['price'] < 1800:
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
                result.append([data['name'], data['sizes_list'], data['price']])
            elif len(data['small_sizes']) == 1:
                print(data['name'], data['sizes_list'], data['price'])
                result.append([data['name'], data['sizes_list'], data['price']])
    return result


wisell_parse('https://wisell.ru/catalog/platya/')
