# dirsearchPlus

<div align="center">

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![Base](https://img.shields.io/badge/Powered%20by-dirsearch-orange)
![Modules](https://img.shields.io/badge/Modules-10%2B-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

**基于 dirsearch 的 Web 安全扫描增强工具**

一键串联目录扫描、403 绕过、JS 信息收集、指纹识别、前端打包器检测、Swagger 未授权、子域名爆破等多个安全测试模块。

[快速开始](#-快速开始) • [运行开关](#-运行开关与安全选项) • [模块详解](docs/modules.md) • [API 扫描](docs/api-scanning.md) • [更新日志](docs/changelog.md)

</div>

---

## 📖 项目简介

dirsearchPlus 是一个增强版的 Web 路径扫描工具，在原版 [dirsearch](https://github.com/maurosoria/dirsearch) 基础上集成了多个安全测试模块，并将它们编排为一条可容错、可阶段化运行的扫描流水线。

### ✨ 核心特性

- 🛠️ **目录扫描**：基于 dirsearch，支持线程、字典、状态码过滤、递归等
- 🔓 **403 绕过**：头部伪造 + URL 重写，支持对单条路径单独绕过
- 🔍 **JS 信息收集**：从 JavaScript 中提取 URL、子域名与敏感信息
- 🧾 **指纹识别**：集成 EHole，识别目标技术框架
- 📦 **前端打包器检测**：集成 Packer-Fuzzer（Webpack 等）
- 🌐 **Swagger 未授权**：对发现的接口做未授权访问测试
- 🔍 **子域名爆破**：集成 SubFinder（subfinder-x）
- ⚠️ **参数污染检测**：HPP/HFP 行为差异分析
- 🔥 **SSRF 深度探测** & 🧠 **动态 API 枚举**（基于行为推断）
- 🚀 **一键启用**：`-a` / `--all` 串联全部模块，单阶段异常不中断流水线

### 🧱 技术栈

| 分类 | 技术 / 组件 |
|------|-------------|
| **语言/运行时** | Python 3.7+（开发测试于 3.13） |
| **核心引擎** | dirsearch（`lib/` 下 connection / controller / parse / reports / utils / core） |
| **网络请求** | requests、urllib3、pyOpenSSL、ntlm-auth / requests_ntlm、pyspnego |
| **解析与匹配** | beautifulsoup4、tldextract、validators、chardet |
| **日志/输出** | loguru、colorama、pyfiglet、Jinja2 |
| **浏览器/报表**（可选） | Selenium、openpyxl（供 Swagger 扫描） |
| **外部工具** | EHole（指纹）、subfinder-x（子域名）、Packer-Fuzzer（打包器） |

---

## 🔄 运行流程

```
目录扫描 → 保存 403 状态路径 → JS 信息收集 → 403 绕过测试 → 指纹识别 → Packer-Fuzzer → 子域名爆破
```

各阶段以流水线方式串联：**单个阶段异常（含 `sys.exit`）不会中断整条流水线**，并会输出每个阶段的耗时。

---

## 🚀 快速开始

### 安装

```bash
# 核心依赖
pip install -r requirements.txt

# 可选：启用 Swagger 扫描的浏览器/报表能力
pip install -r requirements-browser.txt
```

> **环境要求**：最低 Python 3.7（启动时校验），当前开发与测试环境为 Python 3.13。`ehole`、`subfinder-x` 以可执行文件形式随仓库提供；`Packer-Fuzzer` 在首次启用时按需浅克隆。

### 基础使用

```bash
# 基础目录扫描
python dirsearchplus.py -u "http://www.example.com/"

# 分别启用 403 绕过 / JS 收集 / 子域名爆破
python dirsearchplus.py -u "http://www.example.com/" -b yes -j yes -d yes

# 一键启用所有模块
python dirsearchplus.py -u "http://www.example.com/" -a
```

### 实战示例（完整流水线 + 递归 + 内容过滤）

```bash
python dirsearchplus.py -u https://target.com -a -r --deep-recursive \
  --recursion-status 200-399 \
  --exclude-text "404" --exclude-text "Not Found" --exclude-text "Error" \
  -t 50 --wordlists .\db\simple_dicc.txt
```

---

## ⚙️ 运行开关与安全选项

在 dirsearch 原有参数之外，本工具额外提供运行时开关，用于日志、TLS 校验和外部依赖来源控制。这些开关会在启动时从命令行参数中摘除，不与 dirsearch 的参数解析冲突；也可通过环境变量设置。

| 开关 / 环境变量 | 说明 |
| --- | --- |
| `--debug` 或 `DIRSEARCHPLUS_DEBUG=1` | 启用控制台调试日志（将内部 logger 输出到终端），便于定位各阶段错误 |
| `--secure` 或 `DIRSEARCHPLUS_VERIFY_TLS=1` | 开启 TLS 证书校验（`verify=True`） |
| `--insecure` 或 `DIRSEARCHPLUS_INSECURE=1` | 显式关闭 TLS 证书校验（即扫描器默认行为，便于测试自签名/异常证书站点） |
| `PACKER_FUZZER_REF` | 锁定 Packer-Fuzzer 运行时克隆所使用的标签/分支名或提交 SHA，降低动态克隆的供应链风险 |

> **TLS 校验默认关闭**（便于安全测试场景）。若你的测试不需要绕过证书，推荐加上 `--secure` 提升安全性。

```bash
# 调试模式 + 强制 TLS 校验
python dirsearchplus.py -u "https://www.example.com/" -a --debug --secure
```

```powershell
# 锁定 Packer-Fuzzer 版本后再启用该模块
$env:PACKER_FUZZER_REF="v2.0"; python dirsearchplus.py -u "https://www.example.com/" -p yes
```

### 📦 依赖说明

- `requirements.txt`：核心运行依赖（完整清单，直接 `pip install -r requirements.txt`）。
- `requirements-browser.txt`：可选的浏览器 / 报表依赖（Selenium、openpyxl 及其 trio/websocket 依赖栈），主要供 **Swagger 扫描** 使用。未启用 Swagger 可不安装；缺依赖时 Swagger 阶段会自动优雅跳过，不影响整条流水线。

---

## 🧩 功能模块概览

| 模块 | 启用参数 | 作用 |
|------|----------|------|
| 目录扫描 | 默认 | 基于 dirsearch 的路径/目录爆破 |
| 403 绕过 | `-b yes` | 对 403 状态路径进行绕过测试 |
| JS 信息收集 | `-j yes` | 从 JS 中提取 URL / 子域名 / 敏感信息 |
| 指纹识别 | `-z yes` | 使用 EHole 识别技术框架 |
| Packer-Fuzzer | `-p yes` | 前端打包器检测与模糊测试 |
| Swagger 扫描 | `--swagger yes` | Swagger 接口未授权访问测试 |
| 子域名爆破 | `-d yes` | 使用 SubFinder 爆破子域名 |
| 参数污染 / SSRF / 动态 API | 随流水线自动 | 深度漏洞探测 |
| 全模块启动 | `-a` / `--all` | 一键启用上述所有模块 |

👉 每个模块的详细用法、单路径绕过、注意事项见：**[docs/modules.md](docs/modules.md)**
👉 框架专用字典、API 响应过滤与认证策略见：**[docs/api-scanning.md](docs/api-scanning.md)**

---

## 📂 项目结构

```
dirsearchplus/
├── dirsearchplus.py            # 主入口（流水线编排 + 运行时开关）
├── config.ini / options.ini    # 扫描配置
├── requirements.txt            # 核心依赖
├── requirements-browser.txt    # 可选浏览器/报表依赖（Swagger）
├── db/                         # 字典、黑/白名单
│   ├── api-endpoints.txt / spring-boot-*.txt / ruoyi-endpoints.txt
│   ├── simple_dicc.txt / dicc.txt
│   └── *_blacklist.txt / sensitive_whitelist.txt
├── resources/                  # 403 绕过 URL、敏感词白名单
├── docs/                       # 详细文档（本目录）
│   ├── README.md / modules.md / api-scanning.md / changelog.md
├── script/                     # 辅助脚本
│   ├── single_403pass.py       # 单路径 403 绕过
│   └── swagger.py              # Swagger 扫描
├── tests/                      # 单元测试（utils / parse / connection / reports）
└── lib/                        # 核心库
    ├── core/                   # 设置、选项、日志、敏感信息正则
    ├── controller/             # 扫描调度与报告写入
    ├── connection/             # 请求 / DNS
    ├── parse/                  # URL / Header 解析
    ├── reports/                # 报告生成
    ├── utils/                  # 工具函数
    ├── ehole/                  # 指纹识别（EHole）
    ├── subfinderX/             # 子域名爆破（SubFinder）
    ├── Packer-Fuzzer/          # 前端打包器检测
    ├── JSFinder.py             # JS 信息收集
    ├── pass403.py / pass403_optimized.py   # 403 绕过
    └── qc.py                   # 参数污染检测
```

---

## 🧪 测试说明

`tests/` 目录覆盖 dirsearch 核心的纯函数模块，便于二次改动后回归：

| 目录 | 覆盖内容 |
|------|----------|
| `tests/utils/` | common、crawl、diff、mimetype、random、schemedet |
| `tests/parse/` | URL 解析、请求头解析 |
| `tests/connection/` | DNS 解析 |
| `tests/reports/` | 报告生成 |

**运行：**

```bash
pip install pytest
pytest tests/                 # 运行全部单元测试
pytest tests/utils -v         # 运行指定目录
```

> `script/` 下另有若干手动验证脚本（`test_subfinder.py`、`test_sensitive_info.py`、`test_packer_import.py` 等），用于对特定外部模块做冒烟测试。

---

## 📚 更多文档

深入内容已抽离至 [`docs/`](docs/README.md)：

- **[docs/modules.md](docs/modules.md)** — 模块功能详解
- **[docs/api-scanning.md](docs/api-scanning.md)** — API 接口扫描指南
- **[docs/changelog.md](docs/changelog.md)** — 更新日志与历史提交

---

## 🙏 参考项目

本项目基于并参考了以下优秀开源项目：

- [dirsearch](https://github.com/maurosoria/dirsearch) — Web 路径扫描工具
- [403bypasser](https://github.com/yunemse48/403bypasser) — 403 绕过工具
- [JSFinder](https://github.com/Threezh1/JSFinder) — JavaScript 信息收集工具
- [EHole](https://github.com/EdgeSecurityTeam/EHole) — 指纹识别工具
- [Packer-Fuzzer](https://github.com/rtcatc/Packer-Fuzzer) — 前端打包器检测工具
- [SubFinder](https://github.com/kk12-30/subfinder-x) — 子域名爆破工具

---

## 📝 许可证

本项目基于 dirsearch 二次开发，遵循 [MIT License](LICENSE)，仅供学习交流与安全测试使用。

## 📬 联系方式

如有问题或建议，欢迎提交 Issue。

---

*最后更新时间：2026-10-07*
*最近变更：稳定性与安全加固（[0.1.6]，详见 [docs/changelog.md](docs/changelog.md)）*
