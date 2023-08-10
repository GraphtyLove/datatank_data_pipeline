
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pymongo
import os
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

sitemap_url_lavenir = "https://www.lavenir.net/arc/outboundfeeds/sitemap-news/?outputType=xml"



def extract_text_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    elements = soup.find_all("p", class_="text-left ap-StoryElement ap-StoryElement--mb ap-StoryText")
    text_list = [element.get_text() for element in elements]
    return "\n".join(text_list)


def extract_news_title_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    h1_tag = soup.find('h1', class_='ap-Title ap-StoryTitle')
    if h1_tag:
        text = h1_tag.get_text(strip=True)
        return text
    else:
        return ""
   
def extract_sitemap_data(sitemap_url_lavenir):
    response = requests.get(sitemap_url_lavenir)
    sitemap_soup = BeautifulSoup(response.text, "lxml")

    urls = sitemap_soup.find_all("url")

    sitemap_data_lavenir = []
    for url in urls:
        loc = url.find("loc").text
        lastmod = url.find("lastmod").text
        news_title = extract_news_title_from_url(loc)
        news_pub_date_tag = url.find("news:publication_date")
        news_pub_date_str = news_pub_date_tag.text 
        news_pub_date= parser.parse(news_pub_date_str)
        news_name = url.find("news:name").text
        news_language = url.find("news:language").text

        scraped_text = extract_text_from_website(loc)
        data = {
            "url": loc,
            "title": news_title,
            "date": news_pub_date,
            "language": news_language,
            "text": scraped_text
        }

        sitemap_data_lavenir.append(data)

    return sitemap_data_lavenir

if __name__ == "__main__":
    sitemap_data_lavenir = extract_sitemap_data(sitemap_url_lavenir)
    
    MONGODB_URI = os.getenv("MONGODB_URI")
    database_name = "bouman_datatank"
    collection_name = "articles"
    client = pymongo.MongoClient(MONGODB_URI)
    database = client[database_name]
    collection = database[collection_name]

for article in sitemap_data_lavenir:
        article_url = article["url"]
        existing_article = collection.find_one({"url": article_url})
        if not existing_article:
            collection.insert_one(article)

client.close()


