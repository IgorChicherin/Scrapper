import requests
from bs4 import BeautifulSoup
import os


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
        print('Название: {} Цвет\Размер: {} Цена: {} \n'.format(data['name'], data['color_size'], data['price']))
        with open('res.txt', 'a+', encoding='utf-8') as result_file:
            result_file.write(
                'Название: {} Цвет\Размер: {}  Цена: {}\n'.format(data['name'], data['color_size'], data['price']))


if __name__ == '__main__':
    try:
        os.remove('res.txt')
    except FileNotFoundError:
        pass
    novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
    novita_parse('http://novita-nsk.ru/shop/bluzy/')