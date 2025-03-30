#Рабочий Собирает ссылки на соцсети
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import urlparse
import re
from google_sheets import upload_to_google_sheets



INPUT_FILE = r"C:\Users\User\PycharmProjects\Парсер checko.ru\ogrn_recursive_result.xlsx"
OUTPUT_FILE = "ogrn_recursive_result.xlsx"


SOCIAL_DOMAINS = {
    'vk.com': 'vk',
    'instagram.com': 'instagram',
    'facebook.com': 'facebook',
    't.me': 'telegram',
    'wa.me': 'whatsapp',
    'whatsapp.com': 'whatsapp',
    'ok.ru': 'ok'
}

EXCLUDE = [
    'yabs.yandex', 'yandex.', 'ya.ru', 'translate.', 'list-org',
    'flamp', 'gosuslugi', 'nalog.ru', 'checko.ru', 'rusprofile.ru', '2gis', 'audit-it.ru', 'zachestnyibiznes.ru', 'xn--80az8a.xn--d1aqf.xn--p1ai'
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Mozilla/5.0 (X11; Linux x86_64)...',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)...',
    'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)...',
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ru-RU,ru;q=0.9"
    }

def clean_company_name(name):
    if not isinstance(name, str): return ''
    name = name.upper()
    name = re.sub(r'\b(ООО|ЗАО|ОАО|ПАО|ИП)\b', '', name)
    name = re.sub(r'[«»"]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def extract_city(address):
    if not isinstance(address, str): return ''
    patterns = [
        r'г\.?\s*(?:о\.\s*)?город\s*([А-Яа-яёЁ\- ]+)',
        r'г\.?\s*([А-Яа-яёЁ\- ]+)',
        r'город\s*([А-Яа-яёЁ\- ]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, address)
        if match:
            return match.group(1).strip()
    return ''

def extract_social_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = {k: '' for k in SOCIAL_DOMAINS.values()}
    for a in soup.find_all('a', href=True):
        href = a['href']
        for domain, platform in SOCIAL_DOMAINS.items():
            if domain in href and not links[platform]:
                links[platform] = href
    return links

def parse_site(site_url):
    try:
        response = requests.get(site_url, headers=get_headers(), timeout=10)
        return extract_social_links(response.text)
    except Exception as e:
        print(f"    [!] Ошибка парсинга сайта: {e}")
        return {k: '' for k in SOCIAL_DOMAINS.values()}

def find_website_and_socials(company_name, city):
    query = f"{company_name} {city} официальный сайт"
    url = f"https://yandex.ru/search/?text={requests.utils.quote(query)}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        found_site = None
        social_links = {k: '' for k in SOCIAL_DOMAINS.values()}

        for link in soup.find_all('a', href=True):
            raw_href = link['href']

            if "url=" in raw_href:
                match = re.search(r"url=([^&]+)", raw_href)
                if match:
                    href = requests.utils.unquote(match.group(1))
                else:
                    continue
            else:
                href = raw_href

            parsed = urlparse(href)
            if not parsed.scheme.startswith("http"):
                continue
            if any(excl in parsed.netloc for excl in EXCLUDE):
                continue

            for domain, platform in SOCIAL_DOMAINS.items():
                if domain in href and not social_links[platform]:
                    social_links[platform] = href
                    print(f"    [🟢] Найден {platform}: {href}")

            if not found_site and all(domain not in parsed.netloc for domain in SOCIAL_DOMAINS):
                found_site = f"{parsed.scheme}://{parsed.netloc}"
                print(f"    [🌐] Найден сайт: {found_site}")

        return found_site, social_links

    except Exception as e:
        print(f"    [!] Ошибка поиска Яндекс: {e}")
        return None, {k: '' for k in SOCIAL_DOMAINS.values()}

def main():
    print("📂 Загружаем таблицу...")
    df = pd.read_excel(INPUT_FILE)
    for col in SOCIAL_DOMAINS.values():
        df[col] = ''

    for idx, row in df.iterrows():
        raw_name = str(row.get('Название организации', ''))
        name = clean_company_name(raw_name)
        website = str(row.get('Веб-сайт', '')).strip()
        address = str(row.get('Адрес', '')).strip()
        city = extract_city(address)
        phone = str(row.get('Телефон 1', '')).strip()
        email = str(row.get('Электронная почта', '')).strip()

        print(f"\n[{idx+2}] 🔍 {raw_name}")
        print(f"    [🔎] Запрос: {name} {city}")

        links = {k: '' for k in SOCIAL_DOMAINS.values()}

        if website and website.lower() != 'nan':
            print(f"    [🌐] В таблице указан сайт: {website}")
            full_url = website if website.startswith("http") else "http://" + website
            links = parse_site(full_url)
            print(f"    [📥] С сайта получены соцсети: {links}")
        else:
            print(f"    [🕵️] Сайт отсутствует — ищем через Яндекс...")
            found_site, social_links = find_website_and_socials(name, city)

            if found_site:
                print(f"    [🌐] Найден сайт через поиск: {found_site}")
                links = parse_site(found_site)
                for platform, url in social_links.items():
                    if url:
                        links[platform] = url
            else:
                print(f"    [❌] Сайт не найден — используем только соцсети из поиска")
                links = social_links

            print(f"    [📥] Итоговые соцсети: {links}")

        for platform, url in links.items():
            df.at[idx, platform] = url

        print(f"    [📤] Записано в таблицу: {[f'{p}: {u}' for p, u in links.items() if u]}")
        print('-' * 60)
        time.sleep(random.uniform(1.5, 3.0))

    try:
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ Готово: {OUTPUT_FILE}")

        # Загружаем в Google Sheets и сохраняем ссылку
        link = upload_to_google_sheets(df)

        with open("last_link.txt", "w", encoding="utf-8") as f:
            f.write(link)

    except Exception as e:
        print(f"\n❌ Ошибка при сохранении Excel: {e}")

if __name__ == "__main__":
    main()
