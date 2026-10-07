"""
Clash 节点自动轮转代理 - 依赖库

用途：为 dirsearchPlus 的“Clash 自动切换IP模式”提供后台节点轮转能力。
- 通过 Clash 的外部控制器(external-controller) RESTful API 按时间间隔轮转 Selector 策略组节点；
- 对外暴露一个固定的本地 HTTP 混合端口(mixed-port / 7899)，所有扫描请求都走该端口，
  节点在后台被切换，从而实现“边扫描边换出口 IP”。

⚠️ 启动本模式的前置条件（缺一不可，否则无法换 IP）：
1. 已在 Clash(核) 配置中开启“外部控制器 external-controller”；
2. 已正确设置“外部控制器监听地址 external-controller”（默认 http://127.0.0.1:9090）；
3. 已设置“外部控制器 API 密钥 secret”（若配置了 secret，则必须提供正确的密钥）。

本模块不向 stdout 打印业务日志，仅通过项目统一的 logger 记录，
以便被 dirsearchPlus 的 --debug / 日志文件机制接管；面向用户的启动/停止提示
由调用方(dirsearchplus.py)基于 describe()/stats() 输出。
"""

import time
import threading
from typing import List, Optional

import requests

from lib.core.logger import logger
import lib.core.settings as settings


class ClashControllerError(Exception):
    """Clash 外部控制器连接/鉴权/配置错误，携带面向用户的中文提示"""


class ClashAPI:
    """对 Clash 外部控制器 RESTful API 的薄封装"""

    def __init__(self, base_api: str, secret: str):
        # 容错：用户常省略协议头(如 127.0.0.1:9090)，自动补 http://；去除末尾斜杠统一拼接
        base_api = (base_api or "").strip()
        if base_api and not base_api.lower().startswith(("http://", "https://")):
            base_api = "http://" + base_api
        self.base_api = base_api.rstrip("/")
        self.headers = {"Authorization": f"Bearer {secret}"} if secret else {}

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_api}{path}"
        # 控制器地址允许是自签 https，统一走中枢化 TLS 开关
        return requests.request(
            method,
            url,
            headers=self.headers,
            timeout=kwargs.pop("timeout", 5),
            verify=settings.VERIFY_TLS,
            **kwargs,
        )

    def get_proxies(self) -> dict:
        resp = self._request("GET", "/proxies")
        if resp.status_code in (401, 403):
            raise ClashControllerError(
                "外部控制器 API 密钥(secret)不正确或被拒绝访问，请检查 --clash-secret。"
            )
        resp.raise_for_status()
        return resp.json().get("proxies", {})

    def switch_proxy(self, group_name: str, proxy_name: str):
        resp = self._request(
            "PUT", f"/proxies/{group_name}", json={"name": proxy_name}
        )
        if resp.status_code in (401, 403):
            raise ClashControllerError(
                "外部控制器 API 密钥(secret)不正确，切换节点被拒绝。"
            )
        resp.raise_for_status()

    def get_group_nodes(self, group_name: str) -> List[str]:
        proxies = self.get_proxies()
        if group_name in proxies:
            return proxies[group_name].get("all", [])
        return []

    def auto_detect_group(self) -> Optional[str]:
        """自动挑选一个 Selector 类型的策略组用于轮转"""
        proxies = self.get_proxies()
        for name in ("PROXY", "Proxy", "全局", "GLOBAL", "节点选择"):
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


class ClashProxyRotator:
    """
    Clash 节点后台轮转器。

    典型用法（由 dirsearchPlus 主程序调用）：
        rotator = ClashProxyRotator(clash_api, secret, proxy_port, interval)
        rotator.check_prerequisites()   # 连接/鉴权/策略组校验，失败抛 ClashControllerError
        rotator.start()                 # 启动后台轮转线程
        proxy_url = rotator.get_proxy_url()  # 注入到 options["proxies"]
        ...
        rotator.stop()                  # 扫描结束停止线程
    """

    def __init__(
        self,
        clash_api: str = "http://127.0.0.1:9090",
        clash_secret: str = "",
        clash_proxy_port: int = 7899,
        switch_interval: int = 30,
    ):
        self.api = ClashAPI(clash_api, clash_secret)
        # 保存规范化后的地址，供错误提示展示，避免协议头缺失造成误解
        self.clash_api = self.api.base_api
        self.proxy_port = clash_proxy_port
        self.switch_interval = max(1, int(switch_interval))

        self._group_name: Optional[str] = None
        self._nodes: List[str] = []
        self._current_index: int = 0
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        # 运行时统计：成功切换次数 / 失败次数，供状态展示
        self._switch_ok: int = 0
        self._switch_fail: int = 0

    # ------------------------------------------------------------------ #
    # 前置校验
    # ------------------------------------------------------------------ #
    def check_prerequisites(self):
        """
        校验外部控制器可达、密钥正确、存在可用 Selector 策略组。
        任一条件不满足抛出 ClashControllerError（附带可操作的中文提示）。
        """
        try:
            self.api.get_proxies()
        except ClashControllerError:
            # 鉴权类错误(401/403)已带明确提示，直接上抛
            raise
        except requests.exceptions.Timeout as e:
            raise ClashControllerError(
                f"连接 Clash 外部控制器({self.clash_api})超时。"
                "请确认地址与端口正确、Clash 正在运行；如为远程控制器请检查防火墙/网络。"
            )
        except requests.exceptions.SSLError as e:
            raise ClashControllerError(
                f"与 Clash 外部控制器({self.clash_api})建立 TLS 连接失败：证书校验未通过。"
                "若控制器为自签证书，可加 --insecure 或设置 DIRSEARCHPLUS_VERIFY_TLS 关闭校验。"
            )
        except requests.exceptions.ConnectionError as e:
            raise ClashControllerError(
                "无法连接到 Clash 外部控制器 "
                f"({self.clash_api})。请确认：①已在 Clash 配置中开启 external-controller；"
                "②外部控制器监听地址(--clash-api)填写正确；③Clash 正在运行。"
            )
        except requests.exceptions.RequestException as e:
            raise ClashControllerError(
                f"访问 Clash 外部控制器({self.clash_api})失败：{e}"
            )

        self._group_name = self.api.auto_detect_group()
        if not self._group_name:
            raise ClashControllerError(
                "已连接控制器但未找到可用的 Selector 策略组，"
                "请确认 Clash 配置中存在手动选择(Selector)模式的代理分组。"
            )

        self._nodes = self.api.get_group_nodes(self._group_name)
        if len(self._nodes) < 2:
            raise ClashControllerError(
                f"策略组 '{self._group_name}' 内可用节点不足(当前 {len(self._nodes)} 个)，"
                "至少需要 2 个节点才能实现自动换 IP。"
            )

        current = self.api.get_current_node(self._group_name)
        if current and current in self._nodes:
            self._current_index = self._nodes.index(current)

        logger.debug(
            f"Clash 前置校验通过: 策略组={self._group_name}, 节点数={len(self._nodes)}, 当前={current}"
        )

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    def start(self):
        if self._running:
            return
        # 若尚未经过校验（例如被第三方直接调用），这里补一次初始化
        if not self._nodes:
            self.check_prerequisites()
        self._running = True
        self._thread = threading.Thread(target=self._auto_switch_loop, daemon=True)
        self._thread.start()
        logger.debug(f"Clash 轮转已启动 (间隔 {self.switch_interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.debug("Clash 轮转已停止")

    def _auto_switch_loop(self):
        consecutive_fail = 0
        while self._running:
            # 先睡一个周期再切换，保证首个周期使用当前节点（支持提前 stop 响应）
            slept = 0
            while self._running and slept < self.switch_interval:
                time.sleep(0.5)
                slept += 0.5
            if not self._running:
                break
            # switch_node 内部已捕获异常并回滚，这里只负责记录连续失败，避免静默失效
            if self.switch_node():
                consecutive_fail = 0
            else:
                consecutive_fail += 1
                if consecutive_fail in (3, 10):
                    logger.warning(
                        f"Clash: 已连续 {consecutive_fail} 次切换失败，"
                        "出口 IP 可能未变化，请检查外部控制器/节点是否可用。"
                    )

    # ------------------------------------------------------------------ #
    # 节点操作
    # ------------------------------------------------------------------ #
    def switch_node(self, node_name: Optional[str] = None) -> bool:
        """切换到下一个(或指定)节点。失败时回滚索引，保持与实际状态一致。"""
        with self._lock:
            if not self._nodes:
                logger.warning("Clash: 无可用节点，跳过切换")
                return False

            prev_index = self._current_index
            if node_name:
                if node_name not in self._nodes:
                    logger.error(f"Clash: 节点不存在 {node_name}")
                    return False
                self._current_index = self._nodes.index(node_name)
            else:
                self._current_index = (self._current_index + 1) % len(self._nodes)

            target = self._nodes[self._current_index]
            try:
                self.api.switch_proxy(self._group_name, target)
                self._switch_ok += 1
                logger.debug(f"Clash: 已切换节点 -> {target} (累计成功 {self._switch_ok} 次)")
                return True
            except Exception as e:
                # 切换失败回滚，避免本地索引与 Clash 实际节点脱节
                self._current_index = prev_index
                self._switch_fail += 1
                logger.error(f"Clash: 切换节点失败(已回滚): {e}")
                return False

    def get_proxy_url(self) -> str:
        """返回供 dirsearch 使用的本地代理地址(scheme://host:port)"""
        return f"http://127.0.0.1:{self.proxy_port}"

    def get_current_node(self) -> Optional[str]:
        """优先向控制器实时查询真实节点，查询失败时退回本地索引"""
        if self._group_name:
            try:
                node = self.api.get_current_node(self._group_name)
                if node:
                    return node
            except Exception as e:
                logger.debug(f"Clash: 实时查询当前节点失败，回退本地索引: {e}")
        if self._nodes:
            return self._nodes[self._current_index]
        return None

    def get_nodes(self) -> List[str]:
        return list(self._nodes)

    def stats(self) -> dict:
        """返回运行时统计，供上层展示/日志使用"""
        return {
            "group": self._group_name,
            "nodes": len(self._nodes),
            "current": self.get_current_node(),
            "switch_ok": self._switch_ok,
            "switch_fail": self._switch_fail,
        }

    def describe(self) -> str:
        """返回一行简洁状态描述，统一供主程序启动/停止提示使用"""
        s = self.stats()
        return (
            f"策略组={s['group']} | 可用节点={s['nodes']} | 当前节点={s['current']} | "
            f"代理={self.get_proxy_url()} | 切换成功={s['switch_ok']} 次/失败={s['switch_fail']} 次"
        )
