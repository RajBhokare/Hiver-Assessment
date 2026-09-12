"""Deterministic intent labeling based on frozen taxonomy rules."""
import re
from typing import Optional, List, Tuple
import pandas as pd

INTENT_RULES: List[Tuple[str, str, int]] = [
    # (intent_name, regex_pattern, priority)
    ("apple_id_account_security", r"\b(apple\s*id|icloud\s*id|itunes\s*account|two-factor|2fa|verification code|security question|locked out|unlock account|forgot password|password reset|passcode)\b", 1),
    ("store_billing_subscription", r"\b(refund|refunds|charge|charged|charges|unauthorized|subscription|receipt|itunes purchase|app store charge|billed|billing|payment method|declined)\b", 2),
    ("hardware_repair_store_service", r"\b(genius bar|apple store|appointment|repair|cracked screen|shattered|broken glass|warranty|applecare|apple care|replacement cost|trade in)\b", 3),
    ("battery_power_charging", r"\b(battery|drain|draining|battery percentage|drops to|dying fast|charge|charging|charger|lightning cable|overheating|phone hot|burning hot)\b", 4),
    ("audio_call_accessory", r"\b(microphone|mic|speaker|earpiece|call volume|cant hear|cannot hear|airpod|airpods|earpod|earpods|headphone|headphones|dongle|audio crackling)\b", 5),
    ("screen_display_touch", r"\b(screen flickering|black screen|lines on screen|touch not working|unresponsive touch|digitizer|touch id|face id|screen unresponsive)\b", 6),
    ("network_connectivity", r"\b(wifi|wi-fi|bluetooth|cellular|lte|4g|no service|searching for service|carrier signal|disconnecting wifi|bluetooth pair)\b", 7),
    ("icloud_storage_backup", r"\b(icloud|storage full|storage almost full|other storage|system storage|backup failed|sync photos|photo library|icloud drive|space)\b", 8),
    ("ios_update_issue", r"\b(ios\s*1[0-7]|ios\s*update|software update|update to ios|updating to|installing update|verifying update|update failed|downgrade|bootloop)\b", 9),
    ("app_performance_crash", r"\b(crash|crashing|freeze|freezing|frozen|lag|lagging|slow|sluggish|keyboard glitch|letter i glitch|stuck on|unresponsive app)\b", 10),
    ("general_complaint_feedback", r"\b(worst|terrible|hate apple|useless|horrible|switch to android|sucks|garbage|disappointed|unacceptable)\b", 11),
]

FALLBACK_INTENT = "general_complaint_feedback"

def classify_intent_rule(text: str) -> str:
    """Classify a clean tweet text into one of the 11 frozen intents."""
    if not isinstance(text, str) or not text.strip():
        return FALLBACK_INTENT
    
    text_lower = text.lower()
    for intent_name, pattern, _ in INTENT_RULES:
        if re.search(pattern, text_lower):
            return intent_name
            
    return FALLBACK_INTENT

def apply_labels(df: pd.DataFrame, text_col: str = "clean_customer_text") -> pd.DataFrame:
    """Add 'intent' column to dataframe deterministically."""
    df_copy = df.copy()
    df_copy["intent"] = df_copy[text_col].apply(classify_intent_rule)
    return df_copy
