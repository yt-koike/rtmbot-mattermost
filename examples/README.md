# About

* React only `help` command

```
user 0:00 AM
> @bot help
bot 0:00 AM
> Help Message.
```

# execute to Docker

Set environment vars.

```
export URL=$mattermost_server_address
export SCHEME=$http_or_https
export PORT=$number
export TOKEN=$mattermost_user_accsess_token
```

Build image.

```
docker build . -t sample-bot
```

Run.

```
docker run -itd -e URL=$URL -e SCHEME=$SCHEME -e PORT=$PORT -e TOKEN=$TOKEN --name sample-bot sample-bot
```

