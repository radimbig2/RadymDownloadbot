# RadymDownloadBot

[English](#english) | [Українська](#українська) | [Русский](#русский)

---

## English

### 📥 RadymDownloadBot 📥

This is a Telegram bot that allows you to download videos from TikTok, Instagram, and YouTube by simply sending a link. The bot is designed with a whitelist system, meaning only authorized users can interact with it.

### ✨ Features

- 🎬 **Video Downloads**: Download videos from TikTok, Instagram, and YouTube.
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
    - Add your bot token and authentication keys to it:
        ```
        BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
        SECRET_KEY=YOUR_ADMIN_SECRET_KEY
        COMMON_KEY=YOUR_USER_SECRET_KEY
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

### 🤖 How to Use

1. **Start the bot:**
    - Find your bot in Telegram and press "Start".

2. **Send a link:**
    - Send a link to a video from TikTok, Instagram, or YouTube.

3. **Get the video:**
    - The bot will process the link, download the video, and send it to you in the chat.

### 🔑 Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/start` | Everyone | Start the bot and receive a welcome message. |
| `/status` | Whitelisted users | Check if the bot is running. |
| `/auth [key]` | Everyone | Authenticate yourself. Use `SECRET_KEY` to become an **admin**, or `COMMON_KEY` to become a regular **user**. Example: `/auth mysecretkey` |
| `/add-user [user_id]` | Admins only | Add a user to the whitelist by their Telegram Chat ID. Example: `/add-user 123456789` |
| `/add-admin [user_id]` | Admins only | Promote a user to admin by their Telegram Chat ID. Example: `/add-admin 123456789` |

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
    - Додайте до нього токен бота та ключі автентифікації:
        ```
        BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН
        SECRET_KEY=ВАШ_СЕКРЕТНИЙ_КЛЮЧ_АДМІНА
        COMMON_KEY=ВАШ_СЕКРЕТНИЙ_КЛЮЧ_КОРИСТУВАЧА
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
    - Добавьте в него токен бота и ключи аутентификации:
        ```
        BOT_TOKEN=ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН
        SECRET_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_АДМИНА
        COMMON_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ПОЛЬЗОВАТЕЛЯ
        ```
    - `SECRET_KEY` — ключ, который даёт права **администратора** при использовании с `/auth`.
    - `COMMON_KEY` — ключ, который даёт права обычного **пользователя** при использовании с `/auth`.

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

> **Подсказка:** Если вас ещё нет в белом списке, отправьте боту любое сообщение — он ответит вашим Chat ID, который можно использовать с `/auth` или передать администратору.
