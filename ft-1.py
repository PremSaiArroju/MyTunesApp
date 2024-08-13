import sys
import mysql.connector
from mutagen.easyid3 import EasyID3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QFileDialog, 
                             QMenu, QAction, QHeaderView, QSplitter, QSlider, QLabel)
from PyQt5.QtCore import Qt
from pygame import mixer

class MyTunes(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyTunes")
        self.setGeometry(100, 100, 1000, 600)

        # Initialize the mixer for playback
        mixer.init()

        # Database connection
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="prem1200",  # Replace with your MySQL password
            database="mytunes"
        )
        self.cursor = self.db.cursor()
        self.createTables()

        # Main UI Components
        self.setupUI()

        # For tracking the currently playing song
        self.current_song_index = -1

    def createTables(self):
        # Create songs table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                artist VARCHAR(255),
                album VARCHAR(255),
                year INT,
                genre VARCHAR(255),
                comment TEXT,
                filepath VARCHAR(255)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255)
            )
        ''')
        self.db.commit()

    def setupUI(self):
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Splitter to divide the left panel and the main table
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel for Library and Playlists
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Tree widget for Library and Playlists
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)

        # Tree: "Library"
        library_item = QTreeWidgetItem(self.tree_widget, ["Library"])
        library_item.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)  # No expand/collapse indicator

        # Tree: "Playlists"
        self.playlist_root = QTreeWidgetItem(self.tree_widget, ["Playlists"])
        self.playlist_root.setExpanded(False)

        # Load playlists from the database
        self.loadPlaylists()

        left_layout.addWidget(self.tree_widget)
        left_panel.setLayout(left_layout)

        splitter.addWidget(left_panel)

        # Song library table (right side)
        self.library_table = QTableWidget()
        splitter.addWidget(self.library_table)
        self.library_table.setColumnCount(6)
        self.library_table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Year", "Genre", "Comment"])
        self.library_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.library_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_table.customContextMenuRequested.connect(self.openContextMenu)
        self.library_table.setAcceptDrops(True)
        self.library_table.setDragEnabled(True)
        self.library_table.dragEnterEvent = self.dragEnterEvent
        self.library_table.dropEvent = self.dropEvent

        # Make the table headers stretch to fit the content
        header = self.library_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Bottom layout for controls
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        self.pause_button = QPushButton("Pause")
        self.unpause_button = QPushButton("Unpause")
        self.next_button = QPushButton("Next")
        self.prev_button = QPushButton("Prev")
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setValue(50)  # Set initial volume to 50%
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(lambda value: mixer.music.set_volume(value / 100))

        # Time display labels
        self.start_time_label = QLabel("0:00:00")
        self.end_time_label = QLabel("0:00:00")

        bottom_layout.addWidget(self.play_button)
        bottom_layout.addWidget(self.stop_button)
        bottom_layout.addWidget(self.pause_button)
        bottom_layout.addWidget(self.unpause_button)
        bottom_layout.addWidget(self.next_button)
        bottom_layout.addWidget(self.prev_button)
        bottom_layout.addWidget(self.add_button)
        bottom_layout.addWidget(self.delete_button)
        bottom_layout.addWidget(self.volume_slider)
        bottom_layout.addWidget(self.start_time_label)
        bottom_layout.addWidget(self.end_time_label)

        # Connect button actions
        self.play_button.clicked.connect(self.playSong)
        self.stop_button.clicked.connect(self.stopSong)
        self.pause_button.clicked.connect(self.pauseSong)
        self.unpause_button.clicked.connect(self.unpauseSong)
        self.next_button.clicked.connect(self.nextSong)
        self.prev_button.clicked.connect(self.prevSong)
        self.add_button.clicked.connect(self.addSongDialog)
        self.delete_button.clicked.connect(self.deleteSong)

        # Connect tree selection to load the library or playlist
        self.tree_widget.itemSelectionChanged.connect(self.loadLibraryOnSelection)
        self.tree_widget.itemDoubleClicked.connect(self.togglePlaylistExpansion)

        # Load the song library
        self.loadLibrary()

    def createMenuBar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.openSongDialog)
        file_menu.addAction(open_action)

        add_action = QAction("Add Song", self)
        add_action.triggered.connect(self.addSongDialog)
        file_menu.addAction(add_action)

        delete_action = QAction("Delete Song", self)
        delete_action.triggered.connect(self.deleteSong)
        file_menu.addAction(delete_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def loadLibrary(self):
        # Load songs from the database
        self.cursor.execute("SELECT title, artist, album, year, genre, comment, filepath FROM songs")
        self.songs = self.cursor.fetchall()

        self.library_table.setRowCount(len(self.songs))
        for row_idx, song in enumerate(self.songs):
            for col_idx, value in enumerate(song[:-1]):  # Exclude filepath
                item = QTableWidgetItem(str(value))
                if col_idx != 5:  # Make all fields except the comment field read-only
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(row_idx, col_idx, item)

    def loadPlaylists(self):
        self.playlist_root.takeChildren()  # Clear existing playlists
        self.cursor.execute("SELECT id, name FROM playlists")
        playlists = self.cursor.fetchall()

        for playlist in playlists:
            playlist_item = QTreeWidgetItem(self.playlist_root, [playlist[1]])
            playlist_item.setData(0, Qt.UserRole, playlist[0])

    def loadLibraryOnSelection(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item and selected_item.text(0) == "Library":
            self.loadLibrary()

    def togglePlaylistExpansion(self, item, column):
        if item == self.playlist_root:
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def openContextMenu(self, position):
        selected_row = self.library_table.currentRow()
        if selected_row >= 0:
            menu = QMenu()

            add_action = menu.addAction("Add Song")
            delete_action = menu.addAction("Delete Song")
            add_action.triggered.connect(self.addSongDialog)
            delete_action.triggered.connect(self.deleteSong)
            menu.exec_(self.library_table.viewport().mapToGlobal(position))

    def addSongDialog(self):
        file_dialog = QFileDialog()
        files, _ = file_dialog.getOpenFileNames(self, "Add MP3 Files", "", "MP3 Files (*.mp3)")
        for file_path in files:
            self.addSong(file_path)

    def addSong(self, filepath):
        # Extract metadata using mutagen
        audio = EasyID3(filepath)
        title = audio.get('title', ['Unknown'])[0]
        artist = audio.get('artist', ['Unknown'])[0]
        album = audio.get('album', ['Unknown'])[0]
        year = int(audio.get('date', ['0'])[0].split('-')[0])
        genre = audio.get('genre', ['Unknown'])[0]
        comment = "No comments"

        # Insert into the database
        self.cursor.execute("""
            INSERT INTO songs (title, artist, album, year, genre, comment, filepath) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, artist, album, year, genre, comment, filepath))
        self.db.commit()

        # Reload the library
        self.loadLibrary()

    def deleteSong(self):
        selected_row = self.library_table.currentRow()
        if selected_row >= 0:
            title_item = self.library_table.item(selected_row, 0)
            title = title_item.text()
            self.cursor.execute("DELETE FROM songs WHERE title = %s", (title,))
            self.db.commit()
            self.loadLibrary()

    def playSong(self):
        selected_row = self.library_table.currentRow()
        if selected_row >= 0:
            self.current_song_index = selected_row
            self.playSongAtIndex(self.current_song_index)

    def playSongAtIndex(self, index):
        song = self.songs[index]
        filepath = song[-1]
        mixer.music.load(filepath)
        mixer.music.play()

    def stopSong(self):
        mixer.music.stop()

    def pauseSong(self):
        mixer.music.pause()

    def unpauseSong(self):
        mixer.music.unpause()

    def nextSong(self):
        if self.current_song_index < len(self.songs) - 1:
            self.current_song_index += 1
            self.playSongAtIndex(self.current_song_index)

    def prevSong(self):
        if self.current_song_index > 0:
            self.current_song_index -= 1
            self.playSongAtIndex(self.current_song_index)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            self.addSong(filepath)

    def openSongDialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open MP3 File", "", "MP3 Files (*.mp3)")
        if file_path:
            mixer.music.load(file_path)
            mixer.music.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyTunes()
    window.show()
    sys.exit(app.exec_())
