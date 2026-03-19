from django.db import models
from pgvector.django import VectorField

class Document(models.Model):
    content = models.TextField()
    source = models.CharField(max_length=255, blank=True, null=True)
    embedding = VectorField(dimensions=384)  # Dimensions for all-MiniLM-L6-v2

    def __str__(self):
        return f"Document {self.id}: {self.content[:50]}..."

class QueryLog(models.Model):
    query = models.TextField()
    answer = models.TextField()
    cache_hit = models.BooleanField(default=False)
    cache_type = models.CharField(max_length=20, blank=True, null=True) # 'KV' or 'Semantic'
    response_time_ms = models.IntegerField()
    embedding = VectorField(dimensions=384) # Store query embedding for semantic caching
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query {self.id}: {self.query[:50]}..."
