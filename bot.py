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
from instagram_config import log_instagram_startup_status
from tiktok_downloader import handle_tiktok
from tiktok_config import log_tiktok_startup_status
from x_downloader import handle_x
from youtube_config import (
    log_youtube_startup_status,
)
from youtube_downloader import handle_youtube
from inline_mode import InlineMediaService, extract_supported_url
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()
BASE_DIR = os.path.dirname(__file__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
COMMON_KEY = os.getenv("COMMON_KEY")
INLINE_STORAGE_CHAT_ID = os.getenv("INLINE_STORAGE_CHAT_ID", "-1004377346553")
INLINE_QUERY_WAIT_SECONDS = float(os.getenv("INLINE_QUERY_WAIT_SECONDS", "8"))
TEMP_DIRECTORY = os.path.join(BASE_DIR, 'temp_videos')
os.makedirs(TEMP_DIRECTORY, exist_ok=True)
log_youtube_startup_status()
log_instagram_startup_status()
log_tiktok_startup_status()

access_control = AccessControl(BASE_DIR)
access_control.load()


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

register_access_middleware(dp, access_control)
register_commands(dp, access_control, SECRET_KEY, COMMON_KEY)

inline_media_service = None
if INLINE_STORAGE_CHAT_ID:
    inline_media_service = InlineMediaService(
        bot,
        int(INLINE_STORAGE_CHAT_ID),
        TEMP_DIRECTORY,
        INLINE_QUERY_WAIT_SECONDS,
    )


def inline_notice(result_id: str, title: str, message: str, query: str | None = None):
    keyboard = None
    if query:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔄 Check again",
                    switch_inline_query_current_chat=query,
                )
            ]]
        )
    return InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=message,
        input_message_content=InputTextMessageContent(message_text=message),
        reply_markup=keyboard,
    )


@dp.inline_query()
async def handle_inline_query(inline_query: types.InlineQuery):
    if not access_control.is_allowed_user(inline_query.from_user.id):
        await inline_query.answer(
            [inline_notice("access-denied", "Access denied", "Your Telegram ID is not in the bot whitelist.")],
            cache_time=0,
            is_personal=True,
        )
        return

    parsed = extract_supported_url(inline_query.query)
    if not parsed:
        await inline_query.answer(
            [inline_notice("send-link", "Send a supported link", "Paste a TikTok, Instagram, YouTube, Facebook, or X link.")],
            cache_time=0,
            is_personal=True,
        )
        return

    if inline_media_service is None:
        await inline_query.answer(
            [inline_notice("not-configured", "Inline mode is not configured", "INLINE_STORAGE_CHAT_ID is missing.")],
            cache_time=0,
            is_personal=True,
        )
        return

    url, platform = parsed
    try:
        status, stored_media = await inline_media_service.get_or_start(
            url,
            platform,
            inline_query.from_user.id,
        )
        if status == "ready":
            results = inline_media_service.build_results(stored_media, url)
        else:
            results = [inline_notice(
                "processing",
                f"Processing {platform} link…",
                "The media is still being prepared. Tap Check again in a few seconds.",
                url,
            )]
        await inline_query.answer(results, cache_time=0, is_personal=True)
    except Exception as error:
        logging.exception("Inline query processing failed")
        await inline_query.answer(
            [inline_notice("processing-error", "Could not process this link", str(error)[:200])],
            cache_time=0,
            is_personal=True,
        )


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
