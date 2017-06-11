import requests
import os
import re
from bs4 import BeautifulSoup


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
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = re.search(r'(?<=№)(\d+)', soup.h1.text.strip()).group(0)
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
            print(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price']])
            result.append(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price']])
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
    for link in items_link_list:
        r = session.get(link)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = {}
        data['name'] = soup.h1.text.strip()
        data['name'] = data['name'].split(' ')[2] if len(data['name'].split(' ')) > 2 and \
                                                    'new' not in data['name'].split(' ') else data['name'].split(' ')[1]
        price = soup.find('div', attrs={'id': 'catalog-item-description'})
        price = re.search(r'(\d+)', price.p.text.strip().replace(' ', ''))
        data['price'] = int(price.group(0)) * 2
        data['sizes_list'] = soup.find_all('option')
        data['sizes_list'] = [item.text for item in data['sizes_list']]
        print('Прима ' + data['name'].lower(), data['sizes_list'], data['price'])
        result.append(['Прима ' + data['name'], data['sizes_list'], data['price']])
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
                print('Авигаль ' + data['name'], data['sizes_list'], data['price'])
                result.append(['Авигаль ' + data['name'], data['sizes_list'], data['price']])
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
            print('Визель ' + data['name'], data['sizes_list'], data['price'])
            result.append(['Визель ' + data['name'], data['sizes_list'], data['price']])
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
    for page in data['paginaton_url']:
        r = requests.get(page)
        soup = BeautifulSoup(r.text, 'lxml')
        data['item_links'] = soup.find_all('a', {'class': 'woocommerce-LoopProduct-link'})
        data['item_links'] = [item.get('href') for item in data['item_links']]
        for item in data['item_links']:
            r = requests.get(item)
            soup = BeautifulSoup(r.text, 'lxml')
            data['name'] = soup.find('span', {'class': 'sku'}).text
            data['price'] = soup.find('meta', {'itemprop': 'price'})
            data['price'] = data['price']['content']
            data['sizes_list'] = soup.find('div', {'class': 'ivpa_attribute'}, {'class': 'ivpa_text'})
            data['sizes_list'] = data['sizes_list'].find_all('span', {'class': 'ivpa_term'})
            data['sizes_list'] = [item.text.strip() for item in data['sizes_list']]
            print(data['name'], data['sizes_list'], data['price'])
            result.append([data['name'], data['sizes_list'], data['price']])
    return result


def compare_dress(parse_list, bigmoda_dresses, bigmoda_exc):
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
            if bm_drs not in parse_list:
                with open('res.txt', 'a', encoding='utf-8') as file:
                    file.write('Удалить карточку: {}\n'.format(bm_drs[0]))
            elif dress not in bigmoda_dresses:
                with open('res.txt', 'a', encoding='utf-8') as file:
                    file.write('Добавить карточку: {}, {}, {}\n'.format(dress[0], dress[1], dress[2]))
    return True


if __name__ == '__main__':
    # TODO нужен файл корректировок название платья | убрать размер | добавить размер
    files = ['res.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)
    # novita_dresses = novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
    primalinea_dresses = primalinea_parse('http://primalinea.ru/catalog/category/42/all/0')
    # avigal_dresses = avigal_parse('http://avigal.ru/dress/')
    # wisell_dresses = wisell_parse('https://wisell.ru/catalog/platya/')
    bigmoda_dresses = bigmoda_parse('https://big-moda.com/product-category/platya-bolshih-razmerov/')
    # novita_blouse = novita_parse('http://novita-nsk.ru/shop/bluzy/')
    primalinea_blouse = primalinea_parse('http://primalinea.ru/catalog/category/43/all/0')
    # avigal_blouse = avigal_parse('http://avigal.ru/blouse-tunic/')
    # wisell_blouse = wisell_parse('https://wisell.ru/catalog/tuniki_bluzy/')
    bigmoda_blouse = bigmoda_parse('https://big-moda.com/product-category/bluzki-bolshih-razmerov/')
    bigmoda_exc = bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')
    # compare_dress(novita_dresses, bigmoda_dresses, bigmoda_exc)
    compare_dress(primalinea_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(avigal_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(wisell_dresses, bigmoda_dresses, bigmoda_exc)
    # compare_dress(novita_blouse, bigmoda_dresses, bigmoda_exc)
    compare_dress(primalinea_blouse, bigmoda_dresses, bigmoda_exc)
    # compare_dress(avigal_blouse, bigmoda_dresses, bigmoda_exc)
    # compare_dress(wisell_blouse, bigmoda_dresses, bigmoda_exc)
