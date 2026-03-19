import time
import json
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sentence_transformers import SentenceTransformer
import ollama
from .models import Document, QueryLog
from pgvector.django import CosineDistance

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_query_embedding(query):
    return model.encode(query).tolist()

@csrf_exempt
def ask_question(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    data = json.loads(request.body)
    user_query = data.get('question')
    
    if not user_query:
        return JsonResponse({'error': 'No question provided'}, status=400)

    start_time = time.time()
    
    # 1. KV Cache (Redis)
    query_hash = hashlib.md5(user_query.lower().strip().encode()).hexdigest()
    cache_key = f"answer:{query_hash}"
    cached_answer = cache.get(cache_key)
    
    if cached_answer:
        response_time = int((time.time() - start_time) * 1000)
        # Log the hit (KV)
        QueryLog.objects.create(
            query=user_query,
            answer=cached_answer,
            cache_hit=True,
            cache_type='KV',
            response_time_ms=response_time,
            embedding=get_query_embedding(user_query)
        )
        return JsonResponse({
            'answer': cached_answer,
            'cache_used': True,
            'cache_type': 'KV',
            'response_time': response_time
        })

    # 2. Semantic Cache
    query_embedding = get_query_embedding(user_query)
    # Find similar queries in QueryLog within 0.95 similarity (0.05 distance)
    similar_query = QueryLog.objects.annotate(
        distance=CosineDistance('embedding', query_embedding)
    ).filter(distance__lt=0.05).order_by('distance').first()

    if similar_query:
        response_time = int((time.time() - start_time) * 1000)
        # Log the hit (Semantic)
        QueryLog.objects.create(
            query=user_query,
            answer=similar_query.answer,
            cache_hit=True,
            cache_type='Semantic',
            response_time_ms=response_time,
            embedding=query_embedding
        )
        # Also update Redis for this specific query for faster future hits
        cache.set(cache_key, similar_query.answer, timeout=3600)
        
        return JsonResponse({
            'answer': similar_query.answer,
            'cache_used': True,
            'cache_type': 'Semantic',
            'response_time': response_time
        })

    # 3. RAG Pipeline (Cache Miss)
    # Retrieval
    top_docs = Document.objects.annotate(
        distance=CosineDistance('embedding', query_embedding)
    ).order_by('distance')[:3]
    
    context = "\n\n".join([doc.content for doc in top_docs])
    
    # Generation (Llama 3)
    prompt = f"""You are a helpful assistant. Answer the question based only on the provided context. 
If the context doesn't contain the answer, say "I don't have enough information to answer that based on my current documents."

Context:
{context}

Question: {user_query}
Answer:"""

    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt}
        ])
        answer = response['message']['content']
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    response_time = int((time.time() - start_time) * 1000)

    # Save to Caches
    cache.set(cache_key, answer, timeout=3600)
    QueryLog.objects.create(
        query=user_query,
        answer=answer,
        cache_hit=False,
        response_time_ms=response_time,
        embedding=query_embedding
    )

    return JsonResponse({
        'answer': answer,
        'cache_used': False,
        'response_time': response_time,
        'sources': [doc.source for doc in top_docs]
    })

def get_metrics(request):
    logs = QueryLog.objects.all()
    total = logs.count()
    if total == 0:
        return JsonResponse({
            'total_queries': 0,
            'hit_rate': 0,
            'avg_response_time': 0,
            'hits': 0,
            'misses': 0
        })

    hits = logs.filter(cache_hit=True).count()
    misses = total - hits
    avg_time = sum([log.response_time_ms for log in logs]) / total
    
    return JsonResponse({
        'total_queries': total,
        'hit_rate': (hits / total) * 100,
        'avg_response_time': round(avg_time, 2),
        'hits': hits,
        'misses': misses,
        'kv_hits': logs.filter(cache_type='KV').count(),
        'semantic_hits': logs.filter(cache_type='Semantic').count()
    })
