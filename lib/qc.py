import os
import re
import tldextract
from colorama import init, Fore, Style
re_lists=[]

init()

def pass403_qc():
    """
    处理403绕过结果，去除相同页面长度的无效结果并输出有效结果

    该函数主要功能包括：
    1. 读取resources/bypass403_url.txt和jsfind403list.txt中的URL
    2. 提取URL对应的域名文件，分析其中的响应数据
    3. 根据页面大小(SIZE)去重，过滤掉403和404状态码的结果
    4. 输出符合条件的有效结果，并删除临时域名文件

    参数: 无

    返回值: 无
    """
    urls=[]
    try:
        print(Fore.GREEN + Style.BRIGHT +'\nRemove invalid results with the same page length'+Style.RESET_ALL)
        # 读取主URL文件内容
        with open('resources/bypass403_url.txt') as f:
            url = f.read()
        urls.append(url)

        # 读取JS发现的URL列表
        with open('jsfind403list.txt') as js_f:
            js_url=js_f.readlines()
        for js_i in js_url:
            js_i=js_i.replace('\n','').replace('\r','')
            urls.append(js_i)

        # 遍历所有URL进行处理
        for url1 in urls:
            file_domain = tldextract.extract(url1).domain
            # 读取对应域名的结果文件
            with open(file_domain + '.txt') as f:
                f1 = f.readlines()

            # 提取每行中的SIZE信息用于去重
            for i in f1:
                i = i.replace('\n', '').replace('\r', '')
                if 'Header= {' in i:
                    re_i = re.findall('SIZE: (.*?)---Header=', i)
                    re_str = "".join(re_i)
                if 'Header= {' not in i:
                    re_str = i[i.rfind('SIZE: '):]
                if re_str != '':
                    re_lists.append(re_str)
            list2 = list(set(re_lists))

            # 根据去重后的SIZE值筛选并输出有效结果
            for ii in list2:
                for p in f1:
                    p = p.replace('\n', '')
                    if ii in p:
                        if "---Header= {" in p:
                            p = p.replace('---', '\n')
                            p = p+'\n'
                        if "STATUS: 403" in p:
                            pass
                        elif "STATUS: 404" in p:
                            pass
                        else:
                            print(p)
                        break
            # 删除已处理的域名文件
            os.remove(file_domain + '.txt')
    except:
        pass

