# vladbot
this is the repository for the vladbot used in the [vladbot discord server.](https://discord.gg/wMBSMzT5pm)

## development/hosting
#### prerequisites
1. python 3.12 or later. (https://www.python.org/downloads/) (it is hosted with python 3.12.3)
2. if you want to contribute, you'll need git. (https://git-scm.com/downloads)
3. ffmpeg (https://www.ffmpeg.org/download.html)
4. postgresql (https://www.postgresql.org/download/)

#### 1. copy `.env.example` to `.env`

#### 2. edit `config.yml`
the config file is used to store required values and ids for certain features of the bot. just read it, adjust and fill. i made it readable!!!

#### 3. get your discord bot token
you can follow the first step only of [these instructions](https://discord.com/developers/docs/quick-start/getting-started) to create your bot and get it's token. when creating the bot, give it all intents, and when adding it to your server it's easiest to give it administrator perms, unless you know exactly what it needs.

once you have your discord bot token, put it inside the double quotes for TOKEN in your .env file

#### 4. set database up
just download postgresql gang :v:
also put the database url in .env in 'postgresql://user:password@localhost:5432/database' form

#### 5. get your bot admin role id
in your server, you'll need to get the id of the role for bot admin. once you have it, put it in the .env file as `AIRole`

#### 6. install dependencies
these next few parts will all be done in your terminal. make sure you're in the folder with the bot's code in it for them.

to create the virtual environment, run `python -m venv ./venv`.
this will create a new folder, `venv`, that contains your virtual environment.

next, you need to activate the virtual environment. You'll need to do this every time you enter the shell to start the bot, so it always uses the right dependencies.
to do this, run `./venv/Scripts/activate`. Once it finishes, you should see your prompt change to include `(venv)` at the start of it.

run `pip install -r requirements.txt`

to start the bot, run `python main.py`

## credits

many thanks to txshiro, the original developer of this version of squidbot vladbot was forked from.
many thanks to omegametor, the author of the original squidbot readme.md
not so many thanks to vlad15032009, the person who gave the name to vladbot.
