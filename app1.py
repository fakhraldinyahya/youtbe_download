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
    return render_template('index1.html')

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
        
        # تحضير قائمة الجودات المتاحة بشكل تفصيلي
        available_formats = []
        unique_resolutions = set()
        
        for f in info.get('formats', []):
            # نأخذ فقط تنسيقات MP4 التي تحتوي على صوت وفيديو
            if (f.get('ext') == 'mp4' and 
                f.get('vcodec') != 'none' and 
                f.get('acodec') != 'none' and
                f.get('height') is not None):
                
                height = f.get('height')
                width = f.get('width', 0)
                resolution = f"{width}x{height}" if width else f"?x{height}"
                format_id = f.get('format_id')
                filesize = f.get('filesize')
                
                # تحويل حجم الملف إلى ميجابايت
                filesize_mb = f"{filesize / (1024 * 1024):.2f} MB" if filesize else "غير معروف"
                
                # إضافة العنصر فقط إذا لم نضف نفس الدقة من قبل
                if height not in unique_resolutions:
                    unique_resolutions.add(height)
                    available_formats.append({
                        'format_id': format_id,
                        'resolution': resolution,
                        'height': height,
                        'filesize': filesize_mb,
                        'label': f"{resolution} ({filesize_mb})"
                    })
        
        # ترتيب الجودات حسب الدقة (من الأعلى إلى الأقل)
        available_formats.sort(key=lambda x: x['height'], reverse=True)
        
        # الحصول على معلومات الفيديو
        video_info = {
            'title': info.get('title', 'فيديو غير معروف'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'author': info.get('uploader', 'غير معروف'),
            'available_formats': available_formats
        }
        
        return jsonify(video_info)
    except Exception as e:
        return jsonify({'error': f'خطأ في معالجة الفيديو: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id')
    
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'الرجاء إدخال رابط YouTube صحيح'}), 400
    
    try:
        # إنشاء اسم ملف فريد
        output_file = f"{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
        
        # إعداد خيارات yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': output_path,
        }
        
        # إذا تم تحديد معرّف التنسيق، استخدمه
        if format_id:
            ydl_opts['format'] = format_id
        else:
            # وإلا، استخدم أفضل جودة متاحة بتنسيق MP4
            ydl_opts['format'] = 'best[ext=mp4]'
        
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