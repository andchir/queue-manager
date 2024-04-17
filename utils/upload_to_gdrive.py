import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client_secrets.json')


def upload_and_share_file(file_path, folder_id):
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
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')
    folder_id = '1cCg3ywohyFsUNEwPOwL3ThPMiOnp1Ffg'
    shared_file_link = upload_and_share_file(file_path, folder_id)
    print(shared_file_link)
