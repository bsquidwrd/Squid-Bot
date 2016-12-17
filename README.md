## Squid Bot [![Build Status](https://travis-ci.org/bsquidwrd/Squid-Bot.svg?branch=master)](https://travis-ci.org/bsquidwrd/Squid-Bot) [![Documentation Status](https://readthedocs.org/projects/squid-bot/badge/?version=latest)](http://squid-bot.readthedocs.io/en/latest/?badge=latest) [![Coverage Status](https://coveralls.io/repos/github/bsquidwrd/Squid-Bot/badge.svg?branch=master)](https://coveralls.io/github/bsquidwrd/Squid-Bot?branch=master)
A bot of many talents

## Running
_NOTE: If you want to run this yourself, make sure the bot is a "Bot User"_

I'd prefer if only my instance was running so the bot and users don't get confused. You should only need one main configuration file while the rest will be created automatically. In the `web` directory, rename [environment_example.py](web/environment_example.py) to `environment.py`

[Click here to have the bot added to your server](https://discordapp.com/oauth2/authorize?client_id=225463490813493248&scope=bot&permissions=268692480)

#### Environmental Variables
- `SQUID_BOT_DEBUG_MODE:` Should the bot be in Debug mode
- `SQUID_BOT_CLIENT_ID:` The Client ID assigned by Discord
- `SQUID_BOT_TOKEN:` The token used by Discord to sign in with your bot
- `SQUID_BOT_OWNER_ID:` The Discord ID for the owner of the bot
- `SQUID_BOT_EMAIL_PASSWORD:` SMTP Email user password
- `DJANGO_SETTINGS_MODULE:` The module that has django settings
- `SQUID_BOT_DJANGO_SECRET:` Unique 'token' for django
- `SQUID_BOT_DATABASE_ENGINE:` Which django database engine to use
- `SQUID_BOT_DATABASE_NAME:` Name of the database django will use
- `SQUID_BOT_DATABASE_HOST:` The host django will use for the database
- `SQUID_BOT_DATABASE_PORT:` The port for accessing the database
- `SQUID_BOT_DATABASE_USERNAME:` The username for the django database
- `SQUID_BOT_DATABASE_PASSWORD:` The password for the django database


## Requirements
- Python 3.5+
- Async version of discord.py

## Thanks
- [Rapptz](https://github.com/Rapptz) and his amazing work on [Discord.py](https://github.com/Rapptz/discord.py) combined with the code I used as a template [RoboDanny](https://github.com/Rapptz/RoboDanny)
