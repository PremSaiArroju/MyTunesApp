import tkinter as tk
from tkinter import filedialog, messagebox, Menu
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
    def __init__(self, root):
        self.root = root
        self.root.title("MyTunes")

        self.root.minsize(700, 300)
        
        self.current_song_index = None
        self.paused = False
        self.editing_comment = False
        self.comment_entry = None

        self.create_widgets()
        self.populate_song_list()

    def create_widgets(self):
        # Create a style
        style = ttk.Style()
        style.configure("Treeview.Heading", borderwidth=1, relief="solid")
        style.configure("Treeview", borderwidth=1, relief="solid")
        style.map('Treeview', background=[('selected', 'lightblue')])

        # Create frames for layout
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        self.frame_bottom = tk.Frame(self.root)
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
        self.song_treeview.bind('<Double-1>', self.on_double_click)

        # Enable drag and drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # Frame to center the buttons
        self.button_frame = tk.Frame(self.frame_bottom)
        self.button_frame.pack(expand=True)

        # Buttons for control
        self.btn_play = tk.Button(self.button_frame, text="Play", command=self.play_song)
        self.btn_play.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop = tk.Button(self.button_frame, text="Stop", command=self.stop_song)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_pause = tk.Button(self.button_frame, text="Pause", command=self.pause_song)
        self.btn_pause.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_unpause = tk.Button(self.button_frame, text="Unpause", command=self.unpause_song)
        self.btn_unpause.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_next = tk.Button(self.button_frame, text="Next", command=self.next_song)
        self.btn_next.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_prev = tk.Button(self.button_frame, text="Prev", command=self.prev_song)
        self.btn_prev.pack(side=tk.LEFT, padx=5, pady=5)

        # Add/Delete buttons
        self.btn_add = tk.Button(self.button_frame, text="Add", command=self.add_song)
        self.btn_add.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_delete = tk.Button(self.button_frame, text="Delete", command=self.delete_song)
        self.btn_delete.pack(side=tk.LEFT, padx=5, pady=5)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Song", command=self.add_song)
        self.context_menu.add_command(label="Delete Song", command=self.delete_song)
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
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

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
            cursor.execute("SELECT * FROM songs WHERE title = %s AND artist = %s AND album = %s",
                           (title, artist, album))
            existing_song = cursor.fetchone()
            
            if existing_song:
                messagebox.showwarning("Warning", "This song is already in the library.")
            else:
                cursor.execute("INSERT INTO songs (title, artist, album, year, genre, comment, filepath) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (title, artist, album, year, genre, comment, filepath))
                connection.commit()
                messagebox.showinfo("Info", "Song added successfully")
            
            connection.close()
            self.populate_song_list()

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
        self.context_menu.post(event.x_root, event.y_root)

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for file in files:
            if file.endswith(".mp3"):
                self.add_song(file)

    def on_double_click(self, event):
        item = self.song_treeview.selection()
        if not item:
            return
        
        column = self.song_treeview.identify_column(event.x)
        row = self.song_treeview.identify_row(event.y)
        if column == '#6':  # Comment column
            item_values = self.song_treeview.item(item, "values")
            comment = item_values[5] if len(item_values) > 5 else ""
            
            if not self.editing_comment:
                self.editing_comment = True
                x, y, width, height = self.song_treeview.bbox(item, column)
                self.comment_entry = tk.Entry(self.song_treeview)
                self.comment_entry.place(x=x, y=y, width=width, height=height)
                self.comment_entry.insert(0, comment)
                self.comment_entry.bind("<Return>", lambda e: self.save_comment(item))
                self.comment_entry.bind("<FocusOut>", lambda e: self.save_comment(item))
                self.comment_entry.focus()

    def save_comment(self, item):
        new_comment = self.comment_entry.get()
        song_id = self.songs[self.current_song_index][0]

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE songs SET comment = %s WHERE id = %s", (new_comment, song_id))
        connection.commit()
        connection.close()

        self.song_treeview.item(item, values=(
            self.song_treeview.set(item, 'Title'),
            self.song_treeview.set(item, 'Artist'),
            self.song_treeview.set(item, 'Album'),
            self.song_treeview.set(item, 'Year'),
            self.song_treeview.set(item, 'Genre'),
            new_comment
        ))

        self.comment_entry.destroy()
        self.comment_entry = None
        self.editing_comment = False

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MyTunesApp(root)
    root.mainloop()
