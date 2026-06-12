import asyncio
import logging
import aiohttp
import io
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import google.generativeai as genai
from PIL import Image

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# ВАШИ КЛЮЧИ - ВСТАВЬТЕ СВОИ ЗНАЧЕНИЯ
# ======================

BOT_TOKEN = "8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY"
GEMINI_API_KEY = "AIzaSy..."  # ВСТАВЬТЕ ВАШ КЛЮЧ ОТ GOOGLE AI STUDIO

# Проверка наличия ключей
if not BOT_TOKEN:
    logger.error("❌ Укажите правильный BOT_TOKEN")
    exit(1)

if not GEMINI_API_KEY or GEMINI_API_KEY == "AIzaSy...":
    logger.error("❌ Укажите правильный GEMINI_API_KEY")
    logger.error("📌 Получите ключ на https://aistudio.google.com")
    exit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация Google Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Для текстовых моделей
    text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    # Для генерации изображений
    image_model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
    logger.info("✅ Google Gemini initialized")
except Exception as e:
    logger.error(f"❌ Gemini init error: {e}")
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================

async def generate_image_with_gemini(prompt: str, style: str) -> bytes:
    """
    Генерация изображения через Google Gemini
    Возвращает bytes изображения
    """
    full_prompt = f"Create a professional {style} style logo: {prompt}. Clean vector design, high quality, suitable for branding."
    
    try:
        # Генерируем изображение
        response = image_model.generate_content(full_prompt)
        
        # Извлекаем изображение из ответа
        if response._result.candidates:
            for part in response._result.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    return image_bytes
        
        raise Exception("No image data in response")
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise

async def generate_text_response(prompt: str) -> str:
    """Генерация текстового ответа через Gemini"""
    try:
        response = text_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Text generation error: {e}")
        return "Извините, произошла ошибка при обработке запроса."

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    welcome_text = (
        "🎨 <b>AI Logo Bot (Google Gemini)</b>\n\n"
        "Я создаю логотипы с помощью Google Gemini AI!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Бесплатная генерация изображений\n"
        "• 500+ изображений в день\n"
        "• Высокое качество\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выбери стиль (или оставь Minimalism)\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Опиши идею\n\n"
        "💡 <b>Пример:</b> 'логотип для кофейни с чашкой кофе'"
    )
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="HTML")
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
        "- Спортивный бренд с горой\n\n"
        "⚠️ <b>Примечание:</b> Бот использует бесплатный Google Gemini API\n"
        "• Лимит: ~500 изображений в день\n"
        "• Генерация занимает 5-10 секунд"
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
    
    # Подробное описание стиля для лучших результатов
    style_descriptions = {
        "Minimalism": "чистые линии, минимум деталей, современно",
        "Abstract": "абстрактные формы, креативно, уникально",
        "Vintage": "ретро стиль, старинные элементы, винтаж",
        "Cyberpunk": "неоновые цвета, футуристично, техно",
        "Eco": "природные элементы, зелёные тона, экологично",
        "Luxury": "золотые акценты, элегантно, премиум"
    }
    
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n\n"
        f"📝 Описание стиля: {style_descriptions.get(message.text, message.text)}\n\n"
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
        "<b>✅ Хороший пример:</b>\n"
        "Логотип для кофейни Медведь. Кофейная чашка с медведем, "
        "в стиле минимализм, коричневые и бежевые тона\n\n"
        "<b>❌ Плохой пример:</b>\n"
        "Сделай красивый логотип\n\n"
        "⏱ Генерация занимает 5-10 секунд",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def generate_logo(message: Message):
    # Проверяем, не является ли текст командой или кнопкой
    if message.text.startswith('/'):
        return
    
    # Игнорируем текст кнопок
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
               "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]
    if message.text in buttons:
        return
    
    # Получаем стиль пользователя (по умолчанию Minimalism)
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Отправляем статус
    status_msg = await message.answer(
        "🎨 Генерация логотипа через Google Gemini... ⏳\n"
        "Это может занять 5-10 секунд\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:50]}..."
    )
    
    try:
        # Генерация через Google Gemini
        image_bytes = await generate_image_with_gemini(message.text, style)
        
        # Конвертируем bytes в формат для Telegram
        photo = io.BytesIO(image_bytes)
        photo.name = "logo.png"
        
        # Удаляем статус
        await status_msg.delete()
        
        # Отправляем результат
        await message.answer_photo(
            photo=photo,
            caption=(
                f"🎨 <b>Логотип готов!</b>\n\n"
                f"💡 Идея: {message.text}\n"
                f"🎭 Стиль: {style}\n\n"
                f"✨ <b>Хотите еще?</b> Просто снова нажмите 'Создать логотип'\n"
                f"🔄 <b>Сменить стиль</b> - нажмите 'Выбрать стиль'"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"Generated logo for user {message.from_user.id} with style {style}")
        
    except Exception as e:
        await status_msg.delete()
        error_text = str(e)
        
        if "safety" in error_text.lower():
            await message.answer(
                "⚠️ <b>Ошибка безопасности</b>\n\n"
                "Ваше описание не соответствует политике безопасности Google.\n\n"
                "Пожалуйста, измените описание и попробуйте снова.\n"
                "Избегайте:\n"
                "• Насилия\n"
                "• Оскорблений\n"
                "• Нецензурной лексики",
                parse_mode="HTML"
            )
        elif "quota" in error_text.lower() or "limit" in error_text.lower():
            await message.answer(
                "⚠️ <b>Превышен дневной лимит</b>\n\n"
                "Google Gemini имеет ограничение ~500 изображений в день.\n\n"
                "Попробуйте снова через несколько часов или завтра.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка генерации</b>\n\n"
                f"<code>{error_text[:300]}</code>\n\n"
                f"💡 <b>Советы:</b>\n"
                f"• Измените описание\n"
                f"• Используйте более простую идею\n"
                f"• Выберите другой стиль\n\n"
                f"Попробуйте снова!",
                parse_mode="HTML"
            )
        
        logger.error(f"Generation error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    print("=" * 50)
    print("🤖 AI Logo Bot (Google Gemini) запускается...")
    print(f"📌 Bot token: {BOT_TOKEN[:15]}...")
    print(f"🔑 Gemini key: {GEMINI_API_KEY[:15]}...")
    print("=" * 50)
    print("✅ Используется БЕСПЛАТНЫЙ Google Gemini API")
    print("📊 Лимит: ~500 изображений в день")
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
