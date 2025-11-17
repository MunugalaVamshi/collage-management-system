# db_seed.sql


CREATE TABLE IF NOT EXISTS user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(120) UNIQUE,
  password_hash VARCHAR(255),
  full_name VARCHAR(120),
  role VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS course (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) UNIQUE,
  name VARCHAR(200),
  credits INT
);

CREATE TABLE IF NOT EXISTS student (
  id INT AUTO_INCREMENT PRIMARY KEY,
  roll VARCHAR(30) UNIQUE,
  name VARCHAR(200),
  email VARCHAR(120),
  admission_year INT
);

CREATE TABLE IF NOT EXISTS marks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT,
  course_id INT,
  internal FLOAT,
  end_sem FLOAT
);

CREATE TABLE IF NOT EXISTS feepayment (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT,
  amount FLOAT,
  date DATE,
  note VARCHAR(255)
);