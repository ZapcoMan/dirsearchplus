# API 接口扫描指南

> 本文档从主 [README](../README.md) 抽离，专注 API 端点扫描的字典选择与响应过滤策略。
> 返回文档目录：[docs/README.md](README.md)

现代 Web 应用通常采用前后端分离架构，API 接口扫描已成为渗透测试的重要环节。dirsearchPlus 内置了多套面向常见 Java Web 框架的专用字典。

## 使用专门的字典文件

```bash
# 扫描常见 API 端点
python dirsearchplus.py -u https://target.com -w db/api-endpoints.txt -e json,xml

# 扫描 RESTful 资源
python dirsearchplus.py -u https://target.com --wordlists db/api-endpoints.txt

# 扫描 Spring Boot 应用
python dirsearchplus.py -u https://target.com --wordlists db/spring-boot-endpoints.txt

# 扫描 Spring Boot Actuator 端点
python dirsearchplus.py -u https://target.com --wordlists db/spring-boot-actuator.txt

# 扫描 RuoYI 框架应用
python dirsearchplus.py -u https://target.com --wordlists db/ruoyi-endpoints.txt
```

## 框架专用字典说明

本工具针对常见的 Java Web 框架提供了专用的 API 端点字典文件：

1. **通用 API 字典** (`db/api-endpoints.txt`)
   - 包含 500 多个常见的 API 端点路径
   - 适用于各种 Web 应用的初步扫描

2. **Spring Boot 专用字典** (`db/spring-boot-endpoints.txt`)
   - 包含 600 多个 Spring Boot 应用常见端点
   - 涵盖 Actuator、业务 API、安全认证等路径

3. **Spring Boot Actuator 字典** (`db/spring-boot-actuator.txt`)
   - 专门针对 Spring Boot Actuator 管理端点
   - 包含健康检查、监控、配置等敏感路径

4. **RuoYI 框架字典** (`db/ruoyi-endpoints.txt`)
   - 专门针对 RuoYI 开源框架的 API 端点
   - 包含用户管理、角色权限、系统监控等模块路径

## 针对 API 响应特点的处理

由于现代 API 通常即使对于错误响应也返回 200 状态码，因此需要基于响应内容进行过滤：

```bash
# 排除常见的错误响应内容
python dirsearchplus.py -u https://target.com \
  --exclude-text "Not Found" \
  --exclude-text "Error" \
  --exclude-text "404" \
  --exclude-regex "\"error\":\s*true"

# 根据响应大小过滤
python dirsearchplus.py -u https://target.com \
  --exclude-sizes 0B,2KB \
  --exclude-text "页面不存在"
```

## RESTful API 扫描策略

```bash
# 扫描常见的 RESTful 资源和 HTTP 方法
python dirsearchplus.py -u https://target.com/api/ \
  -w db/api-endpoints.txt \
  --exclude-status 405

# 使用递归扫描深入 API 结构
python dirsearchplus.py -u https://target.com/api/ \
  -r --deep-recursive \
  --recursion-status 200-399
```

## 自定义请求头和认证

API 通常需要特定的请求头或认证：

```bash
# 添加 API 密钥或认证头
python dirsearchplus.py -u https://target.com/api/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

---

返回主文档：[README](../README.md) ｜ 文档目录：[docs/README.md](README.md)
