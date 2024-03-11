import os
import json
import requests
import csv
import datetime

# CSV文件路徑
formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d__%H.%M")
csv_file_path = f"tron\\TRON_{formatted_datetime}.csv"

# 打開CSV文件並寫入標題
with open(csv_file_path, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['tron', 'neo4j tron', 'status'])

    # JSON文件夾路徑
    json_directory = "track/"
    json_files = [file for file in os.listdir(json_directory) if file.endswith(".json")]

    # 遍歷每個json
    for file in json_files:
        file_path = os.path.join(json_directory, file)
        with open(file_path, 'r') as f:
            input_data = json.load(f)

            # 剖析外部的api資料，並儲存到m_transactions
            m_transactions = []
            for transaction_group in [input_data["inbound"], input_data["outbound"]]:
                for transaction in transaction_group:
                    new_transaction = {
                        "symbol": str(transaction["currency"]["symbol"]),
                        "to": str(transaction["receiver"]["address"]),
                        "timestamp": str(transaction["timestamp"]),
                        "hash": str(transaction["tx_hash"]),
                        "value": str(float(transaction["amount"] * 1000000)),  # Convert to micro units
                        "from": str(transaction["sender"]["address"])
                    }
                    m_transactions.append(new_transaction)

            print('-------------------------')
            print(m_transactions)

            # 剖析dustin的neo4j資料，並儲存到d_transactions
            def dustin_transaction(transaction, d_transactions):
                if transaction["symbol"] == 'TRX':
                    api_url = "http://192.168.200.73:8000/tron/transaction"
                else:
                    api_url = "http://192.168.200.73:8000/tron/tokenTransfer"

                d_response = requests.post(api_url, json={"hash": transaction["hash"]})

                d_response = json.loads(d_response.text).get("transactions", [])

                for d_transaction in d_response:
                    new_transaction = {
                        "symbol": str(transaction['symbol']),
                        "to": str(d_transaction["to"]),
                        "timestamp": str(d_transaction["timestamp"]),
                        "hash": str(d_transaction["hash"]),
                        "value": str(d_transaction["value"]),
                        "from": str(d_transaction["from"])
                    }
                    d_transactions.append(new_transaction)

            d_transactions = []
            
            for idx, transaction in enumerate(m_transactions, 1):
                dustin_transaction(transaction, d_transactions)

            print('-------------------------')
            print(d_transactions)

            # 比較m_transactions和d_transactions，並將結果寫入csv文件
            status = 'Pass' if m_transactions == d_transactions else 'Fail'
            print(status)
            csv_writer.writerow([json.dumps(m_transactions), json.dumps(d_transactions), status])

print(f'Data written to {csv_file_path}')