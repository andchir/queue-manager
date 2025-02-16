import os
import ffmpeg
from pydub import AudioSegment
import math


def cut_audio_duration(file_path, max_dur=60):
    format = file_path[-3:].lower()
    audio = AudioSegment.from_file(file_path, format=format)
    if audio.duration_seconds <= max_dur:
        return file_path
    file_path_out = file_path[0:-4] + '_' + str(max_dur) + 'sec.' + format
    if os.path.isfile(file_path_out):
        return file_path_out
    audio_out = audio[:max_dur * 1000]
    audio_out.export(file_path_out, format=format)
    return file_path_out


def get_audio_duration(file_path, use_ceil=True):
    format = file_path[-3:].lower()
    audio = AudioSegment.from_file(file_path, format=format)
    return math.ceil(audio.duration_seconds) if use_ceil else int(audio.duration_seconds)


def video_create_duration(file_path, target_duration, start_time=0):
    try:
        probe = ffmpeg.probe(file_path)
    except ffmpeg.Error as e:
        print(str(e))
        return None
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    if video_stream is None:
        return None
    video_duration = float(video_stream['duration'])
    video_frames = float(video_stream['nb_frames'])
    format = file_path[-3:].lower()
    file_path_out = file_path[0:-4] + '_' + str(target_duration) + 'sec.' + format

    # TRIMMING
    if video_duration >= target_duration:
        (
            ffmpeg
            .input(file_path, ss=start_time, to=start_time + target_duration)
            .output(file_path_out, vcodec='copy', acodec='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
            # .compile()
        )

        return file_path_out

    # INCREASE DURATION
    parts_num = math.ceil(target_duration / video_duration)
    inputs = []
    for i in range(parts_num):
        inputs.append(ffmpeg.input(file_path).video)
        if audio_stream:
            inputs.append(ffmpeg.input(file_path).audio)

    joined = ffmpeg.concat(*inputs, v=1, a=1 if audio_stream else 0).node
    outputs = [joined[0]]
    if audio_stream:
        outputs.append(joined[1])

    result = (
        ffmpeg
        .output(*outputs, file_path_out,
                r=25, format='mp4', vcodec='libx264', video_bitrate=2000000,
                acodec='aac', audio_bitrate='128k', preset='slow')
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
        # .compile()
    )
    # print(result)

    return file_path_out


if __name__ == '__main__':
    # output = cut_audio_duration('/media/andrew/KINGSTON/music/mickey mouse song.mp3', 20)
    output = video_create_duration('/home/andrew/python_projects/LivePortrait/assets/examples/driving/face_speaking.mp4', 60)
    print(output)
