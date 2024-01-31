import os
import csv

# 获取"data/"目录中的所有CSV文件路径
csv_directory = "data/"
csv_files = [file for file in os.listdir(csv_directory) if file.endswith(".csv")]

# 合并CSV文件
merged_rows = []
for file in csv_files:
    file_path = os.path.join(csv_directory, file)
    with open(file_path, 'r', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        header = rows[0]
        rows = rows[1:]
        merged_rows.extend(rows)

# 将合并的数据写入新的CSV文件
merged_file_path = "data/merged_data.csv"
with open(merged_file_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)  # 写入标题行
    writer.writerows(merged_rows)  # 写入数据行
