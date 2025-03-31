from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import re
import shutil
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, static_folder='frontend', static_url_path='')

# Enable CORS for all routes
CORS(app)

# Proxy Fix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

ALLOWED_RESOLUTIONS = ["1080", "720", "480", "360", "144"]

@app.route('/')
def home():
    return "TubeFetch Backend Running!"

@app.route('/api/info', methods=['GET'])
def get_video_info():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # Remove extra parameters from URL if needed
    url = url.split('?')[0]
    
    print(f"Received URL: {url}")
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            seen_resolutions = set()
            
            for f in info.get("formats", []):
                if f.get("ext") != "mp4" or f.get("vcodec") == "none":
                    continue
                
                resolution = None
                if f.get("format_note"):
                    resolution = re.sub(r"[^0-9]", "", f.get("format_note"))
                elif f.get("height"):
                    resolution = str(f.get("height"))
                
                if resolution and resolution in ALLOWED_RESOLUTIONS and resolution not in seen_resolutions:
                    seen_resolutions.add(resolution)
                    filesize = f.get("filesize") or f.get("filesize_approx")
                    size_str = "Unknown"
                    if filesize:
                        size_str = f"{filesize/(1024*1024):.1f} MB" if filesize > 1024*1024 else f"{filesize/1024:.1f} KB"
                    
                    formats.append({
                        "itag": f["format_id"],
                        "quality": f"{resolution}p",
                        "type": f["ext"],
                        "size": size_str
                    })
            
            formats.sort(key=lambda x: int(x["quality"].replace("p", "")), reverse=True)
            
            return jsonify({
                "title": info["title"],
                "channel": info.get("uploader", "Unknown"),
                "duration": info["duration"],
                "thumbnail": info["thumbnail"],
                "formats": formats
            })
            
    except Exception as e:
        print(f"Error fetching video info: {str(e)}")
        return jsonify({"error": f"Failed to get video info: {str(e)}"}), 500

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    itag = request.args.get('itag')

    if not url or not itag:
        return jsonify({"error": "Missing URL or format"}), 400

    temp_dir = tempfile.mkdtemp()
    output_filename = os.path.join(temp_dir, f"{uuid.uuid4().hex}.mp4")

    ydl_opts = {
        "format": f"{itag}+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_filename,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferredformat": "mp4"
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            ydl.download([url])
            
            def generate():
                with open(output_filename, 'rb') as f:
                    while chunk := f.read(4096 * 16):
                        yield chunk
                os.remove(output_filename)
                shutil.rmtree(temp_dir)

            return Response(
                generate(),
                mimetype='video/mp4',
                headers={'Content-Disposition': f'attachment; filename="{info["title"][:50]}.mp4"'}
            )
    
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@app.route('/<path:filename>')
def serve_file(filename):
    try:
        return send_from_directory('.', filename)
    except:
        return "File not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
