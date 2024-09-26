import json
from jinja2 import Environment, FileSystemLoader
import os
from collections import Counter, defaultdict
import feedparser
from datetime import datetime
from html import unescape
import re
import shutil

# Define a function to strip HTML tags
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', unescape(text))

# Define the path to the JSON file
json_file_path = 'data.json'

# Read the JSON file
with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
    data = json.load(jsonfile)

tags_counter = Counter()
tag_entries = defaultdict(list)
rss_feeds = []

for row in data:
    tags = row['tags'].split(',')
    for tag in tags:
        tag = tag.strip()
        tags_counter[tag] += 1
        tag_entries[tag].append(row)
    
    # Check for RSS feed
    if 'rss' in row:
        feed = feedparser.parse(row['rss'])
        if feed.bozo == 0 and 'feed' in feed:
            latest_entry = feed.entries[0]
            rss_feeds.append({
                'title': latest_entry.title,
                'link': latest_entry.link,
                'description': f'{strip_html_tags(latest_entry.description)[:500]}...',
                'published': datetime(*latest_entry.published_parsed[:6]) if 'published_parsed' in latest_entry else datetime.now()
            })
        else:
            # Handle encoding issues
            if 'bozo_exception' in feed and isinstance(feed.bozo_exception, UnicodeDecodeError):
                print(f"Encoding error for URL {row['rss']}: {feed.bozo_exception}. Retrying with explicit encoding.")
                feed = feedparser.parse(row['rss'], request_headers={'User-Agent': 'Mozilla/5.0'}, encoding='utf-8')
                if feed.bozo == 0 and 'feed' in feed:
                    latest_entry = feed.entries[0]
                    rss_feeds.append({
                        'title': latest_entry.title,
                        'link': latest_entry.link,
                        'description': f'{strip_html_tags(latest_entry.description)[:500]}...',
                        'published': datetime(*latest_entry.published_parsed[:6]) if 'published_parsed' in latest_entry else datetime.now()
                    })
                else:
                    print(f"Error parsing feed for URL {row['rss']} after retry: {feed.bozo_exception}")
            else:
                print(f"Error parsing feed for URL {row['rss']}: {feed.bozo_exception}")

# Sort rss_feeds by date, newest first
rss_feeds.sort(key=lambda x: x['published'], reverse=True)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('templates'))
index_template = env.get_template('home_page_template.html')
tag_template = env.get_template('topic_page_template.html')
rss_template = env.get_template('new_posts_page_template.html')

# Create output directories if they doesn't exist
output_dir = 'output'
topic_dir = 'output/topic'
css_dir = 'css'
os.makedirs(topic_dir, exist_ok=True)

# Copy the css folder to the output directory
css_src = 'css'
css_dst = os.path.join(output_dir, 'css')
if os.path.exists(css_dst):
    shutil.rmtree(css_dst)  # Remove existing css directory if it exists
shutil.copytree(css_src, css_dst)

# Generate the main page
latest_entries = data[-3:]  # Get the last three entries
index_content = index_template.render(
    title='Home Page',
    latest_entries=latest_entries,
    tags_counter=tags_counter
)
index_file_path = os.path.join(output_dir, 'index.html')
with open(index_file_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

# Generate tag pages
for tag, entries in tag_entries.items():
    tag_content = tag_template.render(
        title=f'{tag} Topic Page',
        tag=tag,
        entries=entries
    )
    tag_file_path = os.path.join(output_dir, f"topic/{tag}.html")
    with open(tag_file_path, 'w', encoding='utf-8') as f:
        f.write(tag_content)

# Generate RSS feed page
rss_content = rss_template.render(
    title='Latest Blog Posts',
    rss_feeds=rss_feeds,
    date_generated=datetime.now().strftime("%B %d, %Y")
)
rss_file_path = os.path.join(output_dir, 'new_posts.html')
with open(rss_file_path, 'w', encoding='utf-8') as f:
    f.write(rss_content)

print("HTML files and JSON data have been generated in the 'output' directory.")