from aiogram import Bot, types

from ytdlp_downloader import download_video


async def handle_facebook(message: types.Message, bot: Bot, temp_directory: str):
    await download_video(message, bot, temp_directory, "Facebook")