import asyncio
import logging
import os
import uuid

import yt_dlp
from aiogram import Bot, types
from aiogram.types import FSInputFile

from instagram_config import (
    configure_instagram_download,
    get_instagram_auth_guidance,
    is_instagram_auth_error,
)
from youtube_config import (
    configure_youtube_download,
    get_youtube_auth_guidance,
    get_youtube_duration_limit_message,
    is_youtube_bot_check_error,
    is_youtube_duration_limit_error,
)


async def download_video(message: types.Message, bot: Bot, temp_directory: str, platform_name: str):
    progress_msg = await message.reply(f"⏳ Processing {platform_name} link...")
    temp_video_path = None
    try:
        request_id = str(uuid.uuid4())[:8]
        filename = f"{platform_name.lower()}_{message.from_user.id}_{request_id}.%(ext)s"
        output_path = os.path.join(temp_directory, filename)

        ytdlp_options = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',
        }

        if platform_name.lower() == 'youtube':
            configure_youtube_download(ytdlp_options)
        elif platform_name.lower() == 'instagram':
            configure_instagram_download(ytdlp_options)

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
            await bot.send_video(chat_id=message.chat.id, video=FSInputFile(temp_video_path))
            await progress_msg.delete()
        else:
            await progress_msg.edit_text("❌ Failed to download video.")
    except Exception as error:
        logging.error(f"Error processing {platform_name} link: {error}")
        if platform_name.lower() == 'youtube' and is_youtube_bot_check_error(error):
            await progress_msg.edit_text(get_youtube_auth_guidance())
        elif platform_name.lower() == 'youtube' and is_youtube_duration_limit_error(error):
            await progress_msg.edit_text(get_youtube_duration_limit_message())
        elif platform_name.lower() == 'instagram' and is_instagram_auth_error(error):
            await progress_msg.edit_text(get_instagram_auth_guidance())
        else:
            await progress_msg.edit_text(f"❌ An error occurred: {error}")
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
