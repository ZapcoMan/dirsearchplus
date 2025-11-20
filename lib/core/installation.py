import subprocess
import sys
import pkg_resources

from lib.core.exceptions import FailedDependenciesInstallation
from lib.core.settings import SCRIPT_PATH
from lib.utils.file import FileUtils

REQUIREMENTS_FILE = f"{SCRIPT_PATH}/requirements.txt"


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


# 检查所有依赖是否满足
def check_dependencies():
    """
    检查当前环境中是否已安装所有必需的依赖包
    使用pkg_resources模块验证依赖包是否满足要求
    """
    pkg_resources.require(get_dependencies())


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

