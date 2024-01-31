from neo4j import GraphDatabase, Driver
from neo4j import Driver

URI = "neo4j://192.168.200.83:7687"
AUTH = ("reader", "P@ssw0rd")

def neo4j_address_data(driver: Driver, hash, database):
    with driver.session(database=database) as session:
        result = session.run(
            f"""
                MATCH p=()-->(t:transaction)-->()
                WHERE t.hash = "{hash}"
                RETURN t, p, [rel IN relationships(p) | rel.value] AS relationship_values
            """
        ).data()


        # 轉入地址數量/轉出地址數量/時間
        input_count = result[0]['t']['input_count']
        output_count = result[0]['t']['output_count']
        timestamp = int(result[0]['t']['timestamp'])

        # 轉入的地址和金額/轉出的地址和金額
        input_address_amount = {}
        output_address_amount = {}
        
        for item in result:
            input_address = item['p'][0]['address']
            output_address = item['p'][4]['address']
            input_amount = item['relationship_values'][0]
            output_amount = item['relationship_values'][1]
            
            if input_address in input_address_amount:
                input_address_amount[input_address] += input_amount
            else:
                input_address_amount[input_address] = input_amount
            
            if output_address in output_address_amount:
                output_address_amount[output_address] += output_amount
            else:
                output_address_amount[output_address] = output_amount
        
        transactions = [{
            'timestamp': timestamp,
            'inputs': [{'from': k, 'value': int(v / output_count)} for k, v in input_address_amount.items()],
            'hash': hash,
            'outputs': [{'to': k, 'value': int(v / input_count)} for k, v in output_address_amount.items()]
        }]

        print({'transactions': transactions})

block = 804274

if 654321 <= block <= 771137:
    database = 'bitcoin'
elif 771138 <= block <= 819676:
    database = 'bitcoin2'
elif 0 <= block <= 299590:
    database = 'bitcoin3'
elif 299591 <= block <= 491537:
    database = 'bitcoin4'
else:
    database = 'bitcoin5'

hash = "9c506b8954a647ac4920f6be0d6feacf41a6c3a1a664790ea83c04835d6178ad"

with GraphDatabase.driver(URI, auth=AUTH) as neo4j_driver:
    neo4j_address_data(neo4j_driver, hash, database)
