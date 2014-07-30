drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  ingredients text not null,
  steps text not null
  tags text,
  url text
);

drop table if exists users;
create table entries (
  id integer primary key autoincrement,
  username text not null,
  password text not null,
);