import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup web3 connection
INFURA_URL = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Contract addresses
TROVE_MANAGER_ADDRESS = "0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2"
BORROWER_OPERATIONS_ADDRESS = "0x24179CD81c9e782A4096035f7eC97fB8B783e007"

# ABI files (you need to have these JSON files in the same directory)
with open("TroveManager.json") as f:
    TROVE_MANAGER_ABI = json.load(f)
with open("BorrowerOperations.json") as f:
    BORROWER_OPERATIONS_ABI = json.load(f)

# Initialize contracts
trove_manager = w3.eth.contract(address=TROVE_MANAGER_ADDRESS, abi=TROVE_MANAGER_ABI)
borrower_operations = w3.eth.contract(address=BORROWER_OPERATIONS_ADDRESS, abi=BORROWER_OPERATIONS_ABI)

# Your Ethereum address and private key
YOUR_ADDRESS = "YOUR_ETHEREUM_ADDRESS"
PRIVATE_KEY = "YOUR_PRIVATE_KEY"

def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return data["ethereum"]["usd"]

def get_trove_details(address):
    trove = trove_manager.functions.Troves(address).call()
    coll = trove[1] / 1e18
    debt = trove[0] / 1e18
    
    if debt > 0:
        price = get_eth_price()
        collateral_ratio = (coll * price) / debt
        return {
            "address": address,
            "collateral": coll,
            "debt": debt,
            "collateral_ratio": collateral_ratio
        }
    return None

def liquidate_trove(address):
    nonce = w3.eth.get_transaction_count(YOUR_ADDRESS)
    
    txn = borrower_operations.functions.liquidateTroves([address]).build_transaction({
        'chainId': 1,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    logging.info(f"Liquidation transaction sent: {tx_hash.hex()}")
    return tx_hash

def main():
    logging.info("Starting Liquity liquidation bot...")
    
    while True:
        try:
            first_trove = trove_manager.functions.getFirstTroveInSortedList().call()
            lowest_cr_trove = get_trove_details(first_trove)
            
            if lowest_cr_trove:
                logging.info(f"Lowest CR Trove: {lowest_cr_trove}")
                
                if lowest_cr_trove['collateral_ratio'] < 1.1:
                    logging.info(f"Attempting to liquidate trove {lowest_cr_trove['address']}...")
                    tx_hash = liquidate_trove(lowest_cr_trove['address'])
                    
                    # Wait for transaction confirmation
                    w3.eth.wait_for_transaction_receipt(tx_hash)
                    logging.info(f"Liquidation complete. Transaction hash: {tx_hash.hex()}")
                else:
                    logging.info("Lowest CR Trove is above liquidation threshold. Waiting...")
            else:
                logging.info("No valid troves found. Waiting...")
            
            # Short delay before next check
            time.sleep(15)
            
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(5)  # Short delay before retry

if __name__ == "__main__":
    main()