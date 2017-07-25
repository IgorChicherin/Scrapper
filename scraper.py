import os

from woocommerce import API

from novita_spider import novita_parse
from prmalinea_spider import primalinea_parse
from avigal_spider import avigal_parse
from wisell_spider import wisell_parse
from krasa_parser import krasa_parse
from bigmoda_spider import bigmoda_parse
from woo_sync_db import compare_dress, del_item


def main(wcapi, answer):
    '''
    Main module
    :param wcapi: woocommerce API object
    :param answer: int
    :return: boolean
    '''

    goods_data = list()
    if int(answer) == 1:
        dress_pages = [novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/'),
                       novita_parse('http://novita-nsk.ru/shop/aktsii/'),
                       novita_parse('http://novita-nsk.ru/index.php?route=product/category&path=1_19'),
                       novita_parse('http://novita-nsk.ru/shop/yubki/'),
                       primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'),
                       avigal_parse('http://avigal.ru/dress/'),
                       wisell_parse('http://wisell.ru/catalog/platya/'),
                       krasa_parse('krasa.csv')]
        blouse_pages = [novita_parse('http://novita-nsk.ru/shop/bluzy/'),
                        primalinea_parse('http://primalinea.ru/catalog/category/43/all/0'),
                        avigal_parse('http://avigal.ru/blouse-tunic/'),
                        wisell_parse('http://wisell.ru/catalog/tuniki_bluzy/')]
        bigmoda_pages = [bigmoda_parse('http://big-moda.com/product-category/platya-bolshih-razmerov/'),
                         bigmoda_parse('http://big-moda.com/product-category/bluzki-bolshih-razmerov/'),
                         bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')]
        # bigmoda_pages = [bigmoda_parse('http://localhost/product-category/platya-bolshih-razmerov/'),
        #                  bigmoda_parse('http://localhost/product-category/bluzki-bolshih-razmerov/'),
        #                  bigmoda_parse('http://localhost/product-category/rasprodazha-bolshie-razmery/')]
        for site in dress_pages:
            compare_dress(site, bigmoda_pages[0], bigmoda_pages[1], wcapi)
        for site in blouse_pages:
            compare_dress(site, bigmoda_pages[1], bigmoda_pages[2], wcapi)
        return True
    elif int(answer) == 2:
        dress_pages = [novita_parse('http://novita-nsk.ru/shop/zhenskie-platja-optom/'),
                       novita_parse('http://novita-nsk.ru/shop/aktsii/'),
                       novita_parse('http://novita-nsk.ru/index.php?route=product/category&path=1_19'),
                       novita_parse('http://novita-nsk.ru/shop/yubki/'),
                       primalinea_parse('http://primalinea.ru/catalog/category/42/all/0'),
                       avigal_parse('http://avigal.ru/dress/'),
                       wisell_parse('http://wisell.ru/catalog/platya/'),
                       krasa_parse('krasa.csv')]
        blouse_pages = [novita_parse('http://novita-nsk.ru/shop/bluzy/'),
                        primalinea_parse('http://primalinea.ru/catalog/category/43/all/0'),
                        avigal_parse('http://avigal.ru/blouse-tunic/'),
                        wisell_parse('http://wisell.ru/catalog/tuniki_bluzy/')]
        bigmoda_pages = [bigmoda_parse('http://big-moda.com/product-category/platya-bolshih-razmerov/'),
                         bigmoda_parse('http://big-moda.com/product-category/bluzki-bolshih-razmerov/'),
                         bigmoda_parse('http://big-moda.com/product-category/rasprodazha-bolshie-razmery/')]
        for site in dress_pages:
            for dress in site:
                goods_data.append(dress)
        for site in blouse_pages:
            for blouse in site:
                goods_data.append(blouse)
        del_item(goods_data, bigmoda_pages, wcapi)
        return True
    else:
        return False


if __name__ == '__main__':

    files = ['добавить удалить размеры.txt', 'добавить удалить карточки.txt', 'errors.txt']
    for file in files:
        if os.path.exists(file):
            os.remove(file)

    with open('keys.txt', 'r') as file:
        keys = [line.strip() for line in file]

    consumer_key = keys[0]
    consumer_secret = keys[1]

    wcapi = API(
        url='http://big-moda.com',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        wp_api=True,
        version="wc/v2",
    )
    answ = input('[1] - Синхронизировать размеры \n[2] - Добавить новинки \nВведите ответ: ')
    main(wcapi, answer=answ)
