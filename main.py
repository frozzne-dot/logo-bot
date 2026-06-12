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
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Проверка наличия переменных
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not DEEPSEEK_API_KEY:
    missing_vars.append("DEEPSEEK_API_KEY")
if not HUGGINGFACE_TOKEN:
    missing_vars.append("HUGGINGFACE_TOKEN")

if missing_vars:
    logger.error("=" * 60)
    logger.error("❌ ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for var in missing_vars:
        logger.error(f"   • {var}")
    logger.error("")
    logger.error("📌 КАК ПОЛУЧИТЬ HUGGING FACE ТОКЕН:")
    logger.error("   1. Перейдите на https://huggingface.co/join")
    logger.error("   2. Зарегистрируйтесь")
    logger.error("   3. Settings → Access Tokens → New token (роль 'read')")
    logger.error("   4. Скопируйте токен")
    logger.error("")
    logger.error("📌 КАК ПОЛУЧИТЬ DEEPSEEK API КЛЮЧ:")
    logger.error("   1. Перейдите на https://platform.deepseek.com/")
    logger.error("   2. Зарегистрируйтесь (дадут 4 млн токенов бесплатно)")
    logger.error("   3. API Keys → Create new API key")
    logger.error("=" * 60)
    sys.exit(1)

logger.info("✅ Переменные окружения загружены успешно")
logger.info(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
logger.info(f"   DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:15]}...")
logger.info(f"   HUGGINGFACE_TOKEN: {HUGGINGFACE_TOKEN[:15]}...")

# ======================
# ИНИЦИАЛИЗАЦИЯ DEEPSEEK
# ======================

try:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    
    logger.info("✅ DeepSeek API initialized successfully")
    logger.info("   Модель: deepseek-chat")
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
# ФУНКЦИЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЙ (Hugging Face)
# ======================

async def generate_logo_image(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Hugging Face FLUX.1 модель (бесплатно!)"""
    
    # Формируем улучшенный промпт для логотипа
    full_prompt = (
        f"Professional {style} style logo design: {prompt}. "
        f"Clean vector graphics, high quality, suitable for branding, "
        f"white background, no text, simple and memorable."
    )
    
    # Используем FLUX.1-schnell от Black Forest Labs (быстрая и качественная)
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
    }
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):  # 3 попытки при ошибке
            try:
                async with session.post(
                    API_URL,
                    headers=headers,
                    json={"inputs": full_prompt},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        image_data = await response.read()
                        if len(image_data) > 1000:  # Проверка что это изображение
                            logger.info(f"✅ Image generated: {len(image_data)} bytes")
                            return image_data
                        else:
                            raise Exception("Получен пустой ответ от API")
                    
                    elif response.status == 503:
                        # Модель загружается, ждем
                        error_data = await response.json()
                        if "estimated_time" in error_data:
                            wait_time = error_data["estimated_time"]
                            logger.warning(f"Модель загружается, ждем {wait_time} секунд")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            await asyncio.sleep(5)
                            continue
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ошибка API {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                if attempt == 2:
                    raise Exception("Таймаут генерации, попробуйте позже")
                await asyncio.sleep(2)
                continue
                
    raise Exception("Не удалось сгенерировать изображение после нескольких попыток")

# ======================
# ФУНКЦИЯ ЧАТА С DEEPSEEK
# ======================

async def chat_with_deepseek(user_id: int, message: str) -> str:
    """Общение с DeepSeek с контекстом"""
    
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append({"role": "user", "content": message})
    
    # Ограничиваем историю последними 10 сообщениями
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="deepseek-chat",
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

# ======================
# ОБРАБОТЧИКИ КОМАНД
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot (DeepSeek + Hugging Face)</b>\n\n"
        "Я создаю профессиональные логотипы и общаюсь с помощью ИИ!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Чат на базе DeepSeek AI\n"
        "• Генерация логотипов через FLUX (Hugging Face)\n"
        "• 6 стилей на выбор\n"
        "• Полностью бесплатно\n\n"
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
        "<b>Доступные стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "<b>💬 Режим чата:</b>\n"
        "Просто отправьте любое сообщение — бот ответит\n\n"
        "<b>💰 Бесплатно:</b>\n"
        "• DeepSeek — 4 млн токенов при регистрации\n"
        "• Hugging Face — неограниченно"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "💬 Чат с AI")
async def chat_mode(message: Message):
    await message.answer(
        "💬 <b>Режим чата активирован</b>\n\n"
        "Просто пишите мне сообщения, и я буду отвечать.\n\n"
        "Что я умею:\n"
        "• Отвечать на вопросы\n"
        "• Писать код\n"
        "• Объяснять концепции\n"
        "• Переводить текст\n\n"
        "Чтобы вернуться к логотипам — нажмите '🎨 Создать логотип'",
        parse_mode="HTML",
        reply_markup=main_kb
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current_style = user_style.get(message.from_user.id)
    current_text = f"\n\nТекущий стиль: <b>{current_style}</b>" if current_style else ""
    
    await message.answer(
        f"🎭 <b>Выберите стиль логотипа:</b>{current_text}",
        reply_markup=style_kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    
    style_hints = {
        "Minimalism": "чистые линии, минимум деталей",
        "Abstract": "абстрактные формы, уникально",
        "Vintage": "ретро-стиль, винтажные элементы",
        "Cyberpunk": "неоновые цвета, футуризм",
        "Eco": "природные мотивы, зелёные тона",
        "Luxury": "золотые акценты, элегантность"
    }
    
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n"
        f"🎨 Характеристика: {style_hints.get(message.text, '')}\n\n"
        f"✨ Теперь нажмите 'Создать логотип' и опишите идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    
    await message.answer(
        f"🎨 <b>Генерация логотипа</b>\n\n"
        f"🎭 Текущий стиль: <b>{style}</b>\n\n"
        f"📝 <b>Опишите идею максимально подробно:</b>\n"
        f"• Что изобразить? (объекты, символы)\n"
        f"• Какие цвета использовать?\n"
        f"• Для какой сферы логотип?\n\n"
        f"⏱ <b>Время:</b> 10-20 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"логотип для IT-компании, облако и шестеренка, сине-белые тона",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    # Игнорируем команды
    if message.text.startswith('/'):
        return
    
    # Игнорируем кнопки
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", 
               "🔙 Назад", "Minimalism", "Abstract", "Vintage", 
               "Cyberpunk", "Eco", "Luxury", "💬 Чат с AI"]
    if message.text in buttons:
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Проверяем, похоже ли на запрос логотипа
    logo_keywords = ["логотип", "бренд", "компания", "магазин", "кофейня", "it", "спорт", "design"]
    is_logo_request = any(keyword in message.text.lower() for keyword in logo_keywords) and len(message.text.split()) > 3
    
    if is_logo_request:
        await generate_logo(message, style)
    else:
        await chat_response(message)

async def generate_logo(message: Message, style: str):
    """Генерация логотипа"""
    
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}{'...' if len(message.text) > 80 else ''}\n\n"
        f"🔄 Используется нейросеть FLUX (Hugging Face)\n"
        f"⏱ Пожалуйста, подождите 10-20 секунд...",
        parse_mode="HTML"
    )
    
    try:
        # Генерируем изображение
        image_bytes = await generate_logo_image(message.text, style)
        
        # Отправляем результат
        photo = io.BytesIO(image_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"📝 <b>Описание:</b> {message.text[:150]}\n"
                f"🎭 <b>Стиль:</b> {style}\n\n"
                f"🔄 <b>Хотите ещё?</b> Нажмите 'Создать логотип'\n"
                f"🎨 <b>Сменить стиль</b> — 'Выбрать стиль'\n"
                f"💬 <b>Пообщаться</b> — 'Чат с AI'"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Logo generated for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_msg = str(e)
        
        if "503" in error_msg or "загружается" in error_msg:
            await message.answer(
                "⏳ <b>Модель загружается</b>\n\n"
                "Первый запрос может занять до 30 секунд.\n"
                "Пожалуйста, попробуйте еще раз через 10 секунд.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка генерации</b>\n\n"
                f"<code>{error_msg[:200]}</code>\n\n"
                f"💡 <b>Что делать?</b>\n"
                f"• Сделайте описание более конкретным\n"
                f"• Попробуйте другой стиль\n"
                f"• Используйте 5-15 слов\n\n"
                f"Попробуйте снова через минуту.",
                parse_mode="HTML"
            )
        
        logger.error(f"❌ Generation error for user {message.from_user.id}: {e}")

async def chat_response(message: Message):
    """Ответ в режиме чата"""
    
    status_msg = await message.answer("🤔 Думаю...")
    
    try:
        response = await chat_with_deepseek(message.from_user.id, message.text)
        
        await status_msg.delete()
        
        # Если ответ длинный, разбиваем на части
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await message.answer(response[i:i+4000], parse_mode="HTML")
        else:
            await message.answer(response, parse_mode="HTML")
            
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            "❌ <b>Ошибка</b>\n\nНе удалось получить ответ от AI.\nПопробуйте позже.",
            parse_mode="HTML"
        )
        logger.error(f"Chat error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🤖 AI LOGO BOT v5.0 (DeepSeek + Hugging Face)")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:15]}... OK")
    print(f"🔑 DeepSeek Key: {DEEPSEEK_API_KEY[:15]}... OK")
    print(f"🤗 Hugging Face Token: {HUGGINGFACE_TOKEN[:15]}... OK")
    print("=" * 60)
    print("🚀 Бот запускается...")
    print("🎨 Модель: FLUX.1-schnell (Hugging Face)")
    print("💬 Чат: DeepSeek AI")
    print("💰 Полностью бесплатно!")
    print("=" * 60 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared")
        logger.info("Bot is ready! Starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
