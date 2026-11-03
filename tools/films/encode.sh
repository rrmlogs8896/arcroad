#!/bin/bash
# Encode each 4K master (tools/films/render.py) into the five sizes the home page picks from, plus a poster.
# Usage: tools/films/encode.sh /home/claude/films-out web/drive/media/films
set -euo pipefail
SRC="$1"; DST="$2"; mkdir -p "$DST"
for M in "$SRC"/*-master.mp4; do
  F=$(basename "$M" -master.mp4)
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M")
  FADE=""; SS=0; ADD=0
  # The drive film is the /drive/ scene itself: skip its first 0.9 s (camera still settling) and fade in and out
  # like the others; its busy street costs more bits, so it is encoded two CRF steps lighter.
  if [ "$F" = "drive" ]; then SS=0.9; ADD=2; D=$(python3 -c "print($D-0.9)"); FADE=",fade=t=in:st=0:d=0.6,fade=t=out:st=$(python3 -c "print(round($D-0.6,3))"):d=0.6"; fi
  for T in "480 854 31" "720 1280 29" "1080 1920 28" "1440 2560 28" "2160 3840 27"; do
    set -- $T
    ffmpeg -y -loglevel error -ss "$SS" -i "$M" -vf "scale=$2:$1:flags=lanczos$FADE" -c:v libx264 -preset veryfast -crf "$(( $3 + ADD ))" \
      -profile:v high -level 5.1 -pix_fmt yuv420p -movflags +faststart -an "$DST/$F-$1.mp4"
  done
  ffmpeg -y -loglevel error -ss "$(python3 -c "print(round($SS+$D*0.45,2))")" -i "$M" -frames:v 1 -vf "scale=1280:720:flags=lanczos" -q:v 4 "$DST/$F.jpg"
  echo "$F: $(du -ch "$DST/$F"-*.mp4 | tail -1 | cut -f1)"
done
