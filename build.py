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
posts_from_today = []

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
            for post in feed.entries:
                published_date = datetime(*post.published_parsed[:6]) if 'published_parsed' in post else datetime(1900, 1, 1)
                if published_date.date() == datetime.now().date():
                    posts_from_today.append({
                        'title': post.title,
                        'link': post.link,
                        'description': f'{strip_html_tags(post.description)[:500]}...',
                        'published_date': published_date,
                        'formatted_date': published_date.strftime("%B %d, %Y")
                    })
        else:
            print(f"Error parsing feed for URL {row['rss']}: {feed.bozo_exception}")

# Sort rss_feeds by date, newest first
posts_from_today.sort(key=lambda x: x['published_date'], reverse=True)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('templates'))
index_template = env.get_template('home_page_template.html')
tag_template = env.get_template('topic_page_template.html')
rss_template = env.get_template('new_posts_page_template.html')

# Create latest entries page slug
latest_entries_slug = f'posts-from-{datetime.now().strftime("%Y-%m-%d")}.html'

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
latest_entries = data[-3:][::-1]  # Get the last three entries
index_content = index_template.render(
    title='Home Page',
    latest_entries_slug=latest_entries_slug,
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
        latest_entries_slug=latest_entries_slug,
        tag=tag,
        entries=entries
    )
    tag_file_path = os.path.join(output_dir, f"topic/{tag}.html")
    with open(tag_file_path, 'w', encoding='utf-8') as f:
        f.write(tag_content)

# Generate RSS feed page
rss_content = rss_template.render(
    title=f'Blog Posts from {datetime.now().strftime("%B %d, %Y")}',
    latest_entries_slug=latest_entries_slug,
    rss_feeds=posts_from_today,
    date_generated=datetime.now().strftime("%B %d, %Y")
)
rss_file_path = os.path.join(output_dir, latest_entries_slug)
with open(rss_file_path, 'w', encoding='utf-8') as f:
    f.write(rss_content)

print("HTML files and JSON data have been generated in the 'output' directory.")