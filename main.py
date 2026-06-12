import asyncio
import logging
import os
import sys
import io
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel
import google.auth

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
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Проверка наличия переменных
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not GOOGLE_CLOUD_PROJECT:
    missing_vars.append("GOOGLE_CLOUD_PROJECT")
if not GOOGLE_APPLICATION_CREDENTIALS:
    missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS (JSON с ключами сервисного аккаунта)")

if missing_vars:
    logger.error("=" * 60)
    logger.error("❌ ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    for var in missing_vars:
        logger.error(f"   • {var}")
    logger.error("")
    logger.error("📌 КАК ИСПРАВИТЬ (на Railway):")
    logger.error("   1. Откройте проект → ваш сервис → вкладка 'Variables'")
    logger.error("   2. Добавьте переменные:")
    logger.error("      • Key: BOT_TOKEN → Value: ваш токен от BotFather")
    logger.error("      • Key: GOOGLE_CLOUD_PROJECT → Value: ID проекта из Google Cloud")
    logger.error("      • Key: GOOGLE_APPLICATION_CREDENTIALS → Value: JSON с ключами сервисного аккаунта")
    logger.error("   3. Нажмите 'Save' и дождитесь перезапуска")
    logger.error("")
    logger.error("📖 Инструкция по созданию сервисного аккаунта:")
    logger.error("   https://cloud.google.com/vertex-ai/docs/generative-ai/setup-vertex-ai")
    logger.error("=" * 60)
    sys.exit(1)

logger.info("✅ Переменные окружения загружены успешно")
logger.info(f"   BOT_TOKEN: {BOT_TOKEN[:10]}...")
logger.info(f"   PROJECT_ID: {GOOGLE_CLOUD_PROJECT[:20]}...")

# ======================
# ИНИЦИАЛИЗАЦИЯ VERTEX AI
# ======================

try:
    # Инициализация Vertex AI
    aiplatform.init(
        project=GOOGLE_CLOUD_PROJECT,
        location="us-central1",  # Регион для генерации изображений
    )
    
    # Загружаем модель Imagen 3 для генерации логотипов
    imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
    
    logger.info("✅ Vertex AI initialized successfully")
    logger.info("   Модель: Imagen 3.0")
    logger.info("   Регион: us-central1")
    
except Exception as e:
    logger.error(f"❌ Ошибка инициализации Vertex AI: {e}")
    logger.error("   Проверьте:")
    logger.error("   1. Корректность GOOGLE_CLOUD_PROJECT")
    logger.error("   2. Наличие файла credentials в GOOGLE_APPLICATION_CREDENTIALS")
    logger.error("   3. Включено ли Vertex AI API в Google Cloud Console")
    sys.exit(1)

# ======================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ======================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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

async def generate_logo_image(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Vertex AI Imagen"""
    
    # Улучшаем промпт для лучших результатов
    full_prompt = (
        f"Create a professional {style} style logo design: {prompt}. "
        f"Clean vector graphics, high quality, suitable for branding, "
        f"white background, no text, simple and memorable."
    )
    
    try:
        # Генерируем изображение в отдельном потоке (синхронный вызов)
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: imagen_model.generate_images(
                prompt=full_prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_some",
                person_generation="allow_adult",
                negative_prompt="text, letters, words, watermark, signature, low quality, blurry"
            )
        )
        
        if not response or not response.images:
            raise Exception("Модель не вернула изображений")
        
        # Конвертируем изображение в bytes
        img_bytes = io.BytesIO()
        response.images[0]._image_bytes.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        logger.info(f"✅ Image generated successfully (size: {len(img_bytes.getvalue())} bytes)")
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        raise

# ======================
# ОБРАБОТЧИКИ КОМАНД
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot (Vertex AI)</b>\n\n"
        "Я создаю профессиональные логотипы с помощью Google Imagen 3!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Нейросеть Imagen 3 от Google\n"
        "• Высокое качество изображений\n"
        "• 6 стилей на выбор\n"
        "• Бесплатно до 500 изображений в месяц\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выберите стиль\n"
        "2. Нажмите 'Создать логотип'\n"
        "3. Опишите идею подробно\n\n"
        "💡 <b>Пример:</b> логотип для кофейни с чашкой кофе и силуэтом медведя",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started the bot")

@dp.message(Command("help"))
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    help_text = (
        "📖 <b>Инструкция по использованию</b>\n\n"
        "• <b>Выбрать стиль</b> — установите стиль логотипа\n"
        "• <b>Создать логотип</b> — начните создание\n"
        "• <b>Помощь</b> — показать это сообщение\n\n"
        "<b>Доступные стили:</b>\n"
        "• Minimalism — минимализм (чистые линии)\n"
        "• Abstract — абстракция (креативные формы)\n"
        "• Vintage — винтажный (ретро-элементы)\n"
        "• Cyberpunk — киберпанк (неон, футуризм)\n"
        "• Eco — эко-стиль (природа, зелёные тона)\n"
        "• Luxury — люксовый (золото, элегантность)\n\n"
        "<b>Советы для хорошего результата:</b>\n"
        "✅ Указывайте объекты (чашка, гора, цветок)\n"
        "✅ Добавляйте цвета (синий, золотой, зелёный)\n"
        "✅ Упоминайте отрасль (IT, кофейня, спорт)\n"
        "❌ Избегайте общих фраз (сделай красиво)\n\n"
        "<b>Пример идеального описания:</b>\n"
        "«Логотип для IT-компании, облако и код, "
        "сине-белые тона, современный минимализм»"
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
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    
    style_hints = {
        "Minimalism": "чистые линии, минимум деталей, современно",
        "Abstract": "абстрактные формы, уникально, креативно",
        "Vintage": "ретро-стиль, винтажные элементы, старина",
        "Cyberpunk": "неоновые цвета, футуризм, техно",
        "Eco": "природные мотивы, зелёные тона, экологично",
        "Luxury": "золотые акценты, элегантность, премиум"
    }
    
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранен!\n"
        f"🎨 Характеристика: {style_hints.get(message.text, '')}\n\n"
        f"✨ Теперь нажмите 'Создать логотип' и опишите идею.\n"
        f"Чем подробнее — тем лучше результат!",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    
    await message.answer(
        f"💡 <b>Опишите идею для логотипа</b>\n\n"
        f"🎭 Текущий стиль: <b>{style}</b>\n\n"
        f"📝 <b>Что писать?</b>\n"
        f"• Что изобразить? (объекты, символы)\n"
        f"• Какие цвета использовать?\n"
        f"• Для какой сферы логотип?\n\n"
        f"⏱ <b>Время генерации:</b> 5-10 секунд\n"
        f"🎨 <b>Качество:</b> Профессиональное\n\n"
        f"💪 <b>Пример:</b> логотип для кофейни Медведь, "
        f"чашка кофе и силуэт медведя, коричневые и бежевые тона",
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
    if len(message.text.split()) < 4:
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Напишите более подробно (минимум 4 слова).\n\n"
            "✅ <b>Хороший пример:</b>\n"
            "«Логотип для кофейни с чашкой кофе и медведем»\n\n"
            "❌ <b>Плохой пример:</b>\n"
            "«Сделай логотип»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Статусное сообщение
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}{'...' if len(message.text) > 80 else ''}\n\n"
        f"🔄 Процесс генерации может занять до 15 секунд\n"
        f"✨ Используется нейросеть Google Imagen 3",
        parse_mode="HTML"
    )
    
    try:
        # Генерация изображения
        image_bytes = await generate_logo_image(message.text, style)
        
        # Отправка результата
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
                f"🎨 <b>Сменить стиль</b> — 'Выбрать стиль'\n\n"
                f"⭐️ Оцените качество генерации!\n"
                f"📊 Осталось генераций на сегодня: ~{500 - datetime.now().day}"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Logo generated for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_msg = str(e).lower()
        
        if "safety" in error_msg or "policy" in error_msg:
            await message.answer(
                "⚠️ <b>Описание не соответствует политике безопасности</b>\n\n"
                "Пожалуйста, переформулируйте идею, избегая:\n"
                "• Насилия и оружия\n"
                "• Оскорблений и ненормативной лексики\n"
                "• Алкоголя и наркотиков\n"
                "• Политической тематики\n\n"
                "Попробуйте снова с другим описанием.",
                parse_mode="HTML"
            )
        elif "quota" in error_msg or "limit" in error_msg or "429" in error_msg:
            await message.answer(
                "⚠️ <b>Дневной лимит генераций исчерпан</b>\n\n"
                "Vertex AI имеет ограничение ~500 изображений в месяц\n"
                "Попробуйте снова завтра.\n\n"
                "Это ограничение бесплатного тарифа.",
                parse_mode="HTML"
            )
        elif "permission" in error_msg or "credential" in error_msg:
            await message.answer(
                "❌ <b>Ошибка авторизации</b>\n\n"
                "Проблема с доступом к Vertex AI.\n\n"
                "Проверьте:\n"
                "1. Правильно ли настроен сервисный аккаунт\n"
                "2. Включено ли Vertex AI API\n"
                "3. Есть ли права у сервисного аккаунта\n\n"
                "Обратитесь к администратору бота.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка генерации</b>\n\n"
                f"<code>{str(e)[:200]}</code>\n\n"
                f"💡 <b>Что делать?</b>\n"
                f"• Сделайте описание более конкретным\n"
                f"• Попробуйте другой стиль\n"
                f"• Используйте 5-15 слов\n\n"
                f"Попробуйте снова через минуту.",
                parse_mode="HTML"
            )
        
        logger.error(f"❌ Generation error for user {message.from_user.id}: {e}")

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🤖 AI LOGO BOT v3.0 (Vertex AI)")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:15]}... OK")
    print(f"🔑 Project ID: {GOOGLE_CLOUD_PROJECT[:20]}... OK")
    print(f"🤖 AI Model: Imagen 3.0")
    print("=" * 60)
    print("🚀 Бот запускается...")
    print("📊 Месячный лимит: ~500 изображений")
    print("📍 Регион: us-central1")
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
