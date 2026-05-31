import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# ======================
# ENV ПЕРЕМЕННЫЕ (Render / Railway)
# ======================

# ✅ ПРАВИЛЬНОЕ получение переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ⚠️ Проверка наличия переменных
if not TOKEN:
    print("❌ BOT_TOKEN не найден в переменных окружения")
    print("Добавьте переменную BOT_TOKEN в настройках Railway/Render")
    exit(1)

if not OPENAI_KEY:
    print("❌ OPENAI_API_KEY не найден в переменных окружения")
    print("Добавьте переменную OPENAI_API_KEY в настройках Railway/Render")
    exit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_KEY)

# Хранилище стилей пользователей
user_style = {}

# ======================
# КЛАВИАТУРЫ
# ======================
# Главная клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✨ Generate Logo")],
        [KeyboardButton(text="🎨 Set Style")]
    ],
    resize_keyboard=True
)

# Клавиатура стилей
style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Abstract")],
        [KeyboardButton(text="Vintage"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Eco"), KeyboardButton(text="Luxury")],
        [KeyboardButton(text="🔙 Back to menu")]
    ],
    resize_keyboard=True
)

# ======================
# КОМАНДЫ
# ======================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 AI Logo Bot Pro\n\n"
        "Я создаю логотипы на основе твоих идей!\n\n"
        "✨ Generate Logo - создать логотип\n"
        "🎨 Set Style - выбрать стиль\n\n"
        "Просто опиши идею логотипа!",
        reply_markup=main_kb
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📖 Как пользоваться:\n\n"
        "1️⃣ Нажми 'Set Style' и выбери стиль\n"
        "2️⃣ Нажми 'Generate Logo'\n"
        "3️⃣ Опиши идею логотипа\n\n"
        "🎨 Доступные стили:\n"
        "• Minimalism - минимализм\n"
        "• Abstract - абстракция\n"
        "• Vintage - винтажный\n"
        "• Cyberpunk - киберпанк\n"
        "• Eco - эко стиль\n"
        "• Luxury - люксовый"
    )

# ======================
# ВЫБОР СТИЛЯ
# ======================
@dp.message(F.text == "🎨 Set Style")
async def set_style(message: Message):
    await message.answer(
        "Выбери стиль для логотипа:",
        reply_markup=style_kb
    )

@dp.message(F.text == "🔙 Back to menu")
async def back_to_menu(message: Message):
    await message.answer(
        "Главное меню",
        reply_markup=main_kb
    )

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ Стиль сохранён: {message.text}\n\nТеперь используй '✨ Generate Logo'",
        reply_markup=main_kb
    )

# ======================
# ГЕНЕРАЦИЯ ЛОГОТИПА
# ======================
@dp.message(F.text == "✨ Generate Logo")
async def ask_idea(message: Message):
    await message.answer(
        "💡 Напиши идею для логотипа\n\n"
        "Примеры:\n"
        "- Кофейня с медведем\n"
        "- IT компания с облаком\n"
        "- Цветочный магазин с розой"
    )

@dp.message(F.text)
async def generate_logo(message: Message):
    # Проверяем, не команда ли это
    if message.text.startswith('/'):
        return
    
    # Получаем стиль пользователя
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Формируем промпт для генерации
    prompt = (
        f"Create a professional logo design. "
        f"Style: {style}. "
        f"Concept: {message.text}. "
        f"The logo should be clean, vector-style, "
        f"suitable for branding, high quality, 8k resolution."
    )
    
    # Отправляем сообщение о начале генерации
    status_msg = await message.answer("🎨 Генерация логотипа... ⏳")
    
    try:
        # Генерация изображения через OpenAI DALL-E
        result = client.images.generate(
            model="dall-e-3",  # Используем DALL-E 3 (более доступный)
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        # Получаем URL изображения
        image_url = result.data[0].url
        
        # Удаляем сообщение о статусе
        await status_msg.delete()
        
        # Отправляем результат
        await message.answer_photo(
            photo=image_url,
            caption=f"🎨 Логотип готов!\n\n"
                   f"💡 Идея: {message.text}\n"
                   f"🎭 Стиль: {style}\n\n"
                   f"✨ Чтобы создать ещё один - нажми '✨ Generate Logo'"
        )
        
    except Exception as e:
        await status_msg.delete()
        error_message = str(e)
        
        # Улучшенная обработка ошибок
        if "billing" in error_message.lower():
            await message.answer(
                "❌ Ошибка биллинга OpenAI\n\n"
                "Проверьте баланс аккаунта в OpenAI Console"
            )
        elif "safety" in error_message.lower():
            await message.answer(
                "❌ Контент не соответствует политике безопасности\n\n"
                "Пожалуйста, измените описание идеи"
            )
        else:
            await message.answer(
                f"❌ Ошибка генерации\n\n"
                f"Пожалуйста, попробуйте ещё раз\n"
                f"или измените описание идеи\n\n"
                f"Детали: {error_message[:200]}"
            )
        
        print(f"ERROR for user {message.from_user.id}: {error_message}")

# ======================
# ЗАПУСК БОТА
# ======================
async def main():
    print("=" * 50)
    print("🤖 AI Logo Bot запускается...")
    print(f"📌 Bot token: {TOKEN[:10]}...")
    print(f"🔑 OpenAI key: {OPENAI_KEY[:10]}...")
    print("=" * 50)
    
    try:
        # Удаляем вебхуки (важно для Railway/Render)
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Вебхук удалён")
        
        # Запускаем поллинг
        print("🚀 Бот готов к работе!")
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
