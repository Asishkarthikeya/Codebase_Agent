# Rate Limit Configuration
# Customize these settings to control API usage and maximize chat availability

# ============================================================================
# PROVIDER LIMITS (Free Tier Defaults)
# ============================================================================

# Gemini 2.0 Flash Experimental (Latest Model)
GEMINI_RPM = 15  # Requests per minute
GEMINI_TPM = 1000000  # Tokens per minute (1 million)
GEMINI_MIN_DELAY = 4.0  # Minimum seconds between requests (60s / 15 RPM = 4s)
GEMINI_BURST_DELAY = 10.0  # Delay when approaching limit

# Groq Free Tier (Increased delays to prevent rate limits)
GROQ_RPM = 30  # Requests per minute
GROQ_TPM = 20000  # Conservative daily token estimate
GROQ_MIN_DELAY = 8.0  # Minimum 8 seconds between requests (was 1s)
GROQ_BURST_DELAY = 20.0  # Delay when approaching limit (was 10s)

# ============================================================================
# OPTIMIZATION SETTINGS
# ============================================================================

# Response Caching
ENABLE_CACHE = True  # Cache identical queries to save API calls
CACHE_TTL = 300  # Cache lifetime in seconds (5 minutes)
MAX_CACHE_SIZE = 100  # Maximum number of cached responses

# Adaptive Delays
USE_ADAPTIVE_DELAYS = True  # Dynamically adjust delays based on usage
RATE_LIMIT_THRESHOLD = 0.7  # Trigger longer delays at 70% of limit (0.0-1.0)

# Context Optimization
MAX_AGENT_TOOL_RESULTS = 5  # Number of search results per tool call
MAX_AGENT_CONTENT_LENGTH = 2000  # Characters per search result
MAX_LINEAR_DOCS = 8  # Number of documents for linear RAG
MAX_LINEAR_CONTENT_LENGTH = 1500  # Characters per document

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Fallback Behavior
AUTO_FALLBACK_TO_LINEAR = True  # Fall back to linear RAG on agent rate limits
MAX_AGENT_RETRIES = 2  # Number of retries on rate limit errors

# Statistics & Monitoring
SHOW_USAGE_STATS = True  # Display usage stats in sidebar
LOG_RATE_LIMIT_WARNINGS = True  # Log when approaching limits

# Token Budget (Optional - set to 0 to disable)
# Stop making requests after hitting daily token budget
DAILY_TOKEN_BUDGET_GEMINI = 0  # 0 = unlimited (within API limits)
DAILY_TOKEN_BUDGET_GROQ = 0  # 0 = unlimited (within API limits)

# ============================================================================
# TIPS FOR MAXIMIZING USAGE
# ============================================================================
# 1. Set lower MIN_DELAY values for faster responses (but higher risk)
# 2. Enable CACHE to avoid repeat API calls
# 3. Reduce MAX_AGENT_TOOL_RESULTS if hitting rate limits frequently
# 4. Use linear RAG mode for simpler questions (faster, fewer API calls)
# 5. Switch providers if one is exhausted (Gemini <-> Groq)
