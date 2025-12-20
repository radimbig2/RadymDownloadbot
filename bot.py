import asyncio
import logging
import os
import uuid
import yt_dlp
import glob
import requests
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaAudio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TEMP_DIRECTORY = os.path.join(os.path.dirname(__file__), 'temp_videos')
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

# --- Whitelist Configuration ---
WHITELIST_FILE = os.path.join(os.path.dirname(__file__), 'whitelist.txt')
WHITELISTED_CHAT_IDS = []

def load_whitelist():
    """Loads whitelisted chat IDs from the file."""
    global WHITELISTED_CHAT_IDS
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    # Split by comma and convert to integers
                    WHITELISTED_CHAT_IDS = [int(chat_id.strip()) for chat_id in content.split(',')]
                    logging.info(f"Whitelist loaded: {WHITELISTED_CHAT_IDS}")
                else:
                    logging.warning("Whitelist file is empty.")
        else:
            logging.warning("whitelist.txt not found. No one will be able to use the bot.")
    except Exception as e:
        logging.error(f"Error loading whitelist: {e}")

# Load the whitelist on startup
load_whitelist()
# --- End of Whitelist Configuration ---


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Middleware to check for whitelist
@dp.message.middleware()
async def whitelist_middleware(handler, event: types.Message, data: dict):
    if event.chat.id not in WHITELISTED_CHAT_IDS:
        await event.reply(f"Your Chat ID is: {event.chat.id} ask admin or deploy by yourself https://github.com/radimbig/telegram-media-download-bot")
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
    Downloads TikTok slideshow (images + audio) using TikWM API.
    """
    progress_msg = await message.reply(f"⏳ Processing TikTok slideshow...")
    temp_files = []
    try:
        request_id = str(uuid.uuid4())[:8]
        base_filename = f"tiktok_{message.from_user.id}_{request_id}"

        # Use TikWM API to get slideshow data
        def fetch_tiktok_data():
            try:
                api_url = "https://www.tikwm.com/api/"
                response = requests.post(api_url, data={'url': message.text}, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logging.error(f"Error fetching from TikWM API: {e}")
            return None

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_tiktok_data)

        if not data or data.get('code') != 0:
            await progress_msg.edit_text("❌ Failed to fetch slideshow data. Trying alternative method...")
            # Fallback to regular download
            await download_video(message, bot, "TikTok")
            return

        tiktok_data = data.get('data', {})

        # Get images
        image_urls = tiktok_data.get('images', [])

        # Get audio/music
        music_url = tiktok_data.get('music') or tiktok_data.get('music_info', {}).get('play')

        if not image_urls:
            await progress_msg.edit_text("❌ No images found in slideshow. Trying as video...")
            await download_video(message, bot, "TikTok")
            return

        # Download images
        images = []
        await progress_msg.edit_text(f"⏳ Downloading {len(image_urls)} images...")

        def download_image(url, index):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    ext = '.jpg'
                    content_type = response.headers.get('content-type', '')
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'

                    img_path = os.path.join(TEMP_DIRECTORY, f"{base_filename}_img_{index}{ext}")
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    return img_path
            except Exception as e:
                logging.error(f"Error downloading image {index}: {e}")
            return None

        for idx, url in enumerate(image_urls):
            img_path = await loop.run_in_executor(None, download_image, url, idx)
            if img_path:
                images.append(img_path)
                temp_files.append(img_path)

        # Download audio
        audio_path = None
        if music_url:
            await progress_msg.edit_text("⏳ Downloading audio...")

            def download_audio(url):
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        audio_path = os.path.join(TEMP_DIRECTORY, f"{base_filename}_audio.mp3")
                        with open(audio_path, 'wb') as f:
                            f.write(response.content)
                        return audio_path
                except Exception as e:
                    logging.error(f"Error downloading audio: {e}")
                return None

            audio_path = await loop.run_in_executor(None, download_audio, music_url)
            if audio_path:
                temp_files.append(audio_path)

        # Send content
        if not images:
            await progress_msg.edit_text("❌ Failed to download images.")
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
    finally:
        # Clean up all temp files
        for file_path in temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {e}")

async def check_tiktok_content_type(url: str) -> str:
    """
    Checks if TikTok URL is a video or slideshow.
    Returns: 'slideshow' or 'video'
    """
    # Simple check: if URL contains '/photo/', it's a slideshow
    if '/photo/' in url:
        return 'slideshow'

    # Try to fetch data from TikWM API to determine type
    try:
        def fetch_data():
            try:
                api_url = "https://www.tikwm.com/api/"
                response = requests.post(api_url, data={'url': url}, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        tiktok_data = data.get('data', {})
                        # If images field exists and has items, it's a slideshow
                        if tiktok_data.get('images'):
                            return 'slideshow'
            except:
                pass
            return 'video'

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fetch_data)

    except Exception as e:
        logging.error(f"Error checking TikTok content type: {e}")
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

# Handler for /status command
@dp.message(Command(commands=["status"]))
async def send_status(message: types.Message):
    await message.reply("I am alive")

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

async def main():
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
