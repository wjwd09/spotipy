# spotipy

To run & use

Ensure you have port forwarded the server machine using the desired port
PORT is a global variable in both threaded_server.py & threaded_client.py. Change as needed

1: Run threaded_server.py
2: On a device run main.py
3: Create a session, Enter your name and click create session. You will be redirected to spotify's OAuth, accept to continue
4: Share the given session ID with users.
5: Users run main.py
6: Join a session, Enter name & session id, click join session. 

From here the host and users can pause/play, skip, and add songs to the queue
Host has the ability to revoke permissions by clicking users & permissions, a person's name and then selecting the permission to allow or deny
