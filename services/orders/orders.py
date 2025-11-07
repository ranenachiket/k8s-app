# This will be the kafka producers server
from confluent_kafka import Producer, KafkaException
from flask import Flask, request, Response, jsonify
from random import choice
import uuid, time
import json
import psycopg2
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
logger.info('Initializing producer')
print('Initializing producer')
producer = Producer(producer_config)
logger.info('Initializing producer complete.')
print('Initializing producer complete.')


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

    logger.info(f'Connected to Database')
    return db_conn, cursor

def kafka_delivery_report(err, msg):
    if err:
        logger.info(f'ERROR: Order message Failed to send to kafka: {err}')
        print(f'ERROR: Order message Failed to send to kafka: {err}')
    else:
        logger.info(f'SUCCESS: message sent to kafka successfully: {msg.value().decode("utf-8")}')
        print(f'SUCCESS: message sent to kafka successfully: {msg.value().decode("utf-8")}')
        logger.info(f'SUCCESS: message sent to kafka topic: {msg.topic()}, partition: {msg.partition()}, offset: {msg.offset()}')
        print(f'SUCCESS: message sent to kafka topic: {msg.topic()}, partition: {msg.partition()}, offset: {msg.offset()}')

def kafka_publish(data_bytes):
    logger.info('=' * 100)
    try:
        logger.info(f'Attempting to send order message to kafka endpoint {kafka_endpoint}')
        producer.produce(topic='orders', value=data_bytes, callback=kafka_delivery_report)
        logger.info(f'Flushing messages to kafka')
        result = producer.flush(timeout=10)
        logger.info(result)
    except KafkaException as e:
        logger.exception(f'Kafka exception: {e}')
        return 'FAILED: Orders sending to Kafka failed', 500
    except KeyboardInterrupt:
        logger.error(f'ABORT: Aborted by user.')
        print(f'ABORT: Aborted by user.')
    else:
        logger.info(f'Flushed messages to kafka successfully')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/data', methods=['POST'])
def orders_post():
    order = request.get_json()
    if order and 'user' in order and 'item' in order and 'quantity' in order:
        order_id = f'{int(time.time())}-{uuid.uuid4().hex[:8]}',
        order['order_id'] = order_id[0]
        logger.info(f"Received JSON data: {order}")
        json_data = json.dumps(order)
        data_bytes = json_data.encode('utf-8')
        kafka_publish(data_bytes)
        return Response(order_id, status=200)
    return f"No JSON data received or Malformed json received: {order}", 400

@app.route('/order/<order_id>', methods=['GET'])
def orders_get(order_id):
    try:
        conn, cursor = database_conn()
        # cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Fetch row by ID
        cursor.execute(f"SELECT * FROM orders WHERE order_id = '{order_id}';")
        order = cursor.fetchone() # Returns Tuple of values

        # Close the db connections cleanly
        cursor.close()
        conn.close()

        if order is None:
            return jsonify({"error": "Order not found"}), 404

        # Convert to dictionary
        order_data = {
            "order_id": order[1],
            "username": order[2],
            "item": order[3],
            "quantity": order[4],
        }
        return jsonify(order_data), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/random', methods=['GET'])
def orders_random():
    order_id = f'{int(time.time())}-{uuid.uuid4().hex[:8]}'
    order = {
        "order_id": order_id,
        "user": choice(["Alice","Bob", "Tom", "Jane", "Eric", "John"]),
        "item": choice(["veg pizza","chicken burger", "Thai fried rice", "Dosa"]),
        "quantity": choice(list(range(20)))
    }
    json_data = json.dumps(order)
    data_bytes = json_data.encode('utf-8')
    kafka_publish(data_bytes)
    return Response(order_id, status=200)



if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0", port=8080, debug=True)
    except KeyboardInterrupt:
        logger.info('orders service terminated')
