drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  ingredients text not null,
  steps text not null
  tags text,
  url text
);