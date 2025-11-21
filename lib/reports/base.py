from lib.core.decorators import locked
from lib.core.settings import IS_WINDOWS


class FileBaseReport:
    """
    文件基础报告类，用于生成和保存报告到文件

    Args:
        output_file (str): 输出文件路径
    """

    def __init__(self, output_file):
        # 如果是Windows系统，规范化文件路径
        if IS_WINDOWS:
            from os.path import normpath

            output_file = normpath(output_file)

        self.output_file = output_file

    @locked
    def save(self, entries):
        """
        保存条目到输出文件

        Args:
            entries (list): 要保存的条目列表

        Returns:
            None
        """
        # 如果没有条目则直接返回
        if not entries:
            return

        # 打开文件并写入生成的内容
        with open(self.output_file, "w") as fd:
            fd.writelines(self.generate(entries))
            fd.flush()

    def generate(self, entries):
        """
        生成报告内容的抽象方法，需要子类实现

        Args:
            entries (list): 要生成报告的条目列表

        Returns:
            str: 生成的报告内容

        Raises:
            NotImplementedError: 当子类没有实现此方法时抛出
        """
        raise NotImplementedError

