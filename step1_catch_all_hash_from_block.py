import csv
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time

chrome_driver_path = "C:\\Users\\user\\Desktop\\區塊科技\\公帳爬蟲\\chromedriver.exe"
service = Service(chrome_driver_path)

block = 820020

BTC_driver = webdriver.Chrome(service=service)
BTC_driver.get(f"https://explorer.btc.com/btc/block/{block}")
time.sleep(3)

index = 2  # 從第二筆開始

block_values = [block] * 9  # 產生包含9個 block 變數的列表

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
        print(f'抓了{index-2}筆')  # 減去初始值2
        break

# 將 block_values 和 hash_values 寫入 CSV 檔案
with open('test.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Block', 'Hash'])  # 寫入標題
    for block_val, hash_val in zip(block_values, hash_values):
        writer.writerow([block_val, hash_val])
