## 2. Application-Layer Messaging Protocol Blueprint (Sprint 1 Deliverable)

### 2.1 Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** [JSON]
- **Framing Mechanism:** [Newline-delimited (`\n`) JSON payloads]
- Newline delimited JSONs will be used, as this makes it easier for the payload to be as long as it needs to be. Depending on the game settings, the messages to be typed will be of variable lengths, which makes this method the easiest way to implement. The type of message will have to be implied by the game state, as the user shouldn't have to type in a specific command while under a time pressure.

### 2.2 Message Schema Definitions

#### Message Types:
1. `CONNECT` (Client -> Server): Request to join the game room.
2. `LOBBY_WAIT` (Server -> Client): Notification that server is waiting for Player 2.
3. `GAME_START` (Server -> Clients): Game initiated, assigns roles (e.g. Player 1 vs Player 2).
4. `SEND_PROMPT` (Server -> Client): The server will send out the message for the clients to copy. This message will then be required in the return payload for EVALUATE_INPUT.
5. `RESEND_PROMPT` (Server -> Client): The server will re-send the prompt with an error message stating that their input was incorrect. 
6. `PLAYER_INPUT` (Clients -> Server): Player submitted payload of text data. This will be evaluated to see if it matches the required text.
7. `STATE_UPDATE` (Server -> Clients): Broadcast current game state and player health values. 
8. `GAME_OVER` (Server -> Clients): Victory notification and final score message.
9. `ERROR` (Server -> Client): Invalid move or malformed packet error.
10. `QUIT` (Client -> Server): Notifies the server that the client has quit or disconnected.

#### Example JSON Protocol Schema:
```json
{
  "msg_type": "PLAYER_INPUT",
  "player_id": "Player_1",
  "payload": {
    "message": "This is an example phrase that needs to be typed out."
  },
  "timestamp": 1727000000
}
```

---
