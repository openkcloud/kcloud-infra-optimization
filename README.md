# Infrastructure Module - Cluster Management

**멀티 클러스터 관리 모듈**

## 📋 주요 기능

### 🌊 Magnum 클러스터 관리
- **클러스터 생성/삭제**: AI 가속기별 전용 클러스터 동적 생성
- **스케일링**: 워크로드 요구사항에 따른 노드 확장/축소
- **클러스터 템플릿**: GPU/NPU/CPU 전용 클러스터 템플릿 관리
- **상태 모니터링**: 클러스터 상태 추적 및 헬스 체크

### 🔧 Heat 템플릿 관리
- **인프라 코드화**: Heat 템플릿을 통한 재현 가능한 인프라 구성
- **자원 정의**: GPU/NPU 노드 타입별 Heat 스택 관리
- **네트워킹**: 클러스터 간 네트워크 격리 및 연결

### ⚡ 워크로드 기반 최적화
- **클러스터 매칭**: 워크로드 특성에 맞는 최적 클러스터 선택
- **자원 할당**: 유휴 자원 최소화를 위한 클러스터 통합/분할
- **비용 최적화**: 사용하지 않는 클러스터 자동 정리

## 🏗 아키텍처

```
kcloud-optimizer → infrastructure → OpenStack Magnum API
    ↓                     ↓              ↓
워크로드 요구사항    클러스터 결정    실제 클러스터 생성/관리
    ↓                     ↓              ↓
core 스케줄러 ← Heat Templates ← Nova/Neutron/Cinder
```

## 🎯 클러스터 타입별 전략

### **GPU-Intensive 클러스터**
- **구성**: NVIDIA GPU 노드 + 고성능 CPU
- **용도**: ML 훈련, 딥러닝 모델 개발
- **최적화**: 전력 효율성 + GPU 활용률

### **NPU-Optimized 클러스터**  
- **구성**: Intel/AMD NPU 노드 + 저전력 CPU
- **용도**: AI 추론, 실시간 처리
- **최적화**: 응답 시간 + 처리량

### **Hybrid-Balanced 클러스터**
- **구성**: GPU + NPU + CPU 혼합
- **용도**: 복합 AI 워크로드
- **최적화**: 자원 활용률 + 유연성

### **CPU-Only 클러스터**
- **구성**: CPU 전용
- **용도**: 일반 서비스, 데이터 처리
- **최적화**: 비용 최소화

## 🚀 핵심 기능

### Magnum 클러스터 생성
```python
# 클러스터 생성 예시
cluster_config = {
    "name": "ml-training-cluster",
    "cluster_template_id": "gpu-intensive-template",
    "node_count": 4,
    "master_count": 1,
    "keypair": "kcloud-keypair",
    "labels": {
        "workload_type": "training",
        "gpu_type": "nvidia-a100",
        "power_optimization": "enabled"
    }
}

cluster = await magnum_client.create_cluster(cluster_config)
```

### 동적 스케일링
```python
# 워크로드 요구사항 기반 스케일링
scaling_decision = await optimizer.analyze_workload_requirements(workloads)

if scaling_decision.action == "scale_out":
    await magnum_client.resize_cluster(
        cluster_id=cluster.id,
        node_count=scaling_decision.target_nodes
    )
```

### Heat 템플릿 관리
```yaml
# GPU 전용 클러스터 템플릿 예시
heat_template_version: wallaby

parameters:
  gpu_flavor: {type: string, default: "gpu.a100.large"}
  gpu_count: {type: number, default: 4}
  network_id: {type: string}

resources:
  gpu_cluster:
    type: OS::Magnum::ClusterTemplate
    properties:
      name: gpu-intensive-template
      coe: kubernetes
      flavor_id: {get_param: gpu_flavor}
      master_flavor_id: "cpu.large"
      volume_driver: cinder
      network_driver: flannel
      labels:
        - "gpu_enabled=true"
        - "power_monitoring=kepler"
```

## 🔧 설정

### OpenStack 연동 설정
```bash
# OpenStack 인증
export OS_AUTH_URL=http://controller:5000/v3
export OS_PROJECT_NAME=kcloud
export OS_USERNAME=admin
export OS_PASSWORD=secretpassword
export OS_REGION_NAME=RegionOne
export OS_IDENTITY_API_VERSION=3

# Magnum 설정
export MAGNUM_API_VERSION=1.15
export MAGNUM_ENDPOINT_TYPE=public

# Heat 설정
export HEAT_API_VERSION=1
```

### 클러스터 템플릿 설정
```yaml
cluster_templates:
  gpu_intensive:
    name: "gpu-intensive-template"
    coe: "kubernetes"
    image: "fedora-atomic-k8s"
    flavor: "gpu.a100.large"
    master_flavor: "cpu.large"
    node_count: 4
    master_count: 1
    volume_driver: "cinder"
    network_driver: "flannel"
    labels:
      gpu_enabled: "true"
      power_monitoring: "kepler"
      workload_type: "training"

  npu_optimized:
    name: "npu-optimized-template"
    coe: "kubernetes"
    image: "fedora-atomic-k8s"
    flavor: "npu.intel.medium"
    master_flavor: "cpu.medium"
    node_count: 2
    master_count: 1
    labels:
      npu_enabled: "true"
      workload_type: "inference"
```

## 📊 API 엔드포인트

```bash
# 클러스터 관리
POST /clusters                    # 클러스터 생성
GET /clusters                     # 클러스터 목록
GET /clusters/{cluster_id}        # 클러스터 상세
PUT /clusters/{cluster_id}/scale  # 클러스터 스케일링
DELETE /clusters/{cluster_id}     # 클러스터 삭제

# 클러스터 템플릿 관리  
GET /templates                    # 템플릿 목록
POST /templates                   # 템플릿 생성
GET /templates/{template_id}      # 템플릿 상세

# 워크로드 매칭
POST /match/workload              # 워크로드에 최적 클러스터 추천
GET /clusters/available           # 사용 가능한 클러스터 목록

# 모니터링
GET /clusters/{cluster_id}/status # 클러스터 상태
GET /clusters/{cluster_id}/metrics # 클러스터 메트릭
GET /clusters/{cluster_id}/costs  # 클러스터 비용
```

## 🧪 사용 예시

```python
from infrastructure.magnum_client import MagnumClient
from infrastructure.cluster_manager import ClusterManager

# Magnum 클라이언트 초기화
magnum = MagnumClient(
    auth_url="http://controller:5000/v3",
    project_name="kcloud",
    username="admin",
    password="secretpassword"
)

# 클러스터 매니저 초기화
manager = ClusterManager(magnum_client=magnum)

# 워크로드 요구사항 기반 클러스터 생성
workload_requirements = {
    "type": "ml_training",
    "gpu_required": True,
    "gpu_count": 4,
    "cpu_cores": 32,
    "memory_gb": 128,
    "power_budget": 2000  # watts
}

# 최적 클러스터 추천 및 생성
cluster = await manager.create_optimal_cluster(workload_requirements)
print(f"클러스터 생성 완료: {cluster.name} ({cluster.id})")

# 워크로드 배포 후 모니터링
status = await manager.get_cluster_status(cluster.id)
print(f"클러스터 상태: {status.phase}, 노드: {status.node_count}")
```

## 🚀 배포

```bash
# 로컬 개발
make install
make test
make run

# OpenStack 환경 설정 확인
make verify-openstack

# Docker 실행  
make docker-build
make docker-run

# K8s 배포
kubectl apply -f deployment/infrastructure.yaml
```

## 🔒 보안

- **OpenStack 인증**: Keystone을 통한 안전한 API 인증
- **RBAC**: 클러스터별 역할 기반 접근 제어
- **네트워크 격리**: Neutron을 통한 클러스터 간 네트워크 분리
- **시크릿 관리**: 클러스터 인증서 및 키 보안 저장
