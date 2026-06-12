import asyncio
import logging
import os
import sys
import io
import aiohttp
import urllib.parse
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# ======================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================
# ЧТЕНИЕ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Проверка наличия переменных
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not DEEPSEEK_API_KEY:
    missing_vars.append("DEEPSEEK_API_KEY")

if missing_vars:
    logger.error("=" * 60)
    logger.error("❌ ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for var in missing_vars:
        logger.error(f"   • {var}")
    logger.error("")
    logger.error("📌 КАК ПОЛУЧИТЬ DEEPSEEK API КЛЮЧ:")
    logger.error("   1. Перейдите на https://platform.deepseek.com/")
    logger.error("   2. Зарегистрируйтесь (дадут 4 млн токенов бесплатно)")
    logger.error("   3. В разделе 'API Keys' создайте новый ключ")
    logger.error("   4. Скопируйте ключ (начинается с 'sk-...')")
    logger.error("")
    logger.error("📌 КАК ДОБАВИТЬ НА RAILWAY:")
    logger.error("   → Проект → сервис → Variables → Добавить:")
    logger.error("     • Key: BOT_TOKEN → Value: ваш токен")
    logger.error("     • Key: DEEPSEEK_API_KEY → Value: ваш DeepSeek ключ")
    logger.error("=" * 60)
    sys.exit(1)

logger.info("✅ Переменные окружения загружены успешно")
logger.info(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
logger.info(f"   DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:15]}...")

# ======================
# ИНИЦИАЛИЗАЦИЯ DEEPSEEK
# ======================

try:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    logger.info("✅ DeepSeek API initialized successfully")
    logger.info("   Модель: deepseek-v4-flash")
    logger.info("   Лимит: 4M токенов бесплатно")
    
except Exception as e:
    logger.error(f"❌ Ошибка инициализации DeepSeek API: {e}")
    sys.exit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище стилей пользователей
user_style = {}
user_history = {}

# ======================
# КЛАВИАТУРЫ
# ======================

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Создать логотип")],
        [KeyboardButton(text="🎭 Выбрать стиль")],
        [KeyboardButton(text="💬 Чат с AI")],
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

# ======================
# ФУНКЦИИ
# ======================

async def chat_with_deepseek(user_id: int, message: str) -> str:
    """Общение с DeepSeek с контекстом"""
    
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append({"role": "user", "content": message})
    
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=user_history[user_id],
                max_tokens=500,
                temperature=0.7,
                stream=False
            )
        )
        
        reply = response.choices[0].message.content
        user_history[user_id].append({"role": "assistant", "content": reply})
        
        return reply
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "Извините, произошла ошибка. Попробуйте позже."

async def generate_logo_image(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Pollinations.ai"""
    
    full_prompt = f"Professional {style} style logo design: {prompt}. Clean vector graphics, high quality, suitable for branding, white background, no text."
    encoded_prompt = urllib.parse.quote(full_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Image generation failed: {response.status}")

# ======================
# НИКАКИХ ПРОВЕРОК ПОДПИСКИ! БОТ РАБОТАЕТ СРАЗУ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot (DeepSeek)</b>\n\n"
        "Я использую мощь DeepSeek AI для создания логотипов и общения!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Нейросеть DeepSeek-V4\n"
        "• 4 млн токенов бесплатно\n"
        "• Генерация логотипов (6 стилей)\n"
        "• Интеллектуальный чат с AI\n"
        "• Высокая скорость ответа\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выберите стиль логотипа\n"
        "2. Нажмите 'Создать логотип' и опишите идею\n"
        "3. Или просто общайтесь в режиме чата\n\n"
        "💡 <b>Пример:</b> логотип для кофейни с чашкой кофе",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started the bot")

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    help_text = (
        "📖 <b>Инструкция</b>\n\n"
        "• <b>Создать логотип</b> — генерация логотипа\n"
        "• <b>Выбрать стиль</b> — установите стиль\n"
        "• <b>Чат с AI</b> — переключиться в режим диалога\n\n"
        "<b>Стили:</b>\n"
        "Minimalism, Abstract, Vintage, Cyberpunk, Eco, Luxury\n\n"
        "<b>💬 Режим чата:</b>\n"
        "Просто отправьте любое сообщение — бот ответит.\n\n"
        "<b>💰 Бесплатно:</b>\n"
        "4 млн токенов DeepSeek при регистрации"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "💬 Чат с AI")
async def chat_mode(message: Message):
    await message.answer(
        "💬 <b>Режим чата активирован</b>\n\n"
        "Просто пишите мне сообщения, и я буду отвечать.\n\n"
        "Чтобы вернуться к логотипам — нажмите '🎨 Создать логотип'",
        parse_mode="HTML",
        reply_markup=main_kb
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current_style = user_style.get(message.from_user.id)
    current_text = f"\n\nТекущий стиль: <b>{current_style}</b>" if current_style else ""
    
    await message.answer(
        f"🎭 <b>Выберите стиль:</b>{current_text}",
        reply_markup=style_kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n\n"
        f"Теперь нажмите 'Создать логотип' и опишите идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    
    await message.answer(
        f"🎨 <b>Опишите идею логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 Напишите подробно:\n"
        f"• Что изобразить?\n"
        f"• Какие цвета?\n"
        f"• Для какой сферы?\n\n"
        f"⏱ Генерация: 5-10 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"логотип для IT-компании, облако и шестеренка, синие тона",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith('/'):
        return
    
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", 
               "🔙 Назад", "Minimalism", "Abstract", "Vintage", 
               "Cyberpunk", "Eco", "Luxury", "💬 Чат с AI"]
    if message.text in buttons:
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Проверка на запрос логотипа
    logo_keywords = ["логотип", "бренд", "компания", "магазин", "кофейня", "it", "спорт"]
    is_logo_request = any(keyword in message.text.lower() for keyword in logo_keywords) and len(message.text.split()) > 3
    
    if is_logo_request:
        await generate_logo(message, style)
    else:
        await chat_response(message)

async def generate_logo(message: Message, style: str):
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}\n\n"
        f"⏱ Пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        image_bytes = await generate_logo_image(message.text, style)
        photo = io.BytesIO(image_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"📝 {message.text[:150]}\n"
                f"🎭 Стиль: {style}\n\n"
                f"🔄 Нажмите 'Создать логотип' для новой генерации"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Logo generated for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            f"❌ <b>Ошибка</b>\n\n"
            f"<code>{str(e)[:150]}</code>\n\n"
            f"Попробуйте другое описание.",
            parse_mode="HTML"
        )
        logger.error(f"Generation error: {e}")

async def chat_response(message: Message):
    status_msg = await message.answer("🤔 Думаю...")
    
    try:
        response = await chat_with_deepseek(message.from_user.id, message.text)
        
        await status_msg.delete()
        
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await message.answer(response[i:i+4000], parse_mode="HTML")
        else:
            await message.answer(response, parse_mode="HTML")
            
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            "❌ Ошибка. Попробуйте позже.",
            parse_mode="HTML"
        )
        logger.error(f"Chat error: {e}")

# ======================
# ЗАПУСК
# ======================

async def main():
    print("\n" + "=" * 50)
    print("🤖 AI LOGO BOT (DeepSeek)")
    print("=" * 50)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"🔑 DeepSeek: {DEEPSEEK_API_KEY[:10]}...")
    print("=" * 50)
    print("🚀 Бот запущен! Нет рекламы, нет проверок.")
    print("=" * 50 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
