# Data Pipeline Documentation

## Overview

The data pipeline is responsible for continuously ingesting, processing, and organizing research papers from multiple academic sources, with a focus on creating intelligent groupings and tracking research evolution.

## Data Sources

### Primary Sources

#### arXiv (Primary Source)
```python
# Configuration for arXiv ingestion
ARXIV_CONFIG = {
    "categories": [
        "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",  # Computer Science
        "stat.ML", "math.ST",                          # Statistics & Math
        "q-bio.QM", "physics.data-an"                  # Quantitative Biology & Physics
    ],
    "max_results_per_query": 1000,
    "update_frequency": "hourly",
    "rate_limit": 3  # requests per second
}
```

#### PubMed (Biomedical Literature)
- **API**: Entrez Programming Utilities
- **Focus**: Medical and life science research
- **Update Frequency**: Daily
- **Volume**: ~5,000 new papers daily

#### IEEE Xplore
- **Coverage**: Engineering and technology papers
- **API**: REST API with authentication
- **Update Frequency**: Daily
- **Rate Limit**: 200 requests/hour

### Data Ingestion Pipeline

#### 1. Scheduled Ingestion
```python
# Airflow DAG for paper ingestion
from airflow import DAG
from airflow.operators.python import PythonOperator

def ingest_arxiv_papers():
    """Fetch latest papers from arXiv"""
    import arxiv
    
    client = arxiv.Client()
    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.LG",
        max_results=1000,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    papers = []
    for paper in client.results(search):
        papers.append({
            'arxiv_id': paper.entry_id.split('/')[-1],
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'abstract': paper.summary,
            'categories': paper.categories,
            'published': paper.published,
            'updated': paper.updated,
            'pdf_url': paper.pdf_url
        })
    
    return papers

# DAG definition
dag = DAG(
    'paper_ingestion',
    schedule_interval='@hourly',
    catchup=False
)

ingest_task = PythonOperator(
    task_id='ingest_arxiv',
    python_callable=ingest_arxiv_papers,
    dag=dag
)
```

#### 2. Real-time Processing
```python
# Kafka consumer for real-time paper processing
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'new_papers',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:
    paper_data = message.value
    process_paper_async.delay(paper_data)
```

## Data Processing Stages

### Stage 1: Text Preprocessing
```python
def preprocess_paper_text(paper):
    """Clean and normalize paper text"""
    import re
    from nltk.corpus import stopwords
    
    # Clean title and abstract
    title = re.sub(r'[^\w\s]', '', paper['title'].lower())
    abstract = re.sub(r'[^\w\s]', '', paper['abstract'].lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    title_words = [w for w in title.split() if w not in stop_words]
    abstract_words = [w for w in abstract.split() if w not in stop_words]
    
    return {
        'clean_title': ' '.join(title_words),
        'clean_abstract': ' '.join(abstract_words),
        'full_text': ' '.join(title_words + abstract_words)
    }
```

### Stage 2: Feature Extraction
```python
def extract_paper_features(paper):
    """Extract key features for clustering and analysis"""
    from transformers import AutoTokenizer, AutoModel
    import torch
    
    # Load SciBERT model for scientific text
    tokenizer = AutoTokenizer.from_pretrained('allenai/scibert_scivocab_uncased')
    model = AutoModel.from_pretrained('allenai/scibert_scivocab_uncased')
    
    # Generate embeddings
    text = f"{paper['title']} {paper['abstract']}"
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
    
    return {
        'embeddings': embeddings.tolist(),
        'author_count': len(paper['authors']),
        'category_primary': paper['categories'][0] if paper['categories'] else None,
        'text_length': len(paper['abstract']),
        'publication_year': paper['published'].year
    }
```

### Stage 3: Intelligent Grouping
```python
def cluster_papers(papers_batch):
    """Group papers using hierarchical clustering"""
    from sklearn.cluster import HDBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    # Extract embeddings
    embeddings = np.array([p['embeddings'] for p in papers_batch])
    
    # Perform clustering
    clusterer = HDBSCAN(
        min_cluster_size=5,
        metric='cosine',
        cluster_selection_epsilon=0.3
    )
    
    cluster_labels = clusterer.fit_predict(embeddings)
    
    # Group papers by cluster
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(papers_batch[i])
    
    return clusters
```

### Stage 4: Research Timeline Construction
```python
def build_research_timeline(topic_papers):
    """Create chronological timeline for a research topic"""
    import networkx as nx
    from datetime import datetime
    
    # Sort papers by publication date
    sorted_papers = sorted(topic_papers, key=lambda x: x['published'])
    
    # Build citation network
    G = nx.DiGraph()
    
    for paper in sorted_papers:
        G.add_node(paper['id'], **paper)
        
        # Add citation edges (simplified - would use actual citation data)
        for cited_paper in find_citations(paper):
            if cited_paper['id'] in G.nodes:
                G.add_edge(cited_paper['id'], paper['id'])
    
    # Identify breakthrough papers
    breakthrough_scores = {}
    for node in G.nodes:
        # Calculate influence based on citation network
        in_degree = G.in_degree(node)
        out_degree = G.out_degree(node)
        breakthrough_scores[node] = (in_degree * 0.7) + (out_degree * 0.3)
    
    return {
        'timeline': sorted_papers,
        'citation_network': G,
        'breakthrough_papers': breakthrough_scores
    }
```

## Data Quality & Validation

### Duplicate Detection
```python
def detect_duplicates(new_paper, existing_papers):
    """Identify potential duplicate papers"""
    from difflib import SequenceMatcher
    
    for existing in existing_papers:
        # Title similarity
        title_similarity = SequenceMatcher(
            None, 
            new_paper['title'].lower(), 
            existing['title'].lower()
        ).ratio()
        
        # Author overlap
        author_overlap = len(set(new_paper['authors']) & set(existing['authors']))
        author_ratio = author_overlap / max(len(new_paper['authors']), len(existing['authors']))
        
        # Combined similarity score
        similarity_score = (title_similarity * 0.7) + (author_ratio * 0.3)
        
        if similarity_score > 0.85:
            return existing['id']  # Potential duplicate
    
    return None
```

### Data Validation Rules
```python
VALIDATION_RULES = {
    'title': {
        'min_length': 10,
        'max_length': 500,
        'required': True
    },
    'abstract': {
        'min_length': 50,
        'max_length': 5000,
        'required': True
    },
    'authors': {
        'min_count': 1,
        'max_count': 50,
        'required': True
    },
    'published_date': {
        'min_year': 1990,
        'max_year': datetime.now().year + 1,
        'required': True
    }
}
```

## Performance Optimization

### Batch Processing
- Process papers in batches of 100-500
- Parallel processing using Celery workers
- Memory-efficient streaming for large datasets

### Caching Strategy
- Cache embeddings for processed papers
- Redis cache for frequently accessed paper groups
- Elasticsearch for fast full-text search

### Monitoring & Alerting
```python
# Metrics collection
PIPELINE_METRICS = {
    'papers_processed_per_hour': 0,
    'processing_errors': 0,
    'duplicate_detection_rate': 0,
    'clustering_accuracy': 0,
    'average_processing_time': 0
}

def track_pipeline_metrics():
    """Send metrics to monitoring system"""
    import prometheus_client
    
    papers_processed = prometheus_client.Counter(
        'papers_processed_total',
        'Total number of papers processed'
    )
    
    processing_time = prometheus_client.Histogram(
        'paper_processing_seconds',
        'Time spent processing papers'
    )
```

## Error Handling & Recovery

### Retry Logic
```python
from celery import Celery
from celery.exceptions import Retry

@celery.task(bind=True, max_retries=3)
def process_paper_with_retry(self, paper_data):
    try:
        return process_paper(paper_data)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            # Log failure and move to dead letter queue
            log_processing_failure(paper_data, exc)
            raise
```

### Data Recovery
- Failed papers stored in dead letter queue
- Manual reprocessing interface
- Backup and restore procedures for critical data