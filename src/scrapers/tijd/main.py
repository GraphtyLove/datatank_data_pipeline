import requests
from bs4 import BeautifulSoup
import csv
import re
import pymongo
import os
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()
sitemap_url_tijd = "https://www.tijd.be/news/sitemap.xml"

def extract_text_from_url(url):
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'}
    response = requests.get(url,headers=headers)
    

    soup = BeautifulSoup(response.text, "html.parser")
   

    all_paragraphs = soup.find_all('p')
    text_list = []

    for paragraph in all_paragraphs:
        text = paragraph.get_text(strip=True)
        cleaned_text = re.sub(r'[^\x00-\x7F]', '', text)
        text_list.append(cleaned_text)
        
    return "\n".join(text_list)
    

def extract_sitemap_data(sitemap_url):
      
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'}
    response = requests.get(sitemap_url, headers=headers)
   
    
    sitemap_soup = BeautifulSoup(response.text, "lxml")
    
    urls = sitemap_soup.find_all("url")

    sitemap_data = []
    for url in urls:
        loc = url.find("loc").text
        

        news_title_tag = url.find("news:title")
        news_title = news_title_tag.text if news_title_tag else None

       

        news_pub_date_tag = url.find("news:publication_date")
        news_pub_date_str = news_pub_date_tag.text if news_pub_date_tag else None

        if news_pub_date_str:
            news_pub_date = parser.parse(news_pub_date_str)
        else:
            news_pub_date = None


        news_name_tag = url.find("news:name")
        news_name = news_name_tag.text if news_name_tag else None

        news_language_tag = url.find("news:language")
        news_language = news_language_tag.text if news_language_tag else None

        
        text_content = extract_text_from_url(loc)
        data = {
            "url": loc,
            "title": news_title,
            "date": news_pub_date,
            "language": news_language,
            "text": text_content
        }


        sitemap_data.append(data)

    return sitemap_data

if __name__ == "__main__":
    sitemap_data_tijd = extract_sitemap_data(sitemap_url_tijd)

    MONGODB_URI = os.getenv("MONGODB_URI")
    database_name = "bouman_datatank"
    collection_name = "articles"
    client = pymongo.MongoClient(MONGODB_URI)
    database = client[database_name]
    collection = database[collection_name]

for article in sitemap_data_tijd:
        article_url = article["url"]
        existing_article = collection.find_one({"url": article_url})
        if not existing_article:
            collection.insert_one(article)

client.close()
