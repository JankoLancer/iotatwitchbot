import re
import threading
import time
import queue
import random
import string
from iota import *
from database import Database
import logging
import config
from api_twitch import Api_twitch
from api_iota import Api_iota
from bot_types import Deposit, Withdraw, IRCMessage
import helper

#database init
bot_db = Database()
bot_db_lock = threading.Lock()

#twitch api init
twitch_api = Api_twitch(config.twitch_HOST, config.twitch_PORT)
twitch_api.login(config.twitch_NICK, config.twitch_PASS)
twitch_api.join_channel(config.twitch_CHAN)

#iota api init
iota_api = Api_iota(config.seed, config.node_address)

#log init
logging.basicConfig(filename='log/iota_tip_bot.log', format='%(levelname)s: %(asctime)s: %(message)s ', level=logging.INFO)

#join all registred channel
with bot_db_lock:
    channels = bot_db.get_channels()

for channel in channels:
    twitch_api.join_channel(channel[1])


deposit_queue = queue.Queue()
def deposits():
    """
    A thread to handle deposits
    Deposits are handled in 2 phases.
       Phase1:
          A unique 0 balance address is generated and given to the user
       Phase2:
          The address is checked for a balance, if the address has a balance greater than 0 then the user has deposited to that address and their account should be credited
    """
    deposit_timeout = (24*60*60)
    deposits = []
    print("Deposit thread started. Waiting for deposits...")

    while True:
        time.sleep(1)
        try:
            #Check the queue for new deposits, add them to the database and local deposit list.
            new_deposit = deposit_queue.get(False)
            deposits.append(new_deposit)
            logging.info('New deposit request received by: {0}\r\n'.format(new_deposit.twitch_username))
            print('New deposit request received by: {0}\r\n'.format(new_deposit.twitch_username))
        except queue.Empty:
            pass
        for index, deposit in enumerate(deposits):
            twitch_username = deposit.twitch_username
            twitch_channel = deposit.twitch_channel
            address = deposit.address

            if address is None:
                #lock the database
                #generate the address
                #add the address to the used addresses
                #make sure address has 0 balance
                with bot_db_lock:
                    while True:
                        address_index = bot_db.get_address_index()
                        address = iota_api.get_new_address(address_index)
                        if iota_api.get_balance(address) == 0:
                            break
                
                reply = "@{0} please transfer your IOTA to this address: {1} Do not deposit to the same address more than once. This address will expire in 24 hours.\r\n".format(twitch_username,address._trytes.decode("utf-8"))
                logging.info('{0} was assigned to address {1}'.format(twitch_username,address._trytes.decode("utf-8")))
                twitch_api.send_message(twitch_channel, reply)
                twitch_api.send_private_message(twitch_channel, twitch_username, reply)
                
                with bot_db_lock:
                    bot_db.update_deposit_address(deposit.depositID, address)
                    deposit.address = address

                del deposits[index]
                deposits.append(deposit)

            else:
                deposit_time = deposit.deposit_time
                address = deposit.address
                twitch_username = deposit.twitch_username
                twitch_channel = deposit.twitch_channel

                #Check if the deposit request has expired
                if (time.time() - deposit_time) > deposit_timeout:
                    print("Transaction has timed out. User: {0} Channel: {1}".format(twitch_username, twitch_channel))
                    reply = "@{0} your deposit request has timed out. Please start a new deposit. Do not transfer to the previous address.\r\n".format(twitch_username)
                    twitch_api.send_message(twitch_channel, reply)
                    twitch_api.send_private_message(twitch_channel, twitch_username, reply)
                    with bot_db_lock:
                        bot_db.timeout_deposit(deposit.depositID)
                    logging.info('{0}\'s deposit has timed out'.format(twitch_username))
                    del deposits[index]
                else:
                    balance = iota_api.get_balance(address)
                    if balance > 0:
                        print("Transaction found, {0} transfered {1} iota".format(twitch_username, balance))
                        with bot_db_lock:
                            bot_db.add_balance(twitch_username, balance)
                        reply = "@{0} you have successfully funded your tipping account with {1} iota!\r\n".format(twitch_username, balance)
                        twitch_api.send_message(twitch_channel, reply)
                        twitch_api.send_private_message(twitch_channel, twitch_username, reply)
                        with bot_db_lock:
                            bot_db.success_deposit(deposit.depositID)
                        logging.info('{0} deposited {1} iota'.format(twitch_username, balance))
                        del deposits[index]

#Start the deposit thread
deposit_thread = threading.Thread(target=deposits, args=())
deposit_thread.daemon = True
deposit_thread.start()


withdraw_queue = queue.Queue()
def withdraws():
    """
    A thread to handle all withdraw requests
    Withdraw requests are pulled from the queue and executed one by one
    """
    withdraws = []
    print("Withdraw thread started. Waiting for withdraws...")
    
    while True:
        time.sleep(1)
        try:
            new_withdraw = withdraw_queue.get(False)    
            withdraws.append(new_withdraw)
            logging.info("New withdraw received: ({0},{1})\r\n".format(new_withdraw.twitch_username,new_withdraw.amount))
            print("New withdraw received: ({0},{1})".format(new_withdraw.twitch_username,new_withdraw.amount))
            print("{0} withdraws in queue".format(withdraw_queue.qsize()))
        except queue.Empty:
                pass
        for index, withdraw in enumerate(withdraws):
            twitch_username = withdraw.twitch_username
            twitch_channel = withdraw.twitch_channel
            amount = withdraw.amount
            address = withdraw.address

            print("Sending transfer to address {0} of amount {1}".format(address.decode("utf-8"),amount))
            iota_api.send_transfer(address,amount)
            print("Transfer complete.")
            logging.info('{0} withdrew {1} iota to address: {2}'.format(twitch_username,amount,address.decode("utf-8")))
            reply = "@{0} You have successfully withdrawn {1} IOTA to address {2}\r\n".format(twitch_username, amount, address.decode("utf-8"))
            
            twitch_api.send_message(twitch_channel, reply)
            twitch_api.send_private_message(twitch_channel, twitch_username, reply)

            with bot_db_lock:
                bot_db.success_withdraw(withdraw.withdrawID)
            del withdraws[index]

withdrawThread = threading.Thread(target=withdraws, args=())
withdrawThread.daemon = True
withdrawThread.start()


def periodic_info():
    print("Periodic Check thread started")
    while True:
        for channel in bot_db.get_channels():
            twitch_api.send_message(channel[1], "Tip any user with IOTA! Type !help for more info and list of commands! For better experience with whisper messages follow me.")
            time.sleep(10)

        time.sleep(1200)

periodic_info = threading.Thread(target=periodic_info, args=())
periodic_info.daemon = True
periodic_info.start()

#Reinitiate any requests that were not completed
with bot_db_lock:
    deposit_requests = bot_db.get_deposit_requests()
    withdraw_requests = bot_db.get_withdraw_requests()

for deposit_request in deposit_requests:
    depositID = deposit_request[0]
    twitch_username = bot_db.get_user_by_id(deposit_request[1])[1]
    twitch_channel = bot_db.get_channel_by_id(deposit_request[2])[1]
    success = deposit_request[3]
    active = deposit_request[4]
    address = deposit_request[5]
    if address is not None:
        address = Address(address)
    deposit_time = deposit_request[6]
    deposit_end_time = deposit_request[7]

    deposit = Deposit(twitch_username, twitch_channel, depositID, address, success, active, deposit_time, deposit_end_time)
    deposit_queue.put(deposit)

for withdraw_request in withdraw_requests:
    withdrawID = withdraw_request[0]
    twitch_username = bot_db.get_user_by_id(withdraw_request[1])[1]
    twitch_channel = bot_db.get_channel_by_id(withdraw_request[2])[1]
    address = withdraw_request[3]
    amount = withdraw_request[4]
    active = withdraw_request[5]
    withdraw_time = withdraw_request[6]
    withdraw_end_time = withdraw_request[7]

    withdraw = Withdraw(twitch_username, twitch_channel, amount, address, withdrawID, active, withdraw_time, withdraw_end_time)
    withdraw_queue.put(withdraw)


print("Message thread started. Waiting for messages...")
print("Bot initalized.")

while True:
    response = twitch_api.socket.recv(1024).decode("utf-8") 
    print(response)
    if response == "PING :tmi.twitch.tv\r\n":
        twitch_api.send_pong()
    else:
        lines = []
        lines = response.split('\r\n')
        
        for line in lines:
            if(twitch_api.is_ircmessage(line)):      
                ircmessage = twitch_api.get_message(line)

                #Check if it is a deposit request
                if twitch_api.is_deposit_request(ircmessage.text):
                    #Check if user already has a deposit request
                    bot_db.add_new_user(ircmessage.username)
                    has_pending_deposit = bot_db.user_have_active_deposits(ircmessage.username)
                    if has_pending_deposit:
                        reply = "@{0} you already have a deposit in progress. Please deposit to the address from the previous message or wait for it to expire.\r\n".format(ircmessage.username)
                        twitch_api.send_message(ircmessage.channel, reply)
                        twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                    else:
                        deposit = Deposit(ircmessage.username,ircmessage.channel)
                        with bot_db_lock:
                            depositID = bot_db.add_deposit_request(deposit)
                            deposit.depositID = depositID
                        deposit_queue.put(deposit)

                #Check if it is a withdraw request
                elif twitch_api.is_withdraw_request(ircmessage.text):
                    #Check if user already has a withdraw request
                    has_pending_withdraw = bot_db.user_have_active_withdraw(ircmessage.username)
                    if has_pending_withdraw:
                        reply = '@{0} you already have a withdraw pending. Please wait for that withdraw to finish before making another.\r\n'.format(ircmessage.username)
                        twitch_api.send_message(ircmessage.channel, reply)
                        twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                    
                    #Check how much they want to withdrawl
                    if twitch_api.contains_iota_amount(ircmessage.text):
                        amount = twitch_api.get_iota_amount(ircmessage.text)
                        with bot_db_lock:
                            valid = bot_db.check_balance(ircmessage.username, amount)
                        if valid:
                            #Find address
                            #TODO: Check if addres is valid
                            address = twitch_api.get_message_address(ircmessage.text)
                            if address:
                                with bot_db_lock:
                                    bot_db.subtract_balance(ircmessage.username, amount)
                                withdraw = Withdraw(ircmessage.username, ircmessage.channel, amount, address)
                                with bot_db_lock:
                                    withdrawID = bot_db.add_withdraw_request(withdraw)
                                    withdraw.withdrawID = withdrawID
                                withdraw_queue.put(withdraw)
                                

                                reply = "@{0} your withdraw has been received and is being processed. Please be patient the withdraw process may take up to a few hours\r\n".format(ircmessage.username)
                                twitch_api.send_message(ircmessage.channel, reply)
                                twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                            else:
                                reply = "@{0} You must put the address you want to withdraw to in your message\r\n".format(ircmessage.username)
                                twitch_api.send_message(ircmessage.channel, reply)
                                twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                        else:
                            with bot_db_lock:
                                balance = bot_db.get_user_balance(ircmessage.username)
                            reply = "@{0} sorry, you don't have {1} IOTA in your account. You currently have {2} IOTA.\r\n".format(ircmessage.username, amount, balance)
                            twitch_api.send_message(ircmessage.channel, reply)
                            twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                    else:
                        reply = "@{0} you must put the amount of IOTA you want to withdraw in your message. Format: 1024 IOTA\r\n".format(ircmessage.username)
                        twitch_api.send_message(ircmessage.channel, reply)
                        twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)

                #Check if it is a balance request
                elif twitch_api.is_balance_request(ircmessage.text):
                    with bot_db_lock:
                        balance = bot_db.get_user_balance(ircmessage.username)
                    reply = "@{0} your current balance is: {1} iota.\r\n".format(ircmessage.username, balance)
                    twitch_api.send_message(ircmessage.channel, reply)
                    twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)

                elif twitch_api.is_tip(ircmessage.text):                    
                    recipient, amount =  twitch_api.get_tip_recipient_and_amount(ircmessage.text)

                    with bot_db_lock:
                        valid = bot_db.check_balance(ircmessage.username, amount)
                    if valid:
                        usdValue = helper.get_iota_value(amount)
                        with bot_db_lock:
                            bot_db.subtract_balance(ircmessage.username, amount)
                            bot_db.add_balance(recipient, amount)
                        print('{0} tipped {1}'.format(ircmessage.username, recipient))
                        logging.info('{0} has tipped {1} {2} iota'.format(ircmessage.username, recipient, amount))   
                        reply = "@{0} You have successfully tipped @{1} with {2} iota(${3}).\r\n".format(ircmessage.username, recipient, amount,'%f' % usdValue)
                        twitch_api.send_message(ircmessage.channel, reply)
                        twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                    else:
                        with bot_db_lock:
                            balance = bot_db.get_user_balance(ircmessage.username)
                        reply = "@{0} you do not have the required funds. Your current balance is: {1} iota\r\n".format(ircmessage.username, balance)
                        twitch_api.send_message(ircmessage.channel, reply)
                        twitch_api.send_private_message(ircmessage.channel, ircmessage.username, reply)
                   
                #Check if it is a help request
                elif twitch_api.is_help_request(ircmessage.text):
                    reply = "You can get list of commands and description of bot purpose here: https://www.reddit.com/r/iotaTwitchTip/wiki/index \r\n"
                    twitch_api.send_message(ircmessage.channel, reply)
                    #twitch_api.send_private_message(ircmessage.channel, ircmessage.username, "Pomoc, privatna poruka\r\n")

                #Check if it is register request, if yes add in db and join channel
                elif ircmessage.channel == config.twitch_CHAN and twitch_api.is_register_request(ircmessage.text):
                    with bot_db_lock:
                        bot_db.add_new_channel("#" + ircmessage.username)
                        twitch_api.join_channel("#" + ircmessage.username)
                        twitch_api.send_message(ircmessage.channel, "{0} you are now registred! iotaTipBot will join your channel!\r\n".format(ircmessage.username))
        
                #Check if it is unregister request, if yes add unregister datetime for user in database
                elif ircmessage.channel == config.twitch_CHAN and twitch_api.is_unregister_request(ircmessage.text):
                    with bot_db_lock:
                        bot_db.unregister_channel("#" + ircmessage.username)
                        twitch_api.leave_channel("#" + ircmessage.username)
                        twitch_api.send_message(ircmessage.channel, "{0} you are now unregistred! iotaTipBot will leave your channel! You can register again if you like.\r\n".format(ircmessage.username))

                #Check if it is a donation request
                elif twitch_api.is_donate_request(ircmessage.text):
                    reply = "If you would like to support this project you can send IOTA or ETH to one of the addresses below or you can tip the bot! Thank you for your support!  IOTA: NU9U9IZN9TLNTPTLMHNPFVJOUQPMUSLMIW9QUDWQSMDDFKGXDIKCUGPGJDXILTQCD99VNDIMTQZQEMYYWFDHNAVACW    ETH: 0x5E24EAF533B058C0F6754Fc0521454FBEEbC24c9 \r\n"
                    twitch_api.send_message(ircmessage.channel, reply)
                #else
                #else:
                    

    time.sleep(1 / config.twitch_RATE)