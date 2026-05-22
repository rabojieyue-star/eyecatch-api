#!/bin/bash
apt-get install -y fonts-noto-cjk
mkdir -p /app/fonts
cp /usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc /app/fonts/
cp /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc /app/fonts/
pip install -r requirements.txt
