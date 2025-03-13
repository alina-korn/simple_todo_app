from flask import Flask, request, jsonify
from kafka import KafkaProducer, KafkaConsumer
import json
import psycopg2

app = Flask(__name__)
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

db_config = {
    'dbname': 'todo_db',
    'user': 'user',
    'password': 'password',
    'host': 'postgres'
}

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    user_id = data['user_id']
    title = data['title']
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("INSERT INTO todos (user_id, title, completed) VALUES (%s, %s, %s) RETURNING id",
                (user_id, title, False))
    todo_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    producer.send('todo-events', {
        'event': 'todo_created',
        'todo_id': todo_id,
        'user_id': user_id,
        'title': title
    })
    return jsonify({'message': 'Todo created', 'todo_id': todo_id})

def consume_user_events():
    consumer = KafkaConsumer(
        'user-events',
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    for message in consumer:
        print(f"Received user event: {message.value}")

if __name__ == '__main__':
    from threading import Thread
    Thread(target=consume_user_events).start()
    app.run(host='0.0.0.0', port=5002)