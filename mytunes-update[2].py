import tkinter as tk
from tkinter import filedialog, messagebox, Menu, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import pygame
from mutagen.easyid3 import EasyID3
import mysql.connector
import os
from tkinter import ttk

# Initialize Pygame mixer
pygame.mixer.init()

# Database connection
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="prem1200",
        database="mytunes"
    )

class MyTunesApp:
    def __init__(self, root, is_main_window=True):
        self.root = root
        self.root.title("MyTunes")

        self.current_song_index = None
        self.paused = False
        self.is_main_window = is_main_window

        self.create_widgets()
        self.populate_song_list()

    def create_widgets(self):
        # Create frames for layout
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        self.frame_bottom = tk.Frame(self.root)
        self.frame_bottom.pack(side=tk.BOTTOM)

        if self.is_main_window:
            # Panel on the left side for Library and Playlist
            self.panel = tk.Frame(self.frame_top, width=200)
            self.panel.pack(side=tk.LEFT, fill=tk.Y)
            self.panel.pack_propagate(False)  # Prevent the panel from resizing

            # Treeview in the panel
            self.tree = ttk.Treeview(self.panel)
            self.tree.pack(fill=tk.BOTH, expand=True)

            # Library branch
            self.tree.insert("", "end", "library", text="Library")
            self.tree.bind("<<TreeviewSelect>>", self.show_library)

            # Playlist branch (collapsible)
            self.tree_playlist = self.tree.insert("", "end", "playlist", text="Playlist", open=True)
            self.tree.bind("<Double-1>", self.toggle_playlist)
            self.tree.bind("<Button-3>", self.show_playlist_context_menu)
            self.populate_playlists()

        # Treeview to display songs in a table format
        columns = ('Title', 'Artist', 'Album', 'Year', 'Genre', 'Comment')
        self.song_treeview = ttk.Treeview(self.frame_top, columns=columns, show='headings')
        self.song_treeview.heading('Title', text='Title')
        self.song_treeview.heading('Artist', text='Artist')
        self.song_treeview.heading('Album', text='Album')
        self.song_treeview.heading('Year', text='Year')
        self.song_treeview.heading('Genre', text='Genre')
        self.song_treeview.heading('Comment', text='Comment')
        
        self.song_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.song_treeview.bind('<<TreeviewSelect>>', self.on_song_select)

        # Enable drag and drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Buttons for control
        self.btn_play = tk.Button(self.frame_bottom, text="Play", command=self.play_song)
        self.btn_play.pack(side=tk.LEFT)

        self.btn_stop = tk.Button(self.frame_bottom, text="Stop", command=self.stop_song)
        self.btn_stop.pack(side=tk.LEFT)

        self.btn_pause = tk.Button(self.frame_bottom, text="Pause", command=self.pause_song)
        self.btn_pause.pack(side=tk.LEFT)

        self.btn_unpause = tk.Button(self.frame_bottom, text="Unpause", command=self.unpause_song)
        self.btn_unpause.pack(side=tk.LEFT)

        self.btn_next = tk.Button(self.frame_bottom, text="Next", command=self.next_song)
        self.btn_next.pack(side=tk.LEFT)

        self.btn_prev = tk.Button(self.frame_bottom, text="Prev", command=self.prev_song)
        self.btn_prev.pack(side=tk.LEFT)

        # Add/Delete buttons
        self.btn_add = tk.Button(self.frame_bottom, text="Add", command=self.add_song)
        self.btn_add.pack(side=tk.LEFT)

        self.btn_delete = tk.Button(self.frame_bottom, text="Delete", command=self.delete_song)
        self.btn_delete.pack(side=tk.LEFT)

        # Volume slider
        self.volume_slider = tk.Scale(self.frame_bottom, from_=0, to=100, orient=tk.HORIZONTAL, label="Volume")
        self.volume_slider.set(50)
        self.volume_slider.pack(side=tk.LEFT)
        self.volume_slider.bind("<Motion>", self.set_volume)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Song", command=self.add_song)
        self.context_menu.add_command(label="Delete Song", command=self.delete_song)
        self.context_menu.add_command(label="Add to Playlist", command=self.add_to_playlist_menu)
        self.context_menu.add_command(label="Exit", command=self.root.quit)

        # Bind the right-click event to show the context menu
        self.song_treeview.bind("<Button-3>", self.show_context_menu)

        # Menu bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_song)
        file_menu.add_separator()
        file_menu.add_command(label="Add Song", command=self.add_song)
        file_menu.add_command(label="Delete Song", command=self.delete_song)
        file_menu.add_command(label="Create Playlist", command=self.create_playlist)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def set_volume(self, event=None):
        volume = self.volume_slider.get() / 100
        pygame.mixer.music.set_volume(volume)

    def populate_song_list(self):
        for i in self.song_treeview.get_children():
            self.song_treeview.delete(i)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, title, artist, album, year, genre, comment FROM songs")
        self.songs = cursor.fetchall()
        for row in self.songs:
            self.song_treeview.insert('', tk.END, values=row[1:])
        connection.close()

    def on_song_select(self, event):
        selection = self.song_treeview.selection()
        if selection:
            self.current_song_index = self.song_treeview.index(selection[0])

    def play_song(self):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

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
        connection.close()

    def stop_song(self):
        pygame.mixer.music.stop()
        self.paused = False

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
            self.song_treeview.selection_set(self.song_treeview.get_children()[self.current_song_index])
            self.play_song()

    def prev_song(self):
        if self.current_song_index is not None:
            self.current_song_index = (self.current_song_index - 1) % len(self.songs)
            self.song_treeview.selection_set(self.song_treeview.get_children()[self.current_song_index])
            self.play_song()

    def add_song(self, filepath=None):
        if not filepath:
            filepath = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        
        if filepath:
            audio = EasyID3(filepath)
            title = audio.get("title", ["Unknown Title"])[0]
            artist = audio.get("artist", ["Unknown Artist"])[0]
            album = audio.get("album", ["Unknown Album"])[0]
            year = audio.get("date", ["Unknown Year"])[0]
            genre = audio.get("genre", ["Unknown Genre"])[0]
            comment = audio.get("comment", [""])[0]

            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO songs (title, artist, album, year, genre, comment, filepath) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (title, artist, album, year, genre, comment, filepath))
            connection.commit()
            connection.close()
            
            self.populate_song_list()
            messagebox.showinfo("Info", "Song added successfully")

    def delete_song(self):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

        song_id = self.songs[self.current_song_index][0]

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM songs WHERE id = %s", (song_id,))
        connection.commit()
        connection.close()
        
        self.populate_song_list()
        self.current_song_index = None
        messagebox.showinfo("Info", "Song deleted successfully")

    def open_song(self):
        filepath = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if filepath:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.paused = False

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for file in files:
            if file.endswith(".mp3"):
                self.add_song_to_library(file)
                if self.is_main_window:
                    selected_item = self.tree.focus()
                    if selected_item.startswith("playlist_"):
                        playlist_id = int(selected_item.split("_")[1])
                        self.add_song_to_playlist(file, playlist_id)

    def create_playlist(self):
        playlist_name = simpledialog.askstring("Input", "Enter playlist name:")
        if playlist_name:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO playlists (name) VALUES (%s)", (playlist_name,))
            connection.commit()
            cursor.execute("SELECT id FROM playlists WHERE name = %s", (playlist_name,))
            playlist_id = cursor.fetchone()[0]
            connection.close()
            
            self.populate_playlists()
            self.show_playlist(playlist_id)
            self.tree.selection_set(self.tree.get_children()[1])
            messagebox.showinfo("Info", "Playlist created successfully")

    def populate_playlists(self):
        for item in self.tree.get_children(self.tree_playlist):
            self.tree.delete(item)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        for playlist in playlists:
            self.tree.insert(self.tree_playlist, "end", text=playlist[1], iid=f"playlist_{playlist[0]}")
        connection.close()

    def show_library(self, event):
        selected_item = self.tree.focus()
        if selected_item == "library":
            self.populate_song_list()

    def toggle_playlist(self, event):
        selected_item = self.tree.focus()
        if selected_item == "playlist":
            if self.tree.item(selected_item, "open"):
                self.tree.item(selected_item, open=False)
            else:
                self.tree.item(selected_item, open=True)

    def show_playlist(self, playlist_id):
        for i in self.song_treeview.get_children():
            self.song_treeview.delete(i)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT s.id, s.title, s.artist, s.album, s.year, s.genre, s.comment FROM playlist_songs ps JOIN songs s ON ps.song_id = s.id WHERE ps.playlist_id = %s", (playlist_id,))
        self.songs = cursor.fetchall()
        for row in self.songs:
            self.song_treeview.insert('', tk.END, values=row[1:])
        connection.close()

    def show_playlist_context_menu(self, event):
        selected_item = self.tree.identify_row(event.y)
        if selected_item.startswith("playlist_"):
            self.tree.selection_set(selected_item)
            self.tree_context_menu = tk.Menu(self.root, tearoff=0)
            self.tree_context_menu.add_command(label="Open in New Window", command=self.open_playlist_in_new_window)
            self.tree_context_menu.add_command(label="Delete Playlist", command=self.delete_playlist)
            self.tree_context_menu.post(event.x_root, event.y_root)

    def open_playlist_in_new_window(self):
        selected_item = self.tree.focus()
        if selected_item.startswith("playlist_"):
            playlist_id = int(selected_item.split("_")[1])
            new_window = tk.Toplevel(self.root)
            app = MyTunesApp(new_window, is_main_window=False)
            app.show_playlist(playlist_id)
            self.populate_song_list()
            self.tree.selection_set("library")

    def delete_playlist(self):
        selected_item = self.tree.focus()
        if selected_item.startswith("playlist_"):
            playlist_id = int(selected_item.split("_")[1])
            confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this playlist?")
            if confirm:
                connection = create_connection()
                cursor = connection.cursor()
                cursor.execute("DELETE FROM playlists WHERE id = %s", (playlist_id,))
                cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = %s", (playlist_id,))
                connection.commit()
                connection.close()
                
                self.populate_playlists()
                messagebox.showinfo("Info", "Playlist deleted successfully")

    def add_to_playlist_menu(self):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

        song_id = self.songs[self.current_song_index][0]

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        connection.close()

        menu = tk.Menu(self.context_menu, tearoff=0)
        for playlist in playlists:
            menu.add_command(label=playlist[1], command=lambda pid=playlist[0]: self.add_song_to_playlist(song_id, pid))
        
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

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
        cursor.execute("INSERT INTO songs (title, artist, album, year, genre, comment, filepath) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (title, artist, album, year, genre, comment, filepath))
        connection.commit()
        cursor.execute("SELECT id FROM songs WHERE filepath = %s", (filepath,))
        song_id = cursor.fetchone()[0]
        connection.close()

        self.populate_song_list()
        return song_id

    def add_song_to_playlist(self, song_id, playlist_id):
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)", (playlist_id, song_id))
        connection.commit()
        connection.close()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MyTunesApp(root)
    root.mainloop()
