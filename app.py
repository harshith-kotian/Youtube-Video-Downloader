from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import requests

app = Flask(__name__, static_folder='frontend', static_url_path='/')
CORS(app)

INVIDIOUS_INSTANCE = "https://invidious.snopyta.org"  # Change if needed

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/info', methods=['GET'])
def get_video_info():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # Extract video ID from URL
    video_id = url.split("/")[-1].split("?")[0]

    # Fetch video details from Invidious API
    api_url = f"{INVIDIOUS_INSTANCE}/api/v1/videos/{video_id}"
    response = requests.get(api_url)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch video info"}), 500

    data = response.json()

    formats = [
        {"quality": f["quality"], "url": f["url"]}
        for f in data.get("formatStreams", []) if f.get("url")
    ]

    return jsonify({
        "title": data["title"],
        "channel": data["author"],
        "duration": data["lengthSeconds"],
        "thumbnail": data["videoThumbnails"][-1]["url"],
        "formats": formats
    })

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "Missing video URL"}), 400

    return Response(
        requests.get(url, stream=True).iter_content(4096),
        mimetype="video/mp4",
        headers={"Content-Disposition": "attachment; filename=video.mp4"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)