import asyncio
import logging
import os
import sys
import io
import aiohttp
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ======================
# НАСТРОЙКА
# ======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("=" * 60)
    logger.error("❌ ОТСУТСТВУЕТ ОБЯЗАТЕЛЬНАЯ ПЕРЕМЕННАЯ BOT_TOKEN")
    logger.error("📌 Добавьте BOT_TOKEN в Railway Variables")
    logger.error("=" * 60)
    sys.exit(1)

logger.info("✅ BOT_TOKEN загружен успешно")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_style = {}

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
# ФУНКЦИЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ
# ======================

async def generate_logo_image(prompt: str, style: str) -> bytes:
    """Генерация логотипа через бесплатный API"""
    
    full_prompt = (
        f"Professional {style} style logo design: {prompt}. "
        f"Clean vector graphics, high quality, suitable for branding, "
        f"white background, no text."
    )
    encoded_prompt = urllib.parse.quote(full_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Ошибка {response.status}")

# ======================
# ПРОСТОЙ БЕСПЛАТНЫЙ ЧАТ
# ======================

async def simple_chat(message_text: str) -> str:
    """Простой чат-бот без API ключей"""
    
    text_lower = message_text.lower()
    
    if any(w in text_lower for w in ["привет", "здравствуй", "hi"]):
        return "👋 Привет! Я бот для создания логотипов. Нажми 'Создать логотип' и опиши идею!"
    elif any(w in text_lower for w in ["как дела", "как ты"]):
        return "У меня всё отлично! Готов создавать логотипы. А у тебя как?"
    elif any(w in text_lower for w in ["спасибо", "thanks"]):
        return "Пожалуйста! Рад помочь 😊"
    elif any(w in text_lower for w in ["логотип", "создай"]):
        return "Чтобы создать логотип: выбери стиль → нажми 'Создать логотип' → подробно опиши идею (цвета, объекты, сферу)."
    else:
        return f"Я понял: «{message_text[:100]}»\n\nЧтобы создать логотип: выбери стиль через кнопку 'Выбрать стиль', затем нажми 'Создать логотип' и опиши идею."

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot</b>\n\n"
        "Я создаю профессиональные логотипы БЕСПЛАТНО!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Нейросеть Flux\n"
        "• 6 стилей на выбор\n"
        "• Абсолютно бесплатно\n"
        "• Без рекламы и подписок\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выбери стиль\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Опиши идею подробно\n\n"
        "💡 <b>Пример:</b> логотип для кофейни с чашкой кофе",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Инструкция</b>\n\n"
        "• <b>Создать логотип</b> — генерация логотипа\n"
        "• <b>Выбрать стиль</b> — установите стиль\n"
        "• <b>Чат с AI</b> — просто поболтать\n\n"
        "<b>Стили:</b>\n"
        "Minimalism, Abstract, Vintage, Cyberpunk, Eco, Luxury\n\n"
        "💡 <b>Совет:</b> Чем подробнее описание, тем лучше результат!",
        parse_mode="HTML"
    )

@dp.message(F.text == "💬 Чат с AI")
async def chat_mode(message: Message):
    await message.answer(
        "💬 <b>Режим чата</b>\n\n"
        "Просто напиши сообщение, и я отвечу.\n\n"
        "Чтобы вернуться к логотипам — нажми '🎨 Создать логотип'",
        parse_mode="HTML"
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current = user_style.get(message.from_user.id)
    text = f"\n\nТекущий стиль: <b>{current}</b>" if current else ""
    await message.answer(f"🎭 <b>Выберите стиль:</b>{text}", reply_markup=style_kb, parse_mode="HTML")

@dp.message(F.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранён!\n\nТеперь нажми 'Создать логотип' и опиши идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )

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
        f"<b>Пример:</b> логотип для кофейни, чашка кофе и медведь, коричневые тона",
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
    
    logo_keywords = ["логотип", "бренд", "компания", "магазин", "кофейня", "спорт"]
    is_logo = any(kw in message.text.lower() for kw in logo_keywords) and len(message.text.split()) > 3
    
    if is_logo:
        await generate_logo(message, style)
    else:
        reply = await simple_chat(message.text)
        await message.answer(reply, parse_mode="HTML")

async def generate_logo(message: Message, style: str):
    status = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}\n\n"
        f"⏱ Подождите 5-10 секунд",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo_image(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status.delete()
        await message.answer_photo(
            photo=photo,
            caption=f"✨ <b>Логотип готов!</b>\n\n📝 {message.text[:150]}\n🎭 Стиль: {style}",
            parse_mode="HTML"
        )
        logger.info(f"✅ Logo for {message.from_user.id}")
        
    except Exception as e:
        await status.delete()
        await message.answer(
            f"❌ <b>Ошибка</b>\n\n{str(e)[:150]}\n\nПопробуйте другое описание.",
            parse_mode="HTML"
        )
        logger.error(f"Error: {e}")

# ======================
# ЗАПУСК (с защитой от конфликтов)
# ======================

async def main():
    print("\n" + "=" * 50)
    print("🤖 LOGO BOT (Бесплатный)")
    print("=" * 50)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}...")
    print("🚀 Бот запущен! Без рекламы, без ключей.")
    print("=" * 50 + "\n")
    
    try:
        # Очищаем вебхук и сбрасываем все ожидающие обновления
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Дополнительная очистка: пропускаем все старые обновления
        updates = await bot.get_updates(offset=-1, timeout=1)
        if updates:
            last_id = updates[-1].update_id
            await bot.get_updates(offset=last_id + 1)
            logger.info(f"Dropped {len(updates)} pending updates")
        
        logger.info("Webhook cleared, starting polling...")
        await dp.start_polling(bot, handle_signals=True)
        
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
