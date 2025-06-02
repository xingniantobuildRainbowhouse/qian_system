from flask import Flask, render_template, request, url_for
import os
import re
import glob

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'qian_imgs')  # 修改文件夹路径
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
REVERSE_NUM_MAP = {v: k for k, v in CHINESE_NUM_MAP.items() if v <= 9}

# 简体 → 繁体项目词映射（含模糊别名）
TERM_ALIASES = {
    '家宅运气': ['家宅運氣'],
    '财富增损': ['財富增損'],
    '谋望': ['謀望'],
    '人际关系': ['人際關係'],
    '诉讼是非': ['訴訟是非'],
    '出行': ['出行'],
    '疾病': ['疾病'],
    '风水厄运': ['風水厄運'],
    '失物': ['失物'],
    '请托': ['請託'],
    '婚姻': ['婚姻']
}

# 简体转繁体项目名
def match_project_name(input_name):
    input_name = input_name.replace(" ", "").strip()
    for simp, trad_list in TERM_ALIASES.items():
        if simp in input_name:
            return trad_list[0]
        for alias in trad_list:
            if alias in input_name:
                return alias
    return None

# 将阿拉伯数字（如22）转成“二二”
def arabic_to_chinese_str(num_str):
    if len(num_str) != 2 or not num_str.isdigit():
        return None
    result = ''
    for ch in num_str:
        ch = int(ch)
        if ch in REVERSE_NUM_MAP:
            result += REVERSE_NUM_MAP[ch]
        else:
            return None
    return result

# 提取数字部分 + 项目名称部分
def parse_input(user_input):
    user_input = user_input.replace(" ", "").strip()
    match = re.match(r'^([0-9]{2}|[一二三四五六七八九十〇零]{1,3})(.*)$', user_input)
    if not match:
        return None, None

    number_part = match.group(1)
    project_part = match.group(2)

    if number_part.isdigit():
        chinese_number = arabic_to_chinese_str(number_part)
    else:
        chinese_number = convert_chinese_numerals(number_part)

    chinese_project = match_project_name(project_part)
    return chinese_number, chinese_project

# 中文数字字符串 → 阿拉伯数字（支持“二十三”“十三”“十七”“十”）
def convert_chinese_numerals(text):
    if not text:
        return None
    result = ''
    if re.fullmatch(r'[一二三四五六七八九十〇零]+', text):
        if '十' in text:
            parts = text.split('十')
            left = CHINESE_NUM_MAP.get(parts[0], 1) if parts[0] else 1
            right = CHINESE_NUM_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            number = left * 10 + right
        else:
            number = int(''.join(str(CHINESE_NUM_MAP[c]) for c in text))
        return arabic_to_chinese_str(f"{number:02d}")
    return None

@app.route('/', methods=['GET'])
def index():
    raw_id = request.args.get('id', '').strip()
    image_url = None
    error = None

    if raw_id:
        chinese_number, chinese_project = parse_input(raw_id)
        if chinese_number and chinese_project:
            # 模糊匹配文件（有无空格）
            pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{chinese_number}*{chinese_project}*.jpg")
            candidates = glob.glob(pattern)
            if candidates:
                rel_path = os.path.relpath(candidates[0], 'static')
                image_url = url_for('static', filename=rel_path)
            else:
                error = f"签条“{chinese_number} {chinese_project}”不存在。"
        else:
            error = f"无法识别“{raw_id}”。请使用正确的签号和项目名。"

    return render_template('index.html', image_url=image_url, error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
