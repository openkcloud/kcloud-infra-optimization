#!/usr/bin/env python3
"""
kcloud-opt 데이터베이스 연결 관리
PostgreSQL + TimescaleDB + Redis 통합 관리자
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

# 패키지 경로 추가
sys.path.insert(0, '/root/kcloud_opt')

import asyncpg
import redis.asyncio as aioredis
from asyncpg import Pool
from redis.asyncio import Redis

# 설정 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """데이터베이스 설정 관리"""
    
    def __init__(self):
        # PostgreSQL/TimescaleDB 설정
        self.postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
        self.postgres_port = int(os.getenv('POSTGRES_PORT', 5432))
        self.postgres_db = os.getenv('POSTGRES_DB', 'kcloud_opt')
        self.postgres_user = os.getenv('POSTGRES_USER', 'kcloud_user')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'kcloud123')
        
        # Redis 설정
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        
        # 연결 풀 설정
        self.postgres_min_connections = int(os.getenv('POSTGRES_MIN_CONN', 10))
        self.postgres_max_connections = int(os.getenv('POSTGRES_MAX_CONN', 50))
        
        # 타임아웃 설정
        self.connection_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', 30))
        self.query_timeout = int(os.getenv('DB_QUERY_TIMEOUT', 60))
    
    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL DSN 생성"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Redis URL 생성"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


class DatabaseManager:
    """통합 데이터베이스 연결 관리자"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.postgres_pool: Optional[Pool] = None
        self.redis_client: Optional[Redis] = None
        self._connected = False
    
    async def connect(self):
        """데이터베이스 연결"""
        try:
            logger.info("🔌 데이터베이스 연결 시작...")
            
            # PostgreSQL 연결 풀 생성
            await self._connect_postgres()
            
            # Redis 연결
            await self._connect_redis()
            
            # 연결 상태 확인
            await self._verify_connections()
            
            self._connected = True
            logger.info("✅ 데이터베이스 연결 완료")
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            await self.disconnect()
            raise
    
    async def _connect_postgres(self):
        """PostgreSQL 연결 풀 생성"""
        try:
            self.postgres_pool = await asyncpg.create_pool(
                self.config.postgres_dsn,
                min_size=self.config.postgres_min_connections,
                max_size=self.config.postgres_max_connections,
                command_timeout=self.config.query_timeout,
                server_settings={
                    'application_name': 'kcloud-opt',
                    'search_path': 'public',
                }
            )
            logger.info(f"📊 PostgreSQL 연결 풀 생성: {self.config.postgres_host}:{self.config.postgres_port}")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL 연결 실패: {e}")
            raise
    
    async def _connect_redis(self):
        """Redis 연결"""
        try:
            self.redis_client = aioredis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_timeout=self.config.connection_timeout,
                socket_connect_timeout=self.config.connection_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 연결 테스트
            await self.redis_client.ping()
            logger.info(f"🔴 Redis 연결 완료: {self.config.redis_host}:{self.config.redis_port}")
            
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            raise
    
    async def _verify_connections(self):
        """연결 상태 확인"""
        try:
            # PostgreSQL 테스트
            async with self.postgres_pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"📊 PostgreSQL 버전: {version.split(',')[0]}")
                
                # TimescaleDB 확장 확인
                timescale = await conn.fetchval(
                    "SELECT installed_version FROM pg_available_extensions WHERE name = 'timescaledb'"
                )
                if timescale:
                    logger.info(f"⏰ TimescaleDB 버전: {timescale}")
                else:
                    logger.warning("⚠️ TimescaleDB 확장이 설치되지 않음")
            
            # Redis 테스트
            redis_info = await self.redis_client.info()
            logger.info(f"🔴 Redis 버전: {redis_info['redis_version']}")
            logger.info(f"🔴 Redis 메모리: {redis_info['used_memory_human']}")
            
        except Exception as e:
            logger.error(f"❌ 연결 확인 실패: {e}")
            raise
    
    async def disconnect(self):
        """데이터베이스 연결 해제"""
        logger.info("🔌 데이터베이스 연결 해제 중...")
        
        # PostgreSQL 연결 풀 닫기
        if self.postgres_pool:
            await self.postgres_pool.close()
            self.postgres_pool = None
        
        # Redis 연결 닫기
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        
        self._connected = False
        logger.info("✅ 데이터베이스 연결 해제 완료")
    
    @asynccontextmanager
    async def postgres_transaction(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """PostgreSQL 트랜잭션 컨텍스트 매니저"""
        if not self._connected:
            raise RuntimeError("데이터베이스가 연결되지 않음")
        
        async with self.postgres_pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    @asynccontextmanager
    async def postgres_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """PostgreSQL 연결 컨텍스트 매니저"""
        if not self._connected:
            raise RuntimeError("데이터베이스가 연결되지 않음")
        
        async with self.postgres_pool.acquire() as conn:
            yield conn
    
    async def execute_query(self, query: str, *args, **kwargs) -> Any:
        """PostgreSQL 쿼리 실행"""
        async with self.postgres_connection() as conn:
            if kwargs.get('fetch', 'all') == 'one':
                return await conn.fetchrow(query, *args)
            elif kwargs.get('fetch') == 'val':
                return await conn.fetchval(query, *args)
            elif kwargs.get('fetch') == 'all':
                return await conn.fetch(query, *args)
            else:
                return await conn.execute(query, *args)
    
    async def redis_get(self, key: str, default=None) -> Any:
        """Redis GET 작업"""
        if not self._connected:
            raise RuntimeError("Redis가 연결되지 않음")
        
        try:
            value = await self.redis_client.get(key)
            return value if value is not None else default
        except Exception as e:
            logger.error(f"Redis GET 오류 ({key}): {e}")
            return default
    
    async def redis_set(self, key: str, value: str, expire: int = None) -> bool:
        """Redis SET 작업"""
        if not self._connected:
            raise RuntimeError("Redis가 연결되지 않음")
        
        try:
            result = await self.redis_client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET 오류 ({key}): {e}")
            return False
    
    async def redis_delete(self, *keys: str) -> int:
        """Redis DELETE 작업"""
        if not self._connected:
            raise RuntimeError("Redis가 연결되지 않음")
        
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE 오류: {e}")
            return 0
    
    async def redis_publish(self, channel: str, message: str) -> int:
        """Redis PUBLISH 작업"""
        if not self._connected:
            raise RuntimeError("Redis가 연결되지 않음")
        
        try:
            return await self.redis_client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis PUBLISH 오류 ({channel}): {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """데이터베이스 상태 확인"""
        status = {
            'connected': self._connected,
            'postgres': False,
            'redis': False,
            'timestamp': datetime.now().isoformat()
        }
        
        if not self._connected:
            return status
        
        try:
            # PostgreSQL 상태 확인
            async with self.postgres_connection() as conn:
                await conn.fetchval("SELECT 1")
                status['postgres'] = True
        except Exception as e:
            logger.error(f"PostgreSQL 상태 확인 실패: {e}")
        
        try:
            # Redis 상태 확인
            await self.redis_client.ping()
            status['redis'] = True
        except Exception as e:
            logger.error(f"Redis 상태 확인 실패: {e}")
        
        return status
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 반환"""
        return self._connected


# 글로벌 데이터베이스 관리자 인스턴스
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """데이터베이스 관리자 싱글톤 반환"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

async def init_database():
    """데이터베이스 초기화"""
    db_manager = get_database_manager()
    await db_manager.connect()
    return db_manager

async def close_database():
    """데이터베이스 연결 해제"""
    global _db_manager
    if _db_manager:
        await _db_manager.disconnect()
        _db_manager = None


# 컨텍스트 매니저로 사용할 수 있는 헬퍼
@asynccontextmanager
async def database_context():
    """데이터베이스 컨텍스트 매니저"""
    db_manager = None
    try:
        db_manager = await init_database()
        yield db_manager
    finally:
        if db_manager:
            await db_manager.disconnect()


if __name__ == "__main__":
    async def test_connection():
        """연결 테스트"""
        print("🧪 데이터베이스 연결 테스트")
        print("=" * 40)
        
        async with database_context() as db:
            # 상태 확인
            health = await db.health_check()
            print(f"📊 연결 상태: {health}")
            
            # PostgreSQL 테스트
            try:
                tables = await db.execute_query(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                print(f"📊 테이블 수: {len(tables)}")
                for table in tables[:5]:  # 처음 5개만
                    print(f"  - {table['table_name']}")
            except Exception as e:
                print(f"❌ PostgreSQL 테스트 실패: {e}")
            
            # Redis 테스트
            try:
                await db.redis_set("test:connection", "success", 60)
                value = await db.redis_get("test:connection")
                print(f"🔴 Redis 테스트: {value}")
                await db.redis_delete("test:connection")
            except Exception as e:
                print(f"❌ Redis 테스트 실패: {e}")
    
    # 테스트 실행
    asyncio.run(test_connection())