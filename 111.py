from typing import Any

import asyncio
from aiogram.types import ChatPermissions
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, User, Chat

TOKEN = '8090773665:AAEgc4TLBnAPAGP8N5p_G10sIDbksjas_as'
ADMIN_IDS: Any = 6056422825, 7466673069  # Ваш ID администратора

# Хранение данных пользователей
users = {}  # user_id: {"username": "", "balance": 0, "last_salary": None, "rank": None, "work": "", "age": None, "inventory": "", "wanted": False, "bio": "", "admin": False}

# Список событий
events = {}  # event_id: {"name": "", "participants": []}

# Список администраторов
admins = {ADMIN_IDS: True}

# Система наказаний
punishments = {
    "warns": {},  # user_id: [{"reason": "", "admin": "", "date": ""}]
    "mutes": {},  # user_id: {"until": datetime, "reason": "", "admin": ""}
    "bans": {}  # user_id: {"reason": "", "admin": "", "date": ""}
}

# Структура с рангами и зарплатами (только цифры)
RANKS = {
    "1": 4000,
    "2": 4200,
    "3": 4500,
    "4": 4700,
    "5": 4800,
    "6": 5000,
    "7": 5200,
    "8": 6000,
    "9": 6200,
    "10": 7000,
    "11": 7100,
    "12": 7800,
    "13": 8000,
    "14": 8700,
    "15": 8800,
    "16": 9000,
    "17": 9700,
    "18": 9800,
    "19": 10000,
    "20": 11000,
    "21": 11500
}

bot = Bot(token=TOKEN)
dp = Dispatcher()


def get_or_create_user(user: User):
    if user.id not in users:
        users[user.id] = {
            "username": user.username or user.full_name or f"user_{user.id}",
            'balance': 0,
            'last_salary': None,
            'rank': None,
            'work': "Не указана",
            'age': None,
            'inventory': "Пусто",
            'wanted': False,
            'bio': "Не указана",
            'admin': user.id in admins
        }
    return user.id


async def check_chat_type(message: Message):
    if message.chat.type == 'private':
        reply = "✨ *Привет!* ✨\n\n" \
                "Этот бот работает только в группе *@OutagamieCountyRolePlay*.\n\n" \
                "🔹 Пожалуйста, переходите в группу для использования всех функций бота.\n" \
                "🔹 Если у вас есть вопросы, обратитесь к администрации.\n\n" \
                "С уважением, команда *Outagamie County RolePlay*."
        await message.answer(reply, parse_mode="Markdown")
        return False
    return True


# ==================== СИСТЕМА НАКАЗАНИЙ ====================


@dp.message(Command("warn"))
async def warn_user(message: Message):
    if message.from_user.id not in admins:
        await message.answer("❌ *Эта команда только для администратора!*", parse_mode="Markdown")
        return

    try:
        # Формат команды: /warn @username причина
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError

        _, username, reason = parts
        username = username.lstrip('@').lower()

        # Поиск пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return

        # Добавляем варн
        if target_user_id not in punishments["warns"]:
            punishments["warns"][target_user_id] = []

        punishments["warns"][target_user_id].append({
            "reason": reason,
            "admin": users[message.from_user.id]['username'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        warn_count = len(punishments["warns"][target_user_id])
        await message.answer(f"⚠️ *Пользователь @{users[target_user_id]['username']} получил варн!*\n\n"
                             f"📌 *Причина:* {reason}\n"
                             f"🔢 *Количество варнов:* {warn_count}/3\n"
                             f"👮 *Администратор:* @{users[message.from_user.id]['username']}",
                             parse_mode="Markdown")

        # Если 3 варна - автоматический бан на 14 дней
        if warn_count >= 3:
            await ban_user_auto(message, target_user_id, "Автоматический бан за 3 варна")

    except Exception as e:
        await message.answer("❌ *Неправильный формат команды*\n\n"
                             "🔹 Используйте: /warn @ник причина\n"
                             "🔹 Пример: /warn @user Оскорбление игроков",
                             parse_mode="Markdown")


async def ban_user_auto(message: Message, user_id: int, reason: str):
    # Устанавливаем бан на 14 дней
    ban_until = datetime.now() + timedelta(days=14)

    # Добавляем бан
    punishments["bans"][user_id] = {
        "reason": reason,
        "admin": "Система",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "until": ban_until
    }

    # Ограничиваем доступ к группе (реализация зависит от API вашего мессенджера)
    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
    except Exception as e:
        print(f"Ошибка при ограничении доступа: {e}")

    # Оповещаем о бане
    await message.answer(f"⛔ *Пользователь @{users[user_id]['username']} забанен на 14 дней!*\n\n"
                         f"📌 *Причина:* {reason}\n"
                         f"🔢 *Количество варнов:* 3/3\n"
                         f"🕒 *Разбан:* {ban_until.strftime('%Y-%m-%d %H:%M:%S')}\n"
                         f"🤖 *Администратор:* Система",
                         parse_mode="Markdown")

    # Удаляем варны
    if user_id in punishments["warns"]:
        del punishments["warns"][user_id]


@dp.message(Command("mute"))
async def mute_user(message: Message):
    if message.from_user.id not in admins:
        await message.answer("❌ *Эта команда только для администратора!*", parse_mode="Markdown")
        return

    try:
        # Формат команды: /mute @username время причина
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            raise ValueError

        _, username, time_str, reason = parts
        username = username.lstrip('@').lower()

        # Парсим время (формат: 1h, 30m, 2d)
        time_value = int(time_str[:-1])
        time_unit = time_str[-1].lower()

        if time_unit == 'm':
            mute_duration = timedelta(minutes=time_value)
        elif time_unit == 'h':
            mute_duration = timedelta(hours=time_value)
        elif time_unit == 'd':
            mute_duration = timedelta(days=time_value)
        else:
            raise ValueError("Неверный формат времени")

        mute_until = datetime.now() + mute_duration

        # Поиск пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return

        # Устанавливаем мут
        punishments["mutes"][target_user_id] = {
            "until": mute_until,
            "reason": reason,
            "admin": users[message.from_user.id]['username']
        }

        # Блокируем отправку сообщений в чате
        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                ),
                until_date=mute_until
            )
        except Exception as e:
            print(f"Ошибка при муте пользователя: {e}")

        await message.answer(f"🔇 *Пользователь @{users[target_user_id]['username']} получил мут!*\n\n"
                             f"📌 *Причина:* {reason}\n"
                             f"⏳ *Длительность:* {time_str}\n"
                             f"🕒 *Размут:* {mute_until.strftime('%Y-%m-%d %H:%M:%S')}\n"
                             f"👮 *Администратор:* @{users[message.from_user.id]['username']}",
                             parse_mode="Markdown")

    except Exception as e:
        await message.answer("❌ *Неправильный формат команды*\n\n"
                             "🔹 Используйте: /mute @ник время причина\n"
                             "🔹 Примеры:\n"
                             "   /mute @user 30m Флуд\n"
                             "   /mute @user 2h Оскорбления\n"
                             "   /mute @user 1d Нарушение правил",
                             parse_mode="Markdown")


@dp.message(Command("unmute"))
async def unmute_user(message: Message):
    if message.from_user.id not in admins:
        await message.answer("❌ *Эта команда только для администратора!*", parse_mode="Markdown")
        return

    try:
        # Формат команды: /unmute @username
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError

        _, username = parts
        username = username.lstrip('@').lower()

        # Поиск пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return

        if target_user_id not in punishments["mutes"]:
            await message.answer(f"ℹ️ *Пользователь @{users[target_user_id]['username']} не в муте.*",
                                 parse_mode="Markdown")
            return

        # Снимаем мут
        removed_mute = punishments["mutes"].pop(target_user_id)

        # Восстанавливаем права в чате
        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
            )
        except Exception as e:
            print(f"Ошибка при размуте пользователя: {e}")

        await message.answer(f"🔊 *Мут снят с @{users[target_user_id]['username']}!*\n\n"
                             f"📌 *Причина мута:* {removed_mute['reason']}\n"
                             f"👮 *Администратор:* @{users[message.from_user.id]['username']}",
                             parse_mode="Markdown")

    except Exception as e:
        await message.answer("❌ *Неправильный формат команды*\n\n"
                             "🔹 Используйте: /unmute @ник\n"
                             "🔹 Пример: /unmute @user",
                             parse_mode="Markdown")


@dp.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in admins:
        await message.answer("❌ *Эта команда только для администратора!*", parse_mode="Markdown")
        return

    try:
        # Формат команды: /ban @username причина
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError

        _, username, reason = parts
        username = username.lstrip('@').lower()

        # Поиск пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return

        if target_user_id in punishments["bans"]:
            await message.answer(f"ℹ️ *Пользователь @{users[target_user_id]['username']} уже забанен.*",
                                 parse_mode="Markdown")
            return

        # Устанавливаем перманентный бан
        punishments["bans"][target_user_id] = {
            "reason": reason,
            "admin": users[message.from_user.id]['username'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "until": None  # Перманентный бан
        }

        # Ограничиваем доступ к группе
        try:
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id
            )
        except Exception as e:
            print(f"Ошибка при бане пользователя: {e}")

        await message.answer(f"⛔ *Пользователь @{users[target_user_id]['username']} забанен!*\n\n"
                             f"📌 *Причина:* {reason}\n"
                             f"👮 *Администратор:* @{users[message.from_user.id]['username']}",
                             parse_mode="Markdown")

    except Exception as e:
        await message.answer("❌ *Неправильный формат команды*\n\n"
                             "🔹 Используйте: /ban @ник причина\n"
                             "🔹 Пример: /ban @user Читы",
                             parse_mode="Markdown")


@dp.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in admins:
        await message.answer("❌ *Эта команда только для администратора!*", parse_mode="Markdown")
        return

    try:
        # Формат команды: /unban @username
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError

        _, username = parts
        username = username.lstrip('@').lower()

        # Поиск пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return

        if target_user_id not in punishments["bans"]:
            await message.answer(f"ℹ️ *Пользователь @{users[target_user_id]['username']} не забанен.*",
                                 parse_mode="Markdown")
            return

        # Снимаем бан
        removed_ban = punishments["bans"].pop(target_user_id)

        # Восстанавливаем доступ к группе
        try:
            await bot.unban_chat_member(
                chat_id=message.chat.id,
                user_id=target_user_id
            )
        except Exception as e:
            print(f"Ошибка при разбане пользователя: {e}")

        await message.answer(f"✅ *Бан снят с @{users[target_user_id]['username']}!*\n\n"
                             f"📌 *Причина бана:* {removed_ban['reason']}\n"
                             f"👮 *Администратор:* @{users[message.from_user.id]['username']}",
                             parse_mode="Markdown")

    except Exception as e:
        await message.answer("❌ *Неправильный формат команды*\n\n"
                             "🔹 Используйте: /unban @ник\n"
                             "🔹 Пример: /unban @user",
                             parse_mode="Markdown")


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================


# В вашем хендлере вызывайте эту функцию вместо одного сообщения с длинным текстом


@dp.message(Command("start"))
async def start_command(message: Message):
    # Проверяем тип чата (чтобы бот работал только в группах)
    if not await check_chat_type(message):
        return

    user_id = message.from_user.id
    user = message.from_user

    # Добавляем/обновляем пользователя в базе
    get_or_create_user(user)

    # Формируем приветственное сообщение
    welcome_text = (
        f"👋 Добро пожаловать в *Outagamie County RolePlay*, {user.full_name}!\n\n"
        "🔹 Вы успешно зарегистрированы в системе.\n"
        "🔹 Для просмотра доступных команд используйте /help\n\n"
        "Приятной игры! 🚔🏙️"
    )

    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message(Command("start"))
async def start(message: Message):
    if not await check_chat_type(message):
        return

    user_id = get_or_create_user(message.from_user)

    def escape_markdown_v2(text):
        special_chars = r"\_*[]()~`>#+-=|{}.!"
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    # Обрабатываем имя пользователя или никнейм
    username_or_fullname = message.from_user.username or message.from_user.full_name
    escaped_username_or_fullname = escape_markdown_v2(username_or_fullname)

    # Формируем приветственный текст
    welcome_text = f"✨ *Добро пожаловать, {escaped_username_or_fullname}!* ✨\n\n"

    # Если пользователь — админ, добавляем раздел с командами администратора
    if message.from_user.id in admins:
        welcome_text += "⚙️ *Команды администратора:*\n"
        admin_commands = [
            # Удалены /setrank, /setname, /setwork, /setage, /setinventory, /setbio, /wanted, /unwanted, /reset, /newevent
            "/addadmin @username", # Не реализована в коде, но была в списке
            "/removeadmin @username", # Не реализована в коде, но была в списке
            "/admins", # Не реализована в коде, но была в списке
            "/warn @user причина",
            "/unwarn @user",
            "/warns @user",
            "/mute @user время причина",
            "/unmute @user",
            "/ban @user причина",
            "/unban @user"
        ]
        for cmd in admin_commands:
            welcome_text += f"{cmd}\n"
        welcome_text += "\n"

    # Общие


# ==================== СПИСОК ЛИДЕРОВ ====================

@dp.message(Command("leaders"))
async def show_leaders(message: Message):
    # Сортируем пользователей по балансу
    sorted_users = sorted(users.items(), key=lambda item: item[1]["balance"], reverse=True)

    if not sorted_users:
        await message.answer("ℹ️ *Нет данных о пользователях*", parse_mode="Markdown")
        return

    # Формируем топ-10
    leaders_text = "🏆 *Топ игроков по балансу:*\n\n"
    for i, (user_id, user_data) in enumerate(sorted_users[:10], start=1):
        leaders_text += f"{i}. @{user_data['username']} - {user_data['balance']}💰\n"

    await message.answer(leaders_text, parse_mode="Markdown")


# ==================== ПОЛУЧЕНИЕ ЗАРПЛАТЫ ====================

@dp.message(Command("getsalary"))
async def get_salary(message: Message):
    user_id = get_or_create_user(message.from_user)
    user = users[user_id]

    # Проверяем, установлен ли ранг
    if not user['rank']:
        await message.answer("❌ *У вас не установлен ранг!*", parse_mode="Markdown")
        return

    # Проверяем, можно ли получить зарплату (раз в 7 дней)
    if user['last_salary']:
        last_salary_date = datetime.strptime(user['last_salary'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_salary_date < timedelta(days=7):
            next_salary = last_salary_date + timedelta(days=7)
            await message.answer(f"⏳ *Вы уже получали зарплату в этом периоде!*\n\n"
                                 f"💰 *Следующая зарплата:* {next_salary.strftime('%Y-%m-%d %H:%M:%S')}",
                                 parse_mode="Markdown")
            return

    # Получаем зарплату по рангу
    salary = RANKS.get(user['rank'], 0)
    user['balance'] += salary
    user['last_salary'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await message.answer(f"💰 *Вы получили зарплату!*\n\n"
                         f"🏅 *Ранг:* {user['rank']}\n"
                         f"💵 *Сумма:* {salary}\n"
                         f"💳 *Новый баланс:* {user['balance']}",
                         parse_mode="Markdown")


@dp.message(Command("profile"))
async def profile(message: Message):
    # Проверяем тип чата
    if not await check_chat_type(message):
        return

    # Проверяем, указан ли username в команде
    args = message.text.split()
    target_username = None

    if len(args) > 1:
        target_username = args[1].lstrip('@').lower()

    if target_username:
        # Ищем пользователя по username
        target_user_id = None
        for uid, data in users.items():
            if target_username == data["username"].lower():
                target_user_id = uid
                break

        if not target_user_id:
            await message.answer("❌ *Пользователь не найден.*", parse_mode="Markdown")
            return
    else:
        target_user_id = get_or_create_user(message.from_user)

    user = users[target_user_id]

    # Определяем место пользователя в списке лидеров
    sorted_users = sorted(users.items(), key=lambda item: item[1]["balance"], reverse=True)

    rank_position = None
    for index, (uid, data) in enumerate(sorted_users, start=1):
        if uid == target_user_id:
            rank_position = index
            break

    profile_text = f"📌 *Профиль @{user['username']}*\n\n"

    if user['age']:
        profile_text += f"🎂 *Возраст:* {user['age']}\n"

    profile_text += f"💰 *Баланс:* {user['balance']}\n"

    if user['work']:
        profile_text += f"💼 *Работа:* {user['work']}\n"

    if user['rank']:
        profile_text += f"🏅 *Ранг:* {user['rank']}\n"

    if user['admin']:
        profile_text += "👑 *Статус:* Администратор\n"

    if user['wanted']:
        profile_text += "🔴 *Статус:* В розыске!\n"

    if rank_position:
        profile_text += f"🏆 *Место в топе:* #{rank_position}\n"

    await message.answer(profile_text, parse_mode="Markdown")


@dp.message(Command("pay"))
async def pay_money(message: Message):
    try:
        # Формат команды: /pay @username сумма
        parts = message.text.split()
        if len(parts) < 3:
            raise ValueError

        _, username, amount_str = parts
        username = username.lstrip('@').lower()

        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Сумма должна быть положительным числом")
            return

        sender_id = get_or_create_user(message.from_user)

        # Поиск получателя по username
        receiver_id = None
        for uid, data in users.items():
            if username == data["username"].lower():
                receiver_id = uid
                break

        if not receiver_id:
            await message.answer("❌ Пользователь не найден.")
            return

        if sender_id == receiver_id:
            await message.answer("❌ Нельзя перевести деньги самому себе")
            return

        if users[sender_id]['balance'] < amount:
            await message.answer("❌ Недостаточно средств на балансе")
            return

        # Совершаем перевод
        users[sender_id]['balance'] -= amount
        users[receiver_id]['balance'] += amount

        await message.answer(f"✅ Вы перевели {amount}💰 пользователю @{users[receiver_id]['username']}\n"
                             f"Ваш новый баланс: {users[sender_id]['balance']}💰")

    except Exception as e:
        await message.answer("❌ Неправильный формат команды\n\n"
                             f"Используйте: /pay @username Сумма\n"
                             f"Пример: /pay @user 1000")


@dp.message(Command("help"))
async def show_help(message: Message):
    help_text = "🆘 *Помощь по командам*\n\n"

    user_id = get_or_create_user(message.from_user)
    is_admin = users[user_id].get('admin', False) or message.from_user.id == ADMIN_IDS

    # Секция администратора: удалены все команды, кроме тех, что относятся к системе наказаний,
    # которые изначально не были перечислены в /help, но остаются в коде.
    # Чтобы не показывать пустую секцию, выведем только те, что остались в коде:
    if is_admin:
        help_text += "⚙️ *Команды администратора (Наказания):*\n"
        help_text += "🔹 /warn @ник причина - выдать предупреждение\n"
        help_text += "🔹 /mute @ник время причина - дать мут\n"
        help_text += "🔹 /unmute @ник - снять мут\n"
        help_text += "🔹 /ban @ник причина - забанить\n"
        help_text += "🔹 /unban @ник - разбанить\n\n"

    help_text += "👥 *Общие команды:*\n"
    help_text += "🔹 /profile [@ник] - посмотреть профиль\n"
    help_text += "🔹 /leaders - топ игроков\n"
    help_text += "🔹 /getsalary - получить зарплату\n"
    help_text += "🔹 /pay @ник сумма - перевести деньги\n"
    # Удалены /payamount, /inventory, /bio, /joinevent

    help_text += "\n📌 Для уточнения по командам обращайтесь к администрации."

    await message.answer(help_text, parse_mode="Markdown")


@dp.message()
async def handle_unknown_command(message: Message):
    if message.text.startswith('/'):
        # Получаем команду (первое слово после /)
        command = message.text.split()[0][1:].lower()

        # Список всех доступных команд (обновлен)
        available_commands = [
            'start', 'help', 'profile', 'leaders', 'getsalary',
            'pay', 'warn', 'mute', 'unmute', 'ban', 'unban'
        ]

        # Ищем похожие команды
        similar = [cmd for cmd in available_commands if cmd.startswith(command[:3])]

        if similar:
            suggestions = "\n".join([f"🔹 /{cmd}" for cmd in similar[:3]])
            reply = f"❌ *Неизвестная команда /{command}*\n\n" \
                    f"Возможно, вы имели в виду:\n{suggestions}\n\n" \
                    f"Введите /help для просмотра всех команд."
        else:
            reply = f"❌ *Неизвестная команда /{command}*\n\n" \
                    "Введите /help для просмотра всех доступных команд."

        await message.answer(reply, parse_mode="Markdown")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
