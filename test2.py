import csv

def check_address_data(row):
    crawler_data = eval(row[5])
    api_data = eval(row[6])
    
    crawler_inputs = crawler_data['transactions'][0]['inputs']
    crawler_outputs = crawler_data['transactions'][0]['outputs']
    api_inputs = api_data['transactions'][0]['inputs']
    api_outputs = api_data['transactions'][0]['outputs']

    print(crawler_outputs)

    # 检查输入
    for crawler_input, api_input in zip(crawler_inputs, api_inputs):
        if crawler_input != api_input:
            return f"Fail: Input address {crawler_input}"

    # 检查输出
    for crawler_output, api_output in zip(crawler_outputs, api_outputs):
        if crawler_output != api_output:
            return f"Fail: Input address {crawler_output}"

    # 如果全部匹配，则返回Pass
    return "Pass"


csv_file_name = 'test.csv'

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