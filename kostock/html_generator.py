import os
from flask import render_template
from abc import *


class HTMLGenerator(metaclass=ABCMeta):

    BASE_HTML = os.path.dirname(os.path.realpath(__file__)) + "\\templates\\.html"
    NAME = ".html"

    def __init__(self, save_path):
        self._save_path = save_path

    def get_save_path(self):
        return self._save_path

    @abstractmethod
    def create(self, *args, **kwargs):
        pass


class TestResultHTMLGenerator(HTMLGenerator):

    BASE_HTML = os.path.dirname(os.path.realpath(__file__)) + '\\templates\\result.html'
    NAME = "test_result.html"

    def create(self, title, profit_path, chart_path, result):
        _rendered = render_template(self.__class__.BASE_HTML,
                                    title=title, profit_path=profit_path, chart_path=chart_path, result=result)

        _path_name = self._save_path + '\\' + self.__class__.NAME
        with open(_path_name, "w") as html:
            html.write(_rendered)

