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