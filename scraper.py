import requests
import os
import re
import csv
from bs4 import BeautifulSoup


# http://primalinea.ru с авторизацие цены Х2
# http://avigal.ru/ c авторизацией цены Х2 не меньше 2500
# https://wisell.ru/

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
    # TODO подогнать названия платьев под Bigmoda
    '''
    Parsing Novita Site
    :param url: str
    :return: tuple
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('div', {'class': 'name'})
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = re.search(r'(?<=Платье -  )(№\d+)', soup.h1.text.strip()).group(0)
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
            print(data['name'], data['color_size'][key], data['price'])
            yield data['name'], data['color_size'][key], data['price']


def primalinea_parse(url):
    # TODO подогнать названия платьев под Bigmoda
    '''
    Parsing Primalinea Site
    :param url: str
    :return: tuple
    '''
    session = requests.Session()
    payload = {'login_name': 'mail@big-moda.com'}
    r = session.post('http://primalinea.ru/customers/login', payload)
    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('a', {'class': 'catalog-item-link'})
    items_link_list = [item.get('href') for item in items_link_list]
    result = {}
    for link in items_link_list:
        r = session.get(link)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = soup.h1.text.strip()
        price = soup.find('div', attrs={'id': 'catalog-item-description'})
        price = re.search(r'(\d+)', price.p.text.strip().replace(' ', ''))
        data['price'] = int(price.group(0)) * 2
        data['sizes_list'] = soup.find_all('option')
        data['sizes_list'] = [item.text for item in data['sizes_list']]
        print(data['name'], data['sizes_list'], data['price'])
        yield data['name'], data['sizes_list'], data['price']


def avigal_parse(url):
    # TODO подогнать названия платьев под Bigmoda
    '''
    Parsing Avigal Site
    :param url: str
    :return: tuple
    '''
    session = requests.Session()
    payload = {'email': 'Bigmoda.com@gmail.com', 'password': '010101'}
    r = session.post('http://avigal.ru/login/', payload)
    r = session.get(url)
    # page_now = re.search(r'(?<=page=)(\d+)', 'http://avigal.ru/dress/&p_val=[700:2422.5]&limit=100&sort=p.date_added&order=DESC&page=1').group(0)
    soup = BeautifulSoup(r.text, 'lxml')
    data = {}
    data['paginaton'] = soup.find_all('div', {'class': 'pagination'})
    data['paginaton'] = data['paginaton'][0].find_all('li')
    data['paginaton_url'] = []
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
        for link in items_link_list:
            # link = 'http://avigal.ru/index.php?route=product/product&path=63&product_id=2103'
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
                print(data['name'], data['sizes_list'], data['price'])
                yield data['name'], data['sizes_list'], data['price']


def wisell_parse(url):
    # TODO подогнать названия платьев под Bigmoda
    '''
    Parsing Wisell Site
    :param url: str
    :return: tuple
    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    data = {}
    data['paginaton'] = soup.find_all('div', {'class': 'page_navi'})
    pagination_links = data['paginaton'][0].find_all('a', {'class': 'menu_link'})
    data['paginaton'] = [item.get('href') for item in pagination_links]
    data['paginaton_url'] = [url]
    for link in data['paginaton']:
        if 'https://wisell.ru' + link not in data['paginaton_url']:
            data['paginaton_url'].append('https://wisell.ru' + link)
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'image_block'})
        data['item_links'] = ['https://wisell.ru' + link.get('href') for link in data['item_links']]
        data['item_links'].pop(0)
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
            yield data['name'], data['sizes_list'], data['price']


def bimoda_parse(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    data = {}
    data['paginaton_url'] = soup.find_all('a', {'class': 'page-numbers'})
    data['paginaton_url'] = [link.get('href') for link in data['paginaton_url'] if link.text != '→']
    last_page = int(re.search(r'(?<=page/)(\d+)', data['paginaton_url'].pop(-1)).group(0))
    pagination_link = 'https://big-moda.com/product-category/platya-bolshih-razmerov/page/'
    data['paginaton_url'] = [pagination_link + str(link) for link in range(2, last_page + 1)]
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'woocommerce-LoopProduct-link'})
        data['item_links'] = [item.get('href') for item in data['item_links']]
        for item in data['item_links']:
            r = requests.get(item)
            soup = BeautifulSoup(r.text, 'lxml')
            data['name'] =

if __name__ == '__main__':
    # TODO нужен файл корректировок название платья | убрать размер | добавить размер
    # files = ['temp.csv']
    # for file in files:
    #     if os.path.exists(file):
    #         os.remove(file)
    # novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
    # novita_parse('http://novita-nsk.ru/shop/bluzy/')
    # for item in primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'):
    #     print(item)
    # primalinea_parse('http://primalinea.ru/catalog/category/43/all/0')
    # avigal_parse('http://avigal.ru/dress/')
    # avigal_parse('http://avigal.ru/blouse-tunic/')
    # wisell_parse('https://wisell.ru/catalog/platya/')
    # wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')
    bimoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/')
