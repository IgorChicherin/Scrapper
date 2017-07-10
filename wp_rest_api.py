# woocommerce REST API need woocommerce v3
# https://woocommerce.github.io/woocommerce-rest-api-docs5
import json
from woocommerce import API

# home api keys
#  consumer_key='ck_b7888f4363792ea77f8d9a353f0bb58fc5c69696',
#  consumer_secret='cs_a417ab12b28261c9581a713c0d60a8723804141e',

# work api keys
# consumer_key = 'ck_4a8ee2b82d4a58f47c93bcc85b1438f2ea4396ca',
# consumer_secret = 'cs_448b32091b94d7e949690b65bfdc1520cddd0fe5',


wcapi = API(
    url='http://localhost',
    consumer_key='ck_b7888f4363792ea77f8d9a353f0bb58fc5c69696',
    consumer_secret='cs_a417ab12b28261c9581a713c0d60a8723804141e',
    wp_api=True,
    version="wc/v2",
)

# data = {
#     'description': '',
#     'regular_price': '2500',
#     'tax_status': 'taxable',
#     'tax_class': '',
#     'attributes': [
#     {
#       "id": 1,
#       "name": "Размер",
#       "option": "66"
#     }
#   ],
# }

# url = 'products/15542/variations'

# r = wcapi.post(url, data=data)
#
# r = wcapi.get('products/15542/variations/15829')
# with open('product_vars_dump.json', 'w') as file:
#     json.dump(r.json(), file, indent=2, ensure_ascii=False)
# print(r.json())

# r = wcapi.delete('products/15542/variations/15829')

# attributes = wcapi.get('products/15542/').json()
# with open('product_attrs_dump.json', 'w') as file:
#     json.dump(attributes['attributes'], file, indent=2, ensure_ascii=False)

# for attribute in attributes['attributes']:
#     if attribute['name'] == 'Размер':
#         attribute['options'].append('68')
#         print(attribute['options'])
# with open('product_attrs_dump.json', 'w') as file:
#     json.dump(attributes, file, indent=2, ensure_ascii=False)
# r = wcapi.put('products/15542', attributes)
# print(r.json())

# product = wcapi.get('products/13022').json()
# with open('product_dump.json', 'w') as file:
#     json.dump(product, file, indent=2, ensure_ascii=False)
# print(product['categories'])

data = {
    'name': 'Платье Новита 666',
    'type': 'variable',
    'status': 'private',
    'catalog_visibility': 'visible',
    'sku': 'Новита 666',
    'regular_price': '666',
    'categories': [
        {
            'slug': 'platya-bolshih-razmerov',
            'name': 'Платья больших размеров',
            'id': 11
        }
    ],
    'attributes': [
        {
            'position': 0,
            'name': 'Цвет',
            'visible': False,
            'options': ['Мультиколор'],
            'id': 2,
            'variation': False
        },
        {
            'position': 1,
            'name': 'Размер',
            'visible': True,
            'options': ['48', '50', '52', '54', '56', '58'],
            'id': 1,
            'variation': True
        },
        {
            'position': 2,
            'name': 'Состав',
            'visible': False,
            'options': ['Полиэстер'],
            'id': 3,
            'variation': False
        }

    ]
}
# product = wcapi.post('products', data).json()
# print(wcapi.get('products/15753').json()['attributes'])
# wcapi.delete('products/15796')

products_list = []
for page in range(1, 100):
    products = wcapi.get('products/?page=%s' % (page))
    for product in products.json():
        if product['id']:
            products_list.append([product['sku'], product['id']])
            print([product['sku'], product['id']])

    products.status_code
print(products_list)