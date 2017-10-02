# mpcs_ticker.py
#
# Copyright (C) 2011-2017 Vas Vasiliadis
# University of Chicago
#
# Basic simulator to generate trades for hack week
#
##
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

#20170610
#Flora Tsai

import sys
import time
import boto3
import json
import random
import uuid
from datetime import datetime
import calendar

region = "us-east-1"
kinesis = boto3.client('kinesis', region_name=region)
kinesis_stream = "<username>_trades"

sqs = boto3.resource('sqs', region_name=region)
sqs_queue_name = "<username>_stop_trading"
queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)

stocks = [
  {"symbol": "MCS", "base_price": 21.13},
  {"symbol": "SNA", "base_price": 148.25},
  {"symbol": "FLIR", "base_price": 31.52},
  {"symbol": "JDSU", "base_price": 13.45},
  {"symbol": "ALP", "base_price": 456.78},
  {"symbol": "AMZN", "base_price": 1003.45}]

'''
Generate random "trades" and post them to a Kinesis stream
'''
def produce_trades(kinesis=None, delay=0):
  timer = {"MCS": time.time() - 11, "SNA": time.time() - 11, "FLIR": time.time() - 11, 
        "JDSU": time.time() - 11, "ALP": time.time() - 11, "AMZN": time.time() - 11}
  # Create a random number generator
  generator = random.SystemRandom(time.time())

  while True:
    # Generate a unique ID for the trade
    trade = {'id': str(uuid.uuid4())}

    # Pick a stock for which to generate a trade and get its symbol
    stock = random.randint(0,5)
    symbol = stocks[stock]["symbol"]

    # extract from SQS
    messages = queue.receive_messages(WaitTimeSeconds=0)
    if len(messages) > 0:
      for message in messages:
        msg_body = json.loads(message.body)['Message']
        timer[msg_body] = time.time()  
        message.delete()

    # process when the time difference is greater than 10s 
    if (time.time() - timer[symbol]) > 10.0:
      # Generate the trade price (a random, small increment on the base price)
      price = round(stocks[stock]["base_price"] + round(generator.random(), 2), 2)

      # Simulate an unusual pricing events
      black_swan = random.randint(0,99)
      if (black_swan < 10):
        print(symbol)
        swing = random.randint(0,1)
        print("******** Here comes the swan: {0}").format(swing)
        if (swing == 0):
          price = round(price - (price * 0.7), 2)
        else:
          price = round(price * 2, 2)

      # Create the trade record
      trade['symbol'] = symbol
      trade['price'] = price
      trade['size'] = int(round(generator.random() * 1000, 0) * 100)
      cur_time = datetime.utcnow()
      trade['trade_time'] = datetime.strftime(cur_time, "%Y%m%dT%H%M%S")
      trade['epoch_time'] = calendar.timegm(cur_time.timetuple())

      # Drop the trade record into the Kinesis stream
      kinesis.put_record(
        StreamName=kinesis_stream, 
        Data=json.dumps(trade), 
        PartitionKey="pkey")
      print(json.dumps(trade))

    # Wait for a bit before generating next trade
    time.sleep(delay)


'''
Pull "trades" from Kinesis stream; just to test reading from Kinesis
'''
def consume_trades(kinesis=None, window=0):
  shard_id = 'shardId-000000000000'
  shard = kinesis.get_shard_iterator(StreamName=kinesis_stream, 
    ShardId=shard_id, ShardIteratorType='LATEST')['ShardIterator']

  while True:
    time.sleep(window)
    feed_data = kinesis.get_records(ShardIterator=shard, Limit=100)
    iterator = feed_data['NextShardIterator']
    for item in feed_data['Records']:
      print item['Data']


if __name__ == '__main__':

  if (sys.argv[1] == 'produce'):
    print ("Ticker started. Generating pseudorandom trades...")
    produce_trades(kinesis=kinesis, delay=float(sys.argv[2]))

  elif (sys.argv[1] == 'consume'):
    print ("Consuming and processing trades...")
    consume_trades(kinesis=kinesis, window=float(sys.argv[2]))

  else:
    print("Must specify role: 'produce' or 'consume'")

### EOF