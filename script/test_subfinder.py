# test_subfinder_scan.py
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 创建测试用的 bypass403_url.txt 文件
os.makedirs('resources', exist_ok=True)
with open('resources/bypass403_url.txt', 'w') as f:
    f.write('example.com')

# 导入并调用函数
from dirsearchplus import subfinder_scan

if __name__ == "__main__":
    # subfinder_scan()
    url = "http://www.baidu.com/"  # 测试用的 url
    # 去掉 url 前面的 https:// 或者 http:// 以及最后的 /
    url = url.replace("https://", "").replace("http://", "")
    url = url.rstrip("/")
    print(url)
