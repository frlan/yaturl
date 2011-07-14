--
-- SQL for setting database for yaturl
--

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Table structure for table `access_log`
--

CREATE TABLE IF NOT EXISTS `access_log` (
  `access_log_id` int(10) unsigned NOT NULL auto_increment,
  `link_id` bigint(20) unsigned NOT NULL,
  `access_time` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `deleted` tinyint(1) NOT NULL DEFAULT '0',
  `del_time` timestamp NULL DEFAULT NULL,
  PRIMARY KEY  (`access_log_id`),
  KEY `link_id` (`link_id`),
  KEY `access_time` (`access_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

--
-- Table structure for table `link`
--

CREATE TABLE IF NOT EXISTS `link` (
  `link_id` bigint(20) unsigned NOT NULL auto_increment,
  `link_shorthash` varchar(25) NOT NULL,
  `link_hash` varchar(100) NOT NULL,
  `link_link` varchar(4096) NOT NULL,
  `link_comment` varchar(255) default NULL,
  `entry_date` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`link_id`),
  UNIQUE KEY `link_hash` (`link_hash`),
  UNIQUE KEY `link_shorthash` (`link_shorthash`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1;


CREATE TABLE IF NOT EXISTS `block` (
  `block_id` bigint(20) unsigned NOT NULL auto_increment,
  `link_id` bigint(20) unsigned NOT NULL,
  `entry_date` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `comment` text,
  PRIMARY KEY  (`block_id`),
  UNIQUE KEY `link_id` (`link_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

ALTER TABLE `access_log`
  ADD CONSTRAINT `access_log_ibfk_1` FOREIGN KEY (`link_id`) REFERENCES `link` (`link_id`) ON DELETE CASCADE;

ALTER TABLE `block`
  ADD CONSTRAINT `block_ibfk_1` FOREIGN KEY (`link_id`) REFERENCES `link` (`link_id`) ON DELETE CASCADE ON UPDATE NO ACTION;
