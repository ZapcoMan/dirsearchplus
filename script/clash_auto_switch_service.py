"""
Clash 自动切换代理服务 - 独立模块

功能：
- 自动按时间间隔切换 Clash 节点
- 手动切换节点
- 提供 requests 兼容的代理地址
- 后台线程自动运行

用法：
    1. 把这个文件复制到你的爬虫项目
    2. from clash_auto_switch_service import start_auto_switch, get_proxy, switch_node
    3. 启动服务后直接用
"""

import requests
import threading
import time
from typing import Optional, List
from loguru import logger


class ClashAPI:
    """Clash API 调用"""
    
    def __init__(self, base_api: str, secret: str):
        self.base_api = base_api
        self.headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    
    def get_proxies(self) -> dict:
        resp = requests.get(
            f"{self.base_api}/proxies",
            headers=self.headers,
            timeout=5,
            verify=False
        )
        return resp.json().get("proxies", {})
    
    def switch_proxy(self, group_name: str, proxy_name: str):
        requests.put(
            f"{self.base_api}/proxies/{group_name}",
            headers=self.headers,
            json={"name": proxy_name},
            timeout=5,
            verify=False
        )
    
    def get_group_nodes(self, group_name: str) -> List[str]:
        proxies = self.get_proxies()
        if group_name in proxies:
            return proxies[group_name].get("all", [])
        return []
    
    def auto_detect_group(self) -> Optional[str]:
        proxies = self.get_proxies()
        for name in ["Proxy", "PROXY", "全局", "GLOBAL"]:
            if name in proxies and proxies[name].get("type") == "Selector":
                return name
        for name, info in proxies.items():
            if info.get("type") == "Selector":
                return name
        return None
    
    def get_current_node(self, group_name: str) -> Optional[str]:
        proxies = self.get_proxies()
        if group_name in proxies:
            return proxies[group_name].get("now")
        return None


class ClashAutoSwitchService:
    """
    Clash 自动切换代理服务
    
    用法：
        service = ClashAutoSwitchService(
            clash_secret="1212121",
            clash_proxy_port=7899,
            switch_interval=30,
        )
        service.start()
        
        proxy = service.get_proxy()
        response = requests.get(url, proxies=proxy)
        
        service.switch_node()  # 手动切换
        service.stop()
    """
    
    def __init__(
        self,
        clash_api: str = "http://127.0.0.1:9090",
        clash_secret: str = "",
        clash_proxy_port: int = 7899,
        switch_interval: int = 30,
    ):
        self.api = ClashAPI(clash_api, clash_secret)
        self.proxy_port = clash_proxy_port
        self.switch_interval = switch_interval
        
        self._group_name: Optional[str] = None
        self._nodes: List[str] = []
        self._current_index: int = 0
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        self._init_nodes()
    
    def _init_nodes(self):
        self._group_name = self.api.auto_detect_group()
        if self._group_name:
            self._nodes = self.api.get_group_nodes(self._group_name)
            current = self.api.get_current_node(self._group_name)
            if current and current in self._nodes:
                self._current_index = self._nodes.index(current)
            
            logger.info(
                f"策略组: {self._group_name}, "
                f"节点数: {len(self._nodes)}, "
                f"当前: {current}"
            )
        else:
            logger.warning("未找到可用策略组")
    
    def start(self):
        if self._running:
            logger.warning("服务已在运行")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._auto_switch_loop, daemon=True)
        self._thread.start()
        logger.info(f"自动切换服务已启动 (间隔: {self.switch_interval}秒)")
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("自动切换服务已停止")
    
    def _auto_switch_loop(self):
        while self._running:
            time.sleep(self.switch_interval)
            if self._running:
                self.switch_node()
    
    def switch_node(self, node_name: Optional[str] = None) -> bool:
        with self._lock:
            if not self._nodes:
                logger.warning("无可用节点")
                return False
            
            if node_name:
                if node_name not in self._nodes:
                    logger.error(f"节点不存在: {node_name}")
                    return False
                self._current_index = self._nodes.index(node_name)
            else:
                self._current_index = (self._current_index + 1) % len(self._nodes)
            
            target_node = self._nodes[self._current_index]
            
            try:
                self.api.switch_proxy(self._group_name, target_node)
                logger.success(f"已切换节点: {target_node}")
                return True
            except Exception as e:
                logger.error(f"切换失败: {e}")
                return False
    
    def get_proxy(self) -> dict:
        proxy_url = f"http://127.0.0.1:{self.proxy_port}"
        return {
            "http": proxy_url,
            "https": proxy_url,
        }
    
    def get_current_node(self) -> Optional[str]:
        if not self._nodes:
            return None
        return self._nodes[self._current_index]
    
    def get_nodes(self) -> List[str]:
        return self._nodes.copy()
    
    def set_switch_interval(self, seconds: int):
        self.switch_interval = seconds
        logger.info(f"切换间隔已设置为 {seconds} 秒")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()


# 全局单例
_global_service = None

def get_service() -> ClashAutoSwitchService:
    global _global_service
    if _global_service is None:
        _global_service = ClashAutoSwitchService(
            clash_secret="1212121",
            clash_proxy_port=7899,
            switch_interval=30,
        )
    return _global_service


def start_auto_switch(interval: int = 30):
    service = get_service()
    service.set_switch_interval(interval)
    service.start()
    return service


def stop_auto_switch():
    global _global_service
    if _global_service:
        _global_service.stop()
        _global_service = None


def switch_node(node_name: Optional[str] = None):
    return get_service().switch_node(node_name)


def get_proxy() -> dict:
    return get_service().get_proxy()


if __name__ == "__main__":
    print("=" * 60)
    print("Clash 自动切换代理服务 - 测试")
    print("=" * 60)
    
    service = ClashAutoSwitchService(
        clash_secret="1212121",
        clash_proxy_port=7899,
        switch_interval=10,
    )
    
    service.start()
    
    print("\n开始爬虫请求...")
    for i in range(30):
        proxy = service.get_proxy()
        current_node = service.get_current_node()
        
        try:
            resp = requests.get(
                "https://httpbin.org/ip",
                proxies=proxy,
                timeout=10,
                verify=False
            )
            print(f"请求 {i+1:2d} | 节点: {current_node:20s} | IP: {resp.json()['origin']}")
        except Exception as e:
            print(f"请求 {i+1:2d} | 节点: {current_node:20s} | 失败: {e}")
        
        time.sleep(2)
    
    service.stop()
    print("\n测试完成！")