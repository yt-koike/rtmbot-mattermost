#!/usr/bin/env python
from argparse import ArgumentParser
from websockets.exceptions import ConnectionClosed
from json.decoder import JSONDecodeError
from logging import getLogger
import sys
import os
import yaml

from rtmbot_mattermost import RtmBot

logger = getLogger(__name__)
sys.path.append(os.getcwd())


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args()


def main(args=None):
    # load args with config path if not specified
    if not args:
        args = parse_args()

    config = yaml.load(open(args.config or 'rtmbot.conf', 'r'))
    bot = RtmBot(config)

    try:
        bot.start()
    except (ConnectionClosed, JSONDecodeError):
        while True:
            try:
                bot.connect()
            except (ConnectionClosed, JSONDecodeError):
                continue
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                import traceback
                logger.error(traceback.format_exc())
                sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
