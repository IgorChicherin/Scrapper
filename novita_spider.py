import time
import re

import requests
import progressbar
from bs4 import BeautifulSoup


def _create_sizes_dict(color_list, sizes_list, sizes_accepted):
    '''
    Create dict of color and sizes of item
    :param color_list: list
    :param sizes_list: list
    :param sizes_accepted: list
    :return: dict
    '''
    i = 0
    temp_dict = dict()
    for color in color_list:
        temp_list = list()
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
    result = list()
    i = 0
    l = len(items_link_list)
    bar = progressbar.ProgressBar(max_value=len(items_link_list),
                                  widgets=['Novita Parsing: ',
                                           progressbar.Bar(left='|', marker='█', right='|'),
                                           progressbar.Percentage(), ' ',
                                           progressbar.AdaptiveETA()])
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        data = dict()
        try:
            data['name'] = re.search(r'(?<=№)(\d+/\d+)|(?<=№)(\d+)', soup.h1.text.strip()).group(0)
            data['type'] = soup.h1.text.strip().split(' ')
            if 'Акция' in data['type'] and '\'Одна' not in data['type'] and '50%' not in data['type']:
                data['type'] = data['type'][2]
            elif '50%' in data['type']:
                data['type'] = data['type'][4]
            elif '\'Одна' in data['type']:
                data['type'] = data['type'][4]
            else:
                data['type'] = data['type'][0]
            if data['type'] == 'Платье' or data['type'] == 'Блузка' or data['type'] == 'Туника':
                colors = soup.find_all('td', {'class': 'col-color'})
                data['color_list'] = [color.text.strip() for color in colors if color.text.strip() != 'Цвет/размер']
                data['sizes_list'] = soup.find_all('td', {'class': 'inv'})
                data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
                data['color_size'] = {color: data['sizes_list'].copy() for color in data['color_list']}
                data['sizes_accepted'] = soup.find_all('td', {'class': 'tdforselect'})
                data['sizes_accepted'] = ['disabled' if 'disabled' in size_accepted['class'] else 'enabled' for
                                          size_accepted in
                                          data['sizes_accepted']]
                data['price'] = soup.find('div', {'class': 'value'}).text.replace(',', '').split('.')[0]
                if (data['type'] == 'Блузка' or data['type'] == 'Туника') and int(data['price']) < 2300:
                    data['price'] = '2300'
                elif data['type'] == 'Платье' and int(data['price']) < 2500:
                    data['price'] = '2500'
                color_size_tags = _create_sizes_dict(data['color_list'], data['sizes_list'], data['sizes_accepted'])
                for key, value in color_size_tags.items():
                    for item in range(len(value)):
                        if value[item] == 'disabled':
                            data['color_size'][key].pop(color_size_tags[key].index(value[item]))
                for key in data['color_size']:
                    # print(['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'], data['type']])
                    result.append(
                        ['Новита ' + data['name'] + ' ' + str(key), data['color_size'][key], data['price'],
                         data['type'], False])
        except AttributeError:
            with open('errors.txt', 'a', encoding='utf-8') as err_file:
                err_file.write('Ошибка в карточке: %s \n' % (link))
            i += 1
            bar.update(i)
            continue
        time.sleep(0.1)
        i += 1
        bar.update(i)
    return result
