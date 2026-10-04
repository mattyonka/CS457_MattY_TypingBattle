# CS 457 Project Statement of Work (SOW) & Protocol Specification Template

**Student Name:** Matthew Yonkaitis

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
