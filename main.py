import asyncio
import logging
import os
import sys
import io
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
    logger.error("   Добавьте переменную BOT_TOKEN в Railway Variables")
    sys.exit(1)

# Очищаем токен от возможных пробелов и переносов строк
BOT_TOKEN = BOT_TOKEN.strip()
logger.info(f"📌 Токен (первые 10 символов): {BOT_TOKEN[:10]}...")

# Базовая проверка формата
if not BOT_TOKEN.startswith(('8675822721:', '5', '6', '7', '8', '9')):
    logger.error("❌ Токен выглядит подозрительно!")
    logger.error("   Убедитесь, что скопировали токен полностью из @BotFather")
    logger.error(f"   Получено: {BOT_TOKEN[:20]}...")
    sys.exit(1)

# Инициализация бота
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    user_style = {}
    logger.info("✅ Бот инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    sys.exit(1)

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Создать логотип")],
        [KeyboardButton(text="🎭 Выбрать стиль")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Abstract")],
        [KeyboardButton(text="Vintage"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Eco"), KeyboardButton(text="Luxury")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Генерация логотипа
async def generate_logo(prompt: str, style: str) -> bytes:
    full_prompt = f"Professional {style} style logo: {prompt}. Clean vector, white background, no text"
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Ошибка {response.status}")

# Обработчики
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Создаю профессиональные логотипы бесплатно!\n\n"
        "📖 <b>Как использовать:</b>\n"
        "1️⃣ Выберите стиль (кнопка 'Выбрать стиль')\n"
        "2️⃣ Нажмите 'Создать логотип'\n"
        "3️⃣ Опишите вашу идею\n\n"
        "💡 <b>Пример:</b>\n"
        "логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started bot")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "🎭 <b>Доступные стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "💡 Чем подробнее описание — тем лучше результат!",
        parse_mode="HTML"
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current = user_style.get(message.from_user.id)
    text = f"\n\n✅ Текущий стиль: <b>{current}</b>" if current else ""
    await message.answer(f"🎭 <b>Выберите стиль:</b>{text}", reply_markup=style_kb, parse_mode="HTML")

@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ <b>Стиль «{message.text}» сохранён!</b>\n\n"
        f"🎨 Теперь нажмите «Создать логотип» и опишите вашу идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Создание логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 <b>Опишите вашу идею:</b>\n"
        f"• Что должно быть изображено?\n"
        f"• Какие цвета использовать?\n"
        f"• Для какой сферы логотип?\n\n"
        f"⏱ Генерация займёт 10-20 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"логотип для IT-компании, облако и шестерёнка, синие тона",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    # Пропускаем кнопки
    if message.text in ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
                        "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]:
        return
    
    # Проверка длины
    if len(message.text.split()) < 3:
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Пожалуйста, напишите более подробно (минимум 3 слова).\n\n"
            "✅ <b>Пример:</b> «логотип для кофейни с чашкой кофе»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 {message.text[:80]}\n\n"
        f"⏱ Подождите 10-20 секунд...",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=f"✨ <b>Логотип готов!</b>\n\n📝 {message.text[:150]}\n🎭 Стиль: {style}",
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Логотип создан для {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            f"❌ <b>Не удалось создать логотип</b>\n\n"
            f"🔍 {str(e)[:150]}\n\n"
            f"💡 Попробуйте другое описание или подождите минуту.",
            parse_mode="HTML"
        )
        logger.error(f"Ошибка: {e}")

# Запуск
async def main():
    print("\n" + "=" * 60)
    print("🎨 AI LOGO BOT v4.0")
    print("=" * 60)
    
    try:
        # Проверяем токен через API Telegram
        me = await bot.get_me()
        print(f"✅ Бот успешно подключен: @{me.username}")
        print(f"📌 Bot ID: {me.id}")
        print("=" * 60)
        print("🚀 Запуск бота...")
        print("=" * 60 + "\n")
        
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram: {e}")
        logger.error("   Проверьте правильность BOT_TOKEN в Railway Variables")
        logger.error("   Токен должен быть скопирован точно из @BotFather")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        sys.exit(1)
