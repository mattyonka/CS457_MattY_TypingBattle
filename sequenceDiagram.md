sequenceDiagram
    participant Player1Client as Player 1<br/>(Client 0)
    participant GameServer as Game Server
    participant Player2Client as Player 2<br/>(Client 1)
    Note over Player1Client,Player2Client: Connection Phase
    Player1Client->>GameServer: CONNECT (player_id: Player_1)
    GameServer->>Player1Client: LOBBY_WAIT
    Player2Client->>GameServer: CONNECT (player_id: Player_2)
    GameServer->>Player1Client: GAME_START
    GameServer->>Player2Client: GAME_START
    Note over Player1Client,Player2Client: Game Round Loop
    loop Until One Player Health ≤ 0
        GameServer->>Player1Client: SEND_PROMPT (text to type)
        GameServer->>Player2Client: SEND_PROMPT (text to type)
        Note over Player1Client,Player2Client: Player Typing (Picked up by selectors)
        par Player 1 Types
            Player1Client->>Player1Client: User types response
        and Player 2 Types
            Player2Client->>Player2Client: User types response
        end
        alt Player 1 submits first or both submit
            Player1Client->>GameServer: PLAYER_INPUT (message & timestamp)
            Player2Client->>GameServer: PLAYER_INPUT (message & timestamp)
            GameServer->>GameServer: Validate inputs & calculate damage
        else Invalid input received
            GameServer->>Player1Client: RESEND_PROMPT (error message + text)
            Player1Client->>GameServer: PLAYER_INPUT (corrected message)
        end
        Note over Player1Client,Player2Client: Damage Phase
        GameServer->>Player1Client: STATE_UPDATE (health values)
        GameServer->>Player2Client: STATE_UPDATE (health values)
    end
    Note over Player1Client,Player2Client: Game End Phase
    alt Player wins
        GameServer->>Player1Client: GAME_OVER (victory message)
        GameServer->>Player2Client: GAME_OVER (defeat message)
    else Player quits
        Player1Client->>GameServer: QUIT
        GameServer->>Player2Client: GAME_OVER
    end
