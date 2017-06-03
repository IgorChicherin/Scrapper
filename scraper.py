import requests
from bs4 import BeautifulSoup


def novita_parse(url):
    # r = requests.get(url)
    # soup = BeautifulSoup(r.text, 'lxml')
    # items_link_list = soup.find_all('div', {'class': 'name'})
    # for link in items_link_list:
    # url = link.find('a').get('href')
    r = requests.get('http://novita-nsk.ru/shop/zhenskie-platja-optom/plate-210/')
    soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
    data = {}
    data['name'] = soup.h1.text.strip()
    colors = soup.find_all('td', {'class': 'col-color'})
    data['color_list'] = [color.text.strip() for color in colors if color.text.strip() != 'Цвет/размер']
    data['sizes_list'] = soup.find_all('td', {'class': 'inv'})
    data['sizes_list'] = [size.text.strip() for size in data['sizes_list']]
    data['color_size'] = {color: data['sizes_list'].copy() for color in data['color_list']}
    data['sizes_accepted'] = []
    i = 0
    for color in data['color_list']:
        # i =+ len(soup.find_all('td', {'class': 'tdforselect'}))
        data['sizes_accepted']={color : soup.find_all('td', {'class': 'tdforselect'})}
    # if data['sizes_accepted']['сиреневый'] == data['sizes_accepted']['т. синий']:
    #     print('fail!!!')
    # print(chunks(data['sizes_accepted'], len(data['sizes_accepted']) // len(data['sizes_list'])))
    # print(type(data['sizes_accepted']))
    # i = 0
    # for key in data['color_size']:
    #     for avaliable in data['sizes_accepted']:
    #             if 'disabled' in avaliable['class']:
    #                 try:
    #                     data['color_size'][key].pop(data['sizes_accepted'].index(avaliable))
    #                 except IndexError:
    #                     i += len(data['sizes_list'])
    #                     data['color_size'][key].pop(data['sizes_accepted'].index(avaliable)-i)

    # print('Название: {} Цвет\Размер: {} Размеры: {} \n'.format(data['name'], data['color_size'], data['sizes_list']))
    # with open('res.txt', 'a', encoding='utf-8') as result_file:
    #     result_file.write('Название: {} Цвет: {} Размеры: {} \n'.format(name, color_list, sizes_list))


novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/')
