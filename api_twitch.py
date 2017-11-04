import config
import socket
import re
import time
import logging
from bot_types import IRCMessage
import helper

class Api_twitch:
    logging.basicConfig(filename='log/api_twitch.log',format='%(levelname)s: %(asctime)s: %(message)s ',level=logging.INFO)

    def __init__(self, host, port):
        """
        Initializes the twitch api
        Connect socket to twitch irc
        Parameters:
        host -- host address of twitch irc
        port -- port of twitch irc
        """ 
        
        self.socket = socket.socket()
        self.connect(host, port)

    def connect(self, host, port):
        """
        Connect socket to host
        Keyword arguments:
        sock -- the socket
        host -- host address of twitch irc
        port -- port of twitch irc
        """

        self.socket.connect((host, port))

    def login(self, nick, psw):
        """
        Login to twitch irc
        Keyword arguments:
        sock -- the socket
        nick -- username for login
        pass -- password for username
        """
    
        self.socket.send("PASS {}\r\n".format(psw).encode("utf-8"))
        self.socket.send("NICK {}\r\n".format(nick).encode("utf-8"))

    def join_channel(self, channel):
        """
        Join to irc channel
        Keyword arguments:
        sock -- the socket
        channel -- desired channel to login
        """

        self.socket.send("JOIN {}\r\n".format(channel).encode("utf-8"))
        print("Joined channel: " + channel)
        logging.info('Joined channel: {0}'.format(channel))
        self.send_message(channel, "iotaTipBot joined channel! Now you can tip channel or user with IOTA. For details type !help. For better experience with whisper messages follow me.\r\n")

    def leave_channel(self, channel):
        """
        Leave irc channel
        Keyword arguments:
            channel -- desired channel to leave
        """

        self.socket.send("LEAVE {}\r\n".format(channel).encode("utf-8"))
        print("Leave channel: " + channel)
        logging.info('Leave channel: {0}'.format(channel))

    def send_message(self, channel, message):
        """
        Send a chat message to the server.
        Keyword arguments:
        sock -- the socket over which to send the message
        msg  -- the message to be sent
        """

        print("PRIVMSG {} :{}".format(channel, message).encode("utf-8"))
        self.socket.send("PRIVMSG {} :{}".format(channel, message).encode("utf-8"))

    def send_private_message(self, channel, username, message):
        """
        Send a chat message to the server.
        Keyword arguments:
        sock -- the socket over which to send the message
        msg  -- the message to be sent
        """

        print("PRIVMSG {} :/w {} {}".format(channel, username, message).encode("utf-8"))
        self.socket.send("PRIVMSG {} :/w {} {}".format(channel, username, message).encode("utf-8"))

    def send_pong(self):
        """
        Send a pong message to the server.
        """

        print("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))

    def is_ircmessage(self, line):
        """
        Check if line have PRIVMSG part
        """
        message = re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)', line)
        return len(message) > 0

    def get_message(self, line):
        """
        Get a massage from line of text
        Arguments:
        line -- one line of text received from socket
        Returns:
        Object with channel, username and massage
        """
        channel = re.findall(r'^:.+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+.+ PRIVMSG (.*?) :', line)[0]
        username = re.findall(r'^:([a-zA-Z0-9_]+)\!', line)[0]
        text = re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)', line)[0]

        print("Kanal: " + channel + " korisnik: " + username + " poruka: " + text)

        return IRCMessage(channel, username, text)

    def is_register_request(self, message):
        """
        Check if the message contains a register request
        Parameters:
            message: The message to check
        """

        register_string = re.compile(config.comm_register,re.I)
        match = register_string.search(message)
        if match:
            return True
        return False

    def is_unregister_request(self, message):
        """
        Check if the message contains a unregister request
        Parameters:
            message: The message to check
        """

        unregister_string = re.compile(config.comm_unregister,re.I)
        match = unregister_string.search(message)
        if match:
            return True
        return False

    def is_help_request(self, message):
        """
        Check if the message contains a help request
        Parameters:
            message: The message to check
        """

        help_string = re.compile(config.comm_help,re.I)
        match = help_string.search(message)
        if match:
            return True
        return False

    def is_deposit_request(self, message):
        """
        Check if the message contains a deposit request
        Parameters:
            message: The message to check
        """

        deposit_string = re.compile(config.comm_deposit,re.I)
        match = deposit_string.search(message)
        if match:
            return True
        return False

    def is_balance_request(self, message):
        """
        Check if the message contains balance request
        Parameters:
            message: The message to check
        """

        balance_string = re.compile(config.comm_balance,re.I)
        match = balance_string.search(message)
        if match:
            return True
        return False

    def is_withdraw_request(self, message):
        """
        Check if the message contains a withdraw request
        Parameters:
            message: The message to check
        """

        withdraw_string = re.compile(config.comm_withdraw,re.I)
        match = withdraw_string.search(message)
        if match:
            return True
        return False

    def is_donate_request(self, message):
        """
        Check if the message contains a donate request
        Parameters:
            message: The message to check
        """

        donate_string = re.compile(config.comm_donate,re.I)
        match = donate_string.search(message)
        if match:
            return True
        return False

    def is_tip(self, message):
        """
        Check if the message is a tip
        Parameters:
            message: The message to check
        """

        tip_string = re.compile("\@([a-zA-Z0-9_]+)\s*\+\s*([0-9.]+)\s*(miota|iota|\$|usd)|\@([a-zA-Z0-9_]+)\s*\+(\$)\s*([0-9.]+)",re.I)
        match = tip_string.search(message)
        if match:
            if self.get_iota_tip_amount(message) == 0:
                return False
            else:
                return True
        return False

    def get_tip_recipient_and_amount(self, message):
        """
        Get a recipient and amount from tip message
        Parameters:
            message: The tip message
        """

        tip_string = re.compile("\@([a-zA-Z0-9_]+)\s*\+\s*([0-9.]+)\s*(miota|iota|\$|usd)|\@([a-zA-Z0-9_]+)\s*\+(\$)\s*([0-9.]+)",re.I)
        match = tip_string.search(message)
        
        if match.group(5):
            recipient = match.group(4)
            amount = helper.get_usd_value(float(match.group(6)))
        else:
            recipient = match.group(1)
            if str(match.group(3)).lower() == "usd" or str(match.group(3)).lower() == "$":
                amount = helper.get_usd_value(float(match.group(2)))
            if str(match.group(3)).lower() == "iota":
                amount = round(float(match.group(2)))
            elif str(match.group(3)).lower() == "miota":
                amount = round(float(match.group(2)) * 1000000)

        return (recipient, amount)

    def contains_iota_amount(self, message):
        """
        Check if the message body contains an iota amount
        Parameters:
            message: The message to check
        """

        iota_amount_string = re.compile("([0-9]+)\s*iota",re.I)
        miota_amount_string = re.compile("([0-9]+)\s*miota",re.I)
        match = iota_amount_string.search(message)
        if match:
            return True
        match = miota_amount_string.search(message)
        if match:
            return True
        return False

    def get_iota_tip_amount(self, message):
        """
        Return the iota amount refrenced in the message, convets miota to iota
        Parameter:
            message: The message to get the iota tip amount from
        """

        iota_amount_string = re.compile("\+\s*([0-9]+)\s*iota",re.I)
        miota_amount_string = re.compile("\+\s*([0-9]+)\s*miota",re.I)
        miota_fraction_amount_string = re.compile("\+\s*([0-9]+.[0-9]+)\s*miota")
        match = iota_amount_string.search(message)
        if match:
            return int(match.group(1))
        match = miota_amount_string.search(message)
        if match:
            return (int(match.group(1))*1000000)
        match = miota_fraction_amount_string.search(message)
        if match:
            return(int(float(match.group(1))*1000000))

    def get_iota_amount(self,message):
        """
        Return the iota amount refrenced in the message, converts miota to iota
        Parameters:
            message: The message to get the iota amount from
        """

        iota_amount_string = re.compile("([0-9]+)\s*iota",re.I)
        miota_amount_string = re.compile("([0-9]+)\s*miota",re.I)
        match = iota_amount_string.search(message)
        if match:
            return int(match.group(1))
        match = miota_amount_string.search(message)
        if match:
            return (int(match.group(1))*1000000)

    def get_message_address(self, message):
        """
        Return the iota address refrenced in the message
        Parameters:
            message: The message to get the address from   
        """

        address_string = re.compile("[A-Z,9]{90}")
        match = address_string.search(message)
        if match:
            return bytearray(match.group(0),"utf-8")
        else:
            return None