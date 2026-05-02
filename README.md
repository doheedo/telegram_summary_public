# tel_suma

텔레그램에서 읽지 않은 메시지를 모아 요약한 뒤, 내 텔레그램 봇에게 하루 요약을 보내는 도구입니다.

개인 텔레그램 계정으로 지정한 채팅방의 최근 메시지를 읽고, NVIDIA 또는 Groq AI 모델로 요약한 다음, 별도로 만든 텔레그램 봇이 나에게 요약문을 보내줍니다.

## 이런 분을 위한 프로젝트입니다

- 텔레그램 단체방을 매번 직접 확인하기 어렵다.
- 특정 채팅방의 최근 대화만 요약해서 받고 싶다.
- 개발자가 아니어도 Windows PC에서 한 번씩 실행해 보고 싶다.
- 나중에 로컬 서버, 윈도우 예약 작업, GitHub Actions 같은 자동 실행도 붙이고 싶다.

## 전체 흐름

1. 텔레그램 봇을 만든다.
2. 텔레그램 개발자 API ID와 API Hash를 받는다.
3. Groq API 키를 준비한다.
4. 이 프로젝트에 필요한 값을 입력해 `.env` 파일을 만든다.
5. 내 텔레그램 계정으로 한 번 로그인한다.
6. 요약할 채팅방을 지정한다.
7. 실행해서 봇으로 요약이 오는지 확인한다.

처음에는 낯선 값이 많지만, 대부분 복사해서 붙여 넣는 작업입니다.

## 준비물

- Windows PC
- Telegram 계정
- Git
- Python 3.12 이상
- Groq API 키
- NVIDIA API 키

Git은 프로젝트를 GitHub에서 내려받을 때 필요합니다. 설치되어 있는지 모르겠다면 PowerShell에서 아래 명령을 실행해 보세요.

```powershell
git --version
```

버전이 나오지 않으면 `https://git-scm.com/download/win`에서 Git for Windows를 설치하세요. 설치 중 선택지는 잘 모르겠다면 기본값으로 진행해도 됩니다.

Python이 설치되어 있는지 모르겠다면 PowerShell에서 아래 명령을 실행해 보세요.

```powershell
py --version
```

버전이 나오지 않으면 Python을 먼저 설치해야 합니다.

## 1. 프로젝트 내려받기

이미 프로젝트 폴더가 있다면 이 단계는 건너뛰어도 됩니다.

GitHub 주소를 알고 있다면 PowerShell에서 원하는 위치로 이동한 뒤 아래처럼 내려받습니다.

```powershell
cd C:\Users\USER\Downloads
git clone <프로젝트 GitHub 주소>
cd tel_suma
```

예를 들어 Codex에게 GitHub 주소를 알려주고 이렇게 요청해도 됩니다.

```text
이 저장소를 내 Downloads 폴더에 git clone 하고, README 순서대로 실행 준비해줘.
```

이미 `C:\Users\USER\Downloads\tel_suma` 폴더가 있다면 PowerShell에서 프로젝트 폴더로 이동합니다.

```powershell
cd C:\Users\USER\Downloads\tel_suma
```

## 2. Python 실행 환경 만들기

프로젝트 안에 `.venv` 폴더가 없다면 아래 명령으로 만듭니다.

```powershell
py -m venv .venv
```

필요한 패키지를 설치합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

이미 설치되어 있다면 다시 실행해도 됩니다.

## 3. 텔레그램 봇 만들기

요약문을 받을 봇을 먼저 만듭니다.

1. 텔레그램에서 `@BotFather`를 검색합니다.
2. `/newbot`을 입력합니다.
3. 봇 이름을 입력합니다. 예: `내 요약 봇`
4. 봇 아이디를 입력합니다. 반드시 `bot`으로 끝나야 합니다. 예: `my_summary_2026_bot`
5. BotFather가 보내주는 토큰을 복사합니다.

토큰은 이런 모양입니다.

```text
<숫자>:<BotFather가 알려준 긴 문자열>
```

이 값이 나중에 `Telegram bot token`입니다. 다른 사람에게 공유하지 마세요.

## 4. 내 봇에게 먼저 메시지 보내기

방금 만든 봇을 텔레그램에서 열고 아무 메시지나 보냅니다.

예:

```text
hello
```

이 과정을 해야 프로그램이 내 개인 채팅 ID를 찾을 수 있습니다.

## 5. 봇 채팅 ID 찾기

PowerShell에서 아래 명령을 실행합니다.

```powershell
powershell -File .\scripts\resolve_bot_chat_id.ps1
```

`Telegram bot token`을 물어보면 BotFather에게 받은 토큰을 붙여 넣습니다.

출력에 나온 개인 채팅 ID를 복사해 둡니다. 이 값이 나중에 `Telegram bot personal chat ID`입니다.

목록이 비어 있다면 봇에게 메시지를 한 번 더 보내고 같은 명령을 다시 실행하세요.

## 6. 텔레그램 API ID와 Hash 받기

이 프로젝트는 봇이 아니라 내 텔레그램 계정으로 채팅방 메시지를 읽습니다. 그래서 텔레그램 개발자 API 값이 필요합니다.

1. 브라우저에서 `https://my.telegram.org`에 접속합니다.
2. 내 텔레그램 전화번호로 로그인합니다.
3. `API development tools`로 들어갑니다.
4. 앱 정보를 입력합니다. 이름은 아무렇게나 적어도 됩니다.
5. 생성된 `api_id`와 `api_hash`를 복사합니다.

나중에 각각 `Telegram API ID`, `Telegram API Hash`에 입력합니다.

## 7. AI 요약 API 키 준비

Groq API 키는 필수입니다.

1. `https://console.groq.com/keys`에 접속합니다.
2. 로그인 후 API 키를 만듭니다.
3. 키를 복사해 둡니다.

NVIDIA API 키도 준비하는 것을 추천합니다. 이 프로젝트는 NVIDIA를 먼저 사용하고, 실패하면 Groq로 넘어가도록 만들어져 있습니다.

NVIDIA API 키 준비:

1. `https://build.nvidia.com/`에 접속합니다.
2. 회원가입 또는 로그인을 합니다.
3. 모델 검색에서 `deepseek-ai/deepseek-v4-pro`를 찾습니다.
4. API 키 생성 메뉴에서 키를 만듭니다.
5. 키를 복사해 둡니다.

설정할 NVIDIA 모델 이름은 아래 값입니다.

```text
deepseek-ai/deepseek-v4-pro
```

키나 모델 이름을 어디에 넣어야 할지 헷갈리면 Codex에게 아래처럼 요청하세요.

```text
README를 보고 NVIDIA API 키를 넣는 위치를 알려줘.
모델은 deepseek-ai/deepseek-v4-pro 로 설정해줘.
```

## 8. 설정 파일 만들기

아래 명령을 실행합니다.

```powershell
powershell -File .\scripts\setup_env.ps1
```

질문이 나오면 준비한 값을 입력합니다.

| 질문 | 입력할 값 |
| --- | --- |
| `Telegram API ID` | my.telegram.org에서 받은 `api_id` |
| `Telegram API Hash` | my.telegram.org에서 받은 `api_hash` |
| `Telegram phone number` | 내 전화번호. 예: `+821012345678` |
| `Telethon session name [tg_session]` | 그냥 Enter |
| `Telegram bot token` | BotFather에게 받은 봇 토큰 |
| `Telegram bot personal chat ID` | 앞에서 찾은 내 봇 채팅 ID |
| `NVIDIA API key` | build.nvidia.com에서 만든 API 키 |
| `NVIDIA model name [deepseek-ai/deepseek-v4-pro]` | 그냥 Enter |
| `Groq API key` | Groq에서 만든 API 키 |
| `Timezone [Asia/Seoul]` | 그냥 Enter |
| `Summary max chars [1000]` | 그냥 Enter |
| `Lookback hours [24]` | 그냥 Enter |
| `Allowed chats` | 요약할 채팅방 주소의 숫자 ID 또는 채팅방 이름을 쉼표로 입력 |

채팅방은 이름보다 숫자 ID로 넣는 것을 추천합니다. 이름은 바뀌거나 똑같은 이름이 여러 개 있으면 헷갈릴 수 있습니다.

숫자 ID를 찾는 쉬운 방법:

1. 브라우저에서 `https://web.telegram.org/a`에 접속합니다.
2. 요약하고 싶은 채팅방을 클릭합니다.
3. 주소창이 `https://web.telegram.org/a/#-0000000000` 같은 모양으로 바뀝니다.
4. `#` 뒤의 값을 복사합니다. `-` 기호도 포함해야 합니다.

예를 들어 주소가 아래와 같다면:

```text
https://web.telegram.org/a/#-1001234567890
```

`Allowed chats`에는 이렇게 넣습니다.

```text
-1001234567890
```

두 채팅방을 요약하려면 쉼표로 구분합니다.

```text
-1001234567890,-1009876543210
```

이 단계가 끝나면 `.env`와 `config/chats.yaml` 파일이 만들어집니다.

직접 확인하고 싶다면 `.env.example` 파일을 참고하세요. 실제 값이 들어간 `.env` 파일은 GitHub에 올리면 안 됩니다.

## 9. 텔레그램 계정 로그인

처음 한 번만 실행합니다.

```powershell
powershell -File .\scripts\bootstrap_login.ps1
```

텔레그램 인증번호나 비밀번호를 물어볼 수 있습니다. 화면 안내에 따라 입력하세요.

성공하면 `tg_session.session` 파일이 만들어집니다. 이 파일은 내 텔레그램 로그인 정보와 관련이 있으니 절대 공유하지 마세요.

## 10. 요약 실행하기

아래 명령을 실행합니다.

```powershell
powershell -File .\scripts\run_daily.ps1
```

정상 동작하면 내 텔레그램 봇이 요약문을 보내줍니다.

요약할 새 메시지가 없으면 내용이 짧거나 비어 보일 수 있습니다.

## Codex에게 맡길 때 준비할 값

이 과정을 직접 하기 어렵다면 Codex에게 실행을 맡기고, 아래 값만 사용자가 직접 붙여 넣는 방식이 가장 편합니다.

- Telegram API ID
- Telegram API Hash
- Telegram 전화번호
- Telegram bot token
- Telegram bot personal chat ID
- NVIDIA API key
- Groq API key
- 요약할 채팅방 ID. 예: `-1001234567890`

Codex에게는 이렇게 요청하면 됩니다.

```text
README 순서대로 이 프로젝트를 로컬에서 실행 준비해줘.
설치, .env 생성, 텔레그램 로그인, 테스트 실행까지 진행하고
내가 직접 입력해야 하는 토큰과 인증번호만 물어봐.
NVIDIA 모델은 deepseek-ai/deepseek-v4-pro 로 설정해줘.
기존 서버 배포 설정이 있다면 건드리지 마.
```

Codex가 물어보는 값에는 토큰과 키를 붙여 넣어도 되지만, GitHub에 커밋하거나 채팅에 그대로 남기는 일은 피하세요.

## 자주 막히는 부분

### 봇 채팅 ID가 안 나와요

봇에게 먼저 메시지를 보내야 합니다. 텔레그램에서 내 봇을 열고 `hello` 같은 메시지를 보낸 뒤 다시 실행하세요.

```powershell
powershell -File .\scripts\resolve_bot_chat_id.ps1
```

### 텔레그램 로그인이 안 돼요

전화번호는 국가번호를 포함해서 입력해야 합니다.

```text
+821012345678
```

2단계 비밀번호를 켜 둔 계정이면 비밀번호도 물어볼 수 있습니다.

### 특정 채팅방이 요약되지 않아요

`config/chats.yaml`에 적은 이름이 실제 텔레그램 채팅방 이름과 다를 수 있습니다. 가능하면 웹 텔레그램 주소에서 숫자 ID를 복사해서 넣으세요.

예:

```yaml
allowed_chats:
  - "-1001234567890"
  - "-1009876543210"
```

웹 텔레그램 주소가 `https://web.telegram.org/a/#-1001234567890`라면 `-1001234567890`처럼 `-`까지 포함해서 넣어야 합니다.

### 토큰이나 키를 GitHub에 올려도 되나요?

안 됩니다. 아래 파일들은 개인 비밀 정보입니다.

- `.env`
- `.env`를 복사해서 만든 파일
- `tg_session.session`
- `*.session`
- `config/chats.yaml`

이 프로젝트의 `.gitignore`에는 이미 제외 설정이 들어 있습니다.

실수로 토큰이나 키를 커밋했다면 파일만 지우는 것으로는 부족합니다. 이미 Git 이력에 남았을 수 있으니 Telegram bot token, Groq API key, NVIDIA API key를 새로 발급하고 기존 키는 폐기하세요.

### NVIDIA 모델은 무엇으로 설정하나요?

아래 값으로 설정하세요.

```text
deepseek-ai/deepseek-v4-pro
```

`setup_env.ps1`에서 `NVIDIA model name [deepseek-ai/deepseek-v4-pro]`라고 나오면 그냥 Enter를 눌러도 이 값이 들어갑니다.

## 매일 자동 실행하기

Windows에서 매일 같은 시간에 실행하려면 아래 명령을 사용할 수 있습니다.

```powershell
powershell -File .\scripts\install_daily_task.ps1
```

기본 작업 이름은 `tel_suma_daily`이고, 기본 실행 시간은 `11:30`입니다.

## 로컬 서버나 GitHub Actions로 자동화하고 싶다면

처음 사용하는 분이라면 직접 설정을 바꾸기보다 Codex에게 맡기는 편이 안전합니다.

예를 들어 Codex에 이렇게 요청하세요.

```text
이 프로젝트를 로컬 서버에서 매일 실행되게 만들어줘.
단, .env와 tg_session.session은 Git에 올리지 않게 해줘.
```

또는 GitHub Actions로 실행하고 싶다면 이렇게 요청하세요.

```text
이 프로젝트를 GitHub Actions로 매일 실행되게 만들어줘.
필요한 Secrets 목록과 등록 방법도 README에 추가해줘.
```

주의할 점:

- `.env` 값은 GitHub Secrets에 넣어야 합니다.
- 텔레그램 세션 파일은 민감한 로그인 파일입니다.
- GitHub Actions에서 텔레그램 개인 계정 세션을 다루는 방식은 보안 검토가 필요합니다.
- 자동화 전에 로컬에서 `run_daily.ps1`이 먼저 성공해야 합니다.
- 이미 서버에서 돌리고 있다면 Codex에게 "기존 배포 파일과 서버 설정은 수정하지 말라"고 명시하세요.

## 현재 요약 모델 순서

기본 순서는 다음과 같습니다.

1. NVIDIA API 키가 있으면 NVIDIA 모델을 먼저 사용합니다.
2. NVIDIA 호출이 실패하면 Groq로 넘어갑니다.
3. NVIDIA API 키가 없으면 Groq만 사용합니다.

현재 기본 모델:

- NVIDIA: `deepseek-ai/deepseek-v4-pro`
- Groq: `llama-3.1-8b-instant`

## 참고

요약 프롬프트의 화자 표시 방식은 [Hacker1337/tg_messages_summarizer](https://github.com/Hacker1337/tg_messages_summarizer)의 아이디어를 참고했습니다. 이 프로젝트는 Telethon과 NVIDIA/Groq API를 사용합니다.
