# ** Concurrency Model ** 
The concurrency model that this game will use is a Non-Blocking/IO multiplexing model. This means that the server will set client sockets to non-blocking, and that the OS event loop will monitor any read/write operations. 
This is because two people will be playing this game simultaneously, and will need to input their answer at any given time. A blocking scheme could cause issues if both players try to submit their answers in a different order.

Using selectors in python should result in a simple approach that is easy to implement and use. 
