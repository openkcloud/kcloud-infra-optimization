#!/usr/bin/env python3
"""
kcloud-opt 향상된 메트릭 수집기
PostgreSQL + TimescaleDB + Redis 통합
"""

import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# 경로 설정
sys.path.insert(0, '/root/kcloud_opt')

# 기존 모니터링 시스템 임포트
from infrastructure.monitoring.metrics_collector import MetricsCollector as BaseMetricsCollector, ClusterMetrics
from infrastructure.database.connection import get_database_manager, DatabaseManager
from infrastructure.database.redis_keys import RedisKeys, RedisPubSubChannels, RedisDataTypes, RedisExpirePolicy

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedClusterMetrics(ClusterMetrics):
    """향상된 클러스터 메트릭 (DB 통합)"""
    
    # 추가 메타데이터
    cluster_id: Optional[str] = None
    collection_id: Optional[str] = None
    data_source: str = "openstack_magnum"
    processing_time_ms: float = 0.0
    
    def to_db_dict(self) -> Dict[str, Any]:
        """데이터베이스 저장용 딕셔너리 변환"""
        db_data = asdict(self)
        
        # 데이터베이스 컬럼과 매핑
        db_data['time'] = datetime.now()
        
        # JSON 필드 처리
        db_data['metadata'] = {
            'collection_id': self.collection_id,
            'data_source': self.data_source,
            'processing_time_ms': self.processing_time_ms,
            'openstack_uuid': db_data.get('uuid'),
            'template_info': {
                'template_id': self.template_id,
                'api_address': self.api_address
            }
        }
        
        # 불필요한 필드 제거
        for field in ['uuid', 'collection_id', 'data_source', 'processing_time_ms']:
            db_data.pop(field, None)
        
        return db_data

class EnhancedMetricsCollector:
    """데이터베이스 통합 메트릭 수집기"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.base_collector = BaseMetricsCollector()
        self.db_manager = db_manager or get_database_manager()
        self.collection_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def collect_and_store_metrics(self, cluster_name: str) -> EnhancedClusterMetrics:
        """메트릭 수집 및 저장"""
        start_time = datetime.now()
        
        try:
            # 기존 수집기로 메트릭 수집
            base_metrics = self.base_collector.collect_full_metrics(cluster_name)
            
            # 향상된 메트릭으로 변환
            enhanced_metrics = self._enhance_metrics(base_metrics)
            enhanced_metrics.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # 데이터베이스에 저장
            if self.db_manager.is_connected:
                await self._store_to_database(enhanced_metrics)
                await self._update_redis_cache(enhanced_metrics)
                await self._publish_metrics_update(enhanced_metrics)
            else:
                logger.warning("데이터베이스 연결 없음 - 메모리에만 저장")
            
            return enhanced_metrics
            
        except Exception as e:
            logger.error(f"메트릭 수집/저장 실패 ({cluster_name}): {e}")
            # 오류 시 기본 메트릭 반환
            return self._create_error_metrics(cluster_name, str(e))
    
    def _enhance_metrics(self, base_metrics: ClusterMetrics) -> EnhancedClusterMetrics:
        """기본 메트릭을 향상된 메트릭으로 변환"""
        enhanced = EnhancedClusterMetrics(**asdict(base_metrics))
        enhanced.collection_id = f"{self.collection_session_id}_{base_metrics.cluster_name}"
        return enhanced
    
    async def _store_to_database(self, metrics: EnhancedClusterMetrics):
        """TimescaleDB에 메트릭 저장"""
        try:
            db_data = metrics.to_db_dict()
            
            # 클러스터 ID 조회/생성
            cluster_id = await self._ensure_cluster_exists(metrics.cluster_name, metrics.template_id)
            db_data['cluster_id'] = cluster_id
            
            # TimescaleDB에 삽입
            insert_query = """
            INSERT INTO cluster_metrics (
                time, cluster_name, cluster_id, status, health_status,
                node_count, master_count, cpu_usage, memory_usage, gpu_usage,
                disk_usage, network_io_mbps, running_pods, failed_pods, pending_pods,
                workload_count, power_consumption_watts, cost_per_hour, 
                estimated_monthly_cost, health_score, efficiency_score, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                $16, $17, $18, $19, $20, $21, $22
            )
            """
            
            await self.db_manager.execute_query(
                insert_query,
                db_data['time'], db_data['cluster_name'], db_data['cluster_id'],
                db_data['status'], db_data['health_status'], db_data['node_count'],
                db_data['master_count'], db_data['cpu_usage'], db_data['memory_usage'],
                db_data['gpu_usage'], db_data['disk_usage'], db_data['network_io_mbps'],
                db_data['running_pods'], db_data['failed_pods'], db_data['pending_pods'],
                db_data['workload_count'], db_data['power_consumption_watts'],
                db_data['cost_per_hour'], db_data['estimated_monthly_cost'],
                db_data['health_score'], db_data['efficiency_score'],
                json.dumps(db_data['metadata'])
            )
            
            logger.debug(f"메트릭 DB 저장 완료: {metrics.cluster_name}")
            
        except Exception as e:
            logger.error(f"메트릭 DB 저장 실패: {e}")
            raise
    
    async def _ensure_cluster_exists(self, cluster_name: str, template_id: str) -> str:
        """클러스터 정보 확인/생성"""
        try:
            # 기존 클러스터 조회
            cluster = await self.db_manager.execute_query(
                "SELECT id FROM clusters WHERE name = $1",
                cluster_name, fetch='one'
            )
            
            if cluster:
                return str(cluster['id'])
            
            # 새 클러스터 생성
            cluster_id = await self.db_manager.execute_query(
                """
                INSERT INTO clusters (name, template_id, project_id, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                cluster_name, template_id, "a6ce5f91a73544c09414fdcae43a129f", "UNKNOWN",
                fetch='val'
            )
            
            logger.info(f"새 클러스터 등록: {cluster_name}")
            return str(cluster_id)
            
        except Exception as e:
            logger.error(f"클러스터 확인/생성 실패: {e}")
            return "unknown"
    
    async def _update_redis_cache(self, metrics: EnhancedClusterMetrics):
        """Redis 캐시 업데이트"""
        try:
            # 최신 메트릭 캐시
            metrics_data = RedisDataTypes.serialize_cluster_metrics(asdict(metrics))
            await self.db_manager.redis_set(
                RedisKeys.metrics_latest(metrics.cluster_name),
                metrics_data,
                RedisExpirePolicy.METRICS_LATEST
            )
            
            # 클러스터 현재 상태 캐시
            current_status = {
                'cluster_name': metrics.cluster_name,
                'status': metrics.status,
                'health_score': metrics.health_score,
                'cost_per_hour': metrics.cost_per_hour,
                'last_update': datetime.now().isoformat()
            }
            await self.db_manager.redis_set(
                RedisKeys.cluster_current(metrics.cluster_name),
                json.dumps(current_status),
                RedisExpirePolicy.CLUSTER_CURRENT
            )
            
            # 메트릭 히스토리 (List에 추가)
            history_key = RedisKeys.metrics_history(metrics.cluster_name, "1h")
            await self.db_manager.redis_client.lpush(history_key, metrics_data)
            await self.db_manager.redis_client.ltrim(history_key, 0, 240)  # 최근 240개 유지 (1시간)
            await self.db_manager.redis_client.expire(history_key, RedisExpirePolicy.METRICS_HISTORY)
            
            # 활성 클러스터 목록 업데이트
            await self.db_manager.redis_client.sadd(RedisKeys.cluster_list(), metrics.cluster_name)
            
            logger.debug(f"Redis 캐시 업데이트 완료: {metrics.cluster_name}")
            
        except Exception as e:
            logger.error(f"Redis 캐시 업데이트 실패: {e}")
    
    async def _publish_metrics_update(self, metrics: EnhancedClusterMetrics):
        """메트릭 업데이트 이벤트 발행"""
        try:
            update_message = {
                'cluster_name': metrics.cluster_name,
                'status': metrics.status,
                'health_score': metrics.health_score,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'metrics_updated'
            }
            
            # 전역 메트릭 업데이트 채널
            await self.db_manager.redis_publish(
                RedisPubSubChannels.METRICS_UPDATED,
                json.dumps(update_message)
            )
            
            # 클러스터별 채널 (패턴 매칭용)
            cluster_channel = f"kcloud:events:cluster:{metrics.cluster_name}:metrics"
            await self.db_manager.redis_publish(cluster_channel, json.dumps(update_message))
            
        except Exception as e:
            logger.error(f"메트릭 업데이트 발행 실패: {e}")
    
    def _create_error_metrics(self, cluster_name: str, error_msg: str) -> EnhancedClusterMetrics:
        """오류 시 기본 메트릭 생성"""
        return EnhancedClusterMetrics(
            cluster_name=cluster_name,
            timestamp=datetime.now().isoformat(),
            status="ERROR",
            health_status="ERROR",
            node_count=0,
            master_count=0,
            template_id="unknown",
            health_score=0.0,
            efficiency_score=0.0,
            collection_id=f"error_{datetime.now().strftime('%H%M%S')}",
            data_source="error_handler",
            processing_time_ms=0.0
        )
    
    async def collect_multiple_clusters_async(self, cluster_names: List[str]) -> List[EnhancedClusterMetrics]:
        """비동기 다중 클러스터 메트릭 수집"""
        logger.info(f"비동기 다중 클러스터 메트릭 수집: {len(cluster_names)}개")
        
        # 동시 수집
        tasks = [self.collect_and_store_metrics(name) for name in cluster_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics_list = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"클러스터 '{cluster_names[i]}' 수집 실패: {result}")
                metrics_list.append(self._create_error_metrics(cluster_names[i], str(result)))
            else:
                metrics_list.append(result)
        
        logger.info(f"다중 클러스터 수집 완료: {len(metrics_list)}/{len(cluster_names)}")
        return metrics_list
    
    async def get_metrics_from_cache(self, cluster_name: str) -> Optional[Dict[str, Any]]:
        """Redis에서 메트릭 조회"""
        try:
            cached_data = await self.db_manager.redis_get(RedisKeys.metrics_latest(cluster_name))
            if cached_data:
                return RedisDataTypes.deserialize_cluster_metrics(cached_data)
            return None
        except Exception as e:
            logger.error(f"메트릭 캐시 조회 실패: {e}")
            return None
    
    async def get_metrics_history(self, cluster_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """메트릭 히스토리 조회 (Redis + DB 하이브리드)"""
        try:
            # Redis에서 최근 1시간
            if hours <= 1:
                history_data = await self.db_manager.redis_client.lrange(
                    RedisKeys.metrics_history(cluster_name, "1h"), 0, -1
                )
                return [RedisDataTypes.deserialize_cluster_metrics(data) for data in history_data]
            
            # DB에서 장기 히스토리
            since_time = datetime.now() - timedelta(hours=hours)
            history = await self.db_manager.execute_query(
                """
                SELECT * FROM cluster_metrics 
                WHERE cluster_name = $1 AND time >= $2 
                ORDER BY time DESC
                LIMIT 1000
                """,
                cluster_name, since_time
            )
            
            return [dict(row) for row in history]
            
        except Exception as e:
            logger.error(f"메트릭 히스토리 조회 실패: {e}")
            return []


async def test_enhanced_collector():
    """향상된 수집기 테스트"""
    print("🚀 향상된 메트릭 수집기 테스트")
    print("=" * 50)
    
    try:
        # 데이터베이스 연결 (시뮬레이션)
        collector = EnhancedMetricsCollector()
        
        # 단일 클러스터 수집 (기존 방식으로 폴백)
        cluster_name = "kcloud-dev-cluster"
        print(f"\n📊 단일 클러스터 메트릭 수집: {cluster_name}")
        
        # 기존 수집기 사용 (DB 연결 없이)
        base_metrics = collector.base_collector.collect_full_metrics(cluster_name)
        enhanced = collector._enhance_metrics(base_metrics)
        
        print(f"✅ 수집 완료:")
        print(f"  클러스터: {enhanced.cluster_name}")
        print(f"  상태: {enhanced.status}")
        print(f"  비용: ${enhanced.cost_per_hour:.2f}/시간")
        print(f"  헬스: {enhanced.health_score:.1f}/100")
        print(f"  수집 ID: {enhanced.collection_id}")
        
        # 다중 클러스터 테스트 준비
        print(f"\n📊 다중 클러스터 수집 준비 완료")
        print(f"  수집기 세션: {collector.collection_session_id}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_collector())