## 2. Application-Layer Messaging Protocol Blueprint (Sprint 1 Deliverable)

### 2.1 Message Transport & Serialization Format
- **Transport Protocol:** TCP
- **Serialization Format:** [JSON]
- **Framing Mechanism:** [Newline-delimited (`\n`) JSON payloads]
- Newline delimited JSONs will be used, as this makes it easier for the payload to be as long as it needs to be. Depending on the game settings, the messages to be typed will be of variable lengths, which makes this method the easiest way to implement. The type of message will have to be implied by the game state, as the user shouldn't have to type in a specific command while under a time pressure.

### 2.2 Message Schema Definitions

#### Message Types and Examples:
1. `CONNECT` (Client -> Server): Request to join the game room.
```json
{
  "msg_type": "CONNECT",
  "player_id": "Player_1",
  "timestamp": 1727000000
}
```
2. `LOBBY_WAIT` (Server -> Client): Notification that server is waiting for Player 2.
  ```json
{
  "msg_type": "LOBBY_WAIT",
  "payload": "Waiting for Player 2...",
  "timestamp": 1727000000
}
```
3. `GAME_START` (Server -> Clients): Game initiated, assigns roles (e.g. Player 1 vs Player 2).
```json
{
  "msg_type": "GAME_START",
  "payload": "Both players have connected.\n This game tests your ability to type. Try to type the phrase faster than the other player! \nThe player who types the fastest will deal damage to the other player. \nFirst player to reach 0 life loses.",
  "timestamp": 1727000000
}
```
4. `SEND_PROMPT` (Server -> Client): The server will send out the message for the clients to copy. This message will then be required in the return payload for EVALUATE_INPUT.
```json
{
  "msg_type": "SEND_PROMPT",
  "payload": "Example text that the user will have to type",
  "timestamp": 1727000000
}
```
5. `RESEND_PROMPT` (Server -> Client): The server will re-send the prompt with an error message stating that their input was incorrect.
```json
{
  "msg_type": "RESEND_PROMPT",
  "payload": "Oops! That wasn't correct!.\n\nExample text that the user will have to type",
  "timestamp": 1727000000
}
```
6. `PLAYER_INPUT` (Clients -> Server): Player submitted payload of text data. This will be evaluated to see if it matches the required text.
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
7. `STATE_UPDATE` (Server -> Clients): Broadcast current game state and player health values.
```json
{
  "msg_type": "STATE_UPDATE",
  "payload": {
    "message": "***Player 1 won that round!***\n\n\nPlayer 1 Health: xx/100 --- Player 2 Health xx/100"
  },
  "timestamp": 1727000000
}
``` 
8. `GAME_OVER` (Server -> Clients): Victory notification and final score message.
```json
{
  "msg_type": "GAME_OVER",
  "payload": {
    "message": "You win! \n\n Player1 Health: xx/100 --- Player 2 Health 0/100"
  },
  "timestamp": 1727000000
}
```
9. `ERROR` (Server -> Client): Invalid move or malformed packet error. Not intended to be output, ERROR should only be used for an issue.
```json
{
  "msg_type": "ERROR",
  "payload": {
    "message": "ERROR"
  },
  "timestamp": 1727000000
}
```
10. `QUIT` (Client -> Server): Notifies the server that the client has quit or disconnected. Only QUIT should be used for quitting.
```json
{
  "msg_type": "QUIT",
  "payload": {
    "message": "QUIT"
  },
  "timestamp": 1727000000
}
```
