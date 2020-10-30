import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import soundcloud
import os
import json

#---- Globals are temporary for testing purposes, will be kept in threaded_client.py---
SCOPE = "user-read-playback-state user-modify-playback-state"
CLIENT_ID = "cc9859af7bda4fea8c2e74321becb949"
REDIRECT_URI = "http://localhost:8888/callback"

class spotifyClient:

    def __init__(self, clientID, redirect_uri, scope):
        '''
        Initializes client
        Inputs: dev clientID, redirect_uri, and scope  
        (these are all defined globally here and in threaded_client.py)
        Returns: none
        '''
        self.clientID = clientID
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.spAuth = None
        self.accTokenDict = None
        self.authCode = None
        self.accToken = None


    def authSetup(self):
        '''
        Creates spotipy auth flow object and opens authentication link for user.
        Grabs authentication code after user accepts, and then grabs access token with auth code.
        Inputs: none
        Returns: none
        '''
        self.spAuth = spotipy.SpotifyPKCE(client_id=self.clientID, redirect_uri=self.redirect_uri, scope=self.scope, open_browser=True)
        self.authCode = self.spAuth.get_authorization_code()
        self.accToken = self.spAuth.get_access_token(code=self.authCode,check_cache=False)

    def getAccToken(self, getDict=True):
        '''
        Returns access token as string or token info as json object.
        Inputs: getDict, if True returns json object of token info
        Returns: Access token string or json
        '''
        if getDict:
            return self.spAuth.get_cached_token()
        else:
            return self.accToken

#These lines are for testing

client = spotifyClient(clientID=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE) #Creates client object
client.authSetup() #Creates auth flow object, redirects user and grabs auth code, and finally grabs access token

print(client.getAccToken()) #Prints access token json, only need "access_token" for now

