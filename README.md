# Pixeldrain Bot
A telegram media to pixeldrain upload bot

---

## Deploy:

```sh
git clone https://github.com/Burhanverse/Pixeldrain-Bot.git
cd Pixeldrain-Bot
python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
# <Create Variables appropriately>
python bot.py
```

---

## Features:
 * [x] Introduce MongoDB for managing auth_users.
 * [x] User Authorization Support.
 * [x] Support Pixeldrain API.
 * [x] Support multiple files upload in one go.
 * [x] No cooldown timer.

## Requirements & Variables:

- `API_HASH` Your API Hash from [Telegram](https://my.telegram.org)
- `API_ID` Your API ID from [Telegram](https://my.telegram.org)
- `BOT_TOKEN` Your bot token from @BotFather
- `MONGODB_URI` Your [MongoDB](https://telegra.ph/How-To-get-Mongodb-URI-04-06) URI 
- `OWNER_ID` Telegram user ID of the Owner
- `PIXELDRAIN_API_KEY` Your [Pixeldrain](https://pixeldrain.com) API KEY 

##### Note: Make the required changes in `.env` file.

---

## Credits:

- [Pixeldrain API](https://pixeldrain.com/api)
- [Pyrogram](https://pyrogram.org)
- [Contributors](https://github.com/Burhanverse/Pixeldrain-Bot/graphs/contributors)

---
