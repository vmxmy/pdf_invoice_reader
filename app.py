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
                # 获取文件保存的路径
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                print(uploaded_file," saved")
                
                with pdfplumber.open(uploaded_file) as pdf:
                    text = ''
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:  # 确保页面有文本
                            text += page_text + "\n\n"
                # 将文件名和文本作为元组添加到结果列表中
                results.append((uploaded_file.filename, text))
             
        # 将results 转换成DataFrame
        df_results = pd.DataFrame(results, columns=['filename', 'content'])

        # 使用replace()函数将所有冒号替换为冒号
        df_results = df_results.replace({r'：': ':'}, regex=True)
        # 使用replace()函数将所有空格替换为空字符串
        df_results['content'] = df_results['content'].str.replace(' ', '')
        # 将￥替换为¥
        df_results['content'] = df_results['content'].str.replace('￥', '¥')
        # 将（和）替换成(和)
        df_results['content'] = df_results['content'].str.replace('（', '(')
        df_results['content'] = df_results['content'].str.replace('）', ')')

        # 使用正则表达式提取信息,并写入dataframe
        for index, raw in df_results.iterrows():
            #提取content列的文本内容
            text = raw['content']

            # 提取开票日期
            invoice_date_pattern = r"开票日期:(?P<date>\d{4}年\d{2}月\d{2}日)"
            match = re.search(invoice_date_pattern, text)
            if match:
                df_results.loc[index, 'invoice_date'] = match.group('date')


            # 提取总金额
            total_amount_pattern = r"小写\)¥(?P<amount>\d+\.\d{2})"
            match = re.search(total_amount_pattern, text)
            if match:
                df_results.loc[index, 'total_amount'] = match.group('amount')

            # 提取服务内容
            service_content_pattern = r'\*([\u4e00-\u9fa5]+)\*'
            match = re.search(service_content_pattern, text)
            if match:
                df_results.loc[index, 'service_content'] = match.group(1)
            
            # 提取销售方名称
            seller_pattern = r"杭州趣链科技有限公司.*名称:([\u4e00-\u9fa5]+)"
            match = re.findall(seller_pattern, text, re.DOTALL)
            if match:
                df_results.loc[index, 'seller'] = match[-1]

            # 提取发票号码
            invoice_number_pattern = r"发票号码:(?P<number>\d+)"
            match = re.search(invoice_number_pattern, text)
            if match:
                df_results.loc[index, 'invoice_number'] = match.group('number')

        # 创建一个DataFrame，包含提取的信息
        df_info = df_results[['filename', 'invoice_date', 'total_amount', 'service_content', 'seller', 'invoice_number']]
        
        # 确保文件名中不含不合法字符
        def sanitize_filename(filename):
            return "".join([c for c in filename if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
        # 以 invoice_date+total_amount+service_content+seller重命名文件
        # 遍历 filename 列的每一行，并将文件重命名为 1+2+3.pdf 的格式
        for index, row in df_info.iterrows():
            path = app.config['UPLOAD_FOLDER']
            old_name_path = os.path.join(path, row['filename'])
            new_name = sanitize_filename(row['invoice_date'] + row['service_content'] +row['total_amount']+ row['seller'] + row['invoice_number'] ) + '.pdf'
            new_name_path = os.path.join(path, new_name)
            if not os.path.exists(new_name_path):
                os.rename(old_name_path, new_name_path)
                print(index,'o:',old_name_path,'===>>>',new_name_path,'\n', flush=True)
            else:
                os.remove(old_name_path)
                print(index,'x:',new_name_path,'已存在\n', flush=True)

        df_html = df_info.to_html(index=False, classes='table table-striped')
        # 将结果发送到新的模板进行渲染
        return render_template('results.html', tables = df_html)
    return "Failed to read PDFs"

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000, debug=True)
