import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import soundcloud
import os
import json
import time

#track = "spotify:track:7GhIk7Il098yCjg4BQjzvb"
accToken = input("Enter access token:")
sp = spotipy.Spotify(auth=accToken)
#current_song = sp.currently_playing()['item']['name']
#current_artist = sp.currently_playing()['item']['album']['artists'][0]['name']
current_song = ""
current_artist = ""

def toggle_playback():
    '''
    Toggles the playback mode between playing and paused.
    Inputs: none
    Returns: none
    '''
    if sp.current_playback()['is_playing']:
        sp.pause_playback()
        print("Paused")
    else:
        sp.start_playback()
        print("Now playing: " + sp.currently_playing()['item']['name'] + " by " + sp.currently_playing()['item']['album']['artists'][0]['name'])

# Spotify Functions

def add_to_queue(song):
    sp.add_to_queue(song)

def previous_track():
    sp.previous_track()
    time.sleep(1)
    print("Now playing: " + sp.currently_playing()['item']['name'] + " by " + sp.currently_playing()['item']['album']['artists'][0]['name'])

def next_track():
    sp.next_track()
    time.sleep(1)
    print("Now playing: " + sp.currently_playing()['item']['name'] + " by " + sp.currently_playing()['item']['album']['artists'][0]['name'])

while True:
    cmd = input("Enter 1 for pause/play, 2 for skip, 3 for previous track, 4 to quit\n")
    if cmd == "1":
        toggle_playback()
    elif cmd == "2":
        next_track()
    elif cmd == "3":
        previous_track()
    elif cmd == "4":
        break