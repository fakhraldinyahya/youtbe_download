from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import re
import shutil

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
        # إعداد خيارات yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'forcejson': True,
        }
        
        # استخدام yt-dlp للحصول على معلومات الفيديو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # تحضير الجودات المتاحة
        formats = []
        for f in info.get('formats', []):
            if f.get('resolution') and f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                if f.get('resolution') not in formats:
                    formats.append(f.get('resolution'))
        
        # ترتيب الجودات بشكل تنازلي
        formats.sort(key=lambda x: int(x.split('x')[1]) if 'x' in x else 0, reverse=True)
        
        # الحصول على معلومات الفيديو
        video_info = {
            'title': info.get('title', 'فيديو غير معروف'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'author': info.get('uploader', 'غير معروف'),
            'available_qualities': formats
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
        # إنشاء اسم ملف فريد
        output_file = f"{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
        
        # إعداد خيارات yt-dlp
        ydl_opts = {
            'format': get_format_for_quality(quality),
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        # تنزيل الفيديو
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        # إنشاء مسار نسبي للتنزيل
        download_url = f'/download/{os.path.basename(output_path)}'
        
        return jsonify({
            'success': True,
            'message': 'تم تنزيل الفيديو بنجاح',
            'download_url': download_url,
            'filename': output_file
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

def get_format_for_quality(quality):
    # تحويل اختيار الجودة إلى صيغة مناسبة لـ yt-dlp
    if quality == 'highest':
        return 'best[ext=mp4]'
    elif 'x' in quality:
        height = quality.split('x')[1]
        return f'best[height<={height}][ext=mp4]'
    else:
        return 'best[ext=mp4]'

@app.route('/cleanup', methods=['POST'])
def cleanup_downloads():
    try:
        # مسح جميع الملفات من مجلد التنزيلات
        for file in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        return jsonify({'success': True, 'message': 'تم تنظيف مجلد التنزيلات بنجاح'})
    except Exception as e:
        return jsonify({'error': f'خطأ في تنظيف مجلد التنزيلات: {str(e)}'}), 500

if __name__ == '__main__':
    # تنظيف مجلد التنزيلات عند بدء التطبيق
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    
    app.run(debug=True)