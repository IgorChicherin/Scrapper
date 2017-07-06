# woocommerce REST API
# https://woocommerce.github.io/woocommerce-rest-api-docs
import json
from woocommerce import API

wcapi = API(
    url='http://localhost',
    consumer_key='ck_9d39983c92489dcc729ebfb3f2e1baaec25c5744',
    consumer_secret='cs_854ebadd61e59317ba6e0af3417c29cb830409d7',
    wp_api=True,
    version='wc/v1'
)

r = wcapi.get('products/15542').json()
with open('product_dump.json', 'w') as file:
    json.dump(r, file, indent=2, ensure_ascii=False)

# data= {
#        "status": "publish"
# }
#
# wcapi.put('products/15542', data)

products = wcapi.get('products').json()
# print([product['sku'] for product in products])
