from plugins.plugin_base import PluginBase
import json

HELP_MESSAGE = '''
> Help Message.
'''


def output_help(bot_name):
    return HELP_MESSAGE.format(bot_name)


class HelpDisplay(PluginBase):
    def __init__(self, *args, **kwargs):
        subcommands = set(['help'])
        super(HelpDisplay, self).__init__(subcommands, *args, **kwargs)

    def process_filtered_massage(self, json_data):
        channel = json_data['data']['post']['channel_id']
        self.outputs.append([channel, output_help(self.bot_name)])

