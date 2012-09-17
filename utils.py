import time
from PyQt4.QtCore import Qt, QThread, pyqtSignal, QFileSystemWatcher, QObject, QDir, QDirIterator, QFileInfo

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

class DirFileInfoList(QObject):
    def __init__(self, directory, parent=None):
        super(DirFileInfoList, self).__init__(parent)
        self.iterator = QDirIterator(directory,
                                     QDir.AllEntries | QDir.NoDotAndDotDot,
                                     QDirIterator.Subdirectories)
        self.__iterate_files()

    def __iterate_files(self):
        self.file_infos = []
        while self.iterator.hasNext():
            info = QFileInfo(self.iterator.next())
            self.file_infos.append(info)


class FSMonitor(QObject):
    def __init__(self, parent=None):
        super(FSMonitor, self).__init__(parent)
        self.__init_watcher()

    def watch(self, directory):
        if self.__dict__.get('directory', False):
            self.watcher.removePath(self.directory)
        self.directory = directory
        self.watcher.addPath(directory)

    def __init_watcher(self):
        self.watcher = watcher = QFileSystemWatcher()
        watcher.directoryChanged.connect(self.__file_changed)

    def __file_changed(self):
        print('some files changed yada lalala')

    def __directory_changed(self):
        print('some directory changed yada lalala')
