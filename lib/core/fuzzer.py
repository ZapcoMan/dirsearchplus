import re
import threading
import time

from lib.core.data import blacklists, options
from lib.core.exceptions import RequestException
from lib.core.logger import logger
from lib.core.scanner import Scanner
from lib.core.settings import (
    DEFAULT_TEST_PREFIXES,
    DEFAULT_TEST_SUFFIXES,
    WILDCARD_TEST_POINT_MARKER,
)
from lib.parse.url import clean_path
from lib.utils.common import human_size, lstrip_once
from lib.utils.crawl import Crawler


class Fuzzer:
    """
    模糊测试器类，用于执行路径扫描任务。

    参数:
        requester: 请求发送对象，负责实际的HTTP请求。
        dictionary: 字典迭代器，提供待测试的路径列表。
        match_callbacks (list): 匹配回调函数列表，在发现有效路径时调用。
        not_found_callbacks (list): 未找到回调函数列表，在路径无效或被排除时调用。
        error_callbacks (list): 错误处理回调函数列表，在发生异常时调用。
    """

    def __init__(self, requester, dictionary, **kwargs):
        self._threads = []
        self._scanned = set()
        self._requester = requester
        self._dictionary = dictionary
        self._is_running = False
        self._play_event = threading.Event()
        self._paused_semaphore = threading.Semaphore(0)
        self._base_path = None
        self.exc = None
        self.match_callbacks = kwargs.get("match_callbacks", [])
        self.not_found_callbacks = kwargs.get("not_found_callbacks", [])
        self.error_callbacks = kwargs.get("error_callbacks", [])

    def wait(self, timeout=None):
        """
        等待所有线程完成运行。

        参数:
            timeout (float): 超时时间（秒），默认为None表示无限等待。

        返回:
            bool: 所有线程是否已完成。

        异常:
            抛出之前记录的异常（如果存在）。
        """
        if self.exc:
            raise self.exc

        for thread in self._threads:
            thread.join(timeout)

            if thread.is_alive():
                return False

        return True

    def setup_scanners(self):
        """
        初始化各种类型的Scanner实例，包括默认、前缀和后缀扫描器，
        用于检测响应中的通配符行为。
        """
        self.scanners = {
            "default": {},
            "prefixes": {},
            "suffixes": {},
        }

        # 默认扫描器（通配符测试点）
        self.scanners["default"].update({
            "index": Scanner(self._requester, path=self._base_path),
            "random": Scanner(self._requester, path=self._base_path + WILDCARD_TEST_POINT_MARKER),
        })

        if options["exclude_response"]:
            self.scanners["default"]["custom"] = Scanner(
                self._requester, tested=self.scanners, path=options["exclude_response"]
            )

        for prefix in options["prefixes"] + DEFAULT_TEST_PREFIXES:
            self.scanners["prefixes"][prefix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{prefix}{WILDCARD_TEST_POINT_MARKER}",
                context=f"/{self._base_path}{prefix}***",
            )

        for suffix in options["suffixes"] + DEFAULT_TEST_SUFFIXES:
            self.scanners["suffixes"][suffix] = Scanner(
                self._requester, tested=self.scanners,
                path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}{suffix}",
                context=f"/{self._base_path}***{suffix}",
            )

        for extension in options["extensions"]:
            if "." + extension not in self.scanners["suffixes"]:
                self.scanners["suffixes"]["." + extension] = Scanner(
                    self._requester, tested=self.scanners,
                    path=f"{self._base_path}{WILDCARD_TEST_POINT_MARKER}.{extension}",
                    context=f"/{self._base_path}***.{extension}",
                )

    def setup_threads(self):
        """
        根据配置选项初始化并创建多个工作线程。
        """
        if self._threads:
            self._threads = []

        for _ in range(options["thread_count"]):
            new_thread = threading.Thread(target=self.thread_proc)
            new_thread.daemon = True
            self._threads.append(new_thread)

    def get_scanners_for(self, path):
        """
        获取与给定路径匹配的所有Scanner实例。

        参数:
            path (str): 待检查的路径字符串。

        生成:
            Scanner: 符合条件的Scanner对象。
        """
        # 清理路径以进行扩展名/后缀判断
        path = clean_path(path)

        for prefix in self.scanners["prefixes"]:
            if path.startswith(prefix):
                yield self.scanners["prefixes"][prefix]

        for suffix in self.scanners["suffixes"]:
            if path.endswith(suffix):
                yield self.scanners["suffixes"][suffix]

        for scanner in self.scanners["default"].values():
            yield scanner

    def start(self):
        """
        启动模糊测试流程：设置扫描器和线程，并开始执行。
        """
        self.setup_scanners()
        self.setup_threads()

        self._running_threads_count = len(self._threads)
        self._is_running = True
        self._play_event.clear()

        for thread in self._threads:
            thread.start()

        self.play()

    def play(self):
        """
        唤醒所有暂停的工作线程继续执行。
        """
        self._play_event.set()

    def pause(self):
        """
        暂停当前正在运行的所有线程。
        """
        self._play_event.clear()
        for thread in self._threads:
            if thread.is_alive():
                self._paused_semaphore.acquire()

        self._is_running = False

    def resume(self):
        """
        继续执行已暂停的线程。
        """
        self._is_running = True
        self._paused_semaphore.release()
        self.play()

    def stop(self):
        """
        停止整个模糊测试过程。
        """
        self._is_running = False
        self.play()

    def scan(self, path, scanners):
        """
        对指定路径发起请求并使用提供的Scanner验证其有效性。

        参数:
            path (str): 需要扫描的目标路径。
            scanners (generator): 提供Scanner实例的可迭代对象。
        """
        # 防止重复扫描相同路径
        if path in self._scanned:
            return
        else:
            self._scanned.add(path)

        response = self._requester.request(path)

        if self.is_excluded(response):
            for callback in self.not_found_callbacks:
                callback(response)
            return

        for tester in scanners:
            # 判断响应是否唯一且不是通配符结果
            if not tester.check(path, response):
                for callback in self.not_found_callbacks:
                    callback(response)
                return

        try:
            for callback in self.match_callbacks:
                callback(response)
        except Exception as e:
            self.exc = e

        if options["crawl"]:
            logger.info(f'THREAD-{threading.get_ident()}: crawling "/{path}"')
            for path_ in Crawler.crawl(response):
                if self._dictionary.is_valid(path_):
                    logger.info(f'THREAD-{threading.get_ident()}: found new path "/{path_}" in /{path}')
                    self.scan(path_, self.get_scanners_for(path_))

    def is_excluded(self, resp):
        """
        使用多种过滤规则来判断一个响应是否应该被忽略。

        参数:
            resp: HTTP响应对象。

        返回:
            bool: 如果该响应应被排除则返回True，否则False。
        """
        """Validate the response by different filters"""

        if resp.status in options["exclude_status_codes"]:
            return True

        if (
            options["include_status_codes"]
            and resp.status not in options["include_status_codes"]
        ):
            return True

        if (
            resp.status in blacklists
            and any(
                resp.path.endswith(lstrip_once(suffix, "/"))
                for suffix in blacklists.get(resp.status)
            )
        ):
            return True

        if human_size(resp.length).rstrip() in options["exclude_sizes"]:
            return True

        if resp.length < options["minimum_response_size"]:
            return True

        if resp.length > options["maximum_response_size"] > 0:
            return True

        if any(text in resp.content for text in options["exclude_texts"]):
            return True

        if options["exclude_regex"] and re.search(options["exclude_regex"], resp.content):
            return True

        if (
            options["exclude_redirect"]
            and (
                options["exclude_redirect"] in resp.redirect
                or re.search(options["exclude_redirect"], resp.redirect)
            )
        ):
            return True

        return False

    def is_stopped(self):
        """
        判断是否所有的线程都已经停止运行。

        返回:
            bool: 当前线程数为零时返回True。
        """
        return self._running_threads_count == 0

    def decrease_threads(self):
        """
        减少活动线程计数。
        """
        self._running_threads_count -= 1

    def increase_threads(self):
        """
        增加活动线程计数。
        """
        self._running_threads_count += 1

    def set_base_path(self, path):
        """
        设置基础路径，后续拼接字典中读取到的相对路径。

        参数:
            path (str): 基础URL路径部分。
        """
        self._base_path = path

    def thread_proc(self):
        """
        工作线程主循环逻辑。从字典获取下一个路径，对其进行扫描。
        处理暂停、恢复以及延迟控制等操作。
        """
        self._play_event.wait()

        while True:
            try:
                path = next(self._dictionary)
                scanners = self.get_scanners_for(path)
                self.scan(self._base_path + path, scanners)

            except StopIteration:
                self._is_running = False

            except RequestException as e:
                for callback in self.error_callbacks:
                    callback(e)

                continue

            finally:
                if not self._play_event.is_set():
                    self.decrease_threads()
                    self._paused_semaphore.release()
                    self._play_event.wait()
                    self.increase_threads()

                if not self._is_running:
                    break

                time.sleep(options["delay"])
