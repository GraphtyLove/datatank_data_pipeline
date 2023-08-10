# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context
import requests
from bs4 import BeautifulSoup as bs
import pymongo
import os
from dotenv import load_dotenv
import json
from functools import partial
from tqdm.contrib.concurrent import thread_map
import tqdm

load_dotenv()

XML_URL = "https://www.knack.be/news-sitemap.xml"

JSON_FILEPATH = os.path.join('.', "knack_scraping","my_json.json")

def get_links(url, session):
    """will get all links from sitemap"""
    page = session.get(url).text
    soup = bs(page, "html.parser")
    
    for link in soup.find_all("loc"):
        yield link.text

def get_article(link, session):
    container = {}

    response = session.get(link)
    if response.status_code!= 200:
        print(response.status_code)
        return 
    soup = bs(response.content, "html.parser")

    container["source"] = XML_URL.split(".")[1]
    
    container["url"] = link

    title = soup.find_all("h1")
    if title :
        article_title = title[0].text.strip()
        container["title"] = article_title
    else :
        print("no title")

    elements = soup.find_all("p", attrs={"class": None})
    if elements :
        text_list = [element.get_text() for element in elements]
        container["text"] = "\n".join(text_list)
    else :
        print("no articles")

    published_time = soup.find('script', {"type": "application/ld+json"})
    if published_time:
        data = json.loads(published_time.text, strict=False)
        published_date = data["@graph"][0]["datePublished"]
        container["date"] = published_date
    else :
        print("no date")

    return container

def get_articles(links, session):
    """Will fetch all titles, articles, dates, from urls, on at a time
    and will store it in a list of dictionary."""
    return list(thread_map(partial(get_article, session=session), links))

def save_json(articles):
    """Usefull to see if there is a mistake when scrapping"""

    with open(JSON_FILEPATH, "w") as f:
        json.dump(articles, f)

def save_articles_to_db(articles):
    """Create a connection with MangoDB and upload database"""
    MONGODB_URI = os.getenv("MONGODB_URI")
    database_name = "bouman_datatank"
    collection_name = "articles"
    client = pymongo.MongoClient(MONGODB_URI)
    database = client[database_name]
    collection = database[collection_name]

    for article in tqdm.tqdm(articles):
        if article is not None and not collection.find_one({"url": {"$eq": article["url"]}}):
            collection.insert_one(article)
    # collection.insert_many(articles)

def main():
    """input xml sitemaps to be read,
    will use all previous functions to create a database that will be send
    to a Mango database to be automatize by Airflow."
    """
    with requests.Session() as session:
        links = get_links(XML_URL, session)
        articles = get_articles(links, session)
    # save_json(container)
    save_articles_to_db(articles)

if __name__ == "__main__":
    main()