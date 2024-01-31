import csv
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor

def check_txn(hash):
    while True:
        url = f'https://explorer.btc.com/btc/transaction/{hash}'
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            try:
                status_elements = soup.select('.jsx-3465105434')
                block_height = status_elements[2].text
                status = status_elements[26].text

                if status_elements[10].text == '-':
                    verification_date = status_elements[10].text
                else:
                    verification_date = (datetime.strptime(status_elements[10].text, '%Y-%m-%d %H:%M:%S') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
                
                current_datetime = datetime.now()
                checked_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

                txn_url = url
                block_url = f'https://explorer.btc.com/btc/block/{block_height}'

                print("Block Height:", block_height)
                print("Status:", status)
                print("Verification Date:", verification_date)
                print("Checked Datetime:", checked_datetime)
                print("Txn URL:", txn_url)
                print("Block URL:", block_url)

                # 打開 CSV 文件
                with open('testcsv.csv', 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    data = list(reader)

                    # 查找匹配的行
                    for row in data:
                        if hash in row[0]:
                            # 將數據添加到 CSV 文件
                            row[9:] = [status, verification_date, block_height, checked_datetime, txn_url, block_url]

                # 寫入 CSV 文件
                with open('testcsv.csv', 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(data)

                return  # 成功處理完畢，跳出函數

            except AttributeError as ex:
                print(f"BeautifulSoup hit error: {ex}")
        
        elif response.status_code == 500:
            print(f"Internal Server Error (status code: {response.status_code}). Returning.")
            return
        
        elif response.status_code == 429:
            print(f"Too Many Requests (status code: {response.status_code}). Retrying in 5 seconds...")
            time.sleep(5)
        
        else:
            print(f"Waiting for response (status code: {response.status_code})...")
            time.sleep(1)  # 每隔 1 秒重試一次

        print(f"Max retries reached. Unable to process {hash}.")


def process_row(row):
    txn_hash = row['Txn Hash']
    check_txn(txn_hash)

# 用 hash 進行查詢
# check_txn('f60f742766c8fa8e1939f7d4945db8176fb66f4c9d1bfea53da5a7c74715c4ea')
    
csv_file_name = 'testcsv.csv'

with open(csv_file_name, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    # 創建 ThreadPoolExecutor，設定最大執行緒數為 10
    with ThreadPoolExecutor(max_workers=1) as executor:
        # 對每一行啟動一個執行緒執行 process_row 函數
        executor.map(process_row, reader)