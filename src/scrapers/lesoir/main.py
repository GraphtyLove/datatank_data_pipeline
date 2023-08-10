"""
Scrape https://www.lesoir.be/18/sections/le-direct to get
the url, title, text, date and language of each article in the news feed.
"""
import time
from dateutil import parser
import requests
from bs4 import BeautifulSoup as bs
import json
import unicodedata
from pymongo import MongoClient
import ssl  # Use this import if you get a Certificate error in Mac
import os
from dotenv import load_dotenv

load_dotenv()

ssl._create_default_https_context = ssl._create_unverified_context

start_time = time.perf_counter()


def find_article_title(soup) -> str:
    article_title = soup.find("h1").text
    return article_title


# selector for geeko.lesoir.be urls
def geeko_selector(soup) -> tuple:
    div = soup.find("div", attrs={"class": "post-content-area"})
    paragraphs = div.find_all("p")
    if "Suivez Geeko sur Facebook" in paragraphs[-1].text:
        paragraphs = paragraphs[:-1]
    text = ""
    return paragraphs, text


# selector for sosoir.lesoir.be urls
def sosoir_selector(soup) -> tuple:
    h2 = soup.find("h2", attrs={"class": "chapeau"}).text.strip()
    div = soup.find("div", attrs={"id": "artBody"})
    paragraphs = div.find_all("p")
    if "sosoir.lesoir.be" in paragraphs[-1].text:
        paragraphs = paragraphs[:-1]
    text = h2
    return paragraphs, text


# selector for www.lesoir.be and soirmag.lesoir.be urls
def lesoirmag_selector(soup) -> tuple:
    article = soup.find("article", attrs={"class": "r-article"})
    paragraphs = article.find_all("p")
    if "www.soirmag.be" in paragraphs[-1].text:
        paragraphs = paragraphs[:-1]
    text = ""
    return paragraphs, text


def find_article_text(soup, url: str) -> str:
    if "sosoir" in url:
        paragraphs, text = sosoir_selector(soup)
    elif "geeko" in url:
        paragraphs, text = geeko_selector(soup)
    else:
        paragraphs, text = lesoirmag_selector(soup)
    for p in paragraphs:
        p_text = unicodedata.normalize("NFKD", p.text.strip())
        text += p_text
    return text


def find_published_date(soup) -> str:
    script = soup.find("script", {"type": "application/ld+json"})
    data = json.loads(script.text, strict=False)
    try:
        published_date = data["@graph"][0]["datePublished"]
    except:
        published_date = data["datePublished"]
    date = parser.parse(published_date)
    return date


print("Creating list of articles of news page ...")
response = requests.get("https://www.lesoir.be/18/sections/le-direct")
soup = bs(response.content, "html.parser")
articles = []
base_url = "https://www.lesoir.be"
links = soup.select("h3 > a")
for link in links:
    print("Adding article ...")
    url = link.get("href")
    print(" Adding url ...")
    dict = {"url": url if "//" in url else base_url + url}
    link_response = requests.get(dict["url"])
    link_soup = bs(link_response.content, "html.parser")
    print(" Adding article text ...")
    dict["text"] = find_article_text(link_soup, dict["url"])
    print(" Adding date ...")
    dict["date"] = find_published_date(link_soup)
    print(" Adding title ...")
    dict["title"] = find_article_title(link_soup)
    print(" Adding language ...")
    dict["language"] = "fr"
    articles.append(dict)
    print(f"The list has {len(articles)} articles")
print("List completed.")

print("Connecting to database ...")
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["bouman_datatank"]
collection = db["articles"]

print("Checking if articles already exist in database, if not adding them ...")
for article in articles:
    if collection.find_one({"url": {"$eq": article["url"]}}):
        print(f"url: {article['url']}")
        print("An article with this url already exists.")
    else:
        print("Adding new article ...")
        collection.insert_one(article)

print("Closing connection to database ...")
client.close()

end_time = time.perf_counter()
print(round(end_time - start_time, 2), "seconds")
