import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import soundcloud
import os
import json

SCOPE = "user-read-playback-state user-modify-playback-state"
spAuth = spotipy.SpotifyPKCE(client_id="cc9859af7bda4fea8c2e74321becb949",redirect_uri="http://localhost:8888/callback",scope=SCOPE,open_browser=True)

authCode = spAuth.get_authorization_code()

accToken = spAuth.get_access_token(code=authCode,check_cache=False)

print(accToken)