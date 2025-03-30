import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
import datetime
import time
import random
import sys

parsed_urls = set()

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:113.0) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/18.19041",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(user_agents)
    }

def format_date(date_str):
    months = {
        "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
        "мая": "05", "июня": "06", "июля": "07", "августа": "08",
        "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
    }
    try:
        date_str = date_str.replace("года", "").strip()
        day, month_str, year = date_str.split()
        month = months.get(month_str.lower(), "01")
        return datetime.date(int(year), int(month), int(day)).strftime("%Y-%m-%d")
    except Exception:
        return "Неверная дата"

def parse_page(company_url, depth):
    time.sleep(5)  # 🔥 Дать отдохнуть IP перед запросом
    response = requests.get(company_url, headers=get_headers(), timeout=10)
    if "Подтвердите, что вы человек" in response.text:
        print(f"[{depth}] 🛑 Капча! Подтверди на сайте: {url}")
        input("👉 Нажми Enter, когда капча будет пройдена вручную...")
        return parse_page(url, depth)  # повторяем

    soup = BeautifulSoup(response.text, "html.parser")

    company_name = soup.select_one('h1#cn')
    company_name = company_name.get_text(strip=True) if company_name else ""
    print(f"[{depth}] {company_name} — {company_url}")

    registration_date = soup.select_one(
        "#top > div > div.row.gy-2.gx-4 > div:nth-child(1) > div:nth-child(3) > div:nth-child(2)"
    )
    registration_date = format_date(registration_date.get_text(strip=True)) if registration_date else ""

    legal_address = soup.select_one("#copy-address")
    legal_address = legal_address.get_text(strip=True) if legal_address else ""

    contact_address = soup.select_one("#contacts > div:nth-child(3)")
    contact_address = contact_address.get_text(strip=True) if contact_address else ""

    phone_tags = soup.select("a.link-pseudo[href^='tel:']")
    first_phone  = phone_tags[0].get_text(strip=True) if len(phone_tags) > 0 else ""
    second_phone = phone_tags[1].get_text(strip=True) if len(phone_tags) > 1 else ""
    third_phone  = phone_tags[2].get_text(strip=True) if len(phone_tags) > 2 else ""

    email_tag = soup.select_one("a[href^='mailto:']")
    email = email_tag.get_text(strip=True) if email_tag else ""

    site = ""
    website_label = soup.find("strong", string="Веб-сайт")
    if website_label:
        site_link = website_label.find_next_sibling("a")
        if site_link and site_link.has_attr("href"):
            site = site_link.get_text(strip=True)

    director_tag = soup.select_one("#management a")
    director = director_tag.get_text(strip=True) if director_tag else ""

    founders = []
    founders_table = soup.select_one("#founders-tab-1 > table")
    if founders_table:
        rows = founders_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                founders.append(cells[1].get_text(strip=True))
    founders = (founders + [""])[:1]

    activity = soup.select_one(
        "#top > div > div.row.gy-2.gx-4 > div:nth-child(1) > div:nth-child(4) > div:nth-child(2) > a"
    )
    activity = activity.get_text(strip=True) if activity else ""

    okved_code = soup.select_one('span.copy.ms-2.link-pseudo')
    okved_code = okved_code.get_text(strip=True) if okved_code else ""

    revenue_block = soup.select_one('a.link-black')
    if revenue_block:
        revenue_text = revenue_block.get_text(strip=True).replace("млн руб.", "").strip()
        try:
            revenue = float(revenue_text.replace(",", "."))
        except:
            revenue = ""
    else:
        revenue = ""

    social_links = []
    social_block = soup.find("div", string="Социальные сети")
    if social_block:
        parent = social_block.find_parent()
        if parent:
            for link in parent.find_all("a", href=True):
                social_links.append(link.get("href"))
    social = ", ".join(social_links) if social_links else ""

    data = [
        company_url, company_name, registration_date, legal_address, contact_address,
        first_phone, second_phone, third_phone,
        email, site, director, founders[0],
        activity, okved_code, revenue, social, depth
    ]

    # Собираем ссылки на конкурентов
    competitors = []
    competitors_header = soup.find('h3', class_='header', string='Конкуренты')
    if competitors_header:
        competitors_section = competitors_header.find_parent().find_all('a', class_='link')
        for link in competitors_section[:7]:
            href = "https://checko.ru" + link.get('href')
            competitors.append(href)

    return data, competitors

def crawl_company(url, depth, ws, headers_list): #Глубина рекурсии
    if depth > 1 or url in parsed_urls:
        return

    try:
        data, competitors = parse_page(url, depth)
    except Exception as e:
        print(f"❌ Ошибка при парсинге {url}: {e}")
        return

    ws.append(data)
    parsed_urls.add(url)
    time.sleep(random.uniform(3, 6))  # антибан

    for comp_url in competitors:
        crawl_company(comp_url, depth + 1, ws, headers_list)



def main():
    if len(sys.argv) > 1:
        ogrn = sys.argv[1].strip()
    else:
        ogrn = input("Введите ОГРН или ИНН: ").strip()

    start_url = f"https://checko.ru/company/{ogrn}"

    headers_list = [
        "Ссылка", "Название организации", "Дата регистрации", "Юридический адрес",
        "Адрес", "Телефон 1", "Телефон 2", "Телефон 3",
        "Электронная почта", "Веб-сайт", "Генеральный директор", "Учредитель 1",
        "Виды деятельности", "Код ОКВЭД", "Выручка за год Млн.руб", "Социальные сети", "Глубина"
    ]

    wb = Workbook()
    ws = wb.active
    ws.append(headers_list)

    crawl_company(start_url, 0, ws, headers_list)

    filename = "ogrn_recursive_result.xlsx"
    wb.save(filename)
    print(f"✅ Готово. Сохранено в файл: {filename}")

if __name__ == "__main__":
    main()
