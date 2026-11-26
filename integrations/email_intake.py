"""Email intake: re-exports from integrations.imap_poller for backwards compatibility."""
from .imap_poller import (
    LiveImapSource,
    MockImapSource,
    _QUOTE_MARKERS,
    _body_text,
    _mock_source,
    _seen_message_ids,
    _state,
    _state_lock,
    get_source,
    is_bounce_or_automated,
    parse_message,
    poll_once,
    start_poller,
    status,
    stop_poller,
)
