# woocommerce REST API
# https://woocommerce.github.io/woocommerce-rest-api-docs
import json
from woocommerce import API
wcapi = API(
    url='http://localhost',
    consumer_key='ck_9d39983c92489dcc729ebfb3f2e1baaec25c5744',
    consumer_secret='cs_854ebadd61e59317ba6e0af3417c29cb830409d7',
    wc_api='v3'
)

# r = wcapi.get('products/15542')
# with open('product_dump.json', 'w') as file:
#     json.dump(r.json(), file, indent=2, ensure_ascii=False)

# data= {
#        "status": "publish"
# }
#
# wcapi.put('products/15542', data)
#
# for page in range(1, 100):
#     products = wcapi.get('products/?page=' + str(page))
#     for product in products.json():
#         if product['id']:
#             variations = [size['attributes'][0]['option'] for size in product['variations']]
#             print([product['id'],product['sku'], variations])
#         else:
#             break
# product_attrs = wcapi.get('products/?attributes=15753').json()
# print(product_attrs)
# for variation in product_attrs[0]['variations']:
#     if variation['attributes'][0]['option'] == '48':
#         product_attrs[0]['variations'].remove(variation)
#         product_attrs[0]['attributes'][1]['options'].remove('48')
#
# print(wcapi.put('products/attributes/15753', data=product_attrs).json())

# print(wcapi.get('products/15753/variations/15762').json())

# product_attrs = wcapi.get("products/?attributes=15753").json()
# with open('product_attrs_dump.json', 'w') as file:
#     json.dump(product_attrs, file, indent=2, ensure_ascii=False)
# print(products)

wcapi