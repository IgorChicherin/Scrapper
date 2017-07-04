import re
import requests
from bs4 import BeautifulSoup

with requests.Session() as session:
    payload = {'log': 'olegsent', 'pwd': 'dW#h$x*^EnGOpLhH'}
    r = session.post('http://localhost/wp-login.php', payload)
    r = session.get('http://localhost/wp-admin/post.php?post=13315&action=edit')
    soup = BeautifulSoup(r.text, 'lxml')
    script_block = soup.findAll('script')
    for item in script_block:
        security_id = re.search(r'(?<=security: \')(\w+)', item.text)
        if security_id is not None:
            security = security_id.group(0)
    data = {'action': 'woocommerce_add_variation', 'post_id': '13315', 'loop': '6', 'security': security}
    payload2 = {'attribute_pa_size[6]': '66', 'variable_post_id[6]': '15779', 'variation_menu_order[6]': '1',
                'upload_image_id[6]': '0', 'variable_sku[6]': '', 'variable_enabled[6]': 'on',
                'variable_regular_price[6]': '', 'variable_sale_price[6]': '', 'variable_sale_price_dates_from[6]': '',
                'variable_sale_price_dates_to[6]': '', 'variable_stock[6]': '', 'variable_backorders[6]': '',
                'variable_stock_status[6]': '', 'variable_weight[6]': '', 'variable_length[6]': '', 'variable_width[6]': '',
                'variable_height[6]': '', 'variable_shipping_class[6]': '-1', 'variable_description[6]': '',
                'variable_download_limit[6]': '', 'variable_download_expiry[6]': '', 'default_attribute_pa_size': '',
                'action': 'woocommerce_save_variations', 'security': security, 'product_id': '13315',
                'product-type': 'variable'
                }
    payload = {'post': data}
    # r = session.post('http://localhost/wp-admin/admin-ajax.php', payload)
    r = session.post('http://localhost/wp-admin/post.php?post=13315&action=edit', payload)
    # r = session.post('http://localhost/wp-admin/admin-ajax.php', data=payload2)
    # with open('res.html', 'w', encoding='utf-8') as file:
    #     file.write(r.text)
    print(r.cookies)