#!/usr/bin/env python3
"""
Virtual Cluster CRUD 테스트
OpenStack 10.0.4.200 환경에서 CRUD 작업 테스트
"""

import os
import sys
import time
import json
from datetime import datetime

# 환경 변수 설정
os.environ['OS_AUTH_URL'] = 'http://10.0.4.200:5000/v3'
os.environ['OS_PROJECT_NAME'] = 'cloud-platform'
os.environ['OS_USERNAME'] = 'admin'
os.environ['OS_PASSWORD'] = 'ketilinux'
os.environ['OS_PROJECT_DOMAIN_NAME'] = 'Default'
os.environ['OS_USER_DOMAIN_NAME'] = 'Default'

from openstack_cluster_crud import (
    OpenStackClusterCRUD,
    ClusterConfig,
    ClusterInfo
)


def print_section(title):
    """섹션 헤더 출력"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def test_connection():
    """OpenStack 연결 테스트"""
    print_section("1. OpenStack Connection Test")
    
    try:
        crud = OpenStackClusterCRUD(cloud_name="openstack")
        print("✅ Successfully connected to OpenStack")
        print(f"   Project ID: {crud.project_id}")
        return crud
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None


def test_list_templates(crud):
    """템플릿 목록 조회 테스트"""
    print_section("2. List Cluster Templates")
    
    try:
        templates = crud.get_cluster_templates()
        print(f"✅ Found {len(templates)} templates:")
        
        for tmpl in templates:
            print(f"   - {tmpl['name']}")
            print(f"     ID: {tmpl['id']}")
            print(f"     COE: {tmpl['coe']}")
            print(f"     Flavor: {tmpl['flavor_id']}")
            print(f"     Master Flavor: {tmpl['master_flavor_id']}")
            print()
            
        return templates
        
    except Exception as e:
        print(f"❌ Failed to list templates: {e}")
        return []


def test_list_clusters(crud):
    """클러스터 목록 조회 테스트"""
    print_section("3. List Existing Clusters")
    
    try:
        clusters = crud.list_clusters()
        print(f"✅ Found {len(clusters)} clusters:")
        
        for cluster in clusters:
            print(f"   - {cluster.name}")
            print(f"     ID: {cluster.id}")
            print(f"     Status: {cluster.status}")
            print(f"     Nodes: {cluster.master_count} masters, {cluster.node_count} workers")
            print(f"     Created: {cluster.created_at}")
            print()
            
        return clusters
        
    except Exception as e:
        print(f"❌ Failed to list clusters: {e}")
        return []


def test_create_cluster(crud):
    """클러스터 생성 테스트"""
    print_section("4. Create New Cluster")
    
    # 테스트용 클러스터 설정
    cluster_name = f"test-crud-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    config = ClusterConfig(
        name=cluster_name,
        cluster_template_id="k8s-1.21-cpu-template",  # CPU 템플릿 사용
        node_count=1,  # 최소 노드로 테스트
        master_count=1,
        fixed_network="cloud-platform-selfservice",
        fixed_subnet="cloud-platform-selfservice-subnet",
        labels={
            "kube_dashboard_enabled": "true",
            "prometheus_monitoring": "false",  # 테스트용이므로 비활성화
            "auto_scaling_enabled": "false"
        }
    )
    
    print(f"📝 Creating cluster: {cluster_name}")
    print(f"   Template: {config.cluster_template_id}")
    print(f"   Nodes: {config.master_count} master, {config.node_count} workers")
    
    try:
        start_time = time.time()
        cluster = crud.create_cluster(config)
        elapsed = time.time() - start_time
        
        print(f"✅ Cluster created successfully in {elapsed:.1f} seconds")
        print(f"   ID: {cluster.id}")
        print(f"   Status: {cluster.status}")
        print(f"   API Address: {cluster.api_address}")
        
        return cluster
        
    except Exception as e:
        print(f"❌ Failed to create cluster: {e}")
        return None


def test_get_cluster(crud, cluster_id):
    """특정 클러스터 조회 테스트"""
    print_section("5. Get Cluster Details")
    
    try:
        cluster = crud.get_cluster(cluster_id=cluster_id)
        
        print(f"✅ Successfully retrieved cluster details:")
        print(f"   Name: {cluster.name}")
        print(f"   ID: {cluster.id}")
        print(f"   Status: {cluster.status}")
        print(f"   Stack ID: {cluster.stack_id}")
        print(f"   API Address: {cluster.api_address}")
        print(f"   Master Addresses: {cluster.master_addresses}")
        print(f"   Node Addresses: {cluster.node_addresses}")
        print(f"   Health: {cluster.health_status}")
        
        return cluster
        
    except Exception as e:
        print(f"❌ Failed to get cluster: {e}")
        return None


def test_update_cluster(crud, cluster_id):
    """클러스터 업데이트 테스트 (노드 수 변경)"""
    print_section("6. Update Cluster (Resize)")
    
    print(f"📝 Resizing cluster to 2 nodes...")
    
    try:
        start_time = time.time()
        cluster = crud.resize_cluster(cluster_id, node_count=2)
        elapsed = time.time() - start_time
        
        print(f"✅ Cluster resized successfully in {elapsed:.1f} seconds")
        print(f"   New node count: {cluster.node_count}")
        print(f"   Status: {cluster.status}")
        
        return cluster
        
    except Exception as e:
        print(f"❌ Failed to update cluster: {e}")
        return None


def test_delete_cluster(crud, cluster_id):
    """클러스터 삭제 테스트"""
    print_section("7. Delete Cluster")
    
    print(f"📝 Deleting cluster {cluster_id}...")
    
    try:
        start_time = time.time()
        success = crud.delete_cluster(cluster_id)
        elapsed = time.time() - start_time
        
        if success:
            print(f"✅ Cluster deleted successfully in {elapsed:.1f} seconds")
        else:
            print(f"⚠️  Cluster deletion returned False")
            
        return success
        
    except Exception as e:
        print(f"❌ Failed to delete cluster: {e}")
        return False


def test_cleanup_stuck_clusters(crud):
    """Stuck 클러스터 정리 테스트"""
    print_section("8. Cleanup Stuck Clusters")
    
    try:
        deleted = crud.cleanup_stuck_clusters(hours=24)
        
        if deleted:
            print(f"✅ Cleaned up {len(deleted)} stuck clusters:")
            for cluster_id in deleted:
                print(f"   - {cluster_id}")
        else:
            print("✅ No stuck clusters found")
            
        return deleted
        
    except Exception as e:
        print(f"❌ Failed to cleanup: {e}")
        return []


def run_full_test(skip_create=False):
    """전체 CRUD 테스트 실행"""
    print("\n" + "="*60)
    print(" OpenStack Virtual Cluster CRUD Test Suite")
    print(" Target: 10.0.4.200")
    print(" Time: " + datetime.now().isoformat())
    print("="*60)
    
    # 1. 연결 테스트
    crud = test_connection()
    if not crud:
        print("\n❌ Cannot proceed without OpenStack connection")
        return
    
    # 2. 템플릿 목록
    templates = test_list_templates(crud)
    
    # 3. 기존 클러스터 목록
    existing_clusters = test_list_clusters(crud)
    
    # 4-7. CRUD 작업 테스트
    if not skip_create:
        print("\n" + "="*60)
        print(" Starting CRUD Operations Test")
        print("="*60)
        
        # 생성
        new_cluster = test_create_cluster(crud)
        
        if new_cluster:
            cluster_id = new_cluster.id
            
            # 조회
            time.sleep(5)  # 상태 안정화 대기
            test_get_cluster(crud, cluster_id)
            
            # 업데이트 (옵션)
            # test_update_cluster(crud, cluster_id)
            
            # 삭제
            print("\n⚠️  Delete the test cluster? (y/n): ", end="")
            if input().lower() == 'y':
                test_delete_cluster(crud, cluster_id)
    
    # 8. 정리 작업
    test_cleanup_stuck_clusters(crud)
    
    # 최종 요약
    print("\n" + "="*60)
    print(" Test Summary")
    print("="*60)
    print("✅ All tests completed")
    print(f"📊 Current cluster count: {len(crud.list_clusters())}")


def run_quick_test():
    """빠른 읽기 전용 테스트"""
    print("\n🚀 Running quick read-only tests...")
    
    crud = test_connection()
    if crud:
        test_list_templates(crud)
        test_list_clusters(crud)
        test_cleanup_stuck_clusters(crud)
    
    print("\n✅ Quick test completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Virtual Cluster CRUD Operations")
    parser.add_argument("--quick", action="store_true", help="Run quick read-only tests")
    parser.add_argument("--full", action="store_true", help="Run full CRUD tests")
    parser.add_argument("--skip-create", action="store_true", help="Skip cluster creation")
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    elif args.full:
        run_full_test(skip_create=args.skip_create)
    else:
        # 기본: 빠른 테스트
        run_quick_test()
        print("\n💡 Use --full for complete CRUD testing")
        print("💡 Use --skip-create to skip cluster creation")