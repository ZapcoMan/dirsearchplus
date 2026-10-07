#!/usr/bin/env python3

import re
import time
from colorama import init, Fore, Style

import lib
from lib.controller.controller import Controller
from lib.pass403_optimized import OptimizedArguments as Arguments, OptimizedProgram as Program
from lib.qc import pass403_qc

import queue

# 403 路径收集队列：定义为模块级单例，避免依赖 __main__ 局部变量造成的隐式耦合
q = queue.Queue()

import sys,os


from lib.core.data import options
from lib.core.exceptions import FailedDependenciesInstallation
from lib.core.logger import logger
from lib.core.installation import (
    check_dependencies,
    install_dependencies,
    DistributionNotFound,
    VersionConflict,
)
from lib.core.settings import OPTIONS_FILE
from lib.parse.config import ConfigParser
from lib.view.colors import set_color
from lib.view.terminal import output

init()

# Packer-Fuzzer 仓库地址与可选的固定引用(需为标签/分支名)，通过环境变量 PACKER_FUZZER_REF 指定，
# 便于在受控环境中锁定来源、降低运行时动态克隆带来的供应链风险
PACKER_FUZZER_REPO = 'https://github.com/rtcatc/Packer-Fuzzer.git'
PACKER_FUZZER_REF = os.environ.get('PACKER_FUZZER_REF')

# 解析本工具自有的运行开关，并从 argv 中摘除，避免传入 dirsearch 参数解析器时因未知选项报错
_DEBUG_MODE = ("--debug" in sys.argv) or os.environ.get("DIRSEARCHPLUS_DEBUG") == "1"
_INSECURE = ("--insecure" in sys.argv) or os.environ.get("DIRSEARCHPLUS_INSECURE") == "1"
_SECURE = ("--secure" in sys.argv)
for _flag in ("--debug", "--insecure", "--secure"):
    while _flag in sys.argv:
        sys.argv.remove(_flag)

import lib.core.settings as _settings
if _INSECURE:
    _settings.VERIFY_TLS = False
elif _SECURE:
    _settings.VERIFY_TLS = True

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
        logger.debug(f"批量403bypass处理失败，回退为逐个处理: {e}")
        # 如果处理失败，尝试逐个处理
        for path_403 in paths_to_process:
            try:
                argument = Arguments(bypass403_url, None, path_403, None)
                program = Program(argument.return_urls(), argument.return_dirs())
                program.initialise()
            except Exception as e:
                logger.debug(f"单个403路径 {path_403} bypass失败: {e}")


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

                        from urllib.parse import urlparse
                        for ff in jsf:
                            ff = ff.replace('\n', '').replace('\r', '').strip()
                            if not ff:
                                continue
                            # jsfind403list.txt 每行是完整URL（如 https://host/admin/secret），
                            # 旧代码用 split('/') 取 split[3] 作为路径，既丢失前导 '/' 又截断多级路径，
                            # 导致 url+path 拼成 https://hostadmin 这类畸形地址使绕过全部失败；
                            # 改用 urlparse 正确拆出 host 与带前导斜杠的完整 path
                            parsed = urlparse(ff)
                            if not parsed.netloc:
                                continue
                            js_url = f"{parsed.scheme}://{parsed.netloc}"
                            js_path = parsed.path or '/'
                            if len(js_path) > 1:
                                js_path = js_path.rstrip('/') or '/'

                            if js_url not in js_urls:
                                js_urls.append(js_url)
                            if js_path not in js_paths:
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
            _js_urls = parse_options()['urls']
            url = _js_urls[0] if _js_urls else ""
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
    import argparse

    # 只调用一次 parse_options() 并存储结果
    parsed_options = lib.core.options.parse_options()

    # 检查 -swagger 参数是否为 yes
    if parsed_options.get('swagger') is None:
        return

    swagger_opt = "".join(parsed_options['swagger'])
    if swagger_opt.lower() != 'yes':
        return

    # 延迟导入 swagger：仅在实际启用时才需要 selenium/openpyxl 等浏览器依赖，
    # 缺依赖时优雅降级而非 sys.exit 拖垮整条流水线
    try:
        from script import swagger
    except (ImportError, SystemExit) as e:
        logger.debug(f"导入 swagger 失败(缺少浏览器依赖): {e}")
        current_time = time.strftime("%H:%M:%S")
        print(set_color(f"[{current_time}] Swagger 依赖未安装，跳过扫描。如需启用请执行: pip install -r requirements-browser.txt", fore="yellow"))
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
                                            logger.debug(f"跳过非200状态码路径: {line.strip()}")
                                            continue
                                    except ValueError:
                                        # 如果第一部分不是状态码，则跳过此行
                                        logger.debug(f"无法从行解析状态码: {line.strip()}")
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
                                logger.debug(f"从行提取URL时出错: {line}。错误: {e}")
                                pass
    except Exception as e:
        logger.debug(f"读取swagger路径时出错: {e}")
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
                    is_sha = bool(PACKER_FUZZER_REF) and re.fullmatch(r'[0-9a-fA-F]{7,40}', PACKER_FUZZER_REF)
                    if PACKER_FUZZER_REF:
                        message = f"[{current_time}] 未找到Packer-Fuzzer -- 正在从GitHub克隆(锁定引用: {PACKER_FUZZER_REF})...！"
                    else:
                        message = f"[{current_time}] 未找到Packer-Fuzzer -- 正在从GitHub克隆(默认分支，建议设置 PACKER_FUZZER_REF 锁定版本)...！"
                    print(set_color(message, fore="blue"), end='')
                    # 确保 lib 目录存在
                    if not os.path.exists(packer_fuzzer_base_dir):
                        os.makedirs(packer_fuzzer_base_dir)
                    # 浅克隆 Packer-Fuzzer 仓库到 lib 目录
                    if is_sha:
                        # 引用为提交SHA：先克隆默认分支，再 fetch 指定提交并 checkout
                        subprocess.run(['git', 'clone', '--depth', '1', PACKER_FUZZER_REPO],
                                       cwd=packer_fuzzer_base_dir, check=True)
                        subprocess.run(['git', 'fetch', '--depth', '1', 'origin', PACKER_FUZZER_REF],
                                       cwd=packer_fuzzer_dir, check=True)
                        subprocess.run(['git', 'checkout', 'FETCH_HEAD'],
                                       cwd=packer_fuzzer_dir, check=True)
                    else:
                        # 引用为标签/分支名(或未指定)：直接 --branch 浅克隆
                        clone_cmd = ['git', 'clone', '--depth', '1']
                        if PACKER_FUZZER_REF:
                            clone_cmd += ['--branch', PACKER_FUZZER_REF]
                        clone_cmd += [PACKER_FUZZER_REPO]
                        subprocess.run(clone_cmd, cwd=packer_fuzzer_base_dir, check=True)

                # 完整性校验：确认入口脚本存在，避免执行克隆失败或被篡改的目录
                entry_script = os.path.join(packer_fuzzer_dir, 'PackerFuzzer.py')
                if not os.path.isfile(entry_script):
                    message = f"[{current_time}] Packer-Fuzzer 入口脚本缺失({entry_script})，已中止以避免执行不完整的代码"
                    print(set_color(message, fore="red"), end='')
                    logger.error(f"Packer-Fuzzer entry not found: {entry_script}")
                    return

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
                    message = f"[{current_time}] 项目虚拟环境(.venv)不存在，请先创建项目虚拟环境"
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
                    venv_python, 'PackerFuzzer.py', '-u', url,'-t','adv'
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


def _run_stage(name, func):
    """执行单个扫描阶段：捕获异常并计时，任一阶段失败不影响后续阶段"""
    start = time.time()
    current_time = time.strftime("%H:%M:%S")
    print(set_color(f"[{current_time}] 开始阶段: {name}", fore="blue"))
    try:
        func()
    except KeyboardInterrupt:
        raise
    except (Exception, SystemExit) as e:
        # 连 SystemExit 一并捕获，避免个别模块内部 sys.exit 中断整条流水线
        elapsed = time.time() - start
        current_time = time.strftime("%H:%M:%S")
        print(set_color(f"[{current_time}] 阶段 {name} 出错(已跳过，耗时 {elapsed:.1f}s): {e}", fore="red"))
        logger.debug(f"stage '{name}' failed: {e}", exc_info=True)
        return
    elapsed = time.time() - start
    current_time = time.strftime("%H:%M:%S")
    print(set_color(f"[{current_time}] 阶段 {name} 完成，耗时 {elapsed:.1f}s", fore="green"))


def _setup_clash_mode():
    """启用 Clash 自动切换IP模式。

    校验外部控制器前置条件、启动后台节点轮转线程，并把本地混合代理端口注入
    options["proxies"]（dirsearch 的 Requester 会让每个请求都走该端口，后台线程
    负责按间隔切换节点，从而实现扫描中自动更换出口 IP）。

    返回已启动的 rotator；未启用或前置校验失败时返回 None（自动降级为普通扫描）。
    """
    if not options.get("clash_mode"):
        return None

    from script.clash_proxy_rotator import ClashProxyRotator, ClashControllerError

    current_time = time.strftime("%H:%M:%S")
    secret = options.get("clash_secret") or ""
    print(set_color(f"[{current_time}] 已启用 Clash 自动切换IP模式", fore="cyan", style="bright"))
    print(set_color(
        f"[{current_time}] 前置要求：Clash 必须已开启外部控制器(external-controller)，"
        f"并已正确设置『外部控制器监听地址』与『外部控制器 API 密钥(secret)』。",
        fore="cyan"))
    print(set_color(
        f"[{current_time}] 当前配置：控制器={options['clash_api']} | "
        f"本地代理端口={options['clash_port']} | 切换间隔={options['clash_interval']}s | "
        f"secret={'已提供' if secret else '未提供(若Clash配了secret会报401/403)'}",
        fore="cyan"))

    # 冲突提醒：Clash 模式会接管 options["proxies"]，与手动代理参数互斥
    conflicting = []
    if options.get("proxies"):
        conflicting.append("--proxy/--proxy-file")
    if options.get("tor"):
        conflicting.append("--tor")
    if conflicting:
        print(set_color(
            f"[{current_time}] 警告：检测到已设置 {'、'.join(conflicting)}，"
            "Clash 模式会用本地代理端口覆盖这些代理设置。",
            fore="yellow"))

    rotator = ClashProxyRotator(
        clash_api=options["clash_api"],
        clash_secret=options["clash_secret"],
        clash_proxy_port=options["clash_port"],
        switch_interval=options["clash_interval"],
    )

    try:
        rotator.check_prerequisites()
    except ClashControllerError as e:
        print(set_color(f"[{current_time}] Clash 模式启动失败：{e}", fore="red"))
        print(set_color("已自动降级为普通扫描模式（不使用 Clash 换 IP）。", fore="yellow"))
        return None

    rotator.start()
    # 注入本地代理：所有扫描请求经该端口，节点由后台线程轮转
    options["proxies"] = [rotator.get_proxy_url()]
    print(set_color(f"[{current_time}] Clash 轮转已运行：{rotator.describe()}", fore="green"))
    print(set_color(f"[{current_time}] 提示：加 --debug 可在控制台查看每次节点切换详情。", fore="cyan"))
    return rotator


def run():
    """
    主函数，负责执行一系列安全扫描和检测功能

    该函数按顺序调用多个安全检测模块。每个阶段独立容错：
    单个阶段失败仅跳过该阶段，不会中断整条流水线。
    """
    # --debug 启用控制台日志
    if _DEBUG_MODE:
        from lib.core.logger import enable_console_logging
        enable_console_logging()

    # 执行基础初始化操作
    hhh()

    # 导入并解析命令行选项配置
    from lib.core.options import parse_options

    # 更新全局选项配置
    options.update(parse_options())

    # Clash 自动切换IP模式：在扫描前启动后台轮转并注入代理
    _clash_rotator = _setup_clash_mode()

    try:
        # 各阶段独立容错执行
        _run_stage("目录扫描(Controller)", Controller)
        _run_stage("JavaScript文件查找和分析", jsfind)
        _run_stage("403 Forbidden状态码绕过测试", run_bypass403)
        _run_stage("EHole指纹识别工具", ehole)
        _run_stage("打包器模糊测试(Packer-Fuzzer)", packer_fuzzer)
        _run_stage("SubFinder子域名扫描", subfinder_scan)
        _run_stage("Swagger接口扫描", swagger_scan)
    finally:
        if _clash_rotator is not None:
            _clash_rotator.stop()
            current_time = time.strftime("%H:%M:%S")
            print(set_color(f"[{current_time}] Clash 自动切换IP模式已停止：{_clash_rotator.describe()}", fore="cyan"))

if __name__ == "__main__":
    run()
