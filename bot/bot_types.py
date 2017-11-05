import time

class Deposit:
    """
    This class represents a deposit request
    Parameters:
        twitch_username: The username of the user that made the deposit request
        twitch_channel: The channel in which user made a deposit request
        address: The address to which the user must deposit(is None then the user must be assigned an address)
    """    

    def __init__(self, twitch_username, twitch_channel, depositID = None, address = None, success = 0, active = 1, deposit_time = time.time(), deposit_end_time = None):
        self.depositID = depositID
        self.twitch_username = twitch_username
        self.twitch_channel = twitch_channel
        self.address = address
        self.success = success
        self.active = active
        self.deposit_time = deposit_time
        self.deposit_end_time = deposit_end_time
    
class Withdraw:
    """
    This class represents a withdraw request
    Parameters:
        reddit_username: The username of the user that made the withdraw request
        message: The message in which the request originated
        address: The address to send the iota to
        amount: The amount of iota to send
    """
       
    def __init__(self, twitch_username, twitch_channel, amount, address, withdrawID = None, active = 1, withdraw_time = time.time(), withdraw_end_time = None):
        self.withdrawID = withdrawID
        self.twitch_username = twitch_username
        self.twitch_channel = twitch_channel
        self.amount = amount
        self.address = address
        self.active = active
        self.withdraw_time = withdraw_time
        self.withdraw_end_time = withdraw_end_time

class IRCMessage:
    """
    This class represents a IRC message
    Parameters:
        channel: The channel were message is sent
        username: Username who sent a message
        text: Text of message
    """    

    def __init__(self, channel, username, text):
        self.channel = channel
        self.username = username
        self.text = text
