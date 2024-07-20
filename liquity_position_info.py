import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import requests
from datetime import datetime, timedelta

# Setup web3 connection
INFURA_URL = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Contract addresses
TROVE_MANAGER_ADDRESS = "0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2"
STABILITY_POOL_ADDRESS = "0x66017D22b0f8556afDd19FC67041899Eb65a21bb"
LQTY_STAKING_ADDRESS = "0x4f9Fbb3f1E99B56e0Fe2892e623Ed36A76Fc605d"

# ABI files (you need to have these JSON files in the same directory)
with open("TroveManager.json") as f:
    TROVE_MANAGER_ABI = json.load(f)
with open("StabilityPool.json") as f:
    STABILITY_POOL_ABI = json.load(f)
with open("LQTYStaking.json") as f:
    LQTY_STAKING_ABI = json.load(f)

# Initialize contracts
trove_manager = w3.eth.contract(address=TROVE_MANAGER_ADDRESS, abi=TROVE_MANAGER_ABI)
stability_pool = w3.eth.contract(address=STABILITY_POOL_ADDRESS, abi=STABILITY_POOL_ABI)
lqty_staking = w3.eth.contract(address=LQTY_STAKING_ADDRESS, abi=LQTY_STAKING_ABI)

def get_trove_info(address):
    trove = trove_manager.functions.Troves(address).call()
    coll = trove[1] / 1e18
    debt = trove[0] / 1e18
    status = trove[3]
    
    if status == 1:  # Active trove
        price = get_eth_price()
        collateral_ratio = (coll * price) / debt if debt > 0 else float('inf')
        return {
            "collateral": coll,
            "debt": debt,
            "collateral_ratio": collateral_ratio,
            "status": "Active"
        }
    else:
        return {"status": "Not active"}

def get_stability_pool_deposit(address):
    deposit = stability_pool.functions.getCompoundedLUSDDeposit(address).call() / 1e18
    return deposit

def get_lqty_stake(address):
    stake = lqty_staking.functions.stakes(address).call() / 1e18
    return stake

def get_eth_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return data["ethereum"]["usd"]

def get_lqty_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=liquity&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return data["liquity"]["usd"]

def calculate_apr(initial_balance, current_balance, days):
    if initial_balance == 0:
        return 0
    daily_rate = (current_balance / initial_balance) ** (1/days) - 1
    apr = ((1 + daily_rate) ** 365) - 1
    return apr * 100

def get_historical_balance(address, contract, days_ago):
    current_block = w3.eth.get_block('latest')['number']
    blocks_per_day = 24 * 60 * 60 / 15  # Assuming 15 seconds per block
    past_block = int(current_block - (blocks_per_day * days_ago))
    
    past_balance = contract.functions.getCompoundedLUSDDeposit(address).call(block_identifier=past_block) / 1e18
    return past_balance

def main():
    address = input("Enter Ethereum address: ")
    address = Web3.to_checksum_address(address)

    print("\nFetching Liquity position details...\n")

    # Trove information
    trove_info = get_trove_info(address)
    if trove_info["status"] == "Active":
        print(f"Trove Status: Active")
        print(f"Collateral: {trove_info['collateral']:.4f} ETH")
        print(f"Debt: {trove_info['debt']:.4f} LUSD")
        print(f"Collateral Ratio: {trove_info['collateral_ratio']:.2%}")
    else:
        print("Trove Status: Not active")

    # Stability Pool
    stability_pool_deposit = get_stability_pool_deposit(address)
    print(f"\nStability Pool Deposit: {stability_pool_deposit:.4f} LUSD")

    # Calculate Stability Pool APR
    days_ago = 365
    past_deposit = get_historical_balance(address, stability_pool, days_ago)
    stability_pool_apr = calculate_apr(past_deposit, stability_pool_deposit, days_ago)
    print(f"Estimated Stability Pool APR (last {days_ago} days): {stability_pool_apr:.2f}%")

    # LQTY Staking
    lqty_stake = get_lqty_stake(address)
    lqty_price = get_lqty_price()
    print(f"\nLQTY Stake: {lqty_stake:.4f} LQTY (${lqty_stake * lqty_price:.2f})")

    # We can't easily calculate LQTY staking APR without more complex historical data
    print("Note: LQTY staking APR calculation requires more complex historical data and is not included in this script.")

if __name__ == "__main__":
    main()