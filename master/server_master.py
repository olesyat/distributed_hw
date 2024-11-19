import logging
from flask import Flask, request, jsonify
import asyncio
import itertools
from utils import post_to_replica, return_confirmation_to_user, replicate_to_pending_replicas, total_ordering

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
REPLICA_TIMEOUT = 20  # max Timeout in seconds for replica response

@app.route('/messages', methods=['POST'])
async def add_message():
    global id_counter
    data = request.get_json()

    # Log the incoming request
    logging.info("Received POST request with data on master: %s", data)

    # Validate the incoming data
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    concern = data.get('concern', 3)
    message_id = str(next(id_counter))
    messages[message_id] = data['message']

    logging.info(f"Message '{data['message']}' added to master with ID: {message_id}")
    confirmations_received = 1

    replica_urls = [
        'http://replica_1:8050/messages',
        'http://replica_2:8080/messages'
    ]

    confirmation_tasks = [
        asyncio.create_task(post_to_replica(url, data, message_id)) for url in replica_urls
    ]

    try:
        # Await confirmations but return as soon as the concern level is met
        for task in asyncio.as_completed(confirmation_tasks, timeout=REPLICA_TIMEOUT):
            try:
                confirmation = await task
                if confirmation[1] == 201:
                    confirmations_received += 1

                if confirmations_received >= concern:
                    response = return_confirmation_to_user(message_id, concern)

                    # background replication for pending replicas if any
                    pending_replicas = [url for url, t in zip(replica_urls, confirmation_tasks) if not t.done()]
                    if pending_replicas:
                        asyncio.create_task(replicate_to_pending_replicas(message_id, data, pending_replicas))
                    return response

            except asyncio.TimeoutError:
                logging.warning("Replica timed out")

    except Exception as e:
        logging.error(f"Error during replication: {e}")

    return jsonify({"message": "Replication initiated", "id": message_id}), 202  # if not met concern


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
