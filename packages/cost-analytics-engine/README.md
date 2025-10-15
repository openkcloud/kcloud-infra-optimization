# kcloud-opt-analyzer

AI반도체 워크로드 분석 및 비용 모델링 서비스 (Python)

## 개요

kcloud-opt-analyzer는 AI반도체 클라우드 서비스의 워크로드 특성 분석과 비용 모델링을 담당합니다. OpenStack 환경에서 수집된 데이터를 기반으로 워크로드 패턴 분류, 자원 사용량 분석, 비용 산출 모델을 제공합니다.

## 주요 기능

### 워크로드 분석
- **자원 프로파일링**: CPU, Memory, GPU, NPU 사용 패턴 분석
- **에너지 프로파일링**: 전력 사용량 패턴 분석 및 분류
- **워크로드 분류**: Training, Inference, Serving 유형별 특성 분석

### 비용 모델링
- **실시간 비용 산출**: 시간별/인스턴스별 운용 비용 계산
- **예측 모델**: 머신러닝 기반 비용 예측
- **최적화 권장**: 비용 절감 방안 제안

### 데이터 수집
- **OpenStack 메트릭**: Nova, Neutron, Cinder 사용량
- **Prometheus 연동**: 실시간 메트릭 수집
- **IPMI/BMC**: 물리 서버 전력 데이터

## 아키텍처

```
analyzer/
├── src/
│   ├── workload_analyzer/    # 워크로드 특성 분석
│   ├── cost_model/          # 비용 산출 모델
│   ├── metrics_collector/   # 메트릭 수집
│   └── api/                # FastAPI 서버
├── models/                 # ML 모델 저장소
├── config.yaml            # 설정 파일
└── tests/                 # 테스트
```

## 설치 및 실행

### 개발 환경

```bash
# 가상환경 생성 및 의존성 설치
make install

# 개발 환경 설정
make dev

# 설정 파일 복사
cp config.example.yaml config.yaml
# config.yaml 편집

# 서비스 실행
make run

# API 서버 실행
make run-api
```

### Docker

```bash
# 이미지 빌드
make docker-build

# 컨테이너 실행
make docker-run
```

## 설정

### 환경변수

- `DB_HOST`: PostgreSQL 데이터베이스 호스트
- `REDIS_HOST`: Redis 캐시 서버
- `INFLUX_HOST`: InfluxDB 시계열 데이터베이스
- `OPENSTACK_AUTH_URL`: OpenStack 인증 URL

### 설정 파일 (config.yaml)

```yaml
analyzer:
  collection_interval: 30
  metrics_retention_days: 90
  models:
    cost_model:
      type: "linear_regression" 
      retrain_interval: "24h"
    workload_classifier:
      type: "random_forest"
      retrain_interval: "12h"
```

## API 엔드포인트

- `GET /health`: 서비스 상태 확인
- `GET /docs`: API 문서 (Swagger UI)
- `POST /api/v1/analyze`: 워크로드 분석 요청
- `GET /api/v1/cost/{workload_id}`: 비용 조회
- `GET /api/v1/metrics`: 수집된 메트릭 조회
- `POST /api/v1/predict-cost`: 비용 예측 요청

## 데이터 모델

### 워크로드 특성
```python
{
  "workload_id": "training-job-001",
  "type": "training",
  "resources": {
    "cpu_cores": 16,
    "memory_gb": 64,
    "gpu_count": 4,
    "npu_count": 0
  },
  "usage_pattern": {
    "cpu_utilization": 85.2,
    "memory_utilization": 78.1,
    "gpu_utilization": 92.3
  }
}
```

### 비용 데이터
```python
{
  "timestamp": "2024-01-01T10:00:00Z",
  "workload_id": "training-job-001", 
  "cost_per_hour": 12.50,
  "cost_breakdown": {
    "compute": 8.00,
    "gpu": 4.00,
    "storage": 0.30,
    "network": 0.20
  }
}
```

## 개발

### 요구사항

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- InfluxDB 2.0+

### 테스트

```bash
# 단위 테스트
make test

# 커버리지 테스트  
pytest --cov=src --cov-report=html

# 린팅
make lint

# 포맷팅
make format
```

### 모델 재학습

```bash
# 비용 모델 재학습
python -m src.cost_model.train

# 워크로드 분류 모델 재학습
python -m src.workload_analyzer.train
```

## 모니터링

- **Prometheus 메트릭**: `/metrics` 엔드포인트
- **로그**: JSON 형태 구조화 로그
- **대시보드**: Grafana 대시보드 제공

## 라이선스

Apache License 2.0