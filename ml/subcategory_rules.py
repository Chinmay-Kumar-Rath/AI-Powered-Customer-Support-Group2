"""Transparent category-specific sub-category rules."""

import re

SUBCATEGORY_RULES = {
    "VPN": [
        (r"timeout|timed out", "Connection Timeout"),
        (r"authentication|credentials", "Authentication Failure"),
        (r"disconnect", "Disconnection"),
        (r"configuration|configure", "Configuration"),
    ],
    "Network": [
        (r"wi[- ]?fi", "Wi-Fi Disconnect"),
        (r"no internet|cannot connect", "No Internet"),
        (r"slow", "Slow Connection"),
        (r"dns", "DNS/Connectivity"),
        (r"outage", "Network Outage"),
    ],
    "Software": [
        (r"crash|crashes|crashing", "Application Crash"),
        (r"install", "Installation Failure"),
        (r"update", "Update Error"),
        (r"compatib", "Compatibility Issue"),
        (r"bug", "Application Bug"),
    ],
    "Hardware": [
        (r"keyboard|mouse", "Keyboard/Mouse"),
        (r"monitor|screen|display", "Display"),
        (r"printer", "Printer"),
        (r"battery|power", "Power/Battery"),
        (r"audio|headset|speaker", "Audio/Peripheral"),
    ],
    "Password Reset": [
        (r"forgot", "Forgot Password"),
        (r"expir", "Password Expired"),
        (r"lock", "Account Locked"),
        (r"reset", "Credential Reset"),
    ],
    "Email": [
        (r"send|receive|outbox", "Send/Receive Failure"),
        (r"sync", "Synchronisation"),
        (r"mailbox full|full mailbox", "Mailbox Full"),
        (r"outlook", "Outlook Access"),
    ],
    "Security": [
        (r"phish", "Phishing"),
        (r"malware|virus", "Malware"),
        (r"unauthori|suspicious login", "Unauthorised Access"),
        (r"breach|leak", "Data Breach"),
    ],
}


def predict_subcategory(text: str, category: str) -> str:
    """Return the first matching sub-category, or Other when evidence is weak."""
    text = str(text).lower()
    for pattern, subcategory in SUBCATEGORY_RULES.get(category, []):
        if re.search(pattern, text):
            return subcategory
    return "Other"
