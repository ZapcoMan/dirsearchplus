import re, os, sys, csv
import time
import subprocess
from urllib.parse import urlparse
# 引入dirsearch的日志和终端输出模块
from lib.view.terminal import output
from lib.view.colors import set_color

def start_ehole():
    """
    启动EHole指纹识别工具，根据配置文件中的URL进行扫描。

    该函数会读取resources/bypass403_url.txt中的目标URL，并尝试从dir_file_path.txt或CSV报告中提取更多路径，
    然后使用EHole对这些路径执行指纹识别。如果无法获取额外路径，则仅对根目录进行扫描。

    参数:
        无显式参数，依赖于以下文件和环境：
        - resources/bypass403_url.txt：包含待扫描的目标URL
        - dir_file_path.txt（可选）：指向一个包含目录扫描结果的文件
        - reports/{domain}.csv（可选）：已有的扫描结果CSV文件

    返回值:
        无返回值。直接调用EHole命令行工具执行扫描并输出结果。
    """
    try:
        # 获取当前工作目录
        path_get = os.getcwd()

        # 首先读取resources/bypass403_url.txt中的URL用于根目录扫描
        with open(os.path.join(path_get, "resources", "bypass403_url.txt"), 'r') as domains:
            domain_url = domains.read().strip()

        if not domain_url:
            output.error("错误: resources/bypass403_url.txt为空")
            return

        # 创建临时文件用于扫描
        ehole_file = os.path.join(path_get, 'lib','ehole', 'ehole.txt')
        open(ehole_file, 'w').close()  # 清空文件

        # 解析域名用于输出文件名
        parsed_url = urlparse(domain_url)
        domain1 = parsed_url.netloc
        domain1 = domain1.replace('.', '_').replace(':', '_')

        # 确保reports目录存在
        reports_dir = os.path.join(path_get, 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        try:
            # 尝试执行正常扫描逻辑（读取dir_file_path.txt和CSV文件）
            current_time = time.strftime("%H:%M:%S")
            message = f'[{current_time}]尝试执行正常扫描.....'
            output.new_line(set_color(message, fore="yellow"))

            # 读取dir_file_path.txt
            if os.path.exists('dir_file_path.txt'):
                with open('dir_file_path.txt') as f:
                    f1 = f.read().strip()

                # 读取扫描结果文件中的URL
                if f1 and os.path.exists(f1):
                    with open(f1) as d:
                        d1 = d.readlines()
                    for dd in d1:
                        dd = dd.replace('\n', '').replace('\r', '')
                        if "404   " not in dd and ' 0B ' not in dd:
                            reg = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                            url = re.findall(reg, dd)
                            try:
                                with open(ehole_file, 'a+') as ehole:
                                    ehole.write(url[0] + '\n')
                                    
                                # 使用与dirsearch一致的输出格式显示找到的URL
                                current_time = time.strftime("%H:%M:%S")
                                message = f"[{current_time}]{url[0]}"
                                output.new_line(set_color(message, fore="green"))
                            except:
                                pass

            # 尝试读取CSV文件中的URL
            csv_file = os.path.join(reports_dir, domain1 + '.csv')
            if os.path.exists(csv_file):
                # 使用更健壮的方式处理文件编码
                try:
                    # 首先尝试使用 UTF-8 编码
                    file_csv = open(csv_file, 'r', encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        # 如果 UTF-8 失败，尝试使用 GB18030 编码
                        file_csv = open(csv_file, 'r', encoding='GB18030')
                    except UnicodeDecodeError:
                        # 如果两种编码都失败，使用系统默认编码并忽略错误
                        file_csv = open(csv_file, 'r', encoding='utf-8', errors='ignore')
                
                rows = csv.reader(file_csv)
                for row in rows:
                    if len(row) > 0 and 'http' in row[0]:
                        try:
                            with open(ehole_file, 'a+') as ehole:
                                ehole.write(row[0] + '\n')
                                
                            # 使用与dirsearch一致的输出格式显示找到的URL
                            current_time = time.strftime("%H:%M:%S")
                            message = f"[{current_time}]{row[0]}"
                            output.new_line(set_color(message, fore="green"))
                        except:
                            pass
                file_csv.close()

            # 检查是否有正常扫描到的URL
            with open(ehole_file, 'r') as f:
                urls = f.read().strip()

            # 如果正常扫描没有找到任何URL，或者文件不存在，则只扫描根目录
            if not urls:
                raise FileNotFoundError("目录扫描未发现路径")

        except FileNotFoundError as e:
            output.new_line(set_color(f"[提示]: {str(e)}，将只扫描根目录的指纹", fore="yellow"))
            # 只写入根URL到临时文件
            with open(ehole_file, 'w') as f:
                f.write(domain_url + '\n')

        # 根据操作系统类型执行不同命令
        win_mac = sys.platform
        if win_mac == "darwin":  # macOS
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]正在扫描指纹: {domain_url}"
            output.new_line(set_color(message, fore="cyan"))
            # 确保ehole可执行
            ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole")
            os.chmod(ehole_executable, 0o755)  # 使用数字权限表示法
            # 执行ehole扫描
            subprocess.run([ehole_executable, "finger", "-l", ehole_file])
        elif win_mac == "win32":  # Windows
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]正在扫描指纹: {domain_url}"
            output.new_line(set_color(message, fore="cyan"))
            ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole.exe")
            json_output = os.path.join(reports_dir, f"{domain1}.json")
            subprocess.run([ehole_executable, "finger", "-l", ehole_file, "-o", json_output])
        else:  # Linux或其他系统
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]正在扫描指纹: {domain_url}"
            output.new_line(set_color(message, fore="cyan"))
            ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole")
            os.chmod(ehole_executable, 0o755)  # 使用数字权限表示法
            subprocess.run([ehole_executable, "finger", "-l", ehole_file])

        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}]指纹扫描完成！"
        output.new_line(set_color(message, fore="green"))

    except Exception as e:
        output.error(f"扫描过程中发生错误: {str(e)}")
        # 错误发生时，也只扫描根目录的指纹
        try:
            path_get = os.getcwd()
            with open(os.path.join(path_get, "resources", "bypass403_url.txt"), 'r') as domains:
                domain_url = domains.read().strip()

            if domain_url:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}]尝试只扫描根目录的指纹: {domain_url}"
                output.new_line(set_color(message, fore="yellow"))
                ehole_file = os.path.join(path_get, 'lib', 'ehole', 'ehole.txt')
                with open(ehole_file, 'w') as f:
                    f.write(domain_url + '\n')

                win_mac = sys.platform
                if win_mac == "darwin":
                    ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole")
                    os.chmod(ehole_executable, 0o755)  # 使用数字权限表示法
                    subprocess.run([ehole_executable, "finger", "-l", ehole_file])
                elif win_mac == "win32":
                    ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole.exe")
                    subprocess.run([ehole_executable, "finger", "-l", ehole_file])
                else:
                    ehole_executable = os.path.join(path_get, "lib", "ehole", "ehole")
                    os.chmod(ehole_executable, 0o755)  # 使用数字权限表示法
                    subprocess.run([ehole_executable, "finger", "-l", ehole_file])
        except Exception as inner_e:
            output.error(f"尝试只扫描根目录指纹时也发生错误: {str(inner_e)}")