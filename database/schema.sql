CREATE DATABASE IF NOT EXISTS visionid_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE visionid_ai;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  full_name VARCHAR(180) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','operator','viewer') NOT NULL DEFAULT 'viewer',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_users_role (role),
  INDEX idx_users_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS datasets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(180) NOT NULL,
  description TEXT NULL,
  source_path VARCHAR(512) NULL,
  total_images INT NOT NULL DEFAULT 0,
  processed_images INT NOT NULL DEFAULT 0,
  status VARCHAR(40) NOT NULL DEFAULT 'pending',
  created_by BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_datasets_status (status),
  CONSTRAINT fk_datasets_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS persons (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  person_code VARCHAR(64) NOT NULL UNIQUE,
  full_name VARCHAR(180) NOT NULL,
  email VARCHAR(255) NULL,
  phone VARCHAR(40) NULL,
  department VARCHAR(120) NULL,
  title VARCHAR(120) NULL,
  notes TEXT NULL,
  primary_image_path VARCHAR(512) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  embedding_model VARCHAR(80) NOT NULL DEFAULT 'insightface_buffalo_l',
  duplicate_of BIGINT NULL,
  created_by BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_persons_name (full_name),
  INDEX idx_persons_active (is_active),
  CONSTRAINT fk_persons_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_persons_duplicate_of FOREIGN KEY (duplicate_of) REFERENCES persons(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS face_samples (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  person_id BIGINT NOT NULL,
  image_path VARCHAR(512) NOT NULL,
  crop_path VARCHAR(512) NULL,
  quality_score FLOAT NOT NULL DEFAULT 0,
  blur_score FLOAT NOT NULL DEFAULT 0,
  low_light_score FLOAT NOT NULL DEFAULT 0,
  detection_score FLOAT NOT NULL DEFAULT 0,
  embedding_hash CHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_face_samples_person (person_id),
  INDEX idx_face_samples_hash (embedding_hash),
  CONSTRAINT fk_face_samples_person FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS face_embeddings (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sample_id BIGINT NOT NULL,
  person_id BIGINT NOT NULL,
  embedding_dim INT NOT NULL,
  embedding_vector LONGBLOB NOT NULL,
  similarity_threshold FLOAT NOT NULL DEFAULT 0.45,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_face_embeddings_person (person_id),
  INDEX idx_face_embeddings_sample (sample_id),
  CONSTRAINT fk_face_embeddings_sample FOREIGN KEY (sample_id) REFERENCES face_samples(id) ON DELETE CASCADE,
  CONSTRAINT fk_face_embeddings_person FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recognition_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  person_id BIGINT NULL,
  person_name VARCHAR(180) NULL,
  source_type VARCHAR(40) NOT NULL,
  source_ref VARCHAR(255) NULL,
  confidence FLOAT NOT NULL DEFAULT 0,
  distance FLOAT NOT NULL DEFAULT 0,
  is_unknown BOOLEAN NOT NULL DEFAULT FALSE,
  frame_index INT NOT NULL DEFAULT 0,
  bounding_box_json JSON NULL,
  embedding_hash CHAR(64) NULL,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_recognition_logs_person (person_id),
  INDEX idx_recognition_logs_unknown (is_unknown),
  INDEX idx_recognition_logs_occurred (occurred_at),
  CONSTRAINT fk_recognition_logs_person FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  actor_user_id BIGINT NULL,
  action VARCHAR(120) NOT NULL,
  entity_type VARCHAR(80) NOT NULL,
  entity_id VARCHAR(80) NULL,
  metadata_json JSON NULL,
  ip_address VARCHAR(80) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_actor (actor_user_id),
  INDEX idx_audit_action (action),
  INDEX idx_audit_created (created_at),
  CONSTRAINT fk_audit_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;
