from __future__ import print_function

import boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
import calendar

region = "us-east-1"
dynamoDB = boto3.resource('dynamodb', region_name=region)
my_table = dynamoDB.Table("<username>-trades")

sns = boto3.resource('sns', region_name=region)
topic = sns.Topic("arn:aws:sns:us-east-1::<username>_stop_trading")
  
def lambda_handler(event, context):
    sum = 0.0
    counter = 0
    input = eval(event['Records'][0]['Sns']['Message'])
    symbol = input['symbol']
    trade_price = input['price']
    print(symbol)
    time = calendar.timegm(datetime.utcnow().timetuple())
    #set N = 10
    response = my_table.query(IndexName='symbol_index', KeyConditionExpression=Key('symbol').eq(symbol), 
                                FilterExpression=Attr('epoch_time').gt(time-10))
    for item in response['Items']:
        sum += float(item['price'])
        counter += 1
    
    aver_price = sum/counter
        
    #anomaly
    if trade_price > aver_price*1.5 or trade_price < aver_price*0.4:
        print('Anomaly!!')
        my_table.update_item(Key={"id":input['id']}, UpdateExpression='SET #status = :val1',
                                    ExpressionAttributeNames={'#status': "status"}, 
                                    ExpressionAttributeValues={':val1': "HALTED"})
        
        #notify ticker to stop trading
        topic.publish(Message=input['symbol'])
    else:
        print("Good!")
    