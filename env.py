from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from PyQt4.QtGui import QApplication
from utils import *

App = QApplication(sys.argv)

class __DataStoreObject(QObject):
    batch_done = pyqtSignal()
    inserting  = pyqtSignal()
    inserted   = pyqtSignal(object)
    updated    = pyqtSignal(list)
    deleted    = pyqtSignal(list)
    moved      = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.__init_database()
        self.query = QSqlQuery()
        self.__setup_database()

    def __init_database(self):
        self.database = QSqlDatabase.addDatabase('QSQLITE')
        self.database.setDatabaseName('database.db')
        self.database.open()

    def __setup_database(self):
        with open('database.sql', 'r') as file:
            for string in file.read().split(';')[0:-1]:
                self.query.exec_(string)

    def get(self, path):
        self.query.exec_('SELECT * FROM file_list WHERE path="%s"' % path)

        while self.query.next():
            return [from_qvariant(self.query.value(i)) for i in range(8)]

        return None

    def update_record(self, info):
        process_event()
        path = from_qvariant(info.absoluteFilePath())
        string = 'UPDATE file_list SET modified_at=%d, size=%d, removed="%d" WHERE path="%s"' % (
            modified_at_of(info),
            info.size(),
            0,
            path
        )

        self.query.exec_(string)
        data = self.get(path)
        if data: self.updated.emit(data)

    def move_record(self, src_path, dest_path):
        process_event()
        dest_info = QFileInfo(dest_path)
        string = 'UPDATE file_list SET name="%s", path="%s", modified_at="%d" WHERE path="%s"' % (
            from_qvariant(dest_info.fileName()),
            dest_path,
            modified_at_of(dest_info),
            src_path
        )

        self.query.exec_(string)
        data = self.get(dest_path)
        if data: self.moved.emit(src_path, data)

    def insert_record(self, info, batch=False):
        process_event()
        path = info.absoluteFilePath()
        if self.exists(path):
            return self.update_record(info)

        string = 'INSERT INTO file_list (name, size, path, is_dir, modified_at)\
                  VALUES (:name, :size, :path, :is_dir, :modified_at)'

        self.query.prepare(string)
        self.query.bindValue(':name', info.fileName())
        self.query.bindValue(':size', info.size())
        self.query.bindValue(':path', path)
        self.query.bindValue(':is_dir', 1 if info.isDir() else 0)
        self.query.bindValue(':modified_at', modified_at_of(info))
        if not batch: self.inserting.emit()
        self.query.exec_()
        if not batch: self.inserted.emit(self.get(path))

    def delete_record(self, path):
        process_event()
        string = 'UPDATE file_list SET modified_at=NULL, removed=1 WHERE path="%s"' % path

        self.query.exec_(string)
        self.deleted.emit(self.get(path))

    def batch_insert(self, infos):
        for info in infos:
            process_event()
            self.insert_record(info, batch=True)
        self.batch_done.emit()

    def exists(self, path):
        return bool(self.get(path))

DataStore = __DataStoreObject()

class __ConfigurationObject(QObject):
    have_updated = pyqtSignal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=None)
        self.query = QSqlQuery()

    def set_directory(self, directory):
        self.query.prepare('UPDATE configuration SET directory=:directory WHERE id=1')
        self.query.bindValue(':directory', directory)
        self.query.exec_()
        self.have_updated.emit()

    def get_directory(self):
        self.query.exec_('SELECT directory FROM configuration WHERE id=1')
        while self.query.next():
            return from_qvariant(self.query.value(0))

Configuration = __ConfigurationObject()
