import asyncio
import logging
import os
import uuid

from aiogram import Bot, types
from aiogram.types import FSInputFile, InputMediaPhoto
from pinchana_tiktok import (
    TikTokConfigurationError,
    TikTokDownloadError,
    download_tiktok_post_assets,
)


def build_tiktok_caption(author_username: str | None, caption: str | None) -> str:
    parts = []
    if author_username:
        username = author_username.lstrip("@")
        parts.append(f"@{username}")
    if caption:
        parts.append(caption.strip())
    return "\n\n".join(part for part in parts if part)


async def send_tiktok_assets(
    bot: Bot,
    chat_id: int,
    files: list[dict],
    caption: str | None,
) -> None:
    visual_files = [item for item in files if item["media_type"] != "audio"]
    audio_files = [item for item in files if item["media_type"] == "audio"]
    inline_caption = caption if caption and len(caption) <= 1024 else None
    caption_used = False

    if len(visual_files) == 1 and visual_files[0]["media_type"] == "video":
        await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(visual_files[0]["path"]),
            caption=inline_caption,
        )
        caption_used = bool(inline_caption)
    elif visual_files:
        photos = [item for item in visual_files if item["media_type"] == "photo"]
        for offset in range(0, len(photos), 10):
            batch = photos[offset:offset + 10]
            if len(batch) == 1:
                photo_caption = inline_caption if not caption_used else None
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=FSInputFile(batch[0]["path"]),
                    caption=photo_caption,
                )
                caption_used = caption_used or bool(photo_caption)
                continue
            media_group = []
            for item in batch:
                item_caption = inline_caption if not caption_used and not media_group else None
                media_group.append(
                    InputMediaPhoto(
                        media=FSInputFile(item["path"]),
                        caption=item_caption,
                    )
                )
            if media_group:
                await bot.send_media_group(chat_id=chat_id, media=media_group)
                caption_used = caption_used or bool(inline_caption)

    for item in audio_files:
        audio_caption = inline_caption if not caption_used else None
        await bot.send_audio(
            chat_id=chat_id,
            audio=FSInputFile(item["path"]),
            caption=audio_caption,
        )
        caption_used = caption_used or bool(audio_caption)

    if caption and not caption_used:
        await bot.send_message(chat_id=chat_id, text=caption)


async def handle_tiktok(message: types.Message, bot: Bot, temp_directory: str):
    progress_msg = await message.reply("⏳ Processing TikTok link...")
    temp_files: list[str] = []
    try:
        request_id = str(uuid.uuid4())[:8]

        def run_download():
            return download_tiktok_post_assets(
                message.text,
                temp_directory,
                message.from_user.id,
                request_id,
            )

        result = await asyncio.get_running_loop().run_in_executor(None, run_download)
        temp_files = [item["path"] for item in result["files"]]
        caption = build_tiktok_caption(
            result.get("author_username"), result.get("caption")
        )

        if not result["files"]:
            await progress_msg.edit_text(
                caption or "❌ The TikTok post does not contain downloadable media."
            )
            return

        await progress_msg.edit_text("✅ Download complete! Sending media...")
        await send_tiktok_assets(bot, message.chat.id, result["files"], caption)
        await progress_msg.delete()
    except TikTokConfigurationError as error:
        logging.error("TikTok configuration error: %s", error)
        await progress_msg.edit_text(f"❌ {error}")
    except TikTokDownloadError as error:
        logging.error("TikTok download error: %s", error)
        await progress_msg.edit_text(f"❌ {error}")
    except Exception as error:
        logging.exception("Unexpected TikTok processing error")
        await progress_msg.edit_text(f"❌ An error occurred: {error}")
    finally:
        for file_path in temp_files:
            if file_path and os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError as error:
                    logging.error("Error removing TikTok file %s: %s", file_path, error)
