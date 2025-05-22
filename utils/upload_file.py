import os
from datetime import datetime
import uuid

import requests
from fastapi import HTTPException, status, UploadFile
from typing import IO
import filetype
from pydub import AudioSegment

from utils.video_audio import cut_audio_duration


def upload_file(file: UploadFile, dir_path: str, type='image'):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    contents = file.file.read()

    item_uuid = str(uuid.uuid1())
    file_info = validate_file_size_type(file=file, type=type)
    file_name = f'{item_uuid}.{file_info.extension}'

    file_path = os.path.join(dir_path, file_name)

    open(file_path, 'wb').write(contents)

    return file_name


def upload_from_url(dir_path: str, file_url: str, type='image'):
    if not os.path.isdir(os.path.dirname(dir_path)):
        os.mkdir(os.path.dirname(dir_path))
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    item_uuid = str(uuid.uuid1())
    file_extension = file_url.split('.')[-1]
    file_name = f'{item_uuid}.{file_extension}'

    resp = requests.get(file_url)
    if 'Content-Disposition' in resp.headers:
        attachment_file_name = resp.headers['Content-Disposition']
        file_extension = attachment_file_name.split('.')[-1]
        file_name = f'{item_uuid}.{file_extension}'

    contents = resp.content
    file_path = os.path.join(dir_path, file_name)

    open(file_path, 'wb').write(contents)

    validate_file_size_type(file_path=file_path, type=type)

    return file_path


def validate_file_size(real_file_size, type='image'):
    IMAGE_MAX_FILE_SIZE = 20 * 1024 * 1024  # 10MB
    AUDIO_MAX_FILE_SIZE = 20 * 1024 * 1024  # 10MB
    VIDEO_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    if (
            (type == 'image' and real_file_size > IMAGE_MAX_FILE_SIZE)
            or (type == 'audio' and real_file_size > AUDIO_MAX_FILE_SIZE)
            or (type == 'video' and real_file_size > VIDEO_MAX_FILE_SIZE)
    ):
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='The file is too large.')

    return True


def validate_file_size_type(file: UploadFile = None, file_path=None, type='image'):
    IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'png', 'jpeg', 'jpg']
    VIDEO_TYPES = ['video/mp4', 'video/webm', 'mp4', 'webm']
    AUDIO_TYPES = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/x-wav', 'mp3', 'wav']

    if file is None and file_path is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail='File not found.',
        )

    file_info = filetype.guess(file.file) if file is not None else filetype.guess(file_path)
    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail='Unable to determine file type.',
        )

    detected_content_type = file_info.extension.lower()
    detected_mime_type = file_info.mime

    if (
            (type == 'image' and (detected_mime_type not in IMAGE_TYPES or detected_content_type not in IMAGE_TYPES))
            or (type == 'video' and (detected_mime_type not in VIDEO_TYPES or detected_content_type not in VIDEO_TYPES))
            or (type == 'audio' and (detected_mime_type not in AUDIO_TYPES or detected_content_type not in AUDIO_TYPES))
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f'Unsupported {type} file type.',
        )

    if file is not None:
        validate_file_size(file.size, type=type)

    if file_path is not None:
        file_size = os.path.getsize(file_path)
        validate_file_size(file_size, type=type)

    return file_info


def is_folder_empty(folder_path):
    return len(os.listdir(folder_path)) == 0


def delete_old_files(dir_path, max_hours=6):
    if not os.path.isdir(dir_path):
        return 0
    files_list = os.listdir(dir_path)
    now = datetime.now()
    deleted = 0
    for file in files_list:
        if not os.path.isfile(os.path.join(dir_path, file)):
            if os.path.isdir(os.path.join(dir_path, file)):
                deleted += delete_old_files(os.path.join(dir_path, file), max_hours)
                if is_folder_empty(os.path.join(dir_path, file)):
                    os.rmdir(os.path.join(dir_path, file))
            continue
        mtime = datetime.fromtimestamp(os.stat(os.path.join(dir_path, file)).st_mtime)
        diff = now - mtime
        if diff.total_seconds() / 60 / 60 > max_hours:
            os.remove(os.path.join(dir_path, file))
            deleted += 1
    return deleted


if __name__ == '__main__':
    out_path = cut_audio_duration('/media/andrew/KINGSTON/work/SadTalker/input_audio/jason_dentist_16000.wav', 20)
    print(out_path)
