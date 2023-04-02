CS 3251 - Fall 2020 - PA 2
William Braga
Dylan Upchurch
Yassine Attia

Files submitted:
	ttweetcli.py
	ttweetser.py
	README.txt
	
Running code (in python3 so no compilation needed):
To run the server use "py ttweetser.py <PORT NUMBER>"
	-When the server runs, it will specify at what IP and PORT the main thread is listening to. Please use the
	specified IP to connect from the client. - 127.0.0.1
To run the client use "py ttweetcli.py <HOST IP (127.0.0.1)> <PORT NUMBER> <USERNAME>"
	-HOST IP specifies the IP of the serve to connect to. Please use the IP printed from ttweetser.py - 127.0.0.1
	-PORT NUMBER specifies the port to connect to.
	-USERNAME specifies the user logging into the server.
	Note: The client IP is set to 127.0.1.1 for pushed tweets from the server
	
Division of Labor:
William Braga - Implementing Commands, Mutexing
Dylan Upchurch - Multithreading Client-Side Subscription and Commands
Yassine Attia - Debugging, Input Validation