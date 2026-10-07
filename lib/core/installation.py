import re
import subprocess
import sys
import importlib.metadata

from lib.core.exceptions import FailedDependenciesInstallation
from lib.core.settings import SCRIPT_PATH
from lib.utils.file import FileUtils

REQUIREMENTS_FILE = f"{SCRIPT_PATH}/requirements.txt"


class DistributionNotFound(Exception):
    """所需的依赖包未安装"""


class VersionConflict(Exception):
    """已安装的版本不满足 requirements.txt 的要求"""


def get_dependencies():
    """
    从requirements.txt文件中读取依赖列表

    Returns:
        list: 包含所有依赖项的列表

    Raises:
        FileNotFoundError: 当找不到requirements.txt文件时退出程序
    """
    try:
        return FileUtils.get_lines(REQUIREMENTS_FILE)
    except FileNotFoundError:
        print("Can't find requirements.txt")
        exit(1)


def _parse_version(version):
    """
    将版本号拆分为可比较的整数/字符串元组，避免依赖 packaging

    支持形如 1.2.3、1.2.3.post1、1.2.3rc1 等常见后缀，
    仅用于满足 requirements.txt 中的==、>=、<=、>、<、!= 比较需求。
    """
    parts = []
    for token in re.split(r"[.\-+]", version.strip()):
        if token.isdigit():
            parts.append((0, int(token)))
        else:
            parts.append((1, token))
    return tuple(parts)


def _compare(installed, spec_version):
    """返回 installed 与 spec_version 的比较结果: -1 / 0 / 1"""
    a, b = _parse_version(installed), _parse_version(spec_version)
    # 补齐长度，缺位按最小值处理
    length = max(len(a), len(b))
    a = a + ((0, 0),) * (length - len(a))
    b = b + ((0, 0),) * (length - len(b))
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def _check_requirement(line):
    """
    校验单条 requirement 是否被当前环境满足

    解析形如 ``name==1.2.3`` / ``name>=1.2`` 的行，
    忽略行内注释、extras 与环境标记。
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return

    # 去掉行内注释、环境标记
    line = line.split("#", 1)[0].split(";", 1)[0].strip()
    if not line:
        return

    # 拆分为 (包名, [(操作符, 版本), ...])
    tokens = re.split(r"(===|==|!=|>=|<=|~=|>|<)", line)
    name = tokens[0].split("[", 1)[0].strip()
    if not name:
        return

    specs = list(zip(tokens[1::2], tokens[2::2]))

    try:
        installed = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        raise DistributionNotFound(f"Required distribution '{name}' is not installed")

    for op, want in specs:
        want = want.strip()
        result = _compare(installed, want)
        satisfied = {
            "==": result == 0,
            "===": installed == want,
            "!=": result != 0,
            ">=": result >= 0,
            "<=": result <= 0,
            ">": result > 0,
            "<": result < 0,
            "~=": result >= 0,
        }.get(op, True)

        if not satisfied:
            raise VersionConflict(
                f"Installed '{name}' version {installed} does not satisfy {op}{want}"
            )


# 检查所有依赖是否满足
def check_dependencies():
    """
    检查当前环境中是否已安装所有必需的依赖包

    使用标准库 importlib.metadata 校验依赖是否满足 requirements.txt 的要求，
    取代已弃用的 pkg_resources。
    """
    for line in get_dependencies():
        _check_requirement(line)


def install_dependencies():
    """
    安装项目所需的所有依赖包

    通过调用pip命令安装requirements.txt中列出的所有依赖包

    Raises:
        FailedDependenciesInstallation: 当依赖安装失败时抛出异常
    """
    try:
        subprocess.check_output(
            [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        raise FailedDependenciesInstallation
