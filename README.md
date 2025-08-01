# DZPJT_Final
생성형 AI 기반 ICT 솔루션 Expert 서비스 개발
### 프로젝트 개요

- **목표:**
    
    교사의 반복적인 행정/문서 업무를 자연어로 요청해 자동 처리하는 AI 챗봇 개발
    
- **핵심 기능:**
    
    가정통신문, 상담일지, 회의록, 시험지 등 다양한 문서 생성/요약
    
- **특징:**
    
    기존 시스템(클래스팅/나이스 등)의 한계 보완
    
    대화형 UI로 실제 학교 현장 시나리오에 맞는 업무 지원


---

## Git 커밋명 규칙
```
- **Feat : 신규 기능 추가**
- **Fix : 버그 수정 **
- Build : 빌드 관련 파일 수정
- Chore : 기타 수정
- Ci : 지속적 개발에 따른 수정
- Docs : 문서 수정
- Style : 코드 스타일, 포멧형식 관련
- Refactor : 리팩토링
- Test : 테스트 코드 수정
```

---

## 터미널 기본 설정(3개의 터미널을 통한 작업 추천)

> git
>> git bash  
>> git switch를 통해 개인 브랜치로 이동  
>> git 관련 커맨드 입력용도
>
> front
>> cmd  
>> 루트 디렉토리에서 cd frontend  
>> 프론트 실행용  
>
> back
>> cmd  
>> 루트 디렉토리에서 cd backend  
>> 백엔드 실행용
>
> 위와 같이 3개의 터미널을 통한 작업 추천
 
---

## 프론트 실행 커맨드
```
1. 터미널에서 cd frontend로 이동하여 npm ins
2. npm start
```
---

## 서버 실행/점검 커멘드
```
1. 터미널에서 cd backend로 이동
2. python -m venv myenv                 // 가상환경 생성
3. myenv\Scripts\activate               // 가상환경 실행
4. pip install -r requirements.txt      // fastapi 패키지 설치 1회만 실행
5. uvicorn main:app --reload            // fastapi 실행

초기 설정 이후에는
1. cd backend
2. myenv\Scripts\activate
3. uvicorn main:app --reload
```

---


## 주의사항
> .env에는 gpt의 api-key 유출 방지로 Git 예외처리를 하여 수동으로 다운로드해줘야함  
> 중요 key가 있다면 유출되지 않도록 주의!  

---

## 각 branch 용도
> ### main(*중요, 메인 브랜치치)
>> 메인 branch  
>> main에 대한 모든 업데이트는 **test에서 먼저 시도**하여 이상이 없을 시에 **팀원 모두의 동의**를 구하고한다.
>
> ### test
>> 각자의 개인 branch에서의 업데이트를 먼저 테스트 해보는 곳.
>
> ### backup
>> 만일의 사태를 대비한 백업용 branch  
>> main이나 test에서 이상이 없다면 주기적으로 백업해두자
>
> ### khg
>> 권혁광 개인 branch
>
> ### nyj
>> 나용주 개인 branch
> 
> ### ndh
>> 나대현 개인 branch
>
> ### jsj
>> 정수정 개인 branch
>
> ### psj
>> 박성주 개인 branch

---

## 초기 설정
> 패키지 설치
>> pip install -r requirements.txt  

## Git 초기설정.
>터미널/cmd/git bash에서 프로젝트를 저장할 위치로 이동 후 아래 코드 입력
>> git clone https://github.com/DouzonFinal-Project/dzpjt_final.git
> vscode에서 해당 프로젝트를 폴더 열기  
> vscode의 터미널에서 아래 코드 입력
>> git switch test  
>> git switch -c [원하는 개인 branch명]  
>
> 좌측 소스 제어(깃)에서 [게시 Branch] 버튼 클릭
> 
> 아래 코드를 입력하여 각 branch가 제대로 추가되었는지 확인  
>> git branch -r
>



---

## GIT 명령어 모음
> branch 새로 생성 후 해당 branch로 즉시 전환
>> git switch -c [branch명]
>
> 로컬(개인컴) branch 목록 조회(*로 강조된 곳이 현재 branch)
>> git branch
>
> 원격(깃허브) branch 목록 조회(*로 강조된 곳이 현재 branch)
>> git branch -r
>
> branch 전환 코드 2가지(최근에는 switch를 더 자주 사용한다고함. checkout은 참고용)
>> git switch [branch명]
>> git checkout [branch명]
>
> branch 병합하기(현재 branch를 대상으로 명령어의 branch를 덮어씌우는 느낌)
>> git merge [branch명]
>
> 해당 커밋의 수정사항'만' 취소하고 새로 커밋하는 명령어
>> git revert <되돌리고 싶은 커밋 id>  
>> ```코드 입력 시 터미널에 이상한 코드가(vi이라고 .txt랑 비슷한 느낌)가 나오면 esc > :q 입력 > 엔터 누르고 깃헙에 푸쉬하면 적용완료```
>
> 병합 도중 병합하기 전으로 되돌리고 싶을 때  
>> git merge --abort  



---
