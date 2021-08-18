
# 관련된 Ubunto 명령들
<br/>

## 실행파일 만들기
###### 아래 내용은 ~/projects/modbus/utils/logs/logviewer.py 기준으로 작성
### STEP 1 - 소스코드에 실행할 인터프리터 추가
###### 최상단에 아래 코드를 추가한다.
###### 추가할 내용: 해당 프로그램이 수행될 가상환경의 python 실행파일
```python
#!/home/freeman/anaconda3/envs/modbus/bin/python
import os, sys
...
```
### STEP 2 - 해당 파일을 실행파일로 만듬.
```text
$ cd ~/projects/modbus/utils/logs
$ chmod +x logviewer.py
```
### STEP 3 - $PATH의 경로중 적당한 경로를 골라 링크 생성
###### 여기서는 ~/.local/bin 경로를 선택함
```text
$ ln -s ~/projects/modbus/utils/logs/logviewer.py ~/.local/bin/logviewer
```
###### 이렇게 하면 아무곳에서나 logviewer를 실행할 수 있음.

<br/>

## 포트정보 조회 및 종료
### 포트정보 조회
```text
$ netstat -nap | grep {PORT-NO}
```
### 포트 강제 종료
```text
fuser -k -n tcp {PORT-NO}
```