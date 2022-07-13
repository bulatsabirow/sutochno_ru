import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
def execute_google_api_sheets(args):
    with open('table_url.txt') as file:
        json_file_name = file.readline()
        email = file.readline()
    CREDENTIALS_FILE = json_file_name  # Имя файла с закрытым ключом, вы должны подставить свое
    # Читаем ключи из файла
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                    ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API
    spreadsheet = service.spreadsheets().create(body = {
        'properties': {'title': 'Parsed rent offers with coordinates v.3', 'locale': 'ru_RU'},
        'sheets': [{'properties': {'sheetType': 'GRID',
                                   'sheetId': 0,
                                   'title': 'All parsed offers with coordinates',
                                   'gridProperties': {'rowCount': 30000, 'columnCount': len(args[0])}}}]
    }).execute()
    spreadsheetId = spreadsheet['spreadsheetId'] # сохраняем идентификатор файла
    driveService = apiclient.discovery.build('drive', 'v3', http = httpAuth) # Выбираем работу с Google Drive и 3 версию API
    access = driveService.permissions().create(
        fileId=spreadsheetId,
        body={'type': 'user', 'role': 'writer', 'emailAddress': email},  # Открываем доступ на редактирование
        fields='id'
    ).execute()

    results = service.spreadsheets().values().batchUpdate(spreadsheetId = spreadsheetId, body = {
    "valueInputOption": "USER_ENTERED", # Данные воспринимаются, как вводимые пользователем (считается значение формул)
    "data": [
        {"range": f"All parsed offers with coordinates!A1:{chr(ord('A') + len(args[0]) - 1)}{len(args)}",
         "majorDimension": "ROWS",     # Сначала заполнять столбцы, затем строки
         "values": [arg for arg in args]}
        ]
        }).execute()

    with open('table_url.txt', 'w', encoding="utf-8") as file:
        file.write('https://docs.google.com/spreadsheets/d/' + spreadsheetId)
