import os
import sys
import yadisk
import datetime
import sys
import time
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

sys.path.append(os.path.abspath('.'))
from config import settings


def upload_and_share_file(file_path: str, dir_path: str, type='image', attempt=1, max_attempts=3):
    client = yadisk.Client(token=settings.yadisk_token)

    with client:
        if not client.check_token():
            # TODO: use refresh_token()
            print('YaDisk token is invalid.')
            return None, None

        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1]
        try:
            if extension in ['.mp4', '.3gp', '.avi']:
                result = client.upload(file_path, str(os.path.join(dir_path, base_name.replace(extension, ''))), overwrite=True, timeout=3600)
                result = client.rename(result.path, base_name, overwrite=True)
            else:
                result = client.upload(file_path, f'{dir_path}/{base_name}', overwrite=True, timeout=3600)
        except Exception as e:
            print(e)
            if attempt <= max_attempts:
                time.sleep(2)
                attempt += 1
                return upload_and_share_file(file_path, dir_path, type, attempt=attempt)
            return None, None

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


def delete_old_files_yadisk(dir_path, offset=0, limit=100, max_hours=12, all=False):
    now = datetime.datetime.now(datetime.timezone.utc)
    client = yadisk.Client(token=settings.yadisk_token)
    with client:
        # info = client.get_disk_info()
        # print('trash_size:', info.trash_size)
        # print('used_space:', info.used_space)
        # print('total_space:', info.total_space)
        # print(info)
        print('offset:', offset)
        print('limit:', limit)
        try:
            files_list = list(client.listdir(dir_path, offset=offset, limit=limit, fields=[
                'path', 'resource_id', 'file', 'size', 'created', 'media_type'], timeout=30, max_items=limit, n_retries=3))
        except Exception as e:
            print(e)
            files_list = []

        deleted_count = 0
        skipped_count = 0
        print('total: ', len(files_list))

        # Create progress bar for this batch
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task(f"[cyan]Processing files (offset={offset})...", total=len(files_list))

            for item in files_list:
                # print(item)
                time_diff = now - item.created
                if time_diff.total_seconds() / 60 / 60 > max_hours:
                    client.remove(item.path)
                    deleted_count += 1
                else:
                    # File is too new, skip it
                    skipped_count += 1
                progress.update(task, advance=1)

        print(f'Deleted {deleted_count} files, skipped {skipped_count} files in {dir_path}.')
        print('Emptying the trash bin...')
        client.remove_trash('/')
        print('Success!\n')

        # Recursively process next batch if needed
        # Key fix: offset should be increased by the number of SKIPPED files, not the limit
        # Only continue if there are files to skip AND we got a full batch (otherwise we've reached the end)
        if all and skipped_count > 0 and len(files_list) == limit:
            new_offset = offset + skipped_count
            delete_old_files_yadisk(dir_path, offset=new_offset, limit=limit, max_hours=max_hours, all=True)


if __name__ == '__main__':
    # https://oauth.yandex.ru/
    dir_path = 'api2app/media'
    file_path = '/media/andrew/KINGSTON/images/rocket.png'
    # file_path = '/media/andrew/KINGSTON/video/River - 131339.mp4'
    args = sys.argv[1:]
    action = args[0] if len(args) > 0 else ''
    offset = int(args[1]) if len(args) > 1 else 0
    limit = int(args[2]) if len(args) > 2 else 100
    print(action, offset, limit)
    if action == 'delete_old_files':
        delete_old_files_yadisk(dir_path, offset=offset, limit=limit, all=True)
    else:
        print('Uploading...')
        file_url, public_url = upload_and_share_file(file_path, dir_path)
        print('Uploaded.')
        print(file_url, public_url)
