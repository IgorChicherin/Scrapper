# woocommerce REST API need woocommerce v3
# https://woocommerce.github.io/woocommerce-rest-api-docs
import json
from woocommerce import API

wcapi = API(
    url='http://localhost',
    consumer_key='ck_b7888f4363792ea77f8d9a353f0bb58fc5c69696',
    consumer_secret='cs_a417ab12b28261c9581a713c0d60a8723804141e',
    wp_api=True,
    version="wc/v2",
)

data = {
    'description': '',
    'regular_price': '2500',
    'tax_status': 'taxable',
    'tax_class': '',
    'attributes': [
    {
      "id": 1,
      "name": "Размер",
      "option": "52"
    }
  ],
}

# r = wcapi.post(url, data=data)

r = wcapi.get('products/15542/variations/15829')
with open('product_vars_dump.json', 'w') as file:
    json.dump(r.json(), file, indent=2, ensure_ascii=False)
print(r.json())