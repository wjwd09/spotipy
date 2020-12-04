import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import soundcloud
import os
import json
import time

#track = "spotify:track:7GhIk7Il098yCjg4BQjzvb"

#current_song = sp.currently_playing()['item']['name']
#current_artist = sp.currently_playing()['item']['album']['artists'][0]['name']
current_song = ""
current_artist = ""

class spotifyServer:

    def __init__(self, accToken, accTokenDict):
        '''
        Initializes server and creates spotify player (sp)
        Inputs: accToken or accTokenDict (ideally just accTokenDict, but accToken is there for testing)
        Returns: none
        '''
        
        self.accTokenDict = accTokenDict
        if accTokenDict:
            self.accToken = accTokenDict["access_token"]
        else:
            self.accToken = accToken
        self.sp = spotipy.Spotify(auth=self.accToken)

    def toggle_playback(self):
        '''
        Toggles the playback mode between playing and paused.
        Inputs: none
        Returns: none
        '''
        try:
            if self.sp.current_playback()['is_playing']:
                self.sp.pause_playback()
                print("Paused")
            else:
                self.sp.start_playback()
                print("Now playing: " + self.sp.currently_playing()['item']['name'] + " by " + self.sp.currently_playing()['item']['album']['artists'][0]['name'])
            return True
        except:
            return False

    def is_spotify_running(self):
        running = self.sp.current_playback()
        if running == None:
            return False
        else:
            return True

    # Spotify Functions

    def add_to_queue(self, uri):
        self.sp.add_to_queue(uri)

    def previous_track(self):
        self.sp.previous_track()
        time.sleep(1)
        print("Now playing: " + self.sp.currently_playing()['item']['name'] + " by " + self.sp.currently_playing()['item']['album']['artists'][0]['name'])

    def next_track(self):
        self.sp.next_track()
        time.sleep(1)
        print("Now playing: " + self.sp.currently_playing()['item']['name'] + " by " + self.sp.currently_playing()['item']['album']['artists'][0]['name'])

    def search(self, song):
        results = self.sp.search(q=song, limit=10, offset=0, type='track')
        if results:
            refResults = {}
            for entry in results['tracks']['items']:
                refResults[entry['name']] = {
                    'artist':   entry['artists'][0]['name'],
                    'uri'   :   entry['uri']  
                }
            return refResults
        else:
            return None

    def play_track(self, uriList):
        self.sp.start_playback(uris=uriList)

#These lines are for testing, will need to get access token from running spotifyClient.py and input here
token = input("Enter access token:\n")
server = spotifyServer(accToken=token, accTokenDict=None)

while True:
        cmd = input("Enter 1 for pause/play, 2 for skip, 3 for previous track, 4 to quit\n")
        if cmd == "1":
            server.toggle_playback()
        elif cmd == "2":
            server.next_track()
        elif cmd == "3":
            server.previous_track()
        elif cmd == "4":
            break
        elif cmd == "5":
            song = input("Enter track to search\n")
            print(server.search(song))
        elif cmd == "6":
            uri = [1]
            uri[0] = input("Enter song uri to play\n")
            server.play_track(uri)

