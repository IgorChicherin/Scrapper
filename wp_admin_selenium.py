import time
from selenium import webdriver

driver = webdriver.Chrome('chromedriver.exe')
driver.get('http://localhost/wp-admin/')
driver.set_page_load_timeout(30)
driver.find_element_by_id('user_login').send_keys('olegsent')
time.sleep(1)
driver.find_element_by_id('user_pass').send_keys('dW#h$x*^EnGOpLhH')
driver.find_element_by_id('wp-submit').click()
driver.implicitly_wait(10)
driver.get('http://localhost/wp-admin/post.php?post=13315&action=edit')
driver.find_element_by_xpath('//*[@id="woocommerce-product-data"]/div/div/ul/li[5]/a').click()
driver.find_element_by_xpath('//*[@id="product_attributes"]/div[2]/div[1]/h3').click()
sizes_input = driver.find_element_by_name('attribute_values[0]')
len_sizes = str(sizes_input.get_attribute('value')).split('|')
for item in range(len(str(sizes_input.get_attribute('value')))):
    sizes_input.send_keys('\b')
sizes_input.send_keys('52 | 54 | 56 | 58 | 60 | 62 | 64 | 66 ')
driver.find_element_by_xpath('//*[@id="product_attributes"]/div[3]/button').click()
time.sleep(3)
driver.find_element_by_xpath('//*[@id="woocommerce-product-data"]/div/div/ul/li[6]/a').click()
driver.find_element_by_xpath('//*[@id="variable_product_options_inner"]/div[2]/a').click()
time.sleep(3)
size_selects = driver.find_elements_by_xpath('//*[@id="variable_product_options_inner"]/div[3]/div')
time.sleep(3)
size_select = size_selects[0].find_element_by_xpath('//select')
options_size_select = size_select.find_elements_by_tag_name('option')
for option in options_size_select:
    if option.get_attribute('value') == '66':
        option.click()
driver.find_element_by_xpath('//*[@id="variable_product_options_inner"]/div[4]/button[1]').click()
time.sleep(5)
driver.close()
