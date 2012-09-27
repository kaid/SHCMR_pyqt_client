# encoding=utf-8

import sys
import time
from PyQt4.QtCore import (Qt,
                          QThread,
                          pyqtSignal,
                          QFileSystemWatcher,
                          QObject,
                          QDir,
                          QDirIterator,
                          QFileInfo,
                          QVariant)

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

    def get_meta_dict(self):
        meta_dict = {}
        for info in self.file_infos:
            meta_dict[info.absoluteFilePath()] = modified_at_of(info)
        return meta_dict

class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])

