================================================================================
 Socket.IO Chat Server with O(n) Abuse Masking (Aho-Corasick + difference array)
================================================================================

REQUIREMENTS
------------
- Python 3.7 or higher
- Install the following Python packages:
    pip install python-socketio[asyncio_client] aiohttp

(No additional dependencies; everything else is standard library)

FILES
-----
server.py       - The Socket.IO server that downloads abuse list, builds trie,
                  and masks messages in linear time.
static/
  index.html    - Simple web client that connects to the server.

RUNNING THE SERVER
------------------
1. Open a terminal in the folder containing server.py and the static/ folder.
2. Run:
      python server.py
3. You will see output like:
      Downloading abuse list...
      Loaded X words.
      Building Aho-Corasick automaton...
      Automaton ready. Starting server at http://localhost:8765

CONNECTING CLIENTS
------------------
- Open a web browser and visit: http://localhost:8765
- The page will connect automatically to the Socket.IO server.
- Type a message and press Send or Enter.
- Any abusive word (from the downloaded list) will be replaced by asterisks (*)
  in real time, and the masked message is broadcast to all connected clients.

TESTING WITH MULTIPLE CLIENTS
-----------------------------
- Open the same URL in different browser tabs or different machines on the same
  network (replace 'localhost' with the server's IP address).
- All clients will see each other's masked messages.

HOW THE ABUSE FILTER WORKS
--------------------------
1. Downloads a word list from GitHub (one word per line).
   (Fallback list is used if download fails.)
2. Builds an Aho-Corasick automaton (trie + failure links) in O(total pattern length).
3. When a message arrives (length n):
   - Aho-Corasick finds all matching patterns in O(n + #matches).
   - Word boundaries are respected (a match is only valid if preceded/followed
     by a non-letter or start/end of string).
   - A difference array records the intervals to mask.
   - A final O(n) pass builds the masked string by replacing characters inside
     intervals with '*'.
4. Overall complexity: O(n) per message, independent of the number or length of
   abusive words.

STOPPING THE SERVER
-------------------
Press Ctrl+C in the terminal where the server is running.

TROUBLESHOOTING
---------------
- Port 8765 already in use? Change the port in server.py (line ~120):
      site = web.TCPSite(runner, 'localhost', 8765)
- If you see CORS errors, check that `cors_allowed_origins='*'` is set in the
  AsyncServer constructor (already there).
- The abuse list URL may change; you can replace it with any raw text URL that
  contains one word per line.