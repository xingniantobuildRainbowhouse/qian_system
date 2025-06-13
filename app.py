from flask import Flask, render_template, request, redirect, session, url_for, jsonify 
import os
import re
import glob


app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = os.path.join('static', 'qian')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ========== 工具函数 ==========
CHINESE_NUM_MAP = {
    '零': 0, '〇': 0,
    '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10
}
REVERSE_NUM_MAP = {v: k for k, v in CHINESE_NUM_MAP.items() if v <= 9}

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
    if len(num_str) != 2 or not num_str.isdigit():
        return None
    result = ''
    for ch in num_str:
        digit = int(ch)
        result += REVERSE_NUM_MAP.get(digit, '')
    return result if len(result) == 2 else None

def convert_chinese_numerals(text):
    text = text.strip()
    if re.fullmatch(r'[一二三四五六七八九十〇零]+', text):
        if '十' in text:
            parts = text.split('十')
            left = CHINESE_NUM_MAP.get(parts[0], 1) if parts[0] else 1
            right = CHINESE_NUM_MAP.get(parts[1], 0) if len(parts) > 1 and parts[1] else 0
            number = left * 10 + right
        else:
            number = sum(CHINESE_NUM_MAP.get(c, 0) * (10 ** i) for i, c in enumerate(reversed(text)))
        return arabic_to_chinese_str(f"{number:02d}")
    return None

def parse_input(user_input):
    cleaned = user_input.replace(" ", "").strip()
    match = re.match(r'^([0-9]{2}|[一二三四五六七八九十〇零]{1,3})(.*)$', cleaned)
    if not match:
        return None, None

    number_part = match.group(1)
    project_part = match.group(2)

    chinese_number = arabic_to_chinese_str(number_part) if number_part.isdigit() else convert_chinese_numerals(number_part)
    chinese_project = match_project_name(project_part)
    return chinese_number, chinese_project

# ========== 页面路由 ==========
@app.route('/')
def pay_online():
    return render_template('pay_online.html')

@app.route('/confirm', methods=['POST'])
def confirm():
    session['paid'] = True
    return redirect(url_for('index'))

@app.route('/pay_store')
def pay_store():
    branch = request.args.get('branch', '')
    return render_template('pay_store.html', branch=branch)

@app.route('/confirm_store', methods=['POST'])
def confirm_store():
    session['paid'] = True
    return redirect(url_for('index'))

@app.route('/index')
def index():
    if not session.get('paid'):
        return redirect(url_for('pay_online'))
    return render_template('index.html')

@app.route('/query')
def query():
    if not session.get('paid'):
        return redirect(url_for('pay_online'))

    branch = session.get('branch', 'unknown')
    raw_id = request.args.get('id', '').strip()
    image_url = None
    error = None

    if raw_id:
        chinese_number, chinese_project = parse_input(raw_id)
        if chinese_number and chinese_project:
            pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{chinese_number}*{chinese_project}*.jpg")
            matches = glob.glob(pattern)
            if matches:
                image_url = '/' + matches[0].replace('\\', '/')
            else:
                error = "未找到对应的签条，请检查输入。"
        else:
            error = "输入格式错误，请重新填写。"

    # 查询一次后清除 session 权限
    session.pop('paid', None)
    return render_template('index.html', image_url=image_url, error=error)

# ========== 测试设置付款记录 ==========
@app.route('/mock_pay/<branch>/<visitor_id>', methods=['GET'])
def mock_pay(branch, visitor_id):
    # 模拟收到付款，设置 Redis 中的标记（有效期10分钟）
    key = f"paid:{branch}:{visitor_id}"
    redis_client.setex(key, 600, '1')  # 10分钟过期
    return f"Mock paid for {visitor_id} at {branch}"

# ========== 主程序入口 ==========
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
