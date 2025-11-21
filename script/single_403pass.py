from lib.pass403 import Arguments,Program
from lib.qc import pass403_qc
import argparse


def bypass(url,path):
    '''
    执行403绕过功能的主要函数

    参数:
        url (str): 目标网站的URL地址
        path (str): URL路径部分

    返回值:
        无返回值

    功能说明:
        该函数通过创建Arguments和Program对象来初始化并执行403绕过程序，
        主要用于测试目标URL的403访问限制绕过方法
    '''
    try:
        argument = Arguments(url, None, path, None)
        program = Program(argument.return_urls(), argument.return_dirs())
        program.initialise()
    except:
        pass



if __name__ == '__main__':
    # 创建命令行参数解析器，用于接收用户输入的URL和路径参数
    parser = argparse.ArgumentParser(description='help')
    parser.add_argument("-u", "--url", help="url", default='')
    parser.add_argument("-p", "--path", help="url path", default='')
    args = parser.parse_args()

    # 获取并保存URL参数到文件
    url=args.url
    with open('../bypass403_url.txt', 'w') as f:
        f.write(url)

    # 获取路径参数并调用绕过函数
    path=args.path
    bypass(url,path)

    # 执行403绕过质量检查
    pass403_qc()


