#!/usr/bin/env python3
"""
kcloud-opt 모니터링 시스템 데모
실제 클러스터와 시뮬레이션 데이터로 모니터링 기능 시연
"""

import sys
import time
from datetime import datetime

sys.path.insert(0, '/root/kcloud_opt')
from infrastructure.monitoring.integrated_monitor import IntegratedMonitor

def demo_monitoring_features():
    """모니터링 기능 데모"""
    print("🎪 kcloud-opt 모니터링 시스템 데모")
    print("=" * 60)
    
    monitor = IntegratedMonitor(update_interval=10)  # 빠른 업데이트
    
    # 테스트할 클러스터 (실제 + 시뮬레이션)
    test_clusters = ['kcloud-ai-cluster-v2']
    
    print(f"\n📊 1. 단일 리포트 생성")
    print("-" * 30)
    
    report = monitor.generate_report(test_clusters)
    monitor.save_report(report)
    
    print(f"  ✅ 리포트 생성 완료")
    print(f"  📊 총 비용: ${report['summary']['total_cost_per_hour']:.2f}/시간")
    print(f"  🔋 총 전력: {report['summary']['total_power_consumption']:.0f}W")
    print(f"  🚨 활성 알림: {report['alerts']['total_active']}개")
    
    print(f"\n📈 2. 연속 모니터링 시연 (30초)")
    print("-" * 30)
    print("실시간으로 클러스터 상태를 모니터링합니다...")
    
    # 30초간 연속 모니터링
    start_time = time.time()
    update_count = 0
    
    try:
        while time.time() - start_time < 30:  # 30초간
            print(f"\n🔄 업데이트 #{update_count + 1}")
            
            cluster_metrics = monitor.monitor_clusters(test_clusters)
            monitor.print_monitoring_summary(cluster_metrics)
            
            update_count += 1
            
            print(f"⏳ 다음 업데이트까지 {monitor.update_interval}초...")
            time.sleep(monitor.update_interval)
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    
    print(f"\n✅ 연속 모니터링 완료 ({update_count}회 업데이트)")
    
    print(f"\n🚨 3. 알림 시스템 기능")
    print("-" * 30)
    
    alert_summary = monitor.alert_system.get_alert_summary()
    print(f"  현재 활성 알림: {alert_summary['total_active']}개")
    
    if alert_summary['total_active'] > 0:
        print(f"  CRITICAL: {alert_summary['by_severity']['CRITICAL']}개")
        print(f"  WARNING: {alert_summary['by_severity']['WARNING']}개")
        print(f"  INFO: {alert_summary['by_severity']['INFO']}개")
    else:
        print("  현재 알림이 없습니다 - 시스템 정상 상태")
    
    print(f"\n💡 4. 최적화 권장사항")
    print("-" * 30)
    
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n🎯 5. 주요 기능 요약")
    print("-" * 30)
    print("  ✅ 실시간 메트릭 수집 (CPU, 메모리, GPU, 전력, 비용)")
    print("  ✅ 자동 알림 시스템 (11가지 규칙)")
    print("  ✅ 실시간 대시보드")
    print("  ✅ 헬스 및 효율성 스코어")
    print("  ✅ 최적화 권장사항")
    print("  ✅ 히스토리 데이터 저장")
    print("  ✅ 리포트 생성")
    
    print(f"\n🌟 모니터링 시스템 구현 완료!")
    print("=" * 60)

def show_usage_examples():
    """사용법 예시 표시"""
    print(f"\n📖 kcloud-opt 모니터링 시스템 사용법")
    print("=" * 50)
    
    examples = [
        ("실시간 대시보드", "python3 infrastructure/monitoring/integrated_monitor.py --mode dashboard"),
        ("연속 모니터링", "python3 infrastructure/monitoring/integrated_monitor.py --mode continuous --interval 15"),
        ("리포트 생성", "python3 infrastructure/monitoring/integrated_monitor.py --mode report"),
        ("여러 클러스터 모니터링", "python3 infrastructure/monitoring/integrated_monitor.py --clusters cluster1 cluster2 cluster3"),
        ("개별 메트릭 수집", "python3 infrastructure/monitoring/metrics_collector.py"),
        ("알림 시스템 테스트", "python3 infrastructure/monitoring/alert_system.py"),
        ("대시보드만 실행", "python3 infrastructure/monitoring/realtime_dashboard.py --mode dashboard")
    ]
    
    for name, command in examples:
        print(f"\n📌 {name}:")
        print(f"   {command}")
    
    print(f"\n🔧 개발자용 API:")
    print("""
from infrastructure.monitoring.integrated_monitor import IntegratedMonitor

# 모니터 초기화
monitor = IntegratedMonitor()

# 리포트 생성
report = monitor.generate_report(['cluster1', 'cluster2'])

# 연속 모니터링
monitor.run_continuous_monitoring(['cluster1'])
""")

if __name__ == "__main__":
    demo_monitoring_features()
    show_usage_examples()