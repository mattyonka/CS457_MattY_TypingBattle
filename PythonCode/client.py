#!/usr/bin/env python3
"""Typing Battle client.

Usage:
    python3 client.py -h
    python3 client.py -i example.server.com -p 8080

Uses selectors to watch the server socket and the keyboard at the same time,
so server messages show up even while you are typing. Linux/macOS terminals
(the lab nodes) are supported; selecting on stdin does not work on Windows.
"""
import argparse
import json
import selectors
import socket
import sys
import time

HELP_EPILOG = """\
how to play:
  Each round the server sends a phrase. Type it exactly and press Enter.
  The faster correct typist wins the round and damages the other player
  based on how much slower they were (1-50 damage). Ties do no damage.
  Both players start with 100 health; reach 0 and you lose.
  Type /quit at any time to leave the game.

examples:
  python3 client.py -h
  python3 client.py -i example.server.com -p 8080
"""


def parse_args():
    parser = argparse.ArgumentParser(
        prog="client.py", add_help=False,
        description="Typing Battle client - a 2 player console typing duel.",
        epilog=HELP_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-h", "--help", action="help",
                        help="display this help message and exit")
    parser.add_argument("-i", "--host", default="localhost", metavar="HOSTNAME",
                        help="DNS hostname (or IP) of the server (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=5000, metavar="PORT",
                        help="server port (default: 5000)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    return args


def text_of(payload):
    """Payloads are either a plain string or {"message": ...}."""
    if isinstance(payload, dict):
        return str(payload.get("message", ""))
    return "" if payload is None else str(payload)


class Client:
    def __init__(self, sock):
        self.sock = sock
        self.inbuf = b""
        self.player_id = "Unassigned"
        self.awaiting_input = False
        self.done = False

    def send(self, msg_type, payload=None):
        msg = {"msg_type": msg_type, "player_id": self.player_id}
        if payload is not None:
            msg["payload"] = payload
        msg["timestamp"] = int(time.time())
        self.sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))

    def quit(self):
        try:
            self.send("QUIT", {"message": "QUIT"})
        except OSError:
            pass
        self.done = True

    def on_keyboard(self):
        line = sys.stdin.readline()
        if line == "":  # EOF (Ctrl-D)
            self.quit()
            return
        text = line.rstrip("\r\n")
        if text.strip().lower() == "/quit":
            print("You left the game.")
            self.quit()
        elif self.awaiting_input:
            self.awaiting_input = False
            self.send("PLAYER_INPUT", {"message": text})
            print("Submitted! Waiting for the result...")
        # otherwise there is no active prompt: ignore stray typing

    def on_socket(self):
        try:
            data = self.sock.recv(4096)
        except OSError:
            data = b""
        if not data:
            print("\nDisconnected from the server.")
            self.done = True
            return
        self.inbuf += data
        while b"\n" in self.inbuf and not self.done:
            line, _, self.inbuf = self.inbuf.partition(b"\n")
            if not line.strip():
                continue
            try:
                self.handle(json.loads(line.decode("utf-8")))
            except ValueError:
                continue

    def handle(self, msg):
        kind = msg.get("msg_type")
        body = text_of(msg.get("payload"))
        if msg.get("player_id"):
            self.player_id = msg["player_id"]
        if kind == "LOBBY_WAIT":
            print(f"You are {self.player_id.replace('_', ' ')}. {body}")
        elif kind == "GAME_START":
            print(f"\n=== TYPING BATTLE: you are {self.player_id.replace('_', ' ')} ===\n{body}")
        elif kind == "SEND_PROMPT":
            print(f"\n--- Round {msg.get('round', '?')} --- type this exactly, then press Enter:\n\n    {body}\n")
            self.awaiting_input = True
        elif kind == "RESEND_PROMPT":
            print(f"\n{body}\n")
            self.awaiting_input = True
        elif kind == "STATE_UPDATE":
            self.awaiting_input = False
            print(f"\n{body}")
        elif kind == "GAME_OVER":
            self.awaiting_input = False
            print(f"\n=== GAME OVER ===\n{body}")
            self.done = True
        elif kind == "ERROR":
            print(f"\n[server error] {body}")


def main():
    args = parse_args()
    try:
        sock = socket.create_connection((args.host, args.port), timeout=10)
    except OSError as e:
        print(f"Could not connect to {args.host}:{args.port} - {e}", file=sys.stderr)
        sys.exit(1)
    sock.settimeout(None)  # blocking socket is fine: we only recv when select says readable
    print(f"Connected to {args.host}:{args.port}.")

    client = Client(sock)
    sel = selectors.DefaultSelector()
    sel.register(sock, selectors.EVENT_READ, "socket")
    sel.register(sys.stdin, selectors.EVENT_READ, "keyboard")
    try:
        client.send("CONNECT")
        while not client.done:
            for key, _ in sel.select():
                if key.data == "socket":
                    client.on_socket()
                else:
                    client.on_keyboard()
                if client.done:
                    break
    except KeyboardInterrupt:
        print()
        client.quit()
    except OSError as e:
        print(f"Connection error: {e}", file=sys.stderr)
    finally:
        sel.close()
        sock.close()


if __name__ == "__main__":
    main()
