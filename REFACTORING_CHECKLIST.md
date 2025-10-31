# 리팩토링 및 수정 체크리스트

기능 변경 없이 코드 품질 개선 및 문제점 수정을 위한 목록입니다.

## 🔴 긴급 (Critical) - 보안 및 안정성 문제

### 1. 하드코딩된 인증 정보 제거
**파일:** 
- `virtual_cluster_group_manager.py` (65-66줄)
- `virtual_cluster_monitoring.py` (64-65줄)

**문제:** 하드코딩된 username/password가 코드에 직접 포함됨
```python
'username': 'admin',
'password': 'ketilinux',
```

**수정 방법:** 환경 변수 또는 설정 파일로 이동
- `os.getenv()` 사용
- `python-dotenv` 또는 `pydantic-settings` 활용

### 2. sys.path.insert 하드코딩 경로 제거
**파일:** 14개 파일에서 발견
- `virtual_cluster_group_manager.py:12`
- `virtual_cluster_monitoring.py:15`
- `monitoring_dashboard.py:11`
- `database/connection.py:16`
- 기타 monitoring 폴더 내 다수 파일

**문제:** 절대 경로 하드코딩 (`/root/kcloud_opt/venv/lib/python3.12/site-packages`)

**수정 방법:**
- `PYTHONPATH` 환경 변수 사용
- 상대 import 경로 사용
- `setup.py` 또는 `pyproject.toml`로 패키지 설치

### 3. 전역 변수 사용 (cluster_api.py)
**파일:** `cluster_api.py:40`
```python
crud_controller = None  # 전역 변수
```

**문제:** 전역 상태는 테스트 및 확장성에 문제

**수정 방법:**
- FastAPI의 dependency injection 사용
- `Depends()` 활용하여 의존성 주입

## 🟡 중요 (High) - 코드 품질 및 유지보수성

### 4. 중복된 OpenStack 연결 설정
**파일:**
- `virtual_cluster_group_manager.py:63-70`
- `virtual_cluster_monitoring.py:62-69`

**문제:** 동일한 auth_config가 여러 파일에 중복

**수정 방법:**
- 공통 설정 모듈 생성 (`config/openstack_config.py`)
- 싱글톤 패턴 또는 팩토리 패턴 사용

### 5. 예외 처리 개선
**파일:** 전체 파일

**문제:**
- 일반적인 `Exception` catch가 많음
- 구체적인 예외 타입 미사용
- 에러 메시지가 개발자에게만 유용함

**수정 방법:**
- 구체적인 예외 타입 사용 (`ResourceNotFound`, `SDKException`, `ValueError` 등)
- 사용자 친화적인 에러 메시지
- 에러 로깅 강화

**예시:**
```python
# 현재
except Exception as e:
    logger.error(f"Failed: {e}")

# 개선
except ResourceNotFound as e:
    logger.warning(f"Resource not found: {e}")
    raise HTTPException(status_code=404, detail="Cluster not found")
except SDKException as e:
    logger.error(f"OpenStack API error: {e}")
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

### 6. 매직 넘버/문자열 상수화
**파일:** 전체

**문제:**
- 하드코딩된 값들이 여러 곳에 산재
- 예: `"CREATE_COMPLETE"`, `"cloud-platform-selfservice"`, `3600` (타임아웃)

**수정 방법:**
- 상수 모듈 생성 (`constants.py`)
- Enum 클래스 사용

**예시:**
```python
# constants.py
class ClusterStatus:
    CREATE_COMPLETE = "CREATE_COMPLETE"
    CREATE_IN_PROGRESS = "CREATE_IN_PROGRESS"
    # ...

DEFAULT_TIMEOUT = 3600
DEFAULT_NETWORK = "cloud-platform-selfservice"
```

### 7. 타입 힌트 보완
**파일:** 전체

**문제:**
- 일부 함수에 타입 힌트 누락
- `Any` 타입 과도 사용
- 반환 타입 명시 부족

**수정 방법:**
- 모든 함수에 타입 힌트 추가
- `typing` 모듈 활용 (`Optional`, `List`, `Dict`, `Union` 등)
- `mypy`로 타입 체크

### 8. 로깅 설정 일관성
**파일:** 여러 파일

**문제:**
- 각 파일마다 `logging.basicConfig()` 호출
- 로깅 레벨이 파일마다 다름
- 포맷이 일관되지 않음

**수정 방법:**
- 중앙 로깅 설정 모듈 생성 (`config/logging_config.py`)
- `structlog` 또는 `loguru` 같은 구조화된 로깅 사용

### 9. 긴 함수 분해
**파일:**
- `openstack_cluster_crud.py:_wait_for_cluster_status()` - 복잡한 로직
- `cluster_api.py:create_multiple_clusters()` - 중복 코드
- `virtual_cluster_monitoring.py:_collect_advanced_metrics()` - 랜덤 데이터 생성

**문제:**
- 함수가 너무 길고 여러 책임을 가짐
- 테스트하기 어려움

**수정 방법:**
- 단일 책임 원칙 적용
- 작은 함수로 분해
- 재사용 가능한 유틸리티 함수 생성

### 10. Docstring 표준화
**파일:** 전체

**문제:**
- 일부 함수에 docstring 누락
- 포맷이 일관되지 않음 (Google style, NumPy style 혼재)

**수정 방법:**
- Google style docstring으로 통일
- 모든 public 함수/클래스에 docstring 추가
- Args, Returns, Raises 섹션 포함

## 🟢 개선 (Medium) - 코드 스타일 및 모범 사례

### 11. 사용되지 않는 import 제거
**파일:** 여러 파일

**문제:**
- `asyncio`, `json` 등 사용하지 않는 import 존재

**수정 방법:**
- `pylint` 또는 `flake8`로 검사
- `autoflake`로 자동 정리

### 12. 변수명 개선
**파일:** 전체

**문제:**
- 일부 변수명이 모호함 (`sess`, `loader`, `c` 등)
- 약어 사용 (`crud`, `tmpl`)

**수정 방법:**
- 명확하고 설명적인 이름 사용
- PEP 8 네이밍 규칙 준수

### 13. 코드 중복 제거
**파일:**
- `cluster_api.py:create_cluster()`와 `create_multiple_clusters()` 내부 로직
- 비용 계산 로직 (`_estimate_cluster_cost`, `_calculate_cluster_cost`)

**문제:**
- 동일한 로직이 여러 곳에 중복

**수정 방법:**
- 공통 함수 추출
- 클래스 메서드로 리팩토링

### 14. 설정값 하드코딩
**파일:** 전체

**문제:**
- 타임아웃, 간격, 임계값 등이 코드에 하드코딩
- 예: `update_interval=30`, `timeout=3600`, `check_interval=30`

**수정 방법:**
- 설정 파일 또는 환경 변수로 분리
- 기본값은 상수로 정의

### 15. 리스트 컴프리헨션 최적화
**파일:** 여러 파일

**문제:**
- 일부 반복문을 컴프리헨션으로 개선 가능

**예시:**
```python
# 개선 가능
clusters = [c for c in clusters if c.get('status') == 'CREATE_COMPLETE']
```

### 16. 컨텍스트 매니저 사용
**파일:** 
- `openstack_cluster_crud.py` - 리소스 정리
- 데이터베이스 연결 관리

**문제:**
- 일부 리소스가 명시적으로 정리되지 않음

**수정 방법:**
- `with` 문 사용
- 커스텀 컨텍스트 매니저 생성

### 17. TODO 주석 정리
**파일:**
- `cluster_group_orchestrator.py` (412, 446, 451, 456줄)

**문제:**
- TODO 주석이 여러 곳에 남아있음

**수정 방법:**
- TODO를 이슈 트래커로 이동하거나 구현
- 주석에 우선순위와 담당자 추가

### 18. 주석 처리된 코드 제거
**파일:**
- `openstack_cluster_crud.py:545-565`

**문제:**
- 사용되지 않는 주석 처리된 코드

**수정 방법:**
- 주석 처리된 코드 삭제 (버전 관리에 있으므로)

### 19. 테스트 코드 구조화
**파일:**
- 각 파일의 `if __name__ == "__main__":` 블록

**문제:**
- 예제/테스트 코드가 메인 로직과 섞여있음

**수정 방법:**
- 별도의 `examples/` 또는 `tests/` 디렉토리로 분리
- `pytest`로 구조화된 테스트 작성

### 20. 의존성 버전 명시
**파일:**
- `requirements.txt`

**문제:**
- 일부 패키지에 버전 범위만 지정 (>=)
- 호환성 문제 가능성

**수정 방법:**
- 가능하면 정확한 버전 명시
- `pip-tools`로 의존성 고정 (`requirements.in` -> `requirements.txt`)

## 🔵 선택적 (Low) - 편의성 개선

### 21. 설정 검증 추가
**파일:**
- `DatabaseConfig`, 클러스터 설정 등

**문제:**
- 설정값 유효성 검사 부족

**수정 방법:**
- `pydantic` 모델로 설정 관리
- 초기화 시 검증

### 22. 프로퍼티 사용
**파일:**
- 일부 getter 메서드

**문제:**
- 단순 getter를 메서드 대신 프로퍼티로 변경 가능

**수정 방법:**
- `@property` 데코레이터 사용

### 23. Enum 활용 강화
**파일:**
- `cluster_group_orchestrator.py` - GroupType, GroupStatus는 이미 Enum 사용 중
- 다른 파일에서 문자열 비교는 상수로 변경

**수정 방법:**
- 문자열 비교를 Enum 비교로 변경

### 24. 에러 코드 표준화
**파일:**
- `cluster_api.py`

**문제:**
- HTTP 상태 코드가 하드코딩되어 있음

**수정 방법:**
- 상수로 정의 (예: `HTTPStatus.NOT_FOUND`)

### 25. 포맷팅 통일
**파일:** 전체

**문제:**
- 문자열 포맷팅 방식 혼재 (f-string, .format(), % 등)

**수정 방법:**
- f-string으로 통일
- `black` 포맷터 적용

## 📋 우선순위별 작업 계획

### Phase 1: 긴급 (보안)
1. 하드코딩된 인증 정보 제거
2. sys.path 하드코딩 제거
3. 전역 변수 의존성 주입으로 변경

### Phase 2: 중요 (코드 품질)
4. 중복 코드 제거 및 공통 모듈화
5. 예외 처리 개선
6. 상수 모듈 생성
7. 타입 힌트 보완
8. 로깅 설정 통일

### Phase 3: 개선 (스타일)
9. 함수 분해 및 리팩토링
10. Docstring 표준화
11. 불필요한 import/코드 제거
12. 설정값 외부화

### Phase 4: 선택적 (편의성)
13. 테스트 구조화
14. 설정 검증 추가
15. 포맷팅 통일

## 🛠️ 권장 도구

- **Linting**: `flake8`, `pylint`, `mypy`
- **포맷팅**: `black`, `isort`
- **보안**: `bandit`
- **의존성**: `pip-tools`, `pip-audit`
- **테스트**: `pytest`, `pytest-cov`

## 📝 참고사항

- 모든 변경사항은 기능을 변경하지 않고 리팩토링에만 집중
- 변경 전후 동작이 동일한지 확인 필요
- 각 단계마다 테스트 실행 권장

