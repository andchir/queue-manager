import sys
import requests


def upload_to_vk(file_path, upload_url):
    with open(file_path, 'rb') as file:
        resp = requests.post(upload_url, files={'file': file})
    return resp.json()


if __name__ == '__main__':
    args = sys.argv[1:]
    file_path = '/media/andrew/KINGSTON/video/10 sec.mp4'
    upload_url = 'https://pu.vk.com/cxxxxxx/upload_doc.php?act=add_doc&mid=xxxxxx'
    response_data = upload_to_vk(file_path, upload_url)
    print('response data:', response_data)
