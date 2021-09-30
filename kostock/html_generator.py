import os
from jinja2 import Environment, PackageLoader

from abc import *



class HtmlGenerator(metaclass=ABCMeta):
    PACKAGE_PATH = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    TEMPLATE_PATH = "templates"
    BASE_NAME = ".html"
    OUTPUT_NAME = ".html"

    def __init__(self, save_path):
        self._save_path = save_path

    def get_save_path(self):
        return self._save_path

    def get_path_name(self):
        return self._save_path + '\\' + self.__class__.OUTPUT_NAME

    @abstractmethod
    def create(self, *args, **kwargs):
        pass


class TestResultHtmlGenerator(HtmlGenerator):
    BASE_NAME = "result.html"
    OUTPUT_NAME = "test_result.html"

    def create(self, title, profit_path, chart_path, result):
        """
        Create Test result, Profit graph, Input chart data graph into HTML file.
        :param title: [str] Title in HTML
        :param profit_path: [str] profit graph path
        :param chart_path: [list<str>] chart graph paths
        :param result: [pandas.DataFrame] BackTest result
        """
        _env = Environment(loader=PackageLoader(self.__class__.PACKAGE_PATH, self.__class__.TEMPLATE_PATH))
        _template = _env.get_template(self.__class__.BASE_NAME)
        _rendered = _template.render(title=title, profit_path=profit_path, chart_path=chart_path, result=result)
        path_name = self._save_path + '\\' + self.__class__.OUTPUT_NAME

        with open(path_name, "w") as html:
            html.write(_rendered)
        return path_name
