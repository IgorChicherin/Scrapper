import re
import requests
from bs4 import BeautifulSoup

session = requests.Session()
payload = {'log': 'olegsent', 'pwd': 'dW#h$x*^EnGOpLhH'}
r = session.post('http://localhost/wp-login.php', payload)
r = session.get('http://localhost/wp-admin/post.php?post=13315&action=edit')
soup = BeautifulSoup(r.text, 'lxml')
script_block = soup.findAll('script')
for item in script_block:
    security_id = re.search(r'(?<=security: \')(\w+)', item.text)
    if security_id is not None:
        security = security_id.group(0)
payload = {'action': 'woocommerce_add_variation', 'post_id': '13315', 'loop': '6', 'security': security}
r = session.post('http://localhost/wp-admin/admin-ajax.php', payload)
print(r.text)