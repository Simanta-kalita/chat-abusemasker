import asyncio
import urllib.request
from collections import deque
import socketio
from aiohttp import web

# ----------------------------------------------------------------------
# Aho-Corasick automaton for O(n) pattern matching
# ----------------------------------------------------------------------
class AhoCorasick:
    def __init__(self):
        self.trie = [{}]      # list of dicts: char -> node index
        self.fail = [0]       # failure links
        self.output = [[]]    # list of pattern lengths ending at node

    def add_word(self, word):
        node = 0
        for ch in word:
            if ch not in self.trie[node]:
                self.trie[node][ch] = len(self.trie)
                self.trie.append({})
                self.fail.append(0)
                self.output.append([])
            node = self.trie[node][ch]
        self.output[node].append(len(word))

    def build(self):
        from collections import deque
        q = deque()
        for ch, nxt in self.trie[0].items():
            self.fail[nxt] = 0
            q.append(nxt)
        while q:
            r = q.popleft()
            for ch, u in self.trie[r].items():
                q.append(u)
                f = self.fail[r]
                while f and ch not in self.trie[f]:
                    f = self.fail[f]
                self.fail[u] = self.trie[f][ch] if ch in self.trie[f] else 0
                self.output[u].extend(self.output[self.fail[u]])

    def match(self, text_lower):
        n = len(text_lower)
        state = 0
        for i, ch in enumerate(text_lower):
            while state and ch not in self.trie[state]:
                state = self.fail[state]
            if ch in self.trie[state]:
                state = self.trie[state][ch]
            else:
                state = 0
            for length in self.output[state]:
                start = i - length + 1
                end = i
                # word boundary check
                prev_ok = (start == 0) or not text_lower[start-1].isalpha()
                next_ok = (end == n-1) or not text_lower[end+1].isalpha()
                if prev_ok and next_ok:
                    yield start, end

# ----------------------------------------------------------------------
# Abuse filter using difference array for O(n) masking
# ----------------------------------------------------------------------
class AbuseFilter:
    def __init__(self, word_list):
        self.automaton = AhoCorasick()
        for w in word_list:
            if w.strip():
                self.automaton.add_word(w.lower())
        self.automaton.build()

    def mask_message(self, message):
        lower_msg = message.lower()
        n = len(message)
        diff = [0] * (n + 1)
        for start, end in self.automaton.match(lower_msg):
            diff[start] += 1
            diff[end + 1] -= 1
        masked = []
        coverage = 0
        for i, ch in enumerate(message):
            coverage += diff[i]
            masked.append('*' if coverage > 0 else ch)
        return ''.join(masked)

# ----------------------------------------------------------------------
# Download abuse list from internet (with fallback)
# ----------------------------------------------------------------------
def download_abuse_list(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read().decode('utf-8')
            return [line.strip() for line in data.splitlines() if line.strip()]
    except Exception as e:
        print(f"Download failed: {e}. Using built-in fallback list.")
        return ["badword", "abuse", "offensive", "swear", "curse", "hate"]

# ----------------------------------------------------------------------
# Socket.IO server
# ----------------------------------------------------------------------
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='aiohttp')
app = web.Application()
sio.attach(app)

abuse_filter = None

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('system', 'Welcome! Abusive words will be masked.', room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def chat_message(sid, data):
    if not isinstance(data, str):
        return
    masked = abuse_filter.mask_message(data)
    await sio.emit('chat_message', {'sender': sid, 'text': masked})

# Serve the static HTML client
async def index(request):
    return web.FileResponse('./static/index.html')

app.router.add_get('/', index)
app.router.add_static('/static', './static')

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
async def main():
    global abuse_filter
    print("Downloading abuse list...")
    abuse_words = download_abuse_list(
        "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/en"
    )
    print(f"Loaded {len(abuse_words)} words.")
    print("Building Aho-Corasick automaton...")
    abuse_filter = AbuseFilter(abuse_words)
    print("Automaton ready. Starting server at http://localhost:8765")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8765)
    await site.start()
    await asyncio.Event().wait()  # run forever

if __name__ == '__main__':
    asyncio.run(main())