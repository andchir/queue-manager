from gradio_client import Client, file


def processing_lips_sync(video_file_path, audio_file_path):
    print('Worker started', video_file_path, audio_file_path)



    return result


if __name__ == '__main__':
    video_file_path = '/media/andrew/KINGSTON/video/stock_video/mixkit-girl-from-the-front-walking-through-a-park-4825-hd-ready.mp4'
    audio_file_path = '/media/andrew/KINGSTON/work/SadTalker/input_audio/api2app - sync - jane.mp3'
    result = processing_lips_sync(video_file_path, audio_file_path)
    print(result)
