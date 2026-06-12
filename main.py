import asyncio
import logging
import os
import sys
import io
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import google.generativeai as genai
from PIL import Image

# ======================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================
# ЧТЕНИЕ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (правильный способ для Railway)
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Проверка наличия переменных с понятными сообщениями
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not GEMINI_API_KEY:
    missing_vars.append("GEMINI_API_KEY")

if missing_vars:
    logger.error("=" * 60)
    logger.error("❌ ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for var in missing_vars:
        logger.error(f"   • {var}")
    logger.error("")
    logger.error("📌 КАК ИСПРАВИТЬ (на Railway):")
    logger.error("   1. Откройте проект → ваш сервис → вкладка 'Variables'")
    logger.error("   2. Добавьте переменные:")
    logger.error(f"      • Key: BOT_TOKEN → Value: ваш токен от BotFather")
    logger.error(f"      • Key: GEMINI_API_KEY → Value: ключ из https://aistudio.google.com")
    logger.error("   3. Нажмите 'Save' и дождитесь перезапуска")
    logger.error("=" * 60)
    sys.exit(1)

logger.info("✅ Переменные окружения загружены успешно")
logger.info(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
logger.info(f"   GEMINI_API_KEY: {GEMINI_API_KEY[:15]}...")

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация Google Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Проверяем доступные модели
    try:
        # Пробуем использовать модель для изображений
        image_model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
        # Тестовая генерация (короткий таймаут)
        logger.info("✅ Gemini Image Model: доступна")
    except Exception as e:
        logger.warning(f"⚠️ Gemini Image Model может быть недоступна: {e}")
        image_model = None
    
    # Модель для текста
    text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    logger.info("✅ Google Gemini initialized successfully")
    
except Exception as e:
    logger.error(f"❌ Ошибка инициализации Gemini: {e}")
    logger.error("   Проверьте правильность GEMINI_API_KEY")
    sys.exit(1)

# Хранилище стилей пользователей
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
# ФУНКЦИЯ ГЕНЕРАЦИИ ИЗОБРАЖЕНИЯ
# ======================

async def generate_logo_image(prompt: str, style: str):
    """Генерация логотипа через Google Gemini"""
    full_prompt = (
        f"Create a professional {style} style logo: {prompt}. "
        f"Clean vector design, high quality, suitable for branding. "
        f"No text, only visual elements. White background recommended."
    )
    
    try:
        if image_model is None:
            raise Exception("Модель для генерации изображений недоступна")
        
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            image_model.generate_content, 
            full_prompt
        )
        
        if response._result.candidates:
            for part in response._result.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return part.inline_data.data
        
        raise Exception("Ответ не содержит изображения")
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise

# ======================
# ОБРАБОТЧИКИ КОМАНД
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Я создаю логотипы с помощью Google Gemini AI!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Бесплатная генерация (до 500 изображений/день)\n"
        "• 6 стилей на выбор\n"
        "• Простота использования\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выберите стиль\n"
        "2. Нажмите 'Создать логотип'\n"
        "3. Опишите вашу идею\n\n"
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
        "• <b>Выбрать стиль</b> — установите стиль логотипа\n"
        "• <b>Создать логотип</b> — начните создание\n"
        "• <b>Помощь</b> — показать это сообщение\n\n"
        "<b>Доступные стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "<b>Примеры описаний:</b>\n"
        "✅ 'Логотип IT-компании, облако и код'\n"
        "✅ 'Цветочный магазин, роза и капли воды'\n"
        "✅ 'Спортивный бренд, гора и солнце'\n\n"
        "❌ 'Сделай красивый логотип' (слишком общее описание)"
    )
    await message.answer(help_text, parse_mode="HTML")

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
    await message.answer("Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    
    style_hints = {
        "Minimalism": "чистые линии, минимум деталей",
        "Abstract": "абстрактные формы, уникально",
        "Vintage": "ретро-стиль, винтажные элементы",
        "Cyberpunk": "неоновые цвета, футуризм",
        "Eco": "природные мотивы, зелёные тона",
        "Luxury": "золото, элегантность, премиум"
    }
    
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n"
        f"🎨 Характеристика: {style_hints.get(message.text, '')}\n\n"
        f"Теперь нажмите 'Создать логотип' и опишите идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    
    await message.answer(
        f"💡 <b>Опишите идею для логотипа</b>\n\n"
        f"Текущий стиль: <b>{style}</b>\n\n"
        f"Напишите подробное описание (от 5 слов).\n\n"
        f"⏱ <b>Время генерации:</b> 5-10 секунд\n"
        f"🎨 <b>Качество:</b> 1024×1024",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def generate_logo(message: Message):
    # Игнорируем команды и кнопки
    if message.text.startswith('/'):
        return
    
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", 
               "🔙 Назад", "Minimalism", "Abstract", "Vintage", 
               "Cyberpunk", "Eco", "Luxury"]
    if message.text in buttons:
        return
    
    # Проверка длины описания
    if len(message.text.split()) < 3:
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Напишите более подробно, например:\n"
            "«Логотип для кофейни Медведь, чашка кофе и силуэт медведя»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Статусное сообщение
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}{'...' if len(message.text) > 80 else ''}\n\n"
        f"⏱ Пожалуйста, подождите 5-10 секунд",
        parse_mode="HTML"
    )
    
    try:
        # Генерация
        image_bytes = await generate_logo_image(message.text, style)
        
        # Отправка
        photo = io.BytesIO(image_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"💡 Описание: {message.text[:150]}\n"
                f"🎭 Стиль: {style}\n\n"
                f"🔄 Чтобы создать ещё — нажмите 'Создать логотип'\n"
                f"🎭 Сменить стиль — 'Выбрать стиль'"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Generated logo for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_msg = str(e).lower()
        
        if "safety" in error_msg:
            await message.answer(
                "⚠️ <b>Описание не соответствует политике безопасности</b>\n\n"
                "Пожалуйста, переформулируйте идею, избегая:\n"
                "• Насилия\n"
                "• Оскорблений\n"
                "• Нецензурной лексики\n\n"
                "Попробуйте снова с другим описанием.",
                parse_mode="HTML"
            )
        elif "quota" in error_msg or "limit" in error_msg or "429" in error_msg:
            await message.answer(
                "⚠️ <b>Дневной лимит генераций исчерпан</b>\n\n"
                "Google Gemini имеет ограничение ~500 изображений в день.\n"
                "Попробуйте снова через несколько часов или завтра.\n\n"
                "Это ограничение бесплатного тарифа.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка генерации</b>\n\n"
                f"<code>{str(e)[:200]}</code>\n\n"
                f"💡 <b>Рекомендации:</b>\n"
                f"• Сделайте описание более конкретным\n"
                f"• Попробуйте другой стиль\n"
                f"• Используйте 3-10 слов в описании\n\n"
                f"Попробуйте снова!",
                parse_mode="HTML"
            )
        
        logger.error(f"❌ Generation error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🤖 AI LOGO BOT v2.0")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:15]}... OK")
    print(f"🔑 Gemini Key: {GEMINI_API_KEY[:15]}... OK")
    print("=" * 60)
    print("🚀 Бот запускается...")
    print("📊 Лимит: ~500 изображений/день")
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
