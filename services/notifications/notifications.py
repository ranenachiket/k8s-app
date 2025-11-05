# This will be the kafka consumer service
from confluent_kafka import Consumer, TopicPartition
import logging
import sys
sys.stdout.flush()

log_handler = logging.FileHandler('notifications.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


def notifications():
    logger.info('=' * 100)
    logger.info('Initializing consumer')
    kafka_endpoint = 'kafka-0.kafka-headless.kafka.svc.cluster.local:9092'
    consumer_config = {
        'bootstrap.servers': kafka_endpoint,
        'group.id': 'orders-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_config)
    logger.info('Initializing consumer complete.')
    print('Initializing consumer complete.')

    # Manually assign a specific partition of the topic
    topic = "orders"
    partition = 0
    tp = TopicPartition(topic, partition)
    # Assign partitions manually (no consumer group rebalance)
    consumer.assign([tp])

    # consumer.subscribe(['orders'])

    logger.info('Listening for messages:')
    print('Listening for messages:')
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            elif msg.error():
                print(f"Consumer error: {msg.error()}")
                logger.error(f"Consumer error: {msg.error()}")
            else:
                print(f"Received message: {msg.value().decode('utf-8')}")
                logger.info(f"Received message: {msg.value().decode('utf-8')}")
    except Exception as e:
        print(f"Error polling Kafka: {e}")
        logger.error(f"Error polling Kafka: {e}")
    except KeyboardInterrupt:
        print("Stopped consuming")
    finally:
        consumer.close()


if __name__ == '__main__':
    try:
        notifications()
    except KeyboardInterrupt:
        logger.info('orders service terminated')
