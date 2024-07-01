import os
import dotenv
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

dotenv.load_dotenv()

Bot = Client(
    "Pixeldrain-Bot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"]
)

# Get authorized user IDs from .env
authorized_users = list(map(int, os.getenv('AUTHORIZED_USERS').split(',')))

PIXELDRAIN_API_KEY = os.environ["PIXELDRAIN_API_KEY"]

START_TEXT = """Hello {},
Please send a media for pixeldrain.com stream link. \
You can also send pixeldrain media ID or link to get more info."""

UNAUTH_TEXT = """Sorry, you are not authorized to use this bot. \
Please contact the bot owner by clicking the button below for access."""

BUTTON = InlineKeyboardButton(text="Feedback", url="https://telegram.me/aqxza")

# Filter to check if the user is authorized
def authorized_user_filter(_, __, message):
    return message.from_user.id in authorized_users

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

async def send_data(id, message):
    # pixeldrain data
    try:
        response = requests.get(f"https://pixeldrain.com/api/file/{id}/info")
        data = response.json() if response.status_code == 200 else None
    except Exception as e:
        data = None
        print(f"Error: {e}")

    text = ""
    if data:
        text += f"**File Name:** `{data['name']}`" + "\n"
    text += f"**Download Page:** `https://pixeldrain.com/u/{id}`" + "\n"
    text += f"**Direct Download Link:** `https://pixeldrain.com/api/file/{id}`" + "\n"
    if data:
        text += f"**Upload Date:** `{data['date_upload']}`" + "\n"
        text += f"**Last View Date:** `{data['date_last_view']}`" + "\n"
        text += f"**Size:** `{data['size']}`" + "\n"
        text += f"**Total Views:** `{data['views']}`" + "\n"
        text += f"**Bandwidth Used:** `{data['bandwidth_used']}`" + "\n"
        text += f"**Mime Type:** `{data['mime_type']}`"
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
        logs.append("Download Successfully")

        # upload
        try:
            await message.edit_text(
                text="`Download Successfully, Now Uploading...`",
                disable_web_page_preview=True
            )
        except:
            pass

        try:
            with open(media, 'rb') as file:
                response = requests.post(
                    "https://pixeldrain.com/api/file",
                    files={'file': file},
                    auth=('', PIXELDRAIN_API_KEY)
                )
            logs.append("Upload Successfully")
            os.remove(media)
            logs.append("Remove media")

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
