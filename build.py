import os
import re
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from html import unescape

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import feedparser

from database import MongoDBClient

# Load environment variables from .env file
load_dotenv()

# Define a function to strip HTML tags
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', unescape(text))

# Define the path to the JSON file
blog_data_json_path = 'data.json'

# Read the JSON file
with open(blog_data_json_path, 'r', encoding='utf-8') as jsonfile:
    data = json.load(jsonfile)

tags_counter = Counter()
tag_entries = defaultdict(list)
posts_from_today = []
list_of_documents = []

# Set MongoDB Variables from the .env file
uri = os.getenv('MONGODB_URI')
db_name = os.getenv('DB_NAME')
collection_name = os.getenv('COLLECTION_NAME')

if not uri or not db_name or not collection_name:
    raise ValueError(f"MongoDB URI {len(uri)}, database name {len(db_name)}, and collection name {len(collection_name)} must be set.")
client = MongoDBClient(uri, db_name, collection_name)

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

                    list_of_documents.append({
                        'blog_id': row['id'],
                        'title': post.title if 'title' in post else None,
                        'link': post.link if 'link' in post else None,
                        'description': strip_html_tags(post.description) if 'description' in post else None,
                        'content': strip_html_tags(post.content[0].value) if 'content' in post else None,
                        'published_date': post.published if 'published' in post else None,
                        'formatted_date': post.published_parsed if 'published_parsed' in post else None,
                        'update': post.updated if 'updated' in post else None
                    })
        else:
            print(f"Error parsing feed for URL {row['rss']}: {feed.bozo_exception}")

#client.insert_documents(list_of_documents)
collection = client.get_full_collection()

# Sort rss_feeds by date, newest first
posts_from_today.sort(key=lambda x: x['published_date'], reverse=True)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('templates'))
index_template = env.get_template('home_page_template.html')
tag_template = env.get_template('topic_page_template.html')
rss_template = env.get_template('new_posts_page_template.html')
all_blogs_template = env.get_template('all_blogs_page_template.html')
search_posts_template = env.get_template('search_posts_page_template.html')

# Create output directories if they doesn't exist
output_dir = 'output'
topic_dir = 'output/topic'
css_dir = 'css'
os.makedirs(topic_dir, exist_ok=True)

# Create json search file
search_data_json = 'search_data.json'
search_data_file_path = os.path.join(output_dir, search_data_json)
with open(search_data_file_path, 'w', encoding='utf-8') as file:
    json.dump(collection, file, indent=4)

# Move search.php to output directory
search_php_file_path = 'search.php'
shutil.copy(search_php_file_path, output_dir)

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
    title=f'Blog Posts from {datetime.now().strftime("%B %d, %Y")}',
    rss_feeds=posts_from_today,
    date_generated=datetime.now().strftime("%B %d, %Y")
)
rss_file_path = os.path.join(output_dir, "new_posts.html")
with open(rss_file_path, 'w', encoding='utf-8') as f:
    f.write(rss_content)

# Generate all blogs page
all_blogs_content = all_blogs_template.render(
    title='All Blogs',
    data=data,
)
all_blogs_file_path = os.path.join(output_dir, 'all_software_blogs.html')
with open(all_blogs_file_path, 'w', encoding='utf-8') as f:
    f.write(all_blogs_content)

# Generate search posts page
search_posts_content = search_posts_template.render(
    title='Search Blog Posts'
)
search_posts_file_path = os.path.join(output_dir, 'search_posts.html')

print("HTML files and JSON data have been generated in the 'output' directory.")