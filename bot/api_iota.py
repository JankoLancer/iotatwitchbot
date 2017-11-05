import re
from iota import *
import random
import string
from iota.adapter.wrappers import RoutingWrapper
import config
import urllib.request
import json
import math
import time
import requests

class Api_iota:

    #logging.basicConfig(filename='api_iota.log',format='%(levelname)s: %(asctime)s: %(message)s ',level=logging.INFO)

    def __init__(self, seed, node_address):
        """     
        Initializes the iota api
        Routes attachToTangle calls to local node
        Parameters:
            seed: The account seed
        """
        self.iota_api = Iota(
            RoutingWrapper(node_address)
                .add_route('attachToTangle','http://localhost:14265'),seed)

    def send_transfer(self,addr,amount):
        """
        Wrapper function for iota.send_transfer
        Parameters:
            addr: the address to send the transfer to
            amount: the amount of iota to send 
        Return:
            The bundle that was attached to the tangle
        """
        
        while True:
            try:                  
              ret = self.iota_api.send_transfer(
                  depth = 3,
                  transfers = [
                      ProposedTransaction(
                          address = Address(
                              addr
                          ),
                          value = amount,
                          tag = Tag(b'IOTATWITCHTIPBOT')
                      ), 
                  ],
                  min_weight_magnitude=14
              )
              break
            except requests.exceptions.RequestException as e: 
                print(e)
                print("Error sending transfer... Retrying...")
            
        bundle = ret['bundle'] 
        confirmed = False
        transaction_time = time.time()
        start_time = time.time()
        transactions_to_check = []
        transactions_to_check.append(bundle.tail_transaction)
        while not confirmed:
            for transaction in transactions_to_check:
                confirmed = self.check_transaction(transaction)
                if confirmed:
                    break
            if (time.time() - start_time) > (10*60) and not confirmed:
                trytes = self.replay_bundle(transaction)
                transactions_to_check.append(Transaction.from_tryte_string(trytes[0]))
                start_time = time.time()
        return bundle

    def get_account_balance(self,index):
        """
        Returns the total balance of the iota account
        Parameters:
            index: the current address index(i.e. the count of all the used addresses)
        """

        while True:
            try:
              #Index must be at least 1
              if index==0:
                  index=1
              addresses = self.iota_api.get_new_addresses(0,index)['addresses']
              balances = self.iota_api.get_balances(addresses)['balances']
              total = 0
              for balance in balances:
                  total = total + balance
              return total
            except requests.exceptions.RequestException:
                pass
    
    def get_balance(self,address):
        """
        Wrapper functon for iota.get_balances()
        Returns the balance of a single address
        Parameters:
            address: the address to get the balance of
        """

        while True:
            try:
                address_data = self.iota_api.get_balances([address])
                return address_data['balances'][0]
            except requests.exceptions.RequestException:
                pass

    def is_address(self,address):
        """
        Wrapper functon for iota.isAddress()
        Returns the balance of a single address
        Parameters:
            address: the address to check if is valid
        """

        while True:
            try:
                address_data = self.iota_api.get_balances([address])
                return address_data['balances'][0]
            except requests.exceptions.RequestException:
                pass

    def get_new_address(self,index):
        """
        Wrapper function for iota.get_new_addresses()
        Returns a single address of the given index with a valid checksum
        Parameters:
            index: the index of the address to get
        """

        addresses = self.iota_api.get_new_addresses(index,1)
        for address in addresses['addresses']:
            address = address.with_valid_checksum()
            return address

    def create_seed(self):
        """
        Generates a random seed
        Depricated and probably cryptographically insecure
        Do not use
        """

        seed = ''.join(random.choice(string.ascii_uppercase + "9") for _ in range(81))
        return seed

    def check_transaction(self,transaction):
        """
        Checks if the given transaction is confirmed       
        Parameters:
            transaction: The transaction to check.
        """
        
        while True:
            try:
                transaction_hash = transaction.hash
                inclusion_states = self.iota_api.get_latest_inclusion([transaction_hash])
                return inclusion_states['states'][transaction_hash]
            except requests.exceptions.RequestException:
                pass

    def replay_bundle(self,transaction):
        """
        Replays the given bundle
        Parameters:
            transaction: The transaction to replay.
        """

        while True:
            try:
                transaction_hash = transaction.hash
                return self.iota_api.replay_bundle(transaction_hash,3,14)['trytes']
            except requests.exceptions.RequestException:
                pass
