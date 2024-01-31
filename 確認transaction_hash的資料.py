from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from datetime import datetime
from collections import deque
import requests
import time
import csv
import json

def convert_timestamp_to_date(timestamp):
    dt_object = datetime.utcfromtimestamp(timestamp)
    formatted_date = dt_object.strftime('%Y-%m-%d')
    return formatted_date

def convert_date_to_timestamp(date):
    dt_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    formatted_timestamp = int(dt_object.timestamp())
    return formatted_timestamp

def check_data(csv_file_path):
    with open(csv_file_path, 'r') as csv_file:
        # 讀取 CSV 檔案為字典列表
        rows = list(csv.DictReader(csv_file))

        # 處理每一列
        for row in rows:
            # 從字典中取得 BTC.com transaction 字串
            transaction_str = row.get('BTC.com', '')
            # Replace single quotes with double quotes
            transaction_str = transaction_str.replace("'", "\"")
            # 將 transaction 字串轉換成字典
            transaction_dict = json.loads(transaction_str)

            # 將 'index' 資料型態轉換為整數
            if 'index' in transaction_dict['transaction']:
                transaction_dict['transaction']['index'] = int(transaction_dict['transaction']['index'])

            # 從字典中取得 api_response transaction 字串
            transaction_str2 = row.get('api_response', '')
            # Replace single quotes with double quotes
            transaction_str2 = transaction_str2.replace("'", "\"")
            # 將 transaction 字串轉換成字典
            transaction_dict2 = json.loads(transaction_str2)

            # 比對兩個字典是否相符
            if transaction_dict == transaction_dict2:
                row['status'] = 'Pass'
            else:
                row['status'] = 'Fail'

    # 更新 CSV 檔案
    with open(csv_file_path, 'w', newline='') as csv_file:
        # 指定 CSV 欄位
        fieldnames = rows[0].keys()
        # 使用 DictWriter 寫入 CSV 檔案
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        # 寫入 title
        writer.writeheader()
        # 寫入資料行
        writer.writerows(rows)

def btc_transaction_hash_api(block, hash):
    api_url = f"http://192.168.200.215:8000/bitcoin/transaction/{block}/{hash}"
    api_response = requests.get(api_url)
    return api_response

def get_index(Blockchain_driver, csv_file_path):
    with open(csv_file_path, 'r') as csv_file:
        # Read the CSV file into a list of dictionaries
        rows = list(csv.DictReader(csv_file))
        try:
            # 迴圈處理每一列
            for row in rows:
                # 從字典中取得 transaction 字串
                transaction_str = row.get('BTC.com', '')
                # # Replace single quotes with double quotes
                transaction_str = transaction_str.replace("'", "\"")
                # 將 transaction 字串轉換成字典
                transaction_dict = json.loads(transaction_str)
                # 從 transaction 字典中取得 hash
                hash_value = transaction_dict['transaction']['hash']

                while True:
                    url = f'https://www.blockchain.com/explorer/transactions/btc/{hash_value}'
                    Blockchain_driver.get(url)
                    time.sleep(3)

                    block = WebDriverWait(Blockchain_driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div/div/section/section/section/div[2]/div[2]/div[2]/a/div/div/div'))
                    )
                    block = block.text.replace(',', '')

                    index = WebDriverWait(Blockchain_driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[2]/div[2]/main/div/div/section/section/section/div[2]/div[3]/div[2]/div/div'))
                    )
                    index = index.text
                    if index != '':
                        break


                api_url = f"http://192.168.200.215:8000/bitcoin/transaction/{block}/{hash_value}"

                row['BTC.com'] = transaction_str.replace('null', index)

                response = btc_transaction_hash_api(block, hash_value)
                # Make a request to the API
                response = requests.get(api_url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Add the API response text to the row
                    row['api_response'] = response.text
                else:
                    print(f"Error: Unable to fetch API data for hash {hash_value}")
        except Exception as ex:
            print(ex)

    try:
        with open(csv_file_path, 'w', newline='') as csv_file:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as ex:
        print(f"write_data_to_csv hit error: {ex}")

def crawler_btc(driver, date, txn_count, hashes_seen, csv_file_path):
    try:
        # 設定開始、結束日期設定
        start_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[1]/div/div/div[2]/div[3]/input'))
        )
        start_date.send_keys(date)
        time.sleep(1)
        end_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[1]/div/div/div[2]/div[1]/input'))
        )
        end_date.send_keys(date)
        time.sleep(1)

        BTC_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 點擊頁面顯示選項，並點擊顯示100頁選項
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[4]/nav/div'))
        )
        button.click()
        time.sleep(1)
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btccom-ui-dropdown"]/div/div/div[4]'))
        )
        button.click()
    except Exception as ex:
        print(f"selenium hit error: {ex}")
    
    time.sleep(5)

    BTC_html = driver.page_source
    BTC_page = BeautifulSoup(BTC_html, 'html.parser')

    rows = BTC_page.select('tr')
    BTC_data_to_write = []

    # 計數器初始化
    current_txn_count = 0

    for row in rows[2:]:
        txn_link = row.select_one('td:nth-of-type(1) a')  # 從表格行中選擇特定的資料欄位

        if txn_link:
            txn_hash = txn_link.get('href').split('/')[-1]

            if txn_hash not in hashes_seen:  # 利用deque排除重複的交易
                hashes_seen.append(txn_hash)

                txn_time = row.select_one('td:nth-of-type(2) div').text
                inputsVolume = row.select_one('td:nth-of-type(3)')
                outputsVolume = row.select_one('td:nth-of-type(4)')
                fees = row.select_one('td:nth-of-type(6)')

                inputsVolume_amt = 0
                inputsCount_amt = 0
                if inputsVolume:
                    inputsVolume_amt = float(inputsVolume.text.split()[0])
                    inputsCount_amt = int(inputsVolume.text.split()[1].replace('(',''))

                outputsVolume_amt = 0
                outputsCount_amt = 0
                if outputsVolume:
                    outputsVolume_amt = float(outputsVolume.text.split()[0])
                    outputsCount_amt = int(outputsVolume.text.split()[1].replace('(',''))

                fees_amt = 0
                if fees:
                    fees_amt = float(fees.text.split()[0])

                inputsVolume_amt = int(inputsVolume_amt * 100000000)
                outputsVolume_amt = int(outputsVolume_amt * 100000000)
                fees_amt = int(fees_amt * 100000000)
                timestamp = convert_date_to_timestamp(txn_time)

                txn_data = {
                    "transaction": {
                        "output_count": outputsCount_amt,
                        "input_count": inputsCount_amt,
                        "fee": fees_amt,
                        "index": "null", 
                        "output_value": outputsVolume_amt,
                        "input_value": inputsVolume_amt,
                        "hash": txn_hash,
                        "timestamp": timestamp
                    }
                }

                BTC_data_to_write.append(txn_data)

                # 更新計數器
                current_txn_count += 1

                # 檢查是否達到指定的 txn_count
                if current_txn_count >= txn_count:
                    break  # 如果達到指定數量，跳出迴圈停止抓取

                # 寫入csv
                try:
                    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        # 寫入標題行
                        csv_writer.writerow(['BTC.com'])
                        # 寫入數據
                        for txn_data in BTC_data_to_write:
                            csv_writer.writerow([txn_data])
                except Exception as ex:
                    print(f"write_data_to_csv hit error: {ex}")

if __name__ == '__main__':
    test_date = '2024-01-20' # 輸入測試時間 eg:test_date = '2024-01-05'
    test_count = 4 # 輸入測試筆數 eg:test_count =  = 

    csv_file_path = f"{test_date}_data_verification_for_{test_count}.csv"

    # selenium 設定參數
    chrome_driver_path = "C:\\Users\\user\\Desktop\\區塊科技\\公帳爬蟲\\chromedriver.exe"
    service = Service(chrome_driver_path)

    BTC_driver = webdriver.Chrome(service=service)
    BTC_driver.get("https://explorer.btc.com/btc/transactions")

    Blockchain_driver = webdriver.Chrome(service=service)
    Blockchain_driver.get("https://www.blockchain.com/explorer/transactions")

    # 設deque來避免爬到同一筆交易
    hashes_deque = deque(maxlen=1000000)

    # 先去公帳爬蟲(爬要對筆的資料)
    print('start')
    crawler_btc(BTC_driver, test_date, test_count, hashes_deque, csv_file_path)
    # 取得區塊index，並呼叫api
    get_index(Blockchain_driver, csv_file_path)
    # 對比資料是否正確
    check_data(csv_file_path)
    print('Done')