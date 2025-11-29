#!/usr/bin/env python3

import re
import time
from colorama import init, Fore, Style

import lib
from lib.controller.controller import Controller
from lib.pass403_optimized import OptimizedArguments as Arguments, OptimizedProgram as Program
from lib.qc import pass403_qc

import queue


import sys,os

from pkg_resources import DistributionNotFound, VersionConflict

from lib.core.data import options
from lib.core.exceptions import FailedDependenciesInstallation
from lib.core.installation import check_dependencies, install_dependencies
from lib.core.settings import OPTIONS_FILE
from lib.parse.config import ConfigParser
from lib.view.colors import set_color
from lib.view.terminal import output

init()

if sys.version_info < (3, 7):
    sys.stdout.write("抱歉，dirsearch需要Python 3.7或更高版本\n")
    sys.exit(1)

config = ConfigParser()
config.read(OPTIONS_FILE)

if config.safe_getboolean("options", "check-dependencies", False):
    try:
        check_dependencies()
    except (DistributionNotFound, VersionConflict):
        option = input("缺少运行所需的依赖项。\n"
                       "您希望dirsearch自动安装它们吗？[Y/n] ")

        if option.lower() == 'y':
            print("正在安装所需的依赖项...")

            try:
                install_dependencies()
            except FailedDependenciesInstallation:
                print("无法安装dirsearch依赖项，请尝试手动安装。")
                exit(1)
        else:
            config.set("options", "check-dependencies", "False")

            with open(OPTIONS_FILE, "w") as fh:
                config.write(fh)


##

def bypass():
    """优化的403bypass函数"""
    with open('resources/bypass403_url.txt') as f:
        bypass403_url = f.read().strip()

    # 收集所有需要处理的路径
    paths_to_process = []
    while not q.empty():
        path_403 = q.get()
        paths_to_process.append(path_403)

    if not paths_to_process:
        return
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}] 开始处理 {len(paths_to_process)} 个403路径" + '\n'
    print(set_color(message, fore="green"), end='')


    # 使用优化版本处理
    try:
        argument = Arguments(bypass403_url, None, None, None)
        program = Program(argument.return_urls(), paths_to_process, max_workers=20)
        program.initialise()
    except Exception as e:
        print(f"bypass处理出错: {e}")
        # 如果处理失败，尝试逐个处理
        for path_403 in paths_to_process:
            try:
                argument = Arguments(bypass403_url, None, path_403, None)
                program = Program(argument.return_urls(), argument.return_dirs())
                program.initialise()
            except:
                pass


def run_bypass403():
    size = os.path.getsize('403list.txt')
    size_js=os.path.getsize('jsfind403list.txt')
    from lib.core.options import parse_options
    if (parse_options()['bypass']) == None:
        pass
    else:
        bp403="".join(parse_options()['bypass'])
        if bp403 =='yes':
            if size ==0 and size_js ==0:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] 没有403状态码存在！" + '\n'
                print(set_color(message, fore="yellow"), end='')
                # print(Fore.GREEN + Style.BRIGHT + '没有403状态码存在！'+Style.RESET_ALL)
            else:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] 开始403bypass！" +'\n'
                print(set_color(message, fore="green"), end='')
                # print(Fore.GREEN + Style.BRIGHT+''+Style.RESET_ALL)

                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] 使用优化的403bypass模式！！" +'\n'
                print(set_color(message, fore="green"), end='')
                # print(Fore.CYAN + Style.BRIGHT + ''+Style.RESET_ALL)

                # 处理403list.txt路径
                with open('403list.txt',) as f1:
                    list_403=f1.readlines()
                for path_403 in list_403:
                    path_403=path_403.replace('\n','').replace('\r','')
                    q.put(path_403)

                # 使用优化的bypass函数
                bypass()

                # 处理jsfind403list.txt路径，使用优化模式
                if size_js > 0:
                    try:
                        with open('jsfind403list.txt') as js1:
                            jsf=js1.readlines()

                        # 收集所有JS发现的URL和路径
                        js_urls = []
                        js_paths = []

                        for ff in jsf:
                            ff = ff.replace('\n', '').replace('\r', '')
                            num_slashes = ff.count('/')
                            if num_slashes == 2:
                                ff = ff + '/'
                            split_url = ff.split("/")
                            js_url = "/".join(split_url[:3])
                            js_path = split_url[3]
                            if js_path == '':
                                js_path = '/'

                            if js_url not in js_urls:
                                js_urls.append(js_url)
                            js_paths.append(js_path)

                        # 使用优化模式处理JS发现的路径
                        if js_urls and js_paths:
                            print(f"开始处理 {len(js_paths)} 个JS发现的403路径")
                            argument = Arguments(None, None, None, None)
                            argument.urls = js_urls
                            argument.dirs = js_paths
                            program = Program(argument.return_urls(), argument.return_dirs(), max_workers=20)
                            program.initialise()

                    except Exception as e:
                        print(f"处理jsfind403list.txt时出错: {str(e)}")

                pass403_qc()

        else:
            pass


def jsfind():
    import lib.JSFinder
    from lib.core.options import parse_options
    from lib.view.terminal import output
    from lib.view.colors import set_color
    import time
    # current_time = time.strftime("%H:%M:%S")
    # message = f"[{current_time}] jsfind "
    # output.new_line(set_color(message, fore="cyan"))
    if (parse_options()['jsfind']) == None:
        pass
    else:
        jsf="".join(parse_options()['jsfind'])
        if jsf=='yes':
            # print(Fore.GREEN + Style.BRIGHT+"开始JsFind！"+Style.RESET_ALL)
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}] 开始JsFind！"
            output.new_line(set_color(message, fore="green", style="bright"))
            url="".join(parse_options()['urls'])
            urls = lib.JSFinder.find_by_url(url)
            lib.JSFinder.giveresult(urls, url)
        else:
            pass

def ehole():
    """
    主函数，用于启动ehole指纹识别功能

    该函数解析命令行选项，检查是否启用指纹识别功能，
    如果启用则调用lib.ehole.ehole模块的start_ehole方法启动识别过程

    参数:
        无

    返回值:
        无
    """
    from lib.core.options import parse_options
    from lib.view.terminal import output
    from lib.view.colors import set_color
    import time
    import subprocess
    # 解析命令行选项并检查zwsb参数是否设置
    if (parse_options()['zwsb']) == None:
        pass
    else:
        # 将zwsb参数值连接成字符串并检查是否为'yes'
        zwsb="".join(parse_options()['zwsb'])
        if zwsb=='yes':
            # 打印指纹识别启动信息并调用ehole主程序
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]  指纹识别！"
            output.new_line(set_color(message, fore="green", style="bright"))
            # 调用 lib/ehole/ehole.py 的 start_ehole() 方法
            import lib.ehole.ehole
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}]  正在启动指纹识别..！"
            output.new_line(set_color(message, fore="green",style="bright"))
            lib.ehole.ehole.start_ehole()
        else:
            pass



def hhh():
    open("403list.txt", 'w').close()
    open('jsfind403list.txt','w').close()

def swagger_scan():
    import lib.core.options
    from script import swagger
    import argparse

    # 只调用一次 parse_options() 并存储结果
    parsed_options = lib.core.options.parse_options()

    # 检查 -swagger 参数是否为 yes
    if parsed_options.get('swagger') is None:
        return

    swagger_opt = "".join(parsed_options['swagger'])
    if swagger_opt.lower() != 'yes':
        return

    # 查找所有可能的 swagger 相关路径
    swagger_paths = []
    try:
        # 从扫描结果中读取所有找到的路径
        if os.path.exists('dir_file_path.txt'):
            with open('dir_file_path.txt', 'r') as f:
                report_path = f.read().strip()

            # 尝试读取报告文件中的路径
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    content = f.read()
                    # 检测 swagger 相关路径
                    swagger_patterns = ['swagger-ui', 'api-docs', 'swagger-resources', 'swagger.json', 'openapi.json']
                    for line in content.split('\n'):
                        # 跳过空行
                        if not line.strip():
                            continue

                        # 跳过注释行（以#开头）
                        if line.strip().startswith('#'):
                            continue

                        # 检查行是否包含任何swagger模式
                        if any(pattern in line.lower() for pattern in swagger_patterns):
                            try:
                                # 按空白字符分割行
                                parts = line.strip().split()

                                # 检查第一部分是否为状态码
                                if len(parts) >= 1:
                                    # 尝试解析状态码
                                    try:
                                        status_code = int(parts[0])
                                        # 只包含200状态码的路径
                                        if status_code != 200:
                                            print(f"跳过非200状态码路径: {line.strip()}")
                                            continue
                                    except ValueError:
                                        # 如果第一部分不是状态码，则跳过此行
                                        print(f"无法从行解析状态码: {line.strip()}")
                                        continue

                                # 完整URL应该是第三个元素或最后一个元素
                                # 根据报告的格式而定
                                if len(parts) >= 3:
                                    # URL可能是第三部分，或者如果有空格在URL中可能是最后一部分
                                    # 让我们找到第一个以'http'开头的部分
                                    url_part = None
                                    for part in parts:
                                        if part.startswith('http'):
                                            url_part = part
                                            break

                                    if url_part:
                                        swagger_paths.append(url_part)
                                    else:
                                        # 回退：使用最后一部分作为URL
                                        swagger_paths.append(parts[-1])
                                else:
                                    # 简单情况：直接使用整行作为URL
                                    swagger_paths.append(line.strip())
                            except Exception as e:
                                print(f"从行提取URL时出错: {line}。错误: {e}")
                                pass
    except Exception as e:
        print(f"读取swagger路径时出错: {e}")
        pass

    # 如果找到了 swagger 路径，调用 swagger.py 进行扫描
    if swagger_paths:
        print(Fore.GREEN + Style.BRIGHT + f'找到 {len(swagger_paths)} 个swagger相关路径，开始swagger扫描...' + Style.RESET_ALL)

        # 创建 swagger.py 需要的参数对象
        args = argparse.Namespace()
        args.target_url = None
        args.url_file = None
        args.debug = False
        args.force_domain = False
        args.custom_path_prefix = ''
        args.header_list = []
        # 获取 dirsearch 的 headers 并传递给 swagger 扫描
        args.custom_headers = parsed_options.get('headers', {})

        # 对每个找到的 swagger 路径进行扫描
        for swagger_url in swagger_paths:
            print(Fore.GREEN + f'扫描swagger路径: {swagger_url}' + Style.RESET_ALL)
            swagger.run(swagger_url, args)

        # 扫描完成后保存Excel文件
        try:
            base_name = "ScanReport"
            # 尝试从第一个swagger路径中提取域名作为文件名
            if swagger_paths:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(swagger_paths[0]).netloc
                    safe_domain = re.sub(r'[.:\\/*?"<>|]', '_', domain)
                    base_name = safe_domain
                except Exception:
                    pass
            swagger.save_workbook(base_name)
        except Exception as e:
            print(f"保存swagger扫描结果到Excel时出错: {e}")
    else:
        print(Fore.YELLOW + '未找到swagger相关路径。' + Style.RESET_ALL)

def packer_fuzzer():
    import os
    import sys
    import subprocess
    import time
    from lib.core.options import parse_options
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}] packer_fuzzer ----------------------------------"
    output.new_line(set_color(message, fore="cyan"))
    # 检查 -p/--packer-fuzzer 参数
    if (parse_options()['packer_fuzzer']) == None:
        return

    packer_opt = "".join(parse_options()['packer_fuzzer'])
    if packer_opt.lower() != 'yes':
        return
    message = f"[{current_time}] 开始Packer-Fuzzer扫描！"
    print(set_color(message, fore="blue"), end='')
    # print(Fore.GREEN + Style.BRIGHT + "开始Packer-Fuzzer扫描！" + Style.RESET_ALL)
    # current_time = time.strftime("%H:%M:%S")

    try:
        # 检查 resources/bypass403_url.txt 文件是否存在并读取URL
        if os.path.exists('resources/bypass403_url.txt'):
            with open('resources/bypass403_url.txt', 'r') as f:
                url = f.read().strip()

            if url:
                # print(f"扫描URL: {url}")
                message = f"\n[{current_time}] 扫描URL: {url}"
                print(set_color(message, fore="blue"), end='')
                # 检查是否已经安装了 Packer-Fuzzer
                # 更新路径为 script/Packer-Fuzzer
                packer_fuzzer_base_dir = os.path.join(os.getcwd(), 'lib')
                packer_fuzzer_dir = os.path.join(packer_fuzzer_base_dir, 'Packer-Fuzzer')

                if not os.path.exists(packer_fuzzer_dir):
                    # print(Fore.YELLOW + "未找到Packer-Fuzzer。正在从GitHub克隆..." + Style.RESET_ALL)
                    message = f"[{current_time}] 未找到Packer-Fuzzer  -- .... -- 正在从GitHub克隆...！"
                    print(set_color(message, fore="blue"), end='')
                    # 确保 script 目录存在
                    if not os.path.exists(packer_fuzzer_base_dir):
                        os.makedirs(packer_fuzzer_base_dir)
                    # 克隆 Packer-Fuzzer 仓库到 script 目录
                    subprocess.run([
                        'git', 'clone', 'https://github.com/rtcatc/Packer-Fuzzer.git'
                    ], cwd=packer_fuzzer_base_dir, check=True)

                # 使用项目根目录下的.venv虚拟环境
                project_root = os.getcwd()
                current_time = time.strftime("%H:%M:%S")
                message =  f"\n[{current_time}] 使用项目根目录下的.venv虚拟环境: {project_root}" + Style.RESET_ALL
                print(set_color(message, fore="blue"), end='')
                message = f"\n[{current_time}] ---------------------------------------------------------------" + Style.RESET_ALL
                print(set_color(message, fore="blue"), end='')
                # print(Fore.GREEN + f"使用项目根目录下的.venv虚拟环境: {project_root}" + Style.RESET_ALL)
                if sys.platform == "win32":
                    venv_python = os.path.join(project_root, '.venv', 'Scripts', 'python.exe')
                    venv_pip = os.path.join(project_root, '.venv', 'Scripts', 'pip.exe')
                else:
                    venv_python = os.path.join(project_root, '.venv', 'bin', 'python')
                    venv_pip = os.path.join(project_root, '.venv', 'bin', 'pip')

                # 检查项目虚拟环境是否存在
                if not os.path.exists(os.path.join(project_root, '.venv')):
                    message = f"{[current_time]} 项目虚拟环境(.venv)不存在，请先创建项目虚拟环境"
                    print(set_color(message, fore="blue"), end='')
                    # print(Fore.RED + "" + Style.RESET_ALL)
                    return

                # 确保 Packer-Fuzzer 的报告目录存在
                reports_dir = os.path.join(packer_fuzzer_dir, 'reports')
                res_dir = os.path.join(reports_dir, 'res')
                if not os.path.exists(reports_dir):
                    os.makedirs(reports_dir)
                if not os.path.exists(res_dir):
                    os.makedirs(res_dir)

                # 优化依赖检查逻辑 - 只在必要时安装依赖
                requirements_file = os.path.join(packer_fuzzer_dir, 'requirements.txt')
                installed_flag = os.path.join(packer_fuzzer_dir, '.installed')

                # 检查是否需要安装依赖
                need_install = False
                if not os.path.exists(installed_flag):
                    # 从未安装过依赖
                    need_install = True
                elif os.path.exists(requirements_file) and os.path.exists(installed_flag):
                    # 检查 requirements.txt 是否比标记文件更新
                    if os.path.getmtime(requirements_file) > os.path.getmtime(installed_flag):
                        need_install = True

                if need_install:
                    # print(Fore.GREEN + "正在项目虚拟环境中安装Packer-Fuzzer依赖..." + Style.RESET_ALL)
                    message = f"\n[{current_time}] 正在项目虚拟环境中安装Packer-Fuzzer依赖..."
                    print(set_color(message, fore="blue"), end='')
                    # 使用项目根目录下的虚拟环境pip来安装Packer-Fuzzer目录中的requirements.txt
                    subprocess.run([
                        venv_pip, 'install', '-r', os.path.join(packer_fuzzer_dir, 'requirements.txt')
                    ], cwd=project_root, check=True)

                    # 创建或更新标记文件
                    with open(installed_flag, 'w') as f:
                        f.write(str(time.time()))
                else:
                    # print(Fore.GREEN + "Packer-Fuzzer依赖已安装，跳过安装步骤" + Style.RESET_ALL)
                    message = f"\n[{current_time}] Packer-Fuzzer依赖已安装，跳过安装步骤"
                    print(set_color(message, fore="blue"), end='')

                # 设置环境变量以解决编码问题
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                if sys.platform == "win32":
                    env['PYTHONLEGACYWINDOWSFSENCODING'] = '1'

                # 运行 Packer-Fuzzer 扫描，使用 errors='ignore' 或 errors='replace' 来处理编码问题
                message = f"\n[{current_time}] 正在运行Packer-Fuzzer扫描..."
                print(set_color(message, fore="blue"), end='')
                # print(Fore.GREEN + "" + Style.RESET_ALL)
                result = subprocess.run([
                    venv_python, 'PackerFuzzer.py', '-u', url
                ], cwd=packer_fuzzer_dir,  # 使用完整的 Packer-Fuzzer 目录路径
                   capture_output=True, text=True, env=env,
                   errors='replace', encoding='utf-8')  # 添加 encoding='utf-8' 参数

                # 查找生成的HTML报告
                import glob
                # 更新报告路径为 script/Packer-Fuzzer/reports
                report_files = glob.glob(os.path.join(packer_fuzzer_dir, 'reports', '*.html'))
                if report_files:
                    latest_report = max(report_files, key=os.path.getctime)
                    message = f"\n[{current_time}]  Packer-Fuzzer扫描报告已找到:"
                    print(set_color(message, fore="blue"), end='')
                    # print(Fore.GREEN + "\nPacker-Fuzzer扫描报告已找到:" + Style.RESET_ALL)
                    message = f"[{current_time}] 报告路径: {latest_report}"
                    print(set_color(message, fore="blue"), end='')
                    message = f"\n [{current_time}] 您可以在浏览器中打开此HTML报告查看详细的扫描结果。"
                    print(set_color(message, fore="blue"), end='')
                    # print(Fore.CYAN + "\n您可以在浏览器中打开此HTML报告查看详细的扫描结果。" + Style.RESET_ALL)
                    message = f"[{current_time}] 报告包含检测到的漏洞、API端点和其他发现的信息。"
                    print(set_color(message, fore="blue"), end='')
                    # print(Fore.CYAN + "报告包含检测到的漏洞、API端点和其他发现的信息。" + Style.RESET_ALL)
                else:
                    # print(Fore.YELLOW + "\n未找到HTML报告。检查Packer-Fuzzer是否成功完成。" + Style.RESET_ALL)
                    message = f"\n[{current_time}] 未找到HTML报告。检查Packer-Fuzzer是否成功完成。"
                    print(set_color(message, fore="yellow"), end='')
                # 输出结果
                # print(Fore.GREEN + "\nPacker-Fuzzer扫描结果:" + Style.RESET_ALL)
                message = f"\n[{current_time}] Packer-Fuzzer扫描结果:"
                print(set_color(message, fore="green"), end='')
                # print(f"[{current_time}]"+ result.stdout)
                message = f"\n[{current_time}]" + result.stdout + ""
                print(set_color(message, fore="green"), end='')

                if result.stderr:
                    pass
                    # print(Fore.RED + "Packer-Fuzzer:" + Style.RESET_ALL)
                    message = f"\n[{current_time}] Packer-Fuzzer"
                    print(set_color(message, fore="yellow"), end='')

                    print(set_color(f"\n[{current_time}]" + result.stderr, fore="green"), end='')
                    # print(result.stderr)
            else:
                # print(Fore.RED + "resources/bypass403_url.txt中未找到URL" + Style.RESET_ALL)
                message = f"[{current_time}] bypass403_url.txt中未找到URL"
                print(set_color(message, fore="red"), end='')
        else:
            message = f"[{current_time}] 未找到bypass403_url.txt"
            print(set_color(message, fore="red"), end='')
            # print(Fore.RED + "未找到resources/bypass403_url.txt" + Style.RESET_ALL)
    except Exception as e:
        message = f"[{current_time}] Packer-Fuzzer扫描期间出错: {str(e)}"
        print(set_color(message, fore="red"), end='')
        # print(Fore.RED + f"Packer-Fuzzer扫描期间出错: {str(e)}" + Style.RESET_ALL)


def subfinder_scan():
    """
    调用 subfinder 子域名扫描模块
    """
    import os
    import time
    from lib.core.options import parse_options
    from lib.view.colors import set_color
    
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}] 开始SubFinder子域名扫描..."
    print(set_color(message, fore="blue"))
    
    try:
        # 检查 resources/bypass403_url.txt 文件是否存在并读取URL
        if os.path.exists('resources/bypass403_url.txt'):
            with open('resources/bypass403_url.txt', 'r') as f:
                url = f.read().strip()

            if url:
                url = url.replace("https://", "").replace("http://", "")
                url = url.rstrip("/")
                message = f"[{current_time}]扫描目标: {url}"
                print(set_color(message, fore="blue"))
                # 导入并调用 subfinder 模块
                from lib.subfinderX.subfinder import run_subfinder
                
                # 调用 subfinder 进行扫描
                run_subfinder(
                    domain=url,
                    deep=5,
                    dict_file="test.txt",
                    enable_http=True,
                    random_check=True
                )
                
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] SubFinder扫描完成"
                print(set_color(message, fore="green"))
            else:
                current_time = time.strftime("%H:%M:%S")
                message = f"[{current_time}] bypass403_url.txt中未找到有效URL"
                print(set_color(message, fore="red"))
        else:
            current_time = time.strftime("%H:%M:%S")
            message = f"[{current_time}] 未找到 resources/bypass403_url.txt文件"
            print(set_color(message, fore="red"))
            
    except Exception as e:
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] SubFinder扫描期间出错: {str(e)}"
        print(set_color(message, fore="red"))


def run():
    """
    主函数，负责执行一系列安全扫描和检测功能

    该函数按顺序调用多个安全检测模块，包括漏洞扫描、JS文件分析、
    403绕过测试、指纹识别、打包器模糊测试和Swagger接口扫描等功能。
    """
    current_time = time.strftime("%H:%M:%S")

    # 执行基础初始化操作
    hhh()

    # 导入并解析命令行选项配置
    from lib.core.options import parse_options

    # 更新全局选项配置
    options.update(parse_options())

    # 初始化并运行主控制器
    Controller()

    # 执行JavaScript文件查找和分析
    print(set_color(f"[{current_time}] 执行JavaScript文件查找和分析 ", fore="blue"))
    jsfind()

    # 运行403 Forbidden状态码绕过测试
    print(set_color(f"[{current_time}] 运行403 Forbidden状态码绕过测试 ", fore="blue"))
    run_bypass403()

    # 执行EHole指纹识别工具
    print(set_color(f"[{current_time}] 执行EHole指纹识别工具 ", fore="blue"))
    ehole()

    # 运行打包器模糊测试
    print(set_color(f"[{current_time}] 运行打包器模糊测试 ", fore="blue"))
    packer_fuzzer()

    # 运行SubFinder子域名扫描
    print(set_color(f"[{current_time}] SubFinder子域名扫描 ", fore="blue"))
    subfinder_scan()

    # 执行Swagger接口扫描
    print(set_color(f"[{current_time}] Swagger接口扫描 ", fore="blue"))
    swagger_scan()

if __name__ == "__main__":
    q = queue.Queue()
    run()
