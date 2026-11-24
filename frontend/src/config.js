export const API_BASE_URL=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
export const USE_MOCKS=false; export const NOTIFICATION_POLL_MS=30000;
export const CATEGORIES=['Network','VPN','Software','Hardware','Password Reset','Email','Security'];
export const SEVERITIES=['Low','Medium','High','Critical']; export const PRIORITIES=['P1','P2','P3','P4'];
export const STATUSES=['Open','Classified','In Progress','Awaiting User','Resolved','Closed','Escalated'];
export const DEPARTMENTS=['IT','HR','Finance','Sales','Operations','Other'];
