import logging
import os

from aiogram import Bot, types
from aiogram.types import FSInputFile, InputMediaPhoto
from tiktokdl.download_post import get_post

from ytdlp_downloader import download_video


async def check_tiktok_content_type(url: str) -> str:
    if '/photo/' in url:
        return 'slideshow'
    return 'video'


async def download_tiktok_slideshow(message: types.Message, bot: Bot, temp_directory: str):
    progress_msg = await message.reply("⏳ Processing TikTok slideshow...")
    temp_files = []
    try:
        result = await get_post(message.text)

        if not result:
            await progress_msg.edit_text("❌ Failed to download slideshow. Trying as video...")
            await download_video(message, bot, temp_directory, "TikTok")
            return

        images = result.get('images', [])
        audio_path = result.get('audio')

        if images:
            temp_files.extend(images)
        if audio_path:
            temp_files.append(audio_path)

        if not images:
            await progress_msg.edit_text("❌ No images found. Trying as video...")
            await download_video(message, bot, temp_directory, "TikTok")
            return

        await progress_msg.edit_text("✅ Download complete! Sending slideshow...")

        for index in range(0, len(images), 10):
            batch = images[index:index + 10]
            media_group = [InputMediaPhoto(media=FSInputFile(img_path)) for img_path in batch]
            if media_group:
                await bot.send_media_group(chat_id=message.chat.id, media=media_group)

        if audio_path and os.path.exists(audio_path):
            await bot.send_audio(chat_id=message.chat.id, audio=FSInputFile(audio_path))

        await progress_msg.delete()
    except Exception as error:
        logging.error(f"Error processing TikTok slideshow: {error}")
        await progress_msg.edit_text(f"❌ An error occurred: {error}")
        try:
            await download_video(message, bot, temp_directory, "TikTok")
        except Exception:
            pass
    finally:
        for file_path in temp_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as error:
                    logging.error(f"Error removing file {file_path}: {error}")


async def handle_tiktok(message: types.Message, bot: Bot, temp_directory: str):
    content_type = await check_tiktok_content_type(message.text)
    if content_type == 'slideshow':
        await download_tiktok_slideshow(message, bot, temp_directory)
    else:
        await download_video(message, bot, temp_directory, "TikTok")