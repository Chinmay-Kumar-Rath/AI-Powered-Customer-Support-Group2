# Category labeling guide

## Scope

This guide defines the seven primary categories used by the Person 2 ticket classifier. Assign the category that best represents the user's primary issue, not every system mentioned in the ticket.

## Categories

| Category | Include | Do not automatically include |
|---|---|---|
| Network | Wi-Fi, internet, DNS, connectivity, routing, or general network outages | VPN-specific problems or application failures that only mention a network |
| VPN | VPN connection, VPN authentication, tunnel timeout, VPN client, or VPN disconnection | General Wi-Fi or internet problems without VPN evidence |
| Software | Application crashes, installation, updates, software bugs, and compatibility | Physical device faults |
| Hardware | Laptop, desktop, monitor, keyboard, mouse, printer, headset, power, or other physical peripherals | Pure application or account problems |
| Password Reset | Forgotten or expired passwords, credential resets, and account lockouts caused by credentials | General permissions or department-access requests |
| Email | Outlook, mailbox, email send/receive, synchronization, and mailbox capacity | General communication requests without an email-support issue |
| Security | Phishing, malware, virus, suspicious login, unauthorized access, breach, or data leak | Ordinary access or performance issues without a security concern |

## Decision rules

1. Use the primary issue the user wants resolved.
2. Prefer VPN over general Network when the ticket explicitly says VPN.
3. Prefer Security when the central issue is an incident, breach, phishing, malware, or unauthorized access.
4. Do not use a source tag as a final label when multiple target tags conflict.
5. Exclude ambiguous tickets instead of forcing a label.
6. Use `Other` as a sub-category when the text does not support a more specific rule.

## Approved sub-categories

- Network: No Internet, Wi-Fi Disconnect, Slow Connection, DNS/Connectivity, Network Outage
- VPN: Connection Timeout, Authentication Failure, Disconnection, Configuration
- Software: Application Crash, Installation Failure, Update Error, Compatibility Issue, Application Bug
- Hardware: Keyboard/Mouse, Display, Printer, Power/Battery, Audio/Peripheral
- Password Reset: Forgot Password, Password Expired, Account Locked, Credential Reset
- Email: Send/Receive Failure, Synchronisation, Mailbox Full, Outlook Access
- Security: Phishing, Malware, Unauthorised Access, Data Breach
