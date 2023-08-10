import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import re
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map
import functools
import os
import pymongo

tqdm.pandas()


def main():
    with requests.Session() as session:
        sitemap = pd.read_xml("https://www.lalibre.be/arc/outboundfeeds/sitemap-news/?outputType=xml")
        df = sitemap.drop(["news", "image"], axis=1)
        df.rename(columns={"loc": "url"}, inplace=True)
        extracted_data = thread_map(functools.partial(extract_content, session=session), df["url"], max_workers=4)
        
        extracted_df = pd.DataFrame(list(extracted_data), columns=["title", "article", "date"])
        
        df = pd.concat([df, extracted_df], axis=1)

        df = df.loc[:, ["url","title","article","date"]]

        MONGODB_URI = os.getenv("MONGODB_URI")
        database_name = "bouman_datatank"
        collection_name = "articles"
        client = pymongo.MongoClient(MONGODB_URI)
        database = client[database_name]
        collection = database[collection_name]
        for _, row in df.iterrows():
            existing_article = collection.find_one({"url": row["url"]})
            if existing_article is None:
                article = {
                    "url": row["url"],
                    "title": row["title"],
                    "article": row["article"],
                    "date": row["date"]
                }
                collection.insert_one(article)
            else:
                print(f"Article with URL {row['url']} already exists in the database.")

def extract_content(url: str, session=None):
    response = session.get(url)
    soup = bs(response.content, "html.parser")
    
    title = soup.find_all("h1")
    article_title = title[0].text.strip() if title else "Unknown"
    
    paragraphs = [p.text for p in soup.select('p[class~="ap-StoryText"]')]
    article_text = "".join(paragraphs)
    
    date = [p.text for p in soup.find("p")]
    data = " ".join(date)
    date_pattern = r"\d{2}-\d{2}-\d{4}"
    date_match = re.search(date_pattern, data)
    date = date_match.group()
    day, month, year = date.split("-")
    published_date = f"{year}-{month}-{day}"
    
    return article_title, article_text, published_date


if __name__ == "__main__":
    main()
