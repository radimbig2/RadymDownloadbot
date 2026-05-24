import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from access_control import AccessControl
from command_handlers import register_access_middleware, register_commands
from dotenv import load_dotenv
from facebook_downloader import handle_facebook
from instagram_downloader import handle_instagram
from tiktok_downloader import handle_tiktok
from x_downloader import handle_x
from youtube_config import (
    log_youtube_startup_status,
)
from youtube_downloader import handle_youtube

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
BASE_DIR = os.path.dirname(__file__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
COMMON_KEY = os.getenv("COMMON_KEY")
TEMP_DIRECTORY = os.path.join(BASE_DIR, 'temp_videos')
os.makedirs(TEMP_DIRECTORY, exist_ok=True)
log_youtube_startup_status()

access_control = AccessControl(BASE_DIR)
access_control.load()


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

register_access_middleware(dp, access_control)
register_commands(dp, access_control, SECRET_KEY, COMMON_KEY)


# Dictionary for identifying platform based on URL
PLATFORM_IDENTIFIERS = {
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "x.com": "X",
    "twitter.com": "X",
}

# Handler for messages containing links
@dp.message()
async def handle_link(message: types.Message):
    if message.text:
        url = message.text
        if "tiktok.com" in url:
            await handle_tiktok(message, bot, TEMP_DIRECTORY)
        elif "instagram.com" in url:
            await handle_instagram(message, bot, TEMP_DIRECTORY)
        elif "youtube.com" in url or "youtu.be" in url:
            await handle_youtube(message, bot, TEMP_DIRECTORY)
        elif "facebook.com" in url or "fb.com" in url:
            await handle_facebook(message, bot, TEMP_DIRECTORY)
        elif "x.com" in url or "twitter.com" in url:
            await handle_x(message, bot, TEMP_DIRECTORY)
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
    port_value = os.environ.get('PORT')
    enable_web_server = os.environ.get('ENABLE_WEB_SERVER', '').lower() in {'1', 'true', 'yes'}

    if not port_value and not enable_web_server:
        logging.info("Skipping web server startup because PORT is not set.")
        return

    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)

    port = int(port_value or 8080)
    runner = web.AppRunner(app)
    await runner.setup()

    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logging.info(f"Web server started on port {port}")
    except OSError as exc:
        await runner.cleanup()
        if port_value or enable_web_server:
            raise
        logging.warning("Could not bind web server on port %s. Continuing without it: %s", port, exc)

async def main():
    # Start web server for Render.com
    await start_web_server()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
