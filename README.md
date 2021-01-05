# Qu / Spotipi

# Description

This project is inspired by Spotify's built in multi-user built in listening sessions
Key difference is this allows users who do not have spotify to also join the sessions

It uses a client server architecture where the server handles all sessions and spotify commands and the client makes requests over websocket connection


# To run & use

Ensure you have port forwarded the server machine using the desired port
PORT is a global variable in both threaded_server.py & threaded_client.py. Change as needed

1: Run threaded_server.py \n
2: On a device run main.py \n
3: Create a session, Enter your name and click create session. You will be redirected to spotify's OAuth, accept to continue \n
4: Share the given session ID with users. \n
5: Users run main.py \n
6: Join a session, Enter name & session id, click join session. \n

From here the host and users can pause/play, skip, and add songs to the queue \n
Host has the ability to revoke permissions by clicking users & permissions, a person's name and then selecting the permission to allow or deny
