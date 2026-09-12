"""Analysis script for AppleSupport conversations in twcs.csv."""
import pandas as pd
import numpy as np
from pathlib import Path
import json

print("Reading twcs.csv...")
df = pd.read_csv("twcs.csv", dtype={"tweet_id": str, "author_id": str, "response_tweet_id": str, "in_response_to_tweet_id": str})
print(f"Total rows in twcs.csv: {len(df):,}")

# Filter AppleSupport
# 1. Outbound tweets from AppleSupport
apple_outbound = df[df["author_id"] == "AppleSupport"]
print(f"Total outbound tweets from AppleSupport: {len(apple_outbound):,}")

# 2. Inbound tweets mentioning AppleSupport or responded to by AppleSupport
apple_inbound_mention = df[df["text"].str.contains(r"@AppleSupport", case=False, na=False)]
print(f"Total tweets mentioning @AppleSupport: {len(apple_inbound_mention):,}")

# Check tweet directions
inbound_apple = df[df["text"].str.contains(r"@AppleSupport", case=False, na=False) & (df["inbound"] == True)]
print(f"Total inbound tweets mentioning @AppleSupport: {len(inbound_apple):,}")

# Look at response relationships:
# A pair is customer inbound tweet -> AppleSupport outbound response
# Let's map response_tweet_id and in_response_to_tweet_id
apple_outbound_dict = apple_outbound.set_index("tweet_id").to_dict(orient="index")

# Find inbound tweets where in_response_to_tweet_id is NaN (conversation starters) vs replies
inbound_starters = inbound_apple[inbound_apple["in_response_to_tweet_id"].isna()]
print(f"Inbound conversation starters mentioning AppleSupport: {len(inbound_starters):,}")

# Find pairs where AppleSupport responded directly to inbound tweets
# Case A: inbound tweet's response_tweet_id is an AppleSupport tweet
# Case B: AppleSupport tweet's in_response_to_tweet_id is an inbound tweet
apple_responses_to_inbound = df[(df["author_id"] == "AppleSupport") & (df["in_response_to_tweet_id"].notna())]
print(f"AppleSupport responses with valid in_response_to_tweet_id: {len(apple_responses_to_inbound):,}")

# Let's match: inbound tweet -> AppleSupport response
merged = apple_responses_to_inbound.merge(
    df[["tweet_id", "author_id", "inbound", "created_at", "text", "in_response_to_tweet_id"]],
    left_on="in_response_to_tweet_id",
    right_on="tweet_id",
    suffixes=("_apple", "_customer")
)
print(f"Direct matched (Customer Inbound -> Apple Response) pairs: {len(merged):,}")
print("Sample matched pairs:")
for i, r in merged.head(5).iterrows():
    print(f"\n[Customer {r['author_id_customer']}]: {r['text_customer']}")
    print(f"[AppleSupport]: {r['text_apple']}")
