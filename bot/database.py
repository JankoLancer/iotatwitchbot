import sqlite3
import config
import time
from datetime import datetime

class Database:
    """
    Implements necessary functions to read from and modify the database
    """

    def __init__(self,name=config.database_name):
        self.conn = sqlite3.connect(name,check_same_thread=False)
        self.db = self.conn.cursor()
        self.create_database()
        #self.address_index = len(self.db.execute("SELECT * FROM usedAddresses").fetchall())
        
    def create_database(self):
        """
        Creates the database structure
        
        self.db.execute("CREATE TABLE IF NOT EXISTS users (twitchUsername TEXT PRIMARY KEY, balance INTEGER)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS commentsRepliedTo (commentId TEXT PRIMARY KEY)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS usedAddresses (addressIndex INTEGER PRIMARY KEY, address TEXT)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS deposits (messageId TEXT PRIMARY KEY, address TEXT)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS withdrawRequests (messageId TEXT PRIMARY KEY, address TEXT, amount INTEGER)")
        self.conn.commit()
        """
        self.db.execute("CREATE TABLE IF NOT EXISTS channels (channelID INTEGER PRIMARY KEY, channelName TEXT NOT NULL, datetimeRegister DATETIME NOT NULL, datetimeUnregister DATETIME)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS users (userID INTEGER PRIMARY KEY, twitchUsername TEXT NOT NULL, balance INTEGER)")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS deposits (depositID INTEGER PRIMARY KEY, userID INTEGER NOT NULL, channelID INTEGER NOT NULL, active INTEGER NOT NULL, success INTEGER NOT NULL, address TEXT, datetimeStart DATETIME NOT NULL, datetimeUEnd DATETIME, FOREIGN KEY(userID) REFERENCES users(userID), FOREIGN KEY(channelID) REFERENCES channels(channelID))")
        self.conn.commit()
        self.db.execute("CREATE TABLE IF NOT EXISTS withdraws (withdrawID INTEGER PRIMARY KEY, userID INTEGER NOT NULL, channelID INTEGER NOT NULL, address TEXT, amount INTEGER, active INTEGER, datetimeStart DATETIME NOT NULL, datetimeUEnd DATETIME, FOREIGN KEY(userID) REFERENCES users(userID), FOREIGN KEY(channelID) REFERENCES channels(channelID))")
        self.conn.commit()

    def add_new_channel(self, channel_name):
        """
        Add a new channel to the database
        Parameters:
            channel_name: The twitch channel name
        """
        entry = self.db.execute("SELECT * FROM channels WHERE channelName=?",(channel_name,)).fetchone()
        if not entry:
            self.db.execute("INSERT INTO channels(channelName, datetimeRegister) VALUES (?,?)",(channel_name,datetime.now()))
            self.conn.commit()
        else:
            self.db.execute("UPDATE channels SET datetimeUnregister = NULL WHERE channelName = ?",(channel_name,))
            self.conn.commit()

    def get_channels(self):
        """
        Returns all active registred channels
        """

        query = self.db.execute("SELECT * FROM channels WHERE datetimeUnregister is NULL")
        return query.fetchall()

    def get_channel(self, channel_name):
        """
        Get a chanell from the database
        Parameters:
            channel_name: The name of the channel
        """
        entry = self.db.execute("SELECT * FROM channels WHERE channelName=?",(channel_name,)).fetchone()
        return entry

    def get_channel_by_id(self, channelID):
        """
        Get a channel from the database by given ID
        Parameters:
            channelID: The ID of desired channel
        """
        entry = self.db.execute("SELECT * FROM channels WHERE channelID=?",(channelID,)).fetchone()
        return entry

    def unregister_channel(self, channel_name):
        """
        Update datetimeUnregister to given channel
        Parameters:
            channel_name: The twitch channel name
        """
        entry = self.db.execute("SELECT * FROM channels WHERE channelName=?",(channel_name,)).fetchone()
        if not entry:
            self.db.execute("UPDATE channels SET datetimeUnregister = ? WHERE channelName = ?",(datetime.now(),channel_name))
            self.conn.commit()

    def add_new_user(self, twitch_username):
        """
        Add a new user to the database
        Parameters:
            twitch_username: The twitch username of the new user
        """
        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if not entry:
            self.db.execute("INSERT INTO users(twitchUsername,balance) VALUES (?,?)",(twitch_username,0))
            self.conn.commit()

    def get_user(self, twitch_username):
        """
        Get a user from the database
        Parameters:
            twitch_username: The twitch username of the user
        """
        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        return entry
    
    def get_user_by_id(self, userID):
        """
        Get a user from the database by given ID
        Parameters:
            userID: The ID of desired user
        """
        entry = self.db.execute("SELECT * FROM users WHERE userID=?",(userID,)).fetchone()
        return entry

    def set_balance(self, twitch_username, amount):
        """
        Sets the balance of the given user
        Parameters:
            twitch_username: The twitch username of the user
            amount: The amount to set the user's balance to
        """
        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if entry:
            self.db.execute("UPDATE users SET balance=? WHERE twitchUsername=?",(amount,twitch_username))
            self.conn.commit()
        else:
            self.add_new_user(twitch_username)
            self.set_balance(twitch_username,amount)

    def add_balance(self, twitch_username, amount):
        """
        Adds to a user's account balance
        Parameters:
            twitch_username: The twitch username of the user
            amount: The amount to add to the user's account
        """
        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if entry:
            balance = entry[2]
            balance = balance + amount
            self.set_balance(twitch_username, balance)
        else:
            self.add_new_user(twitch_username)
            self.add_balance(twitch_username, amount)

    def subtract_balance(self, twitch_username, amount):
        """
        Subtracts from a user's account balance
        Parameters:
            twitch_username: The twitch username of the user
            amount: The amount to subtract from the user's account
        """
        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if entry:
            balance = entry[2]
            balance = balance - amount
            self.set_balance(twitch_username, balance)

    def check_balance(self, twitch_username, amount):
        """
        Check if the user's balance is at least a given amount
        Parameters:
            twitch_username: The twitch username of the user
            amount: The amount to check
        """

        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if entry:
            balance = entry[2]
            if amount > balance:
                return False
            else:
                return True
        else:
            return False
     
    def get_user_balance(self, twitch_username):
        """
        Returns the user's account balance
        Parameters:
            twitch_username: The twitch username of the user
        """

        entry = self.db.execute("SELECT * FROM users WHERE twitchUsername=?",(twitch_username,)).fetchone()
        if entry:
            balance = entry[2]
            return balance
        else:
            self.add_new_user(twitch_username)
            return self.get_user_balance(twitch_username)

    def get_total_balance(self):
        """
        Returns the total balance of all user's
        """

        query = self.db.execute("SELECT * FROM users").fetchall()
        total = 0
        for entry in query:
            total = total + entry[2]
        return total

    def add_deposit_request(self, deposit):
        """
        Adds a deposit to the database
        Parameters:
            deposit: The deposit to add
        """

        twitch_usernameID = self.get_user(deposit.twitch_username)[0]
        twitch_channelID = self.get_channel(deposit.twitch_channel)[0]

        self.db.execute("INSERT INTO deposits (userID, channelID, active, success, datetimeStart) VALUES (?, ?, ?, ?, ?)",(twitch_usernameID, twitch_channelID, deposit.active, deposit.success, deposit.deposit_time))
        self.conn.commit()

        return self.db.lastrowid

    def update_deposit_address(self, depositID, address):
        """
        Update the address of deposit
        Parameters:
            depositID: The deposit to update
            address: New address of deposit
        """

        self.db.execute("UPDATE deposits SET address = ? WHERE depositID = ?",(address._trytes.decode("utf-8"), depositID))
        self.conn.commit()

    def timeout_deposit(self, depositID):
        """
        Update the address of deposit
        Parameters:
            depositID: The deposit to timeout
        """
        self.db.execute("UPDATE deposits SET active = 0, success = 0, datetimeUEnd = ? WHERE depositID = ?",(time.time(), depositID))
        self.conn.commit()
    
    def success_deposit(self, depositID):
        """
        Update the address of deposit
        Parameters:
            depositID: The deposit to success
        """

        self.db.execute("UPDATE deposits SET active = 0, success = 1, datetimeUEnd = ? WHERE depositID = ?",(time.time(), depositID))
        self.conn.commit()

    def get_deposit_requests(self):
        """
        Returns all the deposits in the database
        """

        query = self.db.execute("SELECT * FROM deposits WHERE active = 1")
        return query.fetchall()
    
    def user_have_active_deposits(self, twitch_username):
        """
        Check ih user have active deposts requests
        Parameters:
            twitch_username: Username to check
        """

        twitch_usernameID = self.get_user(twitch_username)[0]

        query = self.db.execute("SELECT count (*) FROM deposits WHERE active = 1 and userID = ?", (twitch_usernameID,))
        count = query.fetchone()[0]
        if count > 0:
            return True
        return False

    def add_withdraw_request(self, withdraw):
        """
        Adds a withdraw to the database
        Parameters:
            withdraw: The deposit to add
        """

        twitch_usernameID = self.get_user(withdraw.twitch_username)[0]
        twitch_channelID = self.get_channel(withdraw.twitch_channel)[0]

        self.db.execute("INSERT INTO withdraws (userID, channelID, address, amount, active, datetimeStart) VALUES (?, ?, ?, ?, ?, ?)",(twitch_usernameID, twitch_channelID, withdraw.address, withdraw.amount, 1, withdraw.deposit_time))
        self.conn.commit()

        return self.db.lastrowid

    def get_withdraw_requests(self):
        """
        Returns all the withdraw requests from the database        
        """

        query = self.db.execute("SELECT * FROM withdraws WHERE active = 1")
        return query.fetchall()

    def success_withdraw(self, withdrawID):
        """
        Update the address of deposit
        Parameters:
            depositID: The deposit to success
        """

        self.db.execute("UPDATE deposits SET active = 0, datetimeUEnd = ? WHERE withdrawID = ?",(time.time(), withdrawID))
        self.conn.commit()

    def user_have_active_withdraw(self, twitch_username):
        """
        Check ih user have active withdraw
        Parameters:
            twitch_username: Username to check
        """

        twitch_usernameID = self.get_user(twitch_username)[0]

        query = self.db.execute("SELECT count (*) FROM withdraws WHERE active = 1 and userID = ?", (twitch_usernameID,))
        count = query.fetchone()[0]
        if count > 0:
            return True
        return False

    def get_address_index(self):
        """
        Returns the current address index(i.e. the count of all the used addresses)
        """

        query = self.db.execute("SELECT count (*) FROM deposits")
        address_index = query.fetchone()[0]
        return address_index 