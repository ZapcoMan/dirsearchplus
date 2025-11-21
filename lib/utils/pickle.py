try:
    import cPickle as _pickle
except ModuleNotFoundError:
    import pickle as _pickle

from lib.core.exceptions import UnpicklingError

# 定义允许反序列化的类列表，用于限制pickle反序列化时可加载的类，
# 防止任意代码执行等安全问题。
ALLOWED_PICKLE_CLASSES = (
    "collections.OrderedDict",
    "http.cookiejar.DefaultCookiePolicy",
    "requests.adapters.HTTPAdapter",
    "requests.cookies.RequestsCookieJar",
    "requests.sessions.Session",
    "requests.structures.CaseInsensitiveDict",
    "lib.connection.requester.Requester",
    "lib.connection.response.Response",
    "lib.connection.requester.Session",
    "lib.core.dictionary.Dictionary",
    "lib.core.report_manager.Report",
    "lib.core.report_manager.ReportManager",
    "lib.core.report_manager.Result",
    "lib.core.structures.AttributeDict",
    "lib.core.structures.CaseInsensitiveDict",
    "lib.output.verbose.Output",
    "lib.reports.csv_report.CSVReport",
    "lib.reports.html_report.HTMLReport",
    "lib.reports.json_report.JSONReport",
    "lib.reports.markdown_report.MarkdownReport",
    "lib.reports.plain_text_report.PlainTextReport",
    "lib.reports.simple_report.SimpleReport",
    "lib.reports.xml_report.XMLReport",
    "lib.reports.sqlite_report.SQLiteReport",
    "urllib3.util.retry.Retry",
)


# 参考文档：https://docs.python.org/3.4/library/pickle.html#restricting-globals
# 自定义受限的Unpickler类，通过重写find_class方法来控制可以被反序列化的类，
# 仅允许在ALLOWED_PICKLE_CLASSES中定义的类进行反序列化。
class RestrictedUnpickler(_pickle.Unpickler):
    """
    一个受限制的pickle反序列化器，防止不安全的类被加载。

    :param file: 要从中读取pickle数据的文件对象或类似文件的对象。
    """

    def find_class(self, module, name):
        """
        控制哪些类可以从pickle流中恢复。

        :param module: 类所在的模块名。
        :param name: 类名。
        :return: 对应的类对象（如果允许）。
        :raises UnpicklingError: 如果尝试加载未授权的类。
        """
        # 检查请求的类是否在允许列表中
        if f"{module}.{name}" in ALLOWED_PICKLE_CLASSES:
            return super().find_class(module, name)

        # 若不在白名单内则抛出异常阻止反序列化
        raise UnpicklingError()


def unpickle(*args, **kwargs):
    """
    使用受限的Unpickler从给定的数据源中安全地反序列化对象。

    :param args: 传递给RestrictedUnpickler构造函数的位置参数。
    :param kwargs: 传递给RestrictedUnpickler构造函数的关键字参数。
    :return: 反序列化后的Python对象。
    """
    return RestrictedUnpickler(*args, **kwargs).load()


def pickle(obj, *args, **kwargs):
    """
    将Python对象序列化为pickle格式并写入到指定的目标中。

    :param obj: 要序列化的Python对象。
    :param args: 传递给_pickle.Pickler构造函数的位置参数。
    :param kwargs: 传递给_pickle.Pickler构造函数的关键字参数。
    :return: None（结果将被写入到提供的目标中）。
    """
    return _pickle.Pickler(*args, **kwargs).dump(obj)

