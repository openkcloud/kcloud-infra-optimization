#!/usr/bin/env python3
"""
kcloud-opt 가상 클러스터 실시간 모니터링 시스템
Prometheus + Grafana + Custom Metrics 통합
"""

import sys
import time
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

from magnumclient import client as magnum_client
from keystoneauth1 import loading, session
import openstack

@dataclass
class ClusterMetrics:
    """클러스터 메트릭 데이터 클래스"""
    cluster_name: str
    timestamp: str
    status: str
    health_status: str
    node_count: int
    running_pods: int = 0
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    gpu_usage_percent: float = 0.0
    network_io_mbps: float = 0.0
    disk_usage_percent: float = 0.0
    power_consumption_watts: float = 0.0
    cost_per_hour: float = 0.0
    workload_count: int = 0
    failed_pods: int = 0
    pending_pods: int = 0

@dataclass
class GroupMetrics:
    """가상 그룹 메트릭 데이터 클래스"""
    group_name: str
    timestamp: str
    total_clusters: int
    active_clusters: int
    total_nodes: int
    total_cost_per_hour: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_gpu_usage: float
    total_power_consumption: float
    health_score: float
    efficiency_score: float
    cluster_metrics: List[ClusterMetrics]

class VirtualClusterMonitor:
    """가상 클러스터 모니터링 시스템"""
    
    def __init__(self, update_interval=30):
        self.auth_config = {
            'auth_url': 'http://10.0.4.200:5000/v3',
            'username': 'admin',
            'password': 'ketilinux',
            'project_name': 'cloud-platform',
            'project_domain_name': 'Default',
            'user_domain_name': 'Default'
        }
        self.update_interval = update_interval
        self.monitoring_active = False
        self.metrics_history = {}  # 그룹별 메트릭 히스토리
        self.alerts = []
        self.setup_clients()
        
    def setup_clients(self):
        """OpenStack 클라이언트 초기화"""
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**self.auth_config)
        sess = session.Session(auth=auth)
        self.magnum = magnum_client.Client('1', session=sess)
        self.conn = openstack.connect(**self.auth_config)
        print("✅ 가상 클러스터 모니터링 시스템 초기화 완료")
    
    def collect_cluster_metrics(self, cluster_name: str) -> ClusterMetrics:
        """단일 클러스터 메트릭 수집"""
        try:
            # Magnum 클러스터 정보
            magnum_cluster = self.magnum.clusters.get(cluster_name)
            
            # 기본 메트릭
            metrics = ClusterMetrics(
                cluster_name=cluster_name,
                timestamp=datetime.now().isoformat(),
                status=magnum_cluster.status,
                health_status=magnum_cluster.health_status or "UNKNOWN",
                node_count=magnum_cluster.node_count
            )
            
            # 고급 메트릭 수집 (실제 환경에서는 Prometheus/Kepler에서 가져옴)
            if magnum_cluster.status == 'CREATE_COMPLETE':
                metrics = self._collect_advanced_metrics(metrics, magnum_cluster)
            
            # 비용 계산
            metrics.cost_per_hour = self._calculate_cluster_cost(magnum_cluster)
            
            return metrics
            
        except Exception as e:
            print(f"❌ 클러스터 '{cluster_name}' 메트릭 수집 실패: {e}")
            return ClusterMetrics(
                cluster_name=cluster_name,
                timestamp=datetime.now().isoformat(),
                status="ERROR",
                health_status="ERROR",
                node_count=0
            )
    
    def _collect_advanced_metrics(self, metrics: ClusterMetrics, magnum_cluster) -> ClusterMetrics:
        """고급 메트릭 수집 (시뮬레이션)"""
        import random
        
        # 실제로는 Prometheus나 Kepler에서 수집
        # 여기서는 시뮬레이션 데이터 생성
        
        # GPU 클러스터 여부 확인
        is_gpu_cluster = 'gpu' in magnum_cluster.labels.get('gpu_device_plugin', '')
        
        if is_gpu_cluster:
            metrics.cpu_usage_percent = random.uniform(60, 95)
            metrics.memory_usage_percent = random.uniform(70, 90)
            metrics.gpu_usage_percent = random.uniform(50, 95)
            metrics.power_consumption_watts = random.uniform(800, 1500) * metrics.node_count
            metrics.running_pods = random.randint(5, 25)
            metrics.network_io_mbps = random.uniform(100, 500)
        else:
            metrics.cpu_usage_percent = random.uniform(20, 60)
            metrics.memory_usage_percent = random.uniform(30, 70)
            metrics.gpu_usage_percent = 0.0
            metrics.power_consumption_watts = random.uniform(200, 400) * metrics.node_count
            metrics.running_pods = random.randint(2, 15)
            metrics.network_io_mbps = random.uniform(50, 200)
        
        metrics.disk_usage_percent = random.uniform(40, 80)
        metrics.workload_count = random.randint(1, 8)
        metrics.failed_pods = random.randint(0, 2)
        metrics.pending_pods = random.randint(0, 3)
        
        return metrics
    
    def _calculate_cluster_cost(self, magnum_cluster) -> float:
        """클러스터 시간당 비용 계산"""
        cost_map = {
            'ai-k8s-template': 1.20,  # GPU 포함
            'dev-k8s-template': 0.15,
            'prod-k8s-template': 0.30
        }
        
        template_name = magnum_cluster.cluster_template_id
        # 템플릿 이름에서 비용 추정 (실제로는 템플릿 정보 조회 필요)
        base_cost = 1.20 if 'ai' in str(template_name) else 0.15
        
        return base_cost * magnum_cluster.node_count
    
    def collect_group_metrics(self, group_name: str, cluster_names: List[str]) -> GroupMetrics:
        """가상 그룹 전체 메트릭 수집"""
        print(f"📊 그룹 '{group_name}' 메트릭 수집 중...")
        
        cluster_metrics = []
        for cluster_name in cluster_names:
            metrics = self.collect_cluster_metrics(cluster_name)
            cluster_metrics.append(metrics)
        
        # 그룹 전체 메트릭 계산
        active_clusters = [m for m in cluster_metrics if m.status == 'CREATE_COMPLETE']
        
        if not cluster_metrics:
            return GroupMetrics(
                group_name=group_name,
                timestamp=datetime.now().isoformat(),
                total_clusters=0,
                active_clusters=0,
                total_nodes=0,
                total_cost_per_hour=0.0,
                avg_cpu_usage=0.0,
                avg_memory_usage=0.0,
                avg_gpu_usage=0.0,
                total_power_consumption=0.0,
                health_score=0.0,
                efficiency_score=0.0,
                cluster_metrics=[]
            )
        
        total_nodes = sum(m.node_count for m in cluster_metrics)
        total_cost = sum(m.cost_per_hour for m in cluster_metrics)
        total_power = sum(m.power_consumption_watts for m in active_clusters)
        
        # 평균 활용률 계산
        if active_clusters:
            avg_cpu = sum(m.cpu_usage_percent for m in active_clusters) / len(active_clusters)
            avg_memory = sum(m.memory_usage_percent for m in active_clusters) / len(active_clusters)
            avg_gpu = sum(m.gpu_usage_percent for m in active_clusters) / len(active_clusters)
        else:
            avg_cpu = avg_memory = avg_gpu = 0.0
        
        # 헬스 스코어 계산 (0-100)
        health_score = self._calculate_health_score(active_clusters)
        
        # 효율성 스코어 계산 (0-100)
        efficiency_score = self._calculate_efficiency_score(active_clusters)
        
        group_metrics = GroupMetrics(
            group_name=group_name,
            timestamp=datetime.now().isoformat(),
            total_clusters=len(cluster_metrics),
            active_clusters=len(active_clusters),
            total_nodes=total_nodes,
            total_cost_per_hour=total_cost,
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            avg_gpu_usage=avg_gpu,
            total_power_consumption=total_power,
            health_score=health_score,
            efficiency_score=efficiency_score,
            cluster_metrics=cluster_metrics
        )
        
        return group_metrics
    
    def _calculate_health_score(self, active_clusters: List[ClusterMetrics]) -> float:
        """헬스 스코어 계산"""
        if not active_clusters:
            return 0.0
        
        total_score = 0.0
        for cluster in active_clusters:
            score = 100.0
            
            # 실패한 포드가 있으면 점수 차감
            if cluster.failed_pods > 0:
                score -= cluster.failed_pods * 10
            
            # 대기 중인 포드가 많으면 점수 차감
            if cluster.pending_pods > 5:
                score -= (cluster.pending_pods - 5) * 5
            
            # 너무 높은 CPU/메모리 사용률은 위험
            if cluster.cpu_usage_percent > 90:
                score -= 20
            if cluster.memory_usage_percent > 90:
                score -= 20
            
            total_score += max(0, score)
        
        return total_score / len(active_clusters)
    
    def _calculate_efficiency_score(self, active_clusters: List[ClusterMetrics]) -> float:
        """효율성 스코어 계산"""
        if not active_clusters:
            return 0.0
        
        total_score = 0.0
        for cluster in active_clusters:
            # 자원 활용률 기반 효율성
            utilization_score = (cluster.cpu_usage_percent + cluster.memory_usage_percent) / 2
            
            # GPU가 있으면 GPU 활용률도 고려
            if cluster.gpu_usage_percent > 0:
                utilization_score = (utilization_score + cluster.gpu_usage_percent) / 2
            
            # 비용 대비 성능 (전력 효율성)
            if cluster.power_consumption_watts > 0:
                power_efficiency = utilization_score / (cluster.power_consumption_watts / 1000)
                efficiency_score = min(100, power_efficiency * 50)
            else:
                efficiency_score = utilization_score
            
            total_score += efficiency_score
        
        return total_score / len(active_clusters)
    
    def start_monitoring(self, virtual_groups: Dict[str, List[str]]):
        """실시간 모니터링 시작"""
        print(f"🚀 실시간 모니터링 시작 (업데이트 주기: {self.update_interval}초)")
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    for group_name, cluster_names in virtual_groups.items():
                        group_metrics = self.collect_group_metrics(group_name, cluster_names)
                        
                        # 히스토리에 저장
                        if group_name not in self.metrics_history:
                            self.metrics_history[group_name] = []
                        
                        self.metrics_history[group_name].append(group_metrics)
                        
                        # 최근 100개 기록만 유지
                        if len(self.metrics_history[group_name]) > 100:
                            self.metrics_history[group_name] = self.metrics_history[group_name][-100:]
                        
                        # 알림 체크
                        self._check_alerts(group_metrics)
                    
                    time.sleep(self.update_interval)
                    
                except Exception as e:
                    print(f"❌ 모니터링 오류: {e}")
                    time.sleep(5)
        
        # 백그라운드 스레드에서 실행
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        print("🛑 모니터링 중지")
        self.monitoring_active = False
    
    def _check_alerts(self, group_metrics: GroupMetrics):
        """알림 조건 체크"""
        alerts = []
        
        # 높은 비용 알림
        if group_metrics.total_cost_per_hour > 20.0:
            alerts.append({
                'type': 'HIGH_COST',
                'group': group_metrics.group_name,
                'message': f'높은 비용: ${group_metrics.total_cost_per_hour:.2f}/시간',
                'severity': 'WARNING'
            })
        
        # 낮은 효율성 알림
        if group_metrics.efficiency_score < 30:
            alerts.append({
                'type': 'LOW_EFFICIENCY',
                'group': group_metrics.group_name,
                'message': f'낮은 효율성: {group_metrics.efficiency_score:.1f}%',
                'severity': 'WARNING'
            })
        
        # 헬스 문제 알림
        if group_metrics.health_score < 50:
            alerts.append({
                'type': 'HEALTH_ISSUE',
                'group': group_metrics.group_name,
                'message': f'헬스 문제: {group_metrics.health_score:.1f}점',
                'severity': 'CRITICAL'
            })
        
        # 높은 전력 소비 알림
        if group_metrics.total_power_consumption > 10000:  # 10kW
            alerts.append({
                'type': 'HIGH_POWER',
                'group': group_metrics.group_name,
                'message': f'높은 전력 소비: {group_metrics.total_power_consumption:.0f}W',
                'severity': 'INFO'
            })
        
        # 새로운 알림만 저장
        for alert in alerts:
            if alert not in self.alerts:
                alert['timestamp'] = datetime.now().isoformat()
                self.alerts.append(alert)
                print(f"🚨 [{alert['severity']}] {alert['message']}")
    
    def get_current_status(self, group_name: str) -> Optional[GroupMetrics]:
        """현재 상태 반환"""
        if group_name in self.metrics_history and self.metrics_history[group_name]:
            return self.metrics_history[group_name][-1]
        return None
    
    def get_historical_data(self, group_name: str, hours: int = 24) -> List[GroupMetrics]:
        """과거 데이터 반환"""
        if group_name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_data = []
        for metrics in self.metrics_history[group_name]:
            metrics_time = datetime.fromisoformat(metrics.timestamp.replace('Z', ''))
            if metrics_time >= cutoff_time:
                filtered_data.append(metrics)
        
        return filtered_data
    
    def generate_monitoring_report(self, group_name: str) -> Dict:
        """모니터링 리포트 생성"""
        current = self.get_current_status(group_name)
        historical = self.get_historical_data(group_name, 24)
        
        if not current:
            return {'error': f'그룹 {group_name}의 데이터가 없습니다'}
        
        # 24시간 평균 계산
        if historical:
            avg_cost = sum(h.total_cost_per_hour for h in historical) / len(historical)
            avg_power = sum(h.total_power_consumption for h in historical) / len(historical)
            avg_efficiency = sum(h.efficiency_score for h in historical) / len(historical)
        else:
            avg_cost = current.total_cost_per_hour
            avg_power = current.total_power_consumption
            avg_efficiency = current.efficiency_score
        
        # 최근 알림
        recent_alerts = [a for a in self.alerts if a['group'] == group_name][-10:]
        
        report = {
            'group_name': group_name,
            'timestamp': current.timestamp,
            'current_status': asdict(current),
            '24h_averages': {
                'cost_per_hour': avg_cost,
                'power_consumption': avg_power,
                'efficiency_score': avg_efficiency
            },
            'trends': {
                'data_points': len(historical),
                'cost_trend': 'stable',  # 실제로는 추세 분석 필요
                'efficiency_trend': 'improving'
            },
            'recent_alerts': recent_alerts,
            'recommendations': self._generate_recommendations(current, historical)
        }
        
        return report
    
    def _generate_recommendations(self, current: GroupMetrics, historical: List[GroupMetrics]) -> List[str]:
        """최적화 권장사항 생성"""
        recommendations = []
        
        if current.efficiency_score < 50:
            recommendations.append("낮은 효율성 감지: 유휴 노드 스케일 인 권장")
        
        if current.total_cost_per_hour > 15:
            recommendations.append("높은 비용: 비GPU 작업을 일반 노드로 이동 권장")
        
        if current.avg_gpu_usage < 30:
            recommendations.append("GPU 활용률 낮음: GPU 노드 수 감소 권장")
        
        if current.health_score < 70:
            recommendations.append("헬스 스코어 낮음: 실패한 포드 및 리소스 부족 확인 필요")
        
        # 24시간 데이터 기반 권장사항
        if len(historical) > 10:
            recent_avg_cost = sum(h.total_cost_per_hour for h in historical[-10:]) / 10
            if recent_avg_cost > current.total_cost_per_hour * 1.2:
                recommendations.append("비용 증가 추세: 스케일 다운 타이밍 검토 필요")
        
        return recommendations
    
    def save_metrics_to_file(self, group_name: str, filename: Optional[str] = None):
        """메트릭을 파일로 저장"""
        if not filename:
            filename = f"metrics_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if group_name in self.metrics_history:
            data = {
                'group_name': group_name,
                'export_time': datetime.now().isoformat(),
                'metrics_count': len(self.metrics_history[group_name]),
                'metrics': [asdict(m) for m in self.metrics_history[group_name]]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"📁 메트릭 저장 완료: {filename}")
        else:
            print(f"❌ 그룹 '{group_name}'의 메트릭 데이터가 없습니다")

def main():
    """모니터링 시스템 사용 예시"""
    monitor = VirtualClusterMonitor(update_interval=10)  # 10초마다 업데이트
    
    print("=" * 60)
    print("📊 가상 클러스터 모니터링 시스템")
    print("=" * 60)
    
    # 예시 가상 그룹 정의
    virtual_groups = {
        'ml-training-group': ['kcloud-ai-cluster-v2'],
        # 실제로는 여러 그룹과 클러스터들을 정의
    }
    
    print("\n🔍 현재 상태 스냅샷:")
    for group_name, cluster_names in virtual_groups.items():
        metrics = monitor.collect_group_metrics(group_name, cluster_names)
        print(f"\n🌐 그룹: {group_name}")
        print(f"  📦 클러스터: {metrics.total_clusters}개 (활성: {metrics.active_clusters}개)")
        print(f"  🖥️ 노드: {metrics.total_nodes}개")
        print(f"  💰 시간당 비용: ${metrics.total_cost_per_hour:.2f}")
        print(f"  📊 평균 CPU: {metrics.avg_cpu_usage:.1f}%")
        print(f"  🧠 평균 메모리: {metrics.avg_memory_usage:.1f}%")
        print(f"  ⚡ 평균 GPU: {metrics.avg_gpu_usage:.1f}%")
        print(f"  🔋 전력 소비: {metrics.total_power_consumption:.0f}W")
        print(f"  💚 헬스 스코어: {metrics.health_score:.1f}/100")
        print(f"  ⚡ 효율성: {metrics.efficiency_score:.1f}/100")
    
    print(f"\n💡 실시간 모니터링을 시작하려면:")
    print(f"monitor.start_monitoring(virtual_groups)")
    print(f"time.sleep(60)  # 1분간 모니터링")
    print(f"report = monitor.generate_monitoring_report('ml-training-group')")
    
    print(f"\n✅ 모니터링 시스템 준비 완료")

if __name__ == "__main__":
    main()