# ** 2.1 Concurrency Model ** 
The concurrency model that this game will use is a Non-Blocking/IO multiplexing model. This means that the server will set client sockets to non-blocking, and that the OS event loop will monitor any read/write operations. 
This is because two people will be playing this game simultaneously, and will need to input their answer at any given time. A blocking scheme could cause issues if both players try to submit their answers in a different order.

Using selectors in python should result in a simple approach that is easy to implement and use. It should avoid race conditions or deadlocks, especially in the case where inputs can come it at different times. 
For this program, no locking mechanisms will be used for player moves. The game state is evaluated after each player has successfully submitted their input, or potentially if they time out.

This is not a computationally advanced program, so the potential advantage from multithreading will not be realized in this program. 
