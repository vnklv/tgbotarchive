#!/usr/bin/env python3
"""SEO content generator — 20 templates, ~10000 chars per bot."""
import json, os, sys, hashlib, time, random, re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

REVIEWS_FILE = os.path.join(SCRIPT_DIR, "reviews.json")
BOT_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "bot_articles.json")
CATEGORY_ARTICLES_FILE = os.path.join(SCRIPT_DIR, "category_articles.json")

# ── 20 SEO templates ──
TEMPLATES = [
    {
        "id": "what_is",
        "title": "What is {name}? A Complete Overview",
        "prompt": """Write a detailed article (2500+ chars) answering "What is {name}?".
Description: {desc}
Tags: {tags}
Cover: what the bot does, how it works, key features, who it's for, verdict.
Write in informative, neutral tone."""
    },
    {
        "id": "how_to_use",
        "title": "How to Use {name}: A Step-by-Step Guide",
        "prompt": """Write a tutorial article (2500+ chars) on how to use the Telegram bot {name}.
Description: {desc}
Cover: how to start, main commands/features step by step, tips for best results, common mistakes.
Write as a practical guide."""
    },
    {
        "id": "review",
        "title": "{name} Review: Features, Pros, Cons & Verdict",
        "prompt": """Write an in-depth review of the Telegram bot {name} (2500+ chars).
Description: {desc}
Tags: {tags}
Cover: overview, key features with details, pros list (5+), cons list (3+), comparison with similar bots, final verdict and rating.
Write as an honest review."""
    },
    {
        "id": "alternatives",
        "title": "Top 5 Alternatives to {name}",
        "prompt": """Write a comparison article (2500+ chars) about alternatives to the Telegram bot {name}.
Description: {desc}
Tags: {tags}
Cover: why users look for alternatives, list 5 similar bots with brief comparison, how {name} differs, which is best for which use case.
Write as a helpful comparison guide."""
    },
    {
        "id": "vs",
        "title": "{name} vs Other Telegram Bots: Which One is Better?",
        "prompt": """Write a comparison article (2500+ chars) comparing {name} with similar Telegram bots.
Description: {desc}
Tags: {tags}
Cover: feature comparison table (conceptual), pricing/limits, ease of use, performance, community, which one wins in different scenarios.
Write as an unbiased comparison."""
    },
    {
        "id": "features",
        "title": "Top 10 Features of {name} You Should Know",
        "prompt": """Write a feature spotlight article (2500+ chars) about the Telegram bot {name}.
Description: {desc}
Cover: list and explain 10 key features, how each feature helps users, advanced tips, hidden features.
Write as an informative listicle."""
    },
    {
        "id": "category_guide",
        "title": "Best Telegram Bots for {category}: A Curated List",
        "prompt": """Write a curated list article (2500+ chars) about the best Telegram bots in the {category} category.
Description of {name}: {desc}
Cover: why this category matters, top 7-10 bots (including {name}), what each does best, comparison tips, how to choose.
Write as a helpful roundup guide."""
    },
    {
        "id": "beginner_guide",
        "title": "Beginner's Guide to Using {name} on Telegram",
        "prompt": """Write a beginner-friendly guide (2500+ chars) for new users of the Telegram bot {name}.
Description: {desc}
Cover: what is this bot, how to find it on Telegram, how to start, basic commands, example use cases, troubleshooting tips, next steps.
Write in simple, accessible language for non-technical users."""
    },
    {
        "id": "tips_tricks",
        "title": "{name} Tips and Tricks: Get the Most Out of It",
        "prompt": """Write a tips article (2500+ chars) with advanced usage tips for the Telegram bot {name}.
Description: {desc}
Cover: 10-15 practical tips, shortcuts, hidden features, power user tricks, time-saving hacks.
Write as an expert advice article."""
    },
    {
        "id": "use_cases",
        "title": "Top 7 Use Cases for {name} in {current_year}",
        "prompt": """Write a use cases article (2500+ chars) showing practical applications of the Telegram bot {name}.
Description: {desc}
Tags: {tags}
Cover: 7 different real-world use cases with specific examples, who benefits most, success scenarios.
Write as a practical application guide."""
    },
    {
        "id": "problem_solution",
        "title": "How {name} Solves Common Telegram Problems",
        "prompt": """Write a problem-solution article (2500+ chars) about how the Telegram bot {name} helps users.
Description: {desc}
Cover: identify 5-7 common problems users face, explain how {name} solves each, comparison with manual workaround, efficiency gains.
Write as a solution-oriented article."""
    },
    {
        "id": "faq",
        "title": "{name} FAQ: Everything You Need to Know",
        "prompt": """Write a comprehensive FAQ article (2500+ chars) about the Telegram bot {name}.
Description: {desc}
Cover: 10-15 common questions with detailed answers, what the bot does, how to use it, limitations, pricing if any, support info.
Write in clear Q&A format."""
    },
    {
        "id": "why_use",
        "title": "Why You Should Use {name} for {category}",
        "prompt": """Write a persuasive article (2500+ chars) explaining why users should choose the Telegram bot {name}.
Description: {desc}
Category: {category}
Cover: key benefits, unique selling points, comparison with doing it manually, time/money savings, user testimonials, final recommendation.
Write as a convincing but honest recommendation."""
    },
    {
        "id": "integration",
        "title": "How to Integrate {name} with Other Tools",
        "prompt": """Write an integration guide (2500+ chars) for the Telegram bot {name}.
Description: {desc}
Cover: what tools/services it integrates with, how to set up integrations, automation possibilities, advanced workflows, tips for power users.
Write as a technical how-to guide."""
    },
    {
        "id": "comparison_roundup",
        "title": "{name} vs Top Competitors: Full Comparison for {current_year}",
        "prompt": """Write a comprehensive comparison article (2500+ chars) of {name} vs its top competitors.
Description: {desc}
Tags: {tags}
Cover: feature matrix comparison, pricing, ease of use, support, community size, ideal user profiles, final recommendations.
Write as an in-depth, data-driven comparison."""
    },
    {
        "id": "trends",
        "title": "Why {name} is Trending in {current_year}",
        "prompt": """Write a trends article (2500+ chars) about why the Telegram bot {name} is gaining popularity.
Description: {desc}
Cover: current trends in {category} space, how {name} fits in, growth factors, community response, future outlook.
Write as an analytical article."""
    },
    {
        "id": "productivity",
        "title": "Boost Your Productivity with {name}",
        "prompt": """Write a productivity article (2500+ chars) about how the Telegram bot {name} improves workflow.
Description: {desc}
Cover: before/after scenarios, time savings, automation features, real user workflows, productivity tips, ROI analysis.
Write as a results-focused article."""
    },
    {
        "id": "ultimate_guide",
        "title": "The Ultimate Guide to {name} in {current_year}",
        "prompt": """Write a comprehensive ultimate guide (2500+ chars) for the Telegram bot {name}.
Description: {desc}
Tags: {tags}
Cover: everything from basics to advanced, complete feature walkthrough, best practices, troubleshooting, expert tips, future updates.
Write as an authoritative, complete resource."""
    },
    {
        "id": "category_spotlight",
        "title": "{name}: The Best {category} Bot on Telegram?",
        "prompt": """Write a spotlight review article (2500+ chars) focusing on why {name} stands out in the {category} category.
Description: {desc}
Cover: state of {category} bots in general, how {name} compares, unique features, community feedback, ratings, final verdict.
Write as an evaluative deep-dive."""
    },
    {
        "id": "quick_start",
        "title": "{name} Quick Start Guide: Get Set Up in 5 Minutes",
        "prompt": """Write a quick start guide (2500+ chars) for the Telegram bot {name}.
Description: {desc}
Cover: what you need before starting, step-by-step setup (5-7 steps), first commands to try, what to do next, where to get help.
Write as a fast-paced, actionable guide."""
    }
]

# ── Helpers ──
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
            req = ureq.Request(
                API_URL,
                data=json.dumps({
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.75,
                    "max_tokens": 2000,
                }).encode(),
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            with ureq.urlopen(req, timeout=45) as resp:
                result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  ⚠️ AI error (attempt {attempt+1}): {e}")
            time.sleep(3)
    return None

# ── Generate SEO content for a bot ──
def generate_bot_content(bot, existing_articles):
    username = bot.get("username", "")
    if not username:
        return None
    if username in existing_articles and existing_articles[username].get("combined"):
        return None  # already has full content
    
    name = bot.get("name", username)
    desc = bot.get("description", "")[:500]
    tags_list = bot.get("tags", [])
    tags = ", ".join(tags_list[:10])
    category = tags_list[0] if tags_list else "Telegram"
    year = datetime.now().year
    
    # Select 3-4 relevant templates
    selected = random.sample(TEMPLATES, min(4, len(TEMPLATES)))
    
    articles = []
    for tmpl in selected:
        prompt = tmpl["prompt"].format(
            name=name, desc=desc, tags=tags,
            category=category, current_year=year
        )
        prompt += "\n\nImportant: Write at least 2500 characters. Return ONLY the article text, no JSON, no metadata."
        
        print(f"    [{tmpl['id']}] Generating...")
        result = ask_deepseek(prompt)
        if result and len(result) > 500:
            articles.append({
                "template": tmpl["id"],
                "title": tmpl["title"].format(name=name, category=category, current_year=year),
                "content": result.strip()
            })
    
    if len(articles) >= 2:
        combined_title = f"{name}: Complete Guide and Review ({year})"
        combined_content = "\n\n---\n\n".join(
            f"## {a['title']}\n\n{a['content']}" for a in articles
        )
        
        return {
            "combined": True,
            "title": combined_title,
            "content": combined_content,
            "articles": articles,
            "word_count": len(combined_content),
            "generated_at": datetime.now().isoformat()
        }
    
    return None

# ── Main ──
if __name__ == "__main__":
    print(f"📝 SEO Content Generator — {len(TEMPLATES)} templates")
    print(f"{'='*50}")
    
    if not API_KEY:
        print("⚠️ DEEPSEEK_API_KEY not set")
        sys.exit(1)
    
    bots = json.load(open(os.path.join(SCRIPT_DIR, "data.json")))
    bot_articles = load_json(BOT_ARTICLES_FILE)
    
    # Find bots without full content
    to_generate = []
    for bot in bots:
        username = bot.get("username", "")
        if not username:
            continue
        if username not in bot_articles or not bot_articles[username].get("combined"):
            to_generate.append(bot)
    
    print(f"Bots total: {len(bots)}, need content: {len(to_generate)}")
    
    if not to_generate:
        print("✅ All bots already have content")
        sys.exit(0)
    
    # Generate for new bots (limit 5 per run to save tokens)
    generated = 0
    for bot in to_generate[:5]:
        username = bot.get("username", "")
        name = bot.get("name", username)
        print(f"\n📄 Generating for {name}...")
        
        result = generate_bot_content(bot, bot_articles)
        if result:
            bot_articles[username] = result
            generated += 1
            chars = result["word_count"]
            articles_count = len(result["articles"])
            print(f"  ✅ {chars} chars from {articles_count} templates")
        else:
            print(f"  ❌ Failed")
    
    # Save
    if generated:
        with open(BOT_ARTICLES_FILE, "w") as f:
            json.dump(bot_articles, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Generated {generated} new articles")
    else:
        print("\n⏭️ Nothing generated")