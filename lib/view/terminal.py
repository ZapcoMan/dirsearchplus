import sys
import time
import shutil

from lib.core.data import options
from lib.core.decorators import locked
from lib.core.settings import IS_WINDOWS
from lib.utils.common import human_size
from lib.view.colors import set_color, clean_color, disable_color

if IS_WINDOWS:
    from colorama.win32 import (
        FillConsoleOutputCharacter,
        GetConsoleScreenBufferInfo,
        STDOUT,
    )


class Output:
    """
    输出管理类，用于处理控制台输出、状态报告、进度条显示等功能。

    属性:
        last_in_line (bool): 标记上一次是否使用了行内输出。
        buffer (str): 存储所有输出内容的缓冲区。
    """

    def __init__(self):
        """初始化输出对象，并根据配置决定是否启用颜色。"""
        self.last_in_line = False
        self.buffer = ""

        if not options["color"]:
            disable_color()

    @staticmethod
    def erase():
        """
        清除当前行的内容，兼容 Windows 和 Unix 系统。

        在 Windows 上通过调用 Win32 API 实现清屏，
        在其他系统中则使用 ANSI 转义序列进行清除。
        """
        if IS_WINDOWS:
            csbi = GetConsoleScreenBufferInfo()
            line = "\b" * int(csbi.dwCursorPosition.X)
            sys.stdout.write(line)
            width = csbi.dwCursorPosition.X
            csbi.dwCursorPosition.X = 0
            FillConsoleOutputCharacter(STDOUT, " ", width, csbi.dwCursorPosition)
            sys.stdout.write(line)
            sys.stdout.flush()

        else:
            sys.stdout.write("\033[1K")
            sys.stdout.write("\033[0G")

    @locked
    def in_line(self, string):
        """
        行内输出字符串（覆盖当前行）。

        参数:
            string (str): 需要输出到终端的文本。
        """
        self.erase()
        sys.stdout.write(string)
        sys.stdout.flush()
        self.last_in_line = True

    @locked
    def new_line(self, string="", do_save=True):
        """
        换行输出字符串并保存至缓冲区。

        参数:
            string (str): 需要输出的文本，默认为空字符串。
            do_save (bool): 是否将输出内容保存进缓冲区，默认为 True。
        """
        if self.last_in_line:
            self.erase()

        if IS_WINDOWS:
            sys.stdout.write(string)
            sys.stdout.flush()
            sys.stdout.write("\n")
            sys.stdout.flush()

        else:
            sys.stdout.write(string + "\n")

        sys.stdout.flush()
        self.last_in_line = False
        sys.stdout.flush()

        if do_save:
            self.buffer += string
            self.buffer += "\n"

    def status_report(self, response, full_url):
        """
        显示 HTTP 响应的状态信息。

        参数:
            response (Response): 包含响应数据的对象。
            full_url (bool): 是否显示完整的 URL 地址。
        """
        status = response.status
        length = human_size(response.length)
        target = response.url if full_url else "/" + response.full_path
        current_time = time.strftime("%H:%M:%S")
        message = f"[{current_time}] {status} - {length.rjust(6, ' ')} - {target}"

        # 根据不同的状态码设置不同颜色
        if status in (200, 201, 204):
            message = set_color(message, fore="green")
        elif status == 401:
            message = set_color(message, fore="yellow")
        elif status == 403:
            message = set_color(message, fore="blue")
        elif status in range(500, 600):
            message = set_color(message, fore="red")
        elif status in range(300, 400):
            message = set_color(message, fore="cyan")
        else:
            message = set_color(message, fore="magenta")

        # 添加重定向信息
        if response.redirect:
            message += f"  ->  {response.redirect}"

        for redirect in response.history:
            message += f"\n-->  {redirect}"

        self.new_line(message)

    def last_path(self, index, length, current_job, all_jobs, rate, errors):
        """
        显示扫描任务的进度条和相关信息。

        参数:
            index (int): 当前已完成的任务数。
            length (int): 总共需要完成的任务总数。
            current_job (int): 当前正在执行的 job 数量。
            all_jobs (int): 所有已加入队列的 job 数量。
            rate (float): 当前扫描速率（每秒请求数）。
            errors (int): 错误计数。
        """
        percentage = int(index / length * 100)
        task = set_color("#", fore="cyan", style="bright") * int(percentage / 5)
        task += " " * (20 - int(percentage / 5))
        progress = f"{index}/{length}"

        grean_job = set_color("job", fore="green", style="bright")
        jobs = f"{grean_job}:{current_job}/{all_jobs}"

        red_error = set_color("errors", fore="red", style="bright")
        errors = f"{red_error}:{errors}"

        progress_bar = f"[{task}] {str(percentage).rjust(2, chr(32))}% "
        progress_bar += f"{progress.rjust(12, chr(32))} "
        progress_bar += f"{str(rate).rjust(9, chr(32))}/s       "
        progress_bar += f"{jobs.ljust(21, chr(32))} {errors}"

        # 如果进度条长度超过终端宽度则跳过显示
        if len(clean_color(progress_bar)) >= shutil.get_terminal_size()[0]:
            return

        self.in_line(progress_bar)

    def new_directories(self, directories):
        """
        提示新增目录被加入扫描队列的消息。

        参数:
            directories (list): 新增目录列表。
        """
        # current_time =
        current_time = set_color(time.strftime("%H:%M:%S"), fore="cyan", style="bright")
        message = set_color(
            f"Added to the queue: {', '.join(directories)}", fore="cyan", style="bright"
        )
        self.new_line(f"[{current_time}] {message}")

    def error(self, reason):
        """
        显示错误提示信息。

        参数:
            reason (str): 错误原因描述。
        """
        message = set_color(reason, fore="white", back="red", style="bright")
        self.new_line("\n" + message)

    def warning(self, message, do_save=True):
        """
        显示警告信息。

        参数:
            message (str): 警告内容。
            do_save (bool): 是否将消息存入缓冲区，默认为 True。
        """
        message = set_color(message, fore="yellow", style="bright")
        self.new_line(message, do_save=do_save)

    def header(self, message):
        """
        显示标题信息。

        参数:
            message (str): 标题内容。
        """
        message = set_color(message, fore="magenta", style="bright")
        self.new_line(message)

    def print_header(self, headers):
        """
        打印键值对形式的信息头。

        参数:
            headers (dict): 键值对格式的数据字典。
        """
        msg = []

        for key, value in headers.items():
            new = set_color(key + ": ", fore="yellow", style="bright")
            new += set_color(value, fore="cyan", style="bright")

            # 判断是否换行以适应终端宽度
            if (
                not msg
                or len(clean_color(msg[-1]) + clean_color(new)) + 3
                >= shutil.get_terminal_size()[0]
            ):
                msg.append("")
            else:
                msg[-1] += set_color(" | ", fore="magenta", style="bright")

            msg[-1] += new

        self.new_line("\n".join(msg))

    def config(self, wordlist_size):
        """
        显示当前运行时的配置信息。

        参数:
            wordlist_size (int): 字典大小。
        """
        config = {}
        config["Extensions"] = ", ".join(options["extensions"])

        if options["prefixes"]:
            config["Prefixes"] = ", ".join(options["prefixes"])
        if options["suffixes"]:
            config["Suffixes"] = ", ".join(options["suffixes"])

        config.update({
            "HTTP method": options["http_method"],
            "Threads": str(options["thread_count"]),
            "Wordlist size": str(wordlist_size),
        })

        self.print_header(config)

    def target(self, target):
        """
        显示目标地址信息。

        参数:
            target (str): 目标 URL 或主机名。
        """
        self.new_line()
        self.print_header({"Target": target})

    def output_file(self, file):
        """
        显示输出文件路径。

        参数:
            file (str): 输出文件路径。
        """
        self.new_line(f"\nOutput File: {file}")

    def log_file(self, file):
        """
        显示日志文件路径。

        参数:
            file (str): 日志文件路径。
        """
        self.new_line(f"\nLog File: {file}")


class QuietOutput(Output):
    """
    安静模式下的输出类，继承自 Output 类。

    此类会屏蔽大部分输出功能，仅保留必要的状态报告。
    """

    def status_report(self, response, full_url):
        """
        只在安静模式下打印状态报告。

        参数:
            response (Response): 响应对象。
            full_url (bool): 是否显示完整 URL。
        """
        super().status_report(response, True)

    def last_path(*args):
        """忽略进度条更新。"""
        pass

    def new_directories(*args):
        """忽略新目录通知。"""
        pass

    def warning(*args, **kwargs):
        """忽略警告信息。"""
        pass

    def header(*args):
        """忽略头部信息。"""
        pass

    def config(*args):
        """忽略配置信息。"""
        pass

    def target(*args):
        """忽略目标信息。"""
        pass

    def output_file(*args):
        """忽略输出文件信息。"""
        pass

    def log_file(*args):
        """忽略日志文件信息。"""
        pass


# 初始化全局输出实例
output = QuietOutput() if options["quiet"] else Output()
