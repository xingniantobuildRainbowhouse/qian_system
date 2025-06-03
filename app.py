from flask import Flask, render_template, request, redirect, session, url_for
import os
import re
import glob

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 替换为安全的密钥字符串

UPLOAD_FOLDER = os.path.join('static', 'qian') # 你的图片存放目录
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

def match_project_name(input_name):
    input_name = input_name.replace(" ", "").strip()
    for simp, trad_list in TERM_ALIASES.items():
        if simp in input_name:
            return trad_list[0]
        for alias in trad_list:
            if alias in input_name:
                return alias
    return None

def arabic_to_chinese_str(num_str):
    # 把两位阿拉伯数字转成两位中文数字字符串，如 "22"->"二二"
    if len(num_str) != 2 or not num_str.isdigit():
        return None
    result = ''
    for ch in num_str:
        digit = int(ch)
        if digit in REVERSE_NUM_MAP:
            result += REVERSE_NUM_MAP[digit]
        else:
            return None
    return result

def convert_chinese_numerals(text):
    # 将中文数字字符串转成两位中文数字字符串，支持“二十三”“十三”“十七”“十”等
    if not text:
        return None
    text = text.strip()
    if re.fullmatch(r'[一二三四五六七八九十〇零]+', text):
        if '十' in text:
            parts = text.split('十')
            left = CHINESE_NUM_MAP.get(parts[0], 1) if parts[0] else 1
            right = CHINESE_NUM_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            number = left * 10 + right
        else:
            number = 0
            for c in text:
                number = number * 10 + CHINESE_NUM_MAP.get(c, 0)
        return arabic_to_chinese_str(f"{number:02d}")
    return None

def parse_input(user_input):
    # 提取数字 + 项目名，返回格式为(两位中文数字, 繁体项目名)
    cleaned = user_input.replace(" ", "").strip()
    match = re.match(r'^([0-9]{2}|[一二三四五六七八九十〇零]{1,3})(.*)$', cleaned)
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

@app.route('/')
def pay():
    return render_template('pay.html')

@app.route('/query', methods=['GET'])
def query():
    # 如果没有付费记录，跳转付款页
    if not session.get('paid'):
        return redirect(url_for('pay'))

    raw_id = request.args.get('id', '').strip()
    image_url = None
    error = None

    if raw_id:
        chinese_number, chinese_project = parse_input(raw_id)
        print(f"解析结果: 数字='{chinese_number}', 项目='{chinese_project}'")  # 打印解析结果

        if chinese_number and chinese_project:
            pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{chinese_number}*{chinese_project}*.jpg")
            print(f"匹配模式: {pattern}")
            candidates = glob.glob(pattern)
            print(f"匹配到的文件列表: {candidates}")

            if candidates:
                rel_path = os.path.relpath(candidates[0], 'static')
                image_url = url_for('static', filename=rel_path)
                session['paid'] = False  # 查询完自动清除一次查询权限
            else:
                error = f"签条“{chinese_number} {chinese_project}”不存在。"
        else:
            error = f"无法识别“{raw_id}”。请使用正确的签号和项目名。"

    return render_template('index.html', image_url=image_url, error=error)

@app.route('/confirm', methods=['POST'])
def confirm():
    session['paid'] = True
    return redirect(url_for('query'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
