import re
import csv

def krasa_parse(file_name):
    '''
    Parsing goods from krasa.csv
    :param file_name: str
    :return: list
    '''
    result = list()
    with open(file_name) as csvfile:
        reader = csv.reader(csvfile, dialect='excel', delimiter=';')
        for row in reader:
            if 'последние экземпляры' in row[0]:
                break
            if ('Наименование' or '') not in row[0]:
                try:
                    name = 'Краса ' + re.search(r'(П-\d+|ПБ-\d+|Р-\d+|РБ-\d+)', row[0]).group(0)
                    price = re.search(r'(\d+)', row[1].strip().replace(' ', '')).group(0)
                    price = 2400 if int(price) < 1200 else int(price) * 2
                    sizes = row[2].split('-')
                    sizes_list = [str(size) for size in range(int(sizes[0]), int(sizes[1]) + 1) if size % 2 == 0]
                    item_type = name.split(' ')[1].split('-')[0]
                    if item_type == 'П' or item_type == 'ПБ':
                        item_type = 'Платье'
                    elif item_type == 'Р' or item_type == 'РБ':
                        item_type = 'Блузка'
                    # print([name, sizes_list, price, item_type])
                    result.append([name, sizes_list, price, item_type, True])
                except AttributeError:
                    continue
    return result