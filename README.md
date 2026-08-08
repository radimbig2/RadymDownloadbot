# RadymDownloadBot

[English](#english) | [Українська](#українська) | [Русский](#русский)

---

## English

### 📥 RadymDownloadBot 📥

This is a Telegram bot that allows you to download media from TikTok, Instagram, YouTube, and X by simply sending a link. The bot is designed with a whitelist system, meaning only authorized users can interact with it.

### ✨ Features

- 🎬 **Media Downloads**: Download videos from TikTok, Instagram, and YouTube, plus photos and videos from X posts.
- 🔒 **Whitelist System**: Only users whose Chat IDs are in `whitelist.txt` can use the bot.
- 🚀 **Easy to Use**: Just send a link, and the bot does the rest.
- ⚙️ **Easy to Deploy**: A few simple steps to get your bot up and running.
- 🛠  **Command to manipulate whitelist** /add-user /add-admin /auth use commands to modify whitelist while running 

### 🛠️ Local Installation and Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your_username/RadymDownloadbot.git
    cd RadymDownloadbot
    ```

2. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Install FFmpeg:**
    ```bash
    # macOS
    brew install ffmpeg

    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # Windows
    # Download from https://ffmpeg.org/download.html
    ```

4. **Create a bot in Telegram:**
    - Talk to [@BotFather](https://t.me/BotFather) on Telegram.
    - Create a new bot and get the **token**.

5. **Create the `.env` file:**
    - Create a file named `.env` in the root of the project.
    - The fastest option is to copy `.env.example` to `.env` and replace the placeholder values.
    - Add your bot token and authentication keys to it:
        ```
        BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        SECRET_KEY=YOUR_ADMIN_SECRET_KEY
        COMMON_KEY=YOUR_USER_SECRET_KEY

        # Optional: YouTube authentication via env secret
        # Recommended for hosting/container deployments
        YTDLP_COOKIES_BASE64=PASTE_BASE64_NETSCAPE_COOKIES_HERE

        # Optional: YouTube max duration in seconds
        # Default is 300 seconds (5 minutes)
        YOUTUBE_MAX_DURATION_SECONDS=300

        # Optional: X post downloads
        # X_BEARER_TOKEN takes priority.
        # X_BEARER_TOKEN=YOUR_X_APP_BEARER_TOKEN
        # X_CONSUMER_KEY=YOUR_X_APP_CONSUMER_KEY
        # X_SECRET_KEY=YOUR_X_APP_SECRET_KEY
        # X_ACCESS_TOKEN=YOUR_X_ACCESS_TOKEN
        # X_ACCESS_TOKEN_SECRET=YOUR_X_ACCESS_TOKEN_SECRET
        ```
    - `SECRET_KEY` — the key that grants **admin** access when used with `/auth`.
    - `COMMON_KEY` — the key that grants regular **user** access when used with `/auth`.

6. **Set up the whitelist:**
    - Create a file named `whitelist.txt` in the root of the project.
    - Add the Telegram Chat IDs of the users who are allowed to use the bot. Separate multiple IDs with commas.
        ```
        123456789,987654321
        ```
    - To find out a user's Chat ID, they can send any message to the bot (when it's running). The bot will reply with their Chat ID if they are not in the whitelist.

7. **Run the bot:**
    ```bash
    python bot.py
    ```

### 🔐 YouTube Authentication

If YouTube replies with `Sign in to confirm you’re not a bot`, provide YouTube cookies through environment variables only.

Recommended `.env` setup:

```env
YTDLP_COOKIES_BASE64=PASTE_BASE64_NETSCAPE_COOKIES_HERE
```

Flow:

1. Export YouTube cookies on your own PC from the dedicated Google account in Netscape format.
2. Convert that cookies text to base64.
3. Put the result into `YTDLP_COOKIES_BASE64` in your hosting or container environment.
4. Restart the bot.

Helper script:

```bash
python encode_cookies_env.py cookies.txt
```

The script prints a ready-to-paste line like `YTDLP_COOKIES_BASE64=...`.

Notes:

- A separate Google account is recommended instead of your main one.
- The bot no longer reads cookies from the local browser profile.
- `YTDLP_COOKIES_BASE64` is recommended for hosting panels because it avoids multiline formatting issues.
- If your platform supports multiline env values, you can use raw Netscape cookies in `YTDLP_COOKIES` instead.

### 🔐 Instagram Authentication

Instagram may return an empty media response for reels that require a logged-in
session. Export cookies from a browser where Instagram is logged in, then keep
them in a separate secret:

```bash
python encode_cookies_env.py instagram-cookies.txt --var-name INSTAGRAM_COOKIES_BASE64
```

Add the generated `INSTAGRAM_COOKIES_BASE64=...` line to `.env` or your hosting
environment and restart the bot. Raw Netscape text can alternatively be supplied
as `INSTAGRAM_COOKIES`. Use a separate Instagram account because session cookies
provide account access; never commit or share them.

For local development, keep the exported file under the Git-ignored `.secrets`
directory and add `INSTAGRAM_COOKIES_FILE=.secrets/instagram-cookies.txt` to
`.env`.

TikTok login/age-restricted videos use a separate session. Export TikTok cookies
to `.secrets/tiktok-cookies.txt` and add
`TIKTOK_COOKIES_FILE=.secrets/tiktok-cookies.txt` to `.env`.

### 🤖 How to Use

1. **Start the bot:**
    - Find your bot in Telegram and press "Start".

2. **Send a link:**
    - Send a link to media from TikTok, Instagram, YouTube, or X.

3. **Get the media:**
    - The bot will process the link, download the media, and send it to you in the chat.

### Inline mode

Authorized users can use the bot in chats where it is not a member by typing
`@RadimBigTest_bot` followed by a supported link. Access is checked against the
bot's admins and whitelist by Telegram user ID.

1. Enable inline mode with `/setinline` in `@BotFather`.
2. Create a private storage channel and add the bot as an administrator with
   permission to post messages.
3. Configure its ID and optionally the short inline wait time:

    ```env
    INLINE_STORAGE_CHAT_ID=-1004377346553
    INLINE_QUERY_WAIT_SECONDS=8
    ```

The bot uploads prepared media to that private channel and reuses Telegram's
`file_id` in the inline result. Slow downloads continue in the background; select
the processing result and use its **Check again** button after a few seconds.

### 🔑 Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/start` | Everyone | Start the bot and receive a welcome message. |
| `/status` | Whitelisted users | Check if the bot is running. |
| `/auth [key]` | Everyone | Authenticate yourself. Use `SECRET_KEY` to become an **admin**, or `COMMON_KEY` to become a regular **user**. Example: `/auth mysecretkey` |
| `/add-user [user_id]` | Admins only | Add a user to the whitelist by their Telegram Chat ID. Example: `/add-user 123456789` |
| `/add-admin [user_id]` | Admins only | Promote a user to admin by their Telegram Chat ID. Example: `/add-admin 123456789` |
| `/list` | Admins only | List all admins and whitelisted users currently stored by the bot. |

> **Tip:** If you are not yet whitelisted, send any message to the bot — it will reply with your Chat ID, which you can then use with `/auth` or share with an admin.

---

## Українська

### 📥 RadymDownloadBot 📥

Це Telegram-бот, який дозволяє завантажувати відео з TikTok, Instagram та YouTube, просто надіславши посилання. Бот розроблений з системою "білого списку", що означає, що тільки авторизовані користувачі можуть взаємодіяти з ним.

### ✨ Функції

- 🎬 **Завантаження відео**: Завантажуйте відео з TikTok, Instagram та YouTube.
- 🔒 **Система "білого списку"**: Тільки користувачі, чиї Chat ID знаходяться в `whitelist.txt`, можуть використовувати бота.
- 🚀 **Простий у використанні**: Просто надішліть посилання, і бот зробить все інше.
- ⚙️ **Легке розгортання**: Кілька простих кроків, щоб запустити вашого бота.

### 🛠️ Локальна установка та налаштування

1. **Клонуйте репозиторій:**
    ```bash
    git clone https://github.com/your_username/RadymDownloadbot.git
    cd RadymDownloadbot
    ```

2. **Встановіть залежності:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Встановіть FFmpeg:**
    ```bash
    # macOS
    brew install ffmpeg

    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # Windows
    # Завантажте з https://ffmpeg.org/download.html
    ```

4. **Створіть бота в Telegram:**
    - Поговоріть з [@BotFather](https://t.me/BotFather) в Telegram.
    - Створіть нового бота та отримайте **токен**.

5. **Створіть файл `.env`:**
    - Створіть файл з назвою `.env` в корені проекту.
    - Найзручніше скопіювати `.env.example` у `.env` і замінити значення-заповнювачі.
    - Додайте до нього токен бота та ключі автентифікації:
        ```
        BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН
        SECRET_KEY=ВАШ_СЕКРЕТНИЙ_КЛЮЧ_АДМІНА
        COMMON_KEY=ВАШ_СЕКРЕТНИЙ_КЛЮЧ_КОРИСТУВАЧА

        # Опціонально: авторизація для YouTube через env-секрет
        YTDLP_COOKIES_BASE64=ВСТАВТЕ_BASE64_NETSCAPE_COOKIES

        # Опціонально: максимальна тривалість YouTube у секундах
        # За замовчуванням 300 секунд (5 хвилин)
        YOUTUBE_MAX_DURATION_SECONDS=300
        ```
    - `SECRET_KEY` — ключ, що надає права **адміна** при використанні з `/auth`.
    - `COMMON_KEY` — ключ, що надає права звичайного **користувача** при використанні з `/auth`.

6. **Налаштуйте "білий список":**
    - Створіть файл з назвою `whitelist.txt` в корені проекту.
    - Додайте Telegram Chat ID користувачів, яким дозволено використовувати бота. Розділяйте кілька ID комами.
        ```
        123456789,987654321
        ```
    - Щоб дізнатися Chat ID користувача, він може надіслати будь-яке повідомлення боту (коли він запущений). Бот відповість його Chat ID, якщо його немає в "білому списку".

7. **Запустіть бота:**
    ```bash
    python bot.py
    ```

### 🔐 Авторизація YouTube

Якщо YouTube повертає `Sign in to confirm you’re not a bot`, передайте cookies для YouTube тільки через змінні середовища.

Рекомендоване налаштування `.env`:

```env
YTDLP_COOKIES_BASE64=ВСТАВТЕ_BASE64_NETSCAPE_COOKIES
```

Кроки:

1. Експортуйте YouTube cookies на своєму ПК з виділеного Google-акаунта у форматі Netscape.
2. Закодуйте цей текст у base64.
3. Додайте результат у `YTDLP_COOKIES_BASE64` на хостингу або в контейнері.
4. Перезапустіть бота.

Допоміжний скрипт:

```bash
python encode_cookies_env.py cookies.txt
```

Скрипт виведе готовий рядок виду `YTDLP_COOKIES_BASE64=...` для вставки в env.

Примітки:

- Бот більше не читає cookies з локального профілю браузера.
- Для панелей хостингу `YTDLP_COOKIES_BASE64` зручніший, бо не ламається на переносах рядків.
- Якщо ваш env підтримує багаторядкові значення, можна використати `YTDLP_COOKIES` з сирим Netscape-текстом.

### 🔐 Авторизація Instagram

Для деяких reels Instagram вимагає авторизовану сесію та без неї повертає порожню
медіавідповідь. Експортуйте cookies з браузера, де виконано вхід в Instagram:

```bash
python encode_cookies_env.py instagram-cookies.txt --var-name INSTAGRAM_COOKIES_BASE64
```

Додайте створений рядок `INSTAGRAM_COOKIES_BASE64=...` у `.env` або змінні
хостингу та перезапустіть бота. Також підтримується сирий Netscape-текст у
`INSTAGRAM_COOKIES`. Використовуйте окремий Instagram-акаунт і не публікуйте cookies.

Для локальної розробки збережіть файл у виключеній з Git папці `.secrets` і
додайте `INSTAGRAM_COOKIES_FILE=.secrets/instagram-cookies.txt` у `.env`.

Для TikTok-відео з авторизацією або віковим обмеженням експортуйте окремий файл
`.secrets/tiktok-cookies.txt` і додайте
`TIKTOK_COOKIES_FILE=.secrets/tiktok-cookies.txt` у `.env`.

### 🤖 Як користуватися

1. **Запустіть бота:**
    - Знайдіть вашого бота в Telegram і натисніть "Start".

2. **Надішліть посилання:**
    - Надішліть посилання на відео з TikTok, Instagram або YouTube.

3. **Отримайте відео:**
    - Бот обробить посилання, завантажить відео та надішле його вам у чат.

### 🔑 Команди

| Команда | Доступ | Опис |
|---------|--------|------|
| `/start` | Усі | Запустити бота та отримати привітальне повідомлення. |
| `/status` | Авторизовані користувачі | Перевірити, чи запущений бот. |
| `/auth [ключ]` | Усі | Автентифікуватись. Використовуйте `SECRET_KEY`, щоб стати **адміном**, або `COMMON_KEY`, щоб стати звичайним **користувачем**. Приклад: `/auth mysecretkey` |
| `/add-user [user_id]` | Тільки адміни | Додати користувача до білого списку за його Telegram Chat ID. Приклад: `/add-user 123456789` |
| `/add-admin [user_id]` | Тільки адміни | Надати права адміна користувачу за його Telegram Chat ID. Приклад: `/add-admin 123456789` |
| `/list` | Тільки адміни | Показати всіх адміністраторів і користувачів у білому списку. |

> **Підказка:** Якщо вас ще немає в білому списку, надішліть будь-яке повідомлення боту — він відповість вашим Chat ID, який ви зможете використати з `/auth` або передати адміну.

---

## Русский

### 📥 RadymDownloadBot 📥

Это Telegram-бот, который позволяет скачивать видео из TikTok, Instagram и YouTube, просто отправив ссылку. Бот разработан с системой "белого списка", что означает, что только авторизованные пользователи могут взаимодействовать с ним.

### ✨ Функции

- 🎬 **Скачивание видео**: Скачивайте видео из TikTok, Instagram и YouTube.
- 🔒 **Система "белого списка"**: Только пользователи, чьи Chat ID находятся в `whitelist.txt`, могут использовать бота.
- 🚀 **Прост в использовании**: Просто отправьте ссылку, и бот сделает все остальное.
- ⚙️ **Легкое развертывание**: Несколько простых шагов, чтобы запустить вашего бота.

### 🛠️ Локальная установка и настройка

1. **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/your_username/RadymDownloadbot.git
    cd RadymDownloadbot
    ```

2. **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Установите FFmpeg:**
    ```bash
    # macOS
    brew install ffmpeg

    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # Windows
    # Скачать с https://ffmpeg.org/download.html
    ```

4. **Создайте бота в Telegram:**
    - Поговорите с [@BotFather](https://t.me/BotFather) в Telegram.
    - Создайте нового бота и получите **токен**.

5. **Создайте файл `.env`:**
    - Создайте файл с названием `.env` в корне проекта.
    - Быстрее всего скопировать `.env.example` в `.env` и заменить значения-заглушки.
    - Добавьте в него токен бота и ключи аутентификации:
        ```
        BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН
        SECRET_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_АДМИНА
        COMMON_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ПОЛЬЗОВАТЕЛЯ

        # Необязательно: авторизация для YouTube через env-секрет
        YTDLP_COOKIES_BASE64=ВСТАВЬТЕ_BASE64_NETSCAPE_COOKIES

        # Необязательно: максимальная длина YouTube в секундах
        # По умолчанию 300 секунд (5 минут)
        YOUTUBE_MAX_DURATION_SECONDS=300
        ```
    - `SECRET_KEY` — ключ, который даёт права **администратора** при использовании с `/auth`.
    - `COMMON_KEY` — ключ, который даёт права обычного **пользователя** при использовании с `/auth`.

### 🔐 Авторизация YouTube

Если YouTube отвечает `Sign in to confirm you’re not a bot`, нужно дать `yt-dlp` cookies от Google-аккаунта.

Поддерживается только передача cookies через env.

Рекомендуемая настройка `.env`:

```env
YTDLP_COOKIES_BASE64=ВСТАВЬТЕ_BASE64_NETSCAPE_COOKIES
```

Порядок действий:

1. На своем ПК экспортируйте YouTube cookies нужного Google-аккаунта в формате Netscape.
2. Закодируйте этот текст в base64.
3. Добавьте результат в переменную окружения `YTDLP_COOKIES_BASE64` на хостинге.
4. Перезапустите бота.

Вспомогательный скрипт:

```bash
python encode_cookies_env.py cookies.txt
```

Скрипт выведет готовую строку вида `YTDLP_COOKIES_BASE64=...`, которую можно вставить в env.

Замечания:

- Лучше использовать отдельный Google-аккаунт, а не основной.
- Чтение cookies из локального браузера удалено.
- Если хостинг поддерживает многострочные env-переменные, можно использовать `YTDLP_COOKIES` с сырым Netscape-текстом вместо base64.

### 🔐 Авторизация Instagram

Для некоторых reels Instagram требует авторизованную сессию и без неё возвращает
пустой медиаответ. Экспортируйте cookies из браузера, где выполнен вход в Instagram:

```bash
python encode_cookies_env.py instagram-cookies.txt --var-name INSTAGRAM_COOKIES_BASE64
```

Добавьте полученную строку `INSTAGRAM_COOKIES_BASE64=...` в `.env` или переменные
хостинга и перезапустите бота. Также поддерживается сырой Netscape-текст в
`INSTAGRAM_COOKIES`. Используйте отдельный Instagram-аккаунт и не публикуйте cookies.

Для локальной разработки сохраните файл в исключённой из Git папке `.secrets` и
добавьте `INSTAGRAM_COOKIES_FILE=.secrets/instagram-cookies.txt` в `.env`.

Для TikTok-видео с авторизацией или возрастным ограничением экспортируйте
отдельный файл `.secrets/tiktok-cookies.txt` и добавьте
`TIKTOK_COOKIES_FILE=.secrets/tiktok-cookies.txt` в `.env`.

6. **Настройте "белый список":**
    - Создайте файл с названием `whitelist.txt` в корне проекта.
    - Добавьте Telegram Chat ID пользователей, которым разрешено использовать бота. Разделяйте несколько ID запятыми.
        ```
        123456789,987654321
        ```
    - Чтобы узнать Chat ID пользователя, он может отправить любое сообщение боту (когда он запущен). Бот ответит его Chat ID, если его нет в "белом списке".

7. **Запустите бота:**
    ```bash
    python bot.py
    ```

### 🤖 Как пользоваться

1. **Запустите бота:**
    - Найдите вашего бота в Telegram и нажмите "Start".

2. **Отправьте ссылку:**
    - Отправьте ссылку на видео из TikTok, Instagram или YouTube.

3. **Получите видео:**
    - Бот обработает ссылку, скачает видео и отправит его вам в чат.

### 🔑 Команды

| Команда | Доступ | Описание |
|---------|--------|----------|
| `/start` | Все | Запустить бота и получить приветственное сообщение. |
| `/status` | Авторизованные пользователи | Проверить, работает ли бот. |
| `/auth [ключ]` | Все | Аутентифицироваться. Используйте `SECRET_KEY`, чтобы стать **администратором**, или `COMMON_KEY`, чтобы стать обычным **пользователем**. Пример: `/auth mysecretkey` |
| `/add-user [user_id]` | Только администраторы | Добавить пользователя в белый список по его Telegram Chat ID. Пример: `/add-user 123456789` |
| `/add-admin [user_id]` | Только администраторы | Выдать права администратора пользователю по его Telegram Chat ID. Пример: `/add-admin 123456789` |
| `/list` | Только администраторы | Показать всех администраторов и пользователей из белого списка. |

> **Подсказка:** Если вас ещё нет в белом списке, отправьте боту любое сообщение — он ответит вашим Chat ID, который можно использовать с `/auth` или передать администратору.
