# 🧠 OGRN Intelligence Bot

Telegram-бот, который по введённому ОГРН:
- собирает данные с checko.ru
- находит до 2 уровней конкурентов (до 50 компаний)
- ищет сайт и соцсети (если не указано)
- сохраняет всё в Google-таблицу
- отправляет ссылку в Telegram

## 📦 Структура

- `google_sheets.py` — заливка в Google Sheets
- `parser_recursive.py` — обход конкурентов
- `socials_from_site.py` — поиск сайта и соцсетей
- `telegram_bot.py` — Telegram-бот
- `ogrn_parser_bot.py` — запуск всей логики

## 🚀 Запуск

1. Установи зависимости:
   ```bash
   pip install -r requirements.txt
