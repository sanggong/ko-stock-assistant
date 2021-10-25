"""
configurer.py

configuration class (Singleton)
"""

import json

from kostock._pattern import Singleton


class Configurer(metaclass=Singleton):
    DB = {}
    KIWOOM = []

    UPDATE_HOLIDAY_KEY = ""

    UPDATE_START_DATE = None
    UPDATE_END_DATE = None

    UPDATE_MANUAL_CHART_TRANSFER = False
    UPDATE_NUMBER_OF_PROCESS = 1

    UPDATE_PICKLE_PATH = 'logs\\update_pid'
    UPDATE_LOG_PATH = 'logs\\update'

    UPDATE_BLACK_LIST = []

    def __init__(self, config_path=""):
        set_list = {"DB": self._set_db, "KIWOOM": self._set_kiwoom,
                    "UPDATE_HOLIDAY_KEY": self._set_update_holiday_key,
                    "UPDATE_START_DATE": self._set_update_start_date, "UPDATE_END_DATE": self._set_update_end_date,
                    "UPDATE_MANUAL_CHART_TRANSFER": self._set_update_manual_chart_transfer,
                    "UPDATE_NUMBER_OF_PROCESS": self._set_update_number_of_process,
                    "UPDATE_PICKLE_PATH": self._set_update_pickle_path, "UPDATE_LOG_PATH": self._set_update_log_path,
                    "UPDATE_BLACK_LIST": self._set_update_black_list}
        if config_path:
            with open(config_path) as f:
               config = json.load(f)

            for attr, value in config.items():
                set_list[attr](value)

    def set_config(self, config):
        self.__init__(config)

    @classmethod
    def _set_db(cls, db):
        cls.DB = db

    @classmethod
    def _set_kiwoom(cls, kiwoom):
        cls.KIWOOM = kiwoom

    @classmethod
    def _set_update_holiday_key(cls, key):
        cls.UPDATE_HOLIDAY_KEY = key

    @classmethod
    def _set_update_start_date(cls, date):
        cls.UPDATE_START_DATE = date

    @classmethod
    def _set_update_end_date(cls, date):
        cls.UPDATE_END_DATE = date

    @classmethod
    def _set_update_manual_chart_transfer(cls, bool):
        cls.UPDATE_MANUAL_CHART_TRANSFER = bool

    @classmethod
    def _set_update_number_of_process(cls, num_proc):
        cls.UPDATE_NUMBER_OF_PROCESS = num_proc

    @classmethod
    def _set_update_pickle_path(cls, path):
        cls.UPDATE_PICKLE_PATH = path

    @classmethod
    def _set_update_log_path(cls, path):
        cls.UPDATE_LOG_PATH = path

    @classmethod
    def _set_update_black_list(cls, list_):
        cls.UPDATE_BLACK_LIST = list_