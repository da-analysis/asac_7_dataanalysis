import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 인증 함수
def authenticate_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_api_key.json", scope)
    client = gspread.authorize(creds)
    return client

# 시트에 사용자 정보 추가
def add_user_to_sheet(sheet_url, sheet_name, name, email, affiliation, timestamp, status):
    try:
        client = authenticate_gspread()
        sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
        sheet.append_row([name, email, affiliation, timestamp, status])
        return f"{name}님의 신청이 정상적으로 접수되었습니다."
    except Exception as e:
        return f"Google Sheets 에러: {str(e)}"
