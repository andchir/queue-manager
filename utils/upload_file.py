import os
from fastapi import HTTPException, status, UploadFile
from typing import IO
import filetype


def upload_file(file: UploadFile, dir_path: str, file_name: str):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

    file_path = os.path.join(dir_path, file_name)

    contents = file.file.read()
    open(file_path, 'wb').write(contents)

    return True


def validate_file_size_type(file: IO, type='image'):
    IMAGE_MAX_FILE_SIZE = 10485760  # 10MB
    IMAGE_ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/heic', 'image/heif', 'image/heics',
                                'png', 'jpeg', 'jpg', 'heic', 'heif', 'heics']
    file_info = filetype.guess(file.file)
    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unable to determine file type",
        )

    detected_content_type = file_info.extension.lower()

    if type == 'image' and (file.content_type not in IMAGE_ALLOWED_FILE_TYPES
                            or detected_content_type not in IMAGE_ALLOWED_FILE_TYPES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail='Unsupported file type',
        )

    real_file_size = 0
    for chunk in file.file:
        real_file_size += len(chunk)
        if type == 'image' and real_file_size > IMAGE_MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Too large')

    return file_info
