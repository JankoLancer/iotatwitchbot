import urllib.request
import json

def get_iota_value(amount):
        """
        Returns the USD value of the given iota amount
        Parameters:
            amount: The amount of iota to get the value of
        """

        try:
            with urllib.request.urlopen('https://api.coinmarketcap.com/v1/ticker/iota/') as url:
                data = json.loads(url.read().decode())[0]
                price = data['price_usd']
                value = (amount / 1000000) * float(price)
                return value
        except:
            return amount / 1000000

def get_usd_value(amount):
        """
        Returns the IOTA value of the given usd amount
        Parameters:
            amount: The amount of usd to get the value of
        """

        try:
            with urllib.request.urlopen('https://api.coinmarketcap.com/v1/ticker/iota/') as url:
                data = json.loads(url.read().decode())[0]
                price = float(data['price_usd']) / 1000000
                value = round(amount / price)
                return value
        except Exception as e:
            print(e)
            return 0