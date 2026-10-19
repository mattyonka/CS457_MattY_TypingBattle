# 2.1 Concurrency Model 
The concurrency model that this game will use is a Non-Blocking/IO multiplexing model. This means that the server will set client sockets to non-blocking, and that the OS event loop will monitor any read/write operations. 
This is because two people will be playing this game simultaneously, and will need to input their answer at any given time. A blocking scheme could cause issues if both players try to submit their answers in a different order.

Using selectors in python should result in a simple approach that is easy to implement and use. It should avoid race conditions or deadlocks, especially in the case where inputs can come it at different times. 
For this program, no locking mechanisms will be used for player moves. The game state is evaluated after each player has successfully submitted their input, or potentially if they time out.

This is not a computationally advanced program, so the potential advantage from multithreading will not be realized in this program. 

Connection Lifecycle:
*Connect  - The server will be in listen mode until both clients connect. There should be a message stating that the game is about to begin once both clients connect.
*Client registration - The client when accepting will be given either player 1 or player 2, depending on who joined first. There's no current plan to allow for custom names/identifiers.
*Active game loop - Since the program will use selectors, the server will wait for any event as stated above. Once something comes into the socket, it will perform the logic necessary. A timeout should also occur if no user input is detected for a long enough period of time. Though the connection will be TCP based, the program may add a heartbeat UDP ping from the client to the server to make sure that no client has disconnected/timed out.
*Socket Teardown - After the game ends cleanup will occur, and the active sockets will be closed on both the host and client end. 

# 2.2 Sequence Diagram 
_See sequenceDiagram.md_

# 2.3 Score Board Design
* Scoring will consist of two things: The health of player 1 and player 2. They will be simple integer values stored in the Host's memory. 

* To update the players on scores, a STATE_UPDATE message will be sent out that consists of each player's current health and the damage that one player sustained in the round. 

* Damage will be sustained by one player if they are slower at typing the correct phrase than the other player. The current plan is to have the slower player take more damage the slower they are compared to the winner.
The losing player will take damage if they are anywhere from 1-50% slower (this may be tweaked if it's less fun) than the other player, corresponding to 1-50 health as damage. It will cap at 50 damage no matter how slow you are.
