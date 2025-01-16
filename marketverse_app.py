import pandas as pd
import random
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Initialize the game components
def initialize_game(num_players):
    players = pd.DataFrame({
        "Player ID": [f"Player_{i+1}" for i in range(num_players)],
        "Starting AOBucks": [10000] * num_players,
        "Remaining AOBucks": [10000] * num_players,
        "Portfolio Value": [0] * num_players,
        "Total Trades": [0] * num_players
    })

    assets = pd.DataFrame({
        "Asset Name": ["MemeOil", "MemeGold", "MemeGrain", "MemeCoffee", "MemeBeans"],
        "Starting Price": [50, 100, 30, 20, 40],
        "Current Price": [50, 100, 30, 20, 40],
        "Supply": [1000, 500, 2000, 1500, 1200],
        "Transactions": [0] * 5,
        "Reserve Ratio": [0.1, 0.2, 0.15, 0.05, 0.1]
    })

    transactions = pd.DataFrame(columns=[
        "Transaction ID", "Player ID", "Asset Name", "Buy/Sell", "Amount", "Transaction Fee", "Net AOBucks"
    ])
    
    return players, assets, transactions

# Simulate a single trade
def simulate_trade(players, assets, transactions, transaction_id):
    player = players.sample(1).iloc[0]
    asset = assets.sample(1).iloc[0]
    player_id = player["Player ID"]
    asset_name = asset["Asset Name"]

    action = random.choice(["Buy", "Sell"])
    max_trade_amount = min(player["Remaining AOBucks"] // asset["Current Price"], 10) if action == "Buy" else 5

    if max_trade_amount <= 0:
        return transactions  # Skip if no valid trade is possible

    trade_amount = random.randint(1, max_trade_amount)
    transaction_fee = trade_amount * asset["Current Price"] * 0.01
    net_aobucks = -trade_amount * asset["Current Price"] - transaction_fee if action == "Buy" else trade_amount * asset["Current Price"]

    players.loc[players["Player ID"] == player_id, "Remaining AOBucks"] += net_aobucks
    assets.loc[assets["Asset Name"] == asset_name, "Supply"] += trade_amount if action == "Sell" else -trade_amount
    assets.loc[assets["Asset Name"] == asset_name, "Transactions"] += 1

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
def simulate_game(num_players, days, transactions_per_day):
    players, assets, transactions = initialize_game(num_players)
    transaction_id = 1

    for day in range(1, days + 1):
        for _ in range(transactions_per_day):
            transactions = simulate_trade(players, assets, transactions, transaction_id)
            transaction_id += 1

        # Recalculate portfolio values at the end of each day
        for i, player in players.iterrows():
            player_assets = transactions[(transactions["Player ID"] == player["Player ID"]) & (transactions["Buy/Sell"] == "Buy")]
            portfolio_value = sum(player_assets["Amount"] * player_assets["Net AOBucks"])
            players.loc[i, "Portfolio Value"] = portfolio_value

    return players, assets, transactions

# Visualizations
def visualize_game(players, transactions, top_n=5):
    players["Net Gain/Loss"] = players["Remaining AOBucks"] + players["Portfolio Value"] - players["Starting AOBucks"]

    # Top Gainers and Losers
    top_gainers = players.nlargest(top_n, "Net Gain/Loss")
    top_losers = players.nsmallest(top_n, "Net Gain/Loss")

    # Bar Chart: Net Gain/Loss
    st.write("### Net Gain/Loss for All Players")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(players["Player ID"], players["Net Gain/Loss"], color=["green" if x > 0 else "red" for x in players["Net Gain/Loss"]])
    ax.set_title("Net Gain/Loss by Player", fontsize=14)
    ax.set_xlabel("Player ID", fontsize=12)
    ax.set_ylabel("Net Gain/Loss (AOBucks)", fontsize=12)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # Heatmap: Transaction Intensity
    st.write("### Transaction Intensity Heatmap")
    transaction_heatmap = transactions.pivot_table(
        index="Player ID", columns="Asset Name", values="Amount", aggfunc="sum", fill_value=0
    )
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(transaction_heatmap, annot=True, fmt=".0f", cmap="YlGnBu", cbar=True, ax=ax)
    ax.set_title("Transaction Intensity by Player and Asset", fontsize=14)
    st.pyplot(fig)

    # Individual Player Performance
    st.write("### Top Gainers and Losers")
    for idx, row in pd.concat([top_gainers, top_losers]).iterrows():
        player_id = row["Player ID"]
        player_transactions = transactions[transactions["Player ID"] == player_id]

        st.write(f"#### {player_id} - Net Gain/Loss: {row['Net Gain/Loss']:.2f}")
        st.write("Transaction Summary:")
        st.dataframe(player_transactions)
        st.write("---")

# Streamlit App
st.title("Marketverse Simulation")
st.write("Simulate a dynamic trading game in a chaotic AI-driven marketplace.")

# Configurable options
num_players = st.slider("Number of Players", min_value=5, max_value=50, value=10)
days = st.slider("Number of Days", min_value=1, max_value=14, value=7)
transactions_per_day = st.slider("Transactions per Day", min_value=10, max_value=500, value=100)

# Simulate the game
if st.button("Run Simulation"):
    players, assets, transactions = simulate_game(num_players, days, transactions_per_day)

    # Display Data
    st.write("### Players Data")
    st.dataframe(players)
    st.write("### Transactions Log")
    st.dataframe(transactions)

    # Visualize Results
    visualize_game(players, transactions)
