"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('uuid', sa.String(length=36), nullable=False, comment='External UUID identifier'),
        sa.Column('name', sa.String(length=50), nullable=True, comment='User display name'),
        sa.Column('birth_date', sa.String(length=10), nullable=True, comment='Birth date in YYYY-MM-DD format'),
        sa.Column('birth_time', sa.String(length=8), nullable=True, comment='Birth time in HH:MM:SS format'),
        sa.Column('birth_location', sa.String(length=100), nullable=True, comment='Birth location for astrology'),
        sa.Column('zodiac_sign', sa.String(length=20), nullable=True, comment='Zodiac sign'),
        sa.Column('preferences', sa.Text(), nullable=True, comment='User preferences as JSON string'),
        sa.Column('last_active_at', sa.DateTime(), nullable=True, comment='Last activity timestamp'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='User account status'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Soft delete timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.CheckConstraint("zodiac_sign IN ('aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces')", name='check_zodiac_sign'),
    )
    
    # Create indexes for users table
    op.create_index('idx_users_uuid', 'users', ['uuid'])
    op.create_index('idx_users_zodiac', 'users', ['zodiac_sign'])
    op.create_index('idx_users_birth_date', 'users', ['birth_date'])
    op.create_index('idx_users_last_active', 'users', ['last_active_at'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_is_deleted', 'users', ['is_deleted'])
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('uuid', sa.String(length=36), nullable=False, comment='External UUID identifier'),
        sa.Column('session_id', sa.String(length=36), nullable=False, comment='Session UUID for WebSocket identification'),
        sa.Column('user_uuid', sa.String(length=36), nullable=True, comment='Associated user UUID'),
        sa.Column('character_name', sa.String(length=50), nullable=False, default='미라', comment='Live2D character name'),
        sa.Column('session_type', sa.String(length=20), nullable=False, default='anonymous', comment='Session type: anonymous or registered'),
        sa.Column('started_at', sa.DateTime(), nullable=False, comment='Session start timestamp'),
        sa.Column('ended_at', sa.DateTime(), nullable=True, comment='Session end timestamp'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='Session expiration timestamp'),
        sa.Column('status', sa.String(length=20), nullable=False, default='active', comment='Session status: active, expired, closed'),
        sa.Column('metadata', sa.Text(), nullable=True, comment='Session metadata as JSON string'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('session_id'),
        sa.ForeignKeyConstraint(['user_uuid'], ['users.uuid'], ondelete='SET NULL'),
        sa.CheckConstraint("session_type IN ('anonymous', 'registered')", name='check_session_type'),
        sa.CheckConstraint("status IN ('active', 'expired', 'closed')", name='check_session_status'),
    )
    
    # Create indexes for chat_sessions table
    op.create_index('idx_chat_sessions_session_id', 'chat_sessions', ['session_id'])
    op.create_index('idx_chat_sessions_user_uuid', 'chat_sessions', ['user_uuid'])
    op.create_index('idx_chat_sessions_status', 'chat_sessions', ['status'])
    op.create_index('idx_chat_sessions_expires_at', 'chat_sessions', ['expires_at'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('uuid', sa.String(length=36), nullable=False, comment='External UUID identifier'),
        sa.Column('message_id', sa.String(length=36), nullable=False, comment='Message UUID'),
        sa.Column('session_id', sa.String(length=36), nullable=False, comment='Associated session ID'),
        sa.Column('sender_type', sa.String(length=20), nullable=False, comment='Message sender: user or assistant'),
        sa.Column('content', sa.Text(), nullable=False, comment='Message content'),
        sa.Column('content_type', sa.String(length=20), nullable=False, default='text', comment='Content type: text, fortune_result, system'),
        sa.Column('live2d_emotion', sa.String(length=20), nullable=True, comment='Live2D emotion for this message'),
        sa.Column('live2d_motion', sa.String(length=50), nullable=True, comment='Live2D motion for this message'),
        sa.Column('audio_url', sa.String(length=255), nullable=True, comment='TTS audio file URL'),
        sa.Column('metadata', sa.Text(), nullable=True, comment='Message metadata as JSON string'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='Soft delete timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('message_id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        sa.CheckConstraint("sender_type IN ('user', 'assistant')", name='check_sender_type'),
        sa.CheckConstraint("content_type IN ('text', 'fortune_result', 'system')", name='check_content_type'),
    )
    
    # Create indexes for chat_messages table
    op.create_index('idx_chat_messages_message_id', 'chat_messages', ['message_id'])
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_sender_type', 'chat_messages', ['sender_type'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index('idx_chat_messages_is_deleted', 'chat_messages', ['is_deleted'])
    
    # Create fortune_sessions table
    op.create_table(
        'fortune_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('uuid', sa.String(length=36), nullable=False, comment='External UUID identifier'),
        sa.Column('fortune_id', sa.String(length=36), nullable=False, comment='Fortune UUID for external reference'),
        sa.Column('session_id', sa.String(length=36), nullable=True, comment='Associated chat session ID'),
        sa.Column('user_uuid', sa.String(length=36), nullable=True, comment='Associated user UUID'),
        sa.Column('fortune_type', sa.String(length=20), nullable=False, comment='Type of fortune reading'),
        sa.Column('question', sa.Text(), nullable=True, comment="User's question (for tarot readings)"),
        sa.Column('question_type', sa.String(length=20), nullable=True, comment='Category of question'),
        sa.Column('result', sa.Text(), nullable=False, comment='Fortune result as JSON string'),
        sa.Column('cached_until', sa.DateTime(), nullable=True, comment='Cache expiration timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('fortune_id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_uuid'], ['users.uuid'], ondelete='SET NULL'),
        sa.CheckConstraint("fortune_type IN ('daily', 'tarot', 'zodiac', 'oriental')", name='check_fortune_type'),
        sa.CheckConstraint("question_type IN ('love', 'money', 'health', 'work', 'general')", name='check_question_type'),
    )
    
    # Create indexes for fortune_sessions table
    op.create_index('idx_fortune_sessions_fortune_id', 'fortune_sessions', ['fortune_id'])
    op.create_index('idx_fortune_sessions_session_id', 'fortune_sessions', ['session_id'])
    op.create_index('idx_fortune_sessions_user_uuid', 'fortune_sessions', ['user_uuid'])
    op.create_index('idx_fortune_sessions_fortune_type', 'fortune_sessions', ['fortune_type'])
    op.create_index('idx_fortune_sessions_created_at', 'fortune_sessions', ['created_at'])
    op.create_index('idx_fortune_sessions_cached_until', 'fortune_sessions', ['cached_until'])
    
    # Create tarot_cards table
    op.create_table(
        'tarot_cards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('card_name', sa.String(length=50), nullable=False, comment='Card name in English'),
        sa.Column('card_name_ko', sa.String(length=50), nullable=False, comment='Card name in Korean'),
        sa.Column('card_number', sa.Integer(), nullable=True, comment='Card number (for numbered cards)'),
        sa.Column('suit', sa.String(length=20), nullable=False, comment='Tarot suit'),
        sa.Column('upright_meaning', sa.Text(), nullable=True, comment='Upright card meaning'),
        sa.Column('reversed_meaning', sa.Text(), nullable=True, comment='Reversed card meaning'),
        sa.Column('general_interpretation', sa.Text(), nullable=True, comment='General interpretation'),
        sa.Column('love_interpretation', sa.Text(), nullable=True, comment='Love and relationship interpretation'),
        sa.Column('career_interpretation', sa.Text(), nullable=True, comment='Career and work interpretation'),
        sa.Column('health_interpretation', sa.Text(), nullable=True, comment='Health interpretation'),
        sa.Column('image_url', sa.String(length=255), nullable=True, comment='Card image URL'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('card_name'),
        sa.CheckConstraint("suit IN ('major', 'wands', 'cups', 'swords', 'pentacles')", name='check_tarot_suit'),
    )
    
    # Create indexes for tarot_cards table
    op.create_index('idx_tarot_cards_card_name', 'tarot_cards', ['card_name'])
    op.create_index('idx_tarot_cards_suit', 'tarot_cards', ['suit'])
    
    # Create zodiac_info table
    op.create_table(
        'zodiac_info',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('sign', sa.String(length=20), nullable=False, comment='Zodiac sign in English'),
        sa.Column('sign_ko', sa.String(length=20), nullable=False, comment='Zodiac sign in Korean'),
        sa.Column('date_range', sa.String(length=50), nullable=True, comment='Date range for the sign'),
        sa.Column('element', sa.String(length=20), nullable=True, comment='Element (fire, earth, air, water)'),
        sa.Column('ruling_planet', sa.String(length=20), nullable=True, comment='Ruling planet'),
        sa.Column('personality_traits', sa.Text(), nullable=True, comment='Personality traits as JSON string'),
        sa.Column('strengths', sa.Text(), nullable=True, comment='Strengths as JSON string'),
        sa.Column('weaknesses', sa.Text(), nullable=True, comment='Weaknesses as JSON string'),
        sa.Column('compatible_signs', sa.Text(), nullable=True, comment='Compatible signs as JSON string'),
        sa.Column('lucky_colors', sa.Text(), nullable=True, comment='Lucky colors as JSON string'),
        sa.Column('lucky_numbers', sa.Text(), nullable=True, comment='Lucky numbers as JSON string'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sign'),
        sa.CheckConstraint("sign IN ('aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces')", name='check_zodiac_sign_info'),
        sa.CheckConstraint("element IN ('fire', 'earth', 'air', 'water')", name='check_zodiac_element'),
    )
    
    # Create indexes for zodiac_info table
    op.create_index('idx_zodiac_info_sign', 'zodiac_info', ['sign'])
    op.create_index('idx_zodiac_info_element', 'zodiac_info', ['element'])
    
    # Create live2d_models table
    op.create_table(
        'live2d_models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('model_name', sa.String(length=50), nullable=False, comment='Unique model identifier'),
        sa.Column('display_name', sa.String(length=50), nullable=False, comment='Display name for the model'),
        sa.Column('model_path', sa.String(length=255), nullable=False, comment='Path to model3.json file'),
        sa.Column('emotions', sa.Text(), nullable=False, comment='Emotion mappings as JSON string'),
        sa.Column('motions', sa.Text(), nullable=False, comment='Motion mappings as JSON string'),
        sa.Column('default_emotion', sa.String(length=20), nullable=False, default='neutral', comment='Default emotion state'),
        sa.Column('description', sa.Text(), nullable=True, comment='Model description'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Model availability status'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name'),
    )
    
    # Create indexes for live2d_models table
    op.create_index('idx_live2d_models_model_name', 'live2d_models', ['model_name'])
    op.create_index('idx_live2d_models_is_active', 'live2d_models', ['is_active'])
    
    # Create content_cache table
    op.create_table(
        'content_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('cache_key', sa.String(length=255), nullable=False, comment='Unique cache key'),
        sa.Column('cache_type', sa.String(length=50), nullable=False, comment='Type of cached content'),
        sa.Column('content', sa.Text(), nullable=False, comment='Cached content as JSON string'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='Cache expiration timestamp'),
        sa.Column('access_count', sa.Integer(), nullable=False, default=0, comment='Number of times cache was accessed'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True, comment='Last access timestamp'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
        sa.CheckConstraint("cache_type IN ('daily_fortune', 'zodiac_weekly', 'zodiac_monthly', 'tarot_cards', 'zodiac_info', 'system_config', 'user_profile', 'live2d_config', 'api_response')", name='check_cache_type'),
    )
    
    # Create indexes for content_cache table
    op.create_index('idx_content_cache_key_type', 'content_cache', ['cache_key', 'cache_type'])
    op.create_index('idx_content_cache_expires_at', 'content_cache', ['expires_at'])
    op.create_index('idx_content_cache_type_expires', 'content_cache', ['cache_type', 'expires_at'])
    
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('setting_key', sa.String(length=100), nullable=False, comment='Unique setting key'),
        sa.Column('setting_value', sa.Text(), nullable=True, comment='Setting value (can be string, JSON, etc.)'),
        sa.Column('setting_type', sa.String(length=20), nullable=False, default='string', comment='Type of setting value'),
        sa.Column('description', sa.Text(), nullable=True, comment='Setting description'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False, comment='Whether setting can be exposed to client'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('setting_key'),
        sa.CheckConstraint("setting_type IN ('string', 'integer', 'boolean', 'json', 'float')", name='check_setting_type'),
    )
    
    # Create indexes for system_settings table
    op.create_index('idx_system_settings_setting_key', 'system_settings', ['setting_key'])
    op.create_index('idx_system_settings_is_public', 'system_settings', ['is_public'])
    
    # Create user_analytics table
    op.create_table(
        'user_analytics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('user_uuid', sa.String(length=36), nullable=True, comment='Associated user UUID'),
        sa.Column('session_id', sa.String(length=36), nullable=True, comment='Associated session ID'),
        sa.Column('event_type', sa.String(length=50), nullable=False, comment='Type of event'),
        sa.Column('event_data', sa.Text(), nullable=True, comment='Event data as JSON string'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='Client IP address'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Client User-Agent string'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_uuid'], ['users.uuid'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        sa.CheckConstraint("event_type IN ('session_start', 'session_end', 'fortune_request', 'message_sent', 'error_occurred', 'page_view', 'api_call', 'live2d_interaction', 'user_registration', 'user_login', 'user_logout', 'cache_hit', 'cache_miss')", name='check_event_type'),
    )
    
    # Create indexes for user_analytics table
    op.create_index('idx_user_analytics_user_uuid', 'user_analytics', ['user_uuid'])
    op.create_index('idx_user_analytics_session_id', 'user_analytics', ['session_id'])
    op.create_index('idx_user_analytics_event_type', 'user_analytics', ['event_type'])
    op.create_index('idx_user_analytics_created_at', 'user_analytics', ['created_at'])
    op.create_index('idx_user_analytics_event_date', 'user_analytics', ['event_type', 'created_at'])


def downgrade() -> None:
    """Downgrade database schema"""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('user_analytics')
    op.drop_table('system_settings')
    op.drop_table('content_cache')
    op.drop_table('live2d_models')
    op.drop_table('zodiac_info')
    op.drop_table('tarot_cards')
    op.drop_table('fortune_sessions')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('users')