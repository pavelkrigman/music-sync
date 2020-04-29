import os
import fnmatch
import spotify
import id3reader_p3 as id3reader
try:
    import tkinter
    from tkinter import filedialog
except ImportError:    # python 2
    import Tkinter as tkinter
    import tkFileDialog as filedialog
from tkinter import ttk

# TODO handle token expired?
# TODO handle different languages
# ============ Global Variables =================
scope = 'playlist-modify-public playlist-modify-private'
spotify_user_id = ""
track_list_id = []
track_artist = []
playlist_list_id = []
chosen_track_id = ""
chosen_playlist_id = ""
track_title_list = []


class Scrollbox(tkinter.Listbox):

    def __init__(self, window, **kwargs):
        super().__init__(window, **kwargs)

        self.scrollbar = tkinter.Scrollbar(window, orient=tkinter.VERTICAL, command=self.yview)

    def grid(self, row, column, sticky='nsw', rowspan=1, columnspan=1, **kwargs):
        super().grid(row=row, column=column, sticky=sticky, rowspan=rowspan, columnspan=columnspan, **kwargs)
        self.scrollbar.grid(row=row, column=column, sticky='nse', rowspan=rowspan)
        self['yscrollcommand'] = self.scrollbar.set


def choose_directory():
    """displays all of the mp3 files in a chosen local directory"""
    title_text.config(text="")
    artist_text.config(text="")
    searchLV.set(("Choose a track",))
    rep = filedialog.askdirectory()
    trackLV.set(tuple(full_file(rep, "mp3")))


def full_file(root, extension="mp3"):
    """
    search for all the files in a chosen directory and file extension
    will try to display the title from the mp3 properties.
    :param root: the path of a directory to search for files
    :param extension: type of files needed (default - mp3)
    :return: returns a list of all the files (from a specific type) in the selected directory
    """
    global track_title_list
    file_errors = []
    track_title_list = []
    for path, directories, files in os.walk(root):  # TODO if there sub directories, search inside as well
        for file in fnmatch.filter(files, "*" + extension):
            try:
                id3r = id3reader.Reader(root + "/" + file)
                if id3r.get_value('title') is None or "":
                    track_title_list.append(file.strip("mp3"))
                else:
                    track_title_list.append(id3r.get_value('title'))
            except OSError:
                file_errors.append(file)
    return track_title_list


def search_track(event):
    """
    search a track in spotify when a track is chosen from the Files listbox
    and display the results in the results listbox
    """
    lb = event.widget
    global track_artist
    global track_list_id
    global chosen_track_id
    if lb.curselection():
        track_artist = []
        track_list_id = []
        index = lb.curselection()[0]
        track_title = lb.get(index)

        # search for the track in spotify
        result = spotify.track_search(track_title, 20)
        if not result:
            searchLV.set(("No results found", "please edit the title", "or", "try a different track"))
        else:
            # (track_title, artists list, track_id (as a list), album_title)
            a_list = []
            for song in range(0, len(result)):
                title, artist_list, track_id, _ = result[song]
                a_list.append(title)
                track_list_id.append(track_id)
                track_artist.append(artist_list)
            title_text.config(text=a_list[0])
            artist_text.config(text="\n".join(track_artist[0]))
            chosen_track_id = track_list_id[0]
            searchLV.set(tuple(a_list))  # TODO try to search track title and artist


def show_details(event):
    """show the title and artists of a selected track"""
    lb = event.widget
    global chosen_track_id
    if lb.curselection():
        index = lb.curselection()[0]
        track_title = lb.get(index)
        title_text.config(text=track_title)
        artist_text.config(text="\n".join(track_artist[index]))
        chosen_track_id = track_list_id[index]


def show_playlists():
    """shows the playlists of the current user"""
    global playlist_list_id
    playlist_list_id = []

    a_list = []
    result = spotify.my_playlist(spotify_user_id)
    for playlist_name, playlist_id in result:
        a_list.append(playlist_name)
        playlist_list_id.append(playlist_id)
    playlistLV.set(tuple(a_list))


def choose_playlist(event):
    """retrieve the id of the chosen playlist and display the title"""
    global chosen_playlist_id
    lb = event.widget
    if lb.curselection():
        index = lb.curselection()[0]
        playlist_title = lb.get(index)
        chosen_playlist_id = playlist_list_id[index]
        playlist_text_details.config(text=playlist_title)


def create_playlist():
    """create a new playlist if there is no playlist with the same name"""
    global chosen_playlist_id
    playlist_title = playlist_text.get()
    if playlist_title == "":
        status_window("Enter a playlist title")
    else:
        chosen_playlist_id = spotify.create_playlist(spotify_user_id, playlist_title)
        playlist_text_details.config(text=playlist_title)
        status_window("Playlist created")
        playlist_text.delete(0, tkinter.END)


def add_track_to_playlist():
    """
    add a track to a chosen playlist and inform the user about the action
    if added successfully, will clear the track title and artist details
    and will un-choose it's ID
    """
    global chosen_track_id
    if spotify_user_id == "" or chosen_track_id == "" or chosen_playlist_id == "":
        status_text = "Something is missing"
    else:
        spotify.add_track(spotify_user_id, chosen_playlist_id, chosen_track_id)
        status_text = "Added successfully"
        chosen_track_id = ""
        title_text.config(text="")
        artist_text.config(text="")

    status_window(status_text)


def add_all_to_playlist():
    """
    adds all of the tracks from the chosen folder to some playlist.
    will automatically add the first result from the title search in spotify.
    **** USE AT YOUR OWN RISK ****
    """
    not_found_list = []
    if chosen_playlist_id:
        for track in track_title_list:
            result = spotify.track_search(track, 1)
            if not result:
                not_found_list.append(track)
                # searchLV.set(("No results found", "please edit the title", "or", "try a different track"))
            else:
                # (track_title, artists list, track_id (as a list), album_title)
                _, _, track_id, _ = result[0]
                spotify.add_track(spotify_user_id, chosen_playlist_id, track_id)
        if not not_found_list:
            status_window("All tracks were added")
        else:
            print(not_found_list)
            status_window("No results found for \n 1 or more tracks")
    else:
        status_window("Please Choose A Playlist")


def connect():
    """makes the connection to the spotify API and gets the connected user_id"""
    global spotify_user_id
    spotify_user_id = spotify.spotify_connect(login_text.get(), scope)
    login_win.destroy()
    show_playlists()


def status_window(msg):
    status_win = tkinter.Toplevel(bd=6, relief='groove')
    status_win.geometry("200x150")
    status_win.lift(main_window)
    status_win.transient(main_window)
    status_win.overrideredirect(True)

    msg_status = ttk.Label(status_win, text=msg)
    msg_status.grid(sticky='we')

    ok_button = ttk.Button(status_win, text="Close")
    ok_button.grid(sticky='we')
    ok_button.config(command=status_win.destroy)
    # center window, text and button
    center_window(status_win)

    text_size = [atr.split('x') for atr in msg_status.winfo_geometry().split('+')]
    pad_text = (200 - int(text_size[0][0])) // 2
    msg_status.grid(padx=(pad_text - 3, 0), pady=(20, 0))

    text_size = [atr.split('x') for atr in ok_button.winfo_geometry().split('+')]
    pad_text = (200 - int(text_size[0][0])) // 2
    ok_button.grid(sticky='we', padx=(pad_text - 3, 0), pady=(20, 0))


def center_window(window):
    """
    centers a new window, relative to the main_window
    :param window: the new window to center
    """
    window.update_idletasks()
    main_window.update_idletasks()
    new_size = [atr.split('x') for atr in window.geometry().split('+')]
    main_size = [atr.split('x') for atr in main_window.geometry().split('+')]
    x = int(main_size[0][0]) // 2 - int(new_size[0][0]) // 2 + int(main_size[1][0])
    y = int(main_size[0][1]) // 2 - int(new_size[0][1]) // 2 + int(main_size[2][0])
    window.geometry("{}x{}+{}+{}".format(int(new_size[0][0]), int(new_size[0][1]), x, y))


main_window = tkinter.Tk()
main_window.title("Music Sync")
main_window.geometry('1000x600+26+26')

main_window.columnconfigure(0, weight=2)
main_window.columnconfigure(1, weight=2)
main_window.columnconfigure(2, weight=2)
main_window.columnconfigure(3, weight=4)
main_window.columnconfigure(4, weight=1)

main_window.rowconfigure(0, weight=1)
main_window.rowconfigure(1, weight=1)
main_window.rowconfigure(2, weight=1)
main_window.rowconfigure(3, weight=1)
main_window.rowconfigure(4, weight=1)
main_window.rowconfigure(5, weight=1)
main_window.rowconfigure(6, weight=1)
main_window.rowconfigure(7, weight=1)

# ============== labels ===================
tkinter.Label(main_window, text="Files:").grid(row=0, column=0, sticky='ws', padx=(30, 0))
tkinter.Label(main_window, text="Search Results:").grid(row=0, column=1, sticky='ws', padx=(30, 0))
tkinter.Label(main_window, text="Your Playlists:").grid(row=0, column=2, sticky='ws', padx=(30, 0))
tkinter.Label(main_window, text="Title:").grid(row=0, column=3, sticky='ws', padx=(15, 0))
tkinter.Label(main_window, text="Artists:").grid(row=2, column=3, sticky='ws', padx=(15, 0))
tkinter.Label(main_window, text="Playlist:").grid(row=4, column=3, sticky='ws', padx=(15, 0))

# ============== File Browser ===================
trackLV = tkinter.Variable(main_window)
trackLV.set(("Choose a folder",))
track_list = Scrollbox(main_window, listvariable=trackLV)
track_list.grid(row=1, column=0, sticky='nsew', rowspan=4, padx=(30, 0))
track_list.config(relief="sunken", border=2)

track_list.bind('<<ListboxSelect>>', search_track)

# ============== Search Results ===================
searchLV = tkinter.Variable(main_window)
searchLV.set(("Choose a track",))
search_list = Scrollbox(main_window, listvariable=searchLV)
search_list.grid(row=1, column=1, sticky='nsew', rowspan=4, padx=(30, 0))
search_list.config(relief="sunken", border=2)

search_list.bind('<<ListboxSelect>>', show_details)

# ============== Playlists ===================
playlistLV = tkinter.Variable(main_window)
playlistLV.set(("Choose a playlist",))
playlist_list = Scrollbox(main_window, listvariable=playlistLV)
playlist_list.grid(row=1, column=2, sticky='nsew', rowspan=4, padx=(30, 0))
playlist_list.config(relief="sunken", border=2)

playlist_list.bind('<<ListboxSelect>>', choose_playlist)

# ============== track details ===================
title_text = ttk.Label(main_window)
title_text.grid(row=1, column=3, sticky="we", padx=(15, 0))
title_text.config(relief='solid', background='white', width=20, wraplength=150)

artist_text = ttk.Label(main_window)
artist_text.grid(row=3, column=3, sticky="we", padx=(15, 0))
artist_text.config(relief='solid', background='white')

playlist_text_details = ttk.Label(main_window)
playlist_text_details.grid(row=5, column=3, sticky="we", padx=(15, 0))
playlist_text_details.config(relief='solid', background='white')

# ============== Browse directories ===================
search_button = ttk.Button(main_window, text="Browse", command=choose_directory)
search_button.grid(row=5, column=0, sticky='w', padx=(30, 0))

# # ============== load results ===================
# load_button = tkinter.Button(main_window, text="Load More")
# load_button.grid(row=5, column=1, sticky='w', padx=(30, 0))

# ============== playlist_buttons ===================
playlist_search_button = ttk.Button(main_window, text="Update Playlists")
playlist_search_button.grid(row=5, column=2, sticky='w', padx=(30, 0))
playlist_search_button.config(command=show_playlists)
playlist_text = ttk.Entry(main_window)
playlist_text.grid(row=6, column=2, sticky='wes', padx=(30, 0))
playlist_new_buttons = ttk.Button(main_window, text="Create New")
playlist_new_buttons.grid(row=7, column=2, sticky='wn', padx=(30, 0))
playlist_new_buttons.config(command=create_playlist)

# ============== add buttons ===================
add_track_button = ttk.Button(main_window, text='Add Track')
add_track_button.grid(row=6, column=3)
add_track_button.config(command=add_track_to_playlist)

add_all_button = ttk.Button(main_window, text='Add All')
add_all_button.grid(row=5, column=0, sticky='e', padx=(0, 15))
add_all_button.config(command=add_all_to_playlist)

# ============== exit ===================
exit_button = ttk.Button(main_window, text="EXIT")
exit_button.grid(row=7, column=3, sticky='e')
exit_button.config(command=main_window.destroy)

# ============== login window ===================
login_win = tkinter.Toplevel(bd=6, relief='groove')
ttk.Label(login_win, text="Please Login").grid(sticky='we', padx=(62, 0), pady=(10, 0))
login_win.geometry("200x150")
center_window(login_win)
login_win.lift(main_window)
login_win.transient(main_window)
login_win.overrideredirect(True)

login_text = ttk.Entry(login_win)
login_text.grid(row=1, column=0, sticky='we', padx=(35, 0), pady=(15, 20))

login_button = ttk.Button(login_win, text="Login")
login_button.grid(row=3, column=0, padx=(35, 0))
login_button.config(command=connect)

# ============== main loop ===================

main_window.mainloop()
