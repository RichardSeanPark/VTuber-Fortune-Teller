"""
Database utilities for testing and validation

Utility functions for database testing, seeding, and validation.
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..config.database import db_manager
from ..models import *
from ..repositories import *
from ..services.database_service import database_service
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)


async def test_database_connection() -> Dict[str, Any]:
    """Test database connection and basic operations"""
    results = {
        'connection_test': False,
        'table_creation_test': False,
        'basic_crud_test': False,
        'repository_test': False,
        'cache_test': False,
        'performance_test': False,
        'errors': []
    }
    
    try:
        # Test 1: Basic connection
        logger.info("Testing database connection...")
        health = await db_manager.check_database_health()
        if health.get('status') == 'healthy':
            results['connection_test'] = True
            logger.info("✅ Database connection successful")
        else:
            results['errors'].append(f"Database connection failed: {health}")
            
        # Test 2: Table creation
        logger.info("Testing table creation...")
        await db_manager.create_tables()
        results['table_creation_test'] = True
        logger.info("✅ Table creation successful")
        
        # Test 3: Basic CRUD operations
        logger.info("Testing basic CRUD operations...")
        async with db_manager.get_session() as session:
            # Test User model
            test_user = User(
                name="Test User",
                birth_date="1990-01-01",
                zodiac_sign="capricorn",
                preferences='{"test": true}'
            )
            session.add(test_user)
            await session.flush()
            
            # Test read
            found_user = await session.get(User, test_user.id)
            if found_user and found_user.name == "Test User":
                results['basic_crud_test'] = True
                logger.info("✅ Basic CRUD operations successful")
            else:
                results['errors'].append("CRUD test failed: User not found or incorrect data")
                
        # Test 4: Repository layer
        logger.info("Testing repository layer...")
        async with db_manager.get_session() as session:
            user_repo = UserRepository(session)
            
            # Test create
            new_user = await user_repo.create(
                name="Repository Test User",
                birth_date="1995-06-15",
                zodiac_sign="gemini"
            )
            
            # Test find
            found_user = await user_repo.find_by_uuid(new_user.uuid)
            if found_user and found_user.name == "Repository Test User":
                results['repository_test'] = True
                logger.info("✅ Repository layer test successful")
            else:
                results['errors'].append("Repository test failed")
                
        # Test 5: Cache service
        logger.info("Testing cache service...")
        cache_service.set("test_key", {"test": "data"}, 60)
        cached_value = cache_service.get("test_key")
        if cached_value and cached_value.get("test") == "data":
            results['cache_test'] = True
            logger.info("✅ Cache service test successful")
        else:
            results['errors'].append("Cache test failed")
            
        # Test 6: Performance optimization
        logger.info("Testing performance optimizations...")
        async with db_manager.get_session() as session:
            await database_service.optimize_sqlite_connection(session)
            
        db_info = await database_service.get_database_info()
        if db_info.get('journal_mode') == 'wal':
            results['performance_test'] = True
            logger.info("✅ Performance optimization test successful")
        else:
            results['errors'].append("Performance test failed: WAL mode not enabled")
            
    except Exception as e:
        error_msg = f"Database test failed: {e}"
        results['errors'].append(error_msg)
        logger.error(error_msg)
    
    # Summary
    total_tests = 6
    passed_tests = sum(1 for key, value in results.items() 
                      if key != 'errors' and value is True)
    
    results['summary'] = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,
        'success_rate': round((passed_tests / total_tests) * 100, 2)
    }
    
    logger.info(f"Database tests completed: {passed_tests}/{total_tests} passed")
    return results


async def seed_sample_data() -> Dict[str, Any]:
    """Seed database with sample data for testing"""
    results = {
        'users_created': 0,
        'zodiac_info_created': 0,
        'tarot_cards_created': 0,
        'live2d_models_created': 0,
        'system_settings_created': 0,
        'errors': []
    }
    
    try:
        async with db_manager.get_session() as session:
            # Create sample zodiac info
            zodiac_data = [
                {
                    'sign': 'aries',
                    'sign_ko': '양자리',
                    'date_range': '3월 21일 ~ 4월 19일',
                    'element': 'fire',
                    'ruling_planet': '화성',
                    'personality_traits': '["열정적", "리더십", "용감함", "독립적"]',
                    'strengths': '["결단력", "에너지", "낙관적"]',
                    'weaknesses': '["성급함", "충동적", "이기적"]',
                    'compatible_signs': '["leo", "sagittarius", "gemini", "aquarius"]',
                    'lucky_colors': '["빨간색", "주황색"]',
                    'lucky_numbers': '[1, 8, 17]'
                },
                {
                    'sign': 'taurus',
                    'sign_ko': '황소자리',
                    'date_range': '4월 20일 ~ 5월 20일',
                    'element': 'earth',
                    'ruling_planet': '금성',
                    'personality_traits': '["안정적", "실용적", "인내심", "충실함"]',
                    'strengths': '["신뢰성", "인내력", "책임감"]',
                    'weaknesses': '["고집", "게으름", "물질주의"]',
                    'compatible_signs': '["virgo", "capricorn", "cancer", "pisces"]',
                    'lucky_colors': '["초록색", "분홍색"]',
                    'lucky_numbers': '[2, 6, 9, 12, 24]'
                }
            ]
            
            for zodiac in zodiac_data:
                existing = await session.execute(
                    text("SELECT id FROM zodiac_info WHERE sign = :sign"),
                    {'sign': zodiac['sign']}
                )
                if not existing.first():
                    zodiac_obj = ZodiacInfo(**zodiac)
                    session.add(zodiac_obj)
                    results['zodiac_info_created'] += 1
            
            # Create sample tarot cards
            tarot_data = [
                {
                    'card_name': 'The Fool',
                    'card_name_ko': '바보',
                    'card_number': 0,
                    'suit': 'major',
                    'upright_meaning': '새로운 시작, 순수함, 자유로운 정신',
                    'reversed_meaning': '무모함, 충동적 행동, 준비 부족',
                    'general_interpretation': '새로운 여행이나 모험의 시작을 의미합니다.',
                    'love_interpretation': '새로운 만남이나 순수한 사랑의 시작',
                    'career_interpretation': '새로운 직업이나 프로젝트의 시작',
                    'health_interpretation': '새로운 건강 습관이나 치료법 도입'
                },
                {
                    'card_name': 'The Magician',
                    'card_name_ko': '마법사',
                    'card_number': 1,
                    'suit': 'major',
                    'upright_meaning': '의지력, 창조력, 기술, 자신감',
                    'reversed_meaning': '의지 부족, 속임수, 오만함',
                    'general_interpretation': '당신의 의지와 능력으로 목표를 달성할 수 있습니다.',
                    'love_interpretation': '적극적인 구애나 관계에서의 주도권',
                    'career_interpretation': '기술과 능력을 발휘할 기회',
                    'health_interpretation': '의지력으로 건강을 회복할 수 있음'
                }
            ]
            
            for tarot in tarot_data:
                existing = await session.execute(
                    text("SELECT id FROM tarot_cards WHERE card_name = :name"),
                    {'name': tarot['card_name']}
                )
                if not existing.first():
                    tarot_obj = TarotCardDB(**tarot)
                    session.add(tarot_obj)
                    results['tarot_cards_created'] += 1
            
            # Create sample Live2D model
            live2d_data = {
                'model_name': 'mira',
                'display_name': '미라',
                'model_path': '/static/live2d/mira/mira.model3.json',
                'emotions': json.dumps({
                    'neutral': 0,
                    'joy': 1,
                    'thinking': 2,
                    'concern': 3,
                    'surprise': 4,
                    'mystical': 5,
                    'comfort': 6,
                    'playful': 7
                }),
                'motions': json.dumps({
                    'greeting': 'motions/greeting.motion3.json',
                    'card_draw': 'motions/card_draw.motion3.json',
                    'crystal_gaze': 'motions/crystal_gaze.motion3.json',
                    'blessing': 'motions/blessing.motion3.json',
                    'special_reading': 'motions/special_reading.motion3.json',
                    'thinking_pose': 'motions/thinking_pose.motion3.json'
                }),
                'default_emotion': 'neutral',
                'description': '신비로운 운세 전문가 미라'
            }
            
            existing_model = await session.execute(
                text("SELECT id FROM live2d_models WHERE model_name = :name"),
                {'name': live2d_data['model_name']}
            )
            if not existing_model.first():
                live2d_obj = Live2DModel(**live2d_data)
                session.add(live2d_obj)
                results['live2d_models_created'] += 1
            
            # Create sample system settings
            settings_data = [
                {
                    'setting_key': 'app_version',
                    'setting_value': '1.0.0',
                    'setting_type': 'string',
                    'description': 'Application version',
                    'is_public': True
                },
                {
                    'setting_key': 'max_session_duration_hours',
                    'setting_value': '24',
                    'setting_type': 'integer',
                    'description': 'Maximum session duration in hours',
                    'is_public': False
                },
                {
                    'setting_key': 'enable_fortune_cache',
                    'setting_value': 'true',
                    'setting_type': 'boolean',
                    'description': 'Enable fortune result caching',
                    'is_public': False
                }
            ]
            
            for setting in settings_data:
                existing_setting = await session.execute(
                    text("SELECT id FROM system_settings WHERE setting_key = :key"),
                    {'key': setting['setting_key']}
                )
                if not existing_setting.first():
                    setting_obj = SystemSetting(**setting)
                    session.add(setting_obj)
                    results['system_settings_created'] += 1
            
            # Create sample users
            users_data = [
                {
                    'name': 'Alice Johnson',
                    'birth_date': '1992-03-25',
                    'zodiac_sign': 'aries',
                    'preferences': json.dumps({
                        'fortune_types': ['tarot', 'zodiac'],
                        'notification_enabled': True
                    })
                },
                {
                    'name': 'Bob Smith',
                    'birth_date': '1988-05-10',
                    'zodiac_sign': 'taurus',
                    'preferences': json.dumps({
                        'fortune_types': ['daily'],
                        'notification_enabled': False
                    })
                }
            ]
            
            for user in users_data:
                user_obj = User(**user)
                session.add(user_obj)
                results['users_created'] += 1
            
            await session.commit()
            
    except Exception as e:
        error_msg = f"Failed to seed sample data: {e}"
        results['errors'].append(error_msg)
        logger.error(error_msg)
    
    logger.info(f"Sample data seeding completed: {results}")
    return results


async def validate_database_schema() -> Dict[str, Any]:
    """Validate database schema integrity"""
    results = {
        'tables_valid': True,
        'indexes_valid': True,
        'constraints_valid': True,
        'foreign_keys_valid': True,
        'issues': [],
        'table_count': 0,
        'index_count': 0
    }
    
    try:
        async with db_manager.get_session() as session:
            # Check tables
            tables_result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            )
            tables = [row[0] for row in tables_result]
            results['table_count'] = len(tables)
            
            expected_tables = [
                'users', 'chat_sessions', 'chat_messages', 'fortune_sessions',
                'tarot_cards', 'zodiac_info', 'live2d_models', 'content_cache',
                'system_settings', 'user_analytics'
            ]
            
            for table in expected_tables:
                if table not in tables:
                    results['tables_valid'] = False
                    results['issues'].append(f"Missing table: {table}")
            
            # Check indexes
            indexes_result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            )
            indexes = [row[0] for row in indexes_result]
            results['index_count'] = len(indexes)
            
            # Check foreign key constraints
            fk_check = await session.execute(text("PRAGMA foreign_key_check"))
            fk_violations = fk_check.fetchall()
            if fk_violations:
                results['foreign_keys_valid'] = False
                results['issues'].extend([f"Foreign key violation: {row}" for row in fk_violations])
            
            # Check database integrity
            integrity_check = await session.execute(text("PRAGMA integrity_check"))
            integrity_result = integrity_check.scalar()
            if integrity_result != 'ok':
                results['constraints_valid'] = False
                results['issues'].append(f"Integrity check failed: {integrity_result}")
                
    except Exception as e:
        error_msg = f"Schema validation failed: {e}"
        results['issues'].append(error_msg)
        logger.error(error_msg)
    
    results['overall_valid'] = (
        results['tables_valid'] and 
        results['indexes_valid'] and 
        results['constraints_valid'] and 
        results['foreign_keys_valid']
    )
    
    logger.info(f"Database schema validation completed: {results['overall_valid']}")
    return results


async def generate_database_report() -> Dict[str, Any]:
    """Generate comprehensive database report"""
    logger.info("Generating comprehensive database report...")
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'connection_test': {},
        'schema_validation': {},
        'database_stats': {},
        'cache_stats': {},
        'performance_analysis': {},
        'recommendations': []
    }
    
    try:
        # Run all tests and validations
        report['connection_test'] = await test_database_connection()
        report['schema_validation'] = await validate_database_schema()
        report['database_stats'] = await database_service.get_database_stats()
        report['cache_stats'] = cache_service.get_stats()
        report['performance_analysis'] = await database_service.analyze_database()
        
        # Generate recommendations
        if report['database_stats'].get('database_info', {}).get('journal_mode') != 'wal':
            report['recommendations'].append("Enable WAL mode for better concurrency")
        
        if report['cache_stats'].get('hit_rate_percent', 0) < 50:
            report['recommendations'].append("Cache hit rate is low, consider tuning cache TTL")
        
        slow_queries = report['database_stats'].get('query_stats', {}).get('slow_queries', 0)
        if slow_queries > 0:
            report['recommendations'].append(f"Found {slow_queries} slow queries, consider adding indexes")
        
        recommendations = report['performance_analysis'].get('recommendations', [])
        report['recommendations'].extend(recommendations)
        
        # Overall health score
        health_score = 100
        if not report['connection_test'].get('summary', {}).get('success_rate', 0) == 100:
            health_score -= 30
        if not report['schema_validation'].get('overall_valid', False):
            health_score -= 20
        if report['cache_stats'].get('hit_rate_percent', 0) < 50:
            health_score -= 15
        if slow_queries > 5:
            health_score -= 20
        
        report['health_score'] = max(0, health_score)
        report['health_status'] = (
            'excellent' if health_score >= 90 else
            'good' if health_score >= 70 else
            'fair' if health_score >= 50 else
            'poor'
        )
        
    except Exception as e:
        logger.error(f"Failed to generate database report: {e}")
        report['error'] = str(e)
    
    logger.info(f"Database report generated with health score: {report.get('health_score', 0)}")
    return report


# Main test function
async def main():
    """Main test function"""
    logger.info("Starting database validation and testing...")
    
    try:
        # Initialize database
        await db_manager.initialize()
        
        # Run comprehensive tests
        report = await generate_database_report()
        
        # Print summary
        print("\n" + "="*60)
        print("DATABASE VALIDATION REPORT")
        print("="*60)
        print(f"Health Score: {report.get('health_score', 0)}/100 ({report.get('health_status', 'unknown').upper()})")
        print(f"Connection Tests: {report.get('connection_test', {}).get('summary', {}).get('success_rate', 0)}% passed")
        print(f"Schema Valid: {report.get('schema_validation', {}).get('overall_valid', False)}")
        print(f"Cache Hit Rate: {report.get('cache_stats', {}).get('hit_rate_percent', 0)}%")
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*60)
        
        # Optionally seed sample data
        print("\nSeeding sample data...")
        seed_result = await seed_sample_data()
        print(f"Sample data created: {sum(v for k, v in seed_result.items() if k != 'errors' and isinstance(v, int))}")
        
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        print(f"ERROR: {e}")
    
    finally:
        await db_manager.close()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    asyncio.run(main())