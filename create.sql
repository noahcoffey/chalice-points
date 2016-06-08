CREATE TABLE `event` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `source` int(10) unsigned NOT NULL,
  `target` int(10) unsigned NOT NULL,
  `type` VARCHAR(255) NOT NULL,
  `amount` tinyint(2) NOT NULL,
  `message` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `source` (`source`),
  KEY `target` (`target`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `user` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `api_key` varchar(255) DEFAULT NULL,
  `gravatar` varchar(255) DEFAULT NULL,
  `max_points` tinyint(1) DEFAULT '5',
  `disabled` tinyint(1) DEFAULT '0',
  `elder` tinyint(1) DEFAULT '0',
  `url` varchar(255) DEFAULT NULL,
  `settings` longtext DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `email` (`email`),
  KEY `api_key` (`api_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
