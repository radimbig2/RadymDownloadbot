import asyncio
import logging
import os
import uuid
import yt_dlp
import glob
import requests
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaAudio
from dotenv import load_dotenv
from tiktokdl.download_post import get_post

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
COMMON_KEY = os.getenv("COMMON_KEY")
TEMP_DIRECTORY = os.path.join(os.path.dirname(__file__), 'temp_videos')
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

# --- Whitelist and Admin Configuration ---
WHITELIST_FILE = os.path.join(os.path.dirname(__file__), 'whitelist.txt')
ADMINS_FILE = os.path.join(os.path.dirname(__file__), 'admins.txt')
WHITELISTED_CHAT_IDS = []
ADMIN_IDS = []

def load_whitelist():
    """Loads whitelisted chat IDs from the file."""
    global WHITELISTED_CHAT_IDS
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    WHITELISTED_CHAT_IDS = [int(chat_id.strip()) for chat_id in content.split(',')]
                    logging.info(f"Whitelist loaded: {WHITELISTED_CHAT_IDS}")
                else:
                    logging.warning("Whitelist file is empty.")
        else:
            logging.warning("whitelist.txt not found.")
    except Exception as e:
        logging.error(f"Error loading whitelist: {e}")

def load_admins():
    """Loads admin IDs from the file."""
    global ADMIN_IDS
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    ADMIN_IDS = [int(admin_id.strip()) for admin_id in content.split(',')]
                    logging.info(f"Admins loaded: {ADMIN_IDS}")
                else:
                    logging.warning("Admins file is empty.")
        else:
            logging.warning("admins.txt not found.")
    except Exception as e:
        logging.error(f"Error loading admins: {e}")

def save_whitelist():
    """Saves whitelisted chat IDs to the file."""
    try:
        with open(WHITELIST_FILE, 'w') as f:
            f.write(','.join(map(str, WHITELISTED_CHAT_IDS)))
        logging.info(f"Whitelist saved: {WHITELISTED_CHAT_IDS}")
    except Exception as e:
        logging.error(f"Error saving whitelist: {e}")

def save_admins():
    """Saves admin IDs to the file."""
    try:
        with open(ADMINS_FILE, 'w') as f:
            f.write(','.join(map(str, ADMIN_IDS)))
        logging.info(f"Admins saved: {ADMIN_IDS}")
    except Exception as e:
        logging.error(f"Error saving admins: {e}")

def add_to_whitelist(user_id: int):
    """Adds a user to the whitelist."""
    if user_id not in WHITELISTED_CHAT_IDS:
        WHITELISTED_CHAT_IDS.append(user_id)
        save_whitelist()

def add_to_admins(user_id: int):
    """Adds a user to admins."""
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        save_admins()

def format_id_section(title: str, user_ids: list[int]) -> str:
    """Formats a section of user IDs for bot responses."""
    if not user_ids:
        return f"{title}:\n- None"
    formatted_ids = "\n".join(f"- {user_id}" for user_id in sorted(user_ids))
    return f"{title}:\n{formatted_ids}"

# Load the whitelist and admins on startup
load_whitelist()
load_admins()
# --- End of Whitelist and Admin Configuration ---


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Middleware to check for whitelist
@dp.message.middleware()
async def whitelist_middleware(handler, event: types.Message, data: dict):
    # Skip whitelist check for /auth command
    if event.text and event.text.startswith('/auth'):
        return await handler(event, data)
    
    if event.chat.id not in WHITELISTED_CHAT_IDS:
        await event.reply(f"Your Chat ID is: {event.chat.id}\nUse /auth [key] to authenticate or ask admin.\nGitHub: https://github.com/radimbig/telegram-media-download-bot")
        return
    return await handler(event, data)


# Dictionary for identifying platform based on URL
PLATFORM_IDENTIFIERS = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}

async def download_video(message: types.Message, bot: Bot, platform_name: str):
    """
    Handles video download for a given platform.
    """
    progress_msg = await message.reply(f"⏳ Processing {platform_name} link...")
    temp_video_path = None
    try:
        request_id = str(uuid.uuid4())[:8]
        filename = f"{platform_name.lower()}_{message.from_user.id}_{request_id}.%(ext)s"
        output_path = os.path.join(TEMP_DIRECTORY, filename)

        ytdlp_options = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',
        }

        if platform_name.lower() == 'youtube':
            ytdlp_options['format'] = 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best'
            ytdlp_options['merge_output_format'] = 'mp4'


        def run_ytdlp():
            with yt_dlp.YoutubeDL(ytdlp_options) as ydl:
                ydl.download([message.text])
                base_path = output_path.replace('.%(ext)s', '')
                for ext in ['.mp4', '.webm', '.mkv']:
                    potential_path = base_path + ext
                    if os.path.exists(potential_path):
                        return potential_path
                return None

        loop = asyncio.get_event_loop()
        temp_video_path = await loop.run_in_executor(None, run_ytdlp)

        if temp_video_path and os.path.exists(temp_video_path):
            await progress_msg.edit_text("✅ Download complete! Sending video...")
            video_file = FSInputFile(temp_video_path)
            await bot.send_video(chat_id=message.chat.id, video=video_file)
            await progress_msg.delete()
        else:
            await progress_msg.edit_text("❌ Failed to download video.")

    except Exception as e:
        logging.error(f"Error processing {platform_name} link: {e}")
        await progress_msg.edit_text(f"❌ An error occurred: {e}")
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)

async def download_tiktok_slideshow(message: types.Message, bot: Bot):
    """
    Downloads TikTok slideshow (images + audio) using tiktok-dlpy.
    """
    progress_msg = await message.reply(f"⏳ Processing TikTok slideshow...")
    temp_files = []
    try:
        # Use tiktok-dlpy to download the slideshow
        result = await get_post(message.text)

        if not result:
            await progress_msg.edit_text("❌ Failed to download slideshow. Trying as video...")
            await download_video(message, bot, "TikTok")
            return

        # get_post returns a dictionary with downloaded file paths
        # Expected structure: {'images': [path1, path2, ...], 'audio': path}
        images = result.get('images', [])
        audio_path = result.get('audio')

        # Add all downloaded files to temp_files for cleanup
        if images:
            temp_files.extend(images)
        if audio_path:
            temp_files.append(audio_path)

        if not images:
            await progress_msg.edit_text("❌ No images found. Trying as video...")
            await download_video(message, bot, "TikTok")
            return

        await progress_msg.edit_text("✅ Download complete! Sending slideshow...")

        # Send images in batches (Telegram limit is 10 media items per group)
        for i in range(0, len(images), 10):
            batch = images[i:i+10]
            media_group = [InputMediaPhoto(media=FSInputFile(img_path)) for img_path in batch]
            if media_group:
                await bot.send_media_group(chat_id=message.chat.id, media=media_group)

        # Send audio if available
        if audio_path and os.path.exists(audio_path):
            audio_file = FSInputFile(audio_path)
            await bot.send_audio(chat_id=message.chat.id, audio=audio_file)

        await progress_msg.delete()

    except Exception as e:
        logging.error(f"Error processing TikTok slideshow: {e}")
        await progress_msg.edit_text(f"❌ An error occurred: {e}")
        # Try fallback to regular video download
        try:
            await download_video(message, bot, "TikTok")
        except:
            pass
    finally:
        # Clean up all temp files
        for file_path in temp_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {e}")

async def check_tiktok_content_type(url: str) -> str:
    """
    Checks if TikTok URL is a video or slideshow.
    Returns: 'slideshow' or 'video'
    """
    # If URL contains '/photo/', it's a slideshow
    if '/photo/' in url:
        return 'slideshow'

    # Otherwise it's a regular video
    return 'video'

async def handle_tiktok(message: types.Message, bot: Bot):
    """
    Handles TikTok content - detects if it's a video or slideshow and processes accordingly.
    """
    content_type = await check_tiktok_content_type(message.text)

    if content_type == 'slideshow':
        await download_tiktok_slideshow(message, bot)
    else:
        await download_video(message, bot, "TikTok")

async def handle_instagram(message: types.Message, bot: Bot):
    await download_video(message, bot, "Instagram")

async def handle_youtube(message: types.Message, bot: Bot):
    await download_video(message, bot, "YouTube")


# Handler for /start command
@dp.message(Command(commands=["start"]))
async def send_welcome(message: types.Message):
    await message.reply("Hello! I am bot radym. Send me a link to download a video.")

# Handler for /help command
@dp.message(Command(commands=["help"]))
async def send_help(message: types.Message):
    help_text = (
        "📖 <b>Available Commands</b>\n\n"
        "<code>/start</code> — Welcome message\n"
        "<code>/help</code> — Show this help message\n"
        "<code>/status</code> — Check if the bot is running\n"
        "<code>/auth [key]</code> — Authenticate yourself with a key to gain access.\n"
        "  • Use the <b>admin key</b> to get admin privileges.\n"
        "  • Use the <b>user key</b> to get standard access.\n\n"
        "🔐 <b>Admin-only Commands</b>\n\n"
        "<code>/add-admin [user_id]</code> — Grant admin rights to a user by their Telegram user ID\n"
        "<code>/add-user [user_id]</code> — Add a user to the whitelist by their Telegram user ID\n"
        "<code>/list</code> — Show all admins and whitelisted users\n\n"
        "🎬 <b>Downloading Media</b>\n\n"
        "Simply send a link from one of the supported platforms and the bot will download and send the media to you:\n"
        "• <b>TikTok</b> — videos and photo slideshows (with audio)\n"
        "• <b>Instagram</b> — videos\n"
        "• <b>YouTube</b> — videos (up to 1080p)\n"
        "• <b>Facebook</b> — videos\n\n"
        "ℹ️ If you are not authenticated, send any message to get your Chat ID, then use <code>/auth [key]</code> to gain access."
    )
    await message.reply(help_text, parse_mode="HTML")

# Handler for /status command
@dp.message(Command(commands=["status"]))
async def send_status(message: types.Message):
    await message.reply("I am alive")

# Handler for /auth command
@dp.message(Command(commands=["auth"]))
async def auth_user(message: types.Message):
    try:
        # Parse command: /auth [key]
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ Usage: /auth [key]")
            return
        
        key = parts[1].strip()
        user_id = message.from_user.id
        
        if key == SECRET_KEY:
            # Add to both admins and whitelist
            add_to_admins(user_id)
            add_to_whitelist(user_id)
            await message.reply("✅ You have been authenticated as ADMIN!")
        elif key == COMMON_KEY:
            # Add only to whitelist
            add_to_whitelist(user_id)
            await message.reply("✅ You have been authenticated as USER!")
        else:
            await message.reply("❌ Invalid authentication key.")
    except Exception as e:
        logging.error(f"Error in auth command: {e}")
        await message.reply(f"❌ An error occurred: {e}")

# Handler for /add-admin command (only for admins)
@dp.message(Command(commands=["add-admin"]))
async def add_admin_command(message: types.Message):
    try:
        # Check if user is admin
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ This command is only for admins.")
            return
        
        # Parse command: /add-admin [user_id]
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ Usage: /add-admin [user_id]")
            return
        
        try:
            new_admin_id = int(parts[1].strip())
        except ValueError:
            await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
            return
        
        # Add to both admins and whitelist
        add_to_admins(new_admin_id)
        add_to_whitelist(new_admin_id)
        await message.reply(f"✅ User {new_admin_id} has been added as ADMIN!")
    except Exception as e:
        logging.error(f"Error in add-admin command: {e}")
        await message.reply(f"❌ An error occurred: {e}")

# Handler for /add-user command (only for admins)
@dp.message(Command(commands=["add-user"]))
async def add_user_command(message: types.Message):
    try:
        # Check if user is admin
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ This command is only for admins.")
            return
        
        # Parse command: /add-user [user_id]
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("❌ Usage: /add-user [user_id]")
            return
        
        try:
            new_user_id = int(parts[1].strip())
        except ValueError:
            await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
            return
        
        # Add only to whitelist
        add_to_whitelist(new_user_id)
        await message.reply(f"✅ User {new_user_id} has been added to whitelist!")
    except Exception as e:
        logging.error(f"Error in add-user command: {e}")
        await message.reply(f"❌ An error occurred: {e}")

# Handler for /list command (only for admins)
@dp.message(Command(commands=["list"]))
async def list_users_command(message: types.Message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ This command is only for admins.")
            return

        admin_ids = sorted(set(ADMIN_IDS))
        whitelist_ids = sorted(set(WHITELISTED_CHAT_IDS))
        user_ids = [user_id for user_id in whitelist_ids if user_id not in admin_ids]
        response_text = (
            "👥 Access list\n\n"
            f"{format_id_section('Admins', admin_ids)}\n\n"
            f"{format_id_section('Whitelisted users', user_ids)}"
        )
        await message.reply(response_text)
    except Exception as e:
        logging.error(f"Error in list command: {e}")
        await message.reply(f"❌ An error occurred: {e}")

# Handler for messages containing links
@dp.message()
async def handle_link(message: types.Message):
    if message.text:
        url = message.text
        if "tiktok.com" in url:
            await handle_tiktok(message, bot)
        elif "instagram.com" in url:
            await handle_instagram(message, bot)
        elif "youtube.com" in url or "youtu.be" in url:
            await handle_youtube(message, bot)
        else:
            # This part might not be reached due to the whitelist middleware,
            # but it's good practice to keep it.
            is_platform_link = False
            for platform in PLATFORM_IDENTIFIERS:
                if platform in url:
                    is_platform_link = True
                    break
            if is_platform_link:
                 await message.reply("This platform is not yet supported for downloading.")
            # If it's not a link to a known platform, do nothing.

async def health_check(request):
    """Health check endpoint for Render.com"""
    return web.Response(text="Bot is running!")

async def start_web_server():
    """Start a simple web server for Render.com port binding"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    # Start web server for Render.com
    await start_web_server()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
