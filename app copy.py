from flask import Flask, render_template, request
import pdfplumber
from werkzeug.utils import secure_filename
import re
import pandas as pd
import os

# 定义正则表达式
date_regex = r'开票日期：(\d{4}年\d{2}月\d{2}日)'
total_amount_regex = r'合 计 ¥(\d+\.\d{2})'
service_content_regex = r'\*(.*?)\*'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制文件大小为16MB
# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def upload_form():
    # 返回上传模板
    return render_template('upload_multiple.html')

@app.route('/uploader', methods=['POST'])
def upload_file():
    # 如果是POST请求，则执行以下操作
    if request.method == 'POST':
        # 获取上传的文件
        uploaded_files = request.files.getlist('file[]')
        results = []
        # 遍历文件，提取文本
        for uploaded_file in uploaded_files:
            if uploaded_file.filename != '':
                filename = secure_filename(uploaded_file.filename)
                # 在文件保存之前，添加以下代码：
                # 使用os模块将文件保存到默认文件夹
                # 获取文件保存的路径
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                print(uploaded_file," saved")
   
        return "done" 
    return "Failed to read PDFs"

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5001, debug=True)