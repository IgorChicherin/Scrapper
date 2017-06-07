import requests
import os
import re
from bs4 import BeautifulSoup

# http://primalinea.ru с авторизацие цены Х2
# http://avigal.ru/ c авторизацией цены Х2 не меньше 2500
# https://wisell.ru/

def create_sizes_dict(color_list, sizes_list, sizes_accepted):
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
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('div', {'class': 'name'})
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = soup.h1.text.strip()
        colors = soup.find_all('td', {'class': 'col-color'})
        data['color_list'] = [color.text.strip() for color in colors if color.text.strip() != 'Цвет/размер']
        data['sizes_list'] = soup.find_all('td', {'class': 'inv'})
        data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
        data['color_size'] = {color: data['sizes_list'].copy() for color in data['color_list']}
        data['sizes_accepted'] = soup.find_all('td', {'class': 'tdforselect'})
        data['sizes_accepted'] = ['disabled' if 'disabled' in size_accepted['class'] else 'enabled' for size_accepted in
                                  data['sizes_accepted']]
        data['price'] = soup.find('div', {'class': 'value'}).text
        color_size_tags = create_sizes_dict(data['color_list'], data['sizes_list'], data['sizes_accepted'])
        for key, value in color_size_tags.items():
            for item in range(len(value)):
                if value[item] == 'disabled':
                    data['color_size'][key].pop(color_size_tags[key].index(value[item]))
        # print('Название: {} Цвет\Размер: {} Цена: {} \n'.format(data['name'], data['color_size'], data['price']))
        with open('novita.txt', 'a+', encoding='utf-8') as result_file:
            result_file.write(
                'Название: {} Цвет\Размер: {}  Цена: {}\n'.format(data['name'], data['color_size'], data['price']))


def primalinea_parse(url):
    session = requests.Session()
    payload = {'login_name': 'mail@big-moda.com'}
    r = session.post('http://primalinea.ru/customers/login', payload)
    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('a', {'class': 'catalog-item-link'})
    items_link_list = [item.get('href') for item in items_link_list]
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
        with open('primalinea.txt', 'a+', encoding='utf-8') as result_file:
            result_file.write(
                'Название: {} Размер: {}  Цена: {}\n'.format(data['name'], data['sizes_list'], data['price']))


def avigal_parse(url):
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
                with open('avigal.txt', 'a+', encoding='utf-8') as result_file:
                    result_file.write(
                        'Название: {} Размер: {}  Цена: {}\n'.format(data['name'], data['sizes_list'], data['price']))


def wisell_parse(url):
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


if __name__ == '__main__':
    files = ['novita.txt', 'primalinea.txt', 'avigal.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    # novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
    # novita_parse('http://novita-nsk.ru/shop/bluzy/')
    # primalinea_parse('http://primalinea.ru/catalog/category/42/all/0')
    # primalinea_parse('http://primalinea.ru/catalog/category/43/all/0')
    # avigal_parse('http://avigal.ru/dress/')
    # avigal_parse('http://avigal.ru/blouse-tunic/')
    # wisell_parse('https://wisell.ru/catalog/platya/')
    # wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')