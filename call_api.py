import requests

# /bitcoin/transaction

# api_url = "http://192.168.200.73:8000/bitcoin/transaction"
# payload = {
#     "address": "3P3kJke64M3YneP65eBwHEuA1PZm7gvBEx",
#     "startTime": 1701792000,
#     "endTime": 1701878400,
#     "minValue": 0,
#     "maxValue": 9223372036854776
# }
# response = requests.post(api_url, json=payload)
# print(response.status_code)
# print(response.text)


# /bitcoin/transaction/{block}/{hash}

hash = "9c506b8954a647ac4920f6be0d6feacf41a6c3a1a664790ea83c04835d6178ad"
block = "804274"
api_url = f"http://192.168.200.73:8000/bitcoin/transaction/{block}/{hash}"
response = requests.get(api_url)
print(response.status_code)
print(response.text)