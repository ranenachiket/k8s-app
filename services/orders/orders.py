# This will be the kafka producers server
from confluent_kafka import Producer, KafkaException
from flask import Flask
from random import choice
import uuid
import json
import logging
import sys
sys.stdout.flush()

app = Flask(__name__)

log_handler = logging.FileHandler('orders.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

kafka_endpoint = 'kafka-0.kafka-headless.kafka.svc.cluster.local:9092'
producer_config = {
    'bootstrap.servers': kafka_endpoint,
    'acks': 'all'
}

def kafka_delivery_report(err, msg):
    if err:
        logger.info(f'ERROR: Order message Failed to send to kafka: {err}')
        print(f'ERROR: Order message Failed to send to kafka: {err}')
    else:
        logger.info(f'SUCCESS: message sent to kafka successfully: {msg.value().decode("utf-8")}')
        print(f'SUCCESS: message sent to kafka successfully: {msg.value().decode("utf-8")}')
        logger.info(f'SUCCESS: message sent to kafka topic: {msg.topic()}, partition: {msg.partition()}, offset: {msg.offset()}')
        print(f'SUCCESS: message sent to kafka topic: {msg.topic()}, partition: {msg.partition()}, offset: {msg.offset()}')


@app.route('/orders', methods=['GET'])
def orders():
    logger.info('=' * 100)
    logger.info('Initializing producer')
    print('Initializing producer')
    producer = Producer(producer_config)
    logger.info('Initializing producer complete.')
    print('Initializing producer complete.')

    order = {
        "order_id": str(uuid.uuid4()),
        "user": choice(["Alic","Bob", "Tom", "Jane"]),
        "item": choice(["veg pizza","chicken burger", "Thai fried rice", "Dosa"]),
        "quantity": choice(list(range(20)))
    }
    json_data = json.dumps(order)
    data_bytes = json_data.encode('utf-8')

    try:
        logger.info(f'Attempting to send order message to kafka endpoint {kafka_endpoint}')
        producer.produce(topic='orders', value=data_bytes, callback=kafka_delivery_report)
        logger.info(f'Flushing messages to kafka')
        result = producer.flush(timeout=10)
        logger.info(result)
    except KafkaException:
        logger.error(f'FAILED: Orders Failed sending to Kafka')
        print('FAILED: Orders Failed sending to Kafka', 500)
        return 'FAILED: Orders Failed sending to Kafka', 500
    except KeyboardInterrupt:
        logger.error(f'ABORT: Aborted by user.')
        print(f'ABORT: Aborted by user.')
    else:
        logger.info(f'Flushed messages to kafka successfully')
        return 'Published to Kafka', 200



if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0", port=8080, debug=True)
    except KeyboardInterrupt:
        logger.info('orders service terminated')
