# This will be the kafka consumer service
from confluent_kafka import Consumer, TopicPartition
import logging
import sys
import json
import psycopg2
sys.stdout.flush() # To flush the print output to the kubectl log - not working

log_handler = logging.FileHandler('notifications.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


def database_conn():
    # Postgres Config
    PG_HOST = '192.168.87.33'
    PG_PORT = '5432'
    PG_USER = 'postgres'
    PG_PASSWORD = 'postgres'
    PG_DATABASE = 'app'

    # Connect to Postgres

    db_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE
    )
    logger.info(f'Connecting to Database')
    cursor = db_conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        row_id SERIAL PRIMARY KEY,
        order_id TEXT,
        username TEXT,
        item TEXT,
        quantity NUMERIC,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db_conn.commit()
    logger.info(f'Connected to Database')
    return db_conn, cursor


def write_to_db(db_conn, cursor, message):
    try:
        logger.info(f"Writing message to db: {message}")
        cursor.execute(
            "INSERT INTO orders (order_id, username, item, quantity) VALUES (%s, %s, %s, %s);",
            (message['order_id'], message['user'], message['item'], message['quantity'])
        )
        db_conn.commit()
        logger.info(f"Successfully Written message to db: {message}")
    except Exception as e:
        logger.error("DB insert error:", e)
        db_conn.rollback()


def notifications(db_conn, cursor):
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

    # # Manually assign a specific partition of the topic
    # # Manual assigning will hardcore to partition 0 and disable the consumer-group coordination causing duplicate with replicated pods.
    # topic = "orders"
    # partition = 0
    # tp = TopicPartition(topic, partition)
    # # Assign partitions manually (no consumer group rebalance)
    # consumer.assign([tp])

    consumer.subscribe(['orders'])

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
                raw_message = msg.value().decode('utf-8')
                data = json.loads(raw_message)
                print(f"Received message: {data}")
                logger.info(f"Received message: {data}")
                write_to_db(db_conn, cursor, data)


    except Exception as e:
        print(f"Error polling Kafka: {e}")
        logger.error(f"Error polling Kafka: {e}")
    except KeyboardInterrupt:
        print("Stopped consuming")
    finally:
        consumer.close()


if __name__ == '__main__':
    try:
        db_conn, cursor = database_conn()
        notifications(db_conn, cursor)
    except KeyboardInterrupt:
        logger.info('orders service terminated')
