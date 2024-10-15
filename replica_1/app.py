import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(
    filename='/app/shared_data/replica1.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# In-memory dictionary to store messages
messages = {}
REPLICA = 1

@app.route('/messages', methods=['POST'])
async def add_message():
    global REPLICA
    data = request.get_json()
    client_ip = request.remote_addr # get client ip
    logging.info(f"Received POST request on replica{REPLICA} from %s with data: %s", client_ip, data)

    # Validate the incoming data
    if not data or 'message' not in data or 'message_id' not in data:
        m_failure = "Invalid request missing 'message' or 'message_id'"
        logging.error(m_failure)
        return jsonify({"error": m_failure}), 400

    message_id = data['message_id']
    messages[message_id] = data['message']
    m = f"Message {data['message']} added to replica{REPLICA}  with ID: {message_id}"
    logging.info(m)
    return jsonify({"message": m}), 201


@app.route('/messages', methods=['GET'])
def get_messages():
    logging.info("Received GET request for messages from secondary")
    return jsonify({"messages": messages}), 200


if __name__ == '__main__':
    port = 8050
    app.run(host='0.0.0.0', port=port)
