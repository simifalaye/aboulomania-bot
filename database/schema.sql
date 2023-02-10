CREATE TABLE IF NOT EXISTS `server_configs` (
  `server_id` int NOT NULL PRIMARY KEY,
  `channel_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `draw_entries` (
  `server_id` int NOT NULL,
  `user_id` int NOT NULL,
  `first_choice` varchar(50) NOT NULL,
  `second_choice` varchar(50) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT servers_users UNIQUE(server_id, user_id)
);

CREATE TABLE IF NOT EXISTS `draw_stats` (
  `server_id` int NOT NULL,
  `user_id` int NOT NULL,
  `num_wins` int NOT NULL,
  `last_win_date` timestamp,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT servers_users UNIQUE(server_id, user_id)
);
