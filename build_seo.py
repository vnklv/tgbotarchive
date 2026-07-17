#!/usr/bin/env python3
"""Generate static site for BotsArchive — SEO-friendly version.
- Each bot gets own HTML file with expanded content
- ALL tags get static pages (not just top 100) + AI articles
- 404.html fallback for truly missing URLs
- Sitemap.xml with lastmod + priorities + robots.txt
- SPA index.html works for browsing"""
import json, os, html, re, textwrap, uuid, markdown2
from pathlib import Path
from datetime import datetime
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR
BOTS_DIR = os.path.join(OUTPUT_DIR, "b")
BOT_DIR = os.path.join(OUTPUT_DIR, "bot")
TAGS_DIR = os.path.join(OUTPUT_DIR, "tag")
os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(BOT_DIR, exist_ok=True)
os.makedirs(TAGS_DIR, exist_ok=True)

bots = json.load(open(os.path.join(SCRIPT_DIR, "botsarchive_enriched.json")))
bots.sort(key=lambda b: b.get("date", ""), reverse=True)

# Load AI-generated category articles (for tag pages)
CATEGORY_ARTICLES = {}
cat_file = os.path.join(SCRIPT_DIR, "category_articles.json")
if os.path.exists(cat_file):
    CATEGORY_ARTICLES = json.load(open(cat_file))

# Load bot comparison articles (generated daily by generate_bot_articles.py)
BOT_ARTICLES = {}
art_file = os.path.join(SCRIPT_DIR, "bot_articles.json")
if os.path.exists(art_file):
    BOT_ARTICLES = json.load(open(art_file))

# Tech/functional tags (not meaningful categories)
TECH_TAGS = {
    "inline","groups","group","bot","channel","channels",
    "free","tool","tools","utility","utilities",
    "text","messages","share","url","link","links",
    "photo","photos","image","images","media","files","file",
    "manager","notifications","anonymous","upload",
    "maker","creator","builder","generator",
    "editor","viewer","tracker","counter","saver",
    "forward","repost","crosspost","feed","rss",
    "web","browser","api","webhook",
    "template","form","export","import","sync",
    "backup","parser","extractor","scraper",
    "admin","moderation","moderator","antispam",
    "subscribe","subscriber","subscription",
    "referral","affiliate","promo",
    "donation","donate","invoice","payment",
    "account","login","auth","oauth","password",
    "security","privacy","protection",
    "design","style","theme","themes",
    "status","stats","statistics",
    "update","updates","notification",
    "widget","shortcut","command",
    "fast","easy","simple","smart",
    "help","faq","support","ticket",
    "setup","config","configuration",
    "vpn","proxy","server","hosting",
    "network","dns","ip","ssl",
    "translation","translate",
    "tag","tags","category","categories",
    "list","listing","directory","index",
    "find","lookup","discovery",
    "botfather","botapi","telegrambot",
    "multilingual","localization","i18n",
    "qr","barcode","nfc",
    "shortener","shortlink","shorturl",
    "emoji","sticker",
    "pdf","document","spreadsheet","csv","json","xml",
    "code","coding","programming",
    "developer","devops","git","github",
    "test","testing","debug","debugging",
    "monitoring","analytics",
    "speed","performance","optimization",
    "calculator","count","timer","clock",
    "date","time","timezone","calendar",
    "reminder","alarm","poll","quiz",
    "vote","voting","survey","feedback",
    "blog","website","site",
    "socialmedia","social_media","smm",
    "automation","workflow","integration",
    "multiplayer","singleplayer","2player","multi","single",
    "telegrambot","telegram_bot",
    "free","premium","paid",
    "nsfw","adult","18plus",
    "android","ios","mac","windows","linux",
    "webapp","desktop","mobile",
    "offline","online","realtime",
    "verified","official","unofficial",
    "new","old","popular","trending",
    "top","best","rated",
    "русский","english_language",
    "downloader","uploader",
    "converter","convert",
    "player","playback",
    "color","colour","size","format","type",
    "box","pack","package",
    "info","information",
    "character","letter","word",
    "number","numeric","digit",
    "sort","filter","search_filter",
    "preview","thumbnail",
    "source","origin",
    "panel","dashboard",
    "rating","review",
    "member","user","users",
    "message","chat",
    "send","receive",
    "add","remove","delete",
    "create","manage","control",
    "custom","customize","personalize",
    "auto","automatic",
    "daily","weekly","monthly",
    "global","local","regional",
    "general",
}

# Precompute tag frequency for finding best category per bot
tag_freq = Counter()
for b in bots:
    for t in b.get("tags", []):
        tag_freq[t] += 1

def best_category_tag(bot):
    """Find the most popular meaningful tag for this bot."""
    tags = bot.get("tags") or []
    best, best_count = None, 0
    for t in tags:
        t_lower = t.lower().strip()
        if t_lower in TECH_TAGS or len(t) <= 1:
            continue
        cnt = tag_freq.get(t, 0)
        if cnt > best_count:
            best, best_count = t, cnt
    return best

def get_category_article(bot):
    """Get AI article for bot's best category."""
    best_tag = best_category_tag(bot)
    if best_tag and best_tag in CATEGORY_ARTICLES:
        return best_tag, CATEGORY_ARTICLES[best_tag]
    return None, None

SITE_URL = "https://tgbotarchive.com"

def esc(s):
    if not s: return ""
    return html.escape(str(s), quote=True)

def slugify(s):
    """Create a safe filesystem/URL slug from a tag name."""
    if not s: return ""
    # Remove leading # and special chars, replace spaces with -
    slug = s.lstrip("#!@$%^&*").strip()
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '', slug.replace(' ', '-'))
    # Remove leading/trailing dashes
    slug = slug.strip('-').lower()
    if not slug or len(slug) < 1:
        return None
    return slug

def star_str(n):
    return "⭐" * min(max(round(n or 0), 0), 5)

# ── Tag category descriptions ──
TAG_DESCRIPTIONS = {
    "ai": "artificial intelligence and machine learning",
    "search": "search and discovery",
    "download": "downloading files, videos, and media",
    "music": "music streaming, searching, and downloading",
    "video": "video processing, downloading, and streaming",
    "image": "image generation, editing, and manipulation",
    "game": "gaming and entertainment",
    "games": "gaming and entertainment",
    "fun": "entertainment and humor",
    "utility": "general utilities and tools",
    "tools": "productivity tools and utilities",
    "tool": "practical tools and utilities",
    "productivity": "productivity and work efficiency",
    "crypto": "cryptocurrency, blockchain, and trading",
    "news": "news aggregation and updates",
    "weather": "weather forecasts and information",
    "education": "learning and educational content",
    "anime": "anime and manga related content",
    "social": "social media integration and management",
    "shopping": "online shopping and price tracking",
    "finance": "financial management and tracking",
    "health": "health, fitness, and wellness",
    "food": "food, recipes, and nutrition",
    "travel": "travel information and booking",
    "security": "security and privacy protection",
    "privacy": "privacy protection and anonymity",
    "proxy": "proxy and VPN services",
    "vpn": "VPN and anonymization services",
    "admin": "group and channel administration",
    "moderation": "content moderation and management",
    "antispam": "spam protection and prevention",
    "protection": "account and group protection",
    "group": "group management and enhancement",
    "groups": "group management features",
    "channel": "channel management and promotion",
    "channels": "channel management and discovery",
    "inline": "inline query functionality",
    "bot": "bot building and development",
    "telegram": "Telegram platform utilities",
    "telegrambot": "Telegram bot development",
    "text": "text processing and manipulation",
    "sticker": "sticker creation and management",
    "gif": "GIF search and creation",
    "photo": "photo editing and processing",
    "photos": "photo management and editing",
    "editor": "photo and video editing",
    "voice": "voice messages and audio processing",
    "audio": "audio processing and music",
    "file": "file management and sharing",
    "files": "file storage and sharing",
    "converter": "file and format conversion",
    "cloud": "cloud storage and sync",
    "backup": "data backup and restoration",
    "translate": "language translation and learning",
    "language": "language learning and translation",
    "english": "English language learning",
    "russian": "Russian language content",
    "feedback": "feedback collection and forms",
    "poll": "polls and voting",
    "quiz": "quizzes and trivia",
    "reminder": "reminders and notifications",
    "notifications": "notifications and alerts",
    "alarm": "alarms and reminders",
    "timer": "timers and countdowns",
    "calendar": "calendar and scheduling",
    "scheduler": "scheduling and planning",
    "todo": "task management and to-do lists",
    "notes": "note-taking and documentation",
    "bookmark": "bookmark and link management",
    "url": "URL shortening and link management",
    "link": "link management and sharing",
    "share": "content sharing and forwarding",
    "upload": "file uploading and hosting",
    "repost": "content reposting and forwarding",
    "forward": "message forwarding",
    "crosspost": "cross-posting between channels",
    "rss": "RSS feed monitoring and updates",
    "feed": "RSS and content feeds",
    "blog": "blogging and content publishing",
    "website": "website monitoring and management",
    "domain": "domain management and DNS",
    "hosting": "hosting and server management",
    "server": "server management and monitoring",
    "monitoring": "system and service monitoring",
    "analytics": "analytics and statistics",
    "stats": "statistics and metrics tracking",
    "tracker": "tracking and monitoring",
    "price": "price tracking and alerts",
    "trade": "trading and exchange",
    "trading": "cryptocurrency and stock trading",
    "invest": "investment tracking and management",
    "wallet": "cryptocurrency wallets and management",
    "exchange": "currency exchange and conversion",
    "donation": "donations and fundraising",
    "payment": "payment processing and invoicing",
    "invoice": "invoicing and billing",
    "subscription": "subscription management",
    "membership": "membership management",
    "referral": "referral program management",
    "coupon": "coupons and discounts",
    "discounts": "discounts and deals",
    "deals": "deals and special offers",
    "promo": "promotions and marketing",
    "marketing": "marketing and promotion tools",
    "advertising": "advertising and ad management",
    "affiliate": "affiliate marketing tools",
    "ecommerce": "e-commerce and online stores",
    "store": "online store management",
    "shop": "shopping and e-commerce",
    "business": "business tools and management",
    "crm": "customer relationship management",
    "support": "customer support and helpdesk",
    "ticket": "ticketing and support systems",
    "help": "help and support tools",
    "faq": "FAQ and knowledge base",
    "wiki": "wiki and knowledge management",
    "database": "database management",
    "api": "API integration and development",
    "webhook": "webhook integration and management",
    "web": "web integration and tools",
    "browser": "browser integration and automation",
    "automation": "task automation and workflows",
    "workflow": "workflow automation",
    "integration": "third-party service integration",
    "logistics": "logistics and delivery tracking",
    "delivery": "delivery tracking and management",
    "tracking": "package and shipment tracking",
    "shipping": "shipping and logistics",
    "job": "job search and recruitment",
    "jobs": "job listings and recruitment",
    "hiring": "hiring and recruitment tools",
    "resume": "resume building and job applications",
    "freelance": "freelancing and gig economy",
    "dating": "dating and social connections",
    "meeting": "meeting scheduling and coordination",
    "event": "event planning and management",
    "events": "events and meetups",
    "booking": "booking and reservations",
    "reservation": "reservations and scheduling",
    "appointment": "appointment scheduling",
    "qr": "QR code generation and scanning",
    "barcode": "barcode generation and scanning",
    "nfc": "NFC tag reading and writing",
    "ip": "IP address and network tools",
    "network": "network tools and diagnostics",
    "dns": "DNS lookup and management",
    "ssl": "SSL certificate checking",
    "seo": "SEO analysis and tools",
    "generator": "content and data generation",
    "maker": "content creation tools",
    "creator": "content creation and management",
    "builder": "builders and construction tools",
    "design": "design tools and graphics",
    "template": "template and form creation",
    "form": "form creation and management",
    "survey": "surveys and data collection",
    "export": "data export and extraction",
    "import": "data import and migration",
    "sync": "data synchronization",
    "migration": "data migration tools",
    "scraper": "web scraping and data extraction",
    "parser": "data parsing and processing",
    "extractor": "data extraction tools",
    "downloader": "content downloading tools",
    "saver": "content saving and archiving",
    "archiver": "archiving and compression",
    "compress": "file compression and archiving",
    "zip": "ZIP file creation and extraction",
    "unzip": "file extraction and decompression",
    "pdf": "PDF creation, editing, and conversion",
    "document": "document processing and management",
    "spreadsheet": "spreadsheet management",
    "csv": "CSV file processing",
    "json": "JSON data processing",
    "xml": "XML data processing",
    "code": "code sharing and formatting",
    "coding": "coding and development tools",
    "programming": "programming and development",
    "developer": "developer tools and APIs",
    "devops": "DevOps and deployment tools",
    "git": "Git repository management",
    "github": "GitHub integration and management",
    "docker": "Docker container management",
    "sql": "SQL query tools",
    "nosql": "NoSQL database tools",
    "redis": "Redis cache management",
    "deploy": "deployment and hosting",
    "ci": "continuous integration tools",
    "cd": "continuous deployment tools",
    "test": "testing and QA tools",
    "testing": "software testing tools",
    "debug": "debugging and troubleshooting",
    "error": "error tracking and monitoring",
    "log": "log management and analysis",
    "performance": "performance monitoring",
    "speed": "speed testing and optimization",
    "optimization": "optimization tools",
    "math": "mathematical calculations",
    "calculator": "calculators and computations",
    "count": "counting and statistics",
    "counter": "counters and tracking",
    "clock": "clocks and time management",
    "time": "time management and timezone conversion",
    "timezone": "timezone conversion tools",
    "date": "date and time tools",
}

# ── Generate bot content sections ──
def jsonld_website():
    """JSON-LD for main page — WebSite + WebPage."""
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "BotsArchive",
                "url": SITE_URL,
                "description": f"Catalog of {len(bots)} Telegram bots with multilingual descriptions, ratings, and tags.",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{SITE_URL}/?search={{search_term_string}}",
                    "query-input": "required name=search_term_string"
                }
            },
            {
                "@type": "WebPage",
                "name": "BotsArchive — Telegram Bots Catalog",
                "url": SITE_URL,
                "inLanguage": ["en", "ru", "fa"],
                "about": {"@type": "Thing", "name": "Telegram Bots"},
                "dateModified": datetime.now().strftime("%Y-%m-%d")
            }
        ]
    }

def jsonld_tag(tag_name, count):
    """JSON-LD for tag page — CollectionPage."""
    label = TAG_DESCRIPTIONS.get(tag_name.lower(), tag_name)
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"#{tag_name} — {count} Telegram Bots",
        "description": f"Browse {count} Telegram bots related to {label}. Find the best {tag_name} bots with ratings, features, and descriptions.",
        "url": f"{SITE_URL}/tag/{slugify(tag_name)}.html",
        "about": {"@type": "Thing", "name": f"Telegram {tag_name} bots"},
        "numberOfItems": count,
        "inLanguage": ["en", "ru", "fa"],
        "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "BotsArchive", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": f"#{tag_name}", "item": f"{SITE_URL}/tag/{slugify(tag_name)}.html"}
        ]}
    }

def jsonld_bot(bot):
    """JSON-LD for bot page — SoftwareApplication."""
    name = bot.get("name", bot["username"])
    desc = (bot.get("description", "") or "")[:500]
    rating_score = bot.get("rating_score")
    rating_votes = bot.get("rating_votes", 0)
    tags = bot.get("tags") or []
    langs = bot.get("languages", "") or ""
    inline = bot.get("inline", "no")
    groups = bot.get("groups", "no")
    categories = [TAG_DESCRIPTIONS.get(t.lower(), t) for t in tags[:5]]

    app = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name,
        "url": f"https://t.me/{bot['username']}",
        "applicationUrl": f"https://t.me/{bot['username']}",
        "operatingSystem": "Telegram (cross-platform)",
        "applicationCategory": "TelegramBot",
        "description": desc,
        "inLanguage": ["en", "ru", "fa"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "BotsArchive", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": name, "item": f"{SITE_URL}/bot/{esc(bot['username'])}.html"}
        ]}
    }
    if categories:
        app["applicationSubCategory"] = ", ".join(categories)
    if rating_score and rating_votes:
        app["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating_score,
            "ratingCount": rating_votes,
            "bestRating": 5
        }
    if langs and langs != "—":
        lang_list = list(dict.fromkeys(langs.split()))[:10]
        app["availableLanguage"] = lang_list
    if inline == "yes" or groups == "yes":
        features = []
        if inline == "yes": features.append("inline mode")
        if groups == "yes": features.append("group chat support")
        app["featureList"] = ", ".join(features)
    return app

def tag_category(tag):
    """Get human-readable category description for a tag."""
    return TAG_DESCRIPTIONS.get(tag.lower(), tag)

def generate_bot_about(bot):
    """Generate expanded 'About this bot' content from available data."""
    tags = bot.get("tags") or []
    langs = bot.get("languages", "") or ""
    inline = bot.get("inline", "no")
    groups = bot.get("groups", "no")
    desc = bot.get("description", "") or ""

    parts = ["<div class=\"about-section\">"]
    parts.append('<div class="section-title">📋 About This Bot</div>')

    if tags:
        tag_labels = [tag_category(t) for t in tags[:5]]
        if len(tag_labels) == 1:
            parts.append(f'<p>This bot belongs to the <strong>{tag_labels[0]}</strong> category.</p>')
        elif len(tag_labels) <= 3:
            parts.append(f'<p>This bot specializes in <strong>{", ".join(tag_labels[:-1])}</strong> and <strong>{tag_labels[-1]}</strong>.</p>')
        else:
            parts.append(f'<p>This bot covers <strong>{", ".join(tag_labels[:3])}</strong> and more.</p>')

    features = []
    if desc:
        features.append(f'<li>{esc(desc[:200])}</li>')
    if langs and langs != "—":
        lang_count = len([l for l in langs.split() if l.strip()])
        features.append(f'<li>🌐 Supports <strong>{lang_count}</strong> language{"s" if lang_count > 1 else ""}</li>')
    if inline == "yes" or groups == "yes":
        modes = []
        if inline == "yes": modes.append("inline mode (type @bot in any chat)")
        if groups == "yes": modes.append("group chat mode")
        features.append(f'<li>⚡ Works via {esc(" and ".join(modes))}</li>')

    if features:
        parts.append('<ul class="feature-list">')
        parts.extend(features)
        parts.append('</ul>')

    parts.append("</div>")
    return "\n".join(parts)

def generate_bot_tags_section(bot):
    """Generate expanded tags section with category descriptions."""
    tags = bot.get("tags") or []
    if not tags:
        return ""

    parts = ['<div class="tags-section">']
    parts.append('<div class="section-title">🏷️ Categories & Tags</div>')
    parts.append('<div class="tag-grid">')
    for t in tags:
        label = tag_category(t)
        slug = esc(t)
        parts.append(
            f'<a href="/tag/{slugify(slug)}.html" class="tag-card" title="Browse {label} bots">'
            f'<span class="tag-name">#{esc(t)}</span>'
            f'<span class="tag-desc">{esc(label)}</span></a>'
        )
    parts.append('</div></div>')
    return "\n".join(parts)

# ── Bot article section (comparison articles generated daily) ──
def bot_article_html(bot):
    """Show AI-generated comparison article for this bot, rendered via markdown2."""
    username = bot["username"]
    if username not in BOT_ARTICLES:
        return ""
    art = BOT_ARTICLES[username]
    article_text = art.get("article", "")
    if not article_text:
        return ""
    article_html = markdown2.markdown(article_text, extras=['tables', 'fenced-code-blocks', 'code-friendly'], safe_mode='escape')
    date_str = esc(art.get("date", ""))
    return f'''
<div class="article-section">
  <div class="section-title">📖 In-Depth Review</div>
  <div class="article-content">
    {article_html}
  </div>
  {"".join(f'<div class="review-date" style="margin-top:0.5rem;">Article generated: {date_str}</div>' if date_str else '')}
</div>'''

# ── Why Choose section (bot advantages) ──
def why_choose_html(bot):
    """Generate bot-specific advantages section."""
    tag, _ = get_category_article(bot)
    tag_label = TAG_DESCRIPTIONS.get(tag.lower(), tag) if tag else "Telegram"

    desc = bot.get("description", "") or ""
    name = esc(bot.get("name", bot["username"]))
    rating = bot.get("rating_score", "")
    votes = bot.get("rating_votes", 0)
    langs = bot.get("languages", "") or ""

    advantages = []
    if rating and float(rating) >= 4.0:
        advantages.append(f"⭐ High rating: {rating}/5 from {votes} users")
    if langs and langs != "—":
        lang_count = len([l for l in langs.split() if l.strip()])
        if lang_count >= 3:
            advantages.append(f"🌐 Supports {lang_count} languages, accessible globally")
    if bot.get("inline") == "yes":
        advantages.append(f"⚡ Works in inline mode — use @{esc(bot['username'])} in any chat")
    if bot.get("groups") == "yes":
        advantages.append("👥 Fully compatible with group chats")

    if not advantages:
        advantages.append(f"🤖 A dedicated bot focused on {tag_label} tasks")

    bot_desc = esc(desc[:300])

    return f'''
<div class="article-section">
  <div class="section-title">✨ Why Choose {name}</div>
  <div class="article-content">
    <p>{bot_desc}</p>
    <ul class="advantage-list">
      {"".join(f"<li>{a}</li>" for a in advantages)}
    </ul>
  </div>
</div>'''

# ── Reviews section ──
REVIEWS_FILE = os.path.join(SCRIPT_DIR, "reviews.json")
ALL_REVIEWS = {}
if os.path.exists(REVIEWS_FILE):
    ALL_REVIEWS = json.load(open(REVIEWS_FILE))

def reviews_html(bot):
    username = bot["username"]
    reviews = ALL_REVIEWS.get(username, [])
    if not reviews:
        return ""
    items = []
    for r in reviews[-3:]:
        items.append(f'<div class="review-item"><span class="review-text">{esc(r["text"])}</span> <span class="review-date">— {esc(r["date"])}</span></div>')
    return f'''
<div class="reviews-section">
  <div class="section-title">💬 User Reviews</div>
  {"".join(items)}
</div>'''

# ── Related bots ──
def get_related(bot, all_bots, limit=5):
    bot_tags = set(bot.get("tags") or [])
    if not bot_tags:
        return []
    scored = []
    for other in all_bots:
        if other["username"] == bot["username"]:
            continue
        other_tags = set(other.get("tags") or [])
        shared = len(bot_tags & other_tags)
        if shared > 0:
            scored.append((shared, other))
    scored.sort(key=lambda x: -x[0])
    return [b for _, b in scored[:limit]]

def related_html(bot, all_bots):
    rel = get_related(bot, all_bots)
    if not rel:
        return ""
    items = []
    for r in rel:
        name = esc(r.get("name", r["username"]))
        username = esc(r["username"])
        desc = esc((r.get("description", "") or "")[:80])
        items.append(
            f'<a href="/bot/{username}.html" class="rel-item">'
            f'<div class="rel-name">🤖 {name}</div>'
            f'<div class="rel-desc">{desc}</div></a>'
        )
    return f'''
<div class="related">
  <div class="rel-label">🔗 Similar Bots</div>
  {"".join(items)}
</div>'''

# ── Bot page HTML ──
def bot_page_html(bot, all_bots):
    desc_en = bot.get("description", "")
    desc_ru = bot.get("desc_ru", desc_en)
    desc_fa = bot.get("desc_fa", desc_en)
    bot_url = f"https://t.me/{bot['username']}"
    tags_html = " ".join(f'<a href="/tag/{slugify(t)}.html" class="tag">#{esc(t)}</a>' for t in (bot.get("tags") or []))

    about_html = generate_bot_about(bot)
    tags_section_html = generate_bot_tags_section(bot)
    comp_article_html = bot_article_html(bot)
    why_html = why_choose_html(bot)

    meta_desc = desc_en[:150]
    if bot.get("tags"):
        meta_desc += f" Categories: {', '.join(bot.get('tags', [])[:6])}."

    views = bot.get("views", 0)
    views_str = f"👁 {views:,}" if views else ""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-V2Q3J579VZ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-V2Q3J579VZ');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(bot.get("name", bot["username"]))} — Telegram Bot | BotsArchive</title>
<meta name="description" content="{esc(meta_desc[:200])}">
<link rel="canonical" href="{SITE_URL}/bot/{esc(bot["username"])}.html">
<link rel="alternate" hreflang="en" href="{SITE_URL}/bot/{esc(bot["username"])}.html">
<link rel="alternate" hreflang="ru" href="{SITE_URL}/bot/{esc(bot["username"])}.html?lang=ru">
<link rel="alternate" hreflang="fa" href="{SITE_URL}/bot/{esc(bot["username"])}.html?lang=fa">
<meta property="og:title" content="{esc(bot.get("name", bot["username"]))}">
<meta property="og:description" content="{esc(meta_desc[:200])}">
<meta property="og:url" content="{SITE_URL}/bot/{esc(bot["username"])}.html">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
<script type="application/ld+json">
{json.dumps(jsonld_bot(bot), ensure_ascii=False)}
</script>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e8e8f0; max-width: 720px; margin: 0 auto; padding: 2rem 1rem; line-height: 1.7; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
.username {{ color: #6c63ff; font-size: 1rem; margin-bottom: 0.5rem; }}
.rating {{ color: #ffd700; margin-bottom: 0.5rem; }}
.desc {{ color: #aaa; margin: 1rem 0; }}
.desc-block {{ border-left: 2px solid #2a2a4a; padding-left: 0.8rem; margin: 0.6rem 0; }}
.desc-label {{ color: #6c63ff; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.2rem; }}
.info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.3rem; margin: 1rem 0; color: #888; font-size: 0.85rem; }}
.info span {{ color: #e8e8f0; font-weight: 500; }}
.tags {{ margin: 0.8rem 0; }}
.tag {{ display: inline-block; padding: 0.15rem 0.5rem; background: #2a2a4a; color: #8888aa; border-radius: 10px; font-size: 0.75rem; margin: 0.15rem; text-decoration: none; }}
.tag:hover {{ background: #6c63ff; color: #fff; }}
.btn {{ display: inline-block; padding: 0.6rem 1.5rem; background: #6c63ff; color: #fff; border-radius: 8px; text-decoration: none; font-size: 0.95rem; text-align: center; width: 100%; }}
.btn:hover {{ background: #7c73ff; }}
.about-section {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.8rem 1rem; margin: 1rem 0; }}
.section-title {{ color: #6c63ff; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }}
.about-section p {{ color: #aaa; font-size: 0.9rem; margin: 0.3rem 0; }}
.feature-list {{ margin: 0.4rem 0 0 1.2rem; color: #aaa; font-size: 0.88rem; }}
.feature-list li {{ margin-bottom: 0.2rem; }}
.tags-section {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.8rem 1rem; margin: 1rem 0; }}
.tag-grid {{ display: flex; flex-wrap: wrap; gap: 0.4rem; }}
.tag-card {{ display: inline-block; background: #2a2a4a; border-radius: 6px; padding: 0.3rem 0.6rem; text-decoration: none; border: 1px solid #3a3a5a; }}
.tag-card:hover {{ border-color: #6c63ff; background: #23234a; }}
.tag-name {{ color: #e8e8f0; font-size: 0.8rem; display: block; }}
.tag-desc {{ color: #8888aa; font-size: 0.7rem; display: block; }}
.article-section {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.8rem 1rem; margin: 1rem 0; }}
.article-content {{ color: #c0c0d0; font-size: 0.9rem; line-height: 1.8; }}
.article-content p {{ margin-bottom: 0.6rem; }}
.article-content h2 {{ color: #e8e8f0; font-size: 1.2rem; margin: 1rem 0 0.5rem; }}
.article-content h3 {{ color: #d0d0e0; font-size: 1.05rem; margin: 0.8rem 0 0.4rem; }}
.article-content h4 {{ color: #c8c8d8; font-size: 0.95rem; margin: 0.6rem 0 0.3rem; }}
.article-content ul {{ margin: 0.4rem 0 0.4rem 1.2rem; }}
.article-content ol {{ margin: 0.4rem 0 0.4rem 1.4rem; }}
.article-content li {{ margin-bottom: 0.2rem; }}
.article-content table {{ width: 100%; border-collapse: collapse; margin: 0.6rem 0; font-size: 0.82rem; }}
.article-content th, .article-content td {{ border: 1px solid #3a3a5a; padding: 0.4rem 0.6rem; text-align: left; }}
.article-content th {{ background: #2a2a4a; color: #e8e8f0; font-weight: 600; }}
.article-content td {{ color: #c0c0d0; }}
.article-content tr:nth-child(even) td {{ background: #1e1e32; }}
.article-content code {{ background: #2a2a4a; color: #ff79c6; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85em; }}
.article-content pre {{ background: #12121e; border: 1px solid #2a2a4a; border-radius: 6px; padding: 0.8rem; overflow-x: auto; margin: 0.6rem 0; }}
.article-content pre code {{ background: none; padding: 0; color: #c0c0d0; }}
.advantage-list {{ list-style: none; padding: 0; margin: 0.5rem 0 0 0; }}
.advantage-list li {{ padding: 0.2rem 0; color: #a0a0b8; font-size: 0.88rem; }}
.reviews-section {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.8rem 1rem; margin: 1rem 0; }}
.review-item {{ padding: 0.4rem 0; border-bottom: 1px solid #2a2a4a; }}
.review-item:last-child {{ border-bottom: none; }}
.review-text {{ color: #d0d0e0; font-size: 0.9rem; font-style: italic; }}
.review-date {{ color: #666; font-size: 0.75rem; }}
.related {{ margin: 1.5rem 0; padding-top: 0.5rem; border-top: 1px solid #2a2a4a; }}
.rel-label {{ color: #6c63ff; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }}
.rel-item {{ display: block; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.4rem; text-decoration: none; }}
.rel-item:hover {{ background: #23234a; border-color: #6c63ff; }}
.rel-name {{ color: #e8e8f0; font-size: 0.9rem; font-weight: 600; }}
.rel-desc {{ color: #8888aa; font-size: 0.8rem; margin-top: 0.1rem; }}
.back {{ display: block; margin-top: 1rem; color: #6c63ff; text-decoration: none; }}
</style>
</head>
<body>
<a href="/" style="color:#6c63ff;text-decoration:none;font-size:0.85rem;">← BotsArchive</a>
<a href="https://t.me/tgbotarchivesupportbot" target="_blank" style="float:right;color:#6c63ff;font-size:0.82rem;text-decoration:none;">💬 Feedback</a>
<img src="https://t.me/i/userpic/320/{esc(bot['username'])}.jpg" alt="" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin:0.5rem 0;background:#2a2a4a;" onerror="this.style.display='none'">
<h1>🤖 {esc(bot.get('name', bot['username']))}</h1>
<div class="username">@{esc(bot["username"])} — <a href="{bot_url}" style="color:#6c63ff;">Open in Telegram</a></div>
<div class="rating">{star_str(bot.get("stars", 0))} {bot.get("rating_score", "")}{" · " + str(bot.get("rating_votes", 0)) + " votes" if bot.get("rating_votes") else ""}</div>

<div class="desc">
  <div class="desc-label">🇬🇧 English</div>
  <div class="desc-block">{esc(desc_en)}</div>
  <div class="desc-label">🇷🇺 Русский</div>
  <div class="desc-block">{esc(desc_ru)}</div>
  <div class="desc-label">🇮🇷 فارسی</div>
  <div class="desc-block" dir="rtl">{esc(desc_fa)}</div>
</div>

{about_html}

<div class="info">
  <div>🌐 Languages: <span>{esc(bot.get("languages", "—"))}</span></div>
  <div>💬 Inline: <span>{bot.get("inline", "no")}</span></div>
  <div>👥 Groups: <span>{bot.get("groups", "no")}</span></div>
  <div>👁 Views: <span>{views_str or "—"}</span></div>
</div>

{tags_section_html}

{comp_article_html}

{why_html}

{reviews_html(bot)}

{related_html(bot, all_bots)}

<a class="btn" href="{bot_url}" target="_blank">🤖 Open @{esc(bot["username"])}</a>
<a class="back" href="/">← Back to catalog</a>
</body>
</html>'''

# ── Tag page HTML ──
def tag_article_html(tag_name):
    """Get AI article for a tag page, rendered via markdown2."""
    if tag_name in CATEGORY_ARTICLES:
        article_html = markdown2.markdown(CATEGORY_ARTICLES[tag_name].strip(), extras=['tables', 'fenced-code-blocks', 'code-friendly'], safe_mode='escape')
        return f'''
<div class="tag-article">
  <h2>📖 About {esc(TAG_DESCRIPTIONS.get(tag_name.lower(), tag_name))} Bots</h2>
  <div class="tag-article-content">
    {article_html}
  </div>
</div>'''
    return ""

def tag_page_html(tag, count, bots_with_tag):
    tag_label = tag_category(tag)
    title = f"#{tag} — {count} Telegram Bots | BotsArchive"
    desc_meta = esc(f"Browse {count} Telegram bots tagged #{tag} — {tag_label}. Find the best {tag} bots, compare features, ratings, and languages.")
    tag_slug = esc(tag)

    # Add AI article at top of tag page
    article_html = tag_article_html(tag)

    bot_list = ""
    for b in bots_with_tag:
        username = b["username"]
        name = b.get("name", username)
        desc = (b.get("description", "") or "")[:120]
        rating = b.get("rating_score", 0)
        stars = star_str(b.get("stars", 0))
        bot_list += f'''<div class="bot-item">
  <a href="/bot/{esc(username)}.html" class="bot-name">🤖 {esc(name)}</a>
  <div class="bot-username">@{esc(username)}</div>
  <div class="bot-desc">{esc(desc)}</div>
  {f'<div class="bot-rating">{stars} {rating}</div>' if rating else ''}
</div>
'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-V2Q3J579VZ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-V2Q3J579VZ');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc_meta}">
<link rel="canonical" href="{SITE_URL}/tag/{tag_slug}.html">
<link rel="alternate" hreflang="en" href="{SITE_URL}/tag/{tag_slug}.html">
<link rel="alternate" hreflang="ru" href="{SITE_URL}/tag/{tag_slug}.html?lang=ru">
<link rel="alternate" hreflang="fa" href="{SITE_URL}/tag/{tag_slug}.html?lang=fa">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc_meta}">
<meta property="og:url" content="{SITE_URL}/tag/{tag_slug}.html">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
<script type="application/ld+json">
{json.dumps(jsonld_tag(tag, count), ensure_ascii=False)}
</script>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e8e8f0; max-width: 720px; margin: 0 auto; padding: 2rem 1rem; line-height: 1.7; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
.tag-intro {{ color: #8888aa; font-size: 0.9rem; margin-bottom: 1.5rem; line-height: 1.5; }}
.count {{ color: #6c63ff; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 1rem; }}
.tag-layout {{ display: flex; gap: 1.5rem; align-items: flex-start; }}
.tag-layout-left {{ flex: 0 0 340px; min-width: 280px; max-width: 100%; }}
.tag-layout-left:empty {{ display: none; }}
.tag-layout-right {{ flex: 1; min-width: 0; }}
.tag-article {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 1rem; }}
.tag-article h2 {{ color: #6c63ff; font-size: 1.05rem; margin-bottom: 0.6rem; }}
.tag-article-content {{ color: #c0c0d0; font-size: 0.85rem; line-height: 1.7; }}
.tag-article-content p {{ margin-bottom: 0.5rem; }}
.tag-article-content h2 {{ color: #d0d0e0; font-size: 1rem; margin: 0.6rem 0 0.3rem; }}
.tag-article-content h3 {{ color: #c8c8d8; font-size: 0.92rem; margin: 0.5rem 0 0.3rem; }}
.tag-article-content ul {{ margin: 0.3rem 0 0.3rem 1rem; }}
.tag-article-content ol {{ margin: 0.3rem 0 0.3rem 1.2rem; }}
.tag-article-content li {{ margin-bottom: 0.15rem; }}
.tag-article-content table {{ width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.78rem; }}
.tag-article-content th, .tag-article-content td {{ border: 1px solid #3a3a5a; padding: 0.3rem 0.4rem; text-align: left; }}
.tag-article-content th {{ background: #2a2a4a; color: #d0d0e0; font-weight: 600; }}
.tag-article-content tr:nth-child(even) td {{ background: #1e1e32; }}
.tag-article-content code {{ background: #2a2a4a; color: #ff79c6; padding: 0.1rem 0.25rem; border-radius: 3px; font-size: 0.85em; }}
.tag-article-content pre {{ background: #12121e; border: 1px solid #2a2a4a; border-radius: 6px; padding: 0.6rem; overflow-x: auto; margin: 0.5rem 0; }}
@media (max-width: 768px) {{
  .tag-layout {{ flex-direction: column; gap: 1rem; }}
  .tag-layout-left {{ flex: none; width: 100%; min-width: 0; }}
}}
.bot-item {{ background: #1a1a2e; border-radius: 8px; padding: 0.8rem 1rem; margin-bottom: 0.6rem; border: 1px solid #2a2a4a; }}
.bot-item:hover {{ border-color: #6c63ff; }}
.bot-name {{ color: #e8e8f0; font-size: 1rem; font-weight: 600; text-decoration: none; }}
.bot-name:hover {{ color: #6c63ff; }}
.bot-username {{ color: #6c63ff; font-size: 0.82rem; margin: 0.1rem 0; }}
.bot-desc {{ color: #8888aa; font-size: 0.85rem; margin: 0.3rem 0; }}
.bot-rating {{ color: #ffd700; font-size: 0.82rem; }}
.back {{ display: block; margin-top: 1rem; color: #6c63ff; text-decoration: none; }}
a {{ color: #6c63ff; }}
</style>
</head>
<body>
<h1>🤖 #{esc(tag)}</h1>
<div class="tag-intro">Telegram bots related to <strong>{esc(tag_label)}</strong>. Browse <strong>{count}</strong> bot{"s" if count != 1 else ""} in this category, compare ratings, features, and languages.</div>

<div class="tag-layout">
  <div class="tag-layout-left">
    {article_html}
  </div>
  <div class="tag-layout-right">
    <div class="count">{count} bot{"s" if count != 1 else ""} tagged #{esc(tag)}</div>
    {bot_list}
  </div>
</div>
<a class="back" href="/">← Back to catalog</a>
</body>
</html>'''

# ── 404 page ──
def page_404_html():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page Not Found — BotsArchive</title>
<meta name="robots" content="noindex, follow">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e8e8f0; max-width: 500px; margin: 0 auto; padding: 4rem 1rem; text-align: center; line-height: 1.7; }
h1 { font-size: 3rem; margin-bottom: 0.5rem; color: #6c63ff; }
p { color: #8888aa; }
a { color: #6c63ff; }
.btn { display: inline-block; padding: 0.6rem 1.5rem; background: #6c63ff; color: #fff; border-radius: 8px; text-decoration: none; margin-top: 1rem; }
</style>
</head>
<body>
<h1>404</h1>
<p>This page doesn't exist in our archive.</p>
<a class="btn" href="/">← Browse BotsArchive</a>
</body>
</html>'''

# ── Generate ALL tag pages ──
tag_counter = Counter()
for b in bots:
    for t in b.get("tags", []):
        tag_counter[t] += 1

tag_bots = {}
for b in bots:
    for t in b.get("tags", []):
        tag_bots.setdefault(t, []).append(b)

tag_count = 0
for tag_name, tag_freq_val in sorted(tag_counter.items()):
    tag_slug = slugify(tag_name)
    if not tag_slug:
        continue
    filepath = os.path.join(TAGS_DIR, f"{tag_slug}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(tag_page_html(tag_name, tag_freq_val, tag_bots.get(tag_name, [])))
    tag_count += 1
print(f"Generated {tag_count} tag pages (all tags)")

# ── Generate 404.html ──
with open(os.path.join(OUTPUT_DIR, "404.html"), "w", encoding="utf-8") as f:
    f.write(page_404_html())
print("Generated 404.html")

# ── Generate individual bot pages ──
count = 0
for bot in bots:
    username = bot.get("username")
    if not username:
        continue
    filepath = os.path.join(BOTS_DIR, f"{username}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(bot_page_html(bot, bots))
    count += 1
print(f"Generated {count} bot pages")

# ── Generate Sitemap ──
today = datetime.now().strftime("%Y-%m-%d")

def bot_priority(bot):
    return 0.9 if (bot.get("rating_score", 0) or 0) >= 4.0 else 0.6

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>\n'

for tag_name in sorted(tag_counter.keys()):
    sitemap += f'  <url><loc>{SITE_URL}/tag/{slugify(tag_name)}.html</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>\n'

for bot in bots:
    if not bot.get("username"):
        continue
    p = bot_priority(bot)
    sitemap += f'  <url><loc>{SITE_URL}/bot/{esc(bot["username"])}.html</loc><lastmod>{today}</lastmod><priority>{p}</priority></url>\n'

sitemap += '</urlset>'

with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(sitemap)
sitemap_urls = 1 + tag_count + count
print(f"Sitemap: {sitemap_urls} URLs (1 main + {tag_count} tags + {count} bots)")

with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w") as f:
    f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
print("robots.txt written")

existing_index = open(os.path.join(OUTPUT_DIR, "index.html"), "r", encoding="utf-8").read()

seo_meta = f'''<meta charset="UTF-8">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-V2Q3J579VZ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-V2Q3J579VZ');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BotsArchive — {len(bots)} Telegram Bots Catalog | Search by Tags, Rating, Languages</title>
<meta name="description" content="The most powerful archive of Telegram bots. Browse {len(bots)} bots in English, Russian and Persian. Search by tags, rating, languages, and category.">
<meta name="keywords" content="Telegram bots, bot directory, Telegram bot catalog, Telegram bot search">
<link rel="canonical" href="{SITE_URL}/">
<link rel="alternate" hreflang="en" href="{SITE_URL}/">
<link rel="alternate" hreflang="ru" href="{SITE_URL}/?lang=ru">
<link rel="alternate" hreflang="fa" href="{SITE_URL}/?lang=fa">
<meta property="og:title" content="BotsArchive — Telegram Bots">
<meta property="og:description" content="Browse and search {len(bots)} Telegram bots with descriptions in 3 languages.">
<meta property="og:url" content="{SITE_URL}/">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
<script type="application/ld+json">
{json.dumps(jsonld_website(), ensure_ascii=False)}
</script>'''

if '<style>' in existing_index:
    existing_index = re.sub(
        r'<meta charset="UTF-8">.*?<style>',
        seo_meta + '<style>',
        existing_index, flags=re.DOTALL
    )
else:
    existing_index = re.sub(
        r'<meta charset="UTF-8">.*?</head>',
        seo_meta + '</head>',
        existing_index, flags=re.DOTALL
    )

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(existing_index)
print("index.html updated with SEO meta")

# ── IndexNow Integration: Notify search engines about changed URLs ──
INDEXNOW_KEY_FILE = os.path.expanduser("~/.hermes/telegram_ub/indexnow_key.txt")

def get_or_create_indexnow_key():
    """Get existing IndexNow key or generate a new UUID key."""
    if os.path.exists(INDEXNOW_KEY_FILE):
        with open(INDEXNOW_KEY_FILE) as f:
            key = f.read().strip()
            if key:
                return key
    key = str(uuid.uuid4())
    os.makedirs(os.path.dirname(INDEXNOW_KEY_FILE), exist_ok=True)
    with open(INDEXNOW_KEY_FILE, "w") as f:
        f.write(key)
    print(f"IndexNow: Generated new key: {key}")
    return key

def submit_indexnow():
    """Submit all site URLs to IndexNow endpoints (general, Yandex, Bing)."""
    import httpx

    # Collect all site URLs
    urls = [f"{SITE_URL}/"]
    for tag_name in tag_counter:
        urls.append(f"{SITE_URL}/tag/{slugify(tag_name)}.html")
    for bot in bots:
        if bot.get("username"):
            urls.append(f"{SITE_URL}/bot/{esc(bot['username'])}.html")

    key = get_or_create_indexnow_key()

    # Write key file to site output so it's accessible at tgbotarchive.com/KEY.txt
    key_file_path = os.path.join(OUTPUT_DIR, f"{key}.txt")
    with open(key_file_path, "w") as f:
        f.write(key)
    print(f"IndexNow key file: {key_file_path}")

    # IndexNow limits: max 10,000 URLs per request
    url_batches = [urls[i:i+10000] for i in range(0, len(urls), 10000)]

    endpoints = [
        "https://api.indexnow.org/indexnow",
        "https://yandex.com/indexnow",
        "https://www.bing.com/indexnow",
    ]

    total_success = 0
    total_endpoints = len(endpoints)
    total_batches = len(url_batches)

    for batch_idx, url_list in enumerate(url_batches):
        payload = {
            "host": "tgbotarchive.com",
            "key": key,
            "keyLocation": f"{SITE_URL}/{key}.txt",
            "urlList": url_list,
        }
        for endpoint in endpoints:
            try:
                resp = httpx.post(endpoint, json=payload, timeout=30)
                if resp.status_code == 200:
                    print(f"  IndexNow OK [{batch_idx+1}/{total_batches}]: {endpoint}")
                    total_success += 1
                else:
                    print(f"  IndexNow {resp.status_code} [{batch_idx+1}/{total_batches}]: {endpoint} — {resp.text[:200]}")
            except Exception as e:
                print(f"  IndexNow error [{batch_idx+1}/{total_batches}]: {endpoint} — {e}")

    if total_success == total_endpoints * total_batches:
        print(f"IndexNow: All {total_endpoints} endpoints notified ({len(urls)} URLs in {total_batches} batch(es))")
    elif total_success > 0:
        print(f"IndexNow: {total_success}/{total_endpoints * total_batches} endpoint-batch requests succeeded (non-fatal)")
    else:
        print("IndexNow: All requests failed (non-fatal, build continues)")

print(f"\n=== FINAL SITE ===")
for f in ["index.html", "data.json", "tags.json", "sitemap.xml", "robots.txt", "404.html"]:
    fp = os.path.join(OUTPUT_DIR, f)
    if os.path.exists(fp):
        sz = os.path.getsize(fp)
        print(f"  {f}: {sz/1024:.1f} KB")
bot_count = len(os.listdir(BOTS_DIR))
bot_size = sum(os.path.getsize(os.path.join(BOTS_DIR, f)) for f in os.listdir(BOTS_DIR))
tag_count_d = len(os.listdir(TAGS_DIR))
tag_size = sum(os.path.getsize(os.path.join(TAGS_DIR, f)) for f in os.listdir(TAGS_DIR))
print(f"  b/ ({bot_count} pages): {bot_size/1024:.0f} KB")
print(f"  tag/ ({tag_count_d} pages): {tag_size/1024:.0f} KB")
print(f"  Total: {(bot_size + tag_size) / 1024 / 1024:.1f} MB")

# ── Notify search engines via IndexNow ──
submit_indexnow()
