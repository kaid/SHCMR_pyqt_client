from PyQt4.QtCore import QObject, pyqtSignal, QEventLoop
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from PyQt4.QtGui import QApplication
from utils import *

_sql_file          = open('database.sql', 'r')
_setup_sql_strings = _sql_file.read().split(';')[0:-1]
_sql_file.close()

class __DataStoreObject(QObject):
    committed = pyqtSignal()

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
        for string in _setup_sql_strings:
            self.query.exec_(string)

    def get(self, path):
        self.query.exec_('SELECT * FROM file_list WHERE path="%s"' % path)

        while self.query.next():
            return self.query

        return None

    def update_record(self, info):
        QApplication.processEvents(QEventLoop.AllEvents)
        string = 'UPDATE file_list SET modified_at=%d, size=%d WHERE path="%s"' % (
            modified_at_of(info),
            info.size(),
            from_qvariant(info.absoluteFilePath()),
        )

        self.query.exec_(string)
        self.committed.emit()

    def move_record(self, src_path, dest_path):
        QApplication.processEvents(QEventLoop.AllEvents)
        dest_info = QFileInfo(dest_path)
        string = 'UPDATE file_list SET name="%s", path="%s", modified_at="%d" WHERE path="%s"' % (
            from_qvariant(dest_info.fileName()),
            dest_path,
            modified_at_of(dest_info),
            src_path
        )

        print(modified_at_of(QFileInfo(dest_path)), string)
        print(self.get(src_path), self.query.lastError().text())
        self.query.exec_(string)
        print(self.get(dest_path), self.query.lastError().text())
        self.committed.emit()

    def insert_record(self, info):
        QApplication.processEvents(QEventLoop.AllEvents)
        if self.get(info.absoluteFilePath()):
            return self.update_record(info)

        string = 'INSERT INTO file_list (name, size, path, is_dir, modified_at)\
                  VALUES (:name, :size, :path, :is_dir, :modified_at)'

        self.query.prepare(string)
        self.query.bindValue(':name', info.fileName())
        self.query.bindValue(':size', info.size())
        self.query.bindValue(':path', info.absoluteFilePath())
        self.query.bindValue(':is_dir', 1 if info.isDir() else 0)
        self.query.bindValue(':modified_at', modified_at_of(info))
        self.query.exec_()
        self.committed.emit()

    def delete_record(self, path):
        print(path.__class__)
        string = 'UPDATE file_list SET modified_at=NULL WHERE path="%s"' % path

        self.query.exec_(string)
        self.committed.emit()

    def batch_insert(self, infos):
        for info in infos:
            self.insert_record(info)

    def batch_update(self, infos):
        for info in infos:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.update_record(info)

    def batch_delete(self, paths):
        for path in paths:
            QApplication.processEvents(QEventLoop.AllEvents)
            self.delete_record(path)

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
            return self.query.value(0)

Configuration = __ConfigurationObject()
