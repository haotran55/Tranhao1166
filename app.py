from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Đường dẫn ảnh nền bạn gửi (nằm trong cùng thư mục)
BASE_IMAGE_PATH = "https://iili.io/3igtA1s.jpg"

# Danh sách API key
API_KEYS = {
    "tranhao1161": True,
    "2DAY": False,
    "busy": False
}

def is_key_valid(api_key):
    """Kiểm tra API key có hợp lệ không"""
    return API_KEYS.get(api_key, False)

def fetch_data(region, uid):
    """Fetch player info data from external API."""
    url = f"https://ffwlxd-info.vercel.app/player-info?region={region}&uid={uid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def overlay_images(base_image_url, item_ids):
    """Overlay item images on top of base image."""
    try:
        base = Image.open(BytesIO(requests.get(base_image_url).content)).convert("RGBA")
    except Exception as e:
        print(f"Error loading base image: {e}")
        return None

    # Vị trí tương ứng 6 ô lục giác trong ảnh bạn gửi
    positions = [
        (95, 170),   # Trái trên
        (95, 320),   # Trái giữa
        (95, 480),   # Trái dưới
        (820, 170),  # Phải trên
        (820, 320),  # Phải giữa
        (820, 480)   # Phải dưới
    ]
    sizes = [(120, 120)] * 6

    for idx in range(min(6, len(item_ids))):
        item_id = item_ids[idx]
        item_url = f"https://system.ffgarena.cloud/api/iconsff?image={item_id}.png"

        try:
            item_img = Image.open(BytesIO(requests.get(item_url).content)).convert("RGBA")
            item_img = item_img.resize(sizes[idx], Image.LANCZOS)
            base.paste(item_img, positions[idx], item_img)
        except Exception as e:
            print(f"Lỗi xử lý item {item_id}: {e}")
            continue

    return base

@app.route('/api/image', methods=['GET'])
def generate_image():
    region = request.args.get('region')
    uid = request.args.get('uid')
    api_key = request.args.get('key')

    if not all([region, uid, api_key]):
        return jsonify({"error": "Thiếu tham số region, uid hoặc key"}), 400

    if not is_key_valid(api_key):
        return jsonify({"error": "API key không hợp lệ hoặc đã bị khóa"}), 403

    data = fetch_data(region, uid)
    if not data or "AccountProfileInfo" not in data or "EquippedOutfit" not in data["AccountProfileInfo"]:
        return jsonify({"error": "Lấy dữ liệu thất bại. Kiểm tra lại UID và Region"}), 500

    item_ids = data["AccountProfileInfo"]["EquippedOutfit"][:6]

    final_image = overlay_images(BASE_IMAGE_PATH, item_ids)
    if final_image is None:
        return jsonify({"error": "Tạo ảnh thất bại"}), 500

    img_io = BytesIO()
    final_image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
