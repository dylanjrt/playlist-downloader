import logging
import os

import spotipy
from dotenv import load_dotenv
from pytubefix import Search, YouTube
from pytubefix.cli import on_progress
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
logging.basicConfig(level=logging.INFO)


def get_spotify_playlist_tracks(sp, playlist_id):
    """
    Retrieve all tracks from a Spotify playlist.

    Parameters
    ----------
    sp : spotipy.Spotify
        An authenticated Spotify client.
    playlist_id : str
        The Spotify ID of the playlist.

    Returns
    -------
    list of dict
        A list of dictionaries containing track details such as name, artist, and bpm.
    """
    results = sp.playlist_tracks(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    playlist_tracks = []
    for track in tracks:
        track_id = track["track"]["id"]
        audio_features = sp.audio_features(track_id)[0]
        bpm = audio_features["tempo"]
        track_details = {
            "name": f"{track['track']['name']}",
            "artist": track["track"]["artists"][0]["name"],
            "bpm": bpm,
        }
        playlist_tracks.append(track_details)

    return playlist_tracks


def get_playlist_title(sp, playlist_id):
    """
    Retrieve the title of a Spotify playlist.

    Parameters
    ----------
    sp : spotipy.Spotify
        An authenticated Spotify client.
    playlist_id : str
        The Spotify ID of the playlist.

    Returns
    -------
    str
        The title of the playlist.
    """
    playlist = sp.playlist(playlist_id)
    playlist_title = playlist["name"]
    return playlist_title


def download_song_from_youtube(song_name, artist_name, output_path, song_bpm):
    """
    Download a song from YouTube.

    Parameters
    ----------
    song_name : str
        The name of the song.
    artist_name : str
        The name of the artist.
    output_dir : str
        The directory to save the downloaded song.
    song_bpm : float
        The BPM (beats per minute) of the song.

    Raises
    ------
    Exception
        If there is an error during the download process.
    """
    search_results = Search(f"{song_name} {artist_name}").videos
    if search_results:
        video_url = search_results[0].watch_url
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)
            ys = yt.streams.get_audio_only()
            logging.info("Downloading: %s - %s", song_name, artist_name)
            ys.download(
                mp3=True,
                output_path=output_path,
                filename=f"{song_bpm} BPM — {song_name} - {artist_name}",
            )
        except Exception as ex:
            raise f"Exception on song: {song_name}: {ex}"


def download_playlist_from_spotify(playlist_id, client_id, client_secret, output_dir):
    """
    Download all tracks from a Spotify playlist and save them to a specified directory.

    Parameters
    ----------
    playlist_id : str
        The Spotify ID of the playlist.
    client_id : str
        The Spotify client ID.
    client_secret : str
        The Spotify client secret.
    """
    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    playlist_tracks = get_spotify_playlist_tracks(sp, playlist_id)

    playlist_title = get_playlist_title(sp, playlist_id)
    output_path = os.path.join(output_dir, playlist_title)
    os.makedirs(output_path, exist_ok=True)

    for track in playlist_tracks:
        song_name = track["name"]
        artist_name = track["artist"]
        song_bpm = track["bpm"]
        try:
            download_song_from_youtube(song_name, artist_name, output_path, song_bpm)
        except Exception as ex:
            print(f"Exception on song: {song_name} - {ex}")
            continue

    logging.info("Playlist download finished.")


def convert_link_to_id(link):
    """
    Convert a Spotify playlist link to its ID.

    Parameters
    ----------
    link : str
        The Spotify playlist link.

    Returns
    -------
    str
        The Spotify playlist ID.
    """
    return link.split("/")[4].split("?")[0]


def main():
    """
    Main function to download a Spotify playlist.
    """
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    output_dir = os.environ.get("OUTPUT_DIR")

    playlist_link = input("Enter the spotify playlist link: ")
    playlist_id = convert_link_to_id(playlist_link)

    download_playlist_from_spotify(playlist_id, client_id, client_secret, output_dir)


if __name__ == "__main__":
    main()
