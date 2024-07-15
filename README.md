<div align="center">
  <img src="https://github.com/Burhanverse/assets/blob/main/1_20240704_134259_0000.png" width="360" height="360">
</div>
<h1 align="center">Pixeldrain Bot</h1>
This project is designed to facilitate easy media uploads from Telegram to PixelDrain, providing a seamless integration for file sharing.

---

## Bot Commands:
- `/start` This is generic like any other bot.
- `/auth` Used to authorise a user and can be used in private mode only. [Owner CMD]
- `/unauth` Used to revoke authorisation. [Owner CMD]
- `/auths` Used to get the the authorised user list. [Owner CMD]
- `/pdup` Used to upload files from a group chat by replying the file with it. [Available for authorised users only]

---

## TO-Dos:
 * [x] Introduce MongoDB for managing auth_users.
 * [x] User Authorization Support.
 * [x] Support Pixeldrain API.
 * [x] Support multiple files upload in one go.
 * [x] No cooldown timer.
 * [x] Add support for group chats.
 * [ ] Add support for links mirror.

---

## Requirements & Variables:

- `API_HASH` Your API Hash from [Telegram](https://my.telegram.org)
- `API_ID` Your API ID from [Telegram](https://my.telegram.org)
- `BOT_TOKEN` Your bot token from @BotFather
- `MONGODB_URI` Your [MongoDB](https://telegra.ph/How-To-get-Mongodb-URI-04-06) URI 
- `OWNER_ID` Telegram user ID of the Owner
- `PIXELDRAIN_API_KEY` Your [Pixeldrain](https://pixeldrain.com) API KEY 

##### Note: Make the required changes in `.env` file.

---

## Deployment:

- Clone the Repository:
```sh
git clone https://github.com/Burhanverse/Pixeldrain-Bot.git
cd Pixeldrain-Bot
```
- Setup Virtual Environment:
```sh
python -m venv venv
. ./venv/bin/activate
```
- Install Dependencies:
```sh
pip install -r requirements.txt
```
- Run the Bot:
```sh
# <Setup the .env Variables appropriately first>
python bot.py
```

---

## Credits:

- [Pixeldrain API](https://pixeldrain.com/api)
- [Pyrogram](https://pyrogram.org)
- [MongoDB](https://mongodb.com)

---
