import threading

from functools import wraps
from time import time

_lock = threading.Lock()
_cache = {}
_cache_lock = threading.Lock()


def cached(timeout=100):
    """
    缓存装饰器工厂函数，用于创建带有缓存功能的装饰器

    参数:
        timeout (int): 缓存超时时间，单位为秒，默认为100秒

    返回:
        function: 返回一个装饰器函数
    """
    def _cached(func):
        """
        实际的缓存装饰器函数

        参数:
            func (function): 被装饰的函数

        返回:
            function: 返回包装后的函数
        """
        @wraps(func)
        def with_caching(*args, **kwargs):
            """
            带有缓存功能的包装函数

            参数:
                *args: 函数的位置参数
                **kwargs: 函数的关键字参数

            返回:
                any: 函数执行结果或缓存的结果
            """
            # 生成缓存键值，基于函数ID和参数ID
            key = id(func)
            for arg in args:
                key += id(arg)
            for k, v in kwargs:
                key += id(k) + id(v)

            # 检查缓存是否存在且未超时
            if key in _cache and time() - _cache[key][0] < timeout:
                return _cache[key][1]

            # 执行函数并更新缓存
            with _cache_lock:
                result = func(*args, **kwargs)
                _cache[key] = (time(), result)

            return result

        return with_caching

    return _cached


def locked(func):
    """
    线程锁装饰器，用于确保函数在多线程环境下的安全执行

    参数:
        func (function): 被装饰的函数

    返回:
        function: 返回带锁机制的包装函数
    """
    def with_locking(*args, **kwargs):
        """
        带有线程锁的包装函数

        参数:
            *args: 函数的位置参数
            **kwargs: 函数的关键字参数

        返回:
            any: 函数执行结果
        """
        # 使用全局锁确保同一时间只有一个线程执行该函数
        with _lock:
            return func(*args, **kwargs)

    return with_locking

