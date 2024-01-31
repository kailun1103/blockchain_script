from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from neo4j import GraphDatabase, Driver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import deque
import requests
import random
import time
import csv
import re
import os
import json

def convert_date_to_timestamp(date):
    dt_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    dt_object += timedelta(hours=8)
    formatted_timestamp = int(dt_object.timestamp())
    return formatted_timestamp

def crawler_hash_data(hash):
    btc_url = f'https://explorer.btc.com/btc/transaction/{hash}'
    response = requests.get(btc_url)
    BTC_page = BeautifulSoup(response.text, 'html.parser')

    # 交易的列表的元素
    txn_element = BTC_page.select('.jsx-3465105434')
    address_elements = BTC_page.select('.TxListItem_list-title__xQLZu')

    block = int(txn_element[2].text.replace(',', ''))
    timestamp = int(convert_date_to_timestamp(txn_element[10].text))
    input_value = int(round(float(txn_element[30].text.replace(' BTC', '')) * 100000000))
    output_value = int(round(float(txn_element[35].text.replace(' BTC', '')) * 100000000))
    fees = int(round(float(txn_element[42].text.replace(' BTC', '')) * 100000000))

    input_number_match = re.search(r'\((\d+)\)', address_elements[0].text)
    output_number_match = re.search(r'\((\d+)\)', address_elements[1].text)

    input_count = int(input_number_match.group(1)) if input_number_match else None
    output_count = int(output_number_match.group(1)) if output_number_match else None

    txn_data = {
        "transaction": {
            "output_count": output_count,
            "input_count": input_count,
            "fee": fees,
            "output_value": output_value,
            "input_value": input_value,
            "hash": hash,
            "timestamp": timestamp
        }
    }
    return txn_data, block

def neo4j_transaction_hash_api(block, hash):
    api_url = f"http://192.168.200.73:8000/bitcoin/transaction/{block}/{hash}"
    api_response = requests.get(api_url)
    api_dict = json.loads(api_response.text)
    api_dict['transaction']['timestamp'] = int(api_dict['transaction']['timestamp']) # 時間轉換成int
    return api_dict

def check_hash_data(row):
    crawler_data = eval(row[2])
    api_data = eval(row[3])

    checks = {
        "output_count": crawler_data['transaction']['output_count'] == api_data['transaction']['output_count'],
        "input_count": crawler_data['transaction']['input_count'] == api_data['transaction']['input_count'],
        "fee": crawler_data['transaction']['fee'] == api_data['transaction']['fee'],
        "output_value": crawler_data['transaction']['output_value'] == api_data['transaction']['output_value'],
        "input_value": crawler_data['transaction']['input_value'] == api_data['transaction']['input_value'],
        "hash": crawler_data['transaction']['hash'] == api_data['transaction']['hash'],
        "timestamp": crawler_data['transaction']['timestamp'] == api_data['transaction']['timestamp']
    }

    if all(checks.values()):
        return "Pass"
    else:
        for check, result in checks.items():
            if not result:
                return f"Fail: {check.replace('_', ' ').title()} error"

def check_address_data(row):
    crawler_data = eval(row[5])
    api_data = eval(row[6])
    
    crawler_inputs = crawler_data['transactions'][0]['inputs']
    crawler_outputs = crawler_data['transactions'][0]['outputs']
    api_inputs = api_data['transactions'][0]['inputs']
    api_outputs = api_data['transactions'][0]['outputs']

    # 檢查輸入
    for crawler_input, api_input in zip(crawler_inputs, api_inputs):
        if crawler_input != api_input:
            return f"Fail: Input address {crawler_input}"

    # 检查输出
    for crawler_output, api_output in zip(crawler_outputs, api_outputs):
        if crawler_output != api_output:
            return f"Fail: Input address {crawler_output}"

    return "Pass"

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

def crawler_address_data(hash):
    url = f'https://explorer.btc.com/btc/transaction/{hash}'
    response = requests.get(url)
    time.sleep(2)
    BTC_page = BeautifulSoup(response.text, 'html.parser')
    # 交易的列表的元素
    try:
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
        return txn_data
    
    except Exception as ex:
        print(f'crawler_address_data hi error: {ex}') 

def neo4j_address_data(driver: Driver, hash, database):
    with driver.session(database=database) as session:
        result = session.run(
            f"""
                MATCH p=()-->(t:transaction)-->()
                WHERE t.hash = "{hash}"
                RETURN t, p, [rel IN relationships(p) | rel.value] AS relationship_values
            """
        ).data()
        time.sleep(2)
        # 轉入地址數量/轉出地址數量/時間
        input_count = result[0]['t']['input_count']
        output_count = result[0]['t']['output_count']
        timestamp = int(result[0]['t']['timestamp'])

        # 轉入的地址和金額/轉出的地址和金額
        input_address_amount = {}
        output_address_amount = {}
        
        for item in result:
            input_address = item['p'][0]['address']
            output_address = item['p'][4]['address']
            input_amount = item['relationship_values'][0]
            output_amount = item['relationship_values'][1]
            
            if input_address in input_address_amount:
                input_address_amount[input_address] += input_amount
            else:
                input_address_amount[input_address] = input_amount
            
            if output_address in output_address_amount:
                output_address_amount[output_address] += output_amount
            else:
                output_address_amount[output_address] = output_amount
        
        transactions = [{
            'timestamp': timestamp,
            'inputs': [{'from': k, 'value': int(v / output_count)} for k, v in input_address_amount.items()],
            'hash': hash,
            'outputs': [{'to': k, 'value': int(v / input_count)} for k, v in output_address_amount.items()]
        }]

        return transactions

def merge_csv():
    csv_directory = "data/"
    csv_files = [file for file in os.listdir(csv_directory) if file.endswith(".csv")]

    merged_rows = []
    for file in csv_files:
        file_path = os.path.join(csv_directory, file)
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            header = rows[0]
            rows = rows[1:]
            merged_rows.extend(rows)
        
    test_date = datetime.now().strftime('%Y-%m-%d')
    merged_file_path = f"data/{test_date}.csv"
    with open(merged_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)  # 写入标题行
        writer.writerows(merged_rows)  # 写入数据行

def step3_address_data(csv_file_name, block):
    print('Start Check Address Data')

    URI = "neo4j://192.168.200.83:7687"
    AUTH = ("reader", "P@ssw0rd")

    if 654321 <= block <= 771137:
        database = 'bitcoin'
    elif 771138 <= block <= 819676:
        database = 'bitcoin2'
    elif 0 <= block <= 299590:
        database = 'bitcoin3'
    elif 299591 <= block <= 491537:
        database = 'bitcoin4'
    else:
        database = 'bitcoin5'

    with open(csv_file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        header = rows[0]
        rows = rows[1:]

    for row in rows:
        hash_value = row[1]
        row_copy = row[:]

        crawler_data =  crawler_address_data(hash_value)
        row_copy.append(crawler_data)
        with GraphDatabase.driver(URI, auth=AUTH) as neo4j_driver:
            neo4j_address_data(neo4j_driver, hash_value, database)
        row_copy.append(crawler_data)

        rows[rows.index(row)] = row_copy

    with open(csv_file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header + ["crawler address"] + ["neo4j address"])
        writer.writerows(rows)

    with open(csv_file_name, 'r', newline='') as f:
        rows = []
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        header.append('check address')  # Add hash check column header
        rows.append(header)
        for row in reader:
            result = check_address_data(row)
            row.append(result)  # Append check result to row
            rows.append(row)  # Add row to the list

    # Write back to the same file
    with open(csv_file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print('Done Check Address Data')

def step2_hash_data(csv_file_name):
    print('Start Check Hash Data')

    # csv读取hash
    with open(csv_file_name, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        header = rows[0]
        rows = rows[1:] 

    for row in rows:
        hash_value = row[1]
        row_copy = row[:]
        
        crawler_data, block = crawler_hash_data(hash_value)
        row_copy.append(crawler_data)
        api_data = neo4j_transaction_hash_api(block, hash_value)
        row_copy.append(api_data)
        
        rows[rows.index(row)] = row_copy

    with open(csv_file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header + ["crawler hash"] + ["neo4j hash"])  # 添加标题
        writer.writerows(rows)

    with open(csv_file_name, 'r', newline='') as f:
        rows = []
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        header.append('check hash')  # Add hash check column header
        rows.append(header)
        for row in reader:
            result = check_hash_data(row)
            row.append(result)  # Append check result to row
            rows.append(row)  # Add row to the list

    # Write back to the same file
    with open(csv_file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print('Done Check Hash Data')

def setp1_crawler_random_hash(BTC_driver, csv_file_name, block):
    print('Start Crawler Random Hash')

    BTC_driver.get(f"https://explorer.btc.com/btc/block/{block}")
    time.sleep(3)

    index = 2  # 從第二筆開始

    block_values = [block] * 9  # 產生包含9個列表存放交易hash
    hash_values = []  # 建立空的列表來存放 hash 值

    while True:
        try:
            xpath = f'//*[@id="__next"]/div[1]/div[5]/div[2]/div[1]/div/div[{index}]/div[1]'
            hash_element = WebDriverWait(BTC_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            hash_value = hash_element.text.split()[0]  # 提取第一個空白之前的部分
            print(hash_value)
            hash_values.append(hash_value)  # 將 hash 值加入列表
            index += 1
        except Exception as ex:
            # print(f'抓了{index-2}筆')
            break

    # 將 block_values 和 hash_values 寫入 CSV 檔案
    with open(csv_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Block', 'Hash'])  # 寫入標題
        for block_val, hash_val in zip(block_values, hash_values):
            writer.writerow([block_val, hash_val])
    
    print('Done Crawler Random Hash')

if __name__ == '__main__':
    test_times = 20
    
    BTC_driver = webdriver.Chrome(service=Service("C:\\Users\\user\\Desktop\\區塊科技\\公帳爬蟲\\chromedriver.exe"))

    for _ in range(test_times):
        random_block = random.randint(654321, 825823)
        csv_file_path = f"data/{random_block}.csv"

        setp1_crawler_random_hash(BTC_driver, csv_file_path, random_block)
        time.sleep(2)
        step2_hash_data(csv_file_path)
        time.sleep(2)
        step3_address_data(csv_file_path, random_block)
        time.sleep(2)
    
    merge_csv()