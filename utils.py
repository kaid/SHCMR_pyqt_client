# encoding=utf-8

import sys
import time
import datetime
from PyQt4.QtCore import (Qt,
                          QThread,
                          pyqtSignal,
                          QFileSystemWatcher,
                          QObject,
                          QDir,
                          QDirIterator,
                          QFileInfo,
                          QEventLoop,
                          QVariant)

from PyQt4.QtGui import QApplication

try:
    from PyQt4.QtCore import QString
except ImportError:
    print('Welcome to world of py3k!')

def convert_byte_size(byte_size):
    for unit in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f%s" % (byte_size, unit)
        byte_size /= 1024.0

def format_time(seconds):
    return time.strftime('%H小时%M分%S秒', time.gmtime(seconds))

def format_date(data):
    if data < 0:
        return
    return datetime.datetime.fromtimestamp(long(data)).isoformat(' ')

def convert_time(qdatetime):
    qdatetime.setTimeSpec(Qt.LocalTime)
    return qdatetime.toTime_t()

def modified_at_of(info):
    if info.isDir():
        return -1
    return convert_time(info.lastModified() or info.created())

def from_qvariant(data):
    if data.__class__ == QVariant:
        pydata = data.toPyObject()
        if pydata.__class__ == QString:
            return str(pydata)
        return pydata
    return data

def unicode_str(str):
    try:
        return unicode(str)
    except NameError:
        return str

def set_unicode():
    try:
        reload(sys)
        sys.setdefaultencoding('utf-8')
    except NameError:
        print('Glad to be back to py3k, python 2.x sucks at unicode, oww!')

def process_event():
    QApplication.processEvents(QEventLoop.AllEvents)

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

class DirFileInfoList(QObject):
    def __init__(self, directory, parent=None):
        super(self.__class__, self).__init__(parent)
        self.iterator = QDirIterator(from_qvariant(directory),
                                     QDir.AllEntries | QDir.NoDotAndDotDot,
                                     QDirIterator.Subdirectories)
        self.__iterate_files()

    def __iterate_files(self):
        self.file_infos = []
        while self.iterator.hasNext():
            info = QFileInfo(self.iterator.next())
            self.file_infos.append(info)
