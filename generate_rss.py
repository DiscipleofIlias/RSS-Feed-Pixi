from playwright.sync_api import sync_playwright
from lxml import html
from datetime import datetime
import xml.etree.ElementTree as ET

# Fetch the webpage with JavaScript rendering
url = "https://pixibots.neocities.org/#new"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(3000)  # Wait 3 seconds for content to load
    content = page.content()
    browser.close()

tree = html.fromstring(content)

# Debug output
print("Fetching:", url)
all_dls = tree.xpath('//dl')
all_dts = tree.xpath('//dt')
all_dds = tree.xpath('//dd')
print(f"Total dl elements found: {len(all_dls)}")
print(f"Total dt elements found: {len(all_dts)}")
print(f"Total dd elements found: {len(all_dds)}")

# Extract items using XPath
items = tree.xpath('/html/body/main/article/dl[1]/dt')
titles = tree.xpath('/html/body/main/article/dl[1]/dd')

print(f"Found {len(items)} items with {len(titles)} titles")

# Create RSS feed
rss = ET.Element('rss', version='2.0')
channel = ET.SubElement(rss, 'channel')

ET.SubElement(channel, 'title').text = 'Pixibots Updates'
ET.SubElement(channel, 'link').text = url
ET.SubElement(channel, 'description').text = 'RSS feed for Pixibots'
ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

# Add items to feed
for item, title in zip(items, titles):
    feed_item = ET.SubElement(channel, 'item')
    ET.SubElement(feed_item, 'title').text = title.text_content().strip()
    ET.SubElement(feed_item, 'description').text = item.text_content().strip()
    ET.SubElement(feed_item, 'link').text = url
    ET.SubElement(feed_item, 'pubDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

# Write to file
tree_out = ET.ElementTree(rss)
ET.indent(tree_out, space='  ')
tree_out.write('feed.xml', encoding='utf-8', xml_declaration=True)

print("RSS feed generated successfully!")