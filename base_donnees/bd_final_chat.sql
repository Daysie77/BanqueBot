-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : mer. 16 oct. 2024 à 09:54
-- Version du serveur : 8.2.0
-- Version de PHP : 8.2.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `bd_final_chat`
--

-- --------------------------------------------------------

--
-- Structure de la table `conversations`
--

DROP TABLE IF EXISTS `conversations`;
CREATE TABLE IF NOT EXISTS `conversations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `conversations`
--

INSERT INTO `conversations` (`id`, `user_id`, `title`, `created_at`) VALUES
(1, 1, 'Soutenance', '2024-07-19 11:51:42');

-- --------------------------------------------------------

--
-- Structure de la table `messages`
--

DROP TABLE IF EXISTS `messages`;
CREATE TABLE IF NOT EXISTS `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `conversation_id` int NOT NULL,
  `content` text NOT NULL,
  `sender` enum('user','bot') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `conversation_id` (`conversation_id`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `messages`
--

INSERT INTO `messages` (`id`, `conversation_id`, `content`, `sender`, `created_at`) VALUES
(1, 1, 'Bonjour', 'user', '2024-07-19 11:51:47'),
(2, 1, 'Bonjour! Comment puis-je vous aider aujourd\'hui ?', 'bot', '2024-07-19 11:51:53'),
(3, 1, 'Parlez maintenant, je veux Fanny sous tes noms sur des machines learning.', 'user', '2024-07-19 11:52:28'),
(4, 1, 'Bonjour ! Tu veux parler de Fanny et du machine learning ? Peux-tu préciser ce que tu souhaites savoir ou discuter ? Est-ce que tu cherches des informations spécifiques sur Fanny et son lien avec le machine learning ou quelque chose d\'autre ?', 'bot', '2024-07-19 11:52:30'),
(5, 1, 'Parlez maintenant, je veux Fanny sous tes noms sur des machines learning.Bonjour.Tu veux parler de famille et du machine learning, peux-tu préciser ce que tu sous ?', 'user', '2024-07-19 11:52:39'),
(6, 1, 'Bonjour! Il semble que tu souhaites parler de la famille et du machine learning, mais je ne suis pas tout à fait sûr de ce que tu veux dire par \"Fanny sous tes noms sur des machines learning.\" Peux-tu donner plus de détails ou clarifier ta demande? Je suis là pour t\'aider!', 'bot', '2024-07-19 11:52:42');

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(150) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `profileImage` varchar(200) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`id`, `nom`, `username`, `email`, `password`, `profileImage`, `created_at`) VALUES
(1, 'GNIMI', 'desie', 'gnimi2julienne@gmail.com', '$2b$12$x5YCdsnG2JZBD4u110i1N.j06L595ScNJqgIG.O6mwOac1Sz.pTL2', 'uploads/images_profil_parent/bot_avatar.jpg', '2024-07-19 11:50:32');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
