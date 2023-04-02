# CS 3251 PA2 - ttweetser by Will Braga, Dylan Upchurch, and Yassine Attia
# A multithreaded, simple, twitter-like server
# Usage -
#       python3 ttweetser.py <Server Port>
#
# Referenced Threaded TCP Base Code @ https://docs.python.org/3/library/socketserver.html
import socketserver
import socket
import sys
import threading
import re

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

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    
    # reference this thread's user with self.user
    user = ""

    # SERVER ACTIONS GO HERE
    def reply(self, message):
        msg_b = message.encode()
        self.request.sendall(msg_b) 
        return

    def push(self, hashtag, message, excl_users = []):
        users = []
        msg_b = message.encode()
        for user in subs[hashtag]:
            if user not in excl_users:
                users += [user]
                with users_online_mutex:
                    sock = users_online[user]
                    sock.sendall(msg_b)
        return users

    def connect(self, message):
        port = int(message[:5])
        username = message[5:]
        push_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        push_sock.connect(('127.0.1.1',port))
        with users_online_mutex:
            if username not in users_online.keys():
                response = "success"
                users_online[username] = push_sock
                self.user = username
            else:
                response = "fail"
        self.reply(response)
        return

    def tweet(self,message):
        hashtag = message.split('\"')[-1].strip().split('#')
        with tweets_mutex:
            if self.user in tweets:
                tweets[self.user] += [message]
            else:
                tweets[self.user] = [message]
        with subs_mutex:
            users_pushed = []
            users_pushed += self.push('#ALL', self.user + ': ' + message)
            print(users_pushed)
            for tag in hashtag:
                tag = "#" + tag
                if tag in subs.keys():
                    users_pushed += self.push(tag, self.user + ': ' + message, users_pushed)
                    print(users_pushed)
        with timeline_mutex:
            for user in users_pushed:
                if user in timeline:
                    timeline[user] += [self.user + ': ' + message]
                else:
                    timeline[user] = [self.user + ': ' + message]
        return

    def subscribe(self,hashtag):
        with subs_mutex:
            counter = 0
            for tag in subs.keys():
                if self.user in subs[tag]:
                    counter += 1
                if counter >= 3:
                    self.reply('operation failed: sub <hashtag> failed, '\
                                + 'already exists or exceeds 3 limitation')
                    return
            if hashtag in subs:
                subs[hashtag] += [self.user]
            else:
                subs[hashtag] = [self.user]
            self.reply('operation success')
        return

    def unsubscribe(self,hashtag):
        with subs_mutex:
            if hashtag in subs.keys() and self.user in subs[hashtag]:
                subs[hashtag].remove(self.user)
            self.reply('operation success')
        return

    def timeline(self):
        response = 'N/A'
        with timeline_mutex:
            if self.user in timeline:
                response = ''
                for tweet in timeline[self.user]:
                    response += tweet + '\n'
                response = response[:-1]
        self.reply(response)
        return

    def getusers(self):
        with users_online_mutex:
            response = '-'.join(users_online.keys())
            self.reply(response)
        return
    
    def gettweets(self,message):
        response = ''
        with tweets_mutex:
            if message in tweets:
                response = ''
                for tweet in tweets[message]:
                    response += message + ': ' + tweet + '\n'
                response = response[:-1]
            else:
                response = 'no user "' + message + '" in the system'
        self.reply(response)
        return

    def exit(self):
        with subs_mutex:
            for tag in subs.keys():
                if self.user in subs[tag]:
                    subs[tag].remove(self.user)
        with tweets_mutex:
            if self.user in tweets:
                tweets.pop(self.user)
        with timeline_mutex:
            if self.user in timeline:
                timeline.pop(self.user)
        with users_online_mutex:
            push_sock = users_online[self.user]
            push_sock.close() 
            users_online.pop(self.user)
        return

    def handle(self):
        while True:
            try:
                received_b = self.request.recv(1024)
            except socket.error:
                return
            received = received_b.decode()
            if len(received) != 0:
                msg_type = received[0]
                msg = str(received[1:])
                if msg_type == MSG_TYPES['connect']:
                    self.connect(msg)
                elif msg_type == MSG_TYPES['tweet']:
                    self.tweet(msg)
                elif msg_type == MSG_TYPES['subscribe']:
                    self.subscribe(msg)
                elif msg_type == MSG_TYPES['unsubscribe']:
                    self.unsubscribe(msg)
                elif msg_type == MSG_TYPES['timeline']:
                    self.timeline()
                elif msg_type == MSG_TYPES['getusers']:
                    self.getusers()
                elif msg_type == MSG_TYPES['gettweets']:
                    self.gettweets(msg)
                elif msg_type == MSG_TYPES['exit']:
                    self.exit()
                    return
                print(str(msg_type) + '-' + msg  + "\n")
        return

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


# ENTRY POINT HERE
# define data structures
users_online = {} # a list of all users
users_online_mutex = threading.Lock()
subs = {'#ALL':[]} # dict with key = hashtag, val = list of subscribed users
subs_mutex = threading.Lock()
tweets = {} # dict with key = user, val = list of user's tweets
tweets_mutex = threading.Lock()
timeline = {} # dict with key = user, val = list of tweets in user's timeline
timeline_mutex = threading.Lock()

# check number of args
if len(sys.argv) != 2:
    sys.exit("error: args should contain <Server Port>")

# get port number and validate it is an integer
try:
    server_port = int(sys.argv[1])
except:
    sys.exit("error: args should contain <Server Port>")

if not 0 <= server_port <= 65353:
    sys.exit("error: server port invalid")
 

# get host IP
# server_ip = socket.gethostbyname(socket.gethostname())
server_ip = '127.0.0.1'

# start first server thread, which spawns a new thread for each request
try:
    server = ThreadedTCPServer((server_ip, server_port), ThreadedTCPRequestHandler)
except:
    sys.exit("ERROR CREATING SERVER")
with server:
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    print("ttweetser main thread is listening at " \
            + str(server_ip) + ":" + str(server_port) + "\n")
    thread.join()
