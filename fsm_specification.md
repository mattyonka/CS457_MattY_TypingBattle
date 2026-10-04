
```
flowchart TB
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
    n2 -- Only one player has sent move, still waiting on second player --> D
    D -- player uses QUIT command/sock.close()--> n5["QUIT"]
    n5 -- Message stating game is terminated --> n3
    D -- TCP Connection temporarily lost --> n6["Disconnect"]
    n6 -- TCP Timeout (RST)/BrokenPipeError/TImeoutError --> n5
    n6 -- TCP Connection Restored --> D

    n1@{ shape: f-circ}

```
