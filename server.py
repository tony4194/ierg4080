from flask import Flask, request, jsonify
import redis
from model import SpamEmailClassifier
import threading
import queue
import json
import telepot
from telepot.loop import MessageLoop

app = Flask(__name__)

redis_client = redis.Redis(host='localhost', port=6379, db=0)

classifier = SpamEmailClassifier()

email_queue = queue.Queue()
result_queue = queue.Queue()

bot = telepot.Bot("6943609123:AAHc3cQdA4Hcn-6_HZJf7TdN-PWj3yonFSc")

def get_email_from_request():
    while True:
        email_body = email_queue.get()
        print("Got email from queue:", email_body)
        redis_client.lpush('email_queue', email_body)
        email_queue.task_done()

def process_email_from_queue():
    while True:
        email_body = redis_client.rpop('email_queue')
        if email_body:
            print("Processing email...")
            result = process_email(email_body.decode('utf-8'))
            print(result)
            redis_client.lpush('result_queue', json.dumps(result))

def process_email(email_body):
    label, probability = classifier.classify(email_body)
    return {'label': label, 'probability': probability}

def handle_telegram_message(msg):
    # print("Got message from Telegram:", msg)
    email_body = msg['text']
    email_queue.put(email_body)
    chat_id = msg['chat']['id']
    redis_client.lpush('chat_id', str(chat_id))

def retrieve_result_from_queue():
    while True:
        result_str = redis_client.rpop('result_queue')
        if result_str:
            print("Got result from queue...")
            result = json.loads(result_str)
            chat_id = redis_client.rpop('chat_id')
            if chat_id:
                print("Sending result to Telegram...")
                bot.sendMessage(chat_id.decode('utf-8'), f"label={result['label']}, probability={result['probability']}")

@app.route('/classify', methods=['POST'])
def classify_email():
    email_body = request.get_json()['email_body']
    email_queue.put(email_body)
    return jsonify({'message': 'Backend Email received, processing...'})

if __name__ == '__main__':
    t1 = threading.Thread(target=get_email_from_request)
    t2 = threading.Thread(target=process_email_from_queue)
    t3 = threading.Thread(target=retrieve_result_from_queue)
    t1.daemon = True
    t2.daemon = True
    t3.daemon = True
    t1.start()
    t2.start()
    t3.start()

    MessageLoop(bot, handle_telegram_message).run_as_thread()
    app.run()