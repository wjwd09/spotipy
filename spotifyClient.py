import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import soundcloud
import os
import json

#Eventually move these global variables into threaded_client and pass them into constructor
SCOPE = "user-read-playback-state user-modify-playback-state"
CLIENT_ID = "cc9859af7bda4fea8c2e74321becb949"
REDIRECT_URI = "http://localhost:8888/callback"

class spotifyClient:

    def __init__(self, clientID, redirect_uri, scope):
        self.clientID = CLIENT_ID
        self.redirect_uri = REDIRECT_URI
        self.scope = SCOPE
        self.spAuth = None
        self.accToken = None


    def authorizationSetup(self):
        self.spAuth = spotipy.SpotifyPKCE(self.clientID, self.redirect_uri, self.scope, open_browser=True)
        self.accToken = self.spAuth.get_access_token(code=self.spAuth.get_authorization_code(),check_cache=False)
        
    def getAuthCode(self):
        return self.spAuth.get_authorization_code()

    def getAccToken(self, authCode):
        return self.spAuth.get_access_token(code=authCode, check_cache=False)

