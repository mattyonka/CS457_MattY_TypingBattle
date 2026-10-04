# CS 457 Project Statement of Work (SOW) & Protocol Specification Template

**Student Name:** Matthew Yonkaitis
**Date:** 2026-09-20  
**Course:** CS 457 - Computer Networks  
**Target Server Domain:** `server.yonkaitis.edu`  

---

## 1. Game Selection & Scope (Sprint 0)

> Planning is going to be an iterative process through the sprints so you don't have to have all the details now. Focus on big overview concepts. You will be updating the SOW as we plan.
> You have a lot of freedom to choose a game. There are a couple caveats.  

> - It must run in the console. The lab nodes won't be able to handle extensive graphics.
> - It has to be self-contained. You can use a internet-connector to download you code, but because the architecture must run 5 nodes you won't be able to run 
> - You are encouraged to use python, but I'm not going to make it a strict requirement. The instructor and TA's ability to help with C or Rust, etc will be diminished in other languages.

### 1.1 Game Overview
- **Chosen Game:** Typing Battle
- **Player Capacity:** 2 Players (Simulated via 2 CML Client nodes)
- **Game Summary:** 2 players will play against each other in a game that’s all about typing as quickly as possible. Players are given 100 health, and are given a sequence of prompts to type in. Each round has one typing prompt. The player that types the correct prompt the fastest wins, and does damage to the losing player based on how much slower the losing player was. This continues until one player wins or loses.

### 1.2 Core Game Rules & Win/Draw Conditions
- **Turn Mechanics:** No strict turn order will be kept, though that is possible. The server will keep track of who responded first with the appropriate answer to the given prompt.
- **Victory Condition:** A player wins the game when the opposing player's health reaches 0 or below.
- **Draw/Tie Condition:** A draw or tie in any round will result in no damage being done to either player's health. The game will continue until one player wins/loses or if one player decides to quit.

---

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

### 2.3 Game State Machine (FSM) Design (Sprint 1 Deliverable)
- **State Transitions:** 
```flowchart TB
    A["Init"] -- Server Started &amp; Listening --> B("WAITING_FOR_PLAYERS")
    B -- 2 clients connected --> C{"GAME_START"}
    n1["Filled Circle"] --> A
    D["PLAYER_INPUT"] -- Any player sends move --> n2["EVALUATE_INPUT"]
    n2 -- "Invalid input (Ask for re-entry of player input)" --> D
    n2 -- Display winner --> n3["CLEAN_UP"]
    C -- Print rules, show UI with health information --> n4["SEND_PROMPT"]
    n4 -- Send out message prompt --> D
    n2 -- No player is below 0 hp --> n4
    n3 -- Reset State --> B
    n2 -- Only one player has sent move, still waiting on second player--> D

    n1@{ shape: f-circ}
  ```
---

## 3. Game Behavior & Server Concurrency Architecture (Sprint 2 Deliverable)

### 3.1 Server Concurrency Strategy
- **Architecture Choice:** [Multi-Threading (`threading.Thread`) OR Non-blocking I/O multiplexing (`select.select` / `selectors`)]
- **Synchronization Logic:** Explain how shared game state and client list are thread-safe (e.g. `threading.Lock`) to prevent race conditions during turn processing.

### 3.2 State & Score Synchronization Across Clients
- **Turn Enforcement:** Detail how the server validates active player ID before processing moves and broadcasts updated turn notifications to all clients.
- **Score & Board Synchronization:** Describe how state broadcasts keep client screens synchronized in real time.

---

## 4. Coding & AI Implementation Plan (Sprint 3)

- **Permitted AI Tools:** [e.g., GitHub Copilot, ChatGPT, Claude]
- **AI Prompting & Constraint Strategy:** Explain how you will constrain AI models to generate code (in Python or your chosen language) that adheres strictly to the protocol blueprint and FSM designed in Sprints 1 & 2.
- **Implementation Risk Management:** Detail your plan to leverage past programming experience and manage time to ensure code completion on schedule.

---

## 5. CML Multi-Subnet Topology & Wireshark Deployment Plan (Sprint 4 & 5 Deliverable)

> For now you can use the topology below. We may update this when we get to defining subnets.

### 5.1 Subnet & Router Design
- **Subnet A (Client 1):** `192.168.10.0/24` (Interface `Gi0/1` on Router R1)
- **Subnet B (Client 2):** `192.168.11.0/24` (Interface `Gi0/2` on Router R1)
- **Subnet C (Game Server):** `192.168.20.0/24` (Interface `Gi0/1` on Router R2)
- **Router Backbone:** `10.0.0.0/30` (Interface `Gi0/0` on R1 <-> `Gi0/0` on R2)

### 5.2 DHCP Pools & DNS Configuration Plan
- **Router R1 DHCP Pool 1 (`CLIENT1_POOL`):** Leases `192.168.10.10` - `192.168.10.50`, gateway `192.168.10.1`, DNS `10.0.0.2`.
- **Router R1 DHCP Pool 2 (`CLIENT2_POOL`):** Leases `192.168.11.10` - `192.168.11.50`, gateway `192.168.11.1`, DNS `10.0.0.2`.
- **Router R2 Authoritative DNS:** Configured with `ip dns server` and static host mapping `server.[yourlastname].edu` -> `192.168.20.100`.

### 5.3 Deployment Strategy & Wireshark Trace Capture
- **CML Deployment Strategy:** Deploy `server.py` onto Subnet C node (`192.168.20.100`) behind Router R2, and `client.py` onto Subnet A and Subnet B nodes behind Router R1.
- **Cisco Infrastructure Configuration:** Router R1 DHCP pools (`CLIENT1_POOL`, `CLIENT2_POOL`) and Router R2 authoritative DNS (`ip host server.[lastname].edu 192.168.20.100`).
- **Wireshark Trace Capture Plan:** Capture DHCP DORA exchange (`dhcp_negotiation.pcap`) and DNS query/response resolution (`dns_lookup.pcap`).
