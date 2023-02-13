-- NOTE: In order to allow cascading deletes by foreign keys, this must be run per db connection:
-- "PRAGMA foreign_keys = ON"

CREATE TABLE IF NOT EXISTS `guilds` (
  `id` int NOT NULL PRIMARY KEY, -- discord guild_id
  `channel_id` int NOT NULL, -- discord channel_id
  `autodraw_weekday` int NOT NULL,
  `autodraw_hour` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL PRIMARY KEY, -- discord user_id
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `enrollments` ( -- Many-to-many junction table for guilds & users
  `guild_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT guilds_users UNIQUE(guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS `entries` (
  `name` varchar(50) NOT NULL,
  `first` int NOT NULL DEFAULT 0, -- boolean, if first choice
  `guild_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `entry_hist` (
  `name` varchar(50) NOT NULL,
  `won` int NOT NULL DEFAULT 0, -- boolean, if entry won
  `guild_id` int NOT NULL,
  `user_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, -- the day the entry was drawn
  FOREIGN KEY(guild_id) REFERENCES guilds(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
