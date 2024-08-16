/*CREATE DATABASE mytunes;

USE mytunes;

CREATE TABLE songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    artist VARCHAR(255),
    album VARCHAR(255),
    year INT,
    genre VARCHAR(255),
    comment TEXT,
    filepath VARCHAR(255)
);

CREATE TABLE playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE playlist_songs (
    playlist_id INT,
    song_id INT,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

DROP DATABASE mytunes;

*/
CREATE DATABASE mytunes
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mytunes;

CREATE TABLE songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    year INT,
    genre VARCHAR(255),
    comment TEXT,
    filepath VARCHAR(255) NOT NULL,
    UNIQUE(filepath)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE playlist_songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    playlist_id INT,
    song_id INT,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

