#!/usr/bin/env python3
"""
Script to fetch the latest geopolitics article from an RSS feed and add it
to the geopolitique-site repository.  It runs daily via GitHub Actions.

The script retrieves the most recent entry from the configured RSS feed,
generates a new HTML page with the article's title, publication date,
description and link, and places it in the `news/` directory.  If the
directory or index does not exist, it will be created.  The script then
updates the main index page (`index.html`) by adding a link to the new
article under a “Derniers articles” section.

To change the news source, modify the FEED_URL constant below.  Make sure
the chosen feed provides descriptive `title`, `link` and `description`
fields and permits fair use of its content.  This script only uses the
description provided by the feed and does not scrape full articles.
"""
import os
import datetime
import feedparser
import html


# RSS feed containing geopolitics news.  This URL can be changed to suit
# another provider that supplies geopolitics or world news articles.  Many
# news organisations provide RSS feeds; for example Reuters offers a
# "World News" feed at https://www.reuters.com/tools/rss.  The default here
# uses Geopolitical Monitor’s public feed.
FEED_URL = "https://www.geopoliticalmonitor.com/feed/"

# Paths relative to the repository root
NEWS_DIR = "news"
INDEX_FILE = "index.html"


def fetch_latest_entry():
    """Fetch the latest entry from the RSS feed.

    Returns a dictionary with keys: title, link, description, published.
    If the feed is empty or unreachable, returns None.
    """
    feed = feedparser.parse(FEED_URL)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    return {
        "title": html.unescape(entry.get("title", "Article sans titre")),
        "link": entry.get("link", ""),
        "description": html.unescape(entry.get("description", "")),
        "published": entry.get("published", datetime.datetime.utcnow().isoformat()),
    }


def generate_article_html(article_data, file_path):
    """Generate an HTML file for the article.

    Args:
        article_data: dict with keys title, link, description, published.
        file_path: destination path for the new HTML file.
    """
    title = article_data["title"]
    link = article_data["link"]
    description = article_data["description"]
    published = article_data["published"]

    content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header>
    <h1>{title}</h1>
    <nav>
      <a href="../index.html">Accueil</a>
    </nav>
  </header>
  <main class="article">
    <p><em>Publié le {published}</em></p>
    <p>{description}</p>
    <p>Lire l'article complet : <a href="{link}">source</a></p>
  </main>
  <footer>
    <p>Ce contenu provient d'un flux RSS externe. Pour plus d'articles, consultez la section actualités du site.</p>
  </footer>
</body>
</html>
"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def update_index(article_filename, article_title):
    """Insert a link to the new article into index.html.

    If a section 'Derniers articles' does not exist, create it near the end of
    the file just before the closing body tag.  Newer articles appear first
    in the list.  The links are relative to index.html.
    """
    if not os.path.exists(INDEX_FILE):
        return
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find existing news section or insertion point
    start_idx = None
    for i, line in enumerate(lines):
        if "<section id=\"derniers-articles\"" in line:
            start_idx = i
            break

    article_link = f"    <li><a href=\"{os.path.join(NEWS_DIR, article_filename)}\">{article_title}</a></li>\n"

    if start_idx is not None:
        # Insert new link after the <ul> opening tag
        for j in range(start_idx, len(lines)):
            if "<ul" in lines[j]:
                insert_idx = j + 1
                break
        else:
            insert_idx = start_idx + 1
        lines.insert(insert_idx, article_link)
    else:
        # Create a new section before </main> or end of body
        insert_idx = len(lines)
        for j, line in enumerate(lines):
            if "</main>" in line:
                insert_idx = j
                break
        section_html = [
            "  <section id=\"derniers-articles\">\n",
            "    <h2>Derniers articles</h2>\n",
            "    <ul>\n",
            article_link,
            "    </ul>\n",
            "  </section>\n",
        ]
        lines[insert_idx:insert_idx] = section_html

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    article = fetch_latest_entry()
    if not article:
        print("Aucun article n'a été trouvé dans le flux RSS.")
        return

    # Use current date to create filename; avoid characters invalid in file names
    date_str = datetime.date.today().isoformat()
    safe_title = "-".join(article["title"].lower().split())[:50]  # Trim length
    filename = f"{date_str}-{safe_title}.html"
    article_path = os.path.join(NEWS_DIR, filename)

    generate_article_html(article, article_path)
    update_index(filename, article["title"])
    print(f"Article ajouté : {filename}")


if __name__ == "__main__":
    main()