import os
import django
import sys
import json
from pathlib import Path

# Set up Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag.models import Document
from sentence_transformers import SentenceTransformer

def ingest():
    # Path to the data file
    data_file = BASE_DIR.parent / 'data' / 'documents.json'
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        return

    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            docs = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    print(f"Found {len(docs)} documents in {data_file.name}")
    
    # Optional: Clear existing documents to avoid duplicates
    # print("Clearing existing documents...")
    # Document.objects.all().delete()

    print(f"Ingesting {len(docs)} documents into the database...")
    count = 0
    for doc in docs:
        content = doc.get('content')
        source = doc.get('source', 'Unknown')
        
        if not content:
            continue
            
        embedding = model.encode(content).tolist()
        Document.objects.create(
            content=content,
            source=source,
            embedding=embedding
        )
        count += 1
        if count % 5 == 0:
            print(f"Processed {count}/{len(docs)} documents...")

    print(f"Successfully ingested {count} documents.")

if __name__ == "__main__":
    ingest()
