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
    # for page in data['paginaton_url']:
    #     r = requests.get(page)
    #     soup = BeautifulSoup(r.text, 'lxml')
    #     data['item_links'] = soup.find_all('a', {'class': 'image_block'})
    #     data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
    #     data['item_links'].pop(0)
    #     i = 0
    #     l = len(data['item_links'])
    #     printProgressBar(i, l, prefix='Progress:',
    #                      suffix='[{} of {}]Complete '.format(j, len(data['paginaton_url']) - 1), length=50)
    data['item_links'] = ['https://wisell.ru/catalog/akcii/posledniy_ekzemplyar/p2-3311-2/',
                          'https://wisell.ru/catalog/bolshie_razmery/p2-3311-3/',
                          'https://wisell.ru/catalog/akcii/posledniy_ekzemplyar/p2-3311-1/',
                          ]
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
        print(data['name'], data['sizes_list'], data['price'])
        result.append([data['name'], data['sizes_list'], data['price']])
    temp = []
    for dress in result:
        if '/' in dress[0]:
            article = dress[0].split('/')
            for item in result:
                if int(article[1]) % 2 != 0:
                    if article[0] + '/' + (str(int(article[1]) - 1)) in item[0]:
                        for dr_size in item[1]:
                            if dr_size not in dress[1]:
                                dress[1].append(dr_size)
                        temp.append([dress[0] + ' ' + item[0], dress[1], dress[2]])
                elif article[0] + '/' + (str(int(article[1]) - 1)) or article[0] not in result:
                    temp.append(dress)
                    break
        else:
            article = dress[0] + '/1'
            for item in result:
                if article in item[0]:
                    for dr_size in item[1]:
                        if dr_size not in dress[1]:
                            dress[1].append(dr_size)
                    temp.append([dress[0] + ' ' + item[0], dress[1], dress[2]])

    print(temp)

    return result


wisell_parse('https://wisell.ru/catalog/platya/')
