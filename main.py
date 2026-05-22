from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import base64
import os

app = Flask(__name__)

W, H = 1200, 630

# カラー設定
COLORS = {
    "setsuyaku": {
        "panel": (248, 242, 234),
        "gold": (180, 130, 60),
        "brown": (44, 31, 26),
        "terra": (196, 113, 74),
        "white": (255, 255, 255),
        "beige": (232, 213, 163),
    },
    "debel": {
        "panel": (28, 16, 10),
        "gold": (201, 169, 110),
        "brown": (255, 255, 255),
        "terra": (196, 113, 74),
        "white": (255, 255, 255),
        "beige": (232, 213, 163),
    }
}

SERIF_JP = "/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc"
SANS_JP  = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
LORA     = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

def generate_eyecatch(image_url, title, category, blog_type="setsuyaku"):
    # 背景画像ダウンロード
    resp = requests.get(image_url, timeout=30)
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)

    colors = COLORS.get(blog_type, COLORS["setsuyaku"])

    # 左側パネル
    from PIL import Image as PILImage
    overlay = PILImage.new("RGBA", (W, H), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)

    panel_w = 600
    # 左側を単色パネルに
    panel_color = colors["panel"]
    ov.rectangle([(0, 0), (panel_w, H)], fill=(*panel_color, 230))

    # 境界グラデーション
    for x in range(150):
        alpha = int(220 * (1 - x / 150))
        ov.rectangle([(panel_w + x, 0), (panel_w + x + 1, H)], fill=(*panel_color, alpha))

    img = PILImage.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    gold  = colors["gold"]
    brown = colors["brown"]
    terra = colors["terra"]
    white = colors["white"]
    beige = colors["beige"]

    # フォント
    try:
        f_cat   = ImageFont.truetype(SANS_JP, 17)
        f_title1 = ImageFont.truetype(SERIF_JP, 54)
        f_title2 = ImageFont.truetype(SERIF_JP, 46)
        f_sub   = ImageFont.truetype(SANS_JP, 19)
        f_brand = ImageFont.truetype(LORA, 17)
        f_by    = ImageFont.truetype(SANS_JP, 13)
    except:
        f_cat = f_title1 = f_title2 = f_sub = f_brand = f_by = ImageFont.load_default()

    X = 56

    # 左縦ゴールドライン
    draw.line([(44, 44), (44, H - 44)], fill=gold, width=2)

    # カテゴリーバッジ
    bbox = draw.textbbox((0, 0), category, font=f_cat)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle([(X, 56), (X + tw + 32, 56 + th + 12)], radius=4, fill=terra)
    draw.text((X + 16, 62), category, font=f_cat, fill=white)

    # ゴールドライン
    line_y = 56 + th + 12 + 22
    draw.line([(X, line_y), (X + 50, line_y)], fill=gold, width=2)

    # タイトルを分割して表示
    t_y = line_y + 24
    if len(title) <= 14:
        lines = [title]
    elif len(title) <= 24:
        mid = len(title) // 2
        lines = [title[:mid], title[mid:]]
    else:
        lines = [title[:12], title[12:24], title[24:]]

    for i, line in enumerate(lines):
        size = 54 if i == 0 else 46
        try:
            f = ImageFont.truetype(SERIF_JP, size)
        except:
            f = ImageFont.load_default()
        draw.text((X, t_y), line, font=f, fill=brown)
        bbox = draw.textbbox((0, 0), line, font=f)
        t_y += bbox[3] - bbox[1] + 8

    # 区切りライン
    draw.line([(X, t_y + 16), (550, t_y + 16)], fill=gold, width=1)

    # サブコピー
    draw.text((X, t_y + 30), "プロが教える節約の知恵", font=f_sub, fill=beige if blog_type == "debel" else (120, 85, 55))

    # 下部ライン
    draw.line([(44, H - 44), (580, H - 44)], fill=gold, width=1)

    # ブランド
    brand = "DEBEL | 痩身美容ラボ" if blog_type == "debel" else "節約ラボ | setsuyaku-lab.jp"
    try:
        draw.text((X, H - 38), brand, font=f_brand, fill=gold)
    except:
        pass

    # base64エンコード
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    return img_b64


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        image_url = data.get("image_url", "")
        title     = data.get("title", "")
        category  = data.get("category", "")
        blog_type = data.get("blog_type", "setsuyaku")

        img_b64 = generate_eyecatch(image_url, title, category, blog_type)

        return jsonify({"image": img_b64, "status": "success"})

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

flask
pillow
requests
gunicorn

#!/bin/bash
# フォントダウンロード
mkdir -p /app/fonts

cp /usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc /app/fonts/
cp /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc /app/fonts/
pip install -r requirements.txt
