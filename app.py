from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# Background image URL
BASE_IMAGE_URL = "https://iili.io/3iSrn5u.jpg"

# Example API keys
API_KEYS = {
    "tranhao116": True,
    "2DAY": False,
    "busy": False
}

def is_key_valid(api_key):
    return API_KEYS.get(api_key, False)

def fetch_data(region, uid):
    url = f"https://ffwlxd-info.vercel.app/player-info?region={region}&uid={uid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def overlay_images(base_image_url, item_ids):
    try:
        base = Image.open(BytesIO(requests.get(base_image_url).content)).convert("RGBA")
    except Exception as e:
        print(f"Error loading base image: {e}")
        return None

    # 🎯 Updated positions (x, y) to align with hexagons
    positions = [
        (180, 690),   # Head
        (180, 930),   # Top
        (180, 1170),  # Bottom
        (830, 690),   # Face
        (830, 930),   # Mask
        (830, 1170),  # Backpack
    ]
    sizes = [(170, 170)] * 6  # Adjust if needed

    for idx in range(min(6, len(item_ids))):
        item_id = item_ids[idx]
        item_url = f"https://system.ffgarena.cloud/api/iconsff?image={item_id}.png"

        try:
            item_img = Image.open(BytesIO(requests.get(item_url).content)).convert("RGBA")
            item_img = item_img.resize(sizes[idx], Image.LANCZOS)
            base.paste(item_img, positions[idx], item_img)
        except Exception as e:
            print(f"Error processing item {item_id}: {e}")
            continue

    return base

@app.route('/api/image', methods=['GET'])
def generate_image():
    region = request.args.get('region')
    uid = request.args.get('uid')
    api_key = request.args.get('key')

    if not all([region, uid, api_key]):
        return jsonify({"error": "Missing region, uid, or key parameter"}), 400

    if not is_key_valid(api_key):
        return jsonify({"error": "Invalid or inactive API key"}), 403

    data = fetch_data(region, uid)
    if not data or "AccountProfileInfo" not in data or "EquippedOutfit" not in data["AccountProfileInfo"]:
        return jsonify({"error": "Failed to fetch data. Recheck uid and region"}), 500

    item_ids = data["AccountProfileInfo"]["EquippedOutfit"][:6]

    final_image = overlay_images(BASE_IMAGE_URL, item_ids)
    if final_image is None:
        return jsonify({"error": "Failed to generate image"}), 500

    img_io = BytesIO()
    final_image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)
