import os
import os.path


class File:
    """
    文件操作封装类，用于统一处理文件路径及常用文件操作。

    :param path_components: 可变数量的路径组件，将通过系统路径分隔符连接成完整路径。
    """

    def __init__(self, *path_components):
        self._path = FileUtils.build_path(*path_components)

    @property
    def path(self):
        """
        获取当前文件对象的路径。

        :return: 当前文件路径字符串。
        """
        return self._path

    @path.setter
    def path(self, value):
        """
        禁止修改路径属性。

        :param value: 新路径值（未使用）。
        :raises NotImplementedError: 总是抛出该异常以阻止设置新路径。
        """
        raise NotImplementedError

    def is_valid(self):
        """
        判断当前路径是否是一个有效的文件。

        :return: 如果路径指向一个存在的普通文件则返回True，否则返回False。
        """
        return FileUtils.is_file(self.path)

    def exists(self):
        """
        检查当前路径对应的文件是否存在。

        :return: 存在返回True，否则返回False。
        """
        return FileUtils.exists(self.path)

    def can_read(self):
        """
        检查当前文件是否可读。

        :return: 可读返回True，否则返回False。
        """
        return FileUtils.can_read(self.path)

    def can_write(self):
        """
        检查当前文件是否可写。

        :return: 可写返回True，否则返回False。
        """
        return FileUtils.can_write(self.path)

    def read(self):
        """
        读取整个文件的内容。

        :return: 返回文件内容字符串。
        """
        return FileUtils.read(self.path)

    def get_lines(self):
        """
        逐行读取文件内容并返回列表。

        :return: 包含每一行文本的列表。
        """
        return FileUtils.get_lines(self.path)

    def __enter__(self):
        """
        支持with语句上下文管理协议。

        :return: 当前File实例。
        """
        return self

    def __exit__(self, type, value, tb):
        """
        上下文退出时调用的方法。目前为空实现。

        :param type: 异常类型。
        :param value: 异常值。
        :param tb: 回溯信息。
        """
        pass


class FileUtils:
    """
    提供静态方法进行各种文件和目录相关操作的工具类。
    """

    @staticmethod
    def build_path(*path_components):
        """
        使用系统默认路径分隔符连接多个路径部分形成完整路径。

        :param path_components: 路径片段组成的元组。
        :return: 连接后的完整路径字符串；若无输入则返回空字符串。
        """
        if path_components:
            path = os.path.join(*path_components)
        else:
            path = ""

        return path

    @staticmethod
    def get_abs_path(file_name):
        """
        获取指定文件名的绝对路径。

        :param file_name: 相对或绝对路径的文件名。
        :return: 对应的绝对路径字符串。
        """
        return os.path.abspath(file_name)

    @staticmethod
    def exists(file_name):
        """
        检测给定名称的文件或目录是否存在。

        :param file_name: 待检测的文件/目录路径。
        :return: 存在返回True，否则返回False。
        """
        return os.access(file_name, os.F_OK)

    @staticmethod
    def can_read(file_name):
        """
        尝试打开文件来判断其是否具有读权限。

        :param file_name: 文件路径。
        :return: 具有读权限且能成功打开返回True，否则返回False。
        """
        try:
            with open(file_name):
                pass
        except IOError:
            return False
        return True

    @staticmethod
    def can_write(path):
        """
        检查目标路径是否有写入权限。如果路径不是目录，则向上查找父级直到找到目录为止。

        :param path: 需要检查写权限的目标路径。
        :return: 若拥有写权限返回True，否则返回False。
        """
        while not FileUtils.is_dir(path):
            path = FileUtils.parent(path)

        return os.access(path, os.W_OK)

    @staticmethod
    def read(file_name):
        """
        一次性读取整个文件的所有内容。

        :param file_name: 文件路径。
        :return: 文件全部内容作为字符串返回。
        """
        return open(file_name, "r").read()

    @staticmethod
    def read_dir(directory):
        """
        遍历目录及其子目录中的所有文件，并将其内容存入字典中。

        :param directory: 根目录路径。
        :return: 字典结构：{文件名: 文件内容}。
        """
        data = {}
        for root, _, files in os.walk(directory):
            for file in files:
                data[file] = FileUtils.read(os.path.join(root, file))

        return data

    @staticmethod
    def get_lines(file_name):
        """
        打开文件并按行分割内容，忽略编码错误。

        :param file_name: 文件路径。
        :return: 行内容组成的列表。
        """
        with open(file_name, "r", errors="replace") as fd:
            return fd.read().splitlines()

    @staticmethod
    def is_dir(path):
        """
        判断给定路径是否为目录。

        :param path: 待判断的路径。
        :return: 是目录返回True，否则返回False。
        """
        return os.path.isdir(path)

    @staticmethod
    def is_file(path):
        """
        判断给定路径是否为普通文件。

        :param path: 待判断的路径。
        :return: 是普通文件返回True，否则返回False。
        """
        return os.path.isfile(path)

    @staticmethod
    def parent(path, depth=1):
        """
        获取指定路径的上级目录，支持多层回退。

        :param path: 原始路径。
        :param depth: 向上回退的层级数，默认为1。
        :return: 上级目录路径。
        """
        for _ in range(depth):
            path = os.path.dirname(path)

        return path

    @staticmethod
    def create_dir(directory):
        """
        创建不存在的目录，包括必要的中间目录。

        :param directory: 要创建的目录路径。
        """
        if not FileUtils.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def create_file(file):
        """
        创建一个新的空文件。

        :param file: 要创建的文件路径。
        """
        open(file, "w").close()

    @staticmethod
    def write_lines(file_name, lines, overwrite=False):
        """
        将一组行数据写入到文件中。

        :param file_name: 写入的目标文件路径。
        :param lines: 要写入的数据，可以是字符串或字符串列表。
        :param overwrite: 是否覆盖原文件内容，默认为追加模式。
        """
        if isinstance(lines, list):
            lines = os.linesep.join(lines)
        with open(file_name, "w" if overwrite else "a") as f:
            f.writelines(lines)

