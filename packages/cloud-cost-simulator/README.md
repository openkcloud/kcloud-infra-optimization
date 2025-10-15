# kcloud-opt-simulator

AI반도체 워크로드 운용 비용 효율 시뮬레이터 (Python)

## 개요

kcloud-opt-simulator는 AI반도체 클라우드 서비스의 운용 비용 효율성을 분석하고 예측하기 위한 시뮬레이션 엔진입니다. 다양한 워크로드 시나리오를 생성하고, 비용 절감 효과를 사전 분석하여 최적화 전략의 유효성을 검증합니다.

## 주요 기능

### 시나리오 기반 시뮬레이션
- **워크로드 생성기**: 다양한 AI 워크로드 패턴 자동 생성
- **시나리오 러너**: 복수 시나리오 병렬 실행
- **상황별 분석**: 피크/오프피크, 계절성, 이벤트 기반 시나리오

### 비용 효율 계산
- **비용 절감 분석**: 최적화 전후 비용 비교 분석
- **ROI 계산**: 최적화 투자 대비 수익 계산
- **민감도 분석**: 주요 변수 변화에 따른 비용 영향도 분석

### 성능 벤치마킹
- **처리량 분석**: 다양한 구성에서의 워크로드 처리 성능
- **지연시간 분석**: 스케줄링 정책별 응답시간 분석
- **확장성 테스트**: 워크로드 증가에 따른 시스템 확장성

## 아키텍처

```
simulator/
├── src/
│   ├── simulator/          # 시뮬레이션 엔진
│   ├── scenario_generator/ # 시나리오 생성기
│   ├── workload_generator/ # 워크로드 생성기
│   ├── cost_calculator/    # 비용 계산기
│   ├── analysis/           # 결과 분석
│   └── visualization/      # 결과 시각화
├── scenarios/              # 시뮬레이션 시나리오
├── config.yaml            # 설정 파일
├── notebooks/             # Jupyter 분석 노트북
└── tests/                 # 테스트
```

## 설치 및 실행

### 개발 환경

```bash
# 가상환경 생성 및 의존성 설치
make install

# Jupyter 확장 설치 (분석용)
pip install jupyterlab plotly dash

# 설정 파일 복사
cp config.example.yaml config.yaml

# 시뮬레이션 실행
make run
```

### Docker

```bash
# 이미지 빌드
make docker-build

# 시뮬레이터 실행
docker run -v $(pwd)/scenarios:/app/scenarios kcloud-opt/simulator:latest
```

## 설정

### 시뮬레이션 설정 (config.yaml)

```yaml
simulator:
  # 시뮬레이션 기본 설정
  duration_days: 30
  time_step_minutes: 5
  parallel_scenarios: 4
  output_format: ["json", "csv", "plot"]
  
  # 비용 모델 설정
  cost_model:
    cpu_cost_per_core_hour: 0.05
    memory_cost_per_gb_hour: 0.01
    gpu_cost_per_hour: 0.50
    npu_cost_per_hour: 0.40
    power_cost_per_kwh: 0.10
    spot_discount: 0.7
  
  # 워크로드 생성기 설정
  workload_generator:
    types: ["training", "inference", "serving"]
    arrival_patterns: ["poisson", "burst", "periodic"]
    resource_distributions: ["normal", "lognormal", "uniform"]
    
  # 성능 모델 설정
  performance_model:
    base_latency_ms: 10
    cpu_scaling_factor: 0.8
    memory_scaling_factor: 0.6
    gpu_acceleration_factor: 5.0
    npu_acceleration_factor: 4.0
```

## 시나리오 정의

### 1. 기본 시나리오 템플릿

```yaml
# scenarios/ml_training_baseline.yaml
name: "ML Training Baseline"
description: "Standard ML training workload simulation"

parameters:
  simulation_duration: "7d"
  workload_count: 100
  
workloads:
  - type: "training"
    count: 60
    resources:
      cpu_cores: 
        distribution: "normal"
        mean: 16
        std: 4
      memory_gb:
        distribution: "normal" 
        mean: 64
        std: 16
      gpu_count:
        distribution: "uniform"
        min: 2
        max: 8
    duration:
      distribution: "lognormal"
      mean: 4  # hours
      std: 2
    arrival_pattern:
      type: "poisson"
      rate: 0.5  # workloads per hour

infrastructure:
  nodes:
    - type: "cpu_node"
      count: 20
      specs:
        cpu_cores: 64
        memory_gb: 256
        cost_per_hour: 3.20
    - type: "gpu_node"
      count: 10
      specs:
        cpu_cores: 32
        memory_gb: 256
        gpu_count: 8
        cost_per_hour: 12.80

optimization_policies:
  - name: "cost_aware"
    enabled: true
    parameters:
      cost_weight: 0.6
      performance_weight: 0.4
```

### 2. 비교 분석 시나리오

```yaml
# scenarios/optimization_comparison.yaml
name: "Optimization Strategy Comparison"
description: "Compare different optimization strategies"

scenarios:
  - name: "no_optimization"
    scheduling_policy: "first_fit"
    optimization: false
    
  - name: "cost_optimization"
    scheduling_policy: "cost_aware" 
    optimization: true
    cost_weight: 0.8
    
  - name: "balanced_optimization"
    scheduling_policy: "cost_aware"
    optimization: true
    cost_weight: 0.5
    performance_weight: 0.5
    
  - name: "performance_first"
    scheduling_policy: "performance_aware"
    optimization: true
    performance_weight: 0.8

metrics:
  - total_cost
  - average_latency
  - resource_utilization
  - sla_violations
```

## 시뮬레이션 실행

### 1. 단일 시나리오 실행

```bash
# 시나리오 실행
python -m src.simulator.run scenarios/ml_training_baseline.yaml

# 결과 확인
ls results/ml_training_baseline/
# - summary.json
# - metrics.csv
# - cost_analysis.png
# - utilization_plot.png
```

### 2. 배치 시뮬레이션

```bash
# 여러 시나리오 병렬 실행
python -m src.simulator.batch_run scenarios/*.yaml

# 비교 분석 리포트 생성
python -m src.analysis.comparative_report results/
```

### 3. 대화형 분석

```bash
# Jupyter Lab 시작
jupyter lab notebooks/

# 또는 Dash 대시보드
python -m src.visualization.dashboard
# 브라우저에서 http://localhost:8050 접속
```

## 분석 결과

### 비용 분석 출력

```json
{
  "scenario": "ml_training_baseline",
  "summary": {
    "total_cost": 15420.50,
    "average_hourly_cost": 92.38,
    "cost_breakdown": {
      "compute": 8246.20,
      "gpu": 6174.30,
      "storage": 580.00,
      "network": 420.00
    }
  },
  "optimization_results": {
    "potential_savings": 2850.75,
    "savings_percentage": 18.5,
    "roi": 4.2,
    "payback_period_days": 87
  },
  "performance_metrics": {
    "average_latency_ms": 145.2,
    "throughput_jobs_per_hour": 24.7,
    "resource_utilization": {
      "cpu": 68.3,
      "memory": 72.1, 
      "gpu": 84.5
    },
    "sla_compliance": 97.2
  }
}
```

### 시각화 결과

```python
# 비용 추이 그래프 생성
from src.visualization import CostAnalyzer

analyzer = CostAnalyzer("results/ml_training_baseline/")
analyzer.plot_cost_trends()
analyzer.plot_resource_utilization()
analyzer.plot_optimization_impact()
```

## 고급 분석 기능

### 1. 몬테카를로 시뮬레이션

```python
# 불확실성을 고려한 비용 분석
from src.analysis import MonteCarloAnalyzer

mc_analyzer = MonteCarloAnalyzer(
    scenarios=["baseline", "optimized"],
    iterations=1000,
    uncertainty_factors={
        "workload_arrival_rate": {"distribution": "normal", "std": 0.2},
        "instance_pricing": {"distribution": "uniform", "variation": 0.1},
        "performance_degradation": {"distribution": "beta", "alpha": 2, "beta": 5}
    }
)

results = mc_analyzer.run_analysis()
confidence_intervals = mc_analyzer.get_confidence_intervals()
```

### 2. 민감도 분석

```python
# 주요 변수의 영향도 분석
from src.analysis import SensitivityAnalyzer

sensitivity = SensitivityAnalyzer()
sensitivity.analyze_parameter_impact(
    parameters=["cpu_cost", "gpu_cost", "optimization_frequency"],
    ranges={
        "cpu_cost": (0.03, 0.08),
        "gpu_cost": (0.30, 0.80), 
        "optimization_frequency": (60, 3600)  # seconds
    }
)
```

### 3. 시나리오 최적화

```python
# 최적 시나리오 탐색
from src.optimization import ScenarioOptimizer

optimizer = ScenarioOptimizer()
optimal_config = optimizer.find_optimal_configuration(
    objective="minimize_cost",
    constraints={
        "max_latency": 200,  # ms
        "min_availability": 99.5,  # %
        "max_power_usage": 5000  # watts
    },
    search_space={
        "node_count": (10, 100),
        "cost_weight": (0.3, 0.9),
        "optimization_interval": (300, 7200)
    }
)
```

## 벤치마킹

### 성능 벤치마크

```bash
# 알고리즘 성능 비교
python -m src.benchmark.algorithm_performance

# 확장성 테스트
python -m src.benchmark.scalability_test \
  --max_workloads 10000 \
  --max_nodes 1000 \
  --step_size 100
```

### 정확도 검증

```bash
# 실제 데이터와 시뮬레이션 결과 비교
python -m src.validation.accuracy_check \
  --real_data data/production_metrics.csv \
  --simulation_results results/validation_scenario/
```

## API 서버

### REST API 실행

```bash
# API 서버 시작
python -m src.api.server

# 시뮬레이션 요청
curl -X POST http://localhost:8004/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d @scenarios/ml_training_baseline.json
```

### WebSocket 실시간 모니터링

```bash
# 실시간 시뮬레이션 모니터링
python -m src.api.websocket_monitor
```

## 개발

### 요구사항

- Python 3.11+
- NumPy, Pandas, SciPy
- Matplotlib, Plotly (시각화)
- Jupyter Lab (분석)

### 커스텀 워크로드 생성기

```python
from src.workload_generator import WorkloadGenerator

class CustomAIWorkloadGenerator(WorkloadGenerator):
    def generate_llm_training(self, model_size="7B"):
        # LLM 학습 워크로드 특성 정의
        if model_size == "7B":
            return {
                "cpu_cores": 32,
                "memory_gb": 256,
                "gpu_count": 8,
                "duration_hours": 72,
                "power_profile": "high_sustained"
            }
    
    def generate_inference_serving(self, requests_per_second=100):
        # 추론 서빙 워크로드 특성 정의
        return {
            "cpu_cores": 8,
            "memory_gb": 32,
            "gpu_count": 1,
            "latency_sla": 50,  # ms
            "scaling_policy": "reactive"
        }
```

### 테스트

```bash
# 단위 테스트
make test

# 시뮬레이션 정확도 테스트
pytest tests/test_simulation_accuracy.py -v

# 성능 테스트
pytest tests/test_performance.py --benchmark-only
```

## 라이선스

Apache License 2.0