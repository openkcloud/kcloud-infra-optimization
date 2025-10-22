#!/usr/bin/env python3
"""
가상 클러스터 그룹 대시보드 예시
"""

import sys
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

from virtual_cluster_group_manager import VirtualClusterGroupManager
import json

def show_group_dashboard():
    """그룹 대시보드 표시"""
    manager = VirtualClusterGroupManager()
    
    print("🌐 가상 클러스터 그룹 대시보드")
    print("=" * 50)
    
    # 예시 그룹들 생성 (실제로는 주석 해제)
    example_groups = {
        "ml-training-team": {
            "type": "ml_training",
            "clusters": 3,
            "total_nodes": 8,
            "hourly_cost": 12.50,
            "status": "Active",
            "utilization": 85
        },
        "ai-inference-prod": {
            "type": "ai_inference", 
            "clusters": 2,
            "total_nodes": 6,
            "hourly_cost": 8.00,
            "status": "Active",
            "utilization": 70
        },
        "dev-testing": {
            "type": "development",
            "clusters": 1,
            "total_nodes": 2,
            "hourly_cost": 2.50,
            "status": "Standby",
            "utilization": 25
        }
    }
    
    total_cost = 0
    total_nodes = 0
    
    for group_name, info in example_groups.items():
        print(f"\n🔸 {group_name} ({info['type']})")
        print(f"  📦 클러스터: {info['clusters']}개")
        print(f"  🖥️ 노드: {info['total_nodes']}개") 
        print(f"  💰 시간당 비용: ${info['hourly_cost']:.2f}")
        print(f"  📊 활용률: {info['utilization']}%")
        print(f"  🔋 상태: {info['status']}")
        
        total_cost += info['hourly_cost']
        total_nodes += info['total_nodes']
    
    print(f"\n" + "=" * 50)
    print(f"📊 전체 요약:")
    print(f"  🌐 그룹 수: {len(example_groups)}개")
    print(f"  🖥️ 총 노드: {total_nodes}개")
    print(f"  💰 총 시간당 비용: ${total_cost:.2f}")
    print(f"  📅 예상 월 비용: ${total_cost * 24 * 30:.2f}")
    
    print(f"\n💡 비용 절감 제안:")
    print(f"  • dev-testing 그룹 야간 자동 종료: 월 $540 절약")
    print(f"  • 유휴 노드 감지 시 자동 스케일 인: 월 $800 절약")
    print(f"  • GPU 활용률 기반 동적 배치: 월 $1200 절약")

if __name__ == "__main__":
    show_group_dashboard()