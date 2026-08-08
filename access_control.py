import logging
import os


class AccessControl:
    def __init__(self, base_dir: str):
        self.whitelist_file = os.path.join(base_dir, 'whitelist.txt')
        self.admins_file = os.path.join(base_dir, 'admins.txt')
        self.whitelisted_chat_ids: list[int] = []
        self.admin_ids: list[int] = []

    def load(self):
        self.whitelisted_chat_ids = self._load_ids(self.whitelist_file, 'Whitelist')
        self.admin_ids = self._load_ids(self.admins_file, 'Admins')

    def _load_ids(self, file_path: str, label: str) -> list[int]:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    content = file.read().strip()
                if content:
                    ids = [int(raw_id.strip()) for raw_id in content.split(',')]
                    logging.info("%s loaded: %s", label, ids)
                    return ids
                logging.warning("%s file is empty.", label.lower())
                return []
            logging.warning("%s not found.", os.path.basename(file_path))
            return []
        except Exception as error:
            logging.error("Error loading %s: %s", label.lower(), error)
            return []

    def _save_ids(self, file_path: str, values: list[int], label: str):
        try:
            with open(file_path, 'w') as file:
                file.write(','.join(map(str, values)))
            logging.info("%s saved: %s", label, values)
        except Exception as error:
            logging.error("Error saving %s: %s", label.lower(), error)

    def add_to_whitelist(self, user_id: int):
        if user_id not in self.whitelisted_chat_ids:
            self.whitelisted_chat_ids.append(user_id)
            self._save_ids(self.whitelist_file, self.whitelisted_chat_ids, 'Whitelist')

    def add_to_admins(self, user_id: int):
        if user_id not in self.admin_ids:
            self.admin_ids.append(user_id)
            self._save_ids(self.admins_file, self.admin_ids, 'Admins')

    def is_whitelisted(self, chat_id: int) -> bool:
        return chat_id in self.whitelisted_chat_ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def is_allowed_user(self, user_id: int) -> bool:
        return self.is_admin(user_id) or self.is_whitelisted(user_id)


def format_id_section(title: str, user_ids: list[int]) -> str:
    if not user_ids:
        return f"{title}:\n- None"
    formatted_ids = "\n".join(f"- {user_id}" for user_id in sorted(user_ids))
    return f"{title}:\n{formatted_ids}"
