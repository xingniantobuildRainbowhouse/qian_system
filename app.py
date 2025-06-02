from flask import Flask, render_template, request, url_for
import os
import re

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'qian')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 中文数字映射
CHINESE_NUM_MAP = {
    '零': 0, '〇': 0,
    '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10
}

# 繁简体项目词映射
TERM_ALIASES = {
    '家宅运气': ['家宅運氣'],
    '财富增损': ['財富增損'],
    '诉讼是非': ['訴訟是非'],
    '谋望': ['謀望'],
    '人际关系': ['人際關係'],
    '风水厄运': ['風水厄運'],
    '请托': ['請託'],
}

def convert_chinese_numerals(text):
    # 支持“二三” → 23；“二十三” → 23；“十七” → 17；“十” → 10；“十三” → 13；“二十” → 20
    result = ''
    if re.fullmatch(r'[一二三四五六七八九十〇零]+', text):
        if '十' in text:
            parts = text.split('十')
            left = CHINESE_NUM_MAP.get(parts[0], 1) if parts[0] else 1
            right = CHINESE_NUM_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            result = str(left * 10 + right)
        else:
            result = ''.join(str(CHINESE_NUM_MAP[c]) for c in text)
    return result

def normalize_input(raw_input):
    raw_input = raw_input.replace(" ", "").strip()
    match = re.match(r'^([一二三四五六七八九十〇零0-9]{1,3})', raw_input)
    if match:
        number_part = match.group(1)
        if number_part.isdigit():
            return number_part
        else:
            arabic = convert_chinese_numerals(number_part)
            if arabic:
                return arabic
    return None

@app.route('/', methods=['GET'])
def index():
    raw_id = request.args.get('id', '').strip()
    image_url = None
    error = None

    if raw_id:
        qian_id = normalize_input(raw_id)
        if qian_id:
            filename = f"{qian_id}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                image_url = url_for('static', filename=f'qian/{filename}')
            else:
                error = f"编号 {qian_id} 的签条不存在。"
        else:
            error = f"无法识别签号“{raw_id}”。请使用阿拉伯数字或中文数字。"

    return render_template('index.html', image_url=image_url, error=error)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    message = None
    if request.method == 'POST':
        qian_id = request.form.get('id')
        file = request.files.get('file')
        if qian_id and file:
            filename = f"{qian_id}.jpg"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            message = f"编号 {qian_id} 的签条上传成功！"
        else:
            message = "请填写签号并选择图片。"
    return render_template('upload.html', message=message)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
