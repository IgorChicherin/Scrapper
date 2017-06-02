import requests
from bs4 import BeautifulSoup


def novita_parse():
    url = 'http://novita-nsk.ru/shop/zhenskie-platja-optom/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    items_link_list = soup.find_all('div', {'class': 'name'})
    for link in items_link_list:
        url = link.find('a').get('href')
        r = requests.get(url)
        soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
        name = soup.h1.text.strip()
        color = soup.find_all('td', {'class': 'col-color'})
        color = color[1].text.strip()
        sizes_list = soup.find_all('td', {'class': 'inv'})
        sizes_list = [size.text.strip() for size in sizes_list]
        with open('res.txt', 'a', encoding='utf-8') as result_file:
            result_file.write('Название: {} Цвет: {} Размеры: {} \n'.format(name, color, sizes_list))


novita_parse()
