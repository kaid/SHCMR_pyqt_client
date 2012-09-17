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
        self.watching_list = []

    def watch(self, directory):
        if self.__dict__.get('directory', False):
            self.watcher.removePaths(self.watching_list)
        self.directory = directory
        self.watching_list = list(map(lambda info: info.absoluteFilePath(),
                                      DirFileInfoList(directory).file_infos))
        self.watcher.addPaths(self.watching_list)

    def __init_watcher(self):
        self.watcher = watcher = QFileSystemWatcher()
        watcher.directoryChanged.connect(self.__directory_changed)
        watcher.fileChanged.connect(self.__file_changed)
        watcher.directoryChanged.connect(self.__update_watching_list)
        watcher.fileChanged.connect(self.__update_watching_list)

    def __update_watching_list(self, path):
        1

    def __file_changed(self, path):
        print('some files has been changed %s' % path)

    def __directory_changed(self, path):
        print('some directories have been changed %s' % path)
