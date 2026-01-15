from playwright.sync_api import sync_playwright
from lxml import html
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib
import json
import os

# Fetch the webpage with JavaScript rendering
url = "https://pixibots.neocities.org/#new"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(3000)
    content = page.content()
    browser.close()

tree = html.fromstring(content)

# Extract items using XPath
items = tree.xpath('/html/body/main/article/dl[1]/dt')
titles = tree.xpath('/html/body/main/article/dl[1]/dd')

print(f"Found {len(items)} items with {len(titles)} titles")

# Load previous items to avoid duplicates
state_file = 'feed_state.json'
if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        seen_items = json.load(f)
else:
    seen_items = {}

current_time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

# Create RSS feed
rss = ET.Element('rss', version='2.0')
channel = ET.SubElement(rss, 'channel')

ET.SubElement(channel, 'title').text = 'Pixibots Updates'
ET.SubElement(channel, 'link').text = url
ET.SubElement(channel, 'description').text = 'RSS feed for Pixibots'
ET.SubElement(channel, 'lastBuildDate').text = current_time

# Process items
new_seen_items = {}
for item, title in zip(items, titles):
    date_text = item.text_content().strip()
    title_text = title.text_content().strip()
    
    # Create unique ID based on date and title
    unique_id = hashlib.md5((date_text + title_text).encode()).hexdigest()
    
    # Parse the date from the dt element (format: YYYY-MM-DD)
    try:
        date_obj = datetime.strptime(date_text, "%Y-%m-%d")
        pub_date = date_obj.strftime('%a, %d %b %Y 00:00:00 GMT')
    except ValueError:
        # If date parsing fails, use current time
        print(f"Could not parse date: {date_text}")
        pub_date = current_time
    
    # Track this item
    new_seen_items[unique_id] = {
        'date': date_text,
        'title': title_text,
        'pubDate': pub_date
    }
    
    # Check if this is a new item
    if unique_id not in seen_items:
        print(f"New item: {date_text} - {title_text}")
    
    feed_item = ET.SubElement(channel, 'item')
    ET.SubElement(feed_item, 'title').text = f"{date_text} - {title_text}"
    ET.SubElement(feed_item, 'description').text = title_text
    ET.SubElement(feed_item, 'link').text = url
    ET.SubElement(feed_item, 'guid', isPermaLink='false').text = unique_id
    ET.SubElement(feed_item, 'pubDate').text = pub_date

# Save state for next run
with open(state_file, 'w') as f:
    json.dump(new_seen_items, f, indent=2)

# Write RSS file
tree_out = ET.ElementTree(rss)
ET.indent(tree_out, space='  ')
tree_out.write('feed.xml', encoding='utf-8', xml_declaration=True)

print("RSS feed generated successfully!")