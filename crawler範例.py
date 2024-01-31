from multiprocessing import Process
import os
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from datetime import datetime
from collections import deque
import time 
import csv

# 計算交易總筆數、查閱最終日期
def catch_final_information():
    last_page_number = 0
    total_transaction_counts = 0
    try:
        try:
            button_7 = WebDriverWait(driver_3, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[7]'))
            )
            button_7_text = button_7.text
        except TimeoutException:
            button_7_text = 'null'

        try:
            button_8 = WebDriverWait(driver_3, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[8]'))
            )
            button_8_text = button_8.text
        except TimeoutException:
            button_8_text = 'null'

        try:
            button_9 = WebDriverWait(driver_3, 2).until( # 等2秒，沒有找到就pass
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[9]'))
            )
            button_9_text = button_9.text
        except TimeoutException:
            button_9_text = 'null'

        # 判斷最後頁數的按鈕，並點擊以及紀錄頁數
        if button_9_text == '>':
            if button_8_text != '>':
                driver_3.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                button = WebDriverWait(driver_3, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[8]'))
                )
                last_page_number = button_8_text
                button.click()
            else:
                print('can not find last button for web page')
        elif button_9_text == 'null':
            if button_8_text == '>':
                driver_3.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                button = WebDriverWait(driver_3, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[7]'))
                )
                last_page_number = button_7_text
                button.click()
            else:
                print('can not find last button for web page')
        else:
            print('can not find last button for web page')
        time.sleep(1)
        # 計算最後一頁的筆數(應該會小於等於100筆)
        BTC_page_3 = BeautifulSoup(driver_3.page_source, 'html.parser')

        rows_3 = BTC_page_3.select('tr')
        last_row = rows_3[-1]
        c_element = last_row.select_one('td:nth-of-type(2) div')
        final_date_value = c_element.text if c_element else None # 總交易最後一筆的日期紀錄起來
        final_page_count = len(rows_3) - 1 # 總交易最後一頁的交易數量紀錄起來

        # 計算總共的交易數量
        total_transaction_counts = ( int(last_page_number) * 100 ) + final_page_count

        # 應該要return total_transaction_counts 和 final_date_value
        return total_transaction_counts ,final_date_value
    except Exception as ex:
        print(f'catch_final_information fail, reason:{ex}')
        return 0,0
    
def python_crawler(driver_1,driver_2,hashes_seen,header_written,start_time_crawl):
    try:
        # print('爬蟲!!!!!!!!!!!!!!!!!')
        start_time = start_time_crawl
        # 獲取網頁內容
        html_1 = driver_1.page_source
        BTC_page_1 = BeautifulSoup(html_1, 'html.parser')

        html_2 = driver_2.page_source
        BTC_page_2 = BeautifulSoup(html_2, 'html.parser')

        rows_1 = BTC_page_1.select('tr')
        BTC_data_to_write_1 = []

        rows_2 = BTC_page_2.select('tr')
        BTC_data_to_write_2 = []

        # 本次迴圈計算的交易量
        this_time_rows = 0

        total_count,final_date = catch_final_information()
        # driver_1迭代處理網頁每一行
        for row in rows_1:
            txn_link_1 = row.select_one('td:nth-of-type(1) a') # 從表格行中選擇特定的資料欄位

            if txn_link_1:
                txn_hash_1 = txn_link_1.get('href').split('/')[-1]

                if txn_hash_1 not in hashes_seen: # 利用deque排除重複的交易
                    hashes_seen.append(txn_hash_1)

                    txn_time_1 = row.select_one('td:nth-of-type(2) div').text
                    inputsVolume_1 = row.select_one('td:nth-of-type(3)')
                    outputsVolume_1 = row.select_one('td:nth-of-type(4)')
                    fees_1 = row.select_one('td:nth-of-type(6)')

                    inputsVolume_amt_1 = 0
                    inputsCount_amt_1 = 0
                    if inputsVolume_1:
                        inputsVolume_amt_1 = float(inputsVolume_1.text.split()[0])
                        inputsCount_amt_1 = int(inputsVolume_1.text.split()[1].replace('(',''))

                    outputsVolume_amt_1 = 0
                    outputsCount_amt_1 = 0
                    if outputsVolume_1:
                        outputsVolume_amt_1 = float(outputsVolume_1.text.split()[0])
                        outputsCount_amt_1 = int(outputsVolume_1.text.split()[1].replace('(',''))

                    fees_amt_1 = 0
                    if fees_1:
                        fees_amt_1 = float(fees_1.text.split()[0])
                
                    # 正常抓(包含正常、異常交易)
                    BTC_data_to_write_1.append([txn_hash_1, txn_time_1, inputsVolume_amt_1, outputsVolume_amt_1, inputsCount_amt_1, outputsCount_amt_1, fees_amt_1, total_count, final_date])

        # driver_2迭代處理網頁每一行
        for row in rows_2:
            txn_link_2 = row.select_one('td:nth-of-type(1) a') 

            if txn_link_2:
                txn_hash_2 = txn_link_2.get('href').split('/')[-1]

                if txn_hash_2 not in hashes_seen: 
                    hashes_seen.append(txn_hash_2)

                    txn_time_2 = row.select_one('td:nth-of-type(2) div').text
                    inputsVolume_2 = row.select_one('td:nth-of-type(3)')
                    outputsVolume_2 = row.select_one('td:nth-of-type(4)')
                    fees_2 = row.select_one('td:nth-of-type(6)')

                    inputsVolume_amt_2 = 0
                    inputsCount_amt_2 = 0
                    if inputsVolume_2:
                        inputsVolume_amt_2 = float(inputsVolume_2.text.split()[0])
                        inputsCount_amt_2 = int(inputsVolume_2.text.split()[1].replace('(',''))

                    outputsVolume_amt_2 = 0
                    outputsCount_amt_2 = 0
                    if outputsVolume_2:
                        outputsVolume_amt_2 = float(outputsVolume_2.text.split()[0])
                        outputsCount_amt_2 = int(outputsVolume_2.text.split()[1].replace('(',''))

                    fees_amt_2 = 0
                    if fees_2:
                        fees_amt_2 = float(fees_2.text.split()[0])
                    
                    BTC_data_to_write_2.append([txn_hash_2, txn_time_2, inputsVolume_amt_2, outputsVolume_amt_2, inputsCount_amt_2, outputsCount_amt_2, fees_amt_2, total_count, final_date])


        if BTC_data_to_write_1:
            with open(csv_file_name, 'a', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                if not header_written:
                    csv_writer.writerow(["Txn Hash","Txn Date", "Input Volume", "Output Volume", "Input Count", "Output Count", "Fees", "Total Txn Amount", "Final Txn Date"])
                    header_written = True
                csv_writer.writerows(BTC_data_to_write_1)

            print(f"- 本次driver_1抓取了 {len(BTC_data_to_write_1)} 條交易")

        if BTC_data_to_write_2:
            with open(csv_file_name, 'a', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                if not header_written:
                    csv_writer.writerow(["Txn Hash","Txn Date", "Input Volume", "Output Volume", "Input Count", "Output Count", "Fees", "Total Txn Amount", "Final Txn Date"])
                    header_written = True
                csv_writer.writerows(BTC_data_to_write_2)

            print(f"- 本次driver_2抓取了 {len(BTC_data_to_write_2)} 條交易")

        this_time_rows = len(BTC_data_to_write_1) + len(BTC_data_to_write_2) # 追蹤總行數

        if this_time_rows != 0:
            current_time = time.time()
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
            print(f"BTC兩個視窗抓取了 {this_time_rows} 條交易")
            print(f"BTC總交易數量為 {total_count} 條交易")
            print(f'BTC目前時間為: {formatted_time}')
            print("----------------------------------------")

        # print('本次沒抓到東西')
    
    except Exception as ex:
        print(f"Failed reason: {ex}")

def run_crawler(driver_1, driver_2, hashes_seen, header_written, start_time):
    python_crawler(driver_1, driver_2, hashes_seen, header_written, start_time)

if __name__ == '__main__':
    # ------------開始selenium自動化腳本------------

    # ----driver_1是第一個自動化視窗----
    driver_1 = webdriver.Chrome()
    driver_1.get('https://explorer.btc.com/btc/unconfirmed-txs')

    # driver_1 滑到最底下
    driver_1.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # driver_1的介面自動化操作
    try:
        # 等待元素出現，並點擊指定元素
        button = WebDriverWait(driver_1, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/div'))
        )
        button.click()
        # 點擊一次顯示100頁選項
        button = WebDriverWait(driver_1, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btccom-ui-dropdown"]/div/div/div[4]'))
        )
        button.click() 
    except Exception as ex:
        print(f"driver_1 hit error: {ex}")

    time.sleep(5)

    # ----driver_2是第二個自動化視窗----
    driver_2 = webdriver.Chrome()
    driver_2.get('https://explorer.btc.com/btc/unconfirmed-txs')

    driver_2.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        button = WebDriverWait(driver_2, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/div'))
        )
        button.click()

        button = WebDriverWait(driver_2, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btccom-ui-dropdown"]/div/div/div[4]'))
        )
        button.click() 

        time.sleep(2)

        driver_2.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(2)

        button = WebDriverWait(driver_2, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/li[3]/button'))
        )
        button.click() 
    except Exception as ex:
        print(f"driver_2 hit error: {ex}")

    time.sleep(5)

    # ----driver_3是第一個自動化視窗----
    driver_3 = webdriver.Chrome()
    driver_3.get('https://explorer.btc.com/btc/unconfirmed-txs')

    driver_3.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        button = WebDriverWait(driver_3, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/div[5]/nav/div'))
        )
        button.click()

        button = WebDriverWait(driver_3, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btccom-ui-dropdown"]/div/div/div[4]'))
        )
        button.click() 
    except Exception as ex:
        print(f"driver_3 hit error: {ex}")

    time.sleep(5)

    # ------------開始爬蟲程序------------

# ------------開始爬蟲程序------------

    continue_time = 180  # 輸入爬蟲持續的時間(分鐘)
    split_count = 1  # 輸入檔案切割數量
    interval = continue_time / split_count  # 計算間隔的時間

    # 初始化一個 deque 用來模擬 hashes_seen，儲存看過的交易hashe
    hashes_seen = deque(maxlen=1000000)  # 設定 deque 的最大長度，這裡設置為 100000

    # 標題寫入的布林值
    header_written = False

    # 顯示開始爬蟲的時間
    current_time = time.time()
    formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
    print(f'開始時間為: {formatted_time}')

    # 設置起始時間
    start_time = time.time()

    # 寫入標題，確保只寫入一次
    for i in range(split_count):
        today_date = datetime.today().strftime('%Y_%m_%d')
        csv_file_name = f"Pending Transactions/BTX_Transaction_data_{today_date}_{i + 1}.csv"
        
        with open(csv_file_name, 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            if not header_written:
                csv_writer.writerow(["Txn Hash","Txn Date", "Input Volume", "Output Volume", "Input Count", "Output Count", "Fees", "Total Txn Amount", "Final Txn Date"])
                header_written = True  # 設定為 True，表示標題已經被寫入

        end_time = time.time() + interval * 60  # 設置計時器，以間隔時間為單位

        with ThreadPoolExecutor(max_workers=5) as executor:
            while time.time() < end_time:
                try:
                    # 使用ThreadPoolExecutor來執行爬蟲函式
                    executor.submit(run_crawler, driver_1, driver_2, hashes_seen, header_written, start_time).result()
                except Exception as ex:
                    print(f"Error in threading: {ex}")

                print(123)
                print(len(hashes_seen))

                if len(hashes_seen) > 1000:
                    # print(f'Before cleanup, hashes_seen count: {len(hashes_seen)}')
                    hashes_seen = deque(list(hashes_seen)[len(hashes_seen) // 2:], maxlen=1000000)
                    print('Cleaned hashes_seen')
                    # print(f'After cleanup, hashes_seen count: {len(hashes_seen)}')


        print(f'已經過 {i+1} 小時，第 {i+1} 次儲存')

    print("Done BTX Web Data Scraping")

    driver_1.quit()
    driver_2.quit()
    driver_3.quit()
