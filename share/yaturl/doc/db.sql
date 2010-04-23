--
-- SQL for setting database for yaturl
--

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `yaturl1`
--

-- --------------------------------------------------------

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
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=381 ;
