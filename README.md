# dirsearchPlus

dirsearchPlus 是一个增强版的 Web 路径扫描工具，在原版 dirsearch 基础上集成了多个安全测试模块，包括 403 绕过、JS 信息收集、指纹识别、前端打包器检测、子域名爆破等功能。

## 功能特性

- 🛠️ 基于 dirsearch 的目录扫描功能
- 🔓 403 绕过测试模块
- 🔍 JS 文件分析和信息提取
- 🧾 Web 应用指纹识别
- 📦 前端打包器检测（Packer-Fuzzer）
- 🌐 Swagger 接口未授权访问检测
- 🔍 子域名爆破扫描（SubFinder）
- 🚀 一键启用所有模块功能

## 运行流程

```
目录扫描 → 保存 403 状态路径 → JS 信息收集 → 403 绕过测试 → 指纹识别 → 子域名爆破
```

## 环境要求

- Python 版本：建议使用 Python < 3.10（兼容性考虑）
- 推荐测试环境：Python 3.8.20

## 快速开始

### 基础使用

```bash
# 基础目录扫描
python dirsearchX.py -u "http://www.example.com/"

# 启用 403 绕过功能
python dirsearchX.py -u "http://www.example.com/" -b yes

# 启用 JS 信息收集功能
python dirsearchX.py -u "http://www.example.com/" -j yes

# 启用子域名爆破功能
python dirsearchX.py -u "http://www.example.com/" -d yes

# 同时启用多个功能
python dirsearchX.py -u "http://www.example.com/" -b yes -j yes -d yes
```

### 一键启用所有功能

```bash
# 一键启用所有模块（403绕过、JS查找、指纹识别、Packer-Fuzzer、Swagger扫描、子域名扫描）
python dirsearchX.py -u "http://www.example.com/" -a
```

### 实际使用示例

```bash
# 针对特定网站的基础扫描
python dirsearchX.py -u https://www.lenovo.com.cn/ -a -r --deep-recursive --recursion-status 200-399 --exclude-text "404" --exclude-text "502" --exclude-text "Not Found" --exclude-text "Error" -t 50 --wordlists .\db\simple_dicc.txt

# 完整功能扫描（包含所有模块）
python dirsearchX.py -u https://www.lenovo.com.cn/ -b yes -j yes -z yes -p yes --swagger yes -d yes -r --deep-recursive --recursion-status 200-399 --exclude-text "404" --exclude-text "502" --exclude-text "Not Found" --exclude-text "Error" -t 50 --wordlists .\db\simple_dicc.txt
```

## 模块功能详解

### 403 绕过测试 (-b yes)

对扫描结果中 403 状态的路径进行绕过测试。

```bash
python dirsearchX.py -u "http://www.example.com/" -b yes
```

单独对指定目录进行绕过测试：

```bash
python single_403pass.py -u "http://www.example.com/" -p "/index.php"
```

### JS 信息收集 (-j yes)

从目标网站的 JavaScript 文件中提取 URL 和子域名信息。

```bash
python dirsearchX.py -u "http://www.example.com/" -j yes
```

### 指纹识别 (-z yes)

使用 EHole 进行网站指纹识别，识别目标使用的技术框架。

```bash
python dirsearchX.py -u "http://www.example.com/" -z yes
```

### Packer-Fuzzer (-p yes)

针对前端打包器（如 Webpack）的检测和模糊测试工具。

```bash
python dirsearchX.py -u "http://www.example.com/" -p yes
```

注意：如果提示模块已安装但仍报错，请删除 `/Packer-Fuzzer` 目录下的 `venv` 文件夹后重新运行。

### Swagger 扫描 (--swagger yes)

对发现的 Swagger 接口进行未授权访问测试。

```bash
python dirsearchX.py -u "http://www.example.com/" --swagger yes
```

### 子域名爆破 (-d yes)

使用 SubFinder 进行子域名爆破，发现目标的子域名信息。

```bash
python dirsearchX.py -u "http://www.example.com/" -d yes
```

该模块会自动从 resources/bypass403_url.txt 文件中读取目标域名，并进行子域名扫描。扫描结果将显示发现的子域名及其相关信息。

## API 接口扫描指南

现代 Web 应用程序通常使用前后端分离架构，API 接口扫描已经成为渗透测试的重要环节。

### 使用专门的字典文件

```bash
# 扫描常见 API 端点
python dirsearchX.py -u https://target.com -w db/api-endpoints.txt -e json,xml

# 扫描 RESTful 资源
python dirsearchX.py -u https://target.com --wordlists db/api-endpoints.txt

# 扫描 Spring Boot 应用
python dirsearchX.py -u https://target.com --wordlists db/spring-boot-endpoints.txt

# 扫描 Spring Boot Actuator 端点
python dirsearchX.py -u https://target.com --wordlists db/spring-boot-actuator.txt

# 扫描 RuoYI 框架应用
python dirsearchX.py -u https://target.com --wordlists db/ruoyi-endpoints.txt
```

### 框架专用字典说明

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

### 针对 API 响应特点的处理

由于现代 API 通常返回 200 状态码，即使是错误响应，因此需要基于响应内容进行过滤：

```bash
# 排除常见的错误响应内容
python dirsearchX.py -u https://target.com \
  --exclude-text "Not Found" \
  --exclude-text "Error" \
  --exclude-text "404" \
  --exclude-regex "\"error\":\s*true"

# 根据响应大小过滤
python dirsearchX.py -u https://target.com \
  --exclude-sizes 0B,2KB \
  --exclude-text "页面不存在"
```

### RESTful API 扫描策略

```bash
# 扫描常见的 RESTful 资源和 HTTP 方法
python dirsearchX.py -u https://target.com/api/ \
  -w db/api-endpoints.txt \
  --exclude-status 405

# 使用递归扫描深入 API 结构
python dirsearchX.py -u https://target.com/api/ \
  -r --deep-recursive \
  --recursion-status 200-399
```

### 自定义请求头和认证

API 通常需要特定的请求头或认证：

```bash
# 添加 API 密钥或认证头
python dirsearchX.py -u https://target.com/api/ \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

## 更新日志

### 最新更新

- 集成 SubFinder 子域名爆破模块，用于发现目标的子域名信息
- 添加 `-d yes` 参数启用子域名扫描功能
- 优化各模块间的数据传递和协调工作

### 2023.5.11 优化更新

- 优化原版 403bypasser，支持单独对某一指定路径进行 403 绕过
- 添加 `single_403pass.py` 脚本，可对单个 URL 的指定路径进行 403 绕过

### 3.1 版本新增

- 集成 Packer-Fuzzer 模块，用于前端打包器检测和模糊测试
- 集成 Swagger 未授权访问扫描功能

### 3.3 版本新增

- 添加 `-a` 或 `--all` 参数，可一键启用所有功能模块

## 参考项目

本项目基于并参考了以下优秀开源项目：

- [dirsearch](https://github.com/maurosoria/dirsearch) - Web 路径扫描工具
- [403bypasser](https://github.com/yunemse48/403bypasser) - 403 绕过工具
- [JSFinder](https://github.com/Threezh1/JSFinder) - JavaScript 信息收集工具
- [EHole](https://github.com/EdgeSecurityTeam/EHole) - 指纹识别工具
- [Packer-Fuzzer](https://github.com/rtcatc/Packer-Fuzzer) - 前端打包器检测工具
- [SubFinder](https://github.com/kk12-30/subfinder-x) - 子域名爆破工具



# 更新日志 (Change Log)

## [0.1.4] - 最新更新
### 新增功能
- 集成SubFinder子域名扫描模块，用于发现目标的子域名信息
- 添加`-d yes`参数启用子域名扫描功能
- 优化各模块间的数据传递和协调工作

## [0.1.3] - by ZapcoMan
### 新增功能
- 集成Packer-Fuzzer模块，用于前端打包器检测和模糊测试
- 集成Swagger未授权访问扫描功能
- 添加多个专用API字典文件：
  - `db/api-endpoints.txt`: 通用API端点字典
  - `db/spring-boot-endpoints.txt`: Spring Boot专用字典
  - `db/spring-boot-actuator.txt`: Spring Boot Actuator字典
  - `db/ruoyi-endpoints.txt`: RuoYI框架字典

### 改进优化
- 优化403绕过功能，提供单独路径绕过能力
- 改进JSFinder模块，增强子域名发现功能
- 统一各模块日志输出格式，与dirsearch保持一致
- 修复ehole模块中"系统找不到指定的路径"错误问题
- 修复Packer-Fuzzer模块导入错误问题

### 使用说明更新
- 添加`-p yes`参数启用Packer-Fuzzer模块
- 添加`--swagger yes`参数启用Swagger扫描
- 添加`-a`或`--all`参数一键启用所有模块
- 更新API接口扫描指南和使用示例

## 历史更新记录

### 最近提交记录
根据git历史记录，最近的主要更新包括：

1. **feat(SubFinder)**: 集成子域名扫描功能
   - 添加SubFinder模块，用于子域名爆破扫描
   - 集成subfinder-x.exe工具，支持HTTP扫描和指纹识别
   - 优化文件路径处理，确保在不同环境下都能正确运行
   - 统一控制台输出格式，增强可读性与调试便利性

2. **feat(Packer-Fuzzer)**: 集成自定义日志系统并优化错误处理
   - 在多个模块中引入并使用Packer-Fuzzer自带的CreatLog日志系统
   - 为HTML检查过程添加异常捕获和错误日志记录
   - 统一控制台输出格式，增强可读性与调试便利性
   - 更新语言配置文件中的提示文本内容
   - 优化代理测试模块的异常处理逻辑
   - 规范化代码注释与日志输出内容的表述方式

3. **feat(cli)**: 添加全模块启动选项
   - 添加`-a`或`--all`参数，可一键启用所有功能模块(bypass, jsfind, zwsb, packer-fuzzer, swagger, subfinder)

4. **feat(core)**: 增强终端输出功能并优化日志显示

5. **feat(dirsearchplus)**: 优化JsFind和Packer-Fuzzer功能并改进输出格式

6. **feat(ehole)**: 更新指纹识别规则并优化扫描输出格式

### 2023.5.11
- 优化原版403bypasser，支持单独对某一指定路径进行403绕过
- 添加single_403pass.py脚本，可对单个URL的指定路径进行403绕过

## 功能模块说明

### 目录扫描 (dirsearch)
基础目录扫描功能，支持多种自定义选项。

### 403绕过 (-b yes)
对扫描结果中403状态的路径进行绕过测试。

### JS查找 (-j yes)
从目标网站的JavaScript文件中提取URL和子域名信息。

### 指纹识别 (-z yes)
使用EHole进行网站指纹识别，识别目标使用的技术框架。

### Packer-Fuzzer (-p yes)
针对前端打包器（如Webpack）的检测和模糊测试工具。

### Swagger扫描 (--swagger yes)
对发现的Swagger接口进行未授权访问测试。

### 子域名扫描 (-d yes)
使用SubFinder进行子域名爆破扫描，发现目标相关的子域名。

### 全模块启动 (-a)
使用单一参数启用所有上述功能模块。