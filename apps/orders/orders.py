# This will be the kafka producers server
from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST
from confluent_kafka import Producer, KafkaException
from flask import Flask, request, Response, jsonify
from random import choice
import uuid, time, json, psycopg2, psycopg2.extras, logging, sys
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

DB_QUERY_COUNT = Counter('db_query_total', 'Total number of DB queries executed')
DB_QUERY_DURATION = Summary('db_query_duration_seconds', 'Time taken for DB query execution')

# Define global metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Summary(
    'http_request_duration_seconds',
    'Time taken to process HTTP requests',
    ['endpoint']
)

def post_metrics(route):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter() # measure start time of request call
            response = func(*args, **kwargs) # Execute the original function
            elapsed = time.perf_counter() - start
            status = response.status_code if isinstance(response, Response) else (
                response[1] if isinstance(response, tuple) else 200)
            REQUEST_COUNT.labels(request.method, route, status).inc() # Incrementing the HTTP request counter
            REQUEST_LATENCY.labels(route).observe(elapsed) # Record the HTTP response time.
            return response
        wrapper.__name__ = func.__name__ # to avoid the AssertionError: View function mapping is overwriting an existing endpoint function: wrapper
        return wrapper
    return decorator


def database_conn():
    # Postgres Config
    PG_HOST = '192.168.87.33'
    PG_PORT = '5432'
    PG_USER = 'postgres'
    PG_PASSWORD = 'postgres'
    PG_DATABASE = 'app'

    # Connect to Postgres
    try:
        logger.info(f'Connecting user "{PG_USER}" to database "{PG_DATABASE}" at "{PG_HOST}:{PG_PORT}"')
        db_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DATABASE
        )

        # cursor = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor = db_conn.cursor()
    except psycopg2.Error as msg:
        logger.error(f'ERROR connecting user {PG_USER} to database {PG_DATABASE} at {PG_HOST} port {PG_PORT}: {msg}')
    else:
        logger.info(f'SUCCESS: Connected user {PG_USER} to database {PG_DATABASE} at {PG_HOST} port {PG_PORT}')
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
        # result = producer.flush(timeout=10) # expensive
        result = producer.poll(0)
        logger.info(result)
    except KafkaException as msg:
        logger.exception(f'Kafka exception: {msg}')
        return 'FAILED: Orders sending to Kafka failed', 500
    except KeyboardInterrupt:
        logger.error(f'ABORT: Aborted by user.')
        print(f'ABORT: Aborted by user.')
    else:
        logger.info(f'Flushed messages to kafka successfully')

def run_db_query(query):
    db_conn, db_cursor = database_conn()
    try:
        start = time.perf_counter()
        db_cursor.execute(query)
    except psycopg2.Error as msg:
        logger.error(f'ERROR: Failed to run the query {query}: {msg}')
    else:
        data = db_cursor.fetchall()  # Returns Tuple of values
        end = time.perf_counter()
        DB_QUERY_COUNT.inc()
        DB_QUERY_DURATION.observe(end - start)
        return data
    finally:
        db_conn.close()
        db_cursor.close()

def parse_db_data(data):
    if not data:
        return jsonify({"error": "Order not found"}), 404
    # List of dictionaries
    order_data = [
        {"order_id": row[1], "username": row[2], "item": row[3], "quantity": row[4]}
        for row in data
    ]
    return jsonify(order_data), 200

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/random', methods=['GET'])
@post_metrics('/random')
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

@app.route('/data', methods=['POST'])
@post_metrics('/data')
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
    return Response(f"No JSON data received or Malformed json received: {order}", 400)

@app.route('/order/<order_id>', methods=['GET'])
@post_metrics('/order')
def orders_get(order_id):
    try:
        logger.info(f'Fetching order by id {order_id} from the database, Executing the db query.')
        query = f"SELECT * FROM orders WHERE order_id = '{order_id}';"
        data = run_db_query(query)
    except Exception as e:
        print("Error:", e)
        return Response(f'ERROR: {str(e)}', 500)
    else:
        logger.info(f'Fetched data from the database successfully.')
        return parse_db_data(data)

@app.route('/count/<count>', methods=['GET'])
@post_metrics('/count')
def orders_count(count):
    try:
        count = int(count)
    except TypeError as msg:
        logger.error(f'ERROR: count {count}, Please provide valid count non-zero integer value')
        Response(f'Invalid count: {count}', 400)
    else:
        count = int(count)
        if count < 1:
            logger.error(f'ERROR: count {count}, Please provide valid count non-zero integer value')
            Response(f'Invalid count: {count}', 400)
        else:
            try:
                logger.info(f'Fetching {count} entries from the database, Executing the db query.')
                query = f"SELECT * FROM orders ORDER BY created_at DESC LIMIT {count};"
                data = run_db_query(query)
            except Exception as msg:
                logger.error("Error:", msg)
                return Response(f'ERROR: {str(msg)}', 500)
            else:
                logger.info(f'Fetched data from the database successfully.')
                return parse_db_data(data)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0", port=8080, debug=True)
    except KeyboardInterrupt:
        logger.info('orders service terminated')
