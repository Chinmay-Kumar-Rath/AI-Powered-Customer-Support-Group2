"""Create reviewed-style training augmentation for weak categories.

The rows are deterministic templates for development coverage. They are marked
synthetic and are never used for the held-out test set.
"""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic_tickets.csv"

contexts = [
    "the finance team",
    "our remote staff",
    "the morning shift",
    "a new employee",
    "the design team",
    "the support desk",
    "several analysts",
    "the operations group",
    "a user in the branch office",
    "the customer service team",
]

templates = {
    "VPN": [
        "VPN connection times out after credentials are entered for {context}.",
        "The VPN client stops at Connecting and never creates a tunnel for {context}.",
        "Remote access drops every few minutes while {context} is working.",
        "The VPN reports an authentication failure even though the password is correct for {context}.",
        "A VPN profile cannot be imported on the laptop used by {context}.",
        "The VPN client closes immediately after selecting the company gateway for {context}.",
        "VPN access works on the office network but fails from home for {context}.",
        "A tunnel disconnects whenever {context} starts a long file transfer.",
        "The remote-access client shows a certificate error for {context}.",
        "The VPN reconnect button does not restore access for {context}.",
        "The VPN connection is unusually slow and then times out for {context}.",
        "A new device cannot complete the VPN configuration for {context}.",
        "The secure tunnel disappears when the laptop wakes from sleep for {context}.",
        "VPN login is rejected after a recent client update for {context}.",
        "The VPN client keeps retrying without displaying a useful error for {context}.",
        "Remote staff cannot reach internal applications through the VPN for {context}.",
    ],
    "Email": [
        "Outlook cannot send messages for {context}.",
        "Incoming email is delayed by more than an hour for {context}.",
        "The mailbox is full and new messages are being rejected for {context}.",
        "Outlook remains stuck on Updating Inbox for {context}.",
        "Messages stay in the outbox and never leave for {context}.",
        "The email client repeatedly asks for credentials for {context}.",
        "Attachments fail to download from the mailbox used by {context}.",
        "The shared mailbox is missing from Outlook for {context}.",
        "Email synchronization stops after the laptop reconnects for {context}.",
        "The team can receive mail but cannot send external messages for {context}.",
        "Old messages are not appearing in the mailbox for {context}.",
        "Outlook displays a connection error whenever {context} opens it.",
        "The email search returns no recent messages for {context}.",
        "A distribution-list message is not reaching {context}.",
        "The mailbox quota warning appears on every login for {context}.",
        "Calendar invitations are not synchronizing with email for {context}.",
    ],
    "Password Reset": [
        "A user forgot the account password and needs a reset for {context}.",
        "The account is locked after too many login attempts for {context}.",
        "The password has expired and the reset page rejects the new value for {context}.",
        "Credentials are no longer accepted by the employee portal for {context}.",
        "The password reset email never arrives for {context}.",
        "A user cannot unlock the account after entering the recovery code for {context}.",
        "The reset link reports that it has expired for {context}.",
        "A forgotten password is preventing access to the internal dashboard for {context}.",
        "The identity portal loops back to login during password reset for {context}.",
        "The temporary password is rejected on first sign-in for {context}.",
        "The account remains locked after a successful password change for {context}.",
        "A user needs credentials reset after returning from leave for {context}.",
        "The password policy prevents the user from completing the reset for {context}.",
        "The login screen does not accept the newly changed password for {context}.",
        "The recovery question is unavailable during account unlock for {context}.",
        "An expired credential is blocking access to the support portal for {context}.",
    ],
    "Software": [
        "The desktop application crashes immediately after launch for {context}.",
        "A required application update fails with an installation error for {context}.",
        "The reporting tool freezes when opening a large file for {context}.",
        "A software plugin is incompatible with the current application version for {context}.",
        "The application shows a blank screen after the latest update for {context}.",
        "A license-enabled program closes whenever {context} selects Export.",
        "The installer rolls back before completing on the machine used by {context}.",
        "A recurring software bug prevents {context} from saving changes.",
        "The application is extremely slow after a recent patch for {context}.",
        "A desktop tool displays an error when {context} imports a spreadsheet.",
        "The software update downloads but never finishes installing for {context}.",
        "A required runtime component is missing from the application used by {context}.",
        "The application crashes only when {context} prints a report.",
        "A version conflict prevents the plugin from loading for {context}.",
        "The software cannot connect to its local configuration store for {context}.",
        "A user sees a repeatable error when {context} opens the settings page.",
    ],
}


rows = []
for category, category_templates in templates.items():
    for context in contexts:
        for template in category_templates:
            rows.append({
                "text": template.format(context=context),
                "category": category,
                "source": "synthetic",
                "label_method": "reviewed_template",
            })

df = pd.DataFrame(rows).drop_duplicates(subset=["text"]).reset_index(drop=True)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT, index=False)
print(f"Wrote {len(df)} rows to {OUTPUT}")
print(df["category"].value_counts())
