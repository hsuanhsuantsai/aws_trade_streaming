# aws_trade_streaming
Try on kinesis and lambda  

## Brief Introduction
Please refer to flowchart.png

1. mpcs_ticker.py generates pseudorandom trades to feed into Kinesis
2. processor.py works as AWS lambda to store trade information in DynamoDB and publish it to sns topic -- \<username\>_check_trade
3. trade_check.py works as AWS lambda to pull data from DynamoDB and check if there's any anomaly.
   If anomaly is detected, publish a message to sns topic -- \<username\>_stop_trading to notify ticker to stop trading
4. An sqs -- \<username\>_stop_trading will subscribe sns -- \<username\>_stop_trading
5. mpcs_ticker.py pulls messages from sqs -- \<username\>_stop_trading to stop trades of the specific stocks for a while

## Usage
* python mpcs_ticker.py produce \<delay\>
* python mpcs_ticker.py consume \<delay\>  
  - Used only for testing reading from Kinesis
