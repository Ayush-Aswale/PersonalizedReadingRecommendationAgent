"""
Ingestion script to populate the books database and Chroma vector store from the raw CSV.
"""
import csv
import sys
from pathlib import Path

from config.settings import settings
from database.db import get_db_connection, init_db, _param
from rag.vector_store import get_vector_store

def ingest_data():
    csv_path = settings.PROJECT_ROOT / "data" / "raw" / "books_raw.csv"
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Please run scripts/generate_books.py first.")
        sys.exit(1)
        
    print("Initializing database schema...")
    init_db()
    
    books_to_insert = []
    vector_docs = []
    vector_metadatas = []
    vector_ids = []
    
    print(f"Reading {csv_path}...")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book_id = row["book_id"]
            title = row["title"]
            author = row["author"]
            genre = row["genre"]
            description = row["description"]
            tags = row["tags"]
            
            books_to_insert.append({
                "book_id": book_id,
                "title": title,
                "author": author,
                "genre": genre,
                "sub_genre": row["sub_genre"],
                "pages": int(row["pages"]) if row["pages"] else 300,
                "reading_level": row["reading_level"],
                "avg_rating": float(row["avg_rating"]) if row["avg_rating"] else 0.0,
                "publish_year": int(row["publish_year"]) if row["publish_year"] else 0,
                "description": description,
                "tags": tags
            })
            
            # Prepare data for vector store
            doc = f"{title} by {author}. Genre: {genre}. {description} Tags: {tags}"
            vector_docs.append(doc)
            vector_metadatas.append({
                "book_id": book_id,
                "genre": genre,
                "reading_level": row["reading_level"],
                "author": author
            })
            vector_ids.append(book_id)

    print(f"Loaded {len(books_to_insert)} books from CSV.")
    
    # 1. Insert into relational database
    print("Populating relational database...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Clear existing
        cursor.execute("DELETE FROM books")
        
        insert_sql = f"""
            INSERT INTO books (book_id, title, author, genre, sub_genre, pages, reading_level, avg_rating, publish_year, description, tags)
            VALUES ({_param('book_id')}, {_param('title')}, {_param('author')}, {_param('genre')}, {_param('sub_genre')}, {_param('pages')}, {_param('reading_level')}, {_param('avg_rating')}, {_param('publish_year')}, {_param('description')}, {_param('tags')})
        """
        
        # Depending on dialect, we can use executemany with a list of dicts. SQLite supports this, Psycopg2 requires a different approach.
        if settings.is_production:
            import psycopg2.extras
            psycopg2.extras.execute_batch(cursor, insert_sql, books_to_insert)
        else:
            cursor.executemany(insert_sql, books_to_insert)
            
        conn.commit()
    
    # 2. Insert into vector store (if local)
    if not settings.is_production:
        print("Populating Chroma vector store (this might take a minute)...")
        # Ensure Chroma path exists
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        vector_store = get_vector_store()
        
        # Add in batches to avoid overloading memory
        batch_size = 100
        for i in range(0, len(vector_docs), batch_size):
            vector_store.add_texts(
                texts=vector_docs[i:i+batch_size],
                metadatas=vector_metadatas[i:i+batch_size],
                ids=vector_ids[i:i+batch_size]
            )
            print(f"  Processed {min(i+batch_size, len(vector_docs))}/{len(vector_docs)} vectors...")
            
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
