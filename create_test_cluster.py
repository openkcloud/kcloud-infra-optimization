#!/usr/bin/env python3
"""
테스트 클러스터 생성 및 모니터링
"""

import os
import time
import json
from datetime import datetime

# 환경 변수 설정
os.environ['OS_CLIENT_CONFIG_FILE'] = '/root/kcloud_opt/clouds.yaml'

from openstack_cluster_crud import OpenStackClusterCRUD, ClusterConfig


def create_test_cluster():
    """테스트 클러스터 생성"""
    print("🚀 Creating test cluster...")
    
    crud = OpenStackClusterCRUD()
    
    # 사용 가능한 템플릿 확인
    print("\n📋 Available templates:")
    templates = crud.get_cluster_templates()
    for i, tmpl in enumerate(templates):
        print(f"  {i+1}. {tmpl['name']} (ID: {tmpl['id']})")
    
    # 가장 작은 템플릿 선택 (dev-k8s-template)
    template_id = None
    for tmpl in templates:
        if 'dev' in tmpl['name'].lower():
            template_id = tmpl['id']
            break
    
    if not template_id:
        template_id = templates[0]['id']  # 첫 번째 템플릿 사용
    
    print(f"✅ Selected template: {template_id}")
    
    # 클러스터 설정
    cluster_name = f"test-demo-{datetime.now().strftime('%m%d-%H%M')}"
    
    config = ClusterConfig(
        name=cluster_name,
        cluster_template_id=template_id,
        master_count=1,
        node_count=1,  # 최소 구성
        fixed_network="cloud-platform-selfservice",
        fixed_subnet="cloud-platform-selfservice-subnet",
        labels={
            "kube_dashboard_enabled": "false",  # 빠른 생성을 위해
            "prometheus_monitoring": "false",
            "auto_scaling_enabled": "false"
        }
    )
    
    print(f"\n📝 Cluster configuration:")
    print(f"  Name: {cluster_name}")
    print(f"  Template: {template_id}")
    print(f"  Masters: {config.master_count}")
    print(f"  Workers: {config.node_count}")
    print(f"  Network: {config.fixed_network}")
    
    # 생성 시작
    try:
        print(f"\n🔄 Starting cluster creation...")
        start_time = time.time()
        
        cluster = crud.create_cluster(config)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Cluster created successfully in {elapsed:.1f} seconds!")
        print(f"  ID: {cluster.id}")
        print(f"  Name: {cluster.name}")
        print(f"  Status: {cluster.status}")
        
        return cluster
        
    except Exception as e:
        print(f"\n❌ Failed to create cluster: {e}")
        return None


def monitor_cluster_creation(cluster_id):
    """클러스터 생성 진행 상황 모니터링"""
    print(f"\n👀 Monitoring cluster creation: {cluster_id}")
    
    crud = OpenStackClusterCRUD()
    
    start_time = time.time()
    check_count = 0
    
    while True:
        try:
            cluster = crud.get_cluster(cluster_id)
            elapsed = time.time() - start_time
            check_count += 1
            
            print(f"  [{check_count:2d}] {elapsed/60:.1f}min - Status: {cluster.status}")
            
            # 완료 상태 체크
            if cluster.status in ["CREATE_COMPLETE"]:
                print(f"\n🎉 Cluster creation completed!")
                print(f"  API Address: {cluster.api_address}")
                print(f"  Master Addresses: {cluster.master_addresses}")
                print(f"  Node Addresses: {cluster.node_addresses}")
                break
                
            elif "FAILED" in cluster.status or "ERROR" in cluster.status:
                print(f"\n❌ Cluster creation failed: {cluster.status}")
                break
                
            # 너무 오래 걸리면 중단
            if elapsed > 3600:  # 1시간
                print(f"\n⏰ Timeout after 1 hour")
                break
                
            time.sleep(30)  # 30초마다 체크
            
        except Exception as e:
            print(f"  Error checking status: {e}")
            time.sleep(30)


def list_all_clusters():
    """모든 클러스터 목록 조회"""
    print("\n📊 Current clusters:")
    
    crud = OpenStackClusterCRUD()
    
    try:
        clusters = crud.list_clusters()
        
        if not clusters:
            print("  No clusters found")
            return
            
        for cluster in clusters:
            age_str = cluster.created_at
            print(f"  • {cluster.name}")
            print(f"    ID: {cluster.id}")
            print(f"    Status: {cluster.status}")
            print(f"    Nodes: {cluster.master_count}M + {cluster.node_count}W")
            print(f"    Created: {age_str}")
            print()
            
    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print(" OpenStack Cluster Creation Test")
    print("="*60)
    
    # 현재 클러스터 상태 확인
    list_all_clusters()
    
    # 사용자 선택
    if len(sys.argv) > 1 and sys.argv[1] == "--create":
        # 새 클러스터 생성
        cluster = create_test_cluster()
        
        if cluster:
            print(f"\n💡 To monitor progress, run:")
            print(f"   python create_test_cluster.py --monitor {cluster.id}")
            
    elif len(sys.argv) > 2 and sys.argv[1] == "--monitor":
        # 클러스터 모니터링
        cluster_id = sys.argv[2]
        monitor_cluster_creation(cluster_id)
        
    else:
        print("\n💡 Usage:")
        print("  python create_test_cluster.py                    # List clusters")
        print("  python create_test_cluster.py --create          # Create new cluster")
        print("  python create_test_cluster.py --monitor <ID>    # Monitor cluster")