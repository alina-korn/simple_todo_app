from flask import Flask, request, jsonify
from kafka import KafkaProducer
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

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                (username, password))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    producer.send('user-events', {'event': 'user_registered', 'user_id': user_id})
    return jsonify({'message': 'User registered', 'user_id': user_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)