import logging
from flask import Flask, request, jsonify
import asyncio
import itertools
from utils import post_to_replica, return_confirmation_to_user, total_ordering, run_in_thread
import threading

app = Flask(__name__)

# Configure logging to a file
logging.basicConfig(
    filename='/app/shared_data/server.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

messages = {}
id_counter = itertools.count()
REPLICA_TIMEOUT = 30  # max Timeout in seconds for replica response

@app.route('/messages', methods=['POST'])
async def add_message():
    global id_counter
    data = request.get_json()

    # Log the incoming request
    logging.info("Received POST request with data on master: %s", data)

    # Validate the incoming data
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    # Record the message in the master
    concern = data.get('concern', 3)
    message_id = str(next(id_counter))
    messages[message_id] = data['message']
    logging.info(f"Message '{data['message']}' added to master with ID: {message_id}")


    # For concern > 1, process replica confirmations
    confirmations_received = 1  # Already confirmed by the master
    replica_urls = [
        'http://replica_1:8050/messages',
        'http://replica_2:8080/messages'
    ]
    confirmation_tasks = [
        asyncio.create_task(post_to_replica(url, data, message_id)) for url in replica_urls
    ]

    # Confirm to user immediately if concern level is 1
    if confirmations_received >= concern:
        response = return_confirmation_to_user(message_id, concern)
        # Schedule replication tasks in the background
        pending_replicas = [url for url, t in zip(replica_urls, confirmation_tasks) if not t.done()]
        thread = threading.Thread(target=run_in_thread, args=(message_id, data, pending_replicas))
        thread.start()
        return response

    try:
        # Await confirmations up to the concern level
        for task in asyncio.as_completed(confirmation_tasks, timeout=REPLICA_TIMEOUT):
            try:
                # logging.info(f'awaiting task {task}')
                confirmation = await task
                # logging.info(f'conf {confirmation}')
                if confirmation[1] == 201:
                    confirmations_received += 1
                if confirmations_received >= concern:
                    response = return_confirmation_to_user(message_id, concern)
                    # User concern met; schedule remaining replication in the background
                    pending_replicas = [url for url, t in zip(replica_urls, confirmation_tasks) if not t.done()]
                    thread = threading.Thread(target=run_in_thread, args=(message_id, data, pending_replicas))
                    thread.start()
                    return response

            except asyncio.TimeoutError:
                logging.warning("Replica timed out")

    except Exception as e:
        logging.error(f"Error during replication: {e}")

    return jsonify({"message": "Replication initiated", "id": message_id}), 202

@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request for messages from master")
    contiguous_messages, last_message_id = total_ordering(messages)
    logging.info(
        f"Returning {len(contiguous_messages)} messages up to the last contiguous sequence (ID: {last_message_id})")
    return jsonify({"messages": contiguous_messages}), 200


if __name__ == '__main__':
    port = 5010
    print(f"Starting the app on port {port}")
    app.run(host='0.0.0.0', port=port)
