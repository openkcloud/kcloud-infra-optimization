#!/usr/bin/env python3
"""
kcloud-opt 클러스터 관리 예시 코드
개발자가 참고할 수 있는 실제 구현 예시
"""

import sys
import time
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

from magnumclient import client as magnum_client
from keystoneauth1 import loading, session
import openstack

class KCloudClusterManager:
    """kcloud-opt 클러스터 관리 클래스"""
    
    def __init__(self):
        self.auth_config = {
            'auth_url': 'http://10.0.4.200:5000/v3',
            'username': 'admin',
            'password': 'ketilinux',
            'project_name': 'cloud-platform',
            'project_domain_name': 'Default',
            'user_domain_name': 'Default'
        }
        self.setup_clients()
    
    def setup_clients(self):
        """OpenStack 클라이언트 초기화"""
        # Magnum 클라이언트
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**self.auth_config)
        sess = session.Session(auth=auth)
        self.magnum = magnum_client.Client('1', session=sess)
        
        # OpenStack SDK
        self.conn = openstack.connect(**self.auth_config)
        print("✅ OpenStack 클라이언트 초기화 완료")
    
    def create_cluster(self, name, workload_type="general", node_count=2):
        """
        워크로드 타입에 따른 최적화된 클러스터 생성
        
        Args:
            name: 클러스터 이름
            workload_type: "ml_training", "ai_inference", "general"
            node_count: 워커 노드 수
        """
        print(f"🚀 클러스터 생성 시작: {name} ({workload_type})")
        
        # 워크로드 타입별 설정
        cluster_configs = {
            "ml_training": {
                "template": "ai-k8s-template",
                "master_flavor": "m1.large",
                "labels": {
                    "gpu_device_plugin": "true",
                    "auto_scaling_enabled": "true",
                    "workload_type": "training"
                }
            },
            "ai_inference": {
                "template": "ai-k8s-template", 
                "master_flavor": "m1.medium",
                "labels": {
                    "gpu_device_plugin": "true",
                    "workload_type": "inference"
                }
            },
            "general": {
                "template": "dev-k8s-template",
                "master_flavor": "m1.small",
                "labels": {}
            }
        }
        
        config = cluster_configs.get(workload_type, cluster_configs["general"])
        
        cluster_spec = {
            'name': name,
            'cluster_template_id': config["template"],
            'keypair': 'kcloud-keypair',
            'master_count': 1,
            'node_count': node_count,
            'fixed_network': 'cloud-platform-selfservice',
            'fixed_subnet': 'cloud-platform-selfservice-subnet',
            'labels': config["labels"]
        }
        
        try:
            cluster = self.magnum.clusters.create(**cluster_spec)
            print(f"✅ 클러스터 생성 요청 완료: {cluster.uuid}")
            return cluster
        except Exception as e:
            print(f"❌ 클러스터 생성 실패: {e}")
            return None
    
    def wait_for_cluster(self, cluster_name, timeout=1800):
        """클러스터 생성 완료까지 대기 (최대 30분)"""
        print(f"⏳ 클러스터 '{cluster_name}' 생성 완료 대기 중...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                cluster = self.magnum.clusters.get(cluster_name)
                status = cluster.status
                
                print(f"📊 현재 상태: {status}")
                
                if status == 'CREATE_COMPLETE':
                    print(f"🎉 클러스터 '{cluster_name}' 생성 완료!")
                    return cluster
                elif status == 'CREATE_FAILED':
                    print(f"❌ 클러스터 '{cluster_name}' 생성 실패")
                    print(f"실패 원인: {cluster.status_reason}")
                    return None
                
                time.sleep(30)  # 30초 대기
                
            except Exception as e:
                print(f"상태 확인 중 오류: {e}")
                time.sleep(30)
        
        print(f"⏰ 타임아웃: 클러스터 생성이 {timeout/60}분 내에 완료되지 않음")
        return None
    
    def scale_cluster(self, cluster_name, new_node_count):
        """클러스터 노드 수 변경"""
        try:
            cluster = self.magnum.clusters.get(cluster_name)
            
            # PATCH 방식으로 노드 수 변경
            update_ops = [
                {
                    'op': 'replace',
                    'path': '/node_count', 
                    'value': new_node_count
                }
            ]
            
            updated_cluster = self.magnum.clusters.update(cluster.uuid, update_ops)
            print(f"✅ 클러스터 '{cluster_name}' 스케일링: {cluster.node_count} → {new_node_count}")
            return updated_cluster
            
        except Exception as e:
            print(f"❌ 스케일링 실패: {e}")
            return None
    
    def get_cluster_status(self, cluster_name):
        """클러스터 상태 정보 반환"""
        try:
            cluster = self.magnum.clusters.get(cluster_name)
            
            status_info = {
                'name': cluster.name,
                'status': cluster.status,
                'health_status': cluster.health_status,
                'node_count': cluster.node_count,
                'master_count': cluster.master_count,
                'api_address': cluster.api_address,
                'template': cluster.cluster_template_id
            }
            
            return status_info
        except Exception as e:
            print(f"❌ 상태 조회 실패: {e}")
            return None
    
    def list_clusters(self):
        """모든 클러스터 목록 반환"""
        try:
            clusters = list(self.magnum.clusters.list())
            
            print(f"📊 총 클러스터 수: {len(clusters)}")
            for cluster in clusters:
                print(f"  🔸 {cluster.name}: {cluster.status} (노드: {cluster.node_count})")
            
            return clusters
        except Exception as e:
            print(f"❌ 목록 조회 실패: {e}")
            return []
    
    def delete_cluster(self, cluster_name):
        """클러스터 삭제"""
        try:
            cluster = self.magnum.clusters.get(cluster_name)
            self.magnum.clusters.delete(cluster.uuid)
            print(f"✅ 클러스터 '{cluster_name}' 삭제 요청 완료")
            return True
        except Exception as e:
            print(f"❌ 삭제 실패: {e}")
            return False
    
    def get_cluster_cost_estimate(self, cluster_name):
        """클러스터 예상 비용 계산"""
        cluster_info = self.get_cluster_status(cluster_name)
        if not cluster_info:
            return None
        
        # Flavor 기반 비용 계산 (예시)
        cost_map = {
            'm1.small': 0.05,
            'm1.medium': 0.10, 
            'm1.large': 0.20,
            'g1.small': 0.50,
            'g1.large': 1.00
        }
        
        # 마스터 + 워커 노드 비용
        master_cost = cost_map.get('m1.large', 0.20)  # AI 템플릿은 m1.large 마스터
        worker_cost = cost_map.get('g1.large', 1.00) * cluster_info['node_count']  # AI 템플릿은 g1.large 워커
        
        total_hourly_cost = master_cost + worker_cost
        
        cost_info = {
            'cluster_name': cluster_name,
            'master_cost_per_hour': master_cost,
            'worker_cost_per_hour': worker_cost,
            'total_cost_per_hour': total_hourly_cost,
            'estimated_daily_cost': total_hourly_cost * 24,
            'estimated_monthly_cost': total_hourly_cost * 24 * 30
        }
        
        return cost_info

def main():
    """메인 함수 - 사용 예시"""
    manager = KCloudClusterManager()
    
    print("=" * 60)
    print("🚀 kcloud-opt 클러스터 관리 예시")
    print("=" * 60)
    
    # 현재 클러스터 목록
    print("\n1️⃣ 현재 클러스터 목록:")
    manager.list_clusters()
    
    # 새 클러스터 생성 예시 (실제로는 주석 해제해서 사용)
    # print("\n2️⃣ 새 ML 훈련 클러스터 생성:")
    # cluster = manager.create_cluster(
    #     name="example-ml-cluster",
    #     workload_type="ml_training", 
    #     node_count=2
    # )
    
    # if cluster:
    #     # 생성 완료 대기
    #     completed_cluster = manager.wait_for_cluster("example-ml-cluster")
    #     
    #     if completed_cluster:
    #         # 비용 계산
    #         cost_info = manager.get_cluster_cost_estimate("example-ml-cluster")
    #         print(f"💰 예상 시간당 비용: ${cost_info['total_cost_per_hour']:.2f}")
    
    print("\n✅ 클러스터 관리 예시 완료")

if __name__ == "__main__":
    main()