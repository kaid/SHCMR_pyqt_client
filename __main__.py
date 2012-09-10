#!/usr/bin/env python
import sys
from PyQt4.QtGui import QApplication, QIcon
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from models import FileTransferSortProxyModel, FileTransferTableModel
from views import MyWindow, FileTransferStatusBar, TrayTool

if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("database.db")
    db.open()
    q = QSqlQuery()
    q.exec_('CREATE TABLE IF NOT EXISTS file_list(\
               id     INTEGER PRIMARY KEY AUTOINCREMENT,\
               status BOOL DEFAULT 0 CHECK (status = 0 OR status = 1),\
               name   VARCHAR(255) NOT NULL,\
               size   INT CHECK (size > 0)\
             )')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(1, 1, \'东方风神录.rar\', 348127232)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(2, 1, \'旅途之中.mp3\', 4194304)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(3, 1, \'zurich.mp4\', 9101244)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(4, 1, \'armageddon.jpg\', 401244)')
    q.exec_('INSERT INTO file_list (id, status, name, size) VALUES(5, 0, \'larmageddon.jpg\', 401240)')
    q.exec_('commit')

    window = MyWindow()
    window.resize(640, 240)
    window.show()
    tray = TrayTool(QIcon('s.png'), app)
    tray.show()
    app.exec_()
    tray = None
    sys.exit(0)

