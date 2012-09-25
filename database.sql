CREATE TABLE IF NOT EXISTS file_list (
       id          INTEGER PRIMARY KEY AUTOINCREMENT,
       status      BOOLEAN DEFAULT 1 CHECK (status = 0 OR status = 1),
       name        VARCHAR(255) NOT NULL,
       size        INTEGER DEFAULT 0 CHECK (size >= 0),
       path        VARCHAR(255) UNIQUE,
       is_dir      BOOLEAN DEFAULT 0 CHECK (is_dir = 0 OR is_dir = 1),
       modified_at DATETIME
);

CREATE TABLE IF NOT EXISTS configuration (
       id        INTEGER PRIMARY KEY AUTOINCREMENT,
       directory VARCHAR(255)
);

INSERT INTO configuration (id) VALUES(1);
