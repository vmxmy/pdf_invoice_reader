import pandas as pd
import pdfplumber
import os

# 设置目录路径
directory = input("请输入文件夹路径：")
if directory == "":
    directory = './uploads/'

# 创建空的DataFrame来存储PDF文本信息
df_list = []

# 遍历目录下的所有文件invoice
for filename in os.listdir(directory):
    if filename.lower().endswith('.pdf'):
        # 打开PDF文件
        with pdfplumber.open(os.path.join(directory, filename)) as pdf:
            # 遍历每一页并提取文本信息
            content = ''
            for page in pdf.pages:
                content += page.extract_text()

            # 将文件名和提取出的文本信息添加到列表中
            df_list.append(pd.DataFrame({'filename': [filename], 'content': [content]}))

# 使用concat函数将所有的DataFrame拼接成一个
df = pd.concat(df_list, ignore_index=True)

#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',1000)

# 使用replace()函数将所有冒号替换为冒号
df = df.replace({r'：': ':'}, regex=True)
# 使用replace()函数将所有空格替换为空字符串
df['content'] = df['content'].str.replace(' ', '')
df['content'] = df['content'].str.replace('\n', '')

import re

for index, raw in df.iterrows():
    #提取content列的文本内容
    text = raw['content']
    
    print("文件名",raw['filename'])
    
    # 提取发票代码
    #df.loc[index, 'invoice_code'] = re.search(r'发票代码:(\d+)', text).group(1)
    #print("发票代码:", df.loc[index, 'invoice_code'])

    # 提取发票号码
    df.loc[index, 'invoice_num'] = re.search(r'发票号码.(\d+)', text).group(1)
    print("发票号码:", df.loc[index, 'invoice_num'])

    # 提取发票开具日期
    df.loc[index, 'invoice_date'] = re.search(r'开票日期:(\d+年\d+月\d+日)', text).group(1)
    print("开票日期:", df.loc[index, 'invoice_date'])

    # 提取购买方名称,销售方名称
    company_name = re.findall(r'名称:(\D.+?[司店龙馆局])', text)
    print(company_name)
    df.loc[index, 'buyer_name'] = company_name[0]
    print("购买方名称:", df.loc[index, 'buyer_name'])
    df.loc[index, 'seller_name'] = company_name[-1]
    print("销售方名称:", df.loc[index, 'seller_name'])


    # 提取购买方纳税人识别号
    buyer_tax_id = re.search(r'(?<=[\D])9[A-Z0-9]{17}', text)
    print(buyer_tax_id)
    df.loc[index, 'buyer_tax_id'] = buyer_tax_id[0]
    print("购买方纳税人识别号:", df.loc[index, 'buyer_tax_id'])


    # 提取服务名称
    df.loc[index, 'service_name'] = re.search(r'(?<=税额).*?(?:费|服务)', text).group()
    print("服务名称:", df.loc[index, 'service_name'])

    # 提取价税合计金额
    total_price = re.findall(r'[¥￥]\d+(?:\.\d+)?', text)
    df.loc[index, 'total_price']= total_price[-1]
    print("价税合计:", total_price[-1])
    
    print("#"*50)

    # 遍历 filename 列的每一行，并将文件重命名为 1+2+3.pdf 的格式
for index, row in df.iterrows():
    old_name = row['filename']
    new_name = row['invoice_date'] + row['seller_name'] + row['service_name'] + row['invoice_num'] + "---" +row['total_price'] + '.pdf'
    new_name = new_name.replace('*','-')
    if not os.path.exists(directory + new_name):
        os.rename(directory + old_name,directory + new_name)
        print(index,'o:',old_name,'===>>>',new_name,'\n')
    else:
        print(index,'x:',new_name,'已存在\n')