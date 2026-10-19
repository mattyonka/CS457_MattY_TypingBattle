# ** 2.1 Concurrency Model ** 
The concurrency model that this game will use is a Non-Blocking/IO multiplexing model. This means that the server will set client sockets to non-blocking, and that the OS event loop will monitor any read/write operations. 
This is because two people will be playing this game simultaneously, and will need to input their answer at any given time. A blocking scheme could cause issues if both players try to submit their answers in a different order.

Using selectors in python should result in a simple approach that is easy to implement and use. It should avoid race conditions or deadlocks, especially in the case where inputs can come it at different times. 
For this program, no locking mechanisms will be used for player moves. The game state is evaluated after each player has successfully submitted their input, or potentially if they time out.

This is not a computationally advanced program, so the potential advantage from multithreading will not be realized in this program. 


# 2.2 Sequence Diagram 
_See sequenceDiagram.md_

# 2.3 Score Board Design
* Scoring will consist of two things: The health of player 1 and player 2. They will be simple integer values stored in the Host's memory. 

* To update the players on scores, a STATE_UPDATE message will be sent out that consists of each player's current health and the damage that one player sustained in the round. 

* Damage will be sustained by one player if they are slower at typing the correct phrase than the other player. The current plan is to have the slower player take more damage the slower they are compared to the winner.
The losing player will take damage if they are anywhere from 1-50% slower (this may be tweaked if it's less fun) than the other player, corresponding to 1-50 health as damage. It will cap at 50 damage no matter how slow you are.
