import os
import dotenv
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

dotenv.load_dotenv()

# Bot configuration
Bot = Client(
    "Pixeldrain-Bot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"]
)

PIXELDRAIN_API_KEY = os.environ["PIXELDRAIN_API_KEY"]

START_TEXT = """Hello {},
Ready to share some media? Send a file to get a Pixeldrain stream link, or drop a Pixeldrain media ID or link to get the scoop on your file!"""

UNAUTH_TEXT = """Sorry, you are not authorized to use this bot. Please contact the bot owner by clicking the button below for access."""

BUTTON = InlineKeyboardButton(text="Feedback", url="https://telegram.me/aqxza")

# MongoDB configuration
MONGODB_URI = os.environ["MONGODB_URI"]
client = MongoClient(MONGODB_URI)
db = client['pixeldrain_bot']
authorized_users_col = db['authorized_users']

# Function to check if the user is authorized
def is_authorized(user_id):
    return authorized_users_col.find_one({"user_id": user_id}) is not None

# Filter to check if the user is authorized
def authorized_user_filter(_, __, message):
    return is_authorized(message.from_user.id)

# Handler for /start command
@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, message):
    if authorized_user_filter(None, None, message):
        await message.reply_text(
            text=START_TEXT.format(message.from_user.mention),
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON]])
        )
    else:
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON]])
        )

# Handler for /auth_user command (only for the bot owner)
@Bot.on_message(filters.private & filters.command("auth_user"))
async def auth_user(bot, message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        try:
            user_id = int(message.command[1])
            if not is_authorized(user_id):
                authorized_users_col.insert_one({"user_id": user_id})
                await message.reply_text(f"User {user_id} has been authorized.")
            else:
                await message.reply_text(f"User {user_id} is already authorized.")
        except (IndexError, ValueError):
            await message.reply_text("Usage: /auth_user <user_id>")
    else:
        await message.reply_text("You are not authorized to use this command.")

# Handler for /ls_auth command (only for the bot owner)
@Bot.on_message(filters.private & filters.command("ls_auth"))
async def ls_auth(bot, message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        authorized_users = authorized_users_col.find()
        text = "**Authorized Users:**\n"
        for user in authorized_users:
            user_id = user["user_id"]
            text += f"[{user_id}](tg://user?id={user_id})\n"
        await message.reply_text(text, disable_web_page_preview=True)
    else:
        await message.reply_text("You are not authorized to use this command.")

# Handler for /unauth_user command (only for the bot owner)
@Bot.on_message(filters.private & filters.command("unauth_user"))
async def unauth_user(bot, message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        try:
            user_id = int(message.command[1])
            result = authorized_users_col.delete_one({"user_id": user_id})
            if result.deleted_count:
                await message.reply_text(f"User {user_id} has been unauthorized.")
            else:
                await message.reply_text(f"User {user_id} is not found.")
        except (IndexError, ValueError):
            await message.reply_text("Usage: /unauth_user <user_id>")
    else:
        await message.reply_text("You are not authorized to use this command.")

def get_id(text):
    if text.startswith("http"):
        if text.endswith("/"):
            id = text.split("/")[-2]
        else:
            id = text.split("/")[-1]
    elif "/" not in text:
        id = text
    else:
        return None
    return id

def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"

def format_date(date_str):
    date, time = date_str.split("T")
    time = time.split(".")[0]  # remove milliseconds and 'Z'
    return f"{date} {time}"

async def send_data(id, message):
    # pixeldrain data
    try:
        response = requests.get(f"https://pixeldrain.com/api/file/{id}/info")
        data = response.json() if response.status_code == 200 else None
    except Exception as e:
        data = None
        print(f"Error: {e}")

    if data:
        text = (
            f"**File Name:** `{data['name']}`\n"
            f"**Download Page:** [Click Here](https://pixeldrain.com/u/{id})\n"
            f"**Direct Link:** [Click Here](https://pixeldrain.com/api/file/{id})\n"
            f"**Upload Date:** `{format_date(data['date_upload'])}`\n"
            f"**Last View Date:** `{format_date(data['date_last_view'])}`\n"
            f"**File Size:** `{format_size(data['size'])}`\n"
            f"**Total Views:** `{data['views']}`\n"
            f"**Bandwidth Used:** `{format_size(data['bandwidth_used'])}`\n"
            f"**File Type:** `{data['mime_type']}`"
        )
    else:
        text = "Failed to retrieve file information."

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Open Link",
                    url=f"https://pixeldrain.com/u/{id}"
                ),
                InlineKeyboardButton(
                    text="Share Link",
                    url=f"https://telegram.me/share/url?url=https://pixeldrain.com/u/{id}"
                )
            ],
            [BUTTON]
        ]
    )

    await message.edit_text(
        text=text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

# Handler for authorized users to get pixeldrain info
@Bot.on_message(filters.private & filters.text & filters.create(authorized_user_filter))
async def info(bot, update):
    try:
        id = get_id(update.text)
        if id is None:
            return
    except:
        return

    message = await update.reply_text(
        text="`Processing...`",
        quote=True,
        disable_web_page_preview=True
    )
    await send_data(id, message)

# Handler for authorized users to upload media
@Bot.on_message(filters.private & filters.media & filters.create(authorized_user_filter))
async def media_filter(bot, update):

    logs = []
    message = await update.reply_text(
        text="`Processing...`",
        quote=True,
        disable_web_page_preview=True
    )

    try:
        # download
        try:
            await message.edit_text(
                text="`Downloading...`",
                disable_web_page_preview=True
            )
        except:
            pass
        media = await update.download()
        logs.append("Downloaded Successfully")

        # rename file to include user ID
        user_id = update.from_user.id
        dir_name, file_name = os.path.split(media)
        file_base, file_extension = os.path.splitext(file_name)
        renamed_file = os.path.join(dir_name, f"{user_id}_{file_base}{file_extension}")
        os.rename(media, renamed_file)
        logs.append("Renamed file successfully")

        # upload
        try:
            await message.edit_text(
                text="`Downloaded Successfully, Now Uploading...`",
                disable_web_page_preview=True
            )
        except:
            pass

        try:
            with open(renamed_file, 'rb') as file:
                response = requests.post(
                    "https://pixeldrain.com/api/file",
                    files={'file': file},
                    auth=('', PIXELDRAIN_API_KEY)
                )
            logs.append("Uploaded Successfully")
            os.remove(renamed_file)
            logs.append("Removed media")

            response_data = response.json()
            if response.status_code == 201:
                await message.edit_text(
                    text="`Uploaded Successfully!`",
                    disable_web_page_preview=True
                )
                await send_data(response_data["id"], message)
            else:
                logs.append("Success is False")
                await message.edit_text(
                    text=f"**Error {response_data['value']}:-** `{response_data['message']}`",
                    disable_web_page_preview=True
                )

        except Exception as error:
            logs.append("Not Uploading")
            await message.edit_text(
                text=f"Error :- `{error}`" + "\n\n" + '\n'.join(logs),
                disable_web_page_preview=True
            )
            return

    except Exception as error:
        await message.edit_text(
            text=f"Error :- `{error}`" + "\n\n" + '\n'.join(logs),
            disable_web_page_preview=True
        )

# Handler for unauthorized users attempting to use the bot
@Bot.on_message(filters.private & ~filters.command("start"))
async def unauthorized_user_handler(bot, message):
    if not authorized_user_filter(None, None, message):
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON]])
        )

Bot.run()
