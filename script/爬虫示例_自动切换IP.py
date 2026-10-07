"""
爬虫示例 - Clash 自动切换 IP

演示如何用 Clash 自动切换服务来爬取网页
优化：
- 关闭 SSL 警告
- 只显示真实 IP
- 添加成功率统计
"""

import time
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

# 关闭 SSL 警告
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

from clash_auto_switch_service import ClashAutoSwitchService


def main():
    print("=" * 60)
    print("爬虫示例 - Clash 自动切换 IP")
    print("=" * 60)
    
    # 创建服务（每 10 秒自动切换节点）
    service = ClashAutoSwitchService(
        clash_secret="1212121",
        clash_proxy_port=7899,
        switch_interval=10,
    )
    
    # 启动自动切换
    service.start()
    print(f"当前节点: {service.get_current_node()}")
    print(f"可用节点数: {len(service.get_nodes())}")
    print(f"切换间隔: {service.switch_interval} 秒")
    print()
    
    # 统计
    total = 0
    success = 0
    failed = 0
    ips_seen = set()
    
    # 模拟爬取（只用 /ip 接口获取真实 IP）
    for i in range(20):
        url = "https://httpbin.org/ip"
        proxy = service.get_proxy()
        current_node = service.get_current_node()
        total += 1
        
        try:
            resp = requests.get(
                url,
                proxies=proxy,
                timeout=10,
                verify=False
            )
            
            if resp.status_code == 200:
                data = resp.json()
                ip = data.get("origin", "N/A")
                ips_seen.add(ip)
                success += 1
                print(f"请求 {total:2d} | 节点: {current_node:30s} | IP: {ip}")
            else:
                failed += 1
                print(f"请求 {total:2d} | 节点: {current_node:30s} | 状态码: {resp.status_code}")
        
        except Exception as e:
            failed += 1
            print(f"请求 {total:2d} | 节点: {current_node:30s} | 失败: {e}")
        
        # 等待 3 秒（10 秒会自动切换一次）
        time.sleep(3)
    
    # 手动切换演示
    print(f"\n{'='*60}")
    print("手动切换节点演示")
    print(f"{'='*60}")
    
    print(f"当前节点: {service.get_current_node()}")
    service.switch_node()
    print(f"切换后: {service.get_current_node()}")
    
    # 再请求一次看 IP 是否变化
    proxy = service.get_proxy()
    resp = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=10, verify=False)
    new_ip = resp.json().get("origin", "N/A")
    print(f"新 IP: {new_ip}")
    
    # 停止服务
    service.stop()
    
    # 打印统计
    print(f"\n{'='*60}")
    print("统计信息")
    print(f"{'='*60}")
    print(f"总请求数: {total}")
    print(f"成功: {success}")
    print(f"失败: {failed}")
    print(f"成功率: {success/total*100:.1f}%")
    print(f"使用过的 IP 数: {len(ips_seen)}")
    print(f"IP 列表: {', '.join(ips_seen)}")
    print("\n测试完成！")


if __name__ == "__main__":
    main()
