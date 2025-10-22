#!/usr/bin/env python3
"""
클러스터 그룹 오케스트레이터 테스트
"""

import os
import asyncio
import json
from datetime import datetime

# 환경 변수 설정
os.environ['OS_CLIENT_CONFIG_FILE'] = '/root/kcloud_opt/clouds.yaml'

from cluster_group_orchestrator import (
    ClusterGroupOrchestrator,
    ClusterGroupConfig,
    GroupType
)


async def test_basic_operations():
    """기본 그룹 운영 테스트"""
    print("🧪 Testing Cluster Group Orchestrator")
    print("="*50)
    
    # 오케스트레이터 초기화
    orchestrator = ClusterGroupOrchestrator()
    
    try:
        # 1. 개발용 그룹 생성
        print("\n1️⃣ Creating development cluster group...")
        dev_config = ClusterGroupConfig(
            name="dev-test-group",
            group_type=GroupType.DEVELOPMENT,
            min_clusters=1,
            max_clusters=3,
            auto_scaling_enabled=True,
            labels={"environment": "development", "team": "platform"}
        )
        
        dev_group = await orchestrator.create_group(dev_config)
        print(f"✅ Created group: {dev_group.name}")
        print(f"   ID: {dev_group.id}")
        print(f"   Type: {dev_group.group_type}")
        print(f"   Clusters: {dev_group.active_clusters}")
        
        # 2. 그룹 목록 조회
        print("\n2️⃣ Listing all groups...")
        groups = orchestrator.list_groups()
        print(f"✅ Found {len(groups)} groups:")
        for group in groups:
            print(f"   - {group.name} ({group.group_type}): {group.active_clusters} clusters")
        
        # 3. 특정 그룹 조회
        print("\n3️⃣ Getting group details...")
        retrieved_group = orchestrator.get_group(dev_group.id)
        if retrieved_group:
            print(f"✅ Retrieved group: {retrieved_group.name}")
            print(f"   Status: {retrieved_group.status}")
            print(f"   Total nodes: {retrieved_group.total_nodes}")
        
        # 4. 클러스터 추가 (시뮬레이션 - 실제 생성은 시간이 오래 걸림)
        print("\n4️⃣ Simulating cluster addition...")
        cluster_spec = {
            'name': 'additional-cluster',
            'node_count': 2,
            'master_count': 1,
            'labels': {'purpose': 'testing'}
        }
        print(f"📝 Would add cluster with spec: {cluster_spec}")
        # await orchestrator.add_cluster_to_group(dev_group.id, cluster_spec)
        
        # 5. 외부 최적화 명령 시뮬레이션
        print("\n5️⃣ Testing external optimization commands...")
        
        # 스케일링 명령
        scale_command = {
            'type': 'scale_group',
            'group_id': dev_group.id,
            'target_clusters': 2,
            'reason': 'increased_demand'
        }
        print(f"📝 Scale command: {scale_command['type']}")
        # result = await orchestrator.execute_optimization_command(scale_command)
        # print(f"   Result: {result.get('success', False)}")
        
        # 6. 그룹 정보 업데이트 확인
        print("\n6️⃣ Checking final group status...")
        final_group = orchestrator.get_group(dev_group.id)
        if final_group:
            print(f"✅ Final group state:")
            print(f"   Name: {final_group.name}")
            print(f"   Status: {final_group.status}")
            print(f"   Active clusters: {final_group.active_clusters}")
            print(f"   Total nodes: {final_group.total_nodes}")
            print(f"   Created: {final_group.created_at}")
            print(f"   Updated: {final_group.updated_at}")
        
        # 7. 정리 (실제로는 실행하지 않음 - 테스트용)
        print("\n7️⃣ Cleanup (simulated)...")
        print(f"📝 Would delete group: {dev_group.id}")
        # await orchestrator.delete_group(dev_group.id, force=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_group_types():
    """다양한 그룹 타입 테스트"""
    print("\n🏷️ Testing different group types...")
    
    orchestrator = ClusterGroupOrchestrator()
    
    group_configs = [
        {
            'name': 'gpu-training',
            'type': GroupType.GPU_INTENSIVE,
            'description': 'GPU 집약적 ML 트레이닝'
        },
        {
            'name': 'cpu-compute',
            'type': GroupType.CPU_COMPUTE,
            'description': 'CPU 연산 집약적 작업'
        },
        {
            'name': 'mixed-workload',
            'type': GroupType.MIXED_WORKLOAD,
            'description': '혼합 워크로드'
        }
    ]
    
    created_groups = []
    
    for config_spec in group_configs:
        try:
            print(f"\n   Creating {config_spec['name']} group...")
            
            config = ClusterGroupConfig(
                name=config_spec['name'],
                group_type=config_spec['type'],
                min_clusters=0,  # 실제 클러스터 생성 방지
                auto_scaling_enabled=False
            )
            
            group = await orchestrator.create_group(config)
            created_groups.append(group)
            
            print(f"   ✅ {config_spec['description']}: {group.id}")
            
        except Exception as e:
            print(f"   ❌ Failed to create {config_spec['name']}: {e}")
    
    # 타입별 그룹 조회 테스트
    print(f"\n   📊 Created {len(created_groups)} groups")
    
    # GPU 그룹만 조회
    gpu_groups = orchestrator.list_groups(group_type=GroupType.GPU_INTENSIVE)
    print(f"   🎮 GPU groups: {len(gpu_groups)}")
    
    return len(created_groups) > 0


async def test_command_interface():
    """외부 명령 인터페이스 테스트"""
    print("\n🔧 Testing command interface...")
    
    orchestrator = ClusterGroupOrchestrator()
    
    # 테스트용 그룹 생성
    config = ClusterGroupConfig(
        name="command-test-group",
        group_type=GroupType.DEVELOPMENT,
        min_clusters=0
    )
    
    group = await orchestrator.create_group(config)
    print(f"   Created test group: {group.id}")
    
    # 다양한 명령 테스트
    commands = [
        {
            'type': 'scale_group',
            'group_id': group.id,
            'target_clusters': 3,
            'description': '그룹 스케일링'
        },
        {
            'type': 'consolidate_groups',
            'source_groups': [group.id],
            'target_group': group.id,
            'description': '그룹 통합'
        },
        {
            'type': 'migrate_workloads',
            'from_cluster': 'cluster-1',
            'to_cluster': 'cluster-2',
            'description': '워크로드 마이그레이션'
        },
        {
            'type': 'optimize_placement',
            'group_id': group.id,
            'strategy': 'cost_minimal',
            'description': '배치 최적화'
        }
    ]
    
    results = []
    
    for cmd in commands:
        try:
            print(f"   🔄 Testing: {cmd['description']}")
            result = await orchestrator.execute_optimization_command(cmd)
            results.append({
                'command': cmd['type'],
                'success': result.get('success', False),
                'description': cmd['description']
            })
            
            status = "✅" if result.get('success') else "❌"
            print(f"      {status} {cmd['type']}")
            
        except Exception as e:
            print(f"      ❌ {cmd['type']}: {e}")
            results.append({
                'command': cmd['type'],
                'success': False,
                'error': str(e)
            })
    
    # 결과 요약
    successful = sum(1 for r in results if r['success'])
    print(f"\n   📊 Command test results: {successful}/{len(results)} successful")
    
    return successful > 0


async def test_integration_with_existing_crud():
    """기존 CRUD와의 통합 테스트"""
    print("\n🔗 Testing integration with existing CRUD...")
    
    orchestrator = ClusterGroupOrchestrator()
    
    # 기존 클러스터 확인
    try:
        existing_clusters = orchestrator.crud.list_clusters()
        print(f"   📋 Found {len(existing_clusters)} existing clusters")
        
        for cluster in existing_clusters:
            print(f"      - {cluster.name}: {cluster.status}")
        
        # 기존 템플릿 확인
        templates = orchestrator.crud.get_cluster_templates()
        print(f"   📋 Available templates: {len(templates)}")
        
        template_names = [t['name'] for t in templates]
        print(f"      Templates: {', '.join(template_names)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False


async def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 Cluster Group Orchestrator Test Suite")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    tests = [
        ("Basic Operations", test_basic_operations),
        ("Group Types", test_group_types),
        ("Command Interface", test_command_interface),
        ("CRUD Integration", test_integration_with_existing_crud)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status}: {test_name}")
            
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # 최종 결과
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"⏰ Completed at: {datetime.now().isoformat()}")
    
    return passed == total


if __name__ == "__main__":
    print("Starting Cluster Group Orchestrator tests...")
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    exit(0 if success else 1)