"""Initial migration - Create all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create papers table
    op.create_table('papers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('arxiv_id', sa.String(50), nullable=True),
        sa.Column('doi', sa.String(100), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', sa.JSON(), nullable=False),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('updated_date', sa.DateTime(), nullable=True),
        sa.Column('journal', sa.String(200), nullable=True),
        sa.Column('categories', sa.JSON(), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('methodology', sa.JSON(), nullable=True),
        sa.Column('github_repos', sa.JSON(), nullable=True),
        sa.Column('has_code', sa.Boolean(), nullable=False, default=False),
        sa.Column('processing_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('embedding_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for papers
    op.create_index('idx_papers_arxiv_id', 'papers', ['arxiv_id'], unique=True)
    op.create_index('idx_papers_doi', 'papers', ['doi'], unique=True)
    op.create_index('idx_papers_title', 'papers', ['title'])
    op.create_index('idx_papers_published_date', 'papers', ['published_date'])
    op.create_index('idx_papers_category_date', 'papers', ['categories', 'published_date'])
    op.create_index('idx_papers_status', 'papers', ['processing_status', 'embedding_status'])

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('affiliation', sa.String(200), nullable=True),
        sa.Column('research_interests', sa.JSON(), nullable=True),
        sa.Column('preferred_frameworks', sa.JSON(), nullable=True),
        sa.Column('experience_level', sa.String(20), nullable=False, default='intermediate'),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('total_queries', sa.Integer(), nullable=False, default=0),
        sa.Column('total_agents_created', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_active', 'users', ['is_active', 'last_login'])

    # Create paper_agents table
    op.create_table('paper_agents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('paper_id', sa.String(36), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('specialization', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('conversation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('response_time_avg', sa.Float(), nullable=True),
        sa.Column('user_rating_avg', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('memory_size', sa.Integer(), nullable=False, default=10),
        sa.Column('context_data', sa.JSON(), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )
    
    # Create indexes for paper_agents
    op.create_index('idx_agents_paper_id', 'paper_agents', ['paper_id'])
    op.create_index('idx_agents_paper_type', 'paper_agents', ['paper_id', 'agent_type'])
    op.create_index('idx_agents_status', 'paper_agents', ['status', 'last_interaction'])

    # Create agent_conversations table
    op.create_table('agent_conversations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('agent_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['paper_agents.id'], ondelete='CASCADE')
    )
    
    # Create indexes for agent_conversations
    op.create_index('idx_conversations_agent_id', 'agent_conversations', ['agent_id'])
    op.create_index('idx_conversations_session', 'agent_conversations', ['session_id', 'created_at'])
    op.create_index('idx_conversations_user', 'agent_conversations', ['user_id', 'created_at'])

    # Create research_topics table
    op.create_table('research_topics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('parent_topic_id', sa.String(36), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, default=0),
        sa.Column('paper_count', sa.Integer(), nullable=False, default=0),
        sa.Column('agent_count', sa.Integer(), nullable=False, default=0),
        sa.Column('popularity_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('first_paper_date', sa.DateTime(), nullable=True),
        sa.Column('latest_paper_date', sa.DateTime(), nullable=True),
        sa.Column('growth_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_topic_id'], ['research_topics.id'])
    )
    
    # Create indexes for research_topics
    op.create_index('idx_topics_name', 'research_topics', ['name'], unique=True)
    op.create_index('idx_topics_category', 'research_topics', ['category'])
    op.create_index('idx_topics_category_popularity', 'research_topics', ['category', 'popularity_score'])
    op.create_index('idx_topics_hierarchy', 'research_topics', ['parent_topic_id', 'level'])

    # Create paper_embeddings table
    op.create_table('paper_embeddings',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('paper_id', sa.String(36), nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('vector_db_id', sa.String(100), nullable=True),
        sa.Column('vector_db_provider', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE')
    )
    
    # Create indexes for paper_embeddings
    op.create_index('idx_embeddings_paper_id', 'paper_embeddings', ['paper_id'], unique=True)
    op.create_index('idx_embeddings_status', 'paper_embeddings', ['status', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('paper_embeddings')
    op.drop_table('research_topics')
    op.drop_table('agent_conversations')
    op.drop_table('paper_agents')
    op.drop_table('users')
    op.drop_table('papers')