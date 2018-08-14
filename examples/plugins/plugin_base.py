import os
import json

from rtmbot_mattermost.core import Plugin


class PluginBase(Plugin):
    def __init__(self, subcommands, *args, **kwargs):
        super(PluginBase, self).__init__(*args, **kwargs)
        self.subcommands = subcommands
        self.bot_id = self.client.api['users'].get_user(user_id='me')['id']
        self.bot_name = self.client.api['users'].get_user(user_id='me')['username']

    def process_posted(self, json_data):

        def match(data):
            if not str(self.bot_id) in data['mentions']:
                return False

            post = data['post']
            message = post['message'].strip().split()
            if len(message) < 2:
                return False

            if message[1] not in self.subcommands:
                return False

            return True

        if 'mentions' in json_data['data'] and 'post' in json_data['data'] and match(json_data['data']):
            self.process_filtered_massage(json_data)
            return

    def process_filtered_massage(self, data):
        raise NotImplementedError()
