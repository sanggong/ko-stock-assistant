import logging
import logging.handlers
from threading import Thread
import platform


class Log:
    def __init__(self):
        self.th = None

    @staticmethod
    def get_logger(name):
        return logging.getLogger(name)

    def listener_start(self, file_path, name, queue):
        """
        Listener perform getting log data in Queue as consumer
        and writing log in way method self.config_log.
        Listener operate in new thread.
        :param file_path:[str] same file_path with method self.config_log
        :param name:[str] name assigned getLogger
        :param queue:[multiprocessing.Queue] Queue used in QueueHandler
        """
        self.th = Thread(target=self._proc_log_queue, args=(file_path, name, queue))
        self.th.start()

    def listener_end(self, queue):
        """
        Multiprocess log listener end method.
        :param queue:[multiprocessing.Queue] same queue with listener_start input queue.
        """
        queue.put(None)
        self.th.join()
        print('log listener end...')

    def _proc_log_queue(self, file_path, name, queue):
        """
        This function must be used in another thread
        :param queue: multiprocessing logging queue
        """
        self.config_log(file_path, name)
        logger = self.get_logger(name)
        while True:
            try:
                record = queue.get()
                if record is None:
                    break
                logger.handle(record)
            except Exception:
                import sys
                print('log problem', file=sys.stderr)

    @staticmethod
    def config_queue_log(queue, name):
        """
        You want to use logging in multiprocessing, call this method in multiprocess and
        call self.listener_start, self.listener_end in main process.
        :param queue:[multiprocessing.Queue] Queue used in QueueHandler as producer.
        :param name:[str] name assigned getLogger.
        """
        qh = logging.handlers.QueueHandler(queue)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(qh)
        return logger

    @staticmethod
    def config_log(file_path, name):
        # err file handler
        fh_err = logging.handlers.TimedRotatingFileHandler(file_path + '_error.log', when='midnight',
                                                           encoding='utf-8', backupCount=60)
        fh_err.setLevel(logging.WARNING)
        # file handler
        fh_dbg = logging.handlers.TimedRotatingFileHandler(file_path + '_debug.log', when='midnight',
                                                           encoding='utf-8', backupCount=60)
        fh_dbg.setLevel(logging.DEBUG)
        # console handler
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        # logging format setting
        ff = logging.Formatter('''[%(asctime)s] %(levelname)s : %(message)s''')
        sf = logging.Formatter('''[%(levelname)s] %(message)s''')
        fh_err.setFormatter(ff)
        fh_dbg.setFormatter(ff)
        sh.setFormatter(sf)
        if platform.system() == 'Windows':
            import msvcrt
            import win32api
            import win32con
            win32api.SetHandleInformation(msvcrt.get_osfhandle(fh_dbg.stream.fileno()),
                                          win32con.HANDLE_FLAG_INHERIT, 0)
            win32api.SetHandleInformation(msvcrt.get_osfhandle(fh_err.stream.fileno()),
                                          win32con.HANDLE_FLAG_INHERIT, 0)

        # create logger, assign handler
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(fh_err)
        logger.addHandler(fh_dbg)
        logger.addHandler(sh)
        return logger
