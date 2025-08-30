# kcloud-opt-predictor

AI반도체 전력 사용량 예측 및 Auto-scaling 서비스 (Python)

## 개요

kcloud-opt-predictor는 머신러닝을 활용하여 AI반도체 워크로드의 전력 사용량을 예측하고, 예측 결과를 기반으로 Auto-scaling 정책을 적용하는 서비스입니다. 실시간 모니터링 데이터와 고급 시계열 예측 모델을 통해 에너지 효율적인 클라우드 운영을 지원합니다.

## 주요 기능

### 전력 예측
- **LSTM 기반 예측**: 시계열 딥러닝 모델을 통한 전력 사용량 예측
- **다중 특성 분석**: CPU, GPU, NPU, 온도, 워크로드 유형을 고려한 종합 예측
- **실시간 예측**: 스트리밍 데이터 기반 실시간 예측 서비스

### Auto-scaling
- **예측 기반 스케일링**: 예측된 전력 사용량에 따른 사전 예방적 스케일링
- **전력 임계치 관리**: 설정된 전력 예산에 따른 자동 스케일 아웃/인
- **정책 기반 제어**: 에너지 효율성과 성능의 균형을 고려한 스케일링

### 모니터링 통합
- **IPMI/BMC 연동**: 물리 서버의 실시간 전력 데이터 수집
- **GPU 모니터링**: NVIDIA-SMI를 통한 GPU 전력 사용량 추적
- **NPU 모니터링**: Ascend/Kunlun NPU 전력 데이터 수집

## 아키텍처

```
predictor/
├── src/
│   ├── power_predictor/      # 전력 예측 모델
│   ├── data_pipeline/        # 데이터 전처리
│   ├── auto_scaler/          # Auto-scaling 엔진
│   └── api/                  # FastAPI 서버
├── trained_models/           # 학습된 모델 저장소
├── config.yaml              # 설정 파일
└── tests/                   # 테스트
```

## 설치 및 실행

### 개발 환경

```bash
# 가상환경 생성 및 의존성 설치
make install

# 개발 환경 설정 (GPU 지원)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 설정 파일 복사
cp config.example.yaml config.yaml

# 서비스 실행
make run

# API 서버 실행  
make run-api
```

### Docker (GPU 지원)

```bash
# GPU 지원 이미지 빌드
docker build -t kcloud-opt/predictor:gpu -f Dockerfile.gpu .

# GPU 컨테이너 실행
docker run --gpus all -p 8002:8002 kcloud-opt/predictor:gpu
```

## 설정

### 환경변수

- `MODEL_PATH`: 학습된 모델 파일 경로
- `INFLUX_HOST`: InfluxDB 시계열 데이터베이스
- `GPU_MONITORING_ENABLED`: GPU 모니터링 활성화
- `IPMI_HOSTS`: IPMI 모니터링 대상 서버 목록

### 설정 파일 (config.yaml)

```yaml
predictor:
  model_update_interval: 3600
  prediction_horizon: "24h"
  models:
    power_predictor:
      type: "lstm"
      sequence_length: 168  # 1주일
      hidden_size: 128
      batch_size: 32
    cost_predictor:  
      type: "gradient_boosting"
      n_estimators: 100
  features:
    - cpu_utilization
    - memory_usage
    - gpu_utilization
    - npu_utilization
    - temperature
    - workload_type
```

## API 엔드포인트

### 예측 API
- `POST /api/v1/predict/power`: 전력 사용량 예측
- `POST /api/v1/predict/cost`: 운영 비용 예측
- `GET /api/v1/predict/batch/{batch_id}`: 배치 예측 결과 조회

### 모델 관리
- `GET /api/v1/models`: 사용 가능한 모델 목록
- `POST /api/v1/models/retrain`: 모델 재학습 트리거
- `GET /api/v1/models/{model_id}/metrics`: 모델 성능 메트릭

### Auto-scaling
- `GET /api/v1/scaling/policies`: 스케일링 정책 조회
- `POST /api/v1/scaling/policies`: 스케일링 정책 생성/수정
- `GET /api/v1/scaling/events`: 스케일링 이벤트 히스토리

## 예측 모델

### LSTM 전력 예측 모델

```python
# 예측 요청 예시
{
  "workload_id": "training-job-001",
  "features": {
    "cpu_utilization": [75.2, 78.1, 82.3],
    "gpu_utilization": [92.1, 94.5, 91.8],
    "temperature": [65.2, 67.1, 68.5]
  },
  "prediction_horizon": "1h"
}

# 예측 응답
{
  "workload_id": "training-job-001",
  "predictions": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "predicted_power": 1250.5,
      "confidence": 0.85
    }
  ],
  "total_predicted_power": 1250.5,
  "model_version": "v1.2.3"
}
```

### Gradient Boosting 비용 예측

```python
# 비용 예측 요청
{
  "resources": {
    "cpu_cores": 16,
    "memory_gb": 64,
    "gpu_count": 4
  },
  "duration_hours": 8,
  "spot_instance": true
}

# 응답
{
  "predicted_cost": 45.20,
  "cost_breakdown": {
    "compute": 28.80,
    "gpu": 14.40,
    "storage": 1.20,
    "network": 0.80
  },
  "confidence": 0.92
}
```

## Auto-scaling 정책

### 전력 기반 스케일링

```yaml
auto_scaling:
  power_based:
    enabled: true
    max_power_budget: 5000  # Watts
    scale_out_threshold: 85  # % of budget
    scale_in_threshold: 60
    cooldown_period: 300  # seconds
  
  predictive_scaling:
    enabled: true
    lookahead_minutes: 30
    confidence_threshold: 0.8
```

## 개발

### 요구사항

- Python 3.11+
- PyTorch 2.0+
- CUDA 11.8+ (GPU 사용 시)
- InfluxDB 2.0+

### 모델 학습

```bash
# 데이터 전처리
python -m src.data_pipeline.preprocess

# LSTM 모델 학습
python -m src.power_predictor.train_lstm

# Gradient Boosting 모델 학습
python -m src.power_predictor.train_gbm

# 모델 평가
python -m src.power_predictor.evaluate
```

### 테스트

```bash
# 단위 테스트
make test

# 모델 성능 테스트
pytest tests/test_models.py -v

# API 테스트
pytest tests/test_api.py -v
```

## 모니터링

### 모델 성능 메트릭
- **RMSE**: 예측 정확도
- **MAE**: 평균 절대 오차  
- **MAPE**: 평균 절대 백분율 오차
- **예측 지연시간**: 실시간 예측 응답 시간

### 시스템 메트릭
- **GPU 메모리 사용량**
- **모델 추론 시간**
- **데이터 파이프라인 처리량**

## 라이선스

Apache License 2.0