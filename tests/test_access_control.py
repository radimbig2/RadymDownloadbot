from aiogram.enums import ChatType

from access_control import AccessControl, DEFAULT_WHITELIST_IDS
from command_handlers import should_notify_unauthorized


DEFAULT_GROUP_ID = -1003440257797


def test_default_group_is_whitelisted_without_a_file(tmp_path) -> None:
    access = AccessControl(str(tmp_path))

    access.load()

    assert DEFAULT_GROUP_ID in DEFAULT_WHITELIST_IDS
    assert access.is_whitelisted(DEFAULT_GROUP_ID)


def test_default_whitelist_is_merged_with_file_values(tmp_path) -> None:
    (tmp_path / "whitelist.txt").write_text("123,456", encoding="utf-8")
    access = AccessControl(str(tmp_path))

    access.load()

    assert set(access.whitelisted_chat_ids) == {DEFAULT_GROUP_ID, 123, 456}


def test_unauthorized_group_is_silent_without_supported_link() -> None:
    assert not should_notify_unauthorized(ChatType.GROUP, "hello everyone")
    assert not should_notify_unauthorized(ChatType.SUPERGROUP, None)


def test_unauthorized_group_gets_access_hint_for_supported_link() -> None:
    assert should_notify_unauthorized(
        ChatType.SUPERGROUP,
        "https://www.instagram.com/reel/example/",
    )


def test_private_chat_still_gets_access_instructions() -> None:
    assert should_notify_unauthorized(ChatType.PRIVATE, "hello")
