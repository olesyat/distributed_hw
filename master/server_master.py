import logging
from flask import Flask, request, jsonify
import asyncio
from utils import post_to_replica

app = Flask(__name__)

# Configure logging to a file
logging.basicConfig(
    filename='/app/shared_data/server.log',
    filemode='w',  # rewrite with each restart
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# In-memory list to store messages and incremental id
messages = {}
id_counter = 0
REPLICA_TIMEOUT = 20

@app.route('/messages', methods=['POST'])
async def add_message():
    global id_counter
    data = request.get_json()

    # Log the incoming request
    logging.info("Received POST request with data on master: %s", data)

    # Validate the incoming data
    if not data or 'message' not in data:
        m_failure = "Invalid request missing 'message' or 'message_id'"
        logging.error(m_failure)
        return jsonify({"error": m_failure}), 400

    message_id = str(id_counter)
    messages[message_id] = data['message']
    id_counter += 1

    logging.info("Message '%s' added to master with ID: %s", data['message'], message_id)


    # assume we know replicas urls upfront
    try:
        replica1_url = 'http://replica_1:8050/messages'
        replica2_url = 'http://replica_2:8080/messages'
        results = await asyncio.gather(
            asyncio.wait_for(post_to_replica(replica1_url, data, message_id), REPLICA_TIMEOUT),
            asyncio.wait_for(post_to_replica(replica2_url, data, message_id), REPLICA_TIMEOUT),
            # return_exceptions=True
        )

        responses_status_codes = [x[1] for x in results]
        if any(status_code != 201 for status_code in responses_status_codes):
            m_failure2 = 'Failed to add message to one or more replicas.'
            logging.error(m_failure2)
            return jsonify({"error": m_failure2}), 500
        else:
            m = f"Message '{data['message']}' added to ALL replicas with ID: {message_id}"
            logging.info(m)
            return jsonify({"message": m}), 201

    except Exception as e:
        m_error = f"Error during replication: {e}"
        logging.error(m_error)
        return jsonify({"error": m_error}), 500


@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request for messages from master")
    return jsonify({"messages": messages}), 200


if __name__ == '__main__':
    port = 5010
    print(f"Starting the app on port {port}")
    app.run(host='0.0.0.0', port=port)
