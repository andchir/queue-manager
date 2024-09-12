import os
import sys
import yadisk
import datetime
import sys

sys.path.append(os.path.abspath('.'))
from config import settings


def upload_and_share_file(file_path: str, dir_path: str, type='image'):
    client = yadisk.Client(token=settings.yadisk_token)

    with client:
        if not client.check_token():
            # TODO: use refresh_token()
            print('YaDisk token is invalid.')
            return None, None

        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1]
        if extension in ['.mp4', '.3gp', '.avi']:
            result = client.upload(file_path, str(os.path.join(dir_path, base_name.replace(extension, ''))), overwrite=True, timeout=3600)
            result = client.rename(result.path, base_name, overwrite=True)
        else:
            result = client.upload(file_path, f'{dir_path}/{base_name}', overwrite=True, timeout=3600)

        if result is None or not hasattr(result, 'path'):
            return None, None

        # print(f'Uploaded {base_name} to {dir_path}.')

        result = client.publish(result.path)

        if result is None or not hasattr(result, 'path'):
            return None, None

        # print(f'Published!')

        meta = client.get_meta(result.path)
        # print(meta)

        return meta.file, meta.public_url


def delete_old_files_yadisk(dir_path, offset=0, limit=100, max_hours=6):
    now = datetime.datetime.now(datetime.timezone.utc)
    client = yadisk.Client(token=settings.yadisk_token)
    files_list = list(client.listdir(dir_path, offset=offset, limit=limit, fields=[
        'path', 'resource_id', 'file', 'size', 'created', 'media_type']))
    count = 0
    for item in files_list:
        time_diff = now - item.created
        if time_diff.total_seconds() / 60 / 60 > max_hours:
            client.remove(item.path)
            count += 1
    print(f'Deleted {count} files in {dir_path}.')
    print('Emptying the trash bin...')
    client.remove_trash('/')
    print('Success!')


if __name__ == '__main__':
    dir_path = 'api2app/media'
    # file_path = '/media/andrew/KINGSTON/clip-art/wallpapers/animal-gea928f56a_1920.jpg'
    file_path = '/media/andrew/KINGSTON/video/River - 131339.mp4'
    args = sys.argv[1:]
    action = args[0] if len(args) > 0 else ''
    offset = int(args[1]) if len(args) > 1 else 0
    limit = int(args[2]) if len(args) > 2 else 100
    print(action, offset, limit)
    if action == 'delete_old_files':
        delete_old_files_yadisk(dir_path, offset=offset, limit=limit)
    else:
        print('Uploading...')
        file_url, public_url = upload_and_share_file(file_path, dir_path)
        print('Uploaded.')
        print(file_url, public_url)
