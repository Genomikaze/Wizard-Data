import asyncio
import subprocess
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from google_sheets import upload_to_google_sheets  # загрузка в Google Sheets

API_TOKEN = "7655963126:AAFwgU16XJ85UU6DuMJ-t33509Vtg9R6ioQ"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply(
        "👋 Привет!\n"
        "Я — бот для разведки компаний по ОГРН или ИНН.\n\n"
        "📥 Вставь сюда номер ОГРН или ИНН, и я соберу:\n"
        "— данные компаний конкурентов\n"
        "— их сайты и соцсети\n\n"
        "И отдам тебе ссылку на Google Таблицу \n"
        "с инфой 📊"
    )

@dp.message_handler()
async def handle_ogrn(message: Message):
    ogrn = message.text.strip()
    await message.reply(f"🚀 Запускаю парсинг по ОГРН: {ogrn}\nОжидай...")

    try:
        # 1. Парсинг checko
        result = subprocess.run([
            r"C:\Users\User\PycharmProjects\Парсер checko.ru\venv\Scripts\python.exe",
            "parser_recursive.py", ogrn
        ], check=True)

        if result.returncode != 0:
            raise Exception("Парсер завершился с ошибкой")

        # 2. Парсинг соцсетей
        result2 = subprocess.run([
            r"C:\Users\User\PycharmProjects\Парсер checko.ru\venv\Scripts\python.exe",
            "socials_from_site.py"
        ], check=True)

        if result2.returncode != 0:
            raise Exception("Парсинг соцсетей завершился с ошибкой")

        # 3. Получение ссылки
        link = upload_to_google_sheets(pd.read_excel("ogrn_recursive_result.xlsx"))
        await message.reply(f"✅ Готово!\n📎 Ссылка на таблицу: {link}")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    print("🤖 Бот запущен")
    executor.start_polling(dp, skip_updates=True)
