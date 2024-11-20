import asyncio

import httpx  # async
from flask import jsonify
import logging


async def post_to_replica(target_url, data, message_id):
    try:
        # asynchronously using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                json={"message": data['message'], "message_id": message_id},
                timeout=30  # for this iteration
            )
        # Check for success
        if response.status_code == 201:
            m = f"Message forwarded successfully to the secondary server {target_url}"
            logging.info(m)
            return m, 201
        m_failure = f"Failed to forward the message. Status code: {response.status_code}"
        logging.error(m_failure)
        return m_failure, response.status_code

    except httpx.RequestError as e:
        m = f"Error while forwarding message: {e} {target_url}"
        logging.error(m)
        return m, 500


def return_confirmation_to_user(message_id, concern):
    logging.info(f"Message with ID {message_id} confirmed to user with concern {concern}")
    return jsonify({"message": "Message confirmed", "id": message_id}), 200


async def replicate_to_pending_replicas2(message_id, data, pending_replicas):
    """Function to handle replication tasks for pending replicas."""
    logging.info("replicate_to_pending_replicas started")
    if not pending_replicas:
        logging.info('No pending replicatons left')
    tasks = []
    for url in pending_replicas:
        logging.info(f'Starting replication to {url}')
        tasks.append(post_to_replica(url, data, message_id))

    # Await all tasks concurrently using asyncio.gather()
    results = await asyncio.gather(*tasks)

    # Process the results
    for confirmation_message, status_code in results:
        logging.info(f"Replication result final: {confirmation_message}")

    return

def total_ordering(messages):
    sorted_message_ids = sorted(messages.keys(), key=int)

    contiguous_messages = []
    last_message_id = -1

    # Iterate over the sorted message ids
    for message_id in sorted_message_ids:
        message_id_int = int(message_id)

        if last_message_id == -1 or message_id_int == last_message_id + 1:
            contiguous_messages.append({'message_id': message_id_int, 'message': messages[message_id]})
            last_message_id = message_id_int
        else:
            break
    return contiguous_messages, last_message_id


def run_in_thread(message_id, data, pending_replicas):
    # This function is run in a separate thread
    asyncio.run(replicate_to_pending_replicas2(message_id, data, pending_replicas))

