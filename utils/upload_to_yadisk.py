import os
import sys
import yadisk

sys.path.append(os.path.abspath('.'))
from config import settings


def upload_and_share_file(file_path, dir_path, type='image'):
    client = yadisk.Client(token=settings.yadisk_token)

    with client:
        if not client.check_token():
            # TODO: use refresh_token()
            print('YaDisk token is invalid.')
            return None, None

        base_name = os.path.basename(file_path)
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


if __name__ == '__main__':
    # file_path = '/media/andrew/KINGSTON/clip-art/wallpapers/animal-gea928f56a_1920.jpg'
    file_path = '/media/andrew/KINGSTON/video/River - 131339.mp4'
    dir_path = 'api2app/media'
    file_url, public_url = upload_and_share_file(file_path, dir_path)
    print(file_url, public_url)
