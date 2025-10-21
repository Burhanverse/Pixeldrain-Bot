import os
import sys
import aiohttp
import asyncio
import base64
import json
from typing import Optional, Tuple, List, Dict, Any, Union

import dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, User
from pymongo import MongoClient

# Load environment variables
dotenv.load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = [
    "BOT_TOKEN",
    "API_ID",
    "API_HASH",
    "PIXELDRAIN_API_KEY",
    "MONGODB_URI",
    "OWNER_ID",
]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Initialize Bot
try:
    Bot = Client(
        "Pixeldrain-Bot",
        bot_token=os.environ["BOT_TOKEN"],
        api_id=int(os.environ["API_ID"]),
        api_hash=os.environ["API_HASH"],
    )
except Exception as e:
    print(f"Error initializing bot: {e}")
    sys.exit(1)

PIXELDRAIN_API_KEY: str = os.environ["PIXELDRAIN_API_KEY"]
OWNER_ID: int = int(os.environ["OWNER_ID"])

# Constants
START_TEXT = """Hello {},
Ready to share some media? Send a file to get a Pixeldrain stream link, or drop a Pixeldrain media ID or link to get the scoop on your file!"""

UNAUTH_TEXT = """Sorry, you are not authorized to use this bot. Please contact the bot owner for access."""

BUTTON1 = InlineKeyboardButton(text="𝘗𝘳𝘫𝘬𝘵:𝘚𝘪𝘥.", url="https://burhanverse.t.me")
BUTTON2 = InlineKeyboardButton(text="Contact Owner", url="https://aqxzaxbot.t.me")

# MongoDB setup
try:
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    client = MongoClient(MONGODB_URI)
    db = client["pixeldrain_bot"]
    authorized_users_col = db["authorized_users"]
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)


# ==================== Authorization Functions ====================


def is_authorized(user_id: int) -> bool:
    """Check if a user is authorized to use the bot."""
    try:
        return authorized_users_col.find_one({"user_id": user_id}) is not None
    except Exception as e:
        print(f"Error checking authorization for user {user_id}: {e}")
        return False


def authorized_user_filter(_, __, message: Message) -> bool:
    """Filter to check if the user is authorized."""
    if not message.from_user:
        return False
    return is_authorized(message.from_user.id)


def update_user_info(user_id: int, username: str) -> None:
    """Update user information in the database."""
    try:
        authorized_users_col.update_one(
            {"user_id": user_id}, {"$set": {"username": username}}, upsert=True
        )
    except Exception as e:
        print(f"Error updating user info for {user_id}: {e}")


def get_user_from_result(user_result: Union[User, List[User]]) -> Optional[User]:
    """Helper function to extract User from get_users result."""
    if isinstance(user_result, list):
        return user_result[0] if user_result else None
    return user_result


async def update_username(bot: Client, user_id: int) -> None:
    """Update username field in the database."""
    try:
        user_result = await bot.get_users(user_id)
        user_info = get_user_from_result(user_result)
        if not user_info:
            return
        username = user_info.username if user_info.username else "No username"
        update_user_info(user_id, username)
    except Exception as e:
        print(f"Error updating username for user {user_id}: {e}")


# ==================== Command Handlers ====================


@Bot.on_message(filters.private & filters.command("start"))
async def start(bot: Client, message: Message) -> None:
    """Handler for /start command."""
    if not message.from_user:
        return

    if authorized_user_filter(None, None, message):
        await message.reply_text(
            text=START_TEXT.format(message.from_user.mention),
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON1, BUTTON2]]),
        )
    else:
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON1, BUTTON2]]),
        )


@Bot.on_message(filters.command("auth"))
async def auth(bot: Client, message: Message) -> None:
    """Handler for /auth command (only for the bot owner)."""
    if not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply_text("You are not authorized to use this command.")
        return

    try:
        user: Optional[User] = None

        if message.reply_to_message and message.reply_to_message.from_user:
            user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user_id_input = int(message.command[1])
            user_result = await bot.get_users(user_id_input)
            user = get_user_from_result(user_result)
            if not user:
                await message.reply_text("User not found.")
                return
        else:
            await message.reply_text(
                "Usage: /auth <user_id> or reply to a user's message with /auth"
            )
            return

        user_id = user.id
        username = user.username if user.username else "No username"

        if not is_authorized(user_id):
            authorized_users_col.insert_one({"user_id": user_id, "username": username})
            await message.reply_text(
                f"User {user_id} (@{username}) has been authorized."
            )
        else:
            await update_username(bot, user_id)
            await message.reply_text(
                f"User {user_id} (@{username}) is already authorized."
            )
    except (IndexError, ValueError) as e:
        await message.reply_text(f"Invalid user ID. Error: {str(e)}")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")


@Bot.on_message(filters.command("auths"))
async def auths(bot: Client, message: Message) -> None:
    """Handler for /auths command (only for the bot owner)."""
    if not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply_text("You are not authorized to use this command.")
        return

    try:
        authorized_users = authorized_users_col.find()
        text = "**Authorized Users:**\n"

        for user in authorized_users:
            user_id = user.get("user_id")
            username = user.get("username", "No username")

            if not user_id:
                continue

            if username == "No username":
                await update_username(bot, user_id)
                try:
                    user_result = await bot.get_users(user_id)
                    user_info = get_user_from_result(user_result)
                    if user_info:
                        username = (
                            user_info.username if user_info.username else "No username"
                        )
                    else:
                        username = "No username"
                except Exception:
                    username = "No username"

            text += f"[{user_id}](tg://user?id={user_id}) (@{username})\n"

        await message.reply_text(text, disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text(f"Error retrieving authorized users: {str(e)}")


@Bot.on_message(filters.command("unauth"))
async def unauth(bot: Client, message: Message) -> None:
    """Handler for /unauth command (only for the bot owner)."""
    if not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id: Optional[int] = None

        if message.reply_to_message and message.reply_to_message.from_user:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            user_id = int(message.command[1])
        else:
            await message.reply_text(
                "Usage: /unauth <user_id> or reply to a user's message with /unauth"
            )
            return

        user_result = await bot.get_users(user_id)
        user_info = get_user_from_result(user_result)
        username = (
            user_info.username if user_info and user_info.username else "No username"
        )

        result = authorized_users_col.delete_one({"user_id": user_id})
        if result.deleted_count:
            await message.reply_text(
                f"User {user_id} (@{username}) has been unauthorized."
            )
        else:
            await message.reply_text(f"User {user_id} is not found.")
    except (IndexError, ValueError) as e:
        await message.reply_text(f"Invalid user ID. Error: {str(e)}")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")


# ==================== Utility Functions ====================


def get_id(text: str) -> Optional[str]:
    """Extract Pixeldrain ID from text/URL."""
    if not text:
        return None

    try:
        if text.startswith("http"):
            if text.endswith("/"):
                file_id = text.split("/")[-2]
            else:
                file_id = text.split("/")[-1]
        elif "/" not in text:
            file_id = text
        else:
            return None
        return file_id
    except Exception as e:
        print(f"Error extracting ID from text: {e}")
        return None


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    try:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    except Exception:
        return f"{size} B"


def format_date(date_str: str) -> str:
    """Format date string to readable format."""
    try:
        date, time = date_str.split("T")
        time = time.split(".")[0]
        return f"{date} {time}"
    except Exception:
        return date_str


async def send_data(file_id: str, message: Message) -> None:
    """Fetch and send Pixeldrain file information."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://pixeldrain.com/api/file/{file_id}/info"
            ) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        text_response = await response.text()
                        try:
                            data = json.loads(text_response)
                        except Exception:
                            data = None
                else:
                    data = None
    except Exception as e:
        print(f"Error fetching file info: {e}")
        data = None

    if data and isinstance(data, dict):
        try:
            text = (
                f"**File Name:** `{data.get('name', 'Unknown')}`\n"
                f"**Upload Date:** `{format_date(data.get('date_upload', 'Unknown'))}`\n"
                f"**File Size:** `{format_size(data.get('size', 0))}`\n"
                f"**File Type:** `{data.get('mime_type', 'Unknown')}`\n\n"
                f"\u00a9 [𝘗𝘳𝘫𝘬𝘵:𝘚𝘪𝘥.](https://burhanverse.t.me)"
            )
        except Exception as e:
            print(f"Error formatting data: {e}")
            text = "Failed to format file information."
    else:
        text = "Failed to retrieve file information."

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Open Link", url=f"https://pixeldrain.com/u/{file_id}"
                ),
                InlineKeyboardButton(
                    text="Direct Link", url=f"https://pixeldrain.com/api/file/{file_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Share Link",
                    url=f"https://telegram.me/share/url?url=https://pixeldrain.com/u/{file_id}",
                )
            ],
            [BUTTON2],
        ]
    )

    try:
        await message.edit_text(
            text=text, reply_markup=reply_markup, disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error editing message: {e}")


# ==================== Info Handler ====================


@Bot.on_message(filters.private & filters.text & filters.create(authorized_user_filter))
async def info(bot: Client, update: Message) -> None:
    """Handler for authorized users to get Pixeldrain info."""
    if not update.text:
        return

    try:
        file_id = get_id(update.text)
        if file_id is None:
            return
    except Exception:
        return

    try:
        message = await update.reply_text(
            text="`Processing...`", quote=True, disable_web_page_preview=True
        )
        await send_data(file_id, message)
    except Exception as e:
        print(f"Error in info handler: {e}")


# ==================== Media Upload Handlers ====================


@Bot.on_message(
    filters.private & filters.media & filters.create(authorized_user_filter)
)
async def media_filter(bot: Client, update: Message) -> None:
    """Handler for authorized users to upload media in private chats."""
    await handle_media(bot, update)


async def handle_media(bot: Client, update: Message) -> None:
    """Handle media upload to Pixeldrain."""
    logs: List[str] = []

    try:
        message = await update.reply_text(
            text="`Processing...`", quote=True, disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error sending processing message: {e}")
        return

    try:
        # Update status
        try:
            await message.edit_text(
                text="`Downloading...`", disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Error updating message: {e}")

        # Download the media
        media_path: Optional[str] = None
        try:
            media_path = await update.download()
        except Exception as e:
            await message.edit_text(
                text=f"Error downloading media: `{str(e)}`",
                disable_web_page_preview=True,
            )
            return

        # Check if download was successful - THIS WAS THE MAIN BUG
        if not media_path:
            await message.edit_text(
                text="Error: Failed to download media. The file path is None or empty.",
                disable_web_page_preview=True,
            )
            return

        if not os.path.exists(media_path):
            await message.edit_text(
                text=f"Error: Downloaded file not found at path: `{media_path}`",
                disable_web_page_preview=True,
            )
            return

        logs.append("Downloaded Successfully")

        # Get user ID for file naming
        user_id: str = "unknown"
        if update.from_user:
            user_id = str(update.from_user.id)

        # Rename file to include user ID
        try:
            dir_name, file_name = os.path.split(media_path)
            file_base, file_extension = os.path.splitext(file_name)
            renamed_file = os.path.join(
                dir_name, f"{file_base}_{user_id}{file_extension}"
            )
            os.rename(media_path, renamed_file)
            logs.append("Renamed file successfully")
        except Exception as e:
            print(f"Error renaming file: {e}")
            renamed_file = media_path  # Use original path if rename fails
            logs.append(f"Rename failed, using original path: {str(e)}")

        # Get file size
        try:
            file_size = os.path.getsize(renamed_file)
            logs.append(f"File size: {format_size(file_size)}")
        except Exception as e:
            print(f"Error getting file size: {e}")
            file_size = 0
            logs.append(f"Could not determine file size: {str(e)}")

        # Update status with file size
        try:
            await message.edit_text(
                text=f"`Downloaded Successfully ({format_size(file_size)}), Now Uploading...`",
                disable_web_page_preview=True,
            )
        except Exception as e:
            print(f"Error updating message: {e}")

        # Queue the upload to run in background
        try:
            asyncio.create_task(
                background_upload(renamed_file, PIXELDRAIN_API_KEY, message, logs)
            )
            await message.edit_text(
                text="`Upload queued — processing in background. You'll get a link when it's ready.`",
                disable_web_page_preview=True,
            )
        except Exception as err:
            await message.edit_text(
                text=f"Failed to queue upload: `{err}`\n\n" + "\n".join(logs),
                disable_web_page_preview=True,
            )

    except Exception as error:
        try:
            error_msg = f"Error: `{str(error)}`\n\n" + "\n".join(logs)
            await message.edit_text(text=error_msg, disable_web_page_preview=True)
        except Exception as e:
            print(f"Error sending error message: {e}")


async def upload_file_stream(
    file_path: str, pixeldrain_api_key: str, message: Optional[Message] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Upload a file to Pixeldrain using streaming to support large files.

    Args:
        file_path: Path to the file to upload
        pixeldrain_api_key: API key for authentication
        message: Optional Telegram message object for progress updates

    Returns:
        Tuple of (response_data, logs)
    """
    logs: List[str] = []

    try:
        # Validate file exists
        if not os.path.exists(file_path):
            logs.append(f"File not found: {file_path}")
            return {"error": "File not found"}, logs

        file_size = os.path.getsize(file_path)
        logs.append(f"File size: {format_size(file_size)}")

        # Create Basic Auth credentials
        credentials = base64.b64encode(f":{pixeldrain_api_key}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}

        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as file:
                # Create form data
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    file,
                    filename=os.path.basename(file_path),
                    content_type="application/octet-stream",
                )

                # Upload the file
                async with session.post(
                    "https://pixeldrain.com/api/file",
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=None),
                ) as response:
                    # Handle response
                    if response.status >= 400:
                        error_text = await response.text()
                        logs.append(
                            f"Upload failed with status {response.status}: {error_text}"
                        )
                        return {"error": f"HTTP {response.status}: {error_text}"}, logs

                    # Try to parse JSON response
                    try:
                        response_data = await response.json(content_type=None)
                    except Exception:
                        text = await response.text()
                        try:
                            response_data = json.loads(text) if text else {"id": None}
                        except Exception:
                            logs.append(
                                f"Could not parse response as JSON: {text[:200]}"
                            )
                            response_data = {"id": None, "raw": text}

        logs.append("Uploaded Successfully")

        # Delete the file after successful upload
        try:
            os.remove(file_path)
            logs.append("Removed media")
        except Exception as e:
            logs.append(f"Could not remove file: {str(e)}")

        return response_data, logs

    except aiohttp.ClientError as e:
        logs.append(f"Network error: {str(e)}")
        return {"error": str(e)}, logs
    except OSError as e:
        logs.append(f"File system error: {str(e)}")
        return {"error": str(e)}, logs
    except Exception as e:
        logs.append(f"Unexpected error: {str(e)}")
        return {"error": str(e)}, logs


async def background_upload(
    file_path: str,
    pixeldrain_api_key: str,
    message: Message,
    initial_logs: Optional[List[str]] = None,
) -> None:
    """
    Run the upload in background and update the Telegram message when done.

    Args:
        file_path: Path to the file to upload
        pixeldrain_api_key: API key for Pixeldrain
        message: Telegram message to update
        initial_logs: Optional initial logs
    """
    logs = initial_logs if initial_logs else []

    try:
        # Update status
        try:
            await message.edit_text(
                text="`Uploading in background...`", disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Error updating message: {e}")

        response_data, upload_logs = await upload_file_stream(
            file_path, pixeldrain_api_key, message
        )
        logs.extend(upload_logs)

        if "error" in response_data:
            try:
                await message.edit_text(
                    text=f"Error: `{response_data['error']}`\n\n" + "\n".join(logs),
                    disable_web_page_preview=True,
                )
            except Exception as e:
                print(f"Error updating message with error: {e}")
        else:
            try:
                await message.edit_text(
                    text="`Uploaded Successfully!`", disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Error updating message: {e}")

            # Send file info if ID is available
            file_id = response_data.get("id")
            if file_id:
                await send_data(file_id, message)
            else:
                # If no ID but raw response exists, show it
                raw = response_data.get("raw")
                if raw:
                    try:
                        await message.edit_text(
                            text=f"Uploaded but could not parse response. Raw:\n`{raw[:500]}`",
                            disable_web_page_preview=True,
                        )
                    except Exception as e:
                        print(f"Error updating message with raw response: {e}")
    except Exception as e:
        try:
            logs.append(f"Background worker error: {str(e)}")
            await message.edit_text(
                text=f"Unexpected error in background upload: `{str(e)}`\n\n"
                + "\n".join(logs),
                disable_web_page_preview=True,
            )
        except Exception as edit_error:
            print(f"Error updating message with exception: {edit_error}")


# ==================== Unauthorized User Handler ====================


@Bot.on_message(filters.private & ~filters.command("start"))
async def unauthorized_user_handler(bot: Client, message: Message) -> None:
    """Handler for unauthorized users attempting to use the bot."""
    if not authorized_user_filter(None, None, message):
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[BUTTON1, BUTTON2]]),
        )


# ==================== Group Upload Handler ====================


@Bot.on_message(
    filters.group
    & filters.reply
    & filters.command("pdup")
    & filters.create(authorized_user_filter)
)
async def group_upload_command(bot: Client, message: Message) -> None:
    """Handler for authorized users to use /pdup as reply to a file in groups."""
    replied_message = message.reply_to_message

    if not replied_message:
        await message.reply_text(
            "Please reply to a valid media message with /pdup to upload."
        )
        return

    # Guard against replied message without sender
    if not replied_message.from_user:
        await message.reply_text("Cannot upload media from anonymous/service messages.")
        return

    # Check if replied message contains media
    if (
        replied_message.photo
        or replied_message.document
        or replied_message.video
        or replied_message.audio
    ):
        await handle_media(bot, replied_message)
    else:
        await message.reply_text(
            "Please reply to a valid media message with /pdup to upload."
        )


# ==================== Main ====================

if __name__ == "__main__":
    print("Bot is starting...")
    try:
        Bot.run()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Bot crashed with error: {e}")
