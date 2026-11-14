#!/usr/bin/env python3
"""Typing Battle server (non-blocking I/O multiplexing with selectors).

Usage:
    python3 server.py -h
    python3 server.py -p 8080

Single-threaded: every socket is non-blocking and the OS event loop
(selectors) tells us when something can be read or written, so no locks are
needed. Messages are newline-delimited JSON over TCP.

Lifecycle: WAITING_FOR_PLAYERS -> (2 CONNECTs) -> BETWEEN/ROUND loop ->
GAME_OVER -> clean up (close both sockets) -> WAITING_FOR_PLAYERS.
"""
import argparse
import json
import random
import selectors
import socket
import sys
import time

START_HEALTH = 100
MAX_DAMAGE = 50          # damage cap, no matter how slow the loser is
TIE_THRESHOLD_PCT = 1.0  # less than 1% slower counts as a tie (no damage)
ROUND_TIMEOUT = 30.0     # seconds before an unanswered round is resolved
ROUND_DELAY = 3.0        # pause between rounds / before the first prompt
MAX_LINE = 65536         # drop clients that send absurdly long lines

PROMPTS = [
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "How vexingly quick daft zebras jump!",
    "Sphinx of black quartz, judge my vow.",
    "A journey of a thousand miles begins with a single step.",
    "To be or not to be, that is the question.",
    "All that glitters is not gold.",
    "Practice makes perfect, so keep on typing.",
    "Speed is nothing without accuracy.",
    "Bright vixens jump; dozy fowl quack.",
    "The five boxing wizards jump quickly.",
    "Type fast or take damage, the choice is yours.",
]


def log(msg):
    print(f"[server] {msg}", flush=True)


class Conn:
    """Per-connection state."""

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.inbuf = b""
        self.outbuf = b""
        self.player = None             # 0 or 1 once registered
        self.close_after_flush = False
        self.closed = False


class Server:
    def __init__(self, port):
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.listener = None
        self.reset_game()

    # ---------------------------------------------------------------- state
    def reset_game(self):
        """CLEAN_UP: reset everything back to WAITING_FOR_PLAYERS."""
        self.players = [None, None]
        self.health = [START_HEALTH, START_HEALTH]
        self.state = "WAITING_FOR_PLAYERS"
        self.prompt = None
        self.answers = [None, None]
        self.round_no = 0
        self.round_start = 0.0
        self.next_round_at = 0.0

    # ------------------------------------------------------------ networking
    def start(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("0.0.0.0", self.port))
        self.listener.listen()
        self.listener.setblocking(False)
        self.sel.register(self.listener, selectors.EVENT_READ, data=None)
        log(f"Listening on 0.0.0.0:{self.port}, waiting for 2 players...")

    def next_timeout(self):
        mono = time.monotonic()
        if self.state == "ROUND":
            return max(0.0, self.round_start + ROUND_TIMEOUT - mono)
        if self.state == "BETWEEN":
            return max(0.0, self.next_round_at - mono)
        return None  # nothing scheduled: sleep until a socket event

    def run(self):
        self.start()
        while True:
            for key, mask in self.sel.select(self.next_timeout()):
                if key.data is None:
                    self.accept()
                    continue
                conn = key.data
                if conn.closed:
                    continue
                if mask & selectors.EVENT_READ:
                    self.read(conn)
                if mask & selectors.EVENT_WRITE and not conn.closed:
                    self.flush(conn)
            self.tick()

    def accept(self):
        try:
            sock, addr = self.listener.accept()
        except (BlockingIOError, InterruptedError):
            return
        sock.setblocking(False)
        conn = Conn(sock, addr)
        self.sel.register(sock, selectors.EVENT_READ, data=conn)
        log(f"Connection from {addr[0]}:{addr[1]}")

    def read(self, conn):
        recv_time = time.monotonic()  # stamp arrival as early as possible
        try:
            data = conn.sock.recv(4096)
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            data = b""
        if not data:
            self.on_disconnect(conn)
            return
        if conn.close_after_flush:
            return  # we're finished with this client; ignore anything else
        conn.inbuf += data
        if len(conn.inbuf) > MAX_LINE and b"\n" not in conn.inbuf:
            self.send(conn, "ERROR", {"message": "Message too long."})
            self.on_disconnect(conn)
            return
        while b"\n" in conn.inbuf and not conn.closed:
            line, _, conn.inbuf = conn.inbuf.partition(b"\n")
            if not line.strip():
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
                if not isinstance(msg, dict):
                    raise ValueError
            except ValueError:
                self.send(conn, "ERROR", {"message": "Malformed message."})
                continue
            self.handle_message(conn, msg, recv_time)

    def send(self, conn, msg_type, payload=None, **extra):
        if conn is None or conn.closed:
            return
        msg = {"msg_type": msg_type}
        if payload is not None:
            msg["payload"] = payload
        msg.update(extra)
        msg["timestamp"] = int(time.time())
        conn.outbuf += (json.dumps(msg) + "\n").encode("utf-8")
        self.flush(conn)

    def flush(self, conn):
        if conn.closed:
            return
        if conn.outbuf:
            try:
                sent = conn.sock.send(conn.outbuf)
                conn.outbuf = conn.outbuf[sent:]
            except (BlockingIOError, InterruptedError):
                pass
            except OSError:
                self.on_disconnect(conn)
                return
        if not conn.outbuf and conn.close_after_flush:
            self.close_conn(conn)
            return
        events = selectors.EVENT_READ
        if conn.outbuf:
            events |= selectors.EVENT_WRITE
        try:
            self.sel.modify(conn.sock, events, data=conn)
        except (KeyError, ValueError, OSError):
            pass

    def close_conn(self, conn):
        if conn.closed:
            return
        conn.closed = True
        try:
            self.sel.unregister(conn.sock)
        except (KeyError, ValueError):
            pass
        try:
            conn.sock.close()
        except OSError:
            pass

    def send_final(self, conn, msg_type, payload):
        """Send one last message, then close once it has been fully written."""
        if conn is None or conn.closed:
            return
        conn.close_after_flush = True
        conn.player = None
        self.send(conn, msg_type, payload)

    # --------------------------------------------------------------- protocol
    def handle_message(self, conn, msg, recv_time):
        kind = msg.get("msg_type")
        if kind == "CONNECT":
            self.handle_connect(conn)
        elif kind == "QUIT":
            log(f"{self.label(conn)} sent QUIT")
            self.on_disconnect(conn)
        elif kind == "PLAYER_INPUT":
            self.handle_input(conn, msg, recv_time)
        else:
            self.send(conn, "ERROR", {"message": f"Unknown msg_type: {kind}"})

    def label(self, conn):
        return f"Player {conn.player + 1}" if conn.player is not None else f"{conn.addr[0]}:{conn.addr[1]}"

    def handle_connect(self, conn):
        if conn.player is not None:
            return
        if self.state != "WAITING_FOR_PLAYERS" or None not in self.players:
            conn.close_after_flush = True
            self.send(conn, "ERROR", {"message": "Game is full. Try again later."})
            return
        slot = self.players.index(None)
        self.players[slot] = conn
        conn.player = slot
        log(f"{self.label(conn)} registered ({conn.addr[0]}:{conn.addr[1]})")
        if None in self.players:
            self.send(conn, "LOBBY_WAIT", "Waiting for Player 2...",
                      player_id=f"Player_{slot + 1}")
            return
        self.start_game()

    def start_game(self):
        log("Both players connected. Game is about to begin!")
        rules = ("Both players have connected.\n"
                 "This game tests your ability to type. Try to type the phrase "
                 "faster than the other player!\n"
                 "The player who types the fastest will deal damage to the other player.\n"
                 "First player to reach 0 life loses.\n"
                 "(Type /quit at any time to leave the game.)")
        for i, c in enumerate(self.players):
            self.send(c, "GAME_START", rules, player_id=f"Player_{i + 1}")
        self.state = "BETWEEN"
        self.next_round_at = time.monotonic() + ROUND_DELAY

    def start_round(self):
        self.round_no += 1
        self.prompt = random.choice(PROMPTS)
        self.answers = [None, None]
        self.state = "ROUND"
        self.round_start = time.monotonic()
        log(f"Round {self.round_no}: {self.prompt!r}")
        for c in self.players:
            self.send(c, "SEND_PROMPT", self.prompt, round=self.round_no)

    def handle_input(self, conn, msg, recv_time):
        p = conn.player
        if p is None or self.state != "ROUND" or self.answers[p] is not None:
            return  # not in a round, or already answered: ignore
        payload = msg.get("payload")
        text = payload.get("message") if isinstance(payload, dict) else payload
        if not isinstance(text, str):
            self.send(conn, "ERROR", {"message": "PLAYER_INPUT needs payload.message"})
            return
        if text.strip() == self.prompt:
            # Server-side arrival time decides the winner (client clocks can't be trusted).
            self.answers[p] = recv_time - self.round_start
            log(f"Player {p + 1} answered correctly in {self.answers[p]:.2f}s")
            if None not in self.answers:
                self.resolve_round()
        else:
            self.send(conn, "RESEND_PROMPT", "Oops! That wasn't correct!.\n\n" + self.prompt)

    def tick(self):
        mono = time.monotonic()
        if self.state == "ROUND" and mono >= self.round_start + ROUND_TIMEOUT:
            log("Round timed out")
            self.resolve_round()
        elif self.state == "BETWEEN" and mono >= self.next_round_at:
            self.start_round()

    def resolve_round(self):
        times = [t if t is not None else ROUND_TIMEOUT for t in self.answers]
        damage = 0
        winner = None
        if self.answers == [None, None]:
            head = "***Nobody finished in time. No damage this round.***"
        else:
            fast, slow = min(times), max(times)
            pct_slower = (slow - fast) / max(fast, 0.001) * 100
            if pct_slower < TIE_THRESHOLD_PCT:
                head = "***Tie! No damage this round.***"
            else:
                winner = 0 if times[0] < times[1] else 1
                loser = 1 - winner
                damage = min(MAX_DAMAGE, int(pct_slower))  # 1% slower = 1 damage, capped
                self.health[loser] = max(0, self.health[loser] - damage)
                head = (f"***Player {winner + 1} won that round!***\n"
                        f"***Player {loser + 1} Takes {damage} Damage***")
        shown = ["no answer" if t is None else f"{t:.2f}s" for t in self.answers]
        message = (f"{head}\n\nTimes: Player 1 {shown[0]} | Player 2 {shown[1]}\n"
                   f"Player 1 Health: {self.health[0]}/{START_HEALTH} --- "
                   f"Player 2 Health: {self.health[1]}/{START_HEALTH}")
        log(f"Round {self.round_no} result: winner={winner} damage={damage} health={self.health}")
        for c in self.players:
            self.send(c, "STATE_UPDATE", {
                "message": message,
                "player1_health": self.health[0],
                "player2_health": self.health[1],
                "damage": damage,
                "round_winner": None if winner is None else f"Player_{winner + 1}",
            })
        for i in range(2):
            if self.health[i] <= 0:
                self.game_over(winner=1 - i, quit_by=None)
                return
        self.state = "BETWEEN"
        self.next_round_at = time.monotonic() + ROUND_DELAY

    def scoreline(self):
        return (f"Player 1 Health: {self.health[0]}/{START_HEALTH} --- "
                f"Player 2 Health: {self.health[1]}/{START_HEALTH}")

    def game_over(self, winner, quit_by):
        log(f"Game over. Player {winner + 1} wins" + (" (opponent quit)" if quit_by is not None else ""))
        players = list(self.players)
        for i, c in enumerate(players):
            if c is None:
                continue
            if i == winner:
                lead = "Your opponent quit. You win!" if quit_by is not None else "You win!"
            else:
                lead = f"You lose! Player {winner + 1} wins."
            self.send_final(c, "GAME_OVER", {"message": f"{lead} \n\n{self.scoreline()}"})
        self.reset_game()  # CLEAN_UP -> WAITING_FOR_PLAYERS

    def on_disconnect(self, conn):
        """Handles QUIT, closed sockets and socket errors."""
        if conn.closed:
            return
        p = conn.player
        in_game = self.state in ("BETWEEN", "ROUND")
        self.close_conn(conn)
        if p is None or self.players[p] is not conn:
            return
        log(f"Player {p + 1} left")
        self.players[p] = None
        if in_game:
            self.game_over(winner=1 - p, quit_by=p)
        # else: they left the lobby; their slot is free for a new player


def parse_args():
    parser = argparse.ArgumentParser(
        prog="server.py", add_help=False,
        description="Typing Battle server - a 2 player console typing duel.",
        epilog="example: python3 server.py -p 8080")
    parser.add_argument("-h", "--help", action="help",
                        help="display this help message and exit")
    parser.add_argument("-p", "--port", type=int, default=5000, metavar="PORT",
                        help="port to listen on, binds to 0.0.0.0 (default: 5000)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    return args


def main():
    args = parse_args()
    server = Server(args.port)
    try:
        server.run()
    except OSError as e:
        print(f"[server] Could not run on port {args.port}: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[server] Shutting down.")


if __name__ == "__main__":
    main()
