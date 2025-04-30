# # Install pytube with: pip install pytube

# from pytube import YouTube
# import os

# def download_youtube_video(url, output_path='.', quality='highest'):
#     try:
#         # Create a YouTube object
#         yt = YouTube(url)
        
#         # Get the video stream based on quality
#         if quality == 'highest':
#             video = yt.streams.get_highest_resolution()
#         else:
#             # Filter by resolution (e.g., '720p')
#             video = yt.streams.filter(res=quality).first()
            
#             # If the specific resolution isn't available, fall back to highest
#             if not video:
#                 print(f"Resolution {quality} not available. Using highest resolution.")
#                 video = yt.streams.get_highest_resolution()
        
#         # Download the video
#         print(f"Downloading: {yt.title}")
#         print(f"Size: {video.filesize / (1024 * 1024):.2f} MB")
#         video.download(output_path)
        
#         print(f"Download complete! File saved to: {output_path}")
#         return True
    
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return False

# # Example usage
# if __name__ == "__main__":
#     video_url = input("Enter YouTube URL: ")
#     quality_options = ['highest', '720p', '480p', '360p']
    
#     print("Available quality options:")
#     for i, quality in enumerate(quality_options, 1):
#         print(f"{i}. {quality}")
    
#     quality_choice = int(input("Select quality (1-4): "))
#     selected_quality = quality_options[quality_choice - 1]
    
#     download_path = input("Enter download path (press Enter for current directory): ") or '.'
    
#     download_youtube_video(video_url, download_path, selected_quality)

from flask import Flask, render_template, request, jsonify, send_file
from pytube import YouTube
import os
import uuid
import re

app = Flask(__name__)

# مجلد لحفظ الفيديوهات المنزلة
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    data = request.json
    url = data.get('url')
    
    # التحقق من صحة رابط YouTube
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'الرجاء إدخال رابط YouTube صحيح'}), 400
    
    try:
        yt = YouTube(url)
        
        # الحصول على معلومات الفيديو
        video_info = {
            'title': yt.title,
            'thumbnail': yt.thumbnail_url,
            'duration': yt.length,
            'author': yt.author,
            'available_qualities': get_available_qualities(yt)
        }
        
        return jsonify(video_info)
    except Exception as e:
        return jsonify({'error': f'خطأ في معالجة الفيديو: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'highest')
    
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'الرجاء إدخال رابط YouTube صحيح'}), 400
    
    try:
        yt = YouTube(url)
        
        # الحصول على بث الفيديو بناءً على الجودة
        if quality == 'highest':
            video = yt.streams.get_highest_resolution()
        else:
            # تصفية حسب الدقة
            video = yt.streams.filter(res=quality).first()
            
            # إذا لم تكن الدقة المحددة متاحة، استخدم أعلى دقة
            if not video:
                video = yt.streams.get_highest_resolution()
        
        # إنشاء اسم ملف فريد
        filename = f"{uuid.uuid4().hex}_{video.default_filename}"
        output_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        # تنزيل الفيديو
        video.download(filename=output_path)
        
        # إنشاء مسار نسبي للتنزيل
        download_url = f'/download/{os.path.basename(output_path)}'
        
        return jsonify({
            'success': True,
            'message': 'تم تنزيل الفيديو بنجاح',
            'download_url': download_url,
            'filename': os.path.basename(output_path)
        })
    except Exception as e:
        return jsonify({'error': f'خطأ في تنزيل الفيديو: {str(e)}'}), 500

@app.route('/download/<filename>')
def serve_file(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)

def is_valid_youtube_url(url):
    # التحقق من صحة رابط YouTube
    youtube_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*'
    return re.match(youtube_regex, url) is not None

def get_available_qualities(yt):
    # الحصول على جميع الدقات المتاحة
    streams = yt.streams.filter(progressive=True)
    qualities = [stream.resolution for stream in streams if stream.resolution]
    return sorted(list(set(qualities)), key=lambda x: int(x[:-1]), reverse=True)

if __name__ == '__main__':
    app.run(debug=True)