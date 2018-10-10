#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import os
import time
import logging
import asyncio

from mattermostdriver import Driver

from rtmbot_mattermost.utils.module_loading import import_string
from rtmbot_mattermost.utils.parse import parse_message

sys.dont_write_bytecode = True


class RtmBot(object):
    def __init__(self, config):
        '''
            Params:
                - config (dict):
                    - URL: your mattermost address
                    - PORT: your mattermost port
                    - SCHEME: protocol for access your mattermost
                        http or https
                    - USER_NAME: your mattermost user name
                    - USER_PASS: your mattermost user password
                    - BASE_PATH (optional: defaults to execution directory) RtmBot will
                        look in this directory for plugins.
                    - LOGFILE (optional: defaults to rtmbot.log) The filename for logs, will
                        be stored inside the BASE_PATH directory
                    - DEBUG (optional: defaults to False) with debug enabled, RtmBot will
                        break on errors
        '''
        # set the config object
        self.config = config

        self.url = config.get('URL', None)
        if not self.url:
            raise ValueError("Please add a URL to your config file.")
        self.token = config.get('TOKEN', None)
        if not self.token:
            raise ValueError("Please add a TOKEN to your config file.")
        self.scheme = config.get('SCHEME', None)
        if not self.scheme:
            self.scheme = "https"
        self.port = config.get('PORT', None)
        if not self.port:
            self.port = 443

        # get list of directories to search for loading plugins
        self.active_plugins = config.get('ACTIVE_PLUGINS', [])

        # set base directory for logs and plugin search
        working_directory = os.path.abspath(os.path.dirname(sys.argv[0]))

        self.directory = self.config.get('BASE_PATH', working_directory)
        if not self.directory.startswith('/'):
            path = os.path.join(os.getcwd(), self.directory)
            self.directory = os.path.abspath(path)

        self.debug = self.config.get('DEBUG', False)
        # establish logging
        log_file = config.get('LOGFILE', 'rtmbot.log')
        if self.debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        logging.basicConfig(filename=log_file,
                            level=log_level,
                            format='%(asctime)s %(message)s')
        logging.info('Initialized in: {}'.format(self.directory))

        # initialize stateful fields
        self.bot_plugins = []
        self.client = Driver({"url": self.url, "token": self.token, "scheme": self.scheme, "port": self.port})

    def _dbg(self, debug_string):
        if self.debug:
            logging.debug(debug_string)

    def connect(self):
        self.client.login()
        if 'DAEMON' in self.config:
            if self.config.get('DAEMON'):
                import daemon
                with daemon.DaemonContext():
                    self.client.init_websocket(self._start)
        self.client.init_websocket(self._start)

    def start(self):
        self.client.login()
        self.load_plugins()
        if 'DAEMON' in self.config:
            if self.config.get('DAEMON'):
                import daemon
                with daemon.DaemonContext():
                    self.client.init_websocket(self._start)
        self.client.init_websocket(self._start)

    @asyncio.coroutine
    def _start(self, m):
        message = parse_message(m)
        for plugin in self.bot_plugins:
            try:
                self._dbg("Registering jobs for {}".format(plugin.name))
                plugin.register_jobs()
            except NotImplementedError:  # this plugin doesn't register jobs
                self._dbg("No jobs registered for {}".format(plugin.name))
            except Exception as error:
                self._dbg("Error registering jobs for {} - {}".format(
                    plugin.name, error)
                )
        self.input(message)
        self.crons()
        self.output()
        time.sleep(1)

    def input(self, data):
        if "event" in data and isinstance(data, dict):
            function_name = "process_" + data['event']
            self._dbg("got {}".format(function_name))
            for plugin in self.bot_plugins:
                plugin.do(function_name, data)

    def output(self):
        for plugin in self.bot_plugins:
            limiter = False
            for output in plugin.do_output():
                channel = output[0]
                message = output[1]
                if channel is not None and message is not None:
                    if limiter:
                        time.sleep(.1)
                        limiter = False
                    # channel.send_message(message)
                    plugin.client.api['posts'].create_post(options={
                        'channel_id': channel,
                        'message': message})
                    limiter = True

    def crons(self):
        for plugin in self.bot_plugins:
            plugin.do_jobs()

    def load_plugins(self):
        ''' Given a set of plugin_path strings (directory names on the python path),
        load any classes with Plugin in the name from any files within those dirs.
        '''
        self._dbg("Loading plugins")
        if not self.active_plugins:
            self._dbg("No plugins specified in conf file")
            return  # nothing to load

        for plugin_path in self.active_plugins:
            self._dbg("Importing {}".format(plugin_path))

            if self.debug is True:
                # this makes the plugin fail with stack trace in debug mode
                cls = import_string(plugin_path)
            else:
                # otherwise we log the exception and carry on
                try:
                    cls = import_string(plugin_path)
                except ImportError as error:
                    logging.exception("Problem importing {} - {}".format(
                        plugin_path, error)
                    )

            plugin_config = self.config.get(cls.__name__, {})
            plugin = cls(client=self.client, plugin_config=plugin_config)  # instatiate!
            self.bot_plugins.append(plugin)
            self._dbg("Plugin registered: {}".format(plugin))


class Plugin(object):

    def __init__(self, name=None, client=None, plugin_config=None):
        '''
        A plugin in initialized with:
            - name (str)
            - client - a connected instance of MattermostDriver - can be used to make API
                calls within the plugins
            - plugin config (dict) - (from the yaml config)
                Values in config:
                - DEBUG (bool) - this will be overridden if debug is set in config for this plugin
        '''
        if name is None:
            self.name = type(self).__name__
        else:
            self.name = name
        if plugin_config is None:
            self.plugin_config = {}
        else:
            self.plugin_config = plugin_config
        self.client = client
        self.jobs = []
        self.debug = self.plugin_config.get('DEBUG', False)
        self.outputs = []

    def register_jobs(self):
        ''' Please override this job with a method that instantiates any jobs
        you'd like to run from this plugin and attaches them to self.jobs. See
        the example plugins for examples.
        '''
        raise NotImplementedError

    def do(self, function_name, data):
        try:
            func = getattr(self, function_name)
        except AttributeError:
            pass
        else:
            if self.debug is True:
                # this makes the plugin fail with stack trace in debug mode
                func(data)
            else:
                # otherwise we log the exception and carry on
                try:
                    func(data)
                except Exception:
                    logging.exception("Problem in Plugin Class: {}: {} \n{}".format(
                        self.name, function_name, data)
                    )

        if hasattr(self, 'catch_all'):
            if self.debug is True:
                # this makes the plugin fail with stack trace in debug mode
                self.catch_all(data)
            else:
                try:
                    self.catch_all(data)
                except Exception:
                    logging.exception("Problem in catch all: {}: {} {}".format(
                        self.name, self.module, data)
                    )

    def do_jobs(self):
        job_output = []
        for job in self.jobs:
            if job.check():
                # interval is up, so run the job

                if self.debug is True:
                    # this makes the plugin fail with stack trace in debug mode
                    job_output = job.run(self.client)
                else:
                    # otherwise we log the exception and carry on
                    try:
                        job_output = job.run(self.client)
                    except Exception:
                        logging.exception("Problem in job run: {}".format(
                            job.__class__)
                        )

                # job attempted execution so reset the timer and log output
                job.lastrun = time.time()
                if job_output:
                    for out in job_output:
                        self.outputs.append(out)

    def do_output(self):
        output = []
        while True:
            if len(self.outputs) > 0:
                logging.info("output from {}".format(self.name))
                output.append(self.outputs.pop(0))
            else:
                break
        return output


class Job(object):
    '''
        Jobs can be used to trigger periodic method calls. Jobs must be
        registered with a Plugin to be called. See the register_jobs method
        and documentation for how to make this work.

        :Args:
            interval (int): The interval in seconds at which this Job's run
                method should be called
    '''

    def __init__(self, interval):
        self.interval = interval
        self.lastrun = 0

    def __str__(self):
        return "{} {} {}".format(self.__class__, self.interval, self.lastrun)

    def __repr__(self):
        return self.__str__()

    def check(self):
        ''' Returns True if `interval` seconds have passed since it last ran '''
        if self.lastrun + self.interval < time.time():
            return True
        else:
            return False

    def run(self, client):
        ''' This method is called from the plugin and is where the logic for
        your Job starts and finished. It is called every `interval` seconds
        from Job.check()

        :Args:
            client (Driver): An instance of the MattermostDriver API connector
                this can be used to make calls directly to the Mattermost Web API if
                necessary.


        This method should return an array of outputs in the form of::

            [[Channel Identifier, Output String]]
            or
            [['C12345678', 'Here's my output for this channel'], ['C87654321', 'Different output']
        '''
        raise NotImplementedError


class UnknownChannel(Exception):
    pass
