#!/usr/bin/env python3
"""
kcloud-opt virtual cluster group management
Manage multiple physical clusters as logical groups
"""

import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
sys.path.insert(0, '/root/kcloud_opt/venv/lib/python3.12/site-packages')

from magnumclient import client as magnum_client
from keystoneauth1 import loading, session
import openstack

class VirtualClusterGroup:
    """Virtual cluster group class"""
    
    def __init__(self, name: str, group_type: str, policy: Dict):
        self.name = name
        self.group_type = group_type  # "ml_training", "ai_inference", "mixed"
        self.policy = policy
        self.clusters = []
        self.created_at = datetime.now()
        self.total_nodes = 0
        self.total_cost = 0.0
        
    def add_cluster(self, cluster_info: Dict):
        """Add a cluster to the group"""
        self.clusters.append(cluster_info)
        self.total_nodes += cluster_info.get('node_count', 0)
        self.total_cost += cluster_info.get('hourly_cost', 0)
        
    def remove_cluster(self, cluster_name: str):
        """Remove a cluster from the group"""
        self.clusters = [c for c in self.clusters if c['name'] != cluster_name]
        self._recalculate_totals()
        
    def _recalculate_totals(self):
        """Recalculate aggregated totals"""
        self.total_nodes = sum(c.get('node_count', 0) for c in self.clusters)
        self.total_cost = sum(c.get('hourly_cost', 0) for c in self.clusters)
        
    def get_status(self):
        """Return group status"""
        return {
            'name': self.name,
            'group_type': self.group_type,
            'cluster_count': len(self.clusters),
            'total_nodes': self.total_nodes,
            'total_hourly_cost': self.total_cost,
            'policy': self.policy,
            'clusters': self.clusters,
            'created_at': self.created_at.isoformat()
        }

class VirtualClusterGroupManager:
    """Virtual cluster group manager"""
    
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
        self.virtual_groups = {}  # store virtual groups
        
    def setup_clients(self):
        """Initialize OpenStack clients"""
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**self.auth_config)
        sess = session.Session(auth=auth)
        self.magnum = magnum_client.Client('1', session=sess)
        self.conn = openstack.connect(**self.auth_config)
        print("✅ 가상 클러스터 그룹 관리자 초기화 완료")
    
    def create_virtual_group(self, name: str, group_type: str, policy: Dict) -> VirtualClusterGroup:
        """
        Create a virtual cluster group
        
        Args:
            name: group name
            group_type: "ml_training", "ai_inference", "mixed", "development"
            policy: policy configuration
        """
        print(f"🌐 가상 클러스터 그룹 생성: {name} ({group_type})")
        
        if name in self.virtual_groups:
            print(f"❌ 그룹 '{name}'이 이미 존재합니다")
            return None
            
        group = VirtualClusterGroup(name, group_type, policy)
        self.virtual_groups[name] = group
        
        print(f"✅ 가상 그룹 '{name}' 생성 완료")
        return group
    
    def create_group_with_clusters(self, group_name: str, group_config: Dict) -> VirtualClusterGroup:
        """
        Create a virtual group and clusters together based on configuration
        
        Args:
            group_name: group name
            group_config: group configuration
        """
        print(f"🚀 가상 그룹 '{group_name}' 및 클러스터들 생성 시작")
        
        # create virtual group
        group = self.create_virtual_group(
            group_name,
            group_config['type'],
            group_config['policy']
        )
        
        if not group:
            return None
        
        # create configured clusters
        for cluster_spec in group_config.get('clusters', []):
            cluster_name = f"{group_name}-{cluster_spec['name']}"
            
            print(f"  📦 클러스터 생성 중: {cluster_name}")
            
            # create actual Magnum cluster
            magnum_cluster = self._create_magnum_cluster(
                cluster_name,
                cluster_spec
            )
            
            if magnum_cluster:
                # add cluster information to group
                cluster_info = {
                    'name': cluster_name,
                    'uuid': magnum_cluster.uuid,
                    'template': cluster_spec.get('template', 'ai-k8s-template'),
                    'node_count': cluster_spec.get('node_count', 1),
                    'workload_type': cluster_spec.get('workload_type', 'general'),
                    'hourly_cost': self._estimate_cluster_cost(cluster_spec),
                    'status': 'CREATE_IN_PROGRESS',
                    'created_at': datetime.now().isoformat()
                }
                
                group.add_cluster(cluster_info)
                print(f"    ✅ 클러스터 '{cluster_name}' 그룹에 추가됨")
            else:
                print(f"    ❌ 클러스터 '{cluster_name}' 생성 실패")
        
        print(f"🎉 가상 그룹 '{group_name}' 생성 완료 ({len(group.clusters)}개 클러스터)")
        return group
    
    def _create_magnum_cluster(self, name: str, spec: Dict):
        """Create actual Magnum cluster"""
        try:
            cluster_spec = {
                'name': name,
                'cluster_template_id': spec.get('template', 'ai-k8s-template'),
                'keypair': 'kcloud-keypair',
                'master_count': spec.get('master_count', 1),
                'node_count': spec.get('node_count', 1),
                'fixed_network': 'cloud-platform-selfservice',
                'fixed_subnet': 'cloud-platform-selfservice-subnet',
                'labels': spec.get('labels', {})
            }
            
            cluster = self.magnum.clusters.create(**cluster_spec)
            return cluster
            
        except Exception as e:
            print(f"❌ Magnum 클러스터 생성 실패: {e}")
            return None
    
    def _estimate_cluster_cost(self, spec: Dict) -> float:
        """Estimate cluster hourly cost"""
        cost_map = {
            'ai-k8s-template': 1.20,  # GPU 노드 포함
            'dev-k8s-template': 0.15,
            'prod-k8s-template': 0.30
        }
        
        base_cost = cost_map.get(spec.get('template', 'dev-k8s-template'), 0.15)
        node_count = spec.get('node_count', 1)
        
        return base_cost * node_count
    
    def scale_group(self, group_name: str, scaling_policy: Dict):
        """그룹 전체 스케일링"""
        if group_name not in self.virtual_groups:
            print(f"❌ 그룹 '{group_name}'을 찾을 수 없음")
            return False
        
        group = self.virtual_groups[group_name]
        print(f"📈 그룹 '{group_name}' 스케일링 시작")
        
        scaling_type = scaling_policy.get('type', 'horizontal')  # horizontal, vertical
        target_nodes = scaling_policy.get('target_total_nodes', group.total_nodes)
        
        if scaling_type == 'horizontal':
            # horizontal scaling: adjust node count
            current_total = sum(c.get('node_count', 0) for c in group.clusters)
            if target_nodes > current_total:
                # scale out
                self._scale_out_group(group, target_nodes - current_total)
            elif target_nodes < current_total:
                # scale in
                self._scale_in_group(group, current_total - target_nodes)
        
        return True
    
    def _scale_out_group(self, group: VirtualClusterGroup, additional_nodes: int):
        """Scale out the group"""
        print(f"📈 스케일 아웃: {additional_nodes}개 노드 추가")
        
        # evenly distribute across existing clusters
        clusters = [c for c in group.clusters if c.get('status') == 'CREATE_COMPLETE']
        if not clusters:
            print("❌ 활성 클러스터가 없어 스케일링 불가")
            return
        
        nodes_per_cluster = additional_nodes // len(clusters)
        remaining_nodes = additional_nodes % len(clusters)
        
        for i, cluster in enumerate(clusters):
            additional_for_this = nodes_per_cluster
            if i < remaining_nodes:
                additional_for_this += 1
            
            if additional_for_this > 0:
                new_count = cluster['node_count'] + additional_for_this
                self._scale_magnum_cluster(cluster['name'], new_count)
                cluster['node_count'] = new_count
        
        group._recalculate_totals()
    
    def _scale_in_group(self, group: VirtualClusterGroup, reduce_nodes: int):
        """그룹 스케일 인"""
        print(f"📉 스케일 인: {reduce_nodes}개 노드 제거")
        
        # remove nodes based on cost efficiency
        clusters = sorted(group.clusters, 
                         key=lambda x: x.get('hourly_cost', 0) / max(x.get('node_count', 1), 1),
                         reverse=True)
        
        remaining_reduce = reduce_nodes
        for cluster in clusters:
            if remaining_reduce <= 0:
                break
                
            current_nodes = cluster['node_count']
            if current_nodes > 1:  # keep at least 1 node
                reduce_from_this = min(remaining_reduce, current_nodes - 1)
                new_count = current_nodes - reduce_from_this
                
                self._scale_magnum_cluster(cluster['name'], new_count)
                cluster['node_count'] = new_count
                remaining_reduce -= reduce_from_this
        
        group._recalculate_totals()
    
    def _scale_magnum_cluster(self, cluster_name: str, new_node_count: int):
        """Scale a Magnum cluster"""
        try:
            cluster = self.magnum.clusters.get(cluster_name)
            update_ops = [{'op': 'replace', 'path': '/node_count', 'value': new_node_count}]
            self.magnum.clusters.update(cluster.uuid, update_ops)
            print(f"  ✅ 클러스터 '{cluster_name}' 노드 수: {new_node_count}")
        except Exception as e:
            print(f"  ❌ 클러스터 '{cluster_name}' 스케일링 실패: {e}")
    
    def get_group_status(self, group_name: str):
        """Return group status"""
        if group_name not in self.virtual_groups:
            return None
        
        group = self.virtual_groups[group_name]
        
        # update actual cluster status
        for cluster_info in group.clusters:
            try:
                magnum_cluster = self.magnum.clusters.get(cluster_info['name'])
                cluster_info['status'] = magnum_cluster.status
                cluster_info['health_status'] = magnum_cluster.health_status
                cluster_info['api_address'] = magnum_cluster.api_address
            except:
                pass
        
        return group.get_status()
    
    def list_virtual_groups(self):
        """List all virtual groups"""
        print(f"📊 가상 클러스터 그룹 목록 ({len(self.virtual_groups)}개)")
        
        for group_name, group in self.virtual_groups.items():
            status = self.get_group_status(group_name)
            active_clusters = len([c for c in status['clusters'] if c.get('status') == 'CREATE_COMPLETE'])
            
            print(f"  🌐 {group_name} ({status['group_type']})")
            print(f"    - 클러스터: {len(status['clusters'])}개 (활성: {active_clusters}개)")
            print(f"    - 노드: {status['total_nodes']}개")
            print(f"    - 시간당 비용: ${status['total_hourly_cost']:.2f}")
    
    def delete_virtual_group(self, group_name: str, delete_clusters: bool = True):
        """가상 그룹 삭제"""
        if group_name not in self.virtual_groups:
            print(f"❌ 그룹 '{group_name}'을 찾을 수 없음")
            return False
        
        group = self.virtual_groups[group_name]
        
        if delete_clusters:
            print(f"🗑️ 그룹 '{group_name}'의 모든 클러스터 삭제 중...")
            for cluster_info in group.clusters:
                try:
                    cluster = self.magnum.clusters.get(cluster_info['name'])
                    self.magnum.clusters.delete(cluster.uuid)
                    print(f"  ✅ 클러스터 '{cluster_info['name']}' 삭제 요청")
                except Exception as e:
                    print(f"  ❌ 클러스터 '{cluster_info['name']}' 삭제 실패: {e}")
        
        del self.virtual_groups[group_name]
        print(f"✅ 가상 그룹 '{group_name}' 삭제 완료")
        return True
    
    def save_groups_config(self, file_path: str = "virtual_groups_config.json"):
        """그룹 설정을 파일로 저장"""
        config = {}
        for name, group in self.virtual_groups.items():
            config[name] = group.get_status()
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"💾 가상 그룹 설정 저장: {file_path}")

def main():
    """사용 예시"""
    manager = VirtualClusterGroupManager()
    
    print("=" * 60)
    print("🌐 kcloud-opt 가상 클러스터 그룹 관리")
    print("=" * 60)
    
    # 예시 1: ML 훈련용 가상 그룹 생성
    ml_training_config = {
        'type': 'ml_training',
        'policy': {
            'auto_scaling': True,
            'cost_optimization': True,
            'max_hourly_cost': 10.0,
            'scaling_metric': 'gpu_utilization'
        },
        'clusters': [
            {
                'name': 'gpu-cluster-1',
                'template': 'ai-k8s-template',
                'node_count': 2,
                'workload_type': 'training',
                'labels': {'gpu_device_plugin': 'true'}
            }
            # 실제로는 여러 클러스터를 정의할 수 있음
        ]
    }
    
    print("\n🚀 ML 훈련용 가상 그룹 생성 예시 (실행하려면 주석 해제):")
    print(f"manager.create_group_with_clusters('ml-training-group', ml_training_config)")
    
    # 예시 2: 개발용 가상 그룹
    dev_config = {
        'type': 'development',
        'policy': {
            'auto_scaling': False,
            'cost_optimization': True,
            'max_hourly_cost': 2.0
        },
        'clusters': []  # 빈 그룹으로 시작
    }
    
    print("\n🛠️ 개발용 가상 그룹 생성 예시:")
    print(f"manager.create_virtual_group('dev-group', 'development', dev_config['policy'])")
    
    # 현재 그룹 목록
    print("\n📊 현재 가상 그룹 목록:")
    manager.list_virtual_groups()
    
    print("\n✅ 가상 클러스터 그룹 관리 예시 완료")

if __name__ == "__main__":
    main()