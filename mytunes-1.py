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

# Establish MySQL database connection
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root", #update your username
        password="prem1200", #use your mysql password
        database="mytunes"
    )

class MyTunesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MyTunes")

        self.root.minsize(800, 300)
        
        self.current_song_index = None
        self.paused = False
        self.editing_comment = False
        self.comment_entry = None
        self.current_playlist = None

        self.create_widgets()
        self.populate_song_list()

    def create_widgets(self):
        # Create a style
        style = ttk.Style()
        style.configure("Treeview.Heading", borderwidth=1, relief="solid")
        style.configure("Treeview", borderwidth=1, relief="solid")
        style.map('Treeview', background=[('selected', 'lightblue')])

        # Create frames for layout
        self.frame_left = tk.Frame(self.root, width=200)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y)

        self.frame_main = tk.Frame(self.root)
        self.frame_main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame for song list
        self.frame_top = tk.Frame(self.frame_main)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        # Frame for control buttons
        self.frame_bottom = tk.Frame(self.frame_main)
        self.frame_bottom.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview to display songs in a table format
        columns = ('Title', 'Artist', 'Album', 'Year', 'Genre', 'Comment')
        self.song_treeview = ttk.Treeview(self.frame_top, columns=columns, show='headings', style="Treeview")
        
        self.song_treeview.heading('Title', text='Title')
        self.song_treeview.column('Title', minwidth=100, width=200)
        
        self.song_treeview.heading('Artist', text='Artist')
        self.song_treeview.column('Artist', minwidth=100, width=150)
        
        self.song_treeview.heading('Album', text='Album')
        self.song_treeview.column('Album', minwidth=100, width=150)
        
        self.song_treeview.heading('Year', text='Year')
        self.song_treeview.column('Year', minwidth=50, width=80)
        
        self.song_treeview.heading('Genre', text='Genre')
        self.song_treeview.column('Genre', minwidth=100, width=150)
        
        self.song_treeview.heading('Comment', text='Comment')
        self.song_treeview.column('Comment', minwidth=100, width=250)
        
        self.song_treeview.pack(fill=tk.BOTH, expand=True)
        self.song_treeview.bind('<<TreeviewSelect>>', self.on_song_select)
        self.song_treeview.bind('<Double-1>', self.on_tree_double_click)

        # Enable drag and drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Buttons for control
        self.btn_play = tk.Button(self.frame_bottom, text="Play", command=self.play_song)
        self.btn_play.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop = tk.Button(self.frame_bottom, text="Stop", command=self.stop_song)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_pause = tk.Button(self.frame_bottom, text="Pause", command=self.pause_song)
        self.btn_pause.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_unpause = tk.Button(self.frame_bottom, text="Unpause", command=self.unpause_song)
        self.btn_unpause.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_next = tk.Button(self.frame_bottom, text="Next", command=self.next_song)
        self.btn_next.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_prev = tk.Button(self.frame_bottom, text="Prev", command=self.prev_song)
        self.btn_prev.pack(side=tk.LEFT, padx=5, pady=5)

        # Add/Delete buttons
        self.btn_add = tk.Button(self.frame_bottom, text="Add", command=self.add_song)
        self.btn_add.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_delete = tk.Button(self.frame_bottom, text="Delete", command=self.delete_song)
        self.btn_delete.pack(side=tk.LEFT, padx=5, pady=5)

        # Volume slider
        self.volume_slider = tk.Scale(self.frame_bottom, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_slider.set(50)
        self.volume_slider.pack(side=tk.LEFT, padx=5, pady=5)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Song", command=self.add_song)
        self.context_menu.add_command(label="Delete Song", command=self.delete_song)
        self.context_menu.add_command(label="Exit", command=self.root.quit)

        self.add_to_playlist_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Add to playlist", menu=self.add_to_playlist_menu)

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

        # Add Library and Playlist trees
        self.library_tree = ttk.Treeview(self.frame_left, selectmode="browse")
        self.library_tree.pack(fill=tk.Y, expand=True)

        self.library_tree.insert('', 'end', 'library', text='Library')
        self.library_tree.insert('', 'end', 'playlist', text='Playlists', open=False)

        self.library_tree.bind('<ButtonRelease-1>', self.on_tree_select)
        self.library_tree.bind('<Double-1>', self.on_tree_double_click)

        self.playlist_menu = tk.Menu(self.root, tearoff=0)
        self.playlist_menu.add_command(label="Open in New Window", command=self.open_playlist_in_new_window)
        self.playlist_menu.add_command(label="Delete Playlist", command=self.delete_playlist)

        self.library_tree.bind("<Button-3>", self.show_playlist_context_menu)

    def populate_song_list(self, playlist_id=None):
        for i in self.song_treeview.get_children():
            self.song_treeview.delete(i)

        connection = create_connection()
        cursor = connection.cursor()
        if playlist_id:
            cursor.execute("SELECT songs.id, title, artist, album, year, genre, comment FROM songs "
                           "JOIN playlist_songs ON songs.id = playlist_songs.song_id WHERE playlist_songs.playlist_id = %s", (playlist_id,))
        else:
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
            cursor.execute("SELECT * FROM songs WHERE title = %s AND artist = %s AND album = %s",
                           (title, artist, album))
            existing_song = cursor.fetchone()
            
            if existing_song:
                song_id = existing_song[0]
            else:
                cursor.execute("INSERT INTO songs (title, artist, album, year, genre, comment, filepath) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (title, artist, album, year, genre, comment, filepath))
                connection.commit()
                song_id = cursor.lastrowid
            
            connection.close()
            self.populate_song_list()
            return song_id

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
        self.stop_song()  # Stop the song if it's playing
        self.current_song_index = None
        messagebox.showinfo("Info", "Song deleted successfully")

    def open_song(self):
        filepath = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if filepath:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self.paused = False

    def show_context_menu(self, event):
        self.populate_playlist_menu()
        self.context_menu.post(event.x_root, event.y_root)

    def populate_playlist_menu(self):
        self.add_to_playlist_menu.delete(0, tk.END)
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        connection.close()
        
        for playlist in playlists:
            self.add_to_playlist_menu.add_command(label=playlist[1], command=lambda p=playlist: self.add_song_to_playlist(p[0]))

    def add_song_to_playlist(self, playlist_id):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

        song_id = self.songs[self.current_song_index][0]

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM playlist_songs WHERE playlist_id = %s AND song_id = %s", (playlist_id, song_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            messagebox.showwarning("Warning", "This song is already in the playlist.")
        else:
            cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)", (playlist_id, song_id))
            connection.commit()
            messagebox.showinfo("Info", "Song added to playlist successfully")

        connection.close()

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for file in files:
            if file.endswith(".mp3"):
                song_id = self.add_song(file)
                if self.current_playlist:
                    self.add_song_to_playlist(self.current_playlist)

    def add_song_to_library_and_playlist(self, filepath, playlist_id=None):
        song_id = self.add_song(filepath)
        if playlist_id:
            self.add_song_to_playlist(playlist_id)

    def on_tree_select(self, event):
        selected_item = self.library_tree.focus()
        if selected_item == "library":
            self.current_playlist = None
            self.populate_song_list()
        elif selected_item.startswith("playlist_"):
            playlist_id = int(selected_item.split("_")[1])
            self.current_playlist = playlist_id
            self.populate_song_list(playlist_id)

    def on_tree_double_click(self, event):
        selected_item = self.library_tree.focus()
        if selected_item == "playlist":
            if self.library_tree.item(selected_item, "open"):
                self.library_tree.item(selected_item, open=False)
            else:
                self.library_tree.item(selected_item, open=True)
        elif selected_item.startswith("playlist_"):
            self.library_tree.selection_set(selected_item)
            self.populate_song_list(int(selected_item.split("_")[1]))

    def create_playlist(self):
        playlist_name = simpledialog.askstring("Create Playlist", "Enter playlist name:")
        if playlist_name:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO playlists (name) VALUES (%s)", (playlist_name,))
            connection.commit()
            playlist_id = cursor.lastrowid
            self.library_tree.insert('playlist', 'end', f'playlist_{playlist_id}', text=playlist_name)
            self.library_tree.selection_set(f'playlist_{playlist_id}')
            self.current_playlist = playlist_id
            self.populate_song_list(playlist_id)
            connection.close()

    def delete_playlist(self):
        selected_item = self.library_tree.focus()
        if not selected_item.startswith("playlist_"):
            return

        playlist_id = int(selected_item.split("_")[1])
        if messagebox.askyesno("Delete Playlist", "Are you sure you want to delete this playlist?"):
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM playlists WHERE id = %s", (playlist_id,))
            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = %s", (playlist_id,))
            connection.commit()
            connection.close()

            self.library_tree.delete(selected_item)
            self.populate_song_list()
            messagebox.showinfo("Info", "Playlist deleted successfully")

    def show_playlist_context_menu(self, event):
        selected_item = self.library_tree.identify_row(event.y)
        if selected_item and selected_item.startswith("playlist_"):
            self.library_tree.selection_set(selected_item)
            self.playlist_menu.post(event.x_root, event.y_root)

    def open_playlist_in_new_window(self):
        selected_item = self.library_tree.focus()
        if not selected_item.startswith("playlist_"):
            return
        
        playlist_id = int(selected_item.split("_")[1])
        new_window = tk.Toplevel(self.root)
        new_app = MyTunesApp(new_window)
        new_app.populate_song_list(playlist_id)

    def set_volume(self, val):
        volume = int(val) / 100
        pygame.mixer.music.set_volume(volume)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MyTunesApp(root)
    root.mainloop()
