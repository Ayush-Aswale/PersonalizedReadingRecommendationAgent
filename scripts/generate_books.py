import csv
import json
import os
import time
import urllib.request
from pathlib import Path

# Required fields:
# book_id, title, author, genre, sub_genre, pages, reading_level, avg_rating, publish_year, description, tags

GENRES = [
    ("Science Fiction", "Hard SF"),
    ("Fantasy", "High Fantasy"),
    ("Mystery", "Thriller"),
    ("Romance", "Contemporary Romance"),
    ("Literary Fiction", "Contemporary"),
    ("Non-Fiction", "Biography"),
    ("Horror", "Supernatural"),
    ("Historical Fiction", "WWII"),
    ("Young Adult", "Coming of Age"),
    ("Psychology", "Self-Help")
]

BOOKS_PER_GENRE = 80
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "raw" / "books_raw.csv"

def generate_books():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # We will use the Open Library Search API
    # http://openlibrary.org/search.json?subject=science_fiction&limit=80
    
    books = []
    book_counter = 1
    
    for genre, sub_genre in GENRES:
        print(f"Fetching books for genre: {genre}...")
        subject_query = genre.lower().replace(" ", "_")
        url = f"https://openlibrary.org/search.json?subject={subject_query}&limit={BOOKS_PER_GENRE}&sort=editions"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            for doc in data.get("docs", []):
                # Extract reliable info
                title = doc.get("title", "Unknown Title")
                author = ", ".join(doc.get("author_name", ["Unknown Author"]))
                publish_year = doc.get("first_publish_year", 2000)
                
                # Pages (fallback to heuristic if missing)
                pages = doc.get("number_of_pages_median")
                if pages is None:
                    pages = 300 # Synthetic default
                    
                # Description - Open Library search API often lacks description.
                # We'll generate a generic placeholder description to avoid making 800 individual API calls.
                # In a real production system we'd fetch works/{id}.json
                description = f"A compelling {genre.lower()} book by {author}, exploring themes of {sub_genre.lower()}."
                
                # Tags
                subjects = doc.get("subject", [])
                tags = ", ".join(subjects[:5]) if subjects else sub_genre
                
                # Synthetic fields (documented in data/README.md)
                # avg_rating: OpenLibrary has ratings_average but it's often missing. We synthesize a realistic rating.
                avg_rating = doc.get("ratings_average")
                if avg_rating is None:
                    # Synthetic rating between 3.5 and 4.8 based on book_id hash to be deterministic
                    avg_rating = 3.5 + (hash(title) % 13) / 10.0
                else:
                    avg_rating = round(avg_rating, 2)
                
                # reading_level: Synthetic heuristic based on pages/genre
                if pages <= 250 or genre in ["Romance", "Young Adult"]:
                    reading_level = "easy"
                elif pages > 450 or genre in ["Literary Fiction", "Non-Fiction"]:
                    reading_level = "hard"
                else:
                    reading_level = "medium"
                    
                books.append({
                    "book_id": f"B{book_counter:04d}",
                    "title": title,
                    "author": author,
                    "genre": genre,
                    "sub_genre": sub_genre,
                    "pages": pages,
                    "reading_level": reading_level,
                    "avg_rating": avg_rating,
                    "publish_year": publish_year,
                    "description": description,
                    "tags": tags
                })
                book_counter += 1
                
        except Exception as e:
            print(f"Failed to fetch {genre}: {e}")
            
        # polite delay
        time.sleep(1)

    print(f"Writing {len(books)} books to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "book_id", "title", "author", "genre", "sub_genre", "pages", 
            "reading_level", "avg_rating", "publish_year", "description", "tags"
        ])
        writer.writeheader()
        writer.writerows(books)
        
    print("Done!")

if __name__ == "__main__":
    generate_books()
