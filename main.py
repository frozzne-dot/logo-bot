import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# ВАШИ КЛЮЧИ - ВСТАВЬТЕ СВОИ ЗНАЧЕНИЯ
# ======================

BOT_TOKEN = "8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY"
OPENAI_API_KEY = "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"

# Проверка наличия ключей
if not BOT_TOKEN:
    logger.error("❌ Укажите правильный BOT_TOKEN")
    exit(1)

if not OPENAI_API_KEY:
    logger.error("❌ Укажите правильный OPENAI_API_KEY")
    exit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация OpenAI
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("✅ OpenAI client initialized")
except Exception as e:
    logger.error(f"❌ OpenAI init error: {e}")
    exit(1)

# Хранилище стилей пользователей
user_style = {}

# ======================
# КЛАВИАТУРЫ
# ======================

# Главная клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Создать логотип")],
        [KeyboardButton(text="🎭 Выбрать стиль")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

# Клавиатура стилей
style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Abstract")],
        [KeyboardButton(text="Vintage"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Eco"), KeyboardButton(text="Luxury")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Я создаю логотипы с помощью ИИ!\n\n"
        "Как пользоваться:\n"
        "1. Выбери стиль (или оставь Minimalism)\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Опиши идею\n\n"
        "Пример: 'логотип для кофейни с чашкой кофе'",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    
    logger.info(f"User {message.from_user.id} started the bot")

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    help_text = (
        "📖 <b>Инструкция</b>\n\n"
        "1. <b>Выбрать стиль</b> - установите стиль логотипа\n"
        "2. <b>Создать логотип</b> - начните создание\n"
        "3. Опишите вашу идею текстом\n\n"
        "<b>Доступные стили:</b>\n"
        "• Minimalism - минимализм\n"
        "• Abstract - абстракция\n"
        "• Vintage - винтажный\n"
        "• Cyberpunk - киберпанк\n"
        "• Eco - эко стиль\n"
        "• Luxury - люксовый\n\n"
        "<b>Примеры идей:</b>\n"
        "- Логотип IT компании с облаком\n"
        "- Цветочный магазин с розой\n"
        "- Спортивный бренд с горой"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    await message.answer(
        "🎭 <b>Выберите стиль логотипа:</b>",
        reply_markup=style_kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    await message.answer(
        "Главное меню",
        reply_markup=main_kb
    )

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n\n"
        f"Теперь нажмите '🎨 Создать логотип' и опишите идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    await message.answer(
        "💡 <b>Опишите идею для логотипа</b>\n\n"
        "Напишите подробное описание того, что вы хотите увидеть.\n\n"
        "<b>Хороший пример:</b>\n"
        "Логотип для кофейни Медведь. Кофейная чашка с медведем, "
        "в стиле минимализм, коричневые и бежевые тона\n\n"
        "<b>Плохой пример:</b>\n"
        "Сделай красивый логотип",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def generate_logo(message: Message):
    # Проверяем, не является ли текст командой или кнопкой
    if message.text.startswith('/'):
        return
    
    if message.text in ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад"]:
        return
    
    if message.text in ["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]:
        return
    
    # Получаем стиль пользователя (по умолчанию Minimalism)
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Формируем промпт
    prompt = f"Create a professional {style} style logo: {message.text}. Clean vector design, high quality, suitable for branding."
    
    # Отправляем статус
    status_msg = await message.answer("🎨 Генерация логотипа... ⏳\nЭто может занять 10-20 секунд.")
    
    try:
        # Генерация через OpenAI
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        
        # Удаляем статус
        await status_msg.delete()
        
        # Отправляем результат
        await message.answer_photo(
            photo=image_url,
            caption=(
                f"🎨 <b>Логотип готов!</b>\n\n"
                f"💡 Идея: {message.text}\n"
                f"🎭 Стиль: {style}\n\n"
                f"✨ Чтобы создать еще один - снова нажмите 'Создать логотип'"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"Generated logo for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_text = str(e)
        
        if "billing" in error_text.lower():
            await message.answer(
                "❌ Ошибка: Проблема с биллингом OpenAI\n\n"
                "Пожалуйста, проверьте баланс аккаунта OpenAI."
            )
        elif "safety" in error_text.lower():
            await message.answer(
                "❌ Ваше описание не соответствует политике безопасности.\n\n"
                "Пожалуйста, измените описание и попробуйте снова."
            )
        else:
            await message.answer(
                f"❌ Ошибка генерации:\n\n{error_text[:200]}\n\n"
                f"Попробуйте изменить описание или выберите другой стиль."
            )
        
        logger.error(f"Generation error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    print("=" * 50)
    print("🤖 AI Logo Bot запускается...")
    print(f"📌 Bot token: {BOT_TOKEN[:15]}...")
    print(f"🔑 OpenAI key: {OPENAI_API_KEY[:15]}...")
    print("=" * 50)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Вебхук удален")
        print("🚀 Бот готов к работе!")
        print("\n💡 Откройте Telegram и найдите своего бота")
        print("📝 Отправьте команду /start для начала работы\n")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Фатальная ошибка: {e}")
