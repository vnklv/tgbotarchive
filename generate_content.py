#!/usr/bin/env python3
"""Generate AI content for new bots: reviews, bot articles, category articles.
Uses DeepSeek API. Skips bots that already have content.
"""
import json, os, sys, hashlib, time
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Config ──
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

# Files to update
REVIEWS_FILE = os.path.join(SCRIPT_DIR, "reviews.json")
BOT_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "bot_articles.json")
CATEGORY_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "category_articles.json")

# ── Load existing data ──
def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {} if path.endswith(".json") else []

bots = json.load(open(os.path.join(SCRIPT_DIR, "data.json")))
reviews = load_json(REVIEWS_FILE) if os.path.exists(REVIEWS_FILE) else {}
bot_articles = load_json(BOT_ARTICLES_FILE) if os.path.exists(BOT_ARTICLES_FILE) else {}
category_articles = load_json(CATEGORY_ARTICLES_FILE) if os.path.exists(CATEGORY_ARTICLES_FILE) else {}

# ── AI call ──
def ask_deepseek(prompt, max_retries=2):
    if not API_KEY:
        return None
    import urllib.request, json as j
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                API_URL,
                data=j.dumps({
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500,
                }).encode(),
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = j.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  ⚠️ AI error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return None

# ── Generate reviews for new bots ──
def generate_reviews():
    changed = 0
    for bot in bots:
        bot_id = bot.get("id", "") or bot.get("name", "")
        if bot_id in reviews:
            continue  # already has reviews
        name = bot.get("name", bot_id)
        desc = bot.get("description", "")[:200]
        prompt = (
            f'Write 2 short positive user reviews for the Telegram bot "{name}". '
            f'Description: {desc}\n'
            f'Return as JSON array of objects with keys: text, author, date, rating.\n'
            f'Example: [{{"text":"Great bot!","author":"User123","date":"2026-07-15","rating":5}}]'
        )
        print(f"  Generating reviews for {name}...")
        result = ask_deepseek(prompt)
        if result:
            try:
                parsed = json.loads(result)
                reviews[bot_id] = parsed
                changed += 1
            except:
                pass
    if changed:
        with open(REVIEWS_FILE, "w") as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"✅ Reviews: {changed} new")
    return changed

# ── Generate bot articles for new bots ──
def generate_articles():
    changed = 0
    for bot in bots:
        bot_id = bot.get("id", "") or bot.get("name", "")
        if bot_id in bot_articles:
            continue
        name = bot.get("name", bot_id)
        desc = bot.get("description", "")[:300]
        prompt = (
            f'Write a detailed article about the Telegram bot "{name}". '
            f'Description: {desc}\n'
            f'Include: what it does, who it is for, alternatives, verdict.\n'
            f'Return as JSON with keys: title, content, pros (list), cons (list).\n'
        )
        print(f"  Generating article for {name}...")
        result = ask_deepseek(prompt)
        if result:
            try:
                parsed = json.loads(result)
                bot_articles[bot_id] = parsed
                changed += 1
            except:
                pass
    if changed:
        with open(BOT_ARTICLES_FILE, "w") as f:
            json.dump(bot_articles, f, indent=2, ensure_ascii=False)
    print(f"✅ Bot articles: {changed} new")
    return changed

# ── Generate category articles for new tags ──
def generate_category_articles():
    existing = set(category_articles.keys())
    all_tags = set()
    for bot in bots:
        for tag in bot.get("tags", []):
            all_tags.add(tag.lower().replace(" ", ""))
    
    changed = 0
    new_tags = all_tags - existing
    for tag in sorted(new_tags)[:20]:  # limit 20 per run to save tokens
        prompt = (
            f'Write a short SEO description for the Telegram bots category "{tag}". '
            f'Describe what kind of bots are in this category and their use cases.\n'
            f'Return as JSON with keys: title, description, keywords (list).'
        )
        print(f"  Generating category article for {tag}...")
        result = ask_deepseek(prompt)
        if result:
            try:
                parsed = json.loads(result)
                category_articles[tag] = parsed
                changed += 1
            except:
                pass
    if changed:
        with open(CATEGORY_ARTICLES_FILE, "w") as f:
            json.dump(category_articles, f, indent=2, ensure_ascii=False)
    print(f"✅ Category articles: {changed} new")
    return changed

# ── Main ──
if __name__ == "__main__":
    print("📝 Generating AI content for new bots...")
    if not API_KEY:
        print("⚠️ DEEPSEEK_API_KEY not set. Set it in GitHub Secrets.")
        sys.exit(1)
    
    total = 0
    total += generate_reviews()
    total += generate_articles()
    total += generate_category_articles()
    
    if total == 0:
        print("✅ All bots already have content. Nothing to generate.")
    else:
        print(f"🎉 Generated {total} new items")
