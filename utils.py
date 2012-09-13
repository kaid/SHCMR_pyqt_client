import time
from PyQt4.QtCore import Qt, QThread, pyqtSignal

def convert_byte_size(byte_size):
    for unit in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f%s" % (byte_size, unit)
        byte_size /= 1024.0

def format_time(seconds):
    return time.strftime('%H小时%M分%S秒', time.gmtime(seconds))

def convert_time(qdatetime):
    qdatetime.setTimeSpec(Qt.LocalTime)
    return qdatetime.toTime_t()

class Worker(QThread):
    done = pyqtSignal()

    def begin(self, job, *args):
        self.__job = job
        self.__args = args
        self.start()

    def __del__(self):
        self.wait()

    def run(self):
        self.__job(*self.__args)
        self.done.emit()
