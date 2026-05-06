# 미션 컴퓨터 모니터링

문제 8, 문제 9에서 사용하는 미션 컴퓨터 시스템 정보 조회 및 모니터링 프로그램입니다.

문제 7에서 만든 `MissionComputer`와 `DummySensor` 구조를 기반으로,  
미션 컴퓨터의 시스템 정보, 실시간 부하, 화성 기지 환경 데이터를 지속적으로 출력합니다.

---

## 📁 문제 파일 위치

```text
ia-codyssey/
├── required/
│   └── stage1/
│       └── problem8/
│           ├── dummy_sensor.py
│           ├── mission_computer.py
│           ├── mars_mission_computer.py
│           ├── setting.txt
│           ├── computer_info.txt
│           └── env_log.csv
```

## 📌 포함 문제

### 문제 8 — 불안정한 미션 컴퓨터

미션 컴퓨터의 시스템 정보를 확인하는 기능을 구현합니다.

- 운영체계
- 운영체계 버전
- CPU 타입
- CPU 코어 수
- 메모리 크기
- CPU 실시간 사용량
- 메모리 실시간 사용량

시스템 정보와 부하 정보는 JSON 형식으로 출력됩니다.

---

### 문제 9 — 미션 컴퓨터 모니터링

문제 8에서 만든 시스템 정보 조회 기능을 20초마다 반복 출력하고,

센서 데이터 출력 기능과 함께 멀티스레드 및 멀티프로세스로 실행합니다.

---

## 🧩 파일 설명

| 파일 | 설명 |
| --- | --- |
| `dummy_sensor.py` | 화성 기지 환경 데이터를 랜덤으로 생성하는 더미 센서 클래스 |
| `mission_computer.py` | `MissionComputer` 클래스와 시스템 정보/부하/센서 데이터 출력 로직 |
| `mars_mission_computer.py` | 프로그램 실행 진입점 |
| `setting.txt` | 출력할 시스템 정보 및 부하 정보 항목 설정 파일 |
| `computer_info.txt` | 시스템 정보 출력 결과 저장 파일 |
| `env_log.csv` | 센서 환경 데이터 로그 파일 |

---

## ⚙️ 주요 기능

### 1. 시스템 정보 출력

`get_mission_computer_info()` 메서드는 다음 정보를 가져와 JSON 형식으로 출력합니다.

- `os`
- `os_version`
- `cpu_type`
- `cpu_cores`
- `memory_total`

출력 결과는 `computer_info.txt`에도 저장됩니다.

---

### 2. 시스템 부하 출력

`get_mission_computer_load()` 메서드는 다음 정보를 가져와 JSON 형식으로 출력합니다.

- `cpu_usage_percent`
- `memory_usage_percent`

---

### 3. 센서 데이터 출력

`get_sensor_data()` 메서드는 `DummySensor`에서 환경 데이터를 가져와 `env_values`에 저장하고 JSON 형식으로 출력합니다.

출력되는 환경 정보는 다음과 같습니다.

- `mars_base_internal_temperature`
- `mars_base_external_temperature`
- `mars_base_internal_humidity`
- `mars_base_external_illuminance`
- `mars_base_internal_co2`
- `mars_base_internal_oxygen`

---

### 4. 20초 반복 출력

문제 9 조건에 따라 아래 두 메서드는 20초마다 반복 출력됩니다.

- `get_mission_computer_info()`
- `get_mission_computer_load()`

센서 데이터는 5초마다 반복 출력됩니다.

---

### 5. 멀티스레드 실행

기본 실행 모드는 멀티스레드입니다.

하나의 `MissionComputer` 인스턴스를 생성한 뒤, 아래 메서드를 각각 별도 스레드로 실행합니다.

- `get_mission_computer_info()`
- `get_mission_computer_load()`
- `get_sensor_data()`

실행:

```
python mars_mission_computer.py
```

또는

```
python mars_mission_computer.py thread
```

---

### 6. 멀티프로세스 실행

멀티프로세스 모드에서는 `MissionComputer` 인스턴스를 각각 생성합니다.

- `runComputer1` → 시스템 정보 출력
- `runComputer2` → 시스템 부하 출력
- `runComputer3` → 센서 데이터 출력

실행:

```
python mars_mission_computer.py process
```

---

## 🛑 종료 방법

프로그램 실행 중 아래 값을 입력하면 반복 출력이 중단됩니다.

```
q
```

입력 후 Enter를 누르면 모든 모니터링 작업이 종료됩니다.

---

## 📝 setting.txt

`setting.txt` 파일을 수정하면 출력할 시스템 정보 항목을 설정할 수 있습니다.

기본 설정 예시는 다음과 같습니다.

```
os
os_version
cpu_type
cpu_cores
memory_total
cpu_usage_percent
memory_usage_percent
```

---

## 📊 5분 평균값 출력

센서 데이터는 5초마다 수집됩니다.

60회 수집이 완료되면 다음 계산에 따라 5분 평균값을 출력합니다.

```
5초 × 60회 = 300초 = 5분
```

평균 출력 후 누적된 센서 기록은 초기화됩니다.

---

## 🧪 실행 예시

### 멀티스레드 모드

```
python mars_mission_computer.py
```

### 멀티프로세스 모드

```
python mars_mission_computer.py process
```

---

## 📚 사용 라이브러리

| 라이브러리 | 구분 | 사용 목적 |
| --- | --- | --- |
| `time` | Python 기본 제공 | 반복 대기 시간 처리 |
| `datetime` | Python 기본 제공 | 출력 시각 기록 |
| `platform` | Python 기본 제공 | 운영체제 및 CPU 정보 조회 |
| `threading` | Python 기본 제공 | 멀티스레드 실행 |
| `multiprocessing` | Python 기본 제공 | 멀티프로세스 실행 |
| `sys` | Python 기본 제공 | 실행 모드 인자 처리 |
| `psutil` | 외부 라이브러리 | CPU/메모리 정보 조회 |

> 문제 8 조건에서 시스템 정보를 가져오는 부분은 별도 라이브러리 사용이 허용되므로 `psutil`을 사용했습니다.
> 

---

## ✅ 구현 조건 체크

### 문제 8

- `MissionComputer` 클래스에 `get_mission_computer_info()` 추가
- 운영체계, 운영체계 버전, CPU 타입, CPU 코어 수, 메모리 크기 출력
- `get_mission_computer_load()` 추가
- CPU 실시간 사용량, 메모리 실시간 사용량 출력
- JSON 형식 출력
- 시스템 정보 조회 부분 예외 처리
- `setting.txt`를 통한 출력 항목 설정

### 문제 9

- 시스템 정보와 부하 정보를 20초마다 반복 출력
- `runComputer` 인스턴스 생성
- `get_mission_computer_info()`, `get_mission_computer_load()`, `get_sensor_data()` 멀티스레드 실행
- `runComputer1`, `runComputer2`, `runComputer3` 인스턴스 생성
- 각 인스턴스를 멀티프로세스로 실행
- `q` 입력 시 반복 출력 중단