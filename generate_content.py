#!/usr/bin/env python3
"""SEO content generator — 20 templates, ~10000 chars per bot.
Skips Google-approved pages (keeps them unchanged)."""
import json, os, sys, time, random
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

REVIEWS_FILE = os.path.join(SCRIPT_DIR, "reviews.json")
BOT_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "bot_articles.json")
CATEGORY_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "category_articles.json")

# ── Approved pages (Google-indexed, DO NOT modify) ──
APPROVED_BOTS = {
    "StyleGremBot", "SmartUtilBot", "ig_watch_bot", "AtTime_Presents_Bot",
    "ArtMatcherBot", "anime_for_streaming_bot", "todoeasybot", "AudioFactoryBot",
    "instabot", "poltronarossastreambot", "SocialBooster_aibot", "GooGLeSearchBXBot",
    "smyplaylistbot", "noSVGbot", "HeXa_InFo_BoT", "GeminiWRBot", "ChatSizeBot",
    "xkcd_comicsbot", "UnlimitedQuestionsBot", "UserAccountInfoBot", "DreamsOutBot",
    "PimOnlineBot", "subtitle_translate_bot", "HTMLtoPDF_bot", "idstracebot",
    "chaoji", "patrosub_bot", "TGCreationDateBot", "DrReactBot", "cats_search_bot",
    "xD0RMuleBot", "Listentomeplease_bot", "GoodReadsBooksBot", "hintorbot",
    "AJviewCounter_bot", "icybreakerbot", "gpt_fast_bot", "jsoonbot",
    "AcceptRequestBot", "Tzy_TODBot", "NexAutoApproveBot", "cardusbot",
    "deepwerk_io_bot", "K_vp_robot", "GibIDBot", "SocialExchangerBot",
    "Stickerdownloadbot", "genius_the_bot", "AlbumCoverFinderBot",
    "CoC_Italia_Stats_bot", "MathsToolsBot", "zenplayerbot", "card_teller_bot",
    "wiki", "InlineTradBot", "JarPlay_Bot", "FootballTeamManagerBot",
    "PinterestVideoDlBot", "SongRefBot", "subtitle_dl_bot", "TagdBot",
    "foldersbot", "mp3toolsbot", "ThirtyOneBot", "foodometer_bot",
    "cricbuzz_bot", "TicTacToes_Bot", "InspiroRobot", "Txt2SpeechBot",
    "TrumpQuotes_Bot", "CalcioGoalBot", "UploadBooksBot", "YtConvertAudioBot",
    "PayScribeBot", "TalkMe_chat_bot", "EasyStrongPasswordBot", "cloudflarecheckbot"
}

# ── 20 SEO templates ──
TEMPLATES = [
    {"id": "what_is", "title": "What is {name}? A Complete Overview",
     "prompt": "Write a detailed article (2500+ chars) answering 'What is {name}?'.\nDescription: {desc}\nTags: {tags}\nCover: what the bot does, how it works, key features, who it's for, verdict.\nWrite in informative, neutral tone."},
    {"id": "how_to_use", "title": "How to Use {name}: A Step-by-Step Guide",
     "prompt": "Write a tutorial article (2500+ chars) on how to use the Telegram bot {name}.\nDescription: {desc}\nCover: how to start, main commands/features step by step, tips for best results.\nWrite as a practical guide."},
    {"id": "review", "title": "{name} Review: Features, Pros, Cons & Verdict",
     "prompt": "Write an in-depth review of {name} (2500+ chars).\nDescription: {desc}\nTags: {tags}\nCover: overview, key features, pros list (5+), cons list (3+), comparison with similar bots, final verdict.\nWrite as an honest review."},
    {"id": "alternatives", "title": "Top 5 Alternatives to {name}",
     "prompt": "Write a comparison article (2500+ chars) about alternatives to {name}.\nDescription: {desc}\nTags: {tags}\nCover: why users look for alternatives, list 5 similar bots, how {name} differs, which is best for which use case."},
    {"id": "vs", "title": "{name} vs Other Telegram Bots: Which One is Better?",
     "prompt": "Write a comparison article (2500+ chars) comparing {name} with similar Telegram bots.\nDescription: {desc}\nTags: {tags}\nCover: feature comparison, pricing/limits, ease of use, performance, community, which one wins."},
    {"id": "features", "title": "Top 10 Features of {name} You Should Know",
     "prompt": "Write a feature spotlight article (2500+ chars) about {name}.\nDescription: {desc}\nCover: list and explain 10 key features, how each helps users, advanced tips, hidden features."},
    {"id": "category_guide", "title": "Best Telegram Bots for {category}: A Curated List",
     "prompt": "Write a curated list article (2500+ chars) about the best Telegram bots in the {category} category.\nCover: why this category matters, top 7-10 bots (including {name}), what each does best, comparison tips."},
    {"id": "beginner_guide", "title": "Beginner's Guide to Using {name} on Telegram",
     "prompt": "Write a beginner-friendly guide (2500+ chars) for new users of {name}.\nDescription: {desc}\nCover: what is this bot, how to find it, how to start, basic commands, example use cases, troubleshooting."},
    {"id": "tips_tricks", "title": "{name} Tips and Tricks: Get the Most Out of It",
     "prompt": "Write a tips article (2500+ chars) with advanced usage tips for {name}.\nDescription: {desc}\nCover: 10-15 practical tips, shortcuts, hidden features, power user tricks."},
    {"id": "use_cases", "title": "Top 7 Use Cases for {name} in {current_year}",
     "prompt": "Write a use cases article (2500+ chars) for {name}.\nDescription: {desc}\nTags: {tags}\nCover: 7 different real-world use cases with examples, who benefits most."},
    {"id": "problem_solution", "title": "How {name} Solves Common Telegram Problems",
     "prompt": "Write a problem-solution article (2500+ chars) about {name}.\nDescription: {desc}\nCover: identify 5-7 common problems, explain how {name} solves each, comparison with manual workaround."},
    {"id": "faq", "title": "{name} FAQ: Everything You Need to Know",
     "prompt": "Write a comprehensive FAQ (2500+ chars) about {name}.\nDescription: {desc}\nCover: 10+ common questions with detailed answers, what it does, how to use it, limitations."},
    {"id": "why_use", "title": "Why You Should Use {name} for {category}",
     "prompt": "Write a persuasive article (2500+ chars) explaining why users should choose {name}.\nCategory: {category}\nCover: key benefits, unique selling points, comparison with alternatives, time savings."},
    {"id": "integration", "title": "How to Integrate {name} with Other Tools",
     "prompt": "Write an integration guide (2500+ chars) for {name}.\nDescription: {desc}\nCover: what tools/services it integrates with, how to set up integrations, automation possibilities."},
    {"id": "comparison_roundup", "title": "{name} vs Top Competitors: Full Comparison for {current_year}",
     "prompt": "Write a comprehensive comparison (2500+ chars) of {name} vs its top competitors.\nDescription: {desc}\nTags: {tags}\nCover: feature matrix, pricing, ease of use, support, recommendations."},
    {"id": "trends", "title": "Why {name} is Trending in {current_year}",
     "prompt": "Write a trends article (2500+ chars) about why {name} is gaining popularity.\nDescription: {desc}\nCover: current trends in {category}, how {name} fits in, growth factors, future outlook."},
    {"id": "productivity", "title": "Boost Your Productivity with {name}",
     "prompt": "Write a productivity article (2500+ chars) about {name}.\nDescription: {desc}\nCover: before/after scenarios, time savings, automation features, real user workflows."},
    {"id": "ultimate_guide", "title": "The Ultimate Guide to {name} in {current_year}",
     "prompt": "Write a comprehensive ultimate guide (2500+ chars) for {name}.\nDescription: {desc}\nTags: {tags}\nCover: everything from basics to advanced, complete feature walkthrough, best practices."},
    {"id": "category_spotlight", "title": "{name}: The Best {category} Bot on Telegram?",
     "prompt": "Write a spotlight review (2500+ chars) focusing on why {name} stands out in {category}.\nDescription: {desc}\nCover: state of {category} bots, how {name} compares, unique features, community feedback, verdict."},
    {"id": "quick_start", "title": "{name} Quick Start Guide: Get Set Up in 5 Minutes",
     "prompt": "Write a quick start guide (2500+ chars) for {name}.\nDescription: {desc}\nCover: what you need, step-by-step setup, first commands, what to do next, where to get help."}
]

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {} if path.endswith(".json") else []

def ask_deepseek(prompt, max_retries=2):
    if not API_KEY:
        return None
    for attempt in range(max_retries):
        try:
            import urllib.request as ureq
            req = ureq.Request(API_URL, data=json.dumps({
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.75, "max_tokens": 2000
            }).encode(), headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            })
            with ureq.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  ⚠️ AI error (attempt {attempt+1}): {e}")
            time.sleep(3)
    return None

def generate_bot_content(bot, existing):
    username = bot.get("username", "")
    if not username or username in APPROVED_BOTS:
        return None
    # If already has new combined format, skip
    if username in existing and existing[username].get("combined"):
        return None  # already has full content
    
    name = bot.get("name", username)
    desc = bot.get("description", "")[:500]
    tags_list = bot.get("tags", [])
    tags = ", ".join(tags_list[:10])
    category = tags_list[0] if tags_list else "Telegram"
    year = datetime.now().year
    
    selected = random.sample(TEMPLATES, min(4, len(TEMPLATES)))
    articles = []
    for tmpl in selected:
        prompt = tmpl["prompt"].format(name=name, desc=desc, tags=tags, category=category, current_year=year)
        prompt += "\n\nWrite at least 2500 characters. Return ONLY the article text, no metadata."
        print(f"    [{tmpl['id']}] Generating...")
        result = ask_deepseek(prompt)
        if result and len(result) > 500:
            articles.append({
                "template": tmpl["id"],
                "title": tmpl["title"].format(name=name, category=category, current_year=year),
                "content": result.strip()
            })
    
    if len(articles) >= 2:
        combined = f"## {articles[0]['title']}\n\n{articles[0]['content']}\n\n---\n\n## {articles[1]['title']}\n\n{articles[1]['content']}"
        if len(articles) >= 3:
            combined += f"\n\n---\n\n## {articles[2]['title']}\n\n{articles[2]['content']}"
        return {
            "combined": True, "title": f"{name}: Complete Guide and Review ({year})",
            "content": combined, "articles": articles,
            "word_count": len(combined), "generated_at": datetime.now().isoformat()
        }
    return None

def generate_reviews(bot):
    username = bot.get("username", "")
    if not username or username in APPROVED_BOTS:
        return None
    name = bot.get("name", username)
    desc = bot.get("description", "")[:200]
    prompt = (
        f'Generate 3 realistic user reviews for the Telegram bot "{name}". '
        f'Description: {desc}\n'
        f'Return as JSON array: [{{"text":"...","author":"User","date":"2026-07-16","rating":5}}]'
    )
    result = ask_deepseek(prompt)
    if result:
        try:
            return json.loads(result)
        except:
            pass
    return None

if __name__ == "__main__":
    print(f"📝 SEO Content Generator — {len(TEMPLATES)} templates, {len(APPROVED_BOTS)} approved bots protected")
    print(f"{'='*50}")
    
    if not API_KEY:
        print("⚠️ DEEPSEEK_API_KEY not set")
        sys.exit(1)
    
    bots = json.load(open(os.path.join(SCRIPT_DIR, "data.json")))
    bot_articles = load_json(BOT_ARTICLES_FILE)
    reviews_data = load_json(REVIEWS_FILE)
    
    to_generate = []
    for bot in bots:
        username = bot.get("username", "")
        if not username or username in APPROVED_BOTS:
            continue
        # Skip only if already has new combined format
        if username in bot_articles and bot_articles.get(username, {}).get("combined"):
            continue
        to_generate.append(bot)
    
    print(f"Bots: {len(bots)}, approved: {len(APPROVED_BOTS)}, to generate: {len(to_generate)}")
    
    if not to_generate:
        print("✅ All non-approved bots already have content")
        sys.exit(0)
    
    generated_articles = 0
    generated_reviews = 0
    for bot in to_generate[:50]:  # 50 per run
        username = bot.get("username", "")
        name = bot.get("name", username)
        print(f"\n📄 {name} (@{username})...")
        
        # 1. Generate article
        result = generate_bot_content(bot, bot_articles)
        if result:
            bot_articles[username] = result
            generated_articles += 1
            print(f"  ✅ Article: {result['word_count']} chars from {len(result['articles'])} templates")
        
        # 2. Generate reviews
        if username not in reviews_data or not reviews_data.get(username):
            revs = generate_reviews(bot)
            if revs:
                reviews_data[username] = revs
                generated_reviews += 1
                print(f"  ✅ Reviews: {len(revs)} new")
    
    if generated_articles:
        with open(BOT_ARTICLES_FILE, "w") as f:
            json.dump(bot_articles, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Articles generated: {generated_articles}")
    
    if generated_reviews:
        with open(REVIEWS_FILE, "w") as f:
            json.dump(reviews_data, f, indent=2, ensure_ascii=False)
        print(f"🎉 Reviews generated: {generated_reviews}")
    
    if not generated_articles and not generated_reviews:
        print("\n⏭️ Nothing generated")