import os
import aiohttp
import dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pymongo import MongoClient

dotenv.load_dotenv()

Bot = Client(
    "Pixeldrain-Bot",
    bot_token=os.environ["BOT_TOKEN"],
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"]
)

PIXELDRAIN_API_KEY = os.environ["PIXELDRAIN_API_KEY"]

START_TEXT = """Hello {},
Ready to share some media? Send a file to get a Pixeldrain stream link, or drop a Pixeldrain media ID or link to get the scoop on your file!"""

UNAUTH_TEXT = """Sorry, you are not authorized to use this bot. Please contact the bot owner for access."""

BUTTON1 = InlineKeyboardButton(text="𝘗𝘳𝘫𝘬𝘵:𝘚𝘪𝘥.", url="https://burhanverse.t.me")
BUTTON2 = InlineKeyboardButton(text="Contact Owner", url="https://aqxzaxbot.t.me")

MONGODB_URI = os.environ["MONGODB_URI"]
client = MongoClient(MONGODB_URI)
db = client['pixeldrain_bot']
authorized_users_col = db['authorized_users']

# Function to check if the user is authorized
def is_authorized(user_id):
    return authorized_users_col.find_one({"user_id": user_id}) is not None

# Filter to check if the user is authorized
def authorized_user_filter(_, __, message: Message):
    return is_authorized(message.from_user.id)
    
# Handler for /start command
@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, message):
    if authorized_user_filter(None, None, message):
        await message.reply_text(
            text=START_TEXT.format(message.from_user.mention),
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([
            [BUTTON1, BUTTON2]
            ])
        )
    else:
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([
            [BUTTON1, BUTTON2]
            ])
        )

# Update user information in the database
def update_user_info(user_id, username):
    authorized_users_col.update_one(
        {"user_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

# Function to update username field in the database
async def update_username(bot, user_id):
    user_info = await bot.get_users(user_id)
    username = user_info.username or "No username"
    update_user_info(user_id, username)

# Handler for /auth command (only for the bot owner)
@Bot.on_message(filters.command("auth"))
async def auth(bot, message: Message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        try:
            if message.reply_to_message:
                user = message.reply_to_message.from_user
            else:
                user_id = int(message.command[1])
                user = await bot.get_users(user_id)
            
            user_id = user.id
            username = user.username or "No username"

            if not is_authorized(user_id):
                authorized_users_col.insert_one({"user_id": user_id, "username": username})
                await message.reply_text(f"User {user_id} (@{username}) has been authorized.")
            else:
                await update_username(bot, user_id)
                await message.reply_text(f"User {user_id} (@{username}) is already authorized.")
        except (IndexError, ValueError):
            await message.reply_text("Usage: /auth <user_id> or reply to a user's message with /auth")
    else:
        await message.reply_text("You are not authorized to use this command.")

# Handler for /auths command (only for the bot owner)
@Bot.on_message(filters.command("auths"))
async def auths(bot, message: Message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        authorized_users = authorized_users_col.find()
        text = "**Authorized Users:**\n"
        for user in authorized_users:
            user_id = user["user_id"]
            username = user.get("username", "No username")
            if username == "No username":
                await update_username(bot, user_id)
                user_info = await bot.get_users(user_id)
                username = user_info.username or "No username"
            text += f"[{user_id}](tg://user?id={user_id}) (@{username})\n"
        await message.reply_text(text, disable_web_page_preview=True)
    else:
        await message.reply_text("You are not authorized to use this command.")

# Handler for /unauth command (only for the bot owner)
@Bot.on_message(filters.command("unauth"))
async def unauth(bot, message: Message):
    owner_id = int(os.environ["OWNER_ID"])
    if message.from_user.id == owner_id:
        try:
            if message.reply_to_message:
                user_id = message.reply_to_message.from_user.id
            else:
                user_id = int(message.command[1])

            user_info = await bot.get_users(user_id)
            username = user_info.username or "No username"

            result = authorized_users_col.delete_one({"user_id": user_id})
            if result.deleted_count:
                await message.reply_text(f"User {user_id} (@{username}) has been unauthorized.")
            else:
                await message.reply_text(f"User {user_id} is not found.")
        except (IndexError, ValueError):
            await message.reply_text("Usage: /unauth <user_id> or reply to a user's message with /unauth")
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
    """Format file size in human-readable format, supporting files up to TB"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

def format_date(date_str):
    date, time = date_str.split("T")
    time = time.split(".")[0]
    return f"{date} {time}"

async def send_data(id, message):
    # pixeldrain data
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pixeldra.in/api/file/{id}/info") as response:
                data = await response.json() if response.status == 200 else None
    except Exception as e:
        data = None
        print(f"Error: {e}")

    if data:
        text = (
            f"**File Name:** `{data['name']}`\n"
            f"**Upload Date:** `{format_date(data['date_upload'])}`\n"
            f"**File Size:** `{format_size(data['size'])}`\n"
            f"**File Type:** `{data['mime_type']}`\n\n"
            f"\u00A9 [𝘗𝘳𝘫𝘬𝘵:𝘚𝘪𝘥.](https://burhanverse.t.me)"
        )
    else:
        text = "Failed to retrieve file information."

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Open Link",
                    url=f"https://pixeldra.in/u/{id}"
                ),
                InlineKeyboardButton(
                    text="Direct Link",
                    url=f"https://pixeldra.in/api/file/{id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Share Link",
                    url=f"https://telegram.me/share/url?url=https://pixeldra.in/u/{id}"
                )
            ],
            [BUTTON2]
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

# Handler for authorized users to upload media in private chats
@Bot.on_message(filters.private & filters.media & filters.create(authorized_user_filter))
async def media_filter(bot, update):
    await handle_media(bot, update)

async def handle_media(bot, update):
    logs = []
    message = await update.reply_text(
        text="`Processing...`",
        quote=True,
        disable_web_page_preview=True
    )

    try:
        # Download the media
        try:
            await message.edit_text(
                text="`Downloading...`",
                disable_web_page_preview=True
            )
        except:
            pass

        media = await update.download()
        logs.append("Downloaded Successfully")

        # Rename file to include user ID
        user_id = update.from_user.id
        dir_name, file_name = os.path.split(media)
        file_base, file_extension = os.path.splitext(file_name)
        renamed_file = os.path.join(dir_name, f"{file_base}_{user_id}{file_extension}")
        os.rename(media, renamed_file)
        logs.append("Renamed file successfully")

        # Get file size for progress tracking
        file_size = os.path.getsize(renamed_file)
        logs.append(f"File size: {format_size(file_size)}")

        # Upload the file
        try:
            await message.edit_text(
                text=f"`Downloaded Successfully ({format_size(file_size)}), Now Uploading...`",
                disable_web_page_preview=True
            )
        except:
            pass

        # Call the chunked upload function
        response_data, upload_logs = await upload_file_stream(renamed_file, PIXELDRAIN_API_KEY, message)
        logs.extend(upload_logs)  # Append logs from the upload function

        if "error" in response_data:
            await message.edit_text(
                text=f"Error :- `{response_data['error']}`" + "\n\n" + '\n'.join(logs),
                disable_web_page_preview=True
            )
        else:
            await message.edit_text(
                text="`Uploaded Successfully!`",
                disable_web_page_preview=True
            )
            await send_data(response_data["id"], message)

    except Exception as error:
        await message.edit_text(
            text=f"Error :- `{error}`" + "\n\n" + '\n'.join(logs),
            disable_web_page_preview=True
        )


async def upload_file_stream(file_path, pixeldrain_api_key, message=None, chunk_size=10 * 1024 * 1024):  # 10 MB chunks
    """
    Upload a file to Pixeldrain using chunked streaming to support large files (>2GB).
    This implementation reads and sends the file in chunks without loading it entirely into memory.
    
    Args:
        file_path: Path to the file to upload
        pixeldrain_api_key: API key for authentication
        message: Optional Telegram message object for progress updates
        chunk_size: Size of chunks to read (default 10MB)
    """
    logs = []
    
    try:
        file_size = os.path.getsize(file_path)
        logs.append(f"File size: {format_size(file_size)}")
        
        # For files larger than 100MB, show progress updates
        show_progress = file_size > 100 * 1024 * 1024  # 100MB
        last_update_time = 0
        
        # Custom payload class for progress tracking
        class ProgressPayload:
            def __init__(self, file_path, message, file_size, chunk_size):
                self.file_path = file_path
                self.message = message
                self.file_size = file_size
                self.chunk_size = chunk_size
                self.uploaded = 0
                self.last_update = 0
                
            async def read(self, n=-1):
                """Read method that tracks progress"""
                import time
                with open(self.file_path, 'rb') as f:
                    f.seek(self.uploaded)
                    chunk = f.read(self.chunk_size if n == -1 else n)
                    
                    if chunk:
                        self.uploaded += len(chunk)
                        
                        # Update progress every 5 seconds for large files
                        if self.message and show_progress:
                            current_time = time.time()
                            if current_time - self.last_update >= 5:
                                self.last_update = current_time
                                progress = (self.uploaded / self.file_size) * 100
                                try:
                                    await self.message.edit_text(
                                        text=f"`Uploading... {progress:.1f}% ({format_size(self.uploaded)} / {format_size(self.file_size)})`",
                                        disable_web_page_preview=True
                                    )
                                except:
                                    pass
                    
                    return chunk
        
        # Create aiohttp session with auth
        auth = aiohttp.BasicAuth('', pixeldrain_api_key)
        
        async with aiohttp.ClientSession() as session:
            # Create a multipart form data with file streaming
            with open(file_path, 'rb') as file:
                # Create form data
                data = aiohttp.FormData()
                data.add_field('file',
                              file,
                              filename=os.path.basename(file_path),
                              content_type='application/octet-stream')
                
                # Upload the file with streaming
                async with session.post(
                    "https://pixeldra.in/api/file",
                    data=data,
                    auth=auth,
                    timeout=aiohttp.ClientTimeout(total=None)  # No timeout for large files
                ) as response:
                    response.raise_for_status()  # Check for HTTP errors
                    response_data = await response.json()

        logs.append("Uploaded Successfully")
        os.remove(file_path)  # Delete the file after successful upload
        logs.append("Removed media")

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


        
# Handler for unauthorized users attempting to use the bot
@Bot.on_message(filters.private & ~filters.command("start"))
async def unauthorized_user_handler(bot, message):
    if not authorized_user_filter(None, None, message):
        await message.reply_text(
            text=UNAUTH_TEXT,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup([
            [BUTTON1, BUTTON2]
            ])
        )

# Handler for authorized users to use /pdup as reply to a file in groups
@Bot.on_message(filters.group & filters.reply & filters.command("pdup") & filters.create(authorized_user_filter))
async def group_upload_command(bot, message):
    replied_message = message.reply_to_message
    if replied_message and (replied_message.photo or replied_message.document or replied_message.video or replied_message.audio):
        await handle_media(bot, replied_message)
    else:
        await message.reply_text("Please reply to a valid media message with /pdup to upload.")

Bot.run()
        
