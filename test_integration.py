#!/usr/bin/env python3
"""
kcloud-opt Infrastructure 모듈 통합 테스트
OpenStack Magnum 연동 확인
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 가상환경 경로 추가
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

# OpenStack SDK
try:
    import openstack
    from magnumclient import client as magnum_client
    from keystoneauth1 import loading, session
    print("✅ OpenStack 라이브러리 로드 완료")
except ImportError as e:
    print(f"❌ 라이브러리 설치 필요: {e}")
    print("실행: pip install openstacksdk python-magnumclient")
    sys.exit(1)

class KCloudInfrastructureTest:
    """kcloud-opt Infrastructure 모듈 테스트 클래스"""
    
    def __init__(self):
        self.auth_config = {
            'auth_url': 'http://10.0.4.200:5000/v3',
            'username': 'admin',
            'password': 'ketilinux',
            'project_name': 'cloud-platform',
            'project_domain_name': 'Default',
            'user_domain_name': 'Default',
            'region_name': 'RegionOne',
            'interface': 'public',
            'identity_api_version': '3'
        }
        self.conn = None
        self.magnum = None
    
    def setup_connections(self):
        """OpenStack 연결 설정"""
        try:
            # OpenStack SDK 연결
            self.conn = openstack.connect(**self.auth_config)
            print("✅ OpenStack SDK 연결 성공")
            
            # Magnum 클라이언트 연결
            loader = loading.get_plugin_loader('password')
            magnum_auth_config = {
                'auth_url': self.auth_config['auth_url'],
                'username': self.auth_config['username'],
                'password': self.auth_config['password'],
                'project_name': self.auth_config['project_name'],
                'project_domain_name': self.auth_config['project_domain_name'],
                'user_domain_name': self.auth_config['user_domain_name']
            }
            auth = loader.load_from_options(**magnum_auth_config)
            sess = session.Session(auth=auth)
            self.magnum = magnum_client.Client('1', session=sess)
            print("✅ Magnum 클라이언트 연결 성공")
            
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
    
    def test_cluster_list(self):
        """클러스터 목록 조회 테스트"""
        print("\n🔍 클러스터 목록 조회 테스트:")
        try:
            clusters = list(self.magnum.clusters.list())
            print(f"  📊 클러스터 수: {len(clusters)}")
            
            for cluster in clusters:
                print(f"  🔸 {cluster.name}: {cluster.status} (노드: {cluster.node_count})")
            
            return clusters
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return []
    
    def test_cluster_templates(self):
        """클러스터 템플릿 조회 테스트"""
        print("\n🔍 클러스터 템플릿 조회 테스트:")
        try:
            templates = list(self.magnum.cluster_templates.list())
            print(f"  📊 템플릿 수: {len(templates)}")
            
            ai_template = None
            for template in templates:
                print(f"  🔸 {template.name}: {template.coe}")
                if 'ai' in template.name.lower():
                    ai_template = template
            
            if ai_template:
                print(f"  ✅ AI 템플릿 발견: {ai_template.name}")
                return ai_template
            else:
                print("  ⚠️ AI 템플릿을 찾을 수 없음")
                return None
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return None
    
    def test_cluster_status(self, cluster_name="kcloud-ai-cluster"):
        """특정 클러스터 상태 확인"""
        print(f"\n🔍 클러스터 '{cluster_name}' 상태 확인:")
        try:
            cluster = self.magnum.clusters.get(cluster_name)
            
            status_info = {
                'name': cluster.name,
                'status': cluster.status,
                'health_status': cluster.health_status,
                'node_count': cluster.node_count,
                'master_count': cluster.master_count,
                'api_address': cluster.api_address,
                'master_addresses': cluster.master_addresses,
                'node_addresses': cluster.node_addresses
            }
            
            print(f"  📊 상태: {cluster.status}")
            print(f"  🏥 헬스: {cluster.health_status}")
            print(f"  🖥️ 노드 수: {cluster.node_count}")
            
            if cluster.api_address:
                print(f"  🌐 API 주소: {cluster.api_address}")
            
            return status_info
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return None
    
    def test_resources_analysis(self):
        """클러스터 자원 분석"""
        print("\n🔍 클러스터 자원 분석:")
        try:
            # 현재 인스턴스 목록
            servers = list(self.conn.compute.servers())
            cluster_servers = [s for s in servers if 'kcloud' in s.name.lower()]
            
            print(f"  📊 kcloud 관련 인스턴스: {len(cluster_servers)}")
            
            total_vcpus = 0
            total_ram = 0
            gpu_instances = 0
            
            for server in cluster_servers:
                flavor = self.conn.compute.get_flavor(server.flavor['id'])
                print(f"  🔸 {server.name}: {flavor.name} ({server.status})")
                
                total_vcpus += flavor.vcpus
                total_ram += flavor.ram
                
                if 'g1' in flavor.name:
                    gpu_instances += 1
            
            resource_summary = {
                'total_instances': len(cluster_servers),
                'gpu_instances': gpu_instances,
                'total_vcpus': total_vcpus,
                'total_ram_mb': total_ram,
                'estimated_cost_per_hour': self.calculate_estimated_cost(cluster_servers)
            }
            
            print(f"  💰 예상 비용/시간: ${resource_summary['estimated_cost_per_hour']:.2f}")
            print(f"  ⚡ GPU 인스턴스: {gpu_instances}개")
            
            return resource_summary
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            return {}
    
    def calculate_estimated_cost(self, servers):
        """비용 추정 계산"""
        cost_map = {
            'm1.small': 0.05,
            'm1.medium': 0.10,
            'm1.large': 0.20,
            'g1.small': 0.50,
            'g1.large': 1.00
        }
        
        total_cost = 0
        for server in servers:
            try:
                flavor = self.conn.compute.get_flavor(server.flavor['id'])
                total_cost += cost_map.get(flavor.name, 0.05)
            except:
                total_cost += 0.05  # 기본값
        
        return total_cost
    
    def test_kcloud_optimization_readiness(self):
        """kcloud-opt 최적화 준비 상태 확인"""
        print("\n🎯 kcloud-opt 최적화 준비 상태:")
        
        readiness = {
            'magnum_service': False,
            'gpu_support': False,
            'ai_template': False,
            'network_setup': False,
            'cluster_ready': False
        }
        
        try:
            # Magnum 서비스 확인
            services = list(self.conn.identity.services())
            magnum_service = any(s.type == 'container-infra' for s in services)
            readiness['magnum_service'] = magnum_service
            
            # GPU 지원 확인
            flavors = list(self.conn.compute.flavors())
            gpu_flavors = [f for f in flavors if 'g1' in f.name]
            readiness['gpu_support'] = len(gpu_flavors) > 0
            
            # AI 템플릿 확인
            templates = list(self.magnum.cluster_templates.list())
            ai_template = any('ai' in t.name.lower() for t in templates)
            readiness['ai_template'] = ai_template
            
            # 네트워크 설정 확인
            networks = list(self.conn.network.networks())
            cloud_network = any('cloud-platform' in n.name for n in networks)
            readiness['network_setup'] = cloud_network
            
            # 클러스터 상태 확인
            clusters = list(self.magnum.clusters.list())
            active_cluster = any(c.status == 'CREATE_COMPLETE' for c in clusters)
            readiness['cluster_ready'] = active_cluster
            
        except Exception as e:
            print(f"  ❌ 확인 중 오류: {e}")
        
        # 결과 출력
        for component, ready in readiness.items():
            status = "✅" if ready else "❌"
            print(f"  {status} {component.replace('_', ' ').title()}")
        
        overall_ready = all(readiness.values())
        print(f"\n🚀 전체 준비 상태: {'완료' if overall_ready else '부분적'}")
        
        return readiness
    
    def generate_integration_report(self):
        """통합 테스트 리포트 생성"""
        print("\n📝 통합 테스트 리포트 생성 중...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'openstack_endpoint': self.auth_config['auth_url'],
            'project': self.auth_config['project_name'],
            'test_results': {}
        }
        
        # 각 테스트 실행
        report['test_results']['clusters'] = self.test_cluster_list()
        report['test_results']['template'] = self.test_cluster_templates()
        report['test_results']['status'] = self.test_cluster_status()
        report['test_results']['resources'] = self.test_resources_analysis()
        report['test_results']['readiness'] = self.test_kcloud_optimization_readiness()
        
        # 리포트 저장
        with open('kcloud_integration_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print("📄 리포트 저장: kcloud_integration_report.json")
        return report

def main():
    """메인 테스트 실행"""
    print("🚀 kcloud-opt Infrastructure 모듈 통합 테스트")
    print("=" * 60)
    
    test = KCloudInfrastructureTest()
    
    # 연결 설정
    if not test.setup_connections():
        print("❌ 연결 설정 실패")
        return 1
    
    # 통합 테스트 실행
    report = test.generate_integration_report()
    
    print("\n" + "=" * 60)
    print("✅ 통합 테스트 완료!")
    print(f"📊 리포트: kcloud_integration_report.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())