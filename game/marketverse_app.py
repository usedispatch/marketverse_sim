import pandas as pd
import random
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Strategies
def random_strategy(player, asset):
    """Randomly decide to Buy or Sell."""
    return random.choice(["Buy", "Sell"])

def greedy_strategy(player, asset):
    """Greedy strategy: Buy when price is low, sell when price is high."""
    if asset["Current Price"] < asset["Starting Price"] * 1.1:  # Buy if price is 10% below starting price
        return "Buy"
    else:
        return "Sell"

def risk_averse_strategy(player, asset):
    """Risk-averse strategy: Hold AOBucks and avoid frequent trades."""
    if player["Remaining AOBucks"] > asset["Current Price"] * 2:  # Only buy if plenty of funds
        return "Buy"
    else:
        return "Sell"

# Initialize the game components
def initialize_game(num_players, starting_aobucks, assets_config, strategies):
    players = pd.DataFrame({
        "Player ID": [f"Player_{i+1}" for i in range(num_players)],
        "Starting AOBucks": [starting_aobucks] * num_players,
        "Remaining AOBucks": [starting_aobucks] * num_players,
        "Portfolio Value": [0] * num_players,
        "Total Trades": [0] * num_players,
        "Strategy": [random.choice(strategies) for _ in range(num_players)]
    })

    assets = pd.DataFrame({
        "Asset Name": [asset["name"] for asset in assets_config],
        "Starting Price": [asset["starting_price"] for asset in assets_config],
        "Current Price": [asset["starting_price"] for asset in assets_config],
        "Supply": [asset["supply"] for asset in assets_config],
        "Scaling Factor": [asset["scaling_factor"] for asset in assets_config],
        "Transactions": [0] * len(assets_config),
    })

    transactions = pd.DataFrame(columns=[
        "Transaction ID", "Player ID", "Asset Name", "Buy/Sell", "Amount", "Transaction Fee", "Net AOBucks"
    ])

    price_trends = pd.DataFrame({asset["name"]: [asset["starting_price"]] for asset in assets_config})

    return players, assets, transactions, price_trends

# Update prices based on bonding curve
def update_prices(assets):
    assets["Current Price"] = assets["Starting Price"] + (assets["Supply"] ** 2) * assets["Scaling Factor"]

# Simulate a single trade
def simulate_trade(players, assets, transactions, transaction_id, max_trade_amount):
    player = players.sample(1).iloc[0]
    asset = assets.sample(1).iloc[0]
    player_id = player["Player ID"]
    asset_name = asset["Asset Name"]
    strategy = player["Strategy"]

    # Execute strategy
    action = strategy(player, asset)

    max_trade_amount = int(min(player["Remaining AOBucks"] // asset["Current Price"], max_trade_amount)) if action == "Buy" else int(max_trade_amount)

    if max_trade_amount <= 0:
        return transactions  # Skip if no valid trade is possible

    trade_amount = random.randint(1, max_trade_amount)
    transaction_fee = trade_amount * asset["Current Price"] * 0.01
    net_aobucks = -trade_amount * asset["Current Price"] - transaction_fee if action == "Buy" else trade_amount * asset["Current Price"]

    players.loc[players["Player ID"] == player_id, "Remaining AOBucks"] += net_aobucks
    players.loc[players["Player ID"] == player_id, "Total Trades"] += 1
    assets.loc[assets["Asset Name"] == asset_name, "Supply"] += trade_amount if action == "Sell" else -trade_amount
    assets.loc[assets["Asset Name"] == asset_name, "Supply"] = assets.loc[assets["Asset Name"] == asset_name, "Supply"].clip(lower=0)
    update_prices(assets)  # Update prices dynamically

    transactions = pd.concat([transactions, pd.DataFrame([{
        "Transaction ID": transaction_id,
        "Player ID": player_id,
        "Asset Name": asset_name,
        "Buy/Sell": action,
        "Amount": trade_amount,
        "Transaction Fee": transaction_fee,
        "Net AOBucks": net_aobucks
    }])], ignore_index=True)

    return transactions

# Simulate the game
def simulate_game(num_players, starting_aobucks, days, transactions_per_day, max_trade_amount, assets_config, strategies):
    players, assets, transactions, price_trends = initialize_game(num_players, starting_aobucks, assets_config, strategies)
    transaction_id = 1

    for day in range(1, days + 1):
        for _ in range(transactions_per_day):
            transactions = simulate_trade(players, assets, transactions, transaction_id, max_trade_amount)
            transaction_id += 1

        # Record current prices for each asset
        price_trends.loc[day] = assets["Current Price"].values

        # Recalculate portfolio values at the end of each day
        for i, player in players.iterrows():
            portfolio_value = sum(
                transactions[(transactions["Player ID"] == player["Player ID"]) & (transactions["Buy/Sell"] == "Buy") & (transactions["Asset Name"] == asset)]["Amount"].sum()
                * assets[assets["Asset Name"] == asset]["Current Price"].values[0]
                for asset in assets["Asset Name"]
            )
            players.loc[i, "Portfolio Value"] = portfolio_value

    return players, assets, transactions, price_trends

# Generate performance summaries
def performance_summary(players, transactions, top_n=5):
    players["Net Gain/Loss"] = players["Remaining AOBucks"] + players["Portfolio Value"] - players["Starting AOBucks"]
    top_gainers = players.nlargest(top_n, "Net Gain/Loss")
    top_losers = players.nsmallest(top_n, "Net Gain/Loss")
    return top_gainers, top_losers

# Visualizations
def visualize_game(players, assets, transactions, top_gainers, top_losers, price_trends):
    st.write("### Net Gain/Loss Overview")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=players["Strategy"].apply(lambda x: x.__name__), y=players["Net Gain/Loss"], ax=ax, ci=None)
    ax.set_title("Net Gain/Loss by Strategy", fontsize=14)
    ax.set_xlabel("Strategy", fontsize=12)
    ax.set_ylabel("Net Gain/Loss (AOBucks)", fontsize=12)
    st.pyplot(fig)

    st.write("### Winners and Losers Breakdown")
    st.dataframe(top_gainers)
    st.dataframe(top_losers)

    st.write("### Asset Price Trends")
    fig, ax = plt.subplots(figsize=(12, 6))
    for column in price_trends.columns:
        ax.plot(price_trends.index, price_trends[column], label=column)
    ax.set_title("Price Trends of Assets Over Time", fontsize=14)
    ax.set_xlabel("Day", fontsize=12)
    ax.set_ylabel("Price (AOBucks)", fontsize=12)
    ax.legend(title="Assets")
    st.pyplot(fig)

# Streamlit App
st.title("Marketverse Simulation")
st.write("Simulate a dynamic trading game in a chaotic AI-driven marketplace.")

# Configurable asset parameters
st.write("### Configure Assets")
num_assets = st.slider("Number of Assets", min_value=1, max_value=10, value=5)
assets_config = []
for i in range(num_assets):
    st.write(f"#### Asset {i+1}")
    name = st.text_input(f"Asset {i+1} Name", value=f"MemeAsset_{i+1}")
    starting_price = st.number_input(f"Starting Price of {name}", min_value=1, value=50)
    supply = st.number_input(f"Initial Supply of {name}", min_value=1, value=1000)
    scaling_factor = st.number_input(f"Scaling Factor of {name}", min_value=0.01, value=0.1)
    assets_config.append({"name": name, "starting_price": starting_price, "supply": supply, "scaling_factor": scaling_factor})

# Configurable player parameters
st.write("### Configure Players")
num_players = st.slider("Number of Players", min_value=5, max_value=50, value=10)
starting_aobucks = st.slider("Starting AOBucks", min_value=1000, max_value=50000, value=10000)

# Configurable simulation parameters
st.write("### Configure Simulation")
days = st.slider("Number of Days", min_value=1, max_value=14, value=7)
transactions_per_day = st.slider("Transactions per Day", min_value=10, max_value=500, value=100)
max_trade_amount = st.slider("Max Trade Amount", min_value=1, max_value=50, value=10)

# Assign strategies
strategies = [random_strategy, greedy_strategy, risk_averse_strategy]

# Run Simulation
if st.button("Run Simulation"):
    players, assets, transactions, price_trends = simulate_game(
        num_players, starting_aobucks, days, transactions_per_day, max_trade_amount, assets_config, strategies
    )
    top_gainers, top_losers = performance_summary(players, transactions)
    st.write("### Players Data")
    st.dataframe(players)
    st.write("### Transactions Log")
    st.dataframe(transactions)
    visualize_game(players, assets, transactions, top_gainers, top_losers, price_trends)