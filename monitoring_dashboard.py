#!/usr/bin/env python3
"""
실시간 가상 클러스터 모니터링 대시보드
터미널 기반 실시간 모니터링 UI
"""

import sys
import time
import json
from datetime import datetime
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

from virtual_cluster_monitoring import VirtualClusterMonitor

def clear_screen():
    """화면 지우기"""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')

def draw_progress_bar(percentage, width=20):
    """진행 막대 그리기"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def get_status_emoji(status):
    """상태에 따른 이모지 반환"""
    status_map = {
        'CREATE_COMPLETE': '✅',
        'CREATE_IN_PROGRESS': '🔄',
        'CREATE_FAILED': '❌',
        'DELETE_IN_PROGRESS': '🗑️',
        'ERROR': '⚠️'
    }
    return status_map.get(status, '❓')

def display_cluster_details(cluster_metrics):
    """클러스터 상세 정보 표시"""
    print(f"    📦 {cluster_metrics.cluster_name}")
    print(f"       {get_status_emoji(cluster_metrics.status)} 상태: {cluster_metrics.status}")
    
    if cluster_metrics.status == 'CREATE_COMPLETE':
        print(f"       🖥️ 노드: {cluster_metrics.node_count}개")
        print(f"       🏃 실행 중 포드: {cluster_metrics.running_pods}개")
        print(f"       💰 시간당 비용: ${cluster_metrics.cost_per_hour:.2f}")
        print(f"       📊 CPU: {draw_progress_bar(cluster_metrics.cpu_usage_percent)}")
        print(f"       🧠 메모리: {draw_progress_bar(cluster_metrics.memory_usage_percent)}")
        
        if cluster_metrics.gpu_usage_percent > 0:
            print(f"       ⚡ GPU: {draw_progress_bar(cluster_metrics.gpu_usage_percent)}")
        
        print(f"       🔋 전력: {cluster_metrics.power_consumption_watts:.0f}W")
        
        if cluster_metrics.failed_pods > 0:
            print(f"       ⚠️ 실패한 포드: {cluster_metrics.failed_pods}개")
        if cluster_metrics.pending_pods > 0:
            print(f"       ⏳ 대기 중 포드: {cluster_metrics.pending_pods}개")

def display_realtime_dashboard(monitor, virtual_groups):
    """실시간 대시보드 표시"""
    
    while True:
        clear_screen()
        
        print("🌐 kcloud-opt 가상 클러스터 실시간 모니터링 대시보드")
        print("=" * 70)
        print(f"⏰ 업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        total_cost = 0.0
        total_power = 0.0
        total_clusters = 0
        active_clusters = 0
        
        # 각 가상 그룹 상태 표시
        for group_name, cluster_names in virtual_groups.items():
            print(f"🌐 가상 그룹: {group_name}")
            print("-" * 50)
            
            try:
                group_metrics = monitor.collect_group_metrics(group_name, cluster_names)
                
                # 그룹 요약
                print(f"  📊 그룹 요약:")
                print(f"    클러스터: {group_metrics.total_clusters}개 (활성: {group_metrics.active_clusters}개)")
                print(f"    총 노드: {group_metrics.total_nodes}개")
                print(f"    시간당 비용: ${group_metrics.total_cost_per_hour:.2f}")
                print(f"    전력 소비: {group_metrics.total_power_consumption:.0f}W")
                
                # 헬스 및 효율성 스코어
                health_color = "🟢" if group_metrics.health_score > 70 else "🟡" if group_metrics.health_score > 40 else "🔴"
                efficiency_color = "🟢" if group_metrics.efficiency_score > 70 else "🟡" if group_metrics.efficiency_score > 40 else "🔴"
                
                print(f"    {health_color} 헬스 스코어: {group_metrics.health_score:.1f}/100")
                print(f"    {efficiency_color} 효율성 스코어: {group_metrics.efficiency_score:.1f}/100")
                
                if group_metrics.active_clusters > 0:
                    print(f"    평균 활용률:")
                    print(f"      CPU: {draw_progress_bar(group_metrics.avg_cpu_usage)}")
                    print(f"      메모리: {draw_progress_bar(group_metrics.avg_memory_usage)}")
                    if group_metrics.avg_gpu_usage > 0:
                        print(f"      GPU: {draw_progress_bar(group_metrics.avg_gpu_usage)}")
                
                print(f"\n  📦 클러스터 상세:")
                for cluster_metrics in group_metrics.cluster_metrics:
                    display_cluster_details(cluster_metrics)
                
                # 전체 합계에 추가
                total_cost += group_metrics.total_cost_per_hour
                total_power += group_metrics.total_power_consumption
                total_clusters += group_metrics.total_clusters
                active_clusters += group_metrics.active_clusters
                
            except Exception as e:
                print(f"  ❌ 그룹 메트릭 수집 실패: {e}")
            
            print()
        
        # 전체 요약
        print("=" * 70)
        print("📊 전체 요약")
        print("-" * 30)
        print(f"🌐 가상 그룹: {len(virtual_groups)}개")
        print(f"📦 총 클러스터: {total_clusters}개 (활성: {active_clusters}개)")
        print(f"💰 총 시간당 비용: ${total_cost:.2f}")
        print(f"🔋 총 전력 소비: {total_power:.0f}W")
        print(f"📅 예상 일 비용: ${total_cost * 24:.2f}")
        print(f"📅 예상 월 비용: ${total_cost * 24 * 30:.2f}")
        
        # 알림 표시
        if hasattr(monitor, 'alerts') and monitor.alerts:
            print(f"\n🚨 최근 알림 ({len(monitor.alerts)}개)")
            print("-" * 30)
            for alert in monitor.alerts[-5:]:  # 최근 5개만 표시
                severity_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(alert['severity'], "❓")
                print(f"  {severity_emoji} [{alert['type']}] {alert['message']}")
        
        print(f"\n💡 다음 업데이트: {monitor.update_interval}초 후")
        print("종료하려면 Ctrl+C를 누르세요")
        
        # 업데이트 주기만큼 대기
        try:
            time.sleep(monitor.update_interval)
        except KeyboardInterrupt:
            print(f"\n👋 모니터링 종료")
            break

def generate_monitoring_summary():
    """모니터링 요약 리포트 생성"""
    print("\n📋 모니터링 요약 리포트")
    print("=" * 50)
    
    monitor = VirtualClusterMonitor()
    
    # 현재 상태만 확인 (실시간 모니터링 없이)
    virtual_groups = {
        'ml-training-group': ['kcloud-ai-cluster-v2']
    }
    
    for group_name, cluster_names in virtual_groups.items():
        print(f"\n🌐 그룹: {group_name}")
        
        group_metrics = monitor.collect_group_metrics(group_name, cluster_names)
        
        print(f"  상태: {'정상' if group_metrics.health_score > 50 else '주의 필요'}")
        print(f"  클러스터: {group_metrics.total_clusters}개")
        print(f"  비용: ${group_metrics.total_cost_per_hour:.2f}/시간")
        print(f"  헬스: {group_metrics.health_score:.1f}/100")
        print(f"  효율성: {group_metrics.efficiency_score:.1f}/100")
        
        # 권장사항
        recommendations = []
        if group_metrics.efficiency_score < 50:
            recommendations.append("효율성 개선 필요")
        if group_metrics.total_cost_per_hour > 10:
            recommendations.append("비용 최적화 권장")
        if group_metrics.health_score < 70:
            recommendations.append("헬스 점검 필요")
        
        if recommendations:
            print(f"  💡 권장사항: {', '.join(recommendations)}")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='가상 클러스터 모니터링 대시보드')
    parser.add_argument('--mode', choices=['dashboard', 'summary'], default='summary',
                       help='실행 모드 (dashboard: 실시간, summary: 요약)')
    parser.add_argument('--interval', type=int, default=30,
                       help='업데이트 주기(초)')
    
    args = parser.parse_args()
    
    if args.mode == 'dashboard':
        print("🚀 실시간 대시보드 시작...")
        monitor = VirtualClusterMonitor(update_interval=args.interval)
        
        virtual_groups = {
            'ml-training-group': ['kcloud-ai-cluster-v2']
            # 실제로는 더 많은 그룹 추가
        }
        
        display_realtime_dashboard(monitor, virtual_groups)
    else:
        generate_monitoring_summary()

if __name__ == "__main__":
    main()