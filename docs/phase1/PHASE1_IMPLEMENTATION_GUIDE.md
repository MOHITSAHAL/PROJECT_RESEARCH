# Phase 1 Implementation Guide: Core Infrastructure & Data Pipeline

## Quick Start Guide

### 1. Environment Setup
```bash
# Clone and navigate to project
cd Project_research

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY, GITHUB_TOKEN (optional)
nano .env

# Start all services
docker-compose up -d
```

### 2. Verify Installation
```bash
# Check all services are running
docker-compose ps

# Check backend API
curl http://localhost:8000/docs

# Check database connections
docker-compose logs backend | grep "Database connected"
```

### 3. Test Data Pipeline
```bash
# Test arXiv integration
curl -X POST "http://localhost:8000/data-pipeline/search-arxiv" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention", "max_results": 5}'

# Process a specific paper
curl -X POST "http://localhost:8000/data-pipeline/process-paper/1706.03762"

# Start bulk ingestion (background task)
curl -X POST "http://localhost:8000/data-pipeline/ingest-papers" \
  -H "Content-Type: application/json" \
  -d '{"days_back": 3}'
```

## Architecture Overview

### Data Flow
```
arXiv API → PDF Download → Content Extraction → GitHub Analysis → Database Storage
     ↓              ↓              ↓               ↓              ↓
  Metadata      Full Text      Sections       Repo Quality   Vector DB
  Filtering     Extraction     Keywords       Assessment     Embeddings
```

### Component Interaction
```
API Endpoints ←→ DataPipelineService ←→ Pipeline Components
     ↓                    ↓                      ↓
Celery Tasks ←→ Background Processing ←→ Database Storage
     ↓                    ↓                      ↓
Scheduled Jobs ←→ Automated Ingestion ←→ Vector/Graph DBs
```

## Core Components

### 1. ArxivClient
**Purpose**: Fetch research papers from arXiv API  
**Key Features**:
- AI category filtering (cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.RO, stat.ML)
- Rate limiting (3 seconds between requests)
- Date range filtering for recent papers
- Search functionality with relevance ranking

**Usage Example**:
```python
from data_pipeline.ingestion.arxiv_client import ArxivClient

client = ArxivClient(max_results=100, delay_seconds=3.0)
papers = await client.fetch_ai_papers(days_back=7)
```

### 2. PDFProcessor
**Purpose**: Extract structured content from research paper PDFs  
**Key Features**:
- PDF download with timeout handling
- Text extraction (pdfplumber + PyPDF2 fallback)
- Section identification (abstract, methodology, results, etc.)
- GitHub URL detection
- Methodology keyword extraction

**Usage Example**:
```python
from data_pipeline.processing.pdf_processor import PDFProcessor

processor = PDFProcessor()
content = await processor.download_and_process_pdf(pdf_url)
```

### 3. GitHubRepoAnalyzer
**Purpose**: Analyze GitHub repositories linked to papers  
**Key Features**:
- Repository metadata extraction
- Implementation complexity assessment
- Tutorial quality scoring
- Key file identification
- README analysis

**Usage Example**:
```python
from data_pipeline.github_integration.repo_analyzer import GitHubRepoAnalyzer

analyzer = GitHubRepoAnalyzer(github_token="your_token")
analysis = await analyzer.analyze_repository(github_url)
```

### 4. DataPipelineService
**Purpose**: Orchestrate the complete pipeline workflow  
**Key Features**:
- End-to-end paper processing
- Database integration
- Error handling and recovery
- Progress tracking

**Usage Example**:
```python
from backend.services.data_pipeline_service import DataPipelineService

service = DataPipelineService(paper_repository, paper_domain)
result = await service.fetch_and_process_papers(days_back=7)
```

## API Endpoints

### Paper Ingestion
```http
POST /data-pipeline/ingest-papers
Content-Type: application/json

{
  "days_back": 7,
  "max_papers": 100
}
```

### Single Paper Processing
```http
POST /data-pipeline/process-paper/{arxiv_id}
```

### arXiv Search
```http
POST /data-pipeline/search-arxiv
Content-Type: application/json

{
  "query": "transformer attention mechanism",
  "max_results": 50
}
```

### GitHub Analysis
```http
POST /data-pipeline/analyze-github
Content-Type: application/json

{
  "github_url": "https://github.com/huggingface/transformers"
}
```

### Pipeline Status
```http
GET /data-pipeline/status
```

## Background Tasks

### Scheduled Tasks
- **Daily Ingestion**: Runs at 2 AM UTC, processes last 24 hours
- **Weekly Backfill**: Runs Mondays at 3 AM UTC, catches missed papers
- **Cleanup**: Runs daily at 4 AM UTC, removes old task results

### Manual Tasks
```bash
# Process specific paper
celery -A backend.core.celery_app call backend.tasks.pipeline_tasks.process_paper_by_id --args='["1706.03762"]'

# Batch process multiple papers
celery -A backend.core.celery_app call backend.tasks.pipeline_tasks.batch_process_papers --args='[["1706.03762", "1810.04805"]]'
```

## Database Schema

### Papers Table
```sql
CREATE TABLE papers (
    id UUID PRIMARY KEY,
    arxiv_id VARCHAR(50) UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT[],
    categories TEXT[],
    published_date TIMESTAMP,
    pdf_url TEXT,
    full_text TEXT,
    github_repos TEXT[],
    processing_status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Vector Storage (Weaviate)
```json
{
  "class": "Paper",
  "properties": [
    {"name": "arxiv_id", "dataType": ["string"]},
    {"name": "title", "dataType": ["text"]},
    {"name": "abstract", "dataType": ["text"]},
    {"name": "content", "dataType": ["text"]},
    {"name": "categories", "dataType": ["string[]"]},
    {"name": "embedding", "dataType": ["number[]"]}
  ]
}
```

### Citation Network (Neo4j)
```cypher
CREATE (p:Paper {arxiv_id: "1706.03762", title: "Attention Is All You Need"})
CREATE (c:Paper {arxiv_id: "1810.04805", title: "BERT"})
CREATE (p)-[:CITED_BY]->(c)
```

## Configuration

### Environment Variables
```bash
# Data Pipeline
ARXIV_RATE_LIMIT=3
MAX_PAPERS_PER_BATCH=100
GITHUB_TOKEN=your_github_token
PDF_PROCESSING_TIMEOUT=300
MAX_PDF_SIZE_MB=50

# Databases
DATABASE_URL=postgresql://user:pass@localhost:5432/research_papers
NEO4J_URI=bolt://localhost:7687
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Docker Services
```yaml
services:
  backend:        # FastAPI application
  postgres:       # Primary database
  redis:          # Cache and message broker
  neo4j:          # Graph database for citations
  weaviate:       # Vector database for embeddings
  celery-worker:  # Background task processor
  celery-beat:    # Task scheduler
  jupyter:        # Development environment
  prometheus:     # Metrics collection
  grafana:        # Monitoring dashboard
```

## Monitoring & Debugging

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# Check pipeline status
curl http://localhost:8000/data-pipeline/status

# View recent tasks
curl http://localhost:8000/tasks/recent
```

### Logs
```bash
# Backend logs
docker-compose logs -f backend

# Celery worker logs
docker-compose logs -f celery-worker

# Database logs
docker-compose logs -f postgres
```

### Metrics
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)

## Troubleshooting

### Common Issues

#### 1. arXiv Rate Limiting
**Symptoms**: HTTP 429 errors, slow responses  
**Solution**: Increase `ARXIV_RATE_LIMIT` delay, reduce batch sizes

#### 2. PDF Processing Failures
**Symptoms**: Empty content, processing timeouts  
**Solution**: Check `PDF_PROCESSING_TIMEOUT`, verify PDF URLs

#### 3. GitHub API Limits
**Symptoms**: Repository analysis failures  
**Solution**: Add `GITHUB_TOKEN` for higher rate limits

#### 4. Memory Issues
**Symptoms**: Container crashes, slow processing  
**Solution**: Increase Docker memory limits, reduce batch sizes

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run single component test
python -c "
import asyncio
from data_pipeline.ingestion.arxiv_client import ArxivClient
client = ArxivClient(max_results=1)
papers = asyncio.run(client.fetch_ai_papers(days_back=1))
print(f'Fetched {len(papers)} papers')
"
```

## Performance Optimization

### Recommended Settings
```bash
# Production settings
ARXIV_RATE_LIMIT=3          # Respect arXiv limits
MAX_PAPERS_PER_BATCH=50     # Balance speed vs memory
PDF_PROCESSING_TIMEOUT=300  # 5 minutes per PDF
CELERY_WORKER_CONCURRENCY=4 # Based on CPU cores
```

### Scaling Considerations
- **Horizontal**: Add more Celery workers
- **Vertical**: Increase memory for PDF processing
- **Database**: Use read replicas for queries
- **Cache**: Implement Redis clustering

## Security

### API Security
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS configuration for frontend
- JWT authentication (ready for Phase 2)

### Data Security
- Database connection encryption
- Secure environment variable handling
- PDF download size limits
- GitHub token scope restrictions

## Next Steps for Phase 2

### AI Agent Framework Preparation
1. **Vector Embeddings**: Generate embeddings for all processed papers
2. **LangChain Integration**: Set up agent framework
3. **Model Configuration**: Configure OpenAI/Anthropic models
4. **Agent Templates**: Design paper-specific agent prompts

### Database Enhancements
1. **Agent Storage**: Add agent configuration tables
2. **Conversation History**: Store agent interactions
3. **Performance Metrics**: Track agent effectiveness
4. **User Preferences**: Store personalization data

The Phase 1 implementation provides a robust foundation for the AI Agent Framework in Phase 2, with scalable architecture and comprehensive monitoring capabilities.