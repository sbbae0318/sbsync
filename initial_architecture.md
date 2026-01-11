# [설계 문서] Obsidian Cross-Platform Sync Architecture (sbSync)

## 1. 개요

모바일, 개인 PC, 업무용 PC 간의 Obsidian Vault 동기화를 자동화한다. 특히 망 제한이 있는 업무 환경에 최신 데이터를 안전하게 전달하는 것을 목적으로 한다.

## 2. 시스템 아키텍처 구성도

### 2.1 동기화 흐름

1. **Mobile ↔ Personal PC**: `DriveSync`(Android)와 `Google Drive for Desktop`을 통해 실시간 양방향 동기화.
2. **Personal PC ↔ Git Remote**: 24시간 가동되는 Docker 컨테이너 내 `sbSync`(Python 앱)가 변경 사항 감지 후 Git Push.
3. **Git Remote → Work PC**: 업무용 PC에서 `Git Pull`을 통해 데이터 수신 (Read-only).

## 3. 구성 요소 상세

| 구분 | 장치/서비스 | 역할 | 비고 |
| --- | --- | --- | --- |
| **Storage** | Google Drive | 실시간 모바일 동기화 허브 |  |
| **Relay** | Personal PC (Docker) | `sbSync` 실행 및 Git 게이트웨이 | 24시간 구동 |
| **Logic** | sbSync (Python) | 파일 변경 감지 및 자동 Git 커밋/푸시 | `Watchdog` 라이브러리 활용 권장 |
| **Transport** | Git Remote (GitHub/Lab) | 업무망 접근을 위한 저장소 |  |
| **Client** | Work PC | Git Pull을 통한 문서 열람 | Read-only 모드 |

---

## 4. 핵심 검토: Vault와 sbSync 코드의 동일 레포 관리 여부

사용자께서 질문하신 **"동기화 대상 Vault와 sbSync 앱 코드가 동일 레포에 있어도 좋을지"**에 대한 검토 결과입니다.

### **결론: 비권장 (분리하는 것을 강력히 추천)**

두 가지를 분리해야 하는 이유는 다음과 같습니다.

1. **보안 및 데이터 오염 방지**:
* 업무용 PC는 보안 정책상 코드 실행이 제한되거나 모니터링될 수 있습니다. 순수 마크다운(Vault)만 있으면 안전하지만, 실행 파일(Python 앱)이 포함되면 보안 팀의 제재 대상이 될 수 있습니다.


2. **Git 히스토리 관리의 복잡성**:
* Vault는 일기, 메모 등 데이터가 빈번하게 변경됩니다. 앱 코드는 업데이트 주기가 훨씬 깁니다. 두 종류의 데이터가 섞이면 Git 히스토리가 지저분해져 특정 시점의 메모를 복구하거나 앱 버전을 관리하기 어려워집니다.


3. **Docker 컨테이너 효율성**:
* `sbSync` 앱 코드는 Docker 이미지 빌드 시 포함되어야 하지만, Vault 데이터는 **볼륨 마운트(Volume Mount)**를 통해 주입되어야 합니다. 데이터와 로직을 분리해야 컨테이너를 업데이트(Rebuild)해도 데이터 유실 위험이 없습니다.



### **권장 구조**

* **Repo A (sbSync)**: Python 소스 코드, Dockerfile, 설정 파일.
* **Repo B (Obsidian Vault)**: 실제 `.md` 파일 및 이미지 자산.
* **운영 방식**: Docker 컨테이너 실행 시, **Repo A**의 로직이 **Repo B** 경로를 감시하도록 설정.

---

## 5. sbSync 구현을 위한 기술적 제언

* **변경 감지**: 매번 전체 스캔을 하는 대신 `watchdog` 라이브러리를 사용해 파일 시스템 이벤트 발생 시에만 Git 커밋을 수행하도록 하세요.
* **커밋 전략**: 너무 잦은 커밋이 부담된다면 "5분간 변경이 없으면 푸시" 하는 식의 `Debounce` 로직을 넣는 것이 좋습니다.
* **Conflict 방지**: 업무용 PC는 Read-only이므로 문제가 없으나, 혹시 모를 충돌을 방지하기 위해 `git push --force` 보다는 상태 체크 후 푸시하는 로직이 필요합니다.
