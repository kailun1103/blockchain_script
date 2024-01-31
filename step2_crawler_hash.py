import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from datetime import datetime, timedelta

def convert_date_to_timestamp(date):
    dt_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    dt_object += timedelta(hours=8)
    formatted_timestamp = int(dt_object.timestamp())
    return formatted_timestamp

def neo4j_transaction_hash_api(block, hash):
    api_url = f"http://192.168.200.73:8000/bitcoin/transaction/{block}/{hash}"
    api_response = requests.get(api_url)
    api_dict = json.loads(api_response.text)
    api_dict['transaction']['timestamp'] = int(api_dict['transaction']['timestamp']) # 時間轉換成int
    return api_dict

api_data = neo4j_transaction_hash_api(798911, hash)

csv_file = 'test.csv'
output_file = 'output.csv'

with open(csv_file, 'r', newline='') as f:
    reader = csv.reader(f)
    rows = list(reader)
    header = rows[0]
    rows = rows[1:]  # 去掉标题行

# 执行crawler_hash函数并将结果写入第三列
for row in rows:
    hash_value = row[1]
    api_data = neo4j_transaction_hash_api(798911, hash_value)
    row.append(api_data)



# checks = {
#     "output_count_check": crawler_data['transaction']['output_count'] == api_data['transaction']['output_count'],
#     "input_count_check": crawler_data['transaction']['input_count'] == api_data['transaction']['input_count'],
#     "fee_check": crawler_data['transaction']['fee'] == api_data['transaction']['fee'],
#     "output_value_check": crawler_data['transaction']['output_value'] == api_data['transaction']['output_value'],
#     "input_value_check": crawler_data['transaction']['input_value'] == api_data['transaction']['input_value'],
#     "hash_check": crawler_data['transaction']['hash'] == api_data['transaction']['hash'],
#     "timestamp_check": crawler_data['transaction']['timestamp'] == api_data['transaction']['timestamp']
# }

# if all(checks.values()):
#     print("Pass")
# else:
#     print("Fail")
#     for check, result in checks.items():
#         if not result:
#             print(f"{check.replace('_', ' ').title()} failed")








# def crawler_hash(hash):
#     btc_url = f'https://explorer.btc.com/btc/transaction/{hash}'
#     response = requests.get(btc_url)
#     BTC_page = BeautifulSoup(response.text, 'html.parser')

#     # 交易的列表的元素
#     txn_element = BTC_page.select('.jsx-3465105434')
#     address_elements = BTC_page.select('.TxListItem_list-title__xQLZu')

#     block = int(txn_element[2].text.replace(',', ''))
#     timestamp = int(convert_date_to_timestamp(txn_element[10].text))
#     input_value = int(round(float(txn_element[30].text.replace(' BTC', '')) * 100000000))
#     output_value = int(round(float(txn_element[35].text.replace(' BTC', '')) * 100000000))
#     fees = int(round(float(txn_element[42].text.replace(' BTC', '')) * 100000000))

#     input_number_match = re.search(r'\((\d+)\)', address_elements[0].text)
#     output_number_match = re.search(r'\((\d+)\)', address_elements[1].text)

#     input_count = int(input_number_match.group(1)) if input_number_match else None
#     output_count = int(output_number_match.group(1)) if output_number_match else None

#     txn_data = {
#         "transaction": {
#             "output_count": output_count,
#             "input_count": input_count,
#             "fee": fees,
#             "output_value": output_value,
#             "input_value": input_value,
#             "hash": hash,
#             "timestamp": timestamp
#         }
#     }

#     return txn_data, block

# # 读取CSV文件
# csv_file = 'test.csv'
# output_file = 'output.csv'

# with open(csv_file, 'r', newline='') as f:
#     reader = csv.reader(f)
#     rows = list(reader)
#     header = rows[0]
#     rows = rows[1:]  # 去掉标题行

# # 执行crawler_hash函数并将结果写入第三列
# for row in rows:
#     hash_value = row[1]
#     crawler_data, block = crawler_hash(hash_value)
#     row.append(crawler_data)
    
# # 写入输出文件
# with open(output_file, 'w', newline='') as f:
#     writer = csv.writer(f)
#     writer.writerow(header)
#     writer.writerows(rows)

    
