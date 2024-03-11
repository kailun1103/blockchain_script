from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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

        for transaction in txn_data["transactions"]:
            input_count = len(transaction["inputs"])
            output_count = len(transaction["outputs"])
            print(f"Transaction has {input_count} inputs and {output_count} outputs.")

        
        return txn_data
    
    except Exception as ex:
        print(f'crawler_address_data hi error: {ex}') 


a = crawler_address_data('d13ef47bcd4e28372848ee4b983f65d8167ffeb93464f212cf4c4cfbd1aa3ba8')
json_data = json.dumps(a, indent=4)
print(json_data)