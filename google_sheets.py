import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def upload_to_google_sheets(df: pd.DataFrame, sheet_name='OGRNBOT'):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(creds)

    spreadsheet = client.create(sheet_name)
    spreadsheet.share('', perm_type='anyone', role='reader')

    sheet = spreadsheet.sheet1
    sheet.insert_row(df.columns.tolist(), 1)

    for i, row in df.iterrows():
        values = [str(x) if not pd.isna(x) else '' for x in row.tolist()]
        sheet.insert_row(values, i + 2)

    print(f"\n✅ Загружено в Google Sheets: {spreadsheet.url}")
    return spreadsheet.url
