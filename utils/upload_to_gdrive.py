import os
import sys
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build

sys.path.append(os.path.abspath('.'))
from config import settings

CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client_secrets.json')
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'service_secrets.json')

def upload_and_share_file(file_path, folder_id, type='image'):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)

    media = MediaFileUpload(file_path, mimetype='image/jpeg')

    file = (
        service.files()
        .create(
            body={
                'name': os.path.basename(file_path),
                'parents': [folder_id]
            },
            media_body=media,
            fields='id,name,parents,webViewLink,webContentLink'
        )
        .execute()
    )
    service.permissions().create(body={'role': 'reader', 'type': 'anyone'}, fileId=file.get('id')).execute()
    output = 'https://lh3.googleusercontent.com/d/{}?authuser=1/view'.format(file.get('id'))\
        if type == 'image'\
        else file.get('webContentLink')
    return output


def upload_and_share_file_pydrive(file_path, folder_id):
    gauth = GoogleAuth()

    # settings = {
    #     "client_config_backend": "service",
    #     "service_config": {
    #         "client_json_file_path": "service-secrets.json",
    #     }
    # }
    # gauth = GoogleAuth(settings=settings)
    # gauth.ServiceAuth()

    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({'title': os.path.basename(file_path), 'parents': [{'id': folder_id}]})
    file.SetContentFile(file_path)
    file.Upload()
    file.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})

    return file['webContentLink']


if __name__ == '__main__':
    file_path = '/media/andrew/KINGSTON/clip-art/wallpapers/animal-gea928f56a_1920.jpg'
    folder_id = settings.gdrive_folder_id
    # shared_file_link = upload_and_share_file_pydrive(file_path, folder_id)
    shared_file_link = upload_and_share_file(file_path, folder_id)
    print(shared_file_link)
