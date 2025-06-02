from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)

# 图片存放路径
UPLOAD_FOLDER = os.path.join('static', 'qian')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET'])
def index():
    qian_id = request.args.get('id')
    image_url = None
    error = None
    if qian_id:
        filename = f"{qian_id}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            image_url = url_for('static', filename=f'qian/{filename}')
        else:
            error = f"编号 {qian_id} 的签条不存在。"
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
    app.run(debug=True)
