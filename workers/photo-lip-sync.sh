#!/bin/bash

# photo-lip-sync.sh '/home/andrew/PycharmProjects/queue-manager/uploads/lip-sync/output/dd2f291d-905e-11ef-bd3f-f57842a97b2c_resized--face_speaking_30sec_15sec.mp4' \
# '/media/andrew/KINGSTON/audio/voice/8 марта - жен.mp3' \
# 'b3ea1d8f-8020-4549-9b07-ec2012451d0c'

cd '/home/andrew/python_projects/facefusion'
source '/home/andrew/.zshrc'
conda activate facefusion

UUID="$3"
BASE_NAME="$(basename "$1")"
DIR_PATH="$(dirname "$1")"

echo $DIR_PATH
echo $UUID

python facefusion.py job-create lipsync-"$UUID"

python facefusion.py job-add-step lipsync-"$UUID" \
-s "$2" \
-t "$1" \
-o "$DIR_PATH"/output_"$UUID".mp4 \
--output-image-quality 95 \
--output-image-resolution '1920x1080' \
--output-audio-encoder 'aac' \
--output-video-encoder 'libx264' \
--output-video-preset 'medium' \
--output-video-quality 95 \
--output-video-resolution '1280x720' \
--output-video-fps 25 \
--lip-syncer-model 'wav2lip_gan_96' \
--face-enhancer-model 'gfpgan_1.3' \
--face-enhancer-blend 100 \
--processors {'lip_syncer','face_enhancer'}

python facefusion.py job-submit lipsync-"$UUID"

python facefusion.py job-run lipsync-"$UUID" --execution-provider cuda

