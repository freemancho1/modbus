
# 관련된 Ubunto 명령들

## 포트정보 조회 및 종료
### 포트정보 조회
```text
$ netstat -nap | grep {PORT-NO}
```
### 포트 강제 종료
```text
fuser -k -n tcp {PORT-NO}
```