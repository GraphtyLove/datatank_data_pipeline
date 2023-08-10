import os
import pymongo
from dotenv import load_dotenv

from utils import embeddings, languages, polarity, source


def preprocess_db():
    """
    Preprocess all the records in the DB.

    Please check the output, they're going to run this on 3M articles.
    Steps are:
        - Get article's sources from URL (https://lesoir.be/article-1 --> lesoir)
        - Get the article's language (fr or nl)
        - Calculate the COS score
        - Calculate the embeddings
        - Calculate the data-related
        - Calculate the polarity
        - Update the record in the DB
    """
    # Loads env variables from .env file. This is used only in dev
    load_dotenv(".env")

    # DB connection
    client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
    db = client["bouman_datatank"]
    collection = db["articles"]

    # docs = collection.find({"embedding": {"$exists": False},"text": {"$exists": True, "$ne": None} })
    docs = collection.find({"text": {"$exists": True, "$ne": None} })
    
    counter = 0
    for doc in docs:
        counter += 1
        print(counter,doc["url"])
        
        # Preprocess record
        embedding = embeddings.compute_embedding(doc)
        cos_score = embeddings.cos_score(embedding)
        data_related = embeddings.data_related(cos_score)
        source_name = source.get_source_url(doc)
        language = languages.language_getter(doc)        
        if language is None:
            polarity_score = None
        else:
            polarity_score = polarity.compute_polarity(doc,language)

        # Update record in DB
        collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "embedding": embedding.tolist(),
                    "source": source_name,
                    "language": language,
                    "cos_score": cos_score,
                    "data_related": data_related,
                    "polarity": polarity_score,
                }
            },
        )



if __name__ == "__main__":
   print("Start preprocessing database...")
   preprocess_db()
   print("Done preprocessing")