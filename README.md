# DeFi python scripts

This repository contains python utility scripts to be built upon

1. `liquity_position_info.py`: Analyzes Liquity protocol positions
2. `python_defi_strategy_comparison.py`: Compares different DeFi strategies
3. `uniswap_option_risks.py`: Calculates option-like risks for Uniswap positions

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository
2. (Optional but recommended) Create a virtual environment:

	python -m venv venv
	source venv/bin/activate  # On Windows, use venv\Scripts\activate
	
3. Install the required packages:

	pip install -r requirements.txt
	
	Alternatively, if you have npm installed, you can use:
	
	npm run install-deps
	
## Usage

### 1. Liquity Position Info

This script fetches and displays Liquity protocol position details for a given Ethereum address.

Run the script: python liquity_position_info.py

You will be prompted to enter an Ethereum address. The script will then display information about the address's Trove, Stability Pool deposit, and LQTY stake.

### 2. DeFi Strategy Comparison

This script simulates and compares different DeFi strategies.

Run the script: python python_defi_strategy_comparison.py

The script will run simulations for various market conditions and display metrics and visualizations comparing the strategies.

### 3. Uniswap Option Risks

This script calculates option-like risk metrics for Uniswap V2 liquidity positions.

Run the script: python uniswap_option_risks.py

The script will output equivalent option risk metrics for a sample Uniswap position. You can modify the position parameters in the script to analyze different scenarios.

## Note

Make sure you have the necessary ABI files (`TroveManager.json`, `StabilityPool.json`, and `LQTYStaking.json`) in the same directory as the `liquity_position_info.py` script.

For the `liquity_position_info.py` script, you need to replace `YOUR_INFURA_PROJECT_ID` in the script with your actual Infura project ID.

