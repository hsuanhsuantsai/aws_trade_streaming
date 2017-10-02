from __future__ import print_function

import boto3
import base64
import json
from decimal import Decimal

region = "us-east-1"
dynamoDB = boto3.resource('dynamodb', region_name=region)
my_table = dynamoDB.Table("<username>-trades")

sns = boto3.resource('sns', region_name=region)
topic = sns.Topic("arn:aws:sns:us-east-1::<username>_check_trade")
	
def lambda_handler(event, context):
    records = event['Records']
    for r in records:
        if r is not None:
            data = base64.b64decode(r['kinesis']['data'])
            # print(data)
            data = eval(data)
            data_to_DB = {'symbol':data['symbol'],
                            'price': Decimal(str(data['price'])),
                            'size': data['size'],
                            'trade_time': data['trade_time'],
                            'epoch_time': data['epoch_time'],
                            'id': data['id'],
                            'shard_id':r['eventID']}
            my_table.put_item(Item=data_to_DB)
            
            data_to_TP = {'symbol':data['symbol'],
                            'price': data['price'],
                            'size': data['size'],
                            'trade_time': data['trade_time'],
                            'epoch_time': data['epoch_time'],
                            'id': data['id'],
                            'shard_id':r['eventID']}
            topic.publish(Message=json.dumps(data_to_TP))
        else:
            print("No data to be stored")

    return "Saved " + str(len(records)) + "trades to DB"
        
        