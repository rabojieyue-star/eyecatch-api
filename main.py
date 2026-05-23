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

SERIF_JP = "fonts/NotoSerifJP-Bold.ttf"
SANS_JP  = "fonts/NotoSansJP-Regular.ttf"
LORA     = "fonts/NotoSansJP-Regular.ttf"  # LORAは代替でSansを使用

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
    panel_w = 520  # ③ 白エリアを少し狭く

    panel_color = colors["panel"]
    ov.rectangle([(0, 0), (panel_w, H)], fill=(*panel_color, 200))  # ③ 不透明度を下げる
    # 境界グラデーション（shorter fade）
    for x in range(120):  # ③ グラデーション幅を短く
        alpha = int(200 * (1 - x / 120))
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
        f_cat    = ImageFont.truetype(SANS_JP, 17)
        f_title1 = ImageFont.truetype(SERIF_JP, 54)
        f_title2 = ImageFont.truetype(SERIF_JP, 46)
        f_sub    = ImageFont.truetype(SANS_JP, 19)
        f_brand  = ImageFont.truetype(LORA, 17)
        f_by     = ImageFont.truetype(SANS_JP, 13)
    except:
        f_cat = f_title1 = f_title2 = f_sub = f_brand = f_by = ImageFont.load_default()

    X = 56

    # 左縦ゴールドライン
    draw.line([(44, 44), (44, H - 44)], fill=gold, width=2)

    # ① カテゴリーバッジ（テキスト垂直中央揃え）
    bbox = draw.textbbox((0, 0), category, font=f_cat)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    badge_top = 56
    badge_bottom = badge_top + th + 16
    badge_mid_y = badge_top + (badge_bottom - badge_top - th) // 2 - bbox[1]
    draw.rounded_rectangle([(X, badge_top), (X + tw + 32, badge_bottom)], radius=4, fill=terra)
    draw.text((X + 16, badge_mid_y), category, font=f_cat, fill=white)  # ① 垂直中央

    # ゴールドライン
    line_y = badge_bottom + 22
    draw.line([(X, line_y), (X + 50, line_y)], fill=gold, width=2)

# ④ タイトル改行ロジック（janomeで単語単位の自然な改行）
    t_y = line_y + 24
    max_width = 460

    from janome.tokenizer import Tokenizer

    def split_title_japanese(draw, title, max_w):
        t = Tokenizer()
        tokens = [token.surface for token in t.tokenize(title)]
        lines = []
        current = ""
        is_first = True

        for token in tokens:
            size = 54 if is_first else 46
            try:
                font = ImageFont.truetype(SERIF_JP, size)
            except:
                font = ImageFont.load_default()
            test = current + token
            w = draw.textbbox((0, 0), test, font=font)[2]
            if w > max_w and current:
                lines.append((current, size))
                current = token
                is_first = False
            else:
                current = test

        if current:
            size = 54 if not lines else 46
            lines.append((current, size))
        return lines

    title_lines = split_title_japanese(draw, title, max_width)
    for line, size in title_lines:
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
    sub_text = "プロが教える美容の知恵" if blog_type == "debel" else "プロが教える節約の知恵"
    draw.text((X, t_y + 30), sub_text, font=f_sub, fill=beige if blog_type == "debel" else (120, 85, 55))
    # 下部ライン
    draw.line([(44, H - 44), (580, H - 44)], fill=gold, width=1)
  # ブランドバッジ（DEBELスタイリッシュ版）
   if blog_type == "debel":
        bw, bh = 240, 90
        bx = X
        by = H - 44 - bh - 10
        # 外枠
        draw.rectangle([(bx, by), (bx + bw, by + bh)], outline=gold, width=3)
        # 内枠
        draw.rectangle([(bx + 8, by + 8), (bx + bw - 8, by + bh - 8)], outline=(*gold, 120), width=1)
        # コーナー装飾
        corner_len = 20
        corner_w = 4
        draw.rectangle([(bx, by), (bx + corner_len, by + corner_w)], fill=gold)
        draw.rectangle([(bx, by), (bx + corner_w, by + corner_len)], fill=gold)
        draw.rectangle([(bx + bw - corner_len, by), (bx + bw, by + corner_w)], fill=gold)
        draw.rectangle([(bx + bw - corner_w, by), (bx + bw, by + corner_len)], fill=gold)
        draw.rectangle([(bx, by + bh - corner_w), (bx + corner_len, by + bh)], fill=gold)
        draw.rectangle([(bx, by + bh - corner_len), (bx + corner_w, by + bh)], fill=gold)
        draw.rectangle([(bx + bw - corner_len, by + bh - corner_w), (bx + bw, by + bh)], fill=gold)
        draw.rectangle([(bx + bw - corner_w, by + bh - corner_len), (bx + bw, by + bh)], fill=gold)
        # フォント
        try:
            f_debel_sub = ImageFont.truetype(LORA, 16)
            f_debel_main = ImageFont.truetype(SERIF_JP, 28)
        except:
            f_debel_sub = f_debel_main = ImageFont.load_default()
        # DEBELテキスト（上）中央配置
        sub_bbox = draw.textbbox((0, 0), "DEBEL", font=f_debel_sub)
        sub_w = sub_bbox[2] - sub_bbox[0]
        sub_h = sub_bbox[3] - sub_bbox[1]
        draw.text((bx + (bw - sub_w) // 2, by + 16), "DEBEL", font=f_debel_sub, fill=(*gold, 180))
        # 痩身美容ラボ（下）中央配置
        main_text = "痩身美容ラボ"
        main_bbox = draw.textbbox((0, 0), main_text, font=f_debel_main)
        main_w = main_bbox[2] - main_bbox[0]
        draw.text((bx + (bw - main_w) // 2, by + 42), main_text, font=f_debel_main, fill=gold)
    else:
        # 節約ラボバッジ（既存）
        brand_text = "節約ラボ｜setsuyaku-lab.jp"
        try:
            f_brand_m = ImageFont.truetype(LORA, 17)
        except:
            f_brand_m = ImageFont.load_default()
        b_bbox = draw.textbbox((0, 0), brand_text, font=f_brand_m)
        bw = b_bbox[2] - b_bbox[0]
        bh = b_bbox[3] - b_bbox[1]
        pad_x, pad_y = 16, 10
        badge_h = 38
        badge_y1 = H - 44 - badge_h
        badge_y2 = H - 44
        draw.rounded_rectangle([(X, badge_y1), (X + bw + pad_x * 2, badge_y2)], radius=5, fill=gold)
        text_y = badge_y1 + (badge_h - bh) // 2 - b_bbox[1]
        draw.text((X + pad_x, text_y), brand_text, font=f_brand_m, fill=(255, 255, 255))
        
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
