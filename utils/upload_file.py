import os
from datetime import datetime
import uuid
from fastapi import HTTPException, status, UploadFile
from typing import IO
import filetype


def upload_file(file: UploadFile, dir_path: str, type='image'):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    item_uuid = str(uuid.uuid1())
    file_info = validate_file_size_type(file, type=type)
    file_name = f'{item_uuid}.{file_info.extension}'

    file_path = os.path.join(dir_path, file_name)

    contents = file.file.read()
    open(file_path, 'wb').write(contents)

    return file_name


def validate_file_size_type(file: IO, type='image'):
    IMAGE_MAX_FILE_SIZE = 10485760  # 10MB
    AUDIO_MAX_FILE_SIZE = 10485760  # 10MB
    VIDEO_MAX_FILE_SIZE = 104857600  # 100MB
    IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'png', 'jpeg', 'jpg']
    VIDEO_TYPES = ['video/mp4', 'video/webm', 'mp4', 'webm']
    AUDIO_TYPES = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'mp3', 'wav']
    file_info = filetype.guess(file.file)
    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail='Unable to determine file type.',
        )

    detected_content_type = file_info.extension.lower()

    if (
            (type == 'image' and (file.content_type not in IMAGE_TYPES or detected_content_type not in IMAGE_TYPES))
            or (type == 'video' and (file.content_type not in VIDEO_TYPES or detected_content_type not in VIDEO_TYPES))
            or (type == 'audio' and (file.content_type not in AUDIO_TYPES or detected_content_type not in AUDIO_TYPES))
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f'Unsupported {type} file type.',
        )

    real_file_size = 0
    for chunk in file.file:
        real_file_size += len(chunk)
        if (
                (type == 'image' and real_file_size > IMAGE_MAX_FILE_SIZE)
                or (type == 'audio' and real_file_size > AUDIO_MAX_FILE_SIZE)
                or (type == 'video' and real_file_size > VIDEO_MAX_FILE_SIZE)
        ):
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='The file is too large.')

    return file_info


def delete_old_files(dir_path, max_hours=6):
    if not os.path.isdir(dir_path):
        return 0
    files_list = os.listdir(dir_path)
    now = datetime.now()
    deleted = 0
    for file in files_list:
        mtime = datetime.fromtimestamp(os.stat(os.path.join(dir_path, file)).st_mtime)
        diff = now - mtime
        if diff.total_seconds() / 60 / 60 > max_hours:
            os.remove(os.path.join(dir_path, file))
            deleted += 1
    return deleted