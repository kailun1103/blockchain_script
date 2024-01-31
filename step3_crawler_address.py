import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

def extract_addresses_and_amounts_from_elements(elements, is_output=False):
    # 將HTML分析，並取出輸入元素和輸出元素。輸入元素儲存在from的鍵下，輸出則放在to
    addresses = []
    # print(elements)
    for address_element in elements:
        link_element = address_element.find('a', class_='monospace')
        if link_element is None:
            # 如果找不到連結元素，跳過目前循環
            continue
        address = link_element['href'].split('/')[-1]
        amount_text = address_element.find('span').text
        amount = int(float(amount_text.replace(',', '')) * 100000000)
        if is_output:
            addresses.append({"to": address, "value": amount})
        else:
            addresses.append({"from": address, "value": amount})
    return addresses

def convert_date_to_timestamp(date):
    dt_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    dt_object += timedelta(hours=8)
    formatted_timestamp = int(dt_object.timestamp())
    return formatted_timestamp

def neo4j_transaction_address_api(timestamp,address):
    api_url = "http://192.168.200.73:8000/bitcoin/transaction"
    payload = {
        "address": address,
        "startTime": timestamp,
        "endTime": timestamp,
        "minValue": 0,
        "maxValue": 9223372036854776
    }
    api_response = requests.post(api_url, json=payload)
    api_dict = json.loads(api_response.text)
    return api_dict

def crawler_address(hash):
    url = f'https://explorer.btc.com/btc/transaction/{hash}'
    response = requests.get(url)
    BTC_page = BeautifulSoup(response.text, 'html.parser')

    # 交易的列表的元素
    status_elements = BTC_page.select('.TxListItem_list-items__2Ganp')
    time_elements = BTC_page.select('.jsx-3465105434')
    input_elements = status_elements[0].find_all('li')
    output_elements = status_elements[1].find_all('li')

    # list存放該筆交易的輸入輸出地址和金額
    input_list = extract_addresses_and_amounts_from_elements(input_elements)
    output_list = extract_addresses_and_amounts_from_elements(output_elements, is_output=True)
    timestamp = int(convert_date_to_timestamp(time_elements[10].text))

    # 將重複地址的金額加總(輸入地址)
    consolidated_inputs = {}
    for input_entry in input_list:
        address = input_entry['from']
        value = input_entry['value']
        if address in consolidated_inputs:
            consolidated_inputs[address] += value
        else:
            consolidated_inputs[address] = value

    # 將重複地址的金額加總(輸入地址)
    consolidated_outputs = {}
    for output_entry in output_list:
        address = output_entry['to']
        value = output_entry['value']
        if address in consolidated_outputs:
            consolidated_outputs[address] += value
        else:
            consolidated_outputs[address] = value
    
    txn_data = {
        "transactions": [
            {
                "timestamp": timestamp,
                "inputs": [{"from": addr, "value": val} for addr, val in consolidated_inputs.items()],
                "hash": hash,
                "outputs": [{"to": addr, "value": val} for addr, val in consolidated_outputs.items()]
            }
        ]
    }
    return txn_data, timestamp


hash = '9c506b8954a647ac4920f6be0d6feacf41a6c3a1a664790ea83c04835d6178ad'

crawler_data, timestamp = crawler_address(hash)

print(crawler_data)
# api_data = neo4j_transaction_address_api(timestamp,first_address)


# crawler_input_addresses = [entry['from'] for entry in crawler_data['transactions'][0]['inputs']]
# crawler_output_addresses = [entry['to'] for entry in crawler_data['transactions'][0]['outputs']]
# api_input_addresses = [entry['from'] for entry in api_data['transactions'][0]['inputs']]
# api_output_addresses = [entry['to'] for entry in api_data['transactions'][0]['outputs']]

# crawler_input_value = [entry['value'] for entry in crawler_data['transactions'][0]['inputs']]
# crawler_output_value = [entry['value'] for entry in crawler_data['transactions'][0]['outputs']]
# api_input_value = [entry['value'] for entry in api_data['transactions'][0]['inputs']]
# api_output_value = [entry['value'] for entry in api_data['transactions'][0]['outputs']]

# print(crawler_data)

# if all(address in api_input_addresses for address in crawler_input_addresses) and \
#    all(address in api_output_addresses for address in crawler_output_addresses):
#     print("Pass")
# else:
#     print("Fail")