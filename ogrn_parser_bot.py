
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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

def get_company_card_link(query):
    url = f"https://checko.ru/search?query={query}"
    resp = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    first_result = soup.select_one("a.link-black[href^='/company/']")
    if first_result:
        href = first_result.get("href")
        return "https://checko.ru" + href
    return None


def parse_page(url):
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    company_name = soup.select_one('h1#cn')
    company_name = company_name.get_text(strip=True) if company_name else ""

    registration_date = soup.select_one(
        "#top > div > div.row.gy-2.gx-4 > div:nth-child(1) > div:nth-child(3) > div:nth-child(2)"
    )
    registration_date = format_date(registration_date.get_text(strip=True)) if registration_date else ""

    legal_address = soup.select_one("#copy-address")
    legal_address = legal_address.get_text(strip=True) if legal_address else ""

    contact_address = soup.select_one("#contacts > div:nth-child(3)")
    contact_address = contact_address.get_text(strip=True) if contact_address else ""

    phone_tags = soup.select("a.link-pseudo[href^='tel:']")
    phones = phone_tags[0].get_text(strip=True) if phone_tags else ""

    email_tag = soup.select_one("a[href^='mailto:']")
    email = email_tag.get_text(strip=True) if email_tag else ""

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

    competitors = []
    competitors_header = soup.find('h3', class_='header', string='Конкуренты')
    if competitors_header:
        competitors_section = competitors_header.find_parent().find_all('a', class_='link')
        for link in competitors_section[:7]:
            name = link.get_text(strip=True)
            href = "https://checko.ru" + link.get('href')
            competitors.append((href, name))

    main_data = [
        url, company_name, registration_date, legal_address, contact_address,
        phones, email, director, founders[0], activity, okved_code, revenue, 0
    ]

    competitors_data = []
    for href, name in competitors:
        competitors_data.append([href, name, "", "", "", "", "", "", "", "", "", "", 1])

    return main_data, competitors_data

def main():
    query = input("Введите ОГРН или ИНН: ").strip()
    url = get_company_card_link(query)
    if not url:
        print("❌ Компания не найдена.")
        return

    main_row, competitors_rows = parse_page(url)

    wb = Workbook()
    ws = wb.active
    headers = [
        "Ссылка", "Название организации", "Дата регистрации", "Юридический адрес",
        "Адрес", "Телефоны", "Электронная почта и сайт", "Генеральный директор",
        "Учредитель 1", "Виды деятельности", "Код ОКВЭД", "Выручка за год Млн.руб", "Глубина"
    ]
    ws.append(headers)
    ws.append(main_row)
    for row in competitors_rows:
        ws.append(row)

    filename = "ogrn_result.xlsx"
    wb.save(filename)
    print(f"✅ Готово! Сохранено в файл: {filename}")

if __name__ == "__main__":
    main()
