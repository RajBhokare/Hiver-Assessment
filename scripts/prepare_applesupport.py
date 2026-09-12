"""Comprehensive data extraction, conversation reconstruction, cleaning,
zero-leakage splitting, and intent analysis for AppleSupport.
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np

# Force UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 60)
    print("STEP 1: Ingesting twcs.csv and inspecting schema")
    print("=" * 60)
    
    twcs_path = Path("twcs.csv")
    if not twcs_path.exists():
        raise FileNotFoundError("twcs.csv not found in root directory!")
    
    # Read relevant columns with string types
    df = pd.read_csv(
        twcs_path,
        dtype={
            "tweet_id": str,
            "author_id": str,
            "inbound": bool,
            "created_at": str,
            "text": str,
            "response_tweet_id": str,
            "in_response_to_tweet_id": str,
        }
    )
    
    total_tweets = len(df)
    print(f"Total rows in twcs.csv: {total_tweets:,}")
    print(f"Columns: {list(df.columns)}")
    
    # ---------------------------------------------------------
    # STEP 2: Filter AppleSupport Ecosystem Tweets
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2: Filtering AppleSupport inbound and outbound tweets")
    print("=" * 60)
    
    # Outbound tweets authored by AppleSupport
    apple_outbound = df[df["author_id"] == "AppleSupport"].copy()
    print(f"Outbound tweets from @AppleSupport: {len(apple_outbound):,}")
    
    # Inbound tweets authored by users mentioning AppleSupport or responded to by AppleSupport
    # First, get all tweet IDs where Apple responded
    apple_replied_to_ids = set(apple_outbound["in_response_to_tweet_id"].dropna().unique())
    print(f"Unique parent tweet IDs replied to by AppleSupport: {len(apple_replied_to_ids):,}")
    
    # All inbound tweets related to Apple
    apple_inbound = df[
        (df["inbound"] == True) & 
        (df["text"].str.contains(r"@AppleSupport", case=False, na=False) | df["tweet_id"].isin(apple_replied_to_ids))
    ].copy()
    print(f"Total relevant AppleSupport inbound tweets: {len(apple_inbound):,}")
    
    # ---------------------------------------------------------
    # STEP 3: Pair Customer Inbound with Historical Apple Response
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 3: Matching Inbound Customer Messages to AppleSupport Responses")
    print("=" * 60)
    
    # Merge on inbound tweet_id == outbound in_response_to_tweet_id
    # Note: Some outbound responses have multiple responses or multiple inbound tweets
    # We match each customer inbound tweet to the direct first AppleSupport reply
    apple_outbound_valid = apple_outbound[apple_outbound["in_response_to_tweet_id"].notna()].copy()
    
    # Sort by created_at if possible to ensure chronological ordering
    pairs = apple_inbound.merge(
        apple_outbound_valid[["tweet_id", "author_id", "created_at", "text", "in_response_to_tweet_id"]],
        left_on="tweet_id",
        right_on="in_response_to_tweet_id",
        suffixes=("_customer", "_apple")
    )
    print(f"Raw Customer-Message -> Apple-Response pairs: {len(pairs):,}")
    
    # ---------------------------------------------------------
    # STEP 4: Conversation Reconstruction and Context Mapping
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 4: Conversation Thread Reconstruction & Turn Detection")
    print("=" * 60)
    
    # Map tweet_id to parent tweet_id to trace conversation roots
    # Build a parent lookup table from the full df
    parent_map = df.set_index("tweet_id")["in_response_to_tweet_id"].dropna().to_dict()
    
    def find_root_tweet(tweet_id: str, max_depth: int = 15) -> str:
        curr = tweet_id
        depth = 0
        while curr in parent_map and depth < max_depth:
            parent = parent_map[curr]
            if parent == curr: # loop prevention
                break
            curr = parent
            depth += 1
        return curr
    
    # Assign conversation_id (root tweet_id)
    print("Tracing root conversation IDs for leakage prevention...")
    pairs["conversation_id"] = pairs["tweet_id_customer"].apply(find_root_tweet)
    pairs["is_conversation_starter"] = pairs["in_response_to_tweet_id_customer"].isna()
    
    print(f"Unique conversation threads (roots): {pairs['conversation_id'].nunique():,}")
    print(f"Direct conversation starters: {pairs['is_conversation_starter'].sum():,} ({pairs['is_conversation_starter'].mean()*100:.1f}%)")
    print(f"Follow-up / multi-turn turns: {(~pairs['is_conversation_starter']).sum():,} ({(~pairs['is_conversation_starter']).mean()*100:.1f}%)")
    
    # ---------------------------------------------------------
    # STEP 5: Cleaning and Deduplication
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 5: Cleaning, Normalization & Deduplication")
    print("=" * 60)
    
    def clean_tweet_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        # Remove user handles like @AppleSupport, @115854, etc.
        cleaned = re.sub(r"@\w+", "", text)
        # Normalize URLs (replace with token or keep domain)
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        # Decode HTML entities
        cleaned = cleaned.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        # Remove excessive whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    pairs["clean_customer_text"] = pairs["text_customer"].apply(clean_tweet_text)
    pairs["clean_apple_text"] = pairs["text_apple"].apply(clean_tweet_text)
    
    # Filter 1: Empty text after handle/URL removal (e.g., tweets containing only screenshot URL or handles)
    initial_count = len(pairs)
    valid_text_mask = pairs["clean_customer_text"].str.len() >= 5
    pairs_cleaned = pairs[valid_text_mask].copy()
    print(f"Removed {initial_count - len(pairs_cleaned):,} messages with <5 chars of actual text (e.g. only handles/URLs).")
    
    # Filter 2: Exact duplicate customer queries within same conversation or bot loops
    before_dedup = len(pairs_cleaned)
    # Deduplicate based on (clean_customer_text, author_id_customer) to prevent user spamming exact same text
    pairs_cleaned = pairs_cleaned.drop_duplicates(subset=["clean_customer_text", "author_id_customer"]).copy()
    print(f"Removed {before_dedup - len(pairs_cleaned):,} duplicate customer messages from same user.")
    
    # Filter 3: General exact text duplicates across dataset if identical
    before_global_dedup = len(pairs_cleaned)
    # Keep first occurrence of identical clean customer text to avoid skewed frequency from viral copypastas
    pairs_cleaned = pairs_cleaned.drop_duplicates(subset=["clean_customer_text"]).copy()
    print(f"Removed {before_global_dedup - len(pairs_cleaned):,} exact global duplicate texts.")
    print(f"Remaining high-quality unique pairs: {len(pairs_cleaned):,}")
    
    # ---------------------------------------------------------
    # STEP 6: Zero-Leakage Dataset Splitting (By Conversation & User)
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 6: Splitting by User/Conversation (Zero Leakage)")
    print("=" * 60)
    
    # To prevent ANY conversation leakage or user-specific style/issue leakage,
    # we split on author_id_customer (User ID). Since each conversation is authored by a user,
    # splitting by user ID strictly guarantees BOTH zero conversation leakage AND zero user leakage!
    # Group users and conversations into connected components so that
    # any conversation that touches multiple users, or any user that has multiple conversations,
    # stays 100% within the exact same split.
    from collections import defaultdict
    
    adj = defaultdict(set)
    for _, row in pairs_cleaned.iterrows():
        u = f"user_{row['author_id_customer']}"
        c = f"conv_{row['conversation_id']}"
        adj[u].add(c)
        adj[c].add(u)
        
    visited = set()
    components = []
    
    for node in list(adj.keys()):
        if node not in visited:
            component_users = set()
            component_convs = set()
            stack = [node]
            visited.add(node)
            while stack:
                curr = stack.pop()
                if curr.startswith("user_"):
                    component_users.add(curr[5:])
                else:
                    component_convs.add(curr[5:])
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            components.append((component_users, component_convs))
            
    print(f"Total isolated Connected Components: {len(components):,}")
    
    # Deterministic shuffle of components
    np.random.seed(42)
    indices = np.arange(len(components))
    np.random.shuffle(indices)
    
    # Partition components approximately 70% / 15% / 15%
    n_comp = len(components)
    train_comp_idx = indices[:int(n_comp * 0.70)]
    val_comp_idx = indices[int(n_comp * 0.70):int(n_comp * 0.85)]
    test_comp_idx = indices[int(n_comp * 0.85):]
    
    train_users = set().union(*[components[i][0] for i in train_comp_idx])
    train_convs = set().union(*[components[i][1] for i in train_comp_idx])
    
    val_users = set().union(*[components[i][0] for i in val_comp_idx])
    val_convs = set().union(*[components[i][1] for i in val_comp_idx])
    
    test_users = set().union(*[components[i][0] for i in test_comp_idx])
    test_convs = set().union(*[components[i][1] for i in test_comp_idx])
    
    train_df = pairs_cleaned[pairs_cleaned["author_id_customer"].isin(train_users)].copy()
    val_df = pairs_cleaned[pairs_cleaned["author_id_customer"].isin(val_users)].copy()
    test_df = pairs_cleaned[pairs_cleaned["author_id_customer"].isin(test_users)].copy()
    
    print(f"Train Set: {len(train_df):,} examples ({len(train_users):,} users, {len(train_convs):,} convs)")
    print(f"Val Set  : {len(val_df):,} examples ({len(val_users):,} users, {len(val_convs):,} convs)")
    print(f"Test Set : {len(test_df):,} examples ({len(test_users):,} users, {len(test_convs):,} convs)")
    
    # Strict zero-leakage assertions
    assert set(train_df["author_id_customer"]).isdisjoint(set(test_df["author_id_customer"])), "User leakage between train and test!"
    assert set(train_df["conversation_id"]).isdisjoint(set(test_df["conversation_id"])), "Conversation leakage between train and test!"
    assert set(val_df["author_id_customer"]).isdisjoint(set(test_df["author_id_customer"])), "User leakage between val and test!"
    assert set(val_df["conversation_id"]).isdisjoint(set(test_df["conversation_id"])), "Conversation leakage between val and test!"
    assert set(train_df["author_id_customer"]).isdisjoint(set(val_df["author_id_customer"])), "User leakage between train and val!"
    assert set(train_df["conversation_id"]).isdisjoint(set(val_df["conversation_id"])), "Conversation leakage between train and val!"
    print("ALL ASSERTIONS PASSED: Mathematically zero user leakage and zero conversation leakage.")
    
    # Save splits to data/splits/
    splits_dir = Path("data/splits")
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    cols_to_save = [
        "tweet_id_customer",
        "author_id_customer",
        "created_at_customer",
        "text_customer",
        "clean_customer_text",
        "tweet_id_apple",
        "created_at_apple",
        "text_apple",
        "clean_apple_text",
        "conversation_id",
        "is_conversation_starter"
    ]
    
    train_df[cols_to_save].to_csv(splits_dir / "train.csv", index=False)
    val_df[cols_to_save].to_csv(splits_dir / "val.csv", index=False)
    test_df[cols_to_save].to_csv(splits_dir / "test.csv", index=False)
    
    # Save processed full dataset
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    pairs_cleaned[cols_to_save].to_csv(processed_dir / "applesupport_pairs.csv", index=False)
    print(f"Saved processed dataset to {processed_dir / 'applesupport_pairs.csv'}")
    
    # ---------------------------------------------------------
    # STEP 7: Intent Discovery & Keyword Pattern Mining
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 7: Intent Pattern Mining & Topic Discovery")
    print("=" * 60)
    
    # Define candidate intent patterns based on domain knowledge and empirical exploration of AppleSupport
    intent_patterns = {
        "ios_update_issue": r"\b(ios\s*1[1-7]|update|updated|updating|upgrade|downgrade|software update|installing ios)\b",
        "battery_power_drain": r"\b(battery|drain|draining|dying|percentage|charge|charging|charger|overheating|hot)\b",
        "app_crash_performance": r"\b(crash|crashing|freeze|freezing|frozen|lag|lagging|slow|sluggish|unresponsive|stuck|glitch|bug)\b",
        "apple_id_icloud_account": r"\b(apple\s*id|icloud|itunes|account|sign in|login|logged out|password|verification code|locked|2fa|two-factor)\b",
        "audio_sound_speaker": r"\b(sound|speaker|volume|microphone|mic|audio|airpod|airpods|headphone|earphone|hear|call volume)\b",
        "screen_display_touch": r"\b(screen|touch|display|flicker|black screen|lines|dim|unresponsive screen|touch id|face id)\b",
        "connectivity_wifi_bluetooth": r"\b(wifi|wi-fi|bluetooth|cellular|no service|lte|4g|signal|disconnecting|connect)\b",
        "hardware_repair_battery_replacement": r"\b(genius bar|apple store|repair|replace|replacement|cracked|warranty|applecare|broken glass)\b",
        "store_billing_subscription": r"\b(refund|charged|charge|receipt|subscription|purchase|payment|bill|billing|app store charge|money)\b",
        "photo_storage_backup": r"\b(storage|full storage|storage almost full|photos|camera|backup|restore|space)\b",
        "feedback_complaint_escalation": r"\b(worst|terrible|hate|useless|horrible|lawsuit|switch to android|sucks|frustrated|angry|disappointed)\b"
    }
    
    intent_counts = {}
    intent_examples = {k: [] for k in intent_patterns}
    
    for intent_name, pattern in intent_patterns.items():
        matches = pairs_cleaned[pairs_cleaned["clean_customer_text"].str.contains(pattern, case=False, na=False)]
        intent_counts[intent_name] = len(matches)
        # Sample representative examples
        sample_rows = matches.sample(min(len(matches), 15), random_state=42)
        for _, row in sample_rows.iterrows():
            intent_examples[intent_name].append({
                "tweet_id": row["tweet_id_customer"],
                "author_id": row["author_id_customer"],
                "text": row["text_customer"],
                "clean_text": row["clean_customer_text"],
                "apple_reply": row["clean_apple_text"]
            })
            
    print("\nEmpirical Intent Distribution across 84k+ unique pairs:")
    for k, v in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k:35s}: {v:6,} matches ({v/len(pairs_cleaned)*100:5.2f}%)")
        
    # Save intent examples and stats for report generation
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    with open("artifacts/intent_discovery_stats.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_pairs": len(pairs_cleaned),
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
            "intent_counts": intent_counts,
            "intent_examples": intent_examples
        }, f, indent=2)
        
    print("Intent discovery statistics saved to artifacts/intent_discovery_stats.json")
    
    # ---------------------------------------------------------
    # STEP 8: Sample Golden Set Candidates from Test Split
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 8: Generating Unlabelled Golden Set Candidates from Test Split")
    print("=" * 60)
    
    # The golden set MUST come exclusively from the held-out test split (test_df)
    # We want 200 high-variety examples:
    # - Representative distribution across distinct intent patterns
    # - Edge cases (short texts, multi-intent queries, frustrated/escalation queries, questions vs complaints)
    # - 0 artificial labels!
    
    golden_candidates = []
    seen_tweet_ids = set()
    
    # 1. Stratified samples across discovered patterns from test_df
    for intent_name, pattern in intent_patterns.items():
        subset = test_df[test_df["clean_customer_text"].str.contains(pattern, case=False, na=False)]
        available = subset[~subset["tweet_id_customer"].isin(seen_tweet_ids)]
        sample_size = min(len(available), 15)
        if sample_size > 0:
            sampled = available.sample(sample_size, random_state=42)
            for _, r in sampled.iterrows():
                seen_tweet_ids.add(r["tweet_id_customer"])
                golden_candidates.append({
                    "id": f"gold_{len(golden_candidates)+1:03d}",
                    "tweet_id": r["tweet_id_customer"],
                    "conversation_id": r["conversation_id"],
                    "author_id": r["author_id_customer"],
                    "created_at": r["created_at_customer"],
                    "text": r["text_customer"],
                    "clean_text": r["clean_customer_text"],
                    "is_conversation_starter": bool(r["is_conversation_starter"]),
                    # Ground truth fields left completely blank for human annotation
                    "intent": None,
                    "requires_escalation": None,
                    "ambiguity_notes": None,
                    "annotator_id": None
                })
                
    # 2. Hard / ambiguous cases (short queries, multiple question marks, negative sentiment)
    ambiguous_candidates = test_df[
        (~test_df["tweet_id_customer"].isin(seen_tweet_ids)) &
        (
            (test_df["clean_customer_text"].str.len() < 25) |
            (test_df["clean_customer_text"].str.count(r"\?") > 1) |
            (test_df["clean_customer_text"].str.contains(r"\b(why|how|what|broken|help)\b", case=False))
        )
    ]
    sampled_ambiguous = ambiguous_candidates.sample(min(len(ambiguous_candidates), 35), random_state=42)
    for _, r in sampled_ambiguous.iterrows():
        seen_tweet_ids.add(r["tweet_id_customer"])
        golden_candidates.append({
            "id": f"gold_{len(golden_candidates)+1:03d}",
            "tweet_id": r["tweet_id_customer"],
            "conversation_id": r["conversation_id"],
            "author_id": r["author_id_customer"],
            "created_at": r["created_at_customer"],
            "text": r["text_customer"],
            "clean_text": r["clean_customer_text"],
            "is_conversation_starter": bool(r["is_conversation_starter"]),
            "intent": None,
            "requires_escalation": None,
            "ambiguity_notes": None,
            "annotator_id": None
        })
        
    print(f"Total unlabelled golden candidate examples generated: {len(golden_candidates)}")
    
    # Save golden_unlabelled.jsonl
    golden_dir = Path("data/golden")
    golden_dir.mkdir(parents=True, exist_ok=True)
    
    golden_jsonl_path = golden_dir / "golden_unlabelled.jsonl"
    with open(golden_jsonl_path, "w", encoding="utf-8") as f:
        for ex in golden_candidates:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated unlabelled gold set at: {golden_jsonl_path.resolve()}")

if __name__ == "__main__":
    main()
