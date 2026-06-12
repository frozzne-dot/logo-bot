import asyncio
import logging
import os
import sys
import io
import aiohttp
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
    logger.error("❌ BOT_TOKEN не найден!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN загружен")

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
# ГЕНЕРАЦИЯ ЧЕРЕЗ PRODIA (БЕСПЛАТНО, СТАБИЛЬНО)
# ======================

async def generate_logo_prodia(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Prodia API (бесплатно!)"""
    
    full_prompt = f"Professional {style} style logo design: {prompt}. Clean vector graphics, high quality, suitable for branding, white background, no text."
    
    # Prodia использует Stability AI модели
    # Модель sd-3.5 даёт отличные результаты для логотипов
    api_url = "https://api.prodia.com/v1/sd/generate"
    
    headers = {
        "Content-Type": "application/json",
        "X-Prodia-Key": "free"  # Бесплатный доступ
    }
    
    payload = {
        "model": "sd-3.5-large.safetensors",
        "prompt": full_prompt,
        "negative_prompt": "text, letters, words, watermark, low quality, blurry, ugly",
        "steps": 30,
        "cfg_scale": 7,
        "width": 1024,
        "height": 1024,
        "sampler": "euler_a"
    }
    
    async with aiohttp.ClientSession() as session:
        # Запускаем генерацию
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Prodia error {response.status}: {error_text}")
            
            job_data = await response.json()
            job_id = job_data.get("job")
            
            if not job_id:
                raise Exception("No job ID returned")
        
        # Ждём результат с ретраями
        for attempt in range(30):
            await asyncio.sleep(1.5)
            
            async with session.get(f"https://api.prodia.com/v1/job/{job_id}") as status_response:
                if status_response.status == 200:
                    status_data = await status_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        image_url = status_data.get("imageUrl")
                        if image_url:
                            # Скачиваем изображение
                            async with session.get(image_url) as img_response:
                                if img_response.status == 200:
                                    return await img_response.read()
                                else:
                                    raise Exception("Failed to download generated image")
                    elif status == "failed":
                        raise Exception("Generation failed")
                    # status == "processing" - продолжаем ждать
        
        raise Exception("Timeout waiting for image generation")

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot</b>\n\n"
        "Создаю профессиональные логотипы через нейросеть Stable Diffusion 3.5!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Бесплатная генерация\n"
        "• 6 стилей на выбор\n"
        "• Высокое качество 1024×1024\n"
        "• Без рекламы и подписок\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выбери стиль через кнопку 'Выбрать стиль'\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Подробно опиши идею\n\n"
        "💡 <b>Пример:</b> логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Инструкция</b>\n\n"
        "• <b>Выбрать стиль</b> — установи стиль логотипа\n"
        "• <b>Создать логотип</b> — начни генерацию\n\n"
        "<b>Доступные стили:</b>\n"
        "• Minimalism — минимализм (чистые линии)\n"
        "• Abstract — абстракция (креативные формы)\n"
        "• Vintage — винтажный (ретро-элементы)\n"
        "• Cyberpunk — киберпанк (неон, футуризм)\n"
        "• Eco — эко-стиль (природа, зелёные тона)\n"
        "• Luxury — люксовый (золото, элегантность)\n\n"
        "<b>Совет:</b> Чем подробнее описание — тем лучше результат!\n"
        "Указывай объекты, цвета и сферу применения.",
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
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Опишите идею логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 Напишите подробно:\n"
        f"• Что изобразить? (объекты, символы)\n"
        f"• Какие цвета использовать?\n"
        f"• Для какой сферы логотип?\n\n"
        f"⏱ Генерация: 10-30 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"логотип для кофейни, чашка кофе и силуэт медведя, коричневые и бежевые тона",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith('/'):
        return
    
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
               "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]
    if message.text in buttons:
        return
    
    # Проверка длины описания
    if len(message.text.split()) < 3:
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Напишите подробнее (минимум 3 слова).\n\n"
            "✅ Хороший пример:\n"
            "«логотип для кофейни с чашкой кофе и медведем»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}{'...' if len(message.text) > 80 else ''}\n\n"
        f"🔄 Используется Stable Diffusion 3.5\n"
        f"⏱ Процесс занимает 10-30 секунд, пожалуйста, подождите...",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo_prodia(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"📝 <b>Описание:</b> {message.text[:150]}\n"
                f"🎭 <b>Стиль:</b> {style}\n\n"
                f"🔄 Чтобы создать ещё — нажми 'Создать логотип'\n"
                f"🎨 Сменить стиль — 'Выбрать стиль'"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Logo generated for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_str = str(e)
        
        if "403" in error_str or "unauthorized" in error_str.lower():
            await message.answer(
                "⚠️ <b>Лимит генераций временно исчерпан</b>\n\n"
                "Пожалуйста, подождите 1-2 минуты и попробуйте снова.\n"
                "Бесплатный тариф Prodia имеет небольшие ограничения.\n\n"
                "Совет: сделайте паузу между запросами.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка генерации</b>\n\n"
                f"<code>{error_str[:150]}</code>\n\n"
                f"💡 <b>Советы:</b>\n"
                f"• Сделайте описание более конкретным\n"
                f"• Попробуйте другой стиль\n"
                f"• Используйте 5-15 слов\n\n"
                f"Попробуйте снова через минуту.",
                parse_mode="HTML"
            )
        
        logger.error(f"❌ Generation error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🤖 AI LOGO BOT (Prodia API)")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:15]}... OK")
    print("=" * 60)
    print("🚀 Бот запускается...")
    print("🎨 Модель: Stable Diffusion 3.5")
    print("💰 Бесплатно! (Prodia API)")
    print("=" * 60 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared")
        logger.info("Bot is ready! Starting polling...")
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
