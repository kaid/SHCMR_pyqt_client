#!/usr/bin/env python
import sys
from PyQt4.QtGui import QApplication, QIcon
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from models import Configuration
from views import MyWindow, FileTransferStatusBar, TrayIcon

def database_setup():
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('database.db')
    db.open()

def sql_setup():
    query = QSqlQuery()
    query.exec_('CREATE TABLE IF NOT EXISTS file_list (' +
                  'id          INTEGER PRIMARY KEY AUTOINCREMENT,' +
                  'status      BOOL DEFAULT 1 CHECK (status = 0 OR status = 1),' +
                  'name        VARCHAR(255) NOT NULL,' +
                  'size        INTEGER DEFAULT 0 CHECK (size >= 0),' +
                  'path        VARCHAR(255) UNIQUE,' +
                  'is_dir      BOOL DEFAULT 0 CHECK (is_dir = 0 OR is_dir = 1),' +
                  'modified_at DATETIME' +
                ')')

    query.exec_('CREATE TABLE IF NOT EXISTS configuration (' +
                  'id        INTEGER PRIMARY KEY AUTOINCREMENT,' +
                  'directory VARCHAR(255)' +
                ')')
    query.exec_('INSERT INTO configuration (id) VALUES(1)')
    query.exec_('commit')


def main():
    app = QApplication(sys.argv)
    database_setup()
    sql_setup()
    config = Configuration()
    window = MyWindow(config)
    window.resize(800, 400)
    window.show()
    tray = TrayIcon(app, config, parent=app)
    tray.show()
    app.exec_()
    tray = None
    sys.exit()

if __name__ == '__main__':
    main()


