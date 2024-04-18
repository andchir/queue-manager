import os
import sys
import subprocess

argv = sys.argv[1:]

# Run launcher:
# python worker_launcher.py python 2 workers/stable-diffusion-webui.py

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_pid(name):
    return list(map(int, subprocess.check_output(['pidof', name]).split()))


if __name__ == '__main__':
    if len(argv) > 2:
        allowed_len = int(argv[1])
        process_name = os.path.join(ROOT_DIR, argv[2])
        pids = get_pid(argv[0])
        if len(pids) <= allowed_len:
            print('Starting worker...')
            # result = subprocess.call(['python', process_name])
            result = subprocess.Popen(['python', process_name])
        else:
            print('Waiting...')
