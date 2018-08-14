import json


def parse_message(m):
    message = json.loads(m)
    if "event" in message and message['event'] == "posted":
        return parse_posted_message(m)
    # TODO: other message
    else:
        return m


def parse_posted_message(m):
    """
    From.
    {"event":"posted","data":{"channel_display_name":"","channel_name":"xxx","channel_type":"D","mentions":"[\"to56ryq76frapk54a1sx1sqppr\"]","post":"{\"id\":\"xxx\",\"create_at\":xxx,\"update_at\":xxx,\"edit_at\":0,\"delete_at\":0,\"is_pinned\":false,\"user_id\":\"xxx\",\"channel_id\":\"xxx\",\"root_id\":\"\",\"parent_id\":\"\",\"original_id\":\"\",\"message\":\"xxx\",\"type\":\"\",\"props\":{},\"hashtags\":\"\",\"pending_post_id\":\"\"}","sender_name":"bot","team_id":""},"broadcast":{"omit_users":null,"user_id":"","channel_id":"xxx","team_id":""},"seq":xxx} (string)

    To.
    { "event": "posted", "data": { "channel_display_name": "", "channel_name": "xxx", "channel_type": "D", "mentions": [ "xxx" ], "post": { "id": "xxx", "create_at": xxx, "update_at": xxx, "edit_at": 0, "delete_at": 0, "is_pinned": false, "user_id": "xxx", "channel_id": "xxx", "root_id": "", "parent_id": "", "original_id": "", "message": "xxx", "type": "", "props": {}, "hashtags": "", "pending_post_id": "" }, "sender_name": "xxx", "team_id": "" }, "broadcast": { "omit_users": "None", "user_id": "", "channel_id": "qgbiknbrj3ytpeqzxb5gjb3wzr", "team_id": "" }, "seq": xxx } (dict)
    """

    message = json.loads(m)
    if "mentions" in message['data']:
        val = message['data'].pop("mentions")
        message['data']['mentions'] = json.loads(val)
    if "post" in message['data']:
        val = message['data'].pop("post")
        message['data']['post'] = json.loads(val)
    if "broadcast" in message['data']:
        val = message['data'].pop("broadcast")
        message['data']['broadcast'] = json.loads(val)

    return message
