# Score Board Design
-Scoring will consist of two things: The health of player 1 and player 2. They will be simple integer values stored in the Host's memory. 

-To update the players on scores, a STATE_UPDATE message will be sent out that consists of each player's current health and the damage that one player sustained in the round. 

-Damage will be sustained by one player if they are slower at typing the correct phrase than the other player. The current plan is to have the slower player take more damage the slower they are compared to the winner.
The losing player will take damage if they are anywhere from 1-50% slower (this may be tweaked if it's less fun) than the other player, corresponding to 1-50 health as damage. It will cap at 50 damage no matter how slow you are.
