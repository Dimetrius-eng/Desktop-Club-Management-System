-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Хост: 127.0.0.1
-- Час створення: Квт 24 2026 р., 11:37
-- Версія сервера: 10.4.32-MariaDB
-- Версія PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База даних: `sports_club`
--

-- --------------------------------------------------------

--
-- Структура таблиці `attendance`
--

CREATE TABLE `attendance` (
  `id_attendance` int(11) NOT NULL,
  `id_schedule` int(11) NOT NULL,
  `id_client` int(11) NOT NULL,
  `presence_status` varchar(50) DEFAULT 'Записаний',
  `id_sale` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `attendance`
--

INSERT INTO `attendance` (`id_attendance`, `id_schedule`, `id_client`, `presence_status`, `id_sale`) VALUES
(1, 2, 1, 'Присутній (вручну)', 1),
(2, 4, 1, 'Записаний', 2),
(3, 7, 3, 'Присутній', 3),
(4, 2, 2, 'Присутній (вручну)', 4),
(5, 3, 2, 'Присутній', 4),
(7, 1, 4, 'Присутній (вручну)', 6),
(9, 2, 5, 'Присутній (вручну)', 8),
(10, 8, 5, 'Записаний', 8),
(12, 3, 5, 'Присутній (вручну)', 8),
(13, 5, 5, 'Записаний', 8),
(14, 5, 6, 'Записаний', 9),
(15, 8, 6, 'Записаний', 9);

-- --------------------------------------------------------

--
-- Структура таблиці `clients`
--

CREATE TABLE `clients` (
  `id_client` int(11) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `birth_date` date NOT NULL,
  `is_vip` tinyint(1) DEFAULT 0,
  `id_user` int(11) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `freeze_until` date DEFAULT NULL,
  `group_blocked_until` datetime DEFAULT NULL,
  `last_freeze_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `clients`
--

INSERT INTO `clients` (`id_client`, `full_name`, `phone`, `birth_date`, `is_vip`, `id_user`, `is_active`, `freeze_until`, `group_blocked_until`, `last_freeze_date`) VALUES
(1, 'Ткаченко Артем Сергійович', '+380978907652', '2000-01-01', 1, 6, 1, NULL, NULL, NULL),
(2, 'Шевченко Максим Юрійович', '+380675567890', '2013-02-02', 0, 7, 1, NULL, NULL, NULL),
(3, 'Мороз Наталія Григорівна', '+380967892211', '2019-03-03', 0, 8, 1, NULL, '2026-05-01 11:42:04', NULL),
(4, 'Павленко Ірина Олегівна', '+380978765521', '2000-05-05', 0, 9, 1, NULL, NULL, NULL),
(5, 'Лисенко Тетяна Дмитрівна', '+380987655567', '2000-05-06', 0, 10, 1, NULL, NULL, NULL),
(6, 'Поліщук Олена Вікторівна', '+380675675521', '2008-02-03', 0, 11, 1, NULL, NULL, NULL),
(7, 'Олійник Марія Олександрівна', '+380987651123', '1998-03-09', 0, 12, 1, NULL, '2026-05-01 12:09:39', NULL),
(8, 'Василенко Богдан Романович', '+380681112223', '2005-09-09', 0, 13, 1, NULL, '2026-05-01 12:15:24', NULL),
(9, 'Клименко Сергій Михайлович', '+380987654129', '2007-09-08', 0, 14, 1, NULL, '2026-05-01 12:28:19', NULL);

-- --------------------------------------------------------

--
-- Структура таблиці `employees`
--

CREATE TABLE `employees` (
  `id_employee` int(11) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `position` varchar(50) DEFAULT NULL,
  `id_user` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `employees`
--

INSERT INTO `employees` (`id_employee`, `full_name`, `position`, `id_user`) VALUES
(1, 'Іван Васильович', 'Адміністратор', 1),
(2, 'Олена Петрівна', 'Менеджер', 2);

-- --------------------------------------------------------

--
-- Структура таблиці `memberships`
--

CREATE TABLE `memberships` (
  `id_membership` int(11) NOT NULL,
  `package_name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `visits_limit` int(11) NOT NULL,
  `duration_days` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `memberships`
--

INSERT INTO `memberships` (`id_membership`, `package_name`, `price`, `visits_limit`, `duration_days`) VALUES
(1, 'Групові + Тренажерний зал', 2500.00, 12, 30),
(2, 'Тільки тренажерний зал', 1500.00, 999, 30),
(3, 'Тільки групові', 1000.00, 12, 30),
(4, 'Разове (Групове)', 200.00, 1, 1),
(5, 'Разове (Самостійно зал)', 250.00, 1, 1),
(6, 'Разове (З тренером)', 0.00, 1, 1);

-- --------------------------------------------------------

--
-- Структура таблиці `sales`
--

CREATE TABLE `sales` (
  `id_sale` int(11) NOT NULL,
  `id_client` int(11) NOT NULL,
  `id_membership` int(11) NOT NULL,
  `sale_date` date NOT NULL,
  `total_paid` decimal(10,2) NOT NULL,
  `classes_left` int(11) DEFAULT 0,
  `id_trainer` int(11) DEFAULT NULL,
  `frozen_days` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `sales`
--

INSERT INTO `sales` (`id_sale`, `id_client`, `id_membership`, `sale_date`, `total_paid`, `classes_left`, `id_trainer`, `frozen_days`) VALUES
(1, 1, 1, '2026-04-24', 2500.00, 11, NULL, 0),
(2, 1, 6, '2026-04-24', 500.00, 0, 1, 0),
(3, 3, 6, '2026-04-24', 500.00, 0, 1, 0),
(4, 2, 3, '2026-04-24', 1000.00, 10, NULL, 0),
(5, 3, 4, '2026-04-24', 200.00, 1, NULL, 0),
(6, 4, 6, '2026-04-24', 500.00, 0, 1, 0),
(7, 3, 3, '2026-04-24', 1000.00, 11, NULL, 0),
(8, 5, 3, '2026-04-24', 1000.00, 8, NULL, 0),
(9, 6, 1, '2026-04-24', 2500.00, 10, NULL, 0),
(10, 7, 4, '2026-04-24', 200.00, 1, NULL, 0),
(11, 7, 3, '2026-04-24', 1000.00, 11, NULL, 0),
(12, 8, 4, '2026-04-24', 200.00, 1, NULL, 0),
(13, 8, 3, '2026-04-24', 1000.00, 11, NULL, 0),
(14, 9, 4, '2026-04-24', 200.00, 0, NULL, 0),
(15, 9, 3, '2026-04-24', 1000.00, 12, NULL, 0);

-- --------------------------------------------------------

--
-- Структура таблиці `schedule`
--

CREATE TABLE `schedule` (
  `id_schedule` int(11) NOT NULL,
  `id_section` int(11) NOT NULL,
  `id_trainer` int(11) NOT NULL,
  `class_date` date NOT NULL,
  `start_time` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `schedule`
--

INSERT INTO `schedule` (`id_schedule`, `id_section`, `id_trainer`, `class_date`, `start_time`) VALUES
(1, 1, 1, '2026-04-24', '09:00:00'),
(2, 4, 2, '2026-04-24', '09:00:00'),
(3, 2, 3, '2026-04-24', '12:00:00'),
(4, 1, 1, '2026-04-25', '10:00:00'),
(5, 2, 3, '2026-04-25', '11:00:00'),
(7, 6, 1, '2026-04-24', '11:30:00'),
(8, 7, 3, '2026-04-25', '10:00:00'),
(9, 2, 3, '2026-04-24', '12:30:00');

-- --------------------------------------------------------

--
-- Структура таблиці `sections`
--

CREATE TABLE `sections` (
  `id_section` int(11) NOT NULL,
  `section_name` varchar(100) NOT NULL,
  `age_limit` int(11) NOT NULL,
  `section_type` varchar(50) NOT NULL DEFAULT 'Групова',
  `capacity` int(11) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `sections`
--

INSERT INTO `sections` (`id_section`, `section_name`, `age_limit`, `section_type`, `capacity`) VALUES
(1, 'Тренажерний зал', 14, 'Індивідуальна', 1),
(2, 'Стретчинг', 0, 'Групова', 15),
(3, 'Бокс', 14, 'Групова', 15),
(4, 'Воркаут', 8, 'Групова', 10),
(5, 'Плавання', 14, 'Групова', 10),
(6, 'Плавання', 6, 'Індивідуальна', 1),
(7, 'Пілатес', 0, 'Групова', 15);

-- --------------------------------------------------------

--
-- Структура таблиці `trainers`
--

CREATE TABLE `trainers` (
  `id_trainer` int(11) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `specialization` varchar(100) NOT NULL,
  `indiv_rate` decimal(10,2) NOT NULL DEFAULT 0.00,
  `group_rate` decimal(10,2) NOT NULL DEFAULT 50.00,
  `id_user` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `trainers`
--

INSERT INTO `trainers` (`id_trainer`, `full_name`, `phone`, `specialization`, `indiv_rate`, `group_rate`, `id_user`) VALUES
(1, 'Руденко Дмитро Русланович', '', '', 500.00, 50.00, 3),
(2, 'Бойко Ігор Володимирович', '', '', 400.00, 50.00, 4),
(3, 'Кравченко Юлія Анатоліївна', '', '', 300.00, 50.00, 5);

-- --------------------------------------------------------

--
-- Структура таблиці `users`
--

CREATE TABLE `users` (
  `id_user` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(100) NOT NULL,
  `role` enum('Admin','Manager','Trainer','Client') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп даних таблиці `users`
--

INSERT INTO `users` (`id_user`, `username`, `password_hash`, `role`) VALUES
(1, 'admin', 'admin123', 'Admin'),
(2, 'manager1', 'man123', 'Manager'),
(3, 'trainer1', 'tr1', 'Trainer'),
(4, 'trainer2', 'tr2', 'Trainer'),
(5, 'trainer3', 'tr3', 'Trainer'),
(6, 'client1', 'cl1', 'Client'),
(7, 'client2', 'cl2', 'Client'),
(8, 'client3', 'cl3', 'Client'),
(9, 'client4', 'cl4', 'Client'),
(10, 'client5', 'cl5', 'Client'),
(11, 'client6', 'cl6', 'Client'),
(12, 'client7', 'cl7', 'Client'),
(13, 'client8', 'cl8', 'Client'),
(14, 'client9', 'cl9', 'Client');

--
-- Індекси збережених таблиць
--

--
-- Індекси таблиці `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id_attendance`),
  ADD KEY `id_schedule` (`id_schedule`),
  ADD KEY `id_client` (`id_client`);

--
-- Індекси таблиці `clients`
--
ALTER TABLE `clients`
  ADD PRIMARY KEY (`id_client`),
  ADD UNIQUE KEY `phone` (`phone`),
  ADD UNIQUE KEY `id_user` (`id_user`);

--
-- Індекси таблиці `employees`
--
ALTER TABLE `employees`
  ADD PRIMARY KEY (`id_employee`),
  ADD UNIQUE KEY `id_user` (`id_user`);

--
-- Індекси таблиці `memberships`
--
ALTER TABLE `memberships`
  ADD PRIMARY KEY (`id_membership`);

--
-- Індекси таблиці `sales`
--
ALTER TABLE `sales`
  ADD PRIMARY KEY (`id_sale`),
  ADD KEY `id_client` (`id_client`),
  ADD KEY `id_membership` (`id_membership`),
  ADD KEY `id_trainer` (`id_trainer`);

--
-- Індекси таблиці `schedule`
--
ALTER TABLE `schedule`
  ADD PRIMARY KEY (`id_schedule`),
  ADD KEY `id_section` (`id_section`),
  ADD KEY `id_trainer` (`id_trainer`);

--
-- Індекси таблиці `sections`
--
ALTER TABLE `sections`
  ADD PRIMARY KEY (`id_section`);

--
-- Індекси таблиці `trainers`
--
ALTER TABLE `trainers`
  ADD PRIMARY KEY (`id_trainer`),
  ADD UNIQUE KEY `id_user` (`id_user`);

--
-- Індекси таблиці `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT для збережених таблиць
--

--
-- AUTO_INCREMENT для таблиці `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id_attendance` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT для таблиці `clients`
--
ALTER TABLE `clients`
  MODIFY `id_client` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT для таблиці `employees`
--
ALTER TABLE `employees`
  MODIFY `id_employee` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT для таблиці `memberships`
--
ALTER TABLE `memberships`
  MODIFY `id_membership` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT для таблиці `sales`
--
ALTER TABLE `sales`
  MODIFY `id_sale` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT для таблиці `schedule`
--
ALTER TABLE `schedule`
  MODIFY `id_schedule` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT для таблиці `sections`
--
ALTER TABLE `sections`
  MODIFY `id_section` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT для таблиці `trainers`
--
ALTER TABLE `trainers`
  MODIFY `id_trainer` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT для таблиці `users`
--
ALTER TABLE `users`
  MODIFY `id_user` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- Обмеження зовнішнього ключа збережених таблиць
--

--
-- Обмеження зовнішнього ключа таблиці `attendance`
--
ALTER TABLE `attendance`
  ADD CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`id_schedule`) REFERENCES `schedule` (`id_schedule`) ON DELETE CASCADE,
  ADD CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`id_client`) REFERENCES `clients` (`id_client`) ON DELETE CASCADE;

--
-- Обмеження зовнішнього ключа таблиці `clients`
--
ALTER TABLE `clients`
  ADD CONSTRAINT `clients_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE SET NULL;

--
-- Обмеження зовнішнього ключа таблиці `employees`
--
ALTER TABLE `employees`
  ADD CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE;

--
-- Обмеження зовнішнього ключа таблиці `sales`
--
ALTER TABLE `sales`
  ADD CONSTRAINT `sales_ibfk_1` FOREIGN KEY (`id_client`) REFERENCES `clients` (`id_client`) ON DELETE CASCADE,
  ADD CONSTRAINT `sales_ibfk_2` FOREIGN KEY (`id_membership`) REFERENCES `memberships` (`id_membership`),
  ADD CONSTRAINT `sales_ibfk_3` FOREIGN KEY (`id_trainer`) REFERENCES `trainers` (`id_trainer`) ON DELETE SET NULL;

--
-- Обмеження зовнішнього ключа таблиці `schedule`
--
ALTER TABLE `schedule`
  ADD CONSTRAINT `schedule_ibfk_1` FOREIGN KEY (`id_section`) REFERENCES `sections` (`id_section`) ON DELETE CASCADE,
  ADD CONSTRAINT `schedule_ibfk_2` FOREIGN KEY (`id_trainer`) REFERENCES `trainers` (`id_trainer`);

--
-- Обмеження зовнішнього ключа таблиці `trainers`
--
ALTER TABLE `trainers`
  ADD CONSTRAINT `trainers_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
