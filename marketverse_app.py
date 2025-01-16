import pandas as pd
import random
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Initialize the game components
def initialize_game():
    players = pd.DataFrame({
        "Player ID": [f"Player_{i+1}" for i in range(10)],  # 10 players
        "Starting AOBucks": [10000] * 10,
        "Remaining AOBucks": [10000] * 10,
        "Portfolio Value": [0] * 10,
        "Total Trades": [0] * 10
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

# Simulate the game for multiple days
def simulate_game(days=7):
    players, assets, transactions = initialize_game()
    transaction_id = 1

    for day in range(1, days + 1):
        for _ in range(100):  # Number of transactions per day
            transactions = simulate_trade(players, assets, transactions, transaction_id)
            transaction_id += 1

        # Recalculate portfolio values at the end of each day
        for i, player in players.iterrows():
            player_assets = transactions[(transactions["Player ID"] == player["Player ID"]) & (transactions["Buy/Sell"] == "Buy")]
            portfolio_value = sum(player_assets["Amount"] * player_assets["Net AOBucks"])
            players.loc[i, "Portfolio Value"] = portfolio_value

    return players, assets, transactions

# Visualizations
def show_visualizations(players, assets, transactions):
    # Bar Chart: Net Gain/Loss
    players["Net Gain/Loss"] = players["Remaining AOBucks"] + players["Portfolio Value"] - players["Starting AOBucks"]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(players["Player ID"], players["Net Gain/Loss"], color=["green" if x > 0 else "red" for x in players["Net Gain/Loss"]])
    ax.set_title("Net Gain/Loss for Each Player", fontsize=14)
    ax.set_xlabel("Player ID", fontsize=12)
    ax.set_ylabel("Net Gain/Loss (AOBucks)", fontsize=12)
    st.pyplot(fig)

    # Heatmap: Transaction Intensity
    transaction_heatmap = transactions.pivot_table(
        index="Player ID", columns="Asset Name", values="Amount", aggfunc="sum", fill_value=0
    )
    st.write("### Transaction Intensity Heatmap")
    st.write(sns.heatmap(transaction_heatmap, annot=True, fmt=".0f", cmap="YlGnBu", cbar=True).figure)

# Streamlit App
st.title("Marketverse Simulation App")
st.write("Simulate a 7-day trading game in the chaotic Marketverse arena.")

# Simulate the game
if st.button("Run Simulation"):
    players, assets, transactions = simulate_game()
    st.write("### Players Data")
    st.dataframe(players)
    st.write("### Assets Data")
    st.dataframe(assets)
    st.write("### Transactions Log")
    st.dataframe(transactions)

    # Show visualizations
    show_visualizations(players, assets, transactions)
