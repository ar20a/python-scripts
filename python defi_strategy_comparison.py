import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from scipy.stats import norm

@dataclass
class UniswapPosition:
    token_a_amount: float
    token_b_amount: float
    initial_price: float
    fee_tier: float

@dataclass
class CoveredCallPosition:
    underlying_amount: float
    strike_price: float
    premium: float
    days_to_expiration: int

@dataclass
class MarketCondition:
    volatility: float
    drift: float

def calculate_uniswap_value(position: UniswapPosition, current_price: float, days: int) -> float:
    k = position.token_a_amount * position.token_b_amount
    sqrt_price = np.sqrt(current_price)
    sqrt_initial_price = np.sqrt(position.initial_price)
    
    token_a = k / (sqrt_price * sqrt_initial_price)
    token_b = k / (sqrt_price / sqrt_initial_price)
    
    # Calculate fees earned
    volume = k * abs(sqrt_price - sqrt_initial_price) / (sqrt_price * sqrt_initial_price)
    fees_earned = volume * position.fee_tier * days / 365
    
    return token_a + token_b * current_price + fees_earned

def black_scholes_call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def calculate_covered_call_value(position: CoveredCallPosition, current_price: float, days: int, r: float, sigma: float) -> float:
    T = (position.days_to_expiration - days) / 365
    if T <= 0:
        return max(current_price, position.strike_price) * position.underlying_amount
    
    call_value = black_scholes_call(current_price, position.strike_price, T, r, sigma)
    return position.underlying_amount * current_price - position.underlying_amount * call_value + position.premium

def heston_model(S0, v0, kappa, theta, sigma, rho, T, steps, num_paths):
    dt = T / steps
    prices = np.zeros((num_paths, steps + 1))
    variances = np.zeros((num_paths, steps + 1))
    prices[:, 0] = S0
    variances[:, 0] = v0
    
    for i in range(1, steps + 1):
        dW1 = np.random.normal(0, np.sqrt(dt), num_paths)
        dW2 = rho * dW1 + np.sqrt(1 - rho**2) * np.random.normal(0, np.sqrt(dt), num_paths)
        
        variances[:, i] = np.maximum(variances[:, i-1] + kappa * (theta - variances[:, i-1]) * dt + sigma * np.sqrt(variances[:, i-1]) * dW1, 0)
        prices[:, i] = prices[:, i-1] * np.exp(np.sqrt(variances[:, i-1]) * dW2 - 0.5 * variances[:, i-1] * dt)
    
    return prices, variances

def simulate_prices(initial_price: float, market_condition: MarketCondition, days: int, num_simulations: int) -> np.ndarray:
    # Use Heston model for more sophisticated price simulation
    v0 = market_condition.volatility ** 2
    kappa = 2  # Mean reversion speed
    theta = v0  # Long-term variance
    sigma = 0.5  # Volatility of volatility
    rho = -0.7  # Correlation between asset returns and variance
    
    prices, _ = heston_model(initial_price, v0, kappa, theta, sigma, rho, days/365, days, num_simulations)
    return prices

def calculate_metrics(values: np.ndarray, initial_investment: float) -> dict:
    returns = (values[:, -1] - initial_investment) / initial_investment
    return {
        "mean_return": np.mean(returns),
        "std_dev": np.std(returns),
        "max_drawdown": np.max((np.maximum.accumulate(values) - values) / np.maximum.accumulate(values)),
        "sharpe_ratio": np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0,
        "sortino_ratio": np.mean(returns) / np.std(returns[returns < 0]) if np.std(returns[returns < 0]) != 0 else 0
    }

# Simulation parameters
initial_price = 100
days = 30
num_simulations = 10000

# Market conditions
bull_market = MarketCondition(volatility=0.2, drift=0.1)
bear_market = MarketCondition(volatility=0.4, drift=-0.1)
sideways_market = MarketCondition(volatility=0.1, drift=0)

market_conditions = [bull_market, bear_market, sideways_market]
market_names = ["Bull", "Bear", "Sideways"]

# Create positions
uniswap_position = UniswapPosition(token_a_amount=10000, token_b_amount=100, initial_price=initial_price, fee_tier=0.003)
covered_call_position = CoveredCallPosition(underlying_amount=100, strike_price=110, premium=5 * 100, days_to_expiration=30)

# Transaction costs and gas fees (in USD)
uniswap_entry_cost = 50
uniswap_exit_cost = 50
option_entry_cost = 20
option_exit_cost = 20

# Risk-free rate
risk_free_rate = 0.02

for market_condition, market_name in zip(market_conditions, market_names):
    print(f"\n{market_name} Market Simulation:")
    
    # Simulate prices
    price_paths = simulate_prices(initial_price, market_condition, days, num_simulations)

    # Calculate values for both strategies
    uniswap_values = np.apply_along_axis(lambda x: [calculate_uniswap_value(uniswap_position, price, i) for i, price in enumerate(x)], 1, price_paths)
    covered_call_values = np.apply_along_axis(lambda x: [calculate_covered_call_value(covered_call_position, price, i, risk_free_rate, market_condition.volatility) for i, price in enumerate(x)], 1, price_paths)

    # Apply transaction costs and gas fees
    uniswap_values -= uniswap_entry_cost
    uniswap_values[:, -1] -= uniswap_exit_cost
    covered_call_values -= option_entry_cost
    covered_call_values[:, -1] -= option_exit_cost

    # Calculate metrics
    initial_investment = uniswap_position.token_a_amount + uniswap_position.token_b_amount * initial_price
    uniswap_metrics = calculate_metrics(uniswap_values, initial_investment)
    covered_call_metrics = calculate_metrics(covered_call_values, initial_investment)

    # Print results
    print("\nUniswap LP Metrics:")
    for key, value in uniswap_metrics.items():
        print(f"{key}: {value:.4f}")

    print("\nCovered Call Metrics:")
    for key, value in covered_call_metrics.items():
        print(f"{key}: {value:.4f}")

    # Visualize results
    plt.figure(figsize=(12, 6))
    plt.plot(np.mean(uniswap_values, axis=0), label="Uniswap LP")
    plt.plot(np.mean(covered_call_values, axis=0), label="Covered Call")
    plt.xlabel("Days")
    plt.ylabel("Value")
    plt.title(f"Average Value over Time - {market_name} Market")
    plt.legend()
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.hist(uniswap_values[:, -1], bins=50, alpha=0.5, label="Uniswap LP")
    plt.hist(covered_call_values[:, -1], bins=50, alpha=0.5, label="Covered Call")
    plt.xlabel("Final Value")
    plt.ylabel("Frequency")
    plt.title(f"Distribution of Final Values - {market_name} Market")
    plt.legend()
    plt.show()

# Compare with another DeFi strategy: Aave lending
def calculate_aave_value(initial_amount: float, apy: float, days: int) -> float:
    return initial_amount * (1 + apy) ** (days / 365)

aave_apy = 0.05  # 5% APY
aave_values = np.array([calculate_aave_value(initial_investment, aave_apy, days) for _ in range(num_simulations)])

print("\nAave Lending Metrics:")
aave_metrics = calculate_metrics(aave_values.reshape(-1, 1), initial_investment)
for key, value in aave_metrics.items():
    print(f"{key}: {value:.4f}")

plt.figure(figsize=(12, 6))
plt.hist(uniswap_values[:, -1], bins=50, alpha=0.5, label="Uniswap LP")
plt.hist(covered_call_values[:, -1], bins=50, alpha=0.5, label="Covered Call")
plt.hist(aave_values, bins=50, alpha=0.5, label="Aave Lending")
plt.xlabel("Final Value")
plt.ylabel("Frequency")
plt.title("Distribution of Final Values - All Strategies")
plt.legend()
plt.show()