import logging

from aiogram import Dispatcher, types
from aiogram.filters import Command

from access_control import AccessControl, format_id_section


def register_access_middleware(dp: Dispatcher, access_control: AccessControl):
    @dp.message.middleware()
    async def whitelist_middleware(handler, event: types.Message, data: dict):
        if event.text and event.text.startswith('/auth'):
            return await handler(event, data)

        if not access_control.is_whitelisted(event.chat.id):
            await event.reply(
                f"Your Chat ID is: {event.chat.id}\n"
                "Use /auth [key] to authenticate or ask admin.\n"
                "GitHub: https://github.com/radimbig/telegram-media-download-bot"
            )
            return
        return await handler(event, data)


def register_commands(
    dp: Dispatcher,
    access_control: AccessControl,
    secret_key: str | None,
    common_key: str | None,
):
    @dp.message(Command(commands=["start"]))
    async def send_welcome(message: types.Message):
        await message.reply("Hello! I am bot radym. Send me a link to download a video.")

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
            "• <b>X</b> — photos and videos from post links\n"
            "• <b>Facebook</b> — videos\n\n"
            "You can also type <code>@RadimBigTest_bot [link]</code> in any chat to use inline mode.\n"
            "Inline mode is available to bot admins and whitelisted users.\n\n"
            "ℹ️ If you are not authenticated, send any message to get your Chat ID, then use <code>/auth [key]</code> to gain access."
        )
        await message.reply(help_text, parse_mode="HTML")

    @dp.message(Command(commands=["status"]))
    async def send_status(message: types.Message):
        await message.reply("I am alive")

    @dp.message(Command(commands=["auth"]))
    async def auth_user(message: types.Message):
        try:
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.reply("❌ Usage: /auth [key]")
                return

            key = parts[1].strip()
            user_id = message.from_user.id

            if key == secret_key:
                access_control.add_to_admins(user_id)
                access_control.add_to_whitelist(user_id)
                await message.reply("✅ You have been authenticated as ADMIN!")
            elif key == common_key:
                access_control.add_to_whitelist(user_id)
                await message.reply("✅ You have been authenticated as USER!")
            else:
                await message.reply("❌ Invalid authentication key.")
        except Exception as error:
            logging.error("Error in auth command: %s", error)
            await message.reply(f"❌ An error occurred: {error}")

    @dp.message(Command(commands=["add-admin"]))
    async def add_admin_command(message: types.Message):
        try:
            if not access_control.is_admin(message.from_user.id):
                await message.reply("❌ This command is only for admins.")
                return

            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.reply("❌ Usage: /add-admin [user_id]")
                return

            try:
                new_admin_id = int(parts[1].strip())
            except ValueError:
                await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
                return

            access_control.add_to_admins(new_admin_id)
            access_control.add_to_whitelist(new_admin_id)
            await message.reply(f"✅ User {new_admin_id} has been added as ADMIN!")
        except Exception as error:
            logging.error("Error in add-admin command: %s", error)
            await message.reply("❌ An internal error occurred while adding the admin.")

    @dp.message(Command(commands=["add-user"]))
    async def add_user_command(message: types.Message):
        try:
            if not access_control.is_admin(message.from_user.id):
                await message.reply("❌ This command is only for admins.")
                return

            parts = message.text.split(maxsplit=1)
            if len(parts) < 2:
                await message.reply("❌ Usage: /add-user [user_id]")
                return

            try:
                new_user_id = int(parts[1].strip())
            except ValueError:
                await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
                return

            access_control.add_to_whitelist(new_user_id)
            await message.reply(f"✅ User {new_user_id} has been added to whitelist!")
        except Exception as error:
            logging.error("Error in add-user command: %s", error)
            await message.reply("❌ An internal error occurred while adding the user.")

    @dp.message(Command(commands=["list"]))
    async def list_users_command(message: types.Message):
        try:
            if not access_control.is_admin(message.from_user.id):
                await message.reply("❌ This command is only for admins.")
                return

            admin_ids_set = set(access_control.admin_ids)
            whitelist_ids = set(access_control.whitelisted_chat_ids)
            regular_user_ids = [user_id for user_id in whitelist_ids if user_id not in admin_ids_set]
            response_text = (
                "👥 Access list\n\n"
                f"{format_id_section('Admins', list(admin_ids_set))}\n\n"
                f"{format_id_section('Whitelisted users', regular_user_ids)}"
            )
            await message.reply(response_text)
        except Exception as error:
            logging.error("Error in list command: %s", error)
            await message.reply("❌ An internal error occurred while loading the access list.")
