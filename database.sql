 -- SQL Queries --

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    class TEXT NOT NULL,
    period TEXT NOT NULL,
    teacher TEXT NOT NULL,
    location TEXT NOT NULL,
    email TEXT
);

CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    class TEXT NOT NULL,
    points_earned NUMERIC NOT NULL,
    points_possible NUMERIC NOT NULL,
    class_id INTEGER NOT NULL
);

CREATE TABLE homework (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    class TEXT NOT NULL,
    class_id INTEGER NOT NULL,
    due_date DATETIME,
    note TEXT
);