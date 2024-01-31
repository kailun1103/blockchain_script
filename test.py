import csv

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

csv_file_name = 'test.csv'

print('Start checking data')

with open(csv_file_name, 'r', newline='') as f:
    rows = []
    reader = csv.reader(f)
    header = next(reader)  # Skip header
    header.append('hash check')  # Add hash check column header
    rows.append(header)
    for row in reader:
        result = check_hash_data(row)
        row.append(result)  # Append check result to row
        rows.append(row)  # Add row to the list

# Write back to the same file
with open(csv_file_name, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print('Done checking data')
