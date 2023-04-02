# CS 3251 PA2 - ttweetcli by William Braga, Dylan Upchurch, and Yassine Attia
# A multithreaded, simple, twitter-like client to communicate with ttweetser
# Usage -
#       python3 ttweetcli.py <Server IP> <Server Port> <Username>
#
import socket
import sys
import threading
import shlex

MSG_TYPES = {
    'connect'    :'0',
    'tweet'      :'1',
    'subscribe'  :'2',
    'unsubscribe':'3',
    'timeline'   :'4',
    'getusers'   :'5',
    'gettweets'  :'6',
    'exit'       :'7'
}

def send(sock, msg_type,msg=''):
    msg_type = MSG_TYPES[msg_type]
    sock.sendall((msg_type+msg).encode())
    return

def receive(sock):
    response = ''
    while True:
        try:
            received = sock.recv(8192)
            if received:
                response += received.decode()
            else:
                break
        except Exception as e:
            print(e)
            return None
        return response


def tweet(sock,tweet,hashtag):
    send(sock, 'tweet', tweet+' '+hashtag)
    return

def subscribe(sock,hashtag):
    send(sock, 'subscribe', hashtag)
    print(receive(sock))
    return

def unsubscribe(sock,hashtag):
    send(sock, 'unsubscribe', hashtag)
    print(receive(sock))
    return

def timeline(sock):
    send(sock, 'timeline')
    line = receive(sock)
    if line != 'N/A':
        print(line)
    return

def getusers(sock):
    send(sock, 'getusers')
    users = receive(sock).split('-')
    for user in users:
        print(user)
    return

def gettweets(sock,username):
    send(sock, 'gettweets', username)
    tweets = receive(sock)
    print(tweets)
    return

def exit(sock):
    send(sock, 'exit')
    return

def userin(user_sock):
    # start user input loop
    ICMD = "INVALID COMMAND"
    while True:
        # take user input and format
        msg = shlex.split(input(), posix=False)

        # validate input length
        if 1 <= len(msg) <= 3:
            cmd = msg[0]
        else:
            print(ICMD)
        
        # execute command
        if len(msg) == 3:
            if cmd == "tweet":
                # Message Validation
                tweet_msg = msg[1].strip('"')
                if len(tweet_msg) > 150:
                    print('message length illegal, connection refused.')
                    continue
                if len(tweet_msg) == 0 or tweet_msg is None:
                    print('message format illegal.')
                    continue
                if not ht_validate(msg[2],istweet=True):
                    print('hashtag illegal format, connection refused.')
                else:
                    tweet(user_sock,msg[1],msg[2])
            else:
                print(ICMD)
        elif len(msg) == 2:
            if cmd == "subscribe":
                if ht_validate(msg[1]):
                    subscribe(user_sock, msg[1])
                else:
                    print('hashtag illegal format, connection refused.')
            elif cmd == "unsubscribe":
                if ht_validate(msg[1]):
                    unsubscribe(user_sock, msg[1])
                else:
                    print('hashtag illegal format, connection refused.')
            elif cmd == "gettweets":
                gettweets(user_sock, msg[1])
            else:
                print(ICMD)
        elif len(msg) == 1:
            if cmd == "timeline":
                timeline(user_sock)
            elif cmd == "getusers":
                getusers(user_sock)
            elif cmd == "exit":
                exit(user_sock)
                user_sock.close()
                print("bye bye")
                break
            else:
                print(ICMD)

def listen(sock):
    sock.settimeout(2.0)
    while True:
        if stop_threads:
            return
        try:
            push_sock, server_ip = sock.accept()
        except:
            continue
        break
    while True:
        if stop_threads:
            push_sock.close()
            return
        response_b = push_sock.recv(1024)
        if not response_b == b'':
            response = response_b.decode()
            print(response)

def ht_validate(hashtags, istweet=False):
    tags =  hashtags.split('#')[1:]
    valid = True if hashtags[0] == '#' else False
    for tag in tags:
        if not tag.isalnum():
            valid = False
        if len(tag) < 1:
            valid = False
        if istweet and tag == 'ALL':
            valid = False
    return valid


# ENTRY POINT HERE
stop_threads = False
args = sys.argv

# Validate Number of Arguments
if len(args) != 4:
    sys.exit('error: args should contain <ServerIP> <ServerPort> <Username>')

server_ip, server_port, username = args[1:]

# Validate IP
try:
    #TODO Use library for validation?
    ip_fields = list(map(lambda x: int(x), server_ip.split('.')))
    if len(ip_fields) != 4:
        raise ValueError
    for x in ip_fields:
        if not 0 <= x <= 255:
            raise ValueError
except ValueError:
    sys.exit('error: server ip invalid, connection refused.')

# Validate Port
try:
    server_port = int(server_port)
    if not 0 <= server_port <= 65353:
        raise ValueError
except ValueError:
    sys.exit('error: server port invalid, connection refused.')

# Validate Username
if not username.isalnum():
    sys.exit('error: username has wrong format, connection refused.')

# Create Socket for Pushed Tweets
client_ip = '127.0.1.1'
push_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
push_sock.bind((client_ip,0))
push_sock.listen(1)
push_port = str(push_sock.getsockname()[1])

# Create Listen Thread for Pushed Tweets
listen = threading.Thread(target = listen, args = (push_sock,))
listen.start()

# pad push port number
padding = ''
while(len(padding) < (5-len(push_port))):
    padding =+ '0'
push_port_p = padding + push_port
# print("push port: " + push_port)

try:
    # Create Socket for User Input
    user_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_sock.connect((server_ip, server_port))
    user_port = str(user_sock.getsockname()[1])
    # print("user port: " + user_port)
    
    # send connection message
    connect_msg = push_port_p + username

    # Connect
    send(user_sock,"connect",connect_msg)
    # wait for response
    response = receive(user_sock)
    if response == "fail":
        raise Exception

except socket.error:
    stop_threads = True
    sys.exit('connection error, please check your server: Connection refused')
except:
    stop_threads = True
    sys.exit('username illegal, connection refused.')

print('username legal, connection established.')

# Create User Input Thread for Client Interactions
userin = threading.Thread(target = userin, args = (user_sock,))
userin.start()
# User Exits
userin.join()

stop_threads = True
push_sock.close()
listen.join()
