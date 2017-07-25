import time
import re

import requests
import progressbar
from bs4 import BeautifulSoup


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
        bar = progressbar.ProgressBar(
            maxval=l,
            widgets=[
                'Bigmoda Parsing: ',
                progressbar.Bar(left='|', marker='█', right='|'),
                progressbar.Percentage(),
                ' [%s of %s] Complete ' % (j, len(data['paginaton_url'])),
                progressbar.AdaptiveETA()
            ]
        )
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
                bar.update(i)
                continue
            time.sleep(0.1)
            i += 1
            bar.update(i)
        j += 1
    return result
