import spotipy
import spotipy.util as util
import os
# from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(requests_session=False)


def my_albums():
    """takes the current user and returns a list with all of it's albums"""
    albums = sp.current_user_saved_albums(limit=50, offset=0)  # i have albums 20 - 69
    album_index = 0
    offset = 0
    while album_index < albums['total']:
        if album_index < (len(albums['items']) + offset):
            print(albums['items'][album_index - offset]['album']['artists'][0]['name'], "-",
                  albums['items'][album_index - offset]['album']['name'])
            album_index += 1
        else:
            offset = album_index
            albums = sp.current_user_saved_albums(limit=50, offset=offset)


def my_playlist(user_id):
    """
    takes the current user and returns a list with all of its playlists
    :return: a list of tuples:
            (playlist_title, playlist_id)
    """
    # playlists = sp.current_user_playlists(limit=50, offset=0)
    playlists = sp.user_playlists(user_id, limit=50, offset=0)
    playlist_index = 0
    offset = 0
    result_list = []
    while playlist_index < playlists['total']:
        if playlist_index < len(playlists['items']) + offset:
            result_list.append((playlists["items"][playlist_index - offset]['name'],
                               playlists["items"][playlist_index - offset]["id"]))
            playlist_index += 1
        else:
            offset = playlist_index
            playlists = sp.user_playlists(user_id, limit=50, offset=offset)
    return result_list


def create_playlist(user_id, title, description=""):
    """
    creates a new playlist if no existing playlist with the same title.
    returns the id of the chosen playlist (new or existing).
    :param user_id: id of the user to add/find a playlist
    :param title: title for the playlist
    :param description: (optional), a description for a new playlist
    :return: returns the id of the chosen playlist (new or existing)
    """
    for playlist_name, playlist_id in my_playlist(user_id):
        if title == playlist_name:
            return playlist_id
    playlist = sp.user_playlist_create(user_id, title, description=description)
    return playlist['id']


def album_search(q, limit=10):
    """
    search for an album title
    :param q: the query text of the album
    :param limit: number of results to display. default to display is 10
    :return: a list of tuples:
            (album_title, artists list, album_id)
    """
    results = sp.search(q, type='album', limit=limit)
    result_list = []
    artist_list = []
    for i in range(0, len(results['albums']['items'])):
        for j in range(0, len(results['albums']['items'][i]['artists'])):
            artist_list.append(results['albums']['items'][i]['artists'][j]['name'])
        result_list.append((results['albums']['items'][i]['name'],
                            artist_list,
                            results['albums']['items'][i]['id']))   # TODO id or uri
        artist_list = []
    return result_list


def track_search(q, limit=10):
    """
    search for a track
    :param q: the query text of the track
    :param limit: number of results to display. default to display is 10
    :return: a list of tuples:
            (track_title, artists list, track_id (as a list), album_title)
    """
    results = sp.search(q, type='track', limit=limit)
    result_list = []
    artist_list = []
    for i in range(0, len(results['tracks']['items'])):
        for j in range(0, len(results['tracks']['items'][i]['artists'])):
            artist_list.append(results['tracks']['items'][i]['artists'][j]['name'])
        result_list.append((results['tracks']['items'][i]['name'],
                            artist_list,
                            [results['tracks']['items'][i]['id']],     # TODO id or uri
                            results['tracks']['items'][i]['album']['name']))
        artist_list = []
    return result_list


def add_track(user_id, playlist_id, track_id):
    """
    add a track to a desired playlist. will add only if the track is not in the playlist already
    :param user_id: the user account of the playlist
    :param playlist_id: the desired play list
    :param track_id: the track to add
    :return: ---
    """
    playlist_tracks = sp.playlist_tracks(playlist_id, fields='items')
    if track_id in [playlist_tracks['items'][i]['track']["id"] for i in range(0, len(playlist_tracks["items"]))]:
        pass
    else:
        sp.user_playlist_add_tracks(user=user_id, playlist_id=playlist_id, tracks=track_id)


def spotify_connect(user_name, scope):
    """
    connect to the spotify api for the "Music Sync" app

    :param user_name: the user name for the current connection
    :param scope: the scope of permissions for this connection
    :return: the user's user_id that you can excess with this connection
    """
    global sp
    try:
        token = util.prompt_for_user_token(user_name,
                                           scope=scope,
                                           client_id='7c3a5882652d44a1be1a857f286bc988',
                                           client_secret='33a1d239e0224e1d85b375800ef0b4a4',
                                           redirect_uri='http://localhost:8888/callback')
    except (AttributeError, spotipy.oauth2.SpotifyOauthError):
        os.remove(f".cache-{user_name}")
        token = util.prompt_for_user_token(user_name,
                                           scope=scope,
                                           client_id='7c3a5882652d44a1be1a857f286bc988',
                                           client_secret='33a1d239e0224e1d85b375800ef0b4a4',
                                           redirect_uri='http://localhost:8888/callback')

    sp = spotipy.Spotify(auth=token, requests_session=True)
    user_id = sp.current_user()
    print(user_id['display_name'])
    
    return user_id['id']


if __name__ == '__main__':

    # creating a connection to the spotify app
    scope_ = 'user-library-read playlist-modify-public playlist-modify-private'
    """
    the playlist-modify-public/playlist-modify-private scope:
    
    Follow a Playlist
    Unfollow a Playlist
    Add Tracks to a Playlist
    Change a Playlist's Details
    Create a Playlist
    Remove Tracks from a Playlist
    Reorder a Playlist's Tracks
    Replace a Playlist's Tracks
    Upload a Custom Playlist Cover Image
    """

    # token = util.prompt_for_user_token('pavel',
    #                                    scope,
    #                                    client_id='7c3a5882652d44a1be1a857f286bc988',
    #                                    client_secret='33a1d239e0224e1d85b375800ef0b4a4',
    #                                    redirect_uri='http://localhost:8888/callback')
    # sp = spotipy.Spotify(auth=token)

    # user2 = sp.user('21rvbfcgfb4sy7lsubpleobmq')
    # spotify_connect("menahem", scope_)
    print(sp.current_user())

