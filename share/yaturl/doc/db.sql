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
  PRIMARY KEY  (`link_id`),
  UNIQUE KEY `link_hash` (`link_hash`),
  UNIQUE KEY `link_shorthash` (`link_shorthash`)
) ENGINE=INNODB  DEFAULT CHARSET=utf8 AUTO_INCREMENT=381 ;

ALTER TABLE `access_log`
  ADD CONSTRAINT `access_log_ibfk_1` FOREIGN KEY (`link_id`) REFERENCES `link` (`link_id`) ON DELETE CASCADE;
