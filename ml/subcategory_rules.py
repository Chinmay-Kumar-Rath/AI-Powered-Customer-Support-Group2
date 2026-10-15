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

HIGH_CONFIDENCE_RULES = [
    ("Security", r"\bphishing\b|\bphishing email\b|\bmalware\b|\bvirus\b|\bdata breach\b|\bdata leak\b|\bunauthori[sz]ed access\b|\bsuspicious login\b"),
    ("VPN", r"\bvpn\b"),
    ("Password Reset", r"\bforgot (my )?password\b|\bpassword reset\b|\breset (my )?password\b|\baccount locked\b|\bcredentials expired\b"),
    ("Email", r"\boutlook\b|\bmailbox\b|\bcannot send (an )?email\b|\bcannot receive (an )?email\b|\bsend and receive email\b"),
    ("Network", r"\bwi[- ]?fi\b|\bno internet\b|\bdns\b|\bnetwork outage\b|\bnetwork keeps? disconnecting\b"),
    ("Software", r"\bexcel\b.*\bcrash|\bcrash.*\bexcel\b|\bapplication crash\b|\bsoftware crash\b|\binstallation error\b"),
]


def high_confidence_category(text: str) -> str | None:
    """Return a category for unmistakable phrases, otherwise None."""
    text = str(text).lower()
    for category, pattern in HIGH_CONFIDENCE_RULES:
        if re.search(pattern, text):
            return category
    return None


def predict_subcategory(text: str, category: str) -> str:
    """Return the first matching sub-category, or Other when evidence is weak."""
    text = str(text).lower()
    for pattern, subcategory in SUBCATEGORY_RULES.get(category, []):
        if re.search(pattern, text):
            return subcategory
    return "Other"
