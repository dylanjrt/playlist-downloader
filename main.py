import os

import spotipy
from dotenv import load_dotenv
from pytubefix import Search, YouTube
from pytubefix.cli import on_progress
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()


def get_spotify_playlist_tracks(sp, playlist_id):
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
    playlist = sp.playlist(playlist_id)
    playlist_title = playlist["name"]
    return playlist_title


def download_song_from_youtube(song_name, artist_name, output_dir, song_bpm):
    search_results = Search(f"{song_name} {artist_name}").videos
    if search_results:
        video_url = search_results[0].watch_url
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)
            print(yt.title)
            ys = yt.streams.get_audio_only()
            print(f"Downloading: {song_name} - {artist_name}")
            ys.download(
                mp3=True,
                output_path=output_dir,
                filename=f"{song_bpm} BPM — {song_name} - {artist_name}",
            )
        except Exception as ex:
            print(ex)
            return


def download_playlist_from_spotify(playlist_id, client_id, client_secret):
    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    playlist_tracks = get_spotify_playlist_tracks(sp, playlist_id)

    playlist_title = get_playlist_title(sp, playlist_id)
    download_dir = f"/Users/dylan/Desktop/mixing/{playlist_title}"
    os.makedirs(download_dir, exist_ok=True)

    for track in playlist_tracks:
        song_name = track["name"]
        artist_name = track["artist"]
        song_bpm = track["bpm"]
        try:
            download_song_from_youtube(song_name, artist_name, download_dir, song_bpm)
        except Exception as ex:
            print(f"Exception on song: {song_name} - {ex}")
            continue

    print("Playlist download finished.")


def convert_link_to_id(link):
    return link.split("/")[4].split("?")[0]


def main():
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    playlist_link = input("Enter the Spotify playlist link: ")
    playlist_id = convert_link_to_id(playlist_link)
    download_playlist_from_spotify(playlist_id, client_id, client_secret)


if __name__ == "__main__":
    main()
