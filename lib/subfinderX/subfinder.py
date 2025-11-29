import subprocess
import argparse
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 引入 dirsearch 的日志模块
from lib.core.logger import logger, enable_logging
from lib.core.data import options
from lib.view.colors import set_color


def remove_locked_files(domain):
    """
    删除可能被锁定的输出文件
    """
    if not domain:
        return
        
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        return
        
    # 生成可能的文件名
    files_to_remove = [
        os.path.join(output_dir, f"{domain}.xlsx"),
        os.path.join(output_dir, f"{domain}_http.xlsx")
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                current_time = time.strftime("%H:%M:%S")
                print(set_color(f"[{current_time}][+] 已删除可能锁定的文件: {os.path.basename(file_path)}", "green"))
            except PermissionError:
                current_time = time.strftime("%H:%M:%S")
                print(set_color(f"[{current_time}][-] 无法删除文件 {os.path.basename(file_path)}，文件可能正在被使用", "yellow"))
            except Exception as e:
                current_time = time.strftime("%H:%M:%S")
                print(set_color(f"[{current_time}][-] 删除文件 {os.path.basename(file_path)} 时出错: {str(e)}", "red"))


def run_subfinder(domain=None, file=None, deep=5, dict_file="test.txt", fuzz_data=None,
                  enable_http=False, random_check=False, finger_path="finger.json",
                  next_dict="mini_names.txt"):
    """
    运行 subfinder-x 工具进行子域名爆破
    """
    # 删除可能被锁定的输出文件
    remove_locked_files(domain)
    
    # 构建完整的可执行文件路径
    exe_path = os.path.join(os.path.dirname(__file__), "subfinder-x.exe")
    # 设置工作目录为subfinderX目录
    work_dir = os.path.dirname(__file__)
    cmd = [exe_path]

    if domain:
        cmd.extend(["-u", domain])
    if file:
        cmd.extend(["-f", file])
    if deep != 5:
        cmd.extend(["-s", str(deep)])
    if dict_file != "test.txt":
        cmd.extend(["-d", dict_file])
    else:
        # 确保使用正确的字典文件路径
        dict_file_path = os.path.join(work_dir, "dict", dict_file)
        if os.path.exists(dict_file_path):
            cmd.extend(["-d", dict_file])
            
    if fuzz_data:
        cmd.extend(["-fd", fuzz_data])
    if enable_http:
        cmd.append("-x")
    if random_check:
        cmd.extend(["-c", "true"])  # 修正：为 -c 参数提供值 "true"
    if finger_path != "finger.json":
        cmd.extend(["-fp", finger_path])
    else:
        # 确保使用正确的指纹库文件路径
        finger_file_path = os.path.join(work_dir, finger_path)
        if os.path.exists(finger_file_path):
            cmd.extend(["-fp", finger_path])
    if next_dict != "mini_names.txt":
        cmd.extend(["-n", next_dict])
    else:
        # 确保使用正确的二级字典文件路径
        next_dict_path = os.path.join(work_dir, next_dict)
        if os.path.exists(next_dict_path):
            cmd.extend(["-n", next_dict])

    # 使用 dirsearch 的日志模块替代 print，统一颜色和风格
    current_time = time.strftime("%H:%M:%S")
    print(set_color(f"[{current_time}][+] " + "执行命令: %s" % " ".join(cmd), "green"))
    
    try:
        # 明确指定编码为 utf-8 来避免 gbk 解码错误
        # 在subfinderX目录中执行命令，确保能正确访问finger.json和dict目录
        print(set_color(f"[{current_time}][+] 开始执行SubFinder扫描，请稍候...", "green"))
        print(set_color(f"[{current_time}][+] 注意：子域名扫描可能需要一些时间，请耐心等待... ", "green"))

        # 使用Popen代替run以便更好地控制进程
        process = subprocess.Popen(cmd, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding='utf-8')

        # 定时提示机制
        start_time = time.time()
        check_interval = 300  # 每5分钟检查一次
        last_check = start_time

        while process.poll() is None:  # 进程仍在运行
            current_time = time.time()
            if current_time - last_check >= check_interval:
                elapsed_minutes = int((current_time - start_time) / 60)
                print(set_color(f"[{time.strftime('%H:%M:%S')}][+] 扫描已持续 {elapsed_minutes} 分钟，请耐心等待...", "green"))
                last_check = current_time
            time.sleep(10)  # 每10秒检查一次进程状态

        # 获取最终结果
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            print(set_color(f"[{time.strftime('%H:%M:%S')}][+] 扫描成功完成", "green"))
            if stdout:
                # 统一输出格式，使用 dirsearch 的输出风格
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        current_time = time.strftime("%H:%M:%S")
                        print(set_color(f"[{current_time}]     " + line.strip(), "green"))
        else:
            print(set_color(f"[{time.strftime('%H:%M:%S')}][-] 扫描过程中出现错误", "red"))
            if stderr:
                # 错误信息也使用统一的日志格式
                for line in stderr.strip().split('\n'):
                    if line.strip():
                        current_time = time.strftime("%H:%M:%S")
                        print(set_color(f"[{current_time}]     " + line.strip(), "red"))
            
    except FileNotFoundError:
        current_time = time.strftime("%H:%M:%S")
        print(set_color(f"[{current_time}][-] 未找到 subfinder-x.exe 可执行文件，请确认路径是否正确", "red"))
    except Exception as e:
        current_time = time.strftime("%H:%M:%S")
        print(set_color(f"[{current_time}][-] 未知错误: {str(e)}", "red"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subfinder-X 子域名扫描工具调用脚本")

    parser.add_argument("-u", "--domain", help="指定目标域名")
    parser.add_argument("-f", "--file", help="用于指定包含多个目标域名的文件")
    parser.add_argument("-s", "--deep", type=int, default=5, help="指定扫描的深度(默认为5)")
    parser.add_argument("-d", "--dict", dest="dict_file", default="test.txt", help="指定字典文件(默认:test.txt)")
    parser.add_argument("-fd", "--fuzz_data", help="设置FUZZ数据")
    parser.add_argument("-x", "--enable_http", action="store_true", help="启用HTTP扫描和指纹识别")
    parser.add_argument("-c", "--random_check", action="store_true", help="是否开启随机子域名检查")
    parser.add_argument("-fp", "--finger_path", default="finger.json", help="指定指纹库路径(默认:finger.json)")
    parser.add_argument("-n", "--next", dest="next_dict", default="mini_names.txt", help="指定二级字典文件(默认:mini_names.txt)")

    args = parser.parse_args()

    run_subfinder(
        domain=args.domain,
        file=args.file,
        deep=args.deep,
        dict_file=args.dict_file,
        fuzz_data=args.fuzz_data,
        enable_http=args.enable_http,
        random_check=args.random_check,
        finger_path=args.finger_path,
        next_dict=args.next_dict
    )