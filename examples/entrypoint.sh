#!/usr/bin/env sh

cat << _EOF_ > rtmbot.conf
DEBUG: ${DEBUG-True}
URL: "$URL"
TOKEN: "$TOKEN"
SCHEME: "${SCHEME-https}"
PORT: ${PORT-443}
ACTIVE_PLUGINS:
    - plugins.HelpDisplay
_EOF_

rtmbot-mattermost
