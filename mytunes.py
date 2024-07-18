import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
from mutagen.easyid3 import EasyID3 
import mysql.connector 
import os

# Initialize Pygame mixer
pygame.mixer.init()

# Establish MySQL database connection
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
        
        self.current_song_index = None
        self.paused = False

        self.create_widgets()
        self.populate_song_list()

    def create_widgets(self):
        # Create frames for layout
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(fill=tk.BOTH, expand=True)

        self.frame_bottom = tk.Frame(self.root)
        self.frame_bottom.pack(side=tk.BOTTOM)

        # Listbox to display songs
        self.song_listbox = tk.Listbox(self.frame_top, selectmode=tk.SINGLE)
        self.song_listbox.pack(fill=tk.BOTH, expand=True)
        self.song_listbox.bind('<<ListboxSelect>>', self.on_song_select)
        
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

        self.btn_add = tk.Button(self.frame_bottom, text="Add", command=self.add_song)
        self.btn_add.pack(side=tk.LEFT)

        self.btn_delete = tk.Button(self.frame_bottom, text="Delete", command=self.delete_song)
        self.btn_delete.pack(side=tk.LEFT)

        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Add Song", command=self.add_song)
        self.context_menu.add_command(label="Delete Song", command=self.delete_song)
        self.song_listbox.bind("<Button-3>", self.show_context_menu)

    def populate_song_list(self):
        self.song_listbox.delete(0, tk.END)
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT title, artist FROM songs")
        for (title, artist) in cursor:
            self.song_listbox.insert(tk.END, f"{title} - {artist}")
        connection.close()

    def on_song_select(self, event):
        selection = self.song_listbox.curselection()
        if selection:
            self.current_song_index = selection[0]

    def play_song(self):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT filepath FROM songs LIMIT %s, 1", (self.current_song_index,))
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
            self.current_song_index = (self.current_song_index + 1) % self.song_listbox.size()
            self.song_listbox.selection_clear(0, tk.END)
            self.song_listbox.selection_set(self.current_song_index)
            self.play_song()

    def prev_song(self):
        if self.current_song_index is not None:
            self.current_song_index = (self.current_song_index - 1) % self.song_listbox.size()
            self.song_listbox.selection_clear(0, tk.END)
            self.song_listbox.selection_set(self.current_song_index)
            self.play_song()

    def add_song(self):
        filepath = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if filepath:
            audio = EasyID3(filepath)
            title = audio.get("title", ["Unknown Title"])[0]
            artist = audio.get("artist", ["Unknown Artist"])[0]
            album = audio.get("album", ["Unknown Album"])[0]
            year = audio.get("date", ["Unknown Year"])[0]
            genre = audio.get("genre", ["Unknown Genre"])[0]

            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO songs (title, artist, album, year, genre, filepath) VALUES (%s, %s, %s, %s, %s, %s)",
                           (title, artist, album, year, genre, filepath))
            connection.commit()
            connection.close()
            
            self.populate_song_list()
            messagebox.showinfo("Info", "Song added successfully")

    def delete_song(self):
        if self.current_song_index is None:
            messagebox.showwarning("Warning", "No song selected")
            return

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM songs LIMIT %s, 1", (self.current_song_index,))
        connection.commit()
        connection.close()
        
        self.populate_song_list()
        self.current_song_index = None
        messagebox.showinfo("Info", "Song deleted successfully")

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    root = tk.Tk()
    app = MyTunesApp(root)
    root.mainloop()
