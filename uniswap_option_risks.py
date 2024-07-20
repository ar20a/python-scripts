import numpy as np
from scipy.stats import norm
from dataclasses import dataclass

@dataclass
class UniswapPosition:
    token_a: float  # Amount of token A
    token_b: float  # Amount of token B
    price: float    # Current price of token B in terms of token A
    fee_tier: float # Fee tier (e.g., 0.003 for 0.3%)

def calculate_uniswap_option_risks(position: UniswapPosition, days: int, risk_free_rate: float, volatility: float):
    # Calculate the constant product k
    k = position.token_a * position.token_b

    # Calculate the implied strike price (geometric mean of price range)
    strike = np.sqrt(k / (position.token_a * position.token_b))

    # Time to expiration in years
    T = days / 365

    # Calculate d1 and d2 for Black-Scholes
    d1 = (np.log(position.price / strike) + (risk_free_rate + 0.5 * volatility**2) * T) / (volatility * np.sqrt(T))
    d2 = d1 - volatility * np.sqrt(T)

    # Calculate option Greeks
    delta = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (position.price * volatility * np.sqrt(T))
    vega = position.price * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for percentage move
    theta = (-position.price * norm.pdf(d1) * volatility / (2 * np.sqrt(T)) 
             - risk_free_rate * strike * np.exp(-risk_free_rate * T) * norm.cdf(-d2)) / 365  # Daily theta

    # Adjust for Uniswap position size
    position_value = position.token_a + position.token_b * position.price
    adjustment_factor = position_value / (position.price * 100)  # Assuming standard option contract size of 100

    delta *= adjustment_factor
    gamma *= adjustment_factor
    vega *= adjustment_factor
    theta *= adjustment_factor

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta
    }

def calculate_impermanent_loss(price_change_ratio):
    return 2 * np.sqrt(price_change_ratio) / (1 + price_change_ratio) - 1

def main():
    # Example usage
    position = UniswapPosition(
        token_a=100000,  # 100,000 USDC
        token_b=1000,    # 1,000 ETH
        price=2000,      # Current ETH price: $2000
        fee_tier=0.003   # 0.3% fee tier
    )

    days = 30
    risk_free_rate = 0.01  # 1% annual risk-free rate
    volatility = 0.5       # 50% annualized volatility

    risks = calculate_uniswap_option_risks(position, days, risk_free_rate, volatility)

    print("Uniswap Liquidity Position:")
    print(f"Token A (USDC): {position.token_a}")
    print(f"Token B (ETH): {position.token_b}")
    print(f"Current Price: ${position.price}")
    print(f"Fee Tier: {position.fee_tier * 100}%")
    print("\nEquivalent Option Risk Metrics:")
    for greek, value in risks.items():
        print(f"{greek.capitalize()}: {value:.4f}")

    # Calculate and print impermanent loss for different price changes
    print("\nImpermanent Loss:")
    for price_change in [0.8, 0.9, 1.1, 1.2]:
        il = calculate_impermanent_loss(price_change)
        print(f"Price change: {price_change:.1f}x, Impermanent Loss: {il:.2%}")

if __name__ == "__main__":
    main()