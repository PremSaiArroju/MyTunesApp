#Updated code with drag and drop

from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSlider, QProgressBar, QLabel, QMenu, QFileDialog, QInputDialog, QLineEdit, QMessageBox, QSplitter
from PyQt5.QtCore import Qt, QTimer, QMimeData, QByteArray, QDataStream
from PyQt5.QtGui import QCursor, QDragEnterEvent, QDropEvent, QDrag
import pygame
from mutagen.easyid3 import EasyID3
import mysql.connector
import os
import json
import random
import sys

# Initialize Pygame mixer
pygame.mixer.init()

# Establish MySQL database connection
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # update your username
        password="prem1200",  # use your MySQL password
        database="mytunes"
    )

class MyTunesApp(QMainWindow):
    def __init__(self, playlist_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MyTunes")
        self.setMinimumSize(800, 500)

        self.current_song_index = None
        self.paused = False
        self.current_playlist = playlist_id  # Set current playlist ID
        self.recent_play = []
        self.shuffle = False
        self.repeat = False

        self.load_configuration()
        self.init_ui()
        self.populate_song_list(self.current_playlist)  # Load songs from the selected playlist
        self.update_timers_and_progress()
        self.load_playlists()

    def load_configuration(self):
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'visible_columns': {'Title': True, 'Artist': True, 'Album': True, 'Year': True, 'Genre': True, 'Comment': True},
                'sort_column': 'Title',
                'sort_reverse': False,
                'recent_play': []
            }
        self.recent_play = self.config.get('recent_play', [])

    def save_configuration(self):
        self.config['recent_play'] = self.recent_play
        with open("config.json", "w") as f:
            json.dump(self.config, f)

    def init_ui(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        
        # Library and Playlist tree on the left side
        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderHidden(True)
        self.library_tree.itemClicked.connect(self.on_library_item_clicked)
        self.library_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_tree.customContextMenuRequested.connect(self.show_playlist_context_menu)
        self.library_tree.setAcceptDrops(True)
        self.library_tree.setDragEnabled(True)
        self.library_tree.dragEnterEvent = self.dragEnterEvent
        self.library_tree.dropEvent = self.dropEvent

        library_item = QTreeWidgetItem(self.library_tree)
        library_item.setText(0, "Library")

        playlist_item = QTreeWidgetItem(self.library_tree)
        playlist_item.setText(0, "Playlists")

        # Creating a splitter to hold the library and playlist with the song tree view
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.library_tree)

        # Vertical layout for the song tree and control buttons
        right_layout = QVBoxLayout()

        # Song tree view in the center
        self.song_treeview = QTreeWidget()
        self.song_treeview.setColumnCount(6)
        self.song_treeview.setHeaderLabels(['Title', 'Artist', 'Album', 'Year', 'Genre', 'Comment'])
        self.song_treeview.itemSelectionChanged.connect(self.on_song_select)
        self.song_treeview.itemDoubleClicked.connect(self.on_tree_double_click)
        self.song_treeview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.song_treeview.customContextMenuRequested.connect(self.show_song_context_menu)
        self.song_treeview.setAcceptDrops(True)
        self.song_treeview.setDragEnabled(True)
        self.song_treeview.setDragDropMode(QTreeWidget.InternalMove)
        self.song_treeview.dragEnterEvent = self.dragEnterEvent
        self.song_treeview.dropEvent = self.dropEvent
        self.song_treeview.startDrag = self.start_drag

        right_layout.addWidget(self.song_treeview)

        # Timers and progress bar
        timer_layout = QVBoxLayout()
        self.left_timer_label = QLabel("0:00:00")
        self.right_timer_label = QLabel("0:00:00")
        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Horizontal)
        timer_layout.addWidget(self.left_timer_label)
        timer_layout.addWidget(self.progress_bar)
        timer_layout.addWidget(self.right_timer_label)
        right_layout.addLayout(timer_layout)

        # Control buttons at the bottom
        controls_layout = QHBoxLayout()
        self.btn_play = QPushButton("Play", self)
        self.btn_stop = QPushButton("Stop", self)
        self.btn_pause = QPushButton("Pause", self)
        self.btn_unpause = QPushButton("Unpause", self)
        self.btn_next = QPushButton("Next", self)
        self.btn_prev = QPushButton("Prev", self)
        self.btn_add = QPushButton("Add", self)
        self.btn_delete = QPushButton("Delete", self)
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.set_volume)

        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_unpause)
        controls_layout.addWidget(self.btn_next)
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_add)
        controls_layout.addWidget(self.btn_delete)
        controls_layout.addWidget(QLabel("Volume"))
        controls_layout.addWidget(self.volume_slider)

        right_layout.addLayout(controls_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.addWidget(right_widget)
        main_layout.addWidget(splitter)

        # Connecting button actions
        self.btn_play.clicked.connect(self.play_song)
        self.btn_stop.clicked.connect(self.stop_song)
        self.btn_pause.clicked.connect(self.pause_song)
        self.btn_unpause.clicked.connect(self.unpause_song)
        self.btn_next.clicked.connect(self.next_song)
        self.btn_prev.clicked.connect(self.prev_song)
        self.btn_add.clicked.connect(self.add_song)
        self.btn_delete.clicked.connect(self.delete_song)

        # Menu bar
        self.menu = self.menuBar()

        file_menu = self.menu.addMenu('File')
        open_action = file_menu.addAction('Open')
        open_action.triggered.connect(self.open_song)
        file_menu.addSeparator()
        add_action = file_menu.addAction('Add Song')
        add_action.triggered.connect(self.add_song)
        delete_action = file_menu.addAction('Delete Song')
        delete_action.triggered.connect(self.delete_song)
        create_playlist_action = file_menu.addAction('Create Playlist')
        create_playlist_action.triggered.connect(self.create_playlist)
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        controls_menu = self.menu.addMenu('Controls')
        play_action = controls_menu.addAction('Play')
        play_action.setShortcut('Space')
        play_action.triggered.connect(self.play_song)

        next_action = controls_menu.addAction('Next')
        next_action.setShortcut('Ctrl+Right')
        next_action.triggered.connect(self.next_song)

        prev_action = controls_menu.addAction('Previous')
        prev_action.setShortcut('Ctrl+Left')
        prev_action.triggered.connect(self.prev_song)

        go_to_current_action = controls_menu.addAction('Go to Current Song')
        go_to_current_action.setShortcut('Ctrl+L')
        go_to_current_action.triggered.connect(self.go_to_current_song)

        controls_menu.addSeparator()
        inc_volume_action = controls_menu.addAction('Increase Volume')
        inc_volume_action.setShortcut('Ctrl+I')
        inc_volume_action.triggered.connect(lambda: self.change_volume(5))

        dec_volume_action = controls_menu.addAction('Decrease Volume')
        dec_volume_action.setShortcut('Ctrl+D')
        dec_volume_action.triggered.connect(lambda: self.change_volume(-5))

        controls_menu.addSeparator()

        shuffle_action = controls_menu.addAction('Shuffle')
        shuffle_action.setCheckable(True)
        shuffle_action.setChecked(self.shuffle)
        shuffle_action.toggled.connect(self.toggle_shuffle)

        repeat_action = controls_menu.addAction('Repeat')
        repeat_action.setCheckable(True)
        repeat_action.setChecked(self.repeat)
        repeat_action.toggled.connect(self.toggle_repeat)

    def populate_song_list(self, playlist_id=None):
        self.song_treeview.clear()

        connection = create_connection()
        cursor = connection.cursor()
        if playlist_id:
            cursor.execute("SELECT songs.id, title, artist, album, year, genre, comment FROM songs "
                           "JOIN playlist_songs ON songs.id = playlist_songs.song_id WHERE playlist_songs.playlist_id = %s", (playlist_id,))
        else:
            cursor.execute("SELECT id, title, artist, album, year, genre, comment FROM songs")
        self.songs = cursor.fetchall()

        column_map = {'Title': 1, 'Artist': 2, 'Album': 3, 'Year': 4, 'Genre': 5, 'Comment': 6}
        self.songs.sort(key=lambda x: x[column_map[self.config['sort_column']]], reverse=self.config['sort_reverse'])

        for row in self.songs:
            item = QTreeWidgetItem(self.song_treeview)
            item.setText(0, row[1])  # Title
            item.setText(1, row[2])  # Artist
            item.setText(2, row[3])  # Album
            item.setText(3, str(row[4]))  # Year (converted to string)
            item.setText(4, row[5])  # Genre
            item.setText(5, row[6])  # Comment
            item.setData(0, Qt.UserRole, row[0])  # Store song ID in the item

        connection.close()

    def on_song_select(self):
        selection = self.song_treeview.selectedItems()
        if selection:
            self.current_song_index = self.song_treeview.indexOfTopLevelItem(selection[0])

    def on_library_item_clicked(self, item, column):
        if item.text(0) == "Library":
            self.current_playlist = None
            self.populate_song_list()
        elif item.parent() and item.parent().text(0) == "Playlists":
            playlist_id = item.data(0, Qt.UserRole)
            self.current_playlist = playlist_id
            self.populate_song_list(playlist_id)

    def play_song(self):
        try:
            if self.current_song_index is not None:
                if self.shuffle:
                    self.current_song_index = random.randint(0, len(self.songs) - 1)

                song_id = self.songs[self.current_song_index][0]

                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute("SELECT filepath FROM songs WHERE id = %s", (song_id,))
                result = cursor.fetchone()
                if result:
                    song_path = result[0]
                    pygame.mixer.music.load(song_path)
                    pygame.mixer.music.play()
                    self.paused = False
                    self.song_length = pygame.mixer.Sound(song_path).get_length()
                    self.start_time = pygame.time.get_ticks()

                    if not self.shuffle:
                        if len(self.recent_play) == 10:
                            self.recent_play.pop(0)
                        self.recent_play.append(self.songs[self.current_song_index])
                        self.save_configuration()

                connection.close()
                self.update_timers_and_progress()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during playback: {e}")

    # When opening a new window, ensure it's properly managed
    def open_playlist_in_new_window(self):
        try:
            selected_item = self.library_tree.currentItem()
            playlist_id = selected_item.data(0, Qt.UserRole)
            new_window = MyTunesApp(playlist_id=playlist_id)  # Removed parent=self to make it fully independent
            new_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open playlist in a new window: {e}")


    def stop_song(self):
        pygame.mixer.music.stop()
        self.paused = False
        self.reset_timers()

    def pause_song(self):
        if not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def unpause_song(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False

    def next_song(self):
        if self.current_song_index is not None:
            self.current_song_index = (self.current_song_index + 1) % len(self.songs)
            self.song_treeview.setCurrentItem(self.song_treeview.topLevelItem(self.current_song_index))
            self.play_song()

    def prev_song(self):
        if self.current_song_index is not None:
            self.current_song_index = (self.current_song_index - 1) % len(self.songs)
            self.song_treeview.setCurrentItem(self.song_treeview.topLevelItem(self.current_song_index))
            self.play_song()

    def add_song(self, filepath=None):
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(self, "Open MP3 File", "", "MP3 files (*.mp3)")

        if filepath:
            song_id = self.add_song_to_library(filepath)
            self.populate_song_list(self.current_playlist)  # Refresh song list after adding
            return song_id
        return None

    def add_song_to_library(self, filepath):
        audio = EasyID3(filepath)
        title = audio.get("title", ["Unknown Title"])[0]
        artist = audio.get("artist", ["Unknown Artist"])[0]
        album = audio.get("album", ["Unknown Album"])[0]
        year = audio.get("date", ["Unknown Year"])[0]
        genre = audio.get("genre", ["Unknown Genre"])[0]
        comment = audio.get("comment", [""])[0]

        connection = create_connection()
        cursor = connection.cursor()

        # Check for duplicates in the library
        cursor.execute("SELECT * FROM songs WHERE title = %s AND artist = %s AND album = %s", (title, artist, album))
        existing_song = cursor.fetchone()

        if existing_song:
            song_id = existing_song[0]
        else:
            cursor.execute("INSERT INTO songs (title, artist, album, year, genre, comment, filepath) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (title, artist, album, year, genre, comment, filepath))
            connection.commit()
            song_id = cursor.lastrowid

        if self.current_playlist:
            cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)", (self.current_playlist, song_id))
            connection.commit()

        connection.close()
        return song_id

    def delete_song(self):
        if self.current_song_index is None:
            QMessageBox.warning(self, "Warning", "No song selected")
            return

        song_id = self.songs[self.current_song_index][0]

        connection = create_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM playlist_songs WHERE song_id = %s", (song_id,))
            cursor.execute("DELETE FROM songs WHERE id = %s", (song_id,))
            connection.commit()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"Error deleting song: {err}")
        finally:
            connection.close()

        self.populate_song_list(self.current_playlist)
        self.stop_song()  # Stop the song if it's playing
        self.current_song_index = None
        QMessageBox.information(self, "Info", "Song deleted successfully")

    def open_song(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open MP3 File", "", "MP3 files (*.mp3)")
        if filepath:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.paused = False

    def set_volume(self, val):
        volume = int(val) / 100
        pygame.mixer.music.set_volume(volume)

    def sort_column(self, col):
        self.config['sort_column'] = col
        self.config['sort_reverse'] = not self.config['sort_reverse']
        self.populate_song_list(self.current_playlist)
        self.save_configuration()

    def update_timers_and_progress(self):
        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() / 1000
            elapsed_time = int(current_time)
            remaining_time = int(self.song_length - current_time)

            self.left_timer_label.setText(self.format_time(elapsed_time))
            self.right_timer_label.setText(self.format_time(remaining_time))

            # Convert the progress to an integer percentage
            progress_value = int((elapsed_time / self.song_length) * 100)
            self.progress_bar.setValue(progress_value)

        else:
            self.reset_timers()

        QTimer.singleShot(1000, self.update_timers_and_progress)

    def on_tree_double_click(self, item, column):
        if column == 5:  # Assuming the "Comment" column is the 6th column (index 5)
            song_id = self.songs[self.current_song_index][0]
            current_comment = item.text(column)

            new_comment, ok = QInputDialog.getText(self, "Edit Comment", "Enter new comment:", QLineEdit.Normal, current_comment)
            if ok:
                item.setText(column, new_comment)
                self.save_comment(song_id, new_comment)

    def save_comment(self, song_id, comment):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE songs SET comment = %s WHERE id = %s", (comment, song_id))
        connection.commit()
        connection.close()

    def reset_timers(self):
        self.left_timer_label.setText("0:00:00")
        self.right_timer_label.setText("0:00:00")
        self.progress_bar.setValue(0)

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours}:{minutes:02}:{seconds:02}"

    def go_to_current_song(self):
        if self.current_song_index is not None:
            self.song_treeview.setCurrentItem(self.song_treeview.topLevelItem(self.current_song_index))
            self.song_treeview.scrollToItem(self.song_treeview.topLevelItem(self.current_song_index))

    def change_volume(self, amount):
        current_volume = self.volume_slider.value()
        new_volume = min(100, max(0, current_volume + amount))
        self.volume_slider.setValue(new_volume)
        self.set_volume(new_volume)

    def toggle_shuffle(self, checked):
        self.shuffle = checked

    def toggle_repeat(self, checked):
        self.repeat = checked

    def show_song_context_menu(self, pos):
        selected_item = self.song_treeview.itemAt(pos)
        if selected_item:
            menu = QMenu(self)

            add_to_playlist_menu = menu.addMenu("Add to Playlist")
            playlists = self.get_playlists()
            for playlist in playlists:
                action = add_to_playlist_menu.addAction(playlist[1])
                action.triggered.connect(lambda checked, p=playlist[0]: self.add_song_to_selected_playlist(self.songs[self.current_song_index][0], p))

            menu.addAction("Delete Song", self.delete_song)
            menu.exec_(self.song_treeview.mapToGlobal(pos))

    def add_song_to_selected_playlist(self, song_id, playlist_id):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)", (playlist_id, song_id))
        connection.commit()
        connection.close()
        QMessageBox.information(self, "Info", "Song added to playlist successfully")

    def get_playlists(self):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        connection.close()
        return playlists

    def create_playlist(self):
        playlist_name, ok = QInputDialog.getText(self, "Create Playlist", "Enter playlist name:")
        if ok and playlist_name:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO playlists (name) VALUES (%s)", (playlist_name,))
            connection.commit()
            playlist_id = cursor.lastrowid

            playlist_item = QTreeWidgetItem(self.library_tree.findItems("Playlists", Qt.MatchExactly)[0])
            playlist_item.setText(0, playlist_name)
            playlist_item.setData(0, Qt.UserRole, playlist_id)

            connection.close()

    def show_playlist_context_menu(self, pos):
        selected_item = self.library_tree.itemAt(pos)
        if selected_item and selected_item.data(0, Qt.UserRole):
            menu = QMenu(self)
            menu.addAction("Open in New Window", self.open_playlist_in_new_window)
            menu.addAction("Delete Playlist", self.delete_playlist)
            menu.exec_(self.library_tree.mapToGlobal(pos))

    def delete_playlist(self):
        selected_item = self.library_tree.currentItem()
        playlist_id = selected_item.data(0, Qt.UserRole)
        if QMessageBox.question(self, "Delete Playlist", "Are you sure you want to delete this playlist?") == QMessageBox.Yes:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = %s", (playlist_id,))
            cursor.execute("DELETE FROM playlists WHERE id = %s", (playlist_id,))
            connection.commit()
            connection.close()

            selected_item.parent().removeChild(selected_item)
            self.current_playlist = None
            self.populate_song_list()
            QMessageBox.information(self, "Info", "Playlist deleted successfully")

    def load_playlists(self):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        connection.close()

        playlist_item = self.library_tree.findItems("Playlists", Qt.MatchExactly)[0]
        for playlist in playlists:
            item = QTreeWidgetItem(playlist_item)
            item.setText(0, playlist[1])
            item.setData(0, Qt.UserRole, playlist[0])

    def start_drag(self, supported_actions):
        drag = QDrag(self)
        mime_data = QMimeData()

        selected_items = self.song_treeview.selectedItems()
        if not selected_items:
            return

        # Serialize the song ID(s) of the selected item(s) to the drag data
        song_ids = [item.data(0, Qt.UserRole) for item in selected_items]
        mime_data.setData("application/x-song-ids", QByteArray(str(song_ids).encode('utf-8')))
        drag.setMimeData(mime_data)
        drag.exec_(supported_actions)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-song-ids"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.endswith(".mp3"):
                    song_id = self.add_song(filepath)
                    if song_id and self.current_playlist:
                        self.add_song_to_selected_playlist(song_id, self.current_playlist)
            self.populate_song_list(self.current_playlist)
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-song-ids"):
            song_ids = eval(event.mimeData().data("application/x-song-ids").data().decode('utf-8'))
            for song_id in song_ids:
                if self.current_playlist:
                    self.add_song_to_selected_playlist(song_id, self.current_playlist)
            event.acceptProposedAction()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyTunesApp()
    window.show()
    sys.exit(app.exec_())
