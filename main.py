import math
import pandas as pd
import yfinance as yf
import datetime

interest_free_rate = yf.download("^IRX")["Adj Close"] 
interest_free_rate = interest_free_rate.iloc[-1]/100


def black_scholes_volatility(S, K, T, option_price, option_type):
    """
    Calculates the implied volatility using the Black-Scholes formula.
    
    Parameters:
    S (float): Current price of the underlying asset
    K (float): Strike price of the option
    T (float): Time to expiration in years
    option_price (float): Observed market price of the option
    option_type (str): Type of the option, either "call" or "put"
    
    Returns:
    float: Implied volatility
    """
    epsilon = 1e-6
    max_iterations = 100
    sigma = 0.5
    
    for i in range(max_iterations):
        if T < 0:
            T = abs(T)
        d1 = (math.log(S / K) + (interest_free_rate + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if option_type == "call":
            option_price_calculated = S * norm_cdf(d1) - K * math.exp(-interest_free_rate * T) * norm_cdf(d2)
        elif option_type == "put":
            option_price_calculated = K * math.exp(-interest_free_rate * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
        else:
            raise ValueError("Invalid option type")
        
        vega = S * norm_pdf(d1) * math.sqrt(T)
        
        if abs(option_price_calculated - option_price) < epsilon:
            return sigma
        
        sigma -= (option_price_calculated - option_price) / vega
    
    return None

def norm_cdf(x):
    """Calculates the cumulative distribution function of the standard normal distribution."""
    return (1 + math.erf(x / math.sqrt(2))) / 2

def norm_pdf(x):
    """Calculates the probability density function of the standard normal distribution."""
    return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

stocks = input("Stock symbol:")
stock = yf.Ticker(stocks)

opt = stock.option_chain(stock.options[0])

closest_call = opt.calls.loc[opt.calls['inTheMoney'] == True].iloc[::-1].iloc[0]
closest_put = opt.puts.loc[opt.puts['inTheMoney'] == True].iloc[0]

closest_call_price = closest_call['lastPrice']
closest_put_price = closest_put['lastPrice']

# Calculate days to expiration
expiration_date = datetime.datetime.strptime(stock.options[0], '%Y-%m-%d')
time_to_expiration = (expiration_date - datetime.datetime.today()).days / 365


# Implied volatility of both call and put
implied_vol_call = black_scholes_volatility(stock.history(period="1d")['Close'].iloc[0], closest_call['strike'], time_to_expiration, closest_call_price, "call")
implied_vol_put = black_scholes_volatility(stock.history(period="1d")['Close'].iloc[0], closest_put['strike'], time_to_expiration, closest_put_price, "put")

print(f"Implied volatility of call: {implied_vol_call*100:.2f}%")
print(f"Implied volatility of put: {implied_vol_put*100:.2f}%")

#Expected move calculation
if time_to_expiration < 0:
    time_to_expiration = abs(time_to_expiration)
expected_move_high = stock.history(period="1d")['Close'].iloc[0] * math.exp(implied_vol_call * math.sqrt(time_to_expiration))
expected_move_low = stock.history(period="1d")['Close'].iloc[0] / math.exp(implied_vol_put * math.sqrt(time_to_expiration))

print(f"{stock.info['longName'].upper()} price: {stock.history(period='1d')['Close'].iloc[0]:.2f}")
print(f"Expected move high of {abs(stock.history(period='1d')['Close'].iloc[0] - expected_move_high):.2f} to : {expected_move_high:.2f}. Expected move low of {stock.history(period='1d')['Close'].iloc[0] - expected_move_low:.2f} to: {expected_move_low:.2f}")
