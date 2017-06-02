import requests
from bs4 import BeautifulSoup
import lxml


def novita_parse():
    url = 'http://novita-nsk.ru/shop/zhenskie-platja-optom/'
    r = requests.get(url)
    with open('temp.html', 'w', encoding='utf-8') as output_file:
        output_file.write(r.text)

    with open('temp.html', 'r', encoding='utf-8') as fp:
        soup = BeautifulSoup(fp, 'lxml')

    items_link_list = soup.find_all('div', {'class': 'name'})
    # for link in items_link_list:
    url = items_link_list[0].find('a').get('href')
    r =requests.get(url)
    soup = BeautifulSoup(r.text.encode('utf-8'), 'lxml')
    name = soup.h1.string
    # print(url)
    print(name)
    # color = soup.find_all('td', {'class': 'col-color'})
    # color = color[1].string
    # with open('res.txt', 'w', encoding='utf-8') as result_file:
    #     result_file.write('Название: {} Цвет: {}'.format(name, color))

novita_parse()
