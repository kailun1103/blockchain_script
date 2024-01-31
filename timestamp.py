from datetime import datetime, timedelta

def convert_date_to_timestamp(date):
    # 将字符串解析为datetime对象
    dt_object = datetime.strptime(date, '%Y-%m-%d')

    # 调整时区为UTC-8
    # dt_object += timedelta(hours=8)

    # 转换为timestamp
    formatted_timestamp = int(dt_object.timestamp())
    return formatted_timestamp

test = convert_date_to_timestamp('2023-10-05')
print(test)