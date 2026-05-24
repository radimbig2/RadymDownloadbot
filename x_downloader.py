import asyncio
import logging
import os
import uuid

from aiogram import Bot, types
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo

from x_download import XConfigurationError, XDownloadError, download_x_post_assets


def build_x_caption(author_username: str | None, text: str | None) -> str:
    parts = []
    if author_username:
        parts.append(f"@{author_username}")
    if text:
        parts.append(text.strip())
    return "\n\n".join(part for part in parts if part)


async def send_x_media(bot: Bot, chat_id: int, files: list[dict], caption: str | None):
    if not caption:
        caption_for_media = None
    elif len(caption) <= 1024:
        caption_for_media = caption
    else:
        caption_for_media = None

    if len(files) == 1:
        file_info = files[0]
        media_file = FSInputFile(file_info['path'])
        if file_info['media_type'] == 'photo':
            await bot.send_photo(chat_id=chat_id, photo=media_file, caption=caption_for_media)
        else:
            await bot.send_video(chat_id=chat_id, video=media_file, caption=caption_for_media)
        if caption and caption_for_media is None:
            await bot.send_message(chat_id=chat_id, text=caption)
        return

    media_group = []
    for index, file_info in enumerate(files):
        item_caption = caption_for_media if index == 0 else None
        file_input = FSInputFile(file_info['path'])
        if file_info['media_type'] == 'photo':
            media_group.append(InputMediaPhoto(media=file_input, caption=item_caption))
        else:
            media_group.append(InputMediaVideo(media=file_input, caption=item_caption))

    await bot.send_media_group(chat_id=chat_id, media=media_group)
    if caption and caption_for_media is None:
        await bot.send_message(chat_id=chat_id, text=caption)


async def handle_x(message: types.Message, bot: Bot, temp_directory: str):
    progress_msg = await message.reply("⏳ Processing X link...")
    temp_files = []

    try:
        request_id = str(uuid.uuid4())[:8]

        def run_x_download():
            return download_x_post_assets(message.text, temp_directory, message.from_user.id, request_id)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_x_download)
        temp_files = [file_info['path'] for file_info in result['files']]
        caption = build_x_caption(result.get('author_username'), result.get('text'))

        if not result['files']:
            if caption:
                await progress_msg.edit_text(caption)
            else:
                await progress_msg.edit_text("❌ The X post does not contain downloadable media.")
            return

        await progress_msg.edit_text("✅ Download complete! Sending media...")
        await send_x_media(bot, message.chat.id, result['files'], caption)
        await progress_msg.delete()
    except XConfigurationError as error:
        logging.error(f"X configuration error: {error}")
        await progress_msg.edit_text(f"❌ {error}")
    except XDownloadError as error:
        logging.error(f"X download error: {error}")
        await progress_msg.edit_text(f"❌ {error}")
    except Exception as error:
        logging.error(f"Unexpected X processing error: {error}")
        await progress_msg.edit_text(f"❌ An error occurred: {error}")
    finally:
        for file_path in temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)