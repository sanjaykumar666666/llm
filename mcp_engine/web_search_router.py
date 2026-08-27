"""
Semantic Temporal Query Router & Intent Classifier.

Core Principle:
    "Can this answer change with time?"
      YES / MAYBE  →  WEB SEARCH  →  LLM
      NO (stable)  →  LLM direct

Classification:
    STATIC    – Conceptual, mathematical, definitional — LLM sufficient
    CURRENT   – Real-world facts that change — WEB SEARCH required
    HISTORICAL – Past-tense facts with explicit year/era — historical web search
    UNKNOWN   – Temporal nature uncertain — WEB SEARCH (safe default)

CRITICAL: Does NOT rely on keywords like "current" / "latest" / "today".
          Classifies by the NATURE of the requested information.

File: mcp_engine/web_search_router.py
"""

import re
from typing import Dict, Any, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# EXPLICIT COMMAND PATTERNS  (override all classification)
# ─────────────────────────────────────────────────────────────────────────────

RE_EXPLICIT_SEARCH = re.compile(
    r"\b(search\s+the\s+web|search\s+online|look\s+up\s+online|google\s+(this|that|for)|"
    r"search\s+internet|find\s+online|web\s+search|search\s+google|browse\s+web|"
    r"look\s+on\s+the\s+web|search\s+for\s+me)\b",
    re.IGNORECASE,
)

RE_RESEARCH_INTENT = re.compile(
    r"\b(deep\s+research|comprehensive\s+analysis|in-depth\s+study|exhaustive\s+review|"
    r"multi-source\s+comparison|systematic\s+review|detailed\s+investigation)\b",
    re.IGNORECASE,
)

RE_MULTIMODAL_HINT = re.compile(
    r"\b(upload|uploaded\s+file|attached\s+document|run\s+this\s+code|execute\s+python|"
    r"dataset|csv\s+file|generate\s+image|analyze\s+image|parse\s+pdf)\b",
    re.IGNORECASE,
)

RE_CLEAN_SEARCH_PREFIX = re.compile(
    r"^\s*(search\s+for|search\s+the\s+web\s+for|search\s+online\s+for|google\s+for|"
    r"tell\s+me\s+about|find\s+out|look\s+up)\s*",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORICAL QUERY DETECTION
# Past-tense queries with explicit year or historical era references.
# Routed to web search for historical context (not live data).
# ─────────────────────────────────────────────────────────────────────────────

RE_HISTORICAL = re.compile(
    r"("
    # Explicit year reference in the past (before 2024)
    r"\bin\s+(19[0-9]{2}|20[01][0-9]|202[0-3])[,\s]"
    r"|\bduring\s+(19[0-9]{2}|20[01][0-9]|202[0-3])\b"
    r"|\bback\s+in\s+\d{4}\b"
    r"|"
    # "who was the [role]... in [year]" — including abbreviations like PM, CM
    r"who\s+was\s+(the\s+)?(president|prime\s+minister|\bpm\b|chief\s+minister|\bcm\b|ceo|governor|"
    r"chancellor|secretary|minister|director|head|leader|chairman)\b"
    r".{0,35}(in\s+(19|20)\d\d|during\s+\d{4})"
    r"|"
    # Historical events / eras
    r"\b(world\s+war\s+(i|ii|1|2|one|two)|cold\s+war|during\s+independence|"
    r"at\s+partition|french\s+revolution|industrial\s+revolution|"
    r"american\s+revolution|ancient\s+(rome|greece|egypt|india|china)|"
    r"medieval|renaissance|colonial\s+era|pre-independence|british\s+raj|"
    r"mughal|maurya|gupta|ottoman|roman\s+empire)\b"
    r"|"
    r"\b(history\s+of|historical\s+analysis|historically)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Standalone year reference pattern used as a fallback UNKNOWN→HISTORICAL upgrade
RE_PAST_YEAR = re.compile(
    r"\b(in|during|of|back\s+in)\s+(19[0-9]{2}|20[01][0-9]|202[0-3])\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# CURRENT INFORMATION DOMAINS
#
# These patterns identify queries whose answer CAN CHANGE OVER TIME.
# They work WITHOUT "current" / "latest" / "today" keywords —
# they detect temporal sensitivity from the DOMAIN of the question.
# ─────────────────────────────────────────────────────────────────────────────

# ── Domain A: People in Roles / Positions ───────────────────────────────────
# "CEO of Google", "PM of India", "Who leads Tesla?" — role occupancy changes.

RE_PERSON_POSITION = re.compile(
    r"("
    # ① Role keyword directly followed by "of / at / for / in / ,"
    # Works both with and without a preceding "Who is" question prefix.
    r"\b(ceo|cto|coo|cfo|cmo|chairman|chairperson|president|prime\s+minister|\bpm\b|"
    r"chief\s+minister|\bcm\b|governor|mayor|chancellor|secretary\s+general|"
    r"secretary|minister|director|managing\s+director|head\s+of|"
    r"leader\s+of|chief\s+of|commander\s+of|commissioner|superintendent|"
    r"ambassador|deputy|vice[-\s]president|"
    r"rbi\s+governor|sebi\s+chairman|fed\s+chair(?:man)?|"
    r"finance\s+minister|home\s+minister|defence\s+minister|defense\s+minister|"
    r"foreign\s+minister|health\s+minister|education\s+minister|"
    r"national\s+security\s+advisor)\b"
    r"\s*(?:of|at|for|in|,)\b"
    r")|("
    # ② "Who leads / runs / heads / manages [org]?"
    r"\bwho\s+(?:leads?|heads?|runs?|chairs?|manages?|directs?|commands?|"
    r"controls?|serves?\s+as|works?\s+as|acts?\s+as|is\s+in\s+charge\s+of|"
    r"currently\s+(?:holds?|leads?|heads?|runs?))\b"
    r")|("
    # ③ "[CEO/head/chief] of [well-known org]"
    r"\b(?:ceo|cto|coo|president|head|chief|leader|director|founder|co-founder|owner|boss)\s+"
    r"(?:of|at)\s+"
    r"(?:google|apple|microsoft|amazon|meta|facebook|tesla|openai|anthropic|"
    r"nvidia|infosys|tcs|wipro|hcl|reliance|tata\s+group|adani|"
    r"rbi|sebi|isro|sbi|hdfc|icici|"
    r"nato|united\s+nations|un\b|who\b|wto|imf|world\s+bank|icc|bcci|fifa|iaf|"
    r"india|usa|uk|china|russia|france|germany|japan|australia|canada|"
    r"ukraine|pakistan|bangladesh|sri\s+lanka|nepal|bhutan|myanmar|"
    r"california|new\s+york|texas|florida|"
    r"bjp|congress\s+party|aap|supreme\s+court|cbi|nia|"
    r"army|navy|air\s+force|senate|parliament|"
    r"lok\s+sabha|rajya\s+sabha|white\s+house|kremlin|"
    r"federal\s+reserve|reserve\s+bank|bank\s+of\s+england|ecb)\b"
    r")",
    re.IGNORECASE,
)

# ── Domain B: Financial / Market Data ───────────────────────────────────────
# "Price of gold", "Bitcoin value", "Sensex today", "Exchange rate" — always live.

RE_FINANCIAL_CURRENT = re.compile(
    r"("
    # Price / rate / value queries
    r"\b(?:price|cost|rate|value|worth|valuation|market\s+cap|market\s+value|"
    r"spot\s+rate|live\s+rate)\s+(?:of|for)\s"
    r"|\b(?:how\s+much\s+is|what\s+is\s+the\s+(?:price|value|rate|cost)\s+of)\s"
    r"|"
    # Named financial instruments
    r"\b(?:gold|silver|platinum|palladium|crude\s+oil|brent\s+crude|wti\s+crude|"
    r"natural\s+gas|bitcoin|btc|ethereum|eth|ripple|xrp|dogecoin|doge|"
    r"solana|sol|usdt|tether|usdc|binance|bnb|crypto|cryptocurrency|nft|"
    r"sensex|nifty\s*50|nifty\s+bank|dow\s+jones|nasdaq|s&p\s*500|"
    r"ftse|nikkei|hang\s+seng|cac\s*40|dax)\s+"
    r"(?:price|rate|value|worth|today|now|currently|performance|level|index|points?)\b"
    r"|"
    # Economic indicators
    r"\b(?:repo\s+rate|reverse\s+repo|crr|slr|interest\s+rate|inflation\s+rate|"
    r"cpi\b|wpi\b|gdp\b|gross\s+domestic\s+product|fiscal\s+deficit|"
    r"current\s+account\s+deficit|forex\s+reserve|foreign\s+exchange\s+reserve|"
    r"dollar\s+reserve|balance\s+of\s+payments)\b"
    r"|"
    # Currency exchange
    r"\b(?:exchange\s+rate|forex\s+rate|currency\s+rate|"
    r"(?:usd|inr|eur|gbp|jpy|cny|aud|cad|chf|sgd|aed|sar)\s*"
    r"(?:to|vs|against|rate|exchange|price|value|today))\b"
    r"|"
    # IPO events
    r"\b(?:ipo|initial\s+public\s+offering)\s+"
    r"(?:today|this\s+week|upcoming|open|close|allotment|listing|price|gmp|grey\s+market)\b"
    r"|"
    # Company financials
    r"\b(?:quarterly\s+results?|annual\s+results?|earnings\s+report|"
    r"revenue|net\s+profit|ebitda)\s+(?:of|for|by|from)\s"
    r")",
    re.IGNORECASE,
)

# ── Domain C: Technology Products / Versions ────────────────────────────────
# "Latest Gemini model", "Current Android version" — changes with every release.

RE_TECH_CURRENT = re.compile(
    r"("
    # "latest / newest / current version/model/release of X"
    r"\b(?:latest|newest|current|most\s+recent)\s+"
    r"(?:version|model|release|update|patch|build)\s*(?:of\s+)?"
    r"|\bwhat\s+is\s+the\s+(?:latest|newest|current|most\s+recent)\s+"
    r"(?:version|model|release|update|iteration)\b"
    r"|"
    # Named AI models (inherently time-sensitive)
    r"\b(?:chatgpt|gpt[-\s]?[0-9o]+|gpt\s+[0-9]+|gemini\s*[0-9.]*|"
    r"claude\s*[0-9.]*|llama\s*[0-9.]*|mistral|groq|copilot|bard|"
    r"palm\s*[0-9.]*|falcon|bloom|grok|perplexity|deepseek|sora|dall-?e)\s*"
    r"(?:latest|newest|current|model|version|update|release|[0-9]+\.[0-9]+|"
    r"available|best|most\s+powerful|most\s+capable)?"
    r"\s*(?:model|version|update|release)?\b"
    r"|"
    r"\bwhat\s+(?:is\s+)?(?:openai|google|anthropic|meta|microsoft|amazon|nvidia|"
    r"mistral|xai)\s*(?:latest|newest|current|best|most\s+advanced)?\s*"
    r"(?:ai|llm|model|gpt|gemini|claude|chatbot)?\b"
    r"|"
    # OS / Device latest version
    r"\b(?:latest|newest|current)\s+"
    r"(?:iphone|ipad|macbook|mac\s+pro|imac|mac\s+mini|"
    r"android|ios|ipados|macos|windows|ubuntu|debian|fedora|arch\s+linux|"
    r"pixel\s+[0-9]+|samsung\s+galaxy|oneplus|xiaomi|redmi|realme)\b"
    r"|"
    # Availability / capability of live AI tools
    r"\b(?:is\s+|does\s+)?"
    r"(?:chatgpt|gemini|claude|copilot|gpt|bard|ai\s+assistant|perplexity)\s+"
    r"(?:available|free|paid|down|support|have|offer|work\s+with|released|launched)\b"
    r")",
    re.IGNORECASE,
)

# ── Domain D: Sports Results / Rankings ─────────────────────────────────────
# "Who won the IPL?", "Current cricket ranking" — change after every match.

RE_SPORTS_CURRENT = re.compile(
    r"("
    # Match / game results
    r"\b(?:who\s+won|who\s+is\s+winning|match\s+result|final\s+score|"
    r"who\s+won\s+the\s+(?:match|game|tournament|series|cup|championship|title))\b"
    r"|"
    # Tournament / league names with optional result keywords
    r"\b(?:ipl|world\s+cup|cricket\s+world\s+cup|t20\s+world\s+cup|"
    r"champions\s+trophy|asia\s+cup|test\s+series|odi\s+series|t20\s+series|"
    r"premier\s+league|champions\s+league|la\s+liga|bundesliga|serie\s+a|ligue\s+1|"
    r"fifa|euro\s+cup|copa\s+america|olympics|commonwealth\s+games|asian\s+games|"
    r"wimbledon|us\s+open|french\s+open|australian\s+open|"
    r"formula\s+1|f1|motogp|wwe|ufc|nba|nfl|mlb|nhl|isl|pro\s+kabaddi)\b"
    r"\s*(?:result|winner|score|standing|table|final|semifinal|schedule|"
    r"points?|today|latest|current|2025|2026)?"
    r"|"
    # Sport + current info keywords
    r"\b(?:cricket|football|soccer|tennis|badminton|basketball|hockey|golf|boxing|"
    r"wrestling|kabaddi|chess|athletics)\s+"
    r"(?:score|result|winner|ranking|standing|points?\s+table|latest|today|live|"
    r"squad|lineup|playing\s+xi)\b"
    r"|"
    # Live / current rankings
    r"\b(?:current|latest|live)\s+"
    r"(?:ranking|standing|points?\s+table|scoreboard|leaderboard|ladder)\b"
    r"|"
    # Team / player current status
    r"\b(?:player\s+transfer|team\s+squad|playing\s+xi|playing\s+11|lineup|"
    r"roster|squad\s+list|selection)\s*"
    r"(?:today|now|latest|current|for\s+the)?\b"
    r")",
    re.IGNORECASE,
)

# ── Domain E: Politics / Government Current State ───────────────────────────
# "Ruling party", "Election results", "Current tax slab" — changes with governance.

RE_POLITICAL_CURRENT = re.compile(
    r"("
    # Current government / policy / law
    r"\b(?:current|new|latest|recent)\s+"
    r"(?:government|policy|law|rule|regulation|scheme|amendment|ordinance|"
    r"notification|circular|directive|guidelines|manifesto)\b"
    r"|"
    # Election outcomes
    r"\b(?:election\s+(?:result|winner|outcome|verdict|date|schedule)|"
    r"who\s+won\s+the\s+(?:election|vote|referendum|poll)|"
    r"election\s+verdict)\b"
    r"|"
    # Ruling party / power
    r"\b(?:current\s+government\s+in|ruling\s+party\s+(?:in|of)|"
    r"which\s+party\s+(?:is|currently)\s+in\s+(?:power|government))\b"
    r"|"
    # New legislation / budget
    r"\b(?:new\s+(?:law|bill|act|policy|amendment|budget|scheme|ordinance)|"
    r"recently\s+(?:passed|approved|enacted|introduced)\s+(?:law|bill|act))\b"
    r"|\b(?:budget\s+20[2-9][0-9]|union\s+budget|interim\s+budget|railway\s+budget)\b"
    r"|"
    # Visa / immigration rules
    r"\b(?:visa\s+(?:rule|requirement|policy|fee|eligibility|process)|"
    r"passport\s+rule|immigration\s+(?:policy|rule|requirement)|"
    r"work\s+permit|residency\s+requirement)\s*(?:2025|2026|now|current|latest)?\b"
    r"|"
    # Tax rates / slabs
    r"\b(?:income\s+tax\s+(?:slab|rate|bracket)|"
    r"gst\s+(?:rate|slab|rule)|corporate\s+tax\s+rate|"
    r"capital\s+gains\s+tax|surcharge\s+rate)\s*"
    r"(?:20[2-9][0-9]|now|current|latest|today)?\b"
    r"|"
    # General "current rules" queries
    r"\bwhat\s+are\s+the\s+(?:current|new|latest)\s+"
    r"(?:rules?|laws?|regulations?|policies?|norms?|guidelines?)\b"
    r")",
    re.IGNORECASE,
)

# ── Domain F: Companies / Organizations Current State ───────────────────────
# "Who is CEO of X?", "Latest product from Y" — changes with corporate events.

RE_COMPANY_CURRENT = re.compile(
    r"("
    # Who is CEO/founder/head of company
    r"\bwho\s+is\s+(?:the\s+)?(?:ceo|cto|coo|cfo|founder|co-founder|owner|"
    r"director|head|boss|chairman|managing\s+director)\s+of\b"
    r"|"
    # Company valuation
    r"\b(?:company\s+valuation|startup\s+valuation|unicorn|decacorn|soonicorn)\s*"
    r"(?:list|value|rank|status|worth)?\b"
    r"|"
    # Latest product/service launch
    r"\b(?:latest|new|newest|recently\s+launch(?:ed)?)\s+"
    r"(?:product|service|feature|model|app|tool|update|announcement|launch)\s+"
    r"(?:from|by|of)\s+\w+"
    r"|"
    # Is [service] available / down?
    r"\bis\s+\w+\s+(?:available|working|operational|down|offline|live|launched|released)\s*"
    r"(?:now|today|yet)?\b"
    r"|"
    # Current pricing / plan
    r"\b(?:current|new|updated)\s+(?:plan|pricing|subscription|price\s+plan|cost)\s+"
    r"(?:of|for|by)?\s*\w+"
    r"|"
    # What does [company] currently offer?
    r"\bwhat\s+(?:does|can)\s+\w+\s+(?:offer|do|support|provide|include)\s+"
    r"(?:now|today|currently)\b"
    r")",
    re.IGNORECASE,
)

# ── Domain G: News / Recent Events ──────────────────────────────────────────
# "What happened in India?", "Latest news", "Current crisis" — always live.

RE_NEWS_EVENTS = re.compile(
    r"("
    r"\bwhat\s+(?:happened|is\s+happening|has\s+happened|occurred)\s*"
    r"(?:to|in|at|with|recently|today|now|lately)?\b"
    r"|\b(?:latest|recent|breaking|today.?s?)\s+news\b"
    r"|\bnews\s+(?:in|from|about|today|regarding)\b"
    r"|\b(?:current\s+situation|situation\s+in\s+\w+\s+(?:now|today|currently))\b"
    r"|\b(?:recent|latest)\s+"
    r"(?:attack|earthquake|flood|tsunami|cyclone|hurricane|tornado|disaster|accident|"
    r"crash|explosion|fire|war|conflict|crisis|protest|rally|strike|scam|fraud|"
    r"announcement|development|update|change|shift|trend|scandal|controversy|incident)\b"
    r"|\bwhat.{0,15}(?:happening|going\s+on)\s*(?:in|with|at|to)?\b"
    r")",
    re.IGNORECASE,
)

# ── Domain H: Weather / Live Conditions ─────────────────────────────────────
# "Weather today", "Current temperature" — always live data.

RE_LIVE_CONDITIONS = re.compile(
    r"("
    r"\b(?:weather|temperature|rainfall|humidity|forecast)\s*"
    r"(?:today|now|tomorrow|tonight|this\s+week|in\s+\w+|for\s+\w+)?\b"
    r"|\btoday.?s?\s+(?:weather|temperature|forecast|rain|snow|sunshine)\b"
    r"|\bcurrent\s+(?:weather|temperature|conditions|forecast|air\s+quality)\b"
    r"|\bis\s+it\s+(?:raining|sunny|hot|cold|cloudy|windy|snowing|foggy)\s*"
    r"(?:today|now|in|there)?\b"
    r"|\b(?:traffic|congestion|road\s+condition)\s*(?:now|today|currently|in\s+\w+)?\b"
    r"|\b(?:air\s+quality|aqi\b|pollution\s+level|pm\s*2\.?5|pm\s*10)\s*"
    r"(?:today|now|in|of|for)?\b"
    r")",
    re.IGNORECASE,
)

# ── Enhanced time-sensitive keywords ────────────────────────────────────────
RE_TIME_SENSITIVE_KEYWORDS = re.compile(
    r"\b(latest|today|yesterday|current\s+status|current\s+price|live\s+score|"
    r"breaking\s+news|recent\s+news|latest\s+news|latest\s+updates?|"
    r"what\s+happened\s+today|this\s+week|2026|2025\s+update|"
    r"newest\s+release|stock\s+price|weather\s+today|current\s+role|"
    r"who\s+is\s+the\s+current|latest\s+developments?|right\s+now|as\s+of\s+today|"
    r"currently\s+holding|at\s+present|as\s+of\s+now|just\s+released|"
    r"just\s+launched|recently\s+(?:announced|released|launched|updated|changed)|"
    r"this\s+(?:month|year|quarter|season)|real[-\s]?time)\b",
    re.IGNORECASE,
)

# All CURRENT domain detectors with human-readable labels
TEMPORAL_DOMAIN_PATTERNS: List[Tuple] = [
    (RE_PERSON_POSITION,      "People / Positions"),
    (RE_FINANCIAL_CURRENT,    "Financial / Market Data"),
    (RE_TECH_CURRENT,         "Technology / Products"),
    (RE_SPORTS_CURRENT,       "Sports / Rankings"),
    (RE_POLITICAL_CURRENT,    "Politics / Government"),
    (RE_COMPANY_CURRENT,      "Companies / Organizations"),
    (RE_NEWS_EVENTS,          "News / Events"),
    (RE_LIVE_CONDITIONS,      "Weather / Live Conditions"),
]


# ─────────────────────────────────────────────────────────────────────────────
# STATIC PATTERNS  (LLM can answer — no live data needed)
# ─────────────────────────────────────────────────────────────────────────────

RE_STATIC_GENERATION = re.compile(
    r"^(?:"
    r"(?:write|create|generate|compose|draft|make|produce|craft)\s+"
    r"(?:a\s+|an\s+|me\s+a\s+|me\s+an\s+|for\s+me\s+)?"
    r"(?:poem|haiku|sonnet|story|short\s+story|essay|joke|rap|song|lyrics|script|"
    r"letter|email|message|blog\s+post|article|paragraph|sentence|summary|"
    r"presentation|cover\s+letter|resume|cv|speech|toast|prayer|itinerary|plan)"
    r"|"
    r"(?:tell\s+me\s+a\s+(?:joke|story|fun\s+fact|riddle|pun)|"
    r"give\s+me\s+a\s+(?:joke|riddle|fun\s+fact|poem|recipe))"
    r"|"
    r"(?:brainstorm|list|enumerate|suggest)\s+(?:ideas?|topics?|ways?|options?|examples?)"
    r")",
    re.IGNORECASE,
)

RE_STATIC_CODE = re.compile(
    r"("
    r"\b(?:write|create|generate|implement|code|build)\s+(?:a\s+|an\s+)?"
    r"(?:function|class|program|script|algorithm|api|server|database|query|loop|"
    r"method|module|library|framework|component|service|bot|app|website|cli|"
    r"microservice|rest\s+api|graphql|lambda|cron\s+job)\b"
    r"|"
    r"\bhow\s+to\s+(?:code|write|implement|build|create|make|develop|set\s+up|deploy)\s+"
    r"(?:a\s+|an\s+)?"
    r"|"
    r"\b(?:debug|fix|refactor|optimize|review|explain|analyze)\s+(?:this|the|my)?\s*"
    r"(?:code|function|script|program|error|bug|issue|snippet|class|method)\b"
    r"|"
    r"\bwhat\s+does\s+(?:this|the)\s+(?:code|function|class|method|variable|snippet)\s+"
    r"(?:do|mean|return)\b"
    r"|"
    r"\b(?:in\s+|using\s+)(?:python|javascript|java|c\+\+|c#|rust|go|golang|"
    r"typescript|php|ruby|swift|kotlin|r\b|matlab|sql|bash|shell|html|css|"
    r"react|vue|angular|django|flask|fastapi|nodejs|express|spring|laravel|rails|"
    r"flutter|dart|scala|haskell)\b.{0,30}(?:how|write|create|build|implement)\b"
    r")",
    re.IGNORECASE,
)

RE_STATIC_MATH = re.compile(
    r"("
    r"\b(?:calculate|compute|solve|evaluate|simplify|differentiate|integrate|"
    r"find\s+the\s+(?:derivative|integral|limit|sum|product|area|volume|"
    r"probability|mean|median|mode|variance|standard\s+deviation|"
    r"eigenvalue|determinant|inverse|lcm|gcd|hcf))\b"
    r"|\bwhat\s+is\s+[0-9]+\s*[+\-*/^%]\s*[0-9]"
    r"|[0-9]+\s*[+\-*/^%]\s*[0-9]+\s*[+\-*/^%=]"
    r")",
    re.IGNORECASE,
)

RE_STATIC_LANGUAGE = re.compile(
    r"("
    r"\b(?:translate|translation\s+of)\s+(?:this|the|following|.{1,50}\s+to)\b"
    r"|\bwhat\s+does\s+.{1,40}\s+mean\s+in\s+"
    r"(?:english|hindi|tamil|telugu|kannada|malayalam|bengali|marathi|gujarati|"
    r"french|german|spanish|japanese|arabic|chinese|korean|italian|portuguese|"
    r"russian|dutch|swedish|turkish|greek|hebrew|urdu|punjabi|odia)\b"
    r"|\b(?:grammar|spelling|punctuation|vocabulary|synonym\s+(?:for|of)|"
    r"antonym\s+(?:of|for)|definition\s+of|word\s+meaning|phrase\s+meaning|"
    r"etymology\s+of|pronunciation\s+of)\b"
    r")",
    re.IGNORECASE,
)

RE_STATIC_SCIENCE_CONCEPT = re.compile(
    r"\b(?:"
    # Definitional "what is [concept]"
    r"what\s+is\s+(?:a\s+|an\s+)?"
    r"(?:photosynthesis|gravity|quantum\s+(?:mechanics|physics|computing|entanglement)|"
    r"dna|rna|protein|atom|molecule|cell|chromosome|evolution|relativity|entropy|"
    r"thermodynamics|electromagnetism|nuclear\s+(?:physics|energy|reaction)|radiation|"
    r"magnetism|electricity|optics|acoustics|fluid\s+dynamics|"
    r"machine\s+learning|deep\s+learning|neural\s+network|"
    r"blockchain|cryptography|encryption|data\s+structure|"
    r"osmosis|diffusion|mitosis|meiosis|respiration|digestion|"
    r"virus|bacteria|fungus|immune\s+system|"
    r"big\s+bang|black\s+hole|galaxy|solar\s+system|"
    r"photon|electron|proton|neutron|quark|boson|"
    r"capitalism|socialism|communism|democracy|monarchy|republic|"
    r"dharma|karma|yoga|meditation|mindfulness|stoicism|utilitarianism|"
    r"feminism|marxism|liberalism|conservatism)"
    r"|"
    # "How does [process] work"
    r"how\s+does\s+(?:photosynthesis|gravity|the\s+immune\s+system|democracy|"
    r"capitalism|recursion|machine\s+learning|the\s+internet|blockchain|"
    r"quantum\s+computing|neural\s+network|transistor|engine|battery|"
    r"solar\s+panel|nuclear\s+reactor|digestive\s+system|evolution|vaccination|"
    r"penicillin|anesthesia|radar|sonar|gps|wifi|5g)\s+work"
    r"|"
    # Named laws and theories
    r"(?:newton|einstein|darwin|pythagoras|archimedes|boyle|ohm|faraday|"
    r"heisenberg|schrodinger|planck|maxwell|bernoulli|pascal|avogadro).{0,10}"
    r"(?:law|principle|theorem|theory|equation|constant)"
    r")\b",
    re.IGNORECASE,
)

RE_STATIC_PHILOSOPHY_HISTORY = re.compile(
    r"\b(?:"
    r"who\s+is\s+(?:krishna|rama|shiva|vishnu|ganesha|hanuman|buddha|mahavira|jesus|guru\s+nanak|socrates|plato|aristotle|confucius|lao\s+tzu)"
    r"|"
    r"what\s+is\s+the\s+meaning\s+of\s+"
    r"(?:life|dharma|karma|yoga|nirvana|moksha|love|freedom|justice|ethics|"
    r"consciousness|existence|truth|beauty|art)"
    r"|"
    r"what\s+(?:happened|caused|led\s+to|started|ended)\s+"
    r"(?:world\s+war\s+(?:i|ii|1|2|one|two)|the\s+cold\s+war|"
    r"the\s+french\s+revolution|the\s+industrial\s+revolution|"
    r"the\s+american\s+revolution|the\s+moon\s+landing|the\s+partition|"
    r"the\s+holocaust|the\s+great\s+depression)"
    r"|"
    r"explain\s+(?:the\s+meaning\s+of|the\s+concept\s+of|"
    r"the\s+theory\s+of|the\s+principles?\s+of)"
    r")\b",
    re.IGNORECASE,
)

# All static patterns in priority order
STATIC_PATTERNS: List = [
    RE_STATIC_GENERATION,
    RE_STATIC_CODE,
    RE_STATIC_MATH,
    RE_STATIC_LANGUAGE,
    RE_STATIC_SCIENCE_CONCEPT,
    RE_STATIC_PHILOSOPHY_HISTORY,
]

# Short conversational inputs (greetings, ack, etc.) → STATIC
RE_CONVERSATIONAL = re.compile(
    r"^(?:hello|hi\b|hey\b|good\s+(?:morning|evening|afternoon|night)|"
    r"how\s+are\s+you|thank\s+(?:you|u)|thanks\b|ok\b|okay\b|great\b|"
    r"nice\b|cool\b|awesome\b|perfect\b|got\s+it\b|understood\b|sure\b|"
    r"(?:yes|no|absolutely|definitely|certainly)\b|"
    r"what.{0,10}your\s+name|who\s+are\s+you|what\s+can\s+you\s+do|"
    r"help\s+me|i\s+need\s+help|can\s+you\s+help)\b",
    re.IGNORECASE,
)

# Detects factual question structure (for UNKNOWN routing decision)
RE_FACTUAL_QUESTION = re.compile(
    r"\b(?:who|what|where|when|how\s+much|how\s+many|how\s+often|"
    r"which|whose|is\s+(?:it|there|this|that)|are\s+(?:there|they)|"
    r"does|did|has|have|will|can|should)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_current_result(query: str, domain: str, reason: str) -> Dict[str, Any]:
    return {
        "category": "WEB_REQUIRED",
        "should_search": True,
        "search_query": query,
        "reason": reason,
        "max_sources": 3,
        "early_stop": True,
        "execution_mode": "PARALLEL_SEARCH",
        "temporal_class": "CURRENT",
        "temporal_domain": domain,
    }


def _make_static_result(query: str, reason: str) -> Dict[str, Any]:
    return {
        "category": "SIMPLE",
        "should_search": False,
        "search_query": query,
        "reason": reason,
        "max_sources": 0,
        "early_stop": True,
        "execution_mode": "DIRECT_LLM",
        "temporal_class": "STATIC",
        "temporal_domain": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────

class WebSearchRouter:
    """
    Semantic Temporal Query Router.

    Execution tiers:
      SIMPLE          → LLM direct (stable knowledge)
      WEB_REQUIRED    → Live web search + LLM synthesis
      COMPLEX_RESEARCH→ Multi-source deep research
      MULTIMODAL      → File/image/video tool
    """

    @classmethod
    def classify_query_intent(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        forced_tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify a query into an execution tier using semantic temporal reasoning.

        Returns dict with keys:
            category, should_search, search_query, reason,
            max_sources, early_stop, execution_mode,
            temporal_class, temporal_domain
        """
        raw_prompt = (prompt or "").strip()

        # ── 0. Forced tool override ────────────────────────────────────────────
        if forced_tool and forced_tool != "💬 Standard Chat":
            if "Web Search" in forced_tool:
                return {
                    "category": "WEB_REQUIRED",
                    "should_search": True,
                    "search_query": raw_prompt,
                    "reason": "Explicit tool selector: Web Search.",
                    "max_sources": 3,
                    "early_stop": True,
                    "execution_mode": "PARALLEL_SEARCH",
                    "temporal_class": "CURRENT",
                    "temporal_domain": "Explicit Tool",
                }
            elif "Deep Research" in forced_tool:
                return {
                    "category": "COMPLEX_RESEARCH",
                    "should_search": True,
                    "search_query": raw_prompt,
                    "reason": "Explicit tool selector: Deep Research.",
                    "max_sources": 5,
                    "early_stop": False,
                    "execution_mode": "RESEARCH_ENRICHMENT",
                    "temporal_class": "CURRENT",
                    "temporal_domain": "Explicit Research",
                }
            else:
                return {
                    "category": "MULTIMODAL",
                    "should_search": False,
                    "search_query": raw_prompt,
                    "reason": f"Tool route: {forced_tool}",
                    "max_sources": 0,
                    "early_stop": True,
                    "execution_mode": "TOOL",
                    "temporal_class": "STATIC",
                    "temporal_domain": None,
                }

        # ── 1. Resolve follow-up pronoun context ──────────────────────────────
        resolved_query, _ = cls._resolve_followup_context(raw_prompt, chat_history)

        # ── 2. Deep research explicit request ─────────────────────────────────
        if RE_RESEARCH_INTENT.search(resolved_query):
            return {
                "category": "COMPLEX_RESEARCH",
                "should_search": True,
                "search_query": resolved_query,
                "reason": "Complex in-depth research requested.",
                "max_sources": 4,
                "early_stop": False,
                "execution_mode": "RESEARCH_ENRICHMENT",
                "temporal_class": "LIVE_GROUNDED",
                "temporal_domain": "Deep Research",
            }

        # ── 3. Multimodal / file hints ─────────────────────────────────────────
        if RE_MULTIMODAL_HINT.search(resolved_query):
            return {
                "category": "MULTIMODAL",
                "should_search": False,
                "search_query": resolved_query,
                "reason": "Multimodal / document context detected.",
                "max_sources": 0,
                "early_stop": True,
                "execution_mode": "TOOL",
                "temporal_class": "STATIC",
                "temporal_domain": None,
            }

        # ── 4. Conversational pure greetings without question intent ─────────
        # Only trivial non-informational phrases bypass search (e.g. "hi", "ok", "thanks")
        clean_input = resolved_query.strip().lower()
        if clean_input in ("hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "good morning", "good evening", "good night"):
            return _make_static_result(
                resolved_query, "Conversational greeting / acknowledgement — direct response."
            )

        # ── 5. UNIVERSAL LIVE GROUNDED RETRIEVAL (Rule 1 & Rule 2) ───────────
        # EVERY question, entity query, topic, concept, historical query,
        # technical query, religious/philosophical query, or factual request
        # MUST pass through live information retrieval before the final answer.

        # Detect domain tag for rich UI telemetry & receipt logging
        detected_domain = "General Information"
        for pattern, domain in TEMPORAL_DOMAIN_PATTERNS:
            if pattern.search(resolved_query):
                detected_domain = domain
                break

        if detected_domain == "General Information":
            if RE_HISTORICAL.search(resolved_query) or RE_PAST_YEAR.search(resolved_query):
                detected_domain = "Historical Record"
            elif any(w in clean_input for w in ["photosynthesis", "gravity", "physics", "atom", "quantum", "biology", "dna"]):
                detected_domain = "Science & Education"
            elif any(w in clean_input for w in ["gita", "dharma", "karma", "philosophy", "bible", "quran", "krishna", "buddha"]):
                detected_domain = "Philosophy & Traditions"
            elif any(w in clean_input for w in ["python", "code", "asyncio", "cpu", "engine", "software", "api"]):
                detected_domain = "Technical & Systems"

        clean_search_query = RE_CLEAN_SEARCH_PREFIX.sub("", resolved_query).strip(" .?,")
        clean_search_query = clean_search_query or resolved_query

        return {
            "category": "WEB_REQUIRED",
            "should_search": True,
            "search_query": clean_search_query,
            "reason": f"Universal live grounding mode — live retrieval across verified sources ({detected_domain}).",
            "max_sources": 3,
            "early_stop": True,
            "execution_mode": "PARALLEL_SEARCH",
            "temporal_class": "LIVE_GROUNDED",
            "temporal_domain": detected_domain,
        }

    @classmethod
    def evaluate_search_intent(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible helper returning should_search and metadata."""
        resolved_q, context_applied = cls._resolve_followup_context(prompt, chat_history)
        classified = cls.classify_query_intent(prompt, chat_history)
        
        intent_type = classified["category"]
        if classified.get("temporal_domain") == "Explicit Search":
            intent_type = "EXPLICIT_SEARCH"
        elif classified["category"] == "WEB_REQUIRED":
            intent_type = "REALTIME_INFO"
        elif classified["category"] == "SIMPLE":
            intent_type = "STATIC_KNOWLEDGE"

        return {
            "should_search": classified["should_search"],
            "reason": classified["reason"],
            "search_query": classified["search_query"],
            "intent_type": intent_type,
            "category": classified["category"],
            "execution_mode": classified["execution_mode"],
            "context_applied": context_applied,
            "temporal_class": classified.get("temporal_class"),
        }

    @classmethod
    def _resolve_followup_context(
        cls,
        prompt: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, bool]:
        """Resolves ambiguous pronouns ('it', 'his', 'her') from chat history."""
        if not chat_history or len(chat_history) < 2:
            return prompt, False

        lower_prompt = prompt.lower()
        followup_pronouns = [
            "when did it happen", "where did it happen", "what about it",
            "tell me more about it", "who led it", "his teachings",
            "her teachings", "his", "her",
        ]
        if not any(p in lower_prompt for p in followup_pronouns):
            return prompt, False

        for msg in reversed(chat_history):
            text = msg.get("text", "")
            if text and len(text) > 3 and msg.get("role") == "user":
                subject = text.split("?")[0].strip()
                return f"{prompt} (regarding {subject[:40]})", True

        return prompt, False
