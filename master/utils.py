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
                timeout=10 # for this iteration
            )
        # Check for success
        if response.status_code == 201:
            m = "Message forwarded successfully to the secondary server"
            logging.info(m)
            return jsonify({"message": m, "id": message_id}), 201
        m_failure = f"Failed to forward the message. Status code: {response.status_code}"
        logging.error(m_failure)
        return jsonify({"error": m_failure}), 500

    except httpx.RequestError as e:
        m = f"Error while forwarding message: {e}"
        logging.error(m)
        return jsonify({"error": m}), 500
