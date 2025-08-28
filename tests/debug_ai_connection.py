import requests
import socket
import subprocess
import platform
from datetime import datetime

def test_network_connectivity():
    """네트워크 연결 상태 진단"""
    
    ai_host = "192.168.0.223"
    ai_port = 8000
    
    print("🔍 네트워크 연결 진단")
    print("=" * 40)
    
    # 1. 핑 테스트
    print(f"1. 핑 테스트: {ai_host}")
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(["ping", "-n", "1", ai_host], 
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(["ping", "-c", "1", ai_host], 
                                  capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ 핑 성공: {ai_host} 접근 가능")
        else:
            print(f"❌ 핑 실패: {ai_host} 접근 불가")
            print("   가능한 원인:")
            print("   - AI 서버가 다른 네트워크에 있음")
            print("   - 방화벽 차단")
            print("   - IP 주소 변경됨")
    except Exception as e:
        print(f"❌ 핑 테스트 실패: {e}")
    
    # 2. 포트 연결 테스트
    print(f"\n2. 포트 연결 테스트: {ai_host}:{ai_port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ai_host, ai_port))
        sock.close()
        
        if result == 0:
            print(f"✅ 포트 연결 성공: {ai_port} 포트가 열려있음")
        else:
            print(f"❌ 포트 연결 실패: {ai_port} 포트 접근 불가")
            print("   가능한 원인:")
            print("   - AI 서버가 실행되지 않음")
            print("   - 포트가 다름 (8000이 아닐 수 있음)")
            print("   - 방화벽에서 포트 차단")
    except Exception as e:
        print(f"❌ 포트 테스트 실패: {e}")
    
    # 3. 로컬 네트워크 확인
    print(f"\n3. 로컬 네트워크 확인")
    try:
        # 자신의 IP 확인
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"✅ 내 IP 주소: {local_ip}")
        
        # 같은 네트워크 대역인지 확인
        ai_network = ".".join(ai_host.split(".")[:-1])
        local_network = ".".join(local_ip.split(".")[:-1])
        
        if ai_network == local_network:
            print(f"✅ 같은 네트워크 대역: {ai_network}.x")
        else:
            print(f"⚠️  다른 네트워크 대역:")
            print(f"   AI 서버: {ai_network}.x")
            print(f"   내 컴퓨터: {local_network}.x")
            print("   => VPN이나 네트워크 설정 확인 필요")
            
    except Exception as e:
        print(f"❌ 네트워크 확인 실패: {e}")

def test_alternative_connections():
    """대안 연결 방법 테스트"""
    
    print("\n🔄 대안 연결 방법 테스트")
    print("=" * 40)
    
    # 1. localhost 테스트 (AI 서버가 로컬에 있을 경우)
    print("1. localhost 테스트")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ localhost:8000 연결 성공: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답: {data}")
            return "http://localhost:8000"
    except Exception as e:
        print(f"❌ localhost:8000 연결 실패: {e}")
    
    # 2. 다른 포트 테스트
    ports_to_test = [8001, 8002, 8080, 3000, 5000]
    print(f"\n2. 다른 포트 테스트: 192.168.0.223")
    
    for port in ports_to_test:
        try:
            response = requests.get(f"http://192.168.0.223:{port}/health", timeout=3)
            print(f"✅ 포트 {port} 연결 성공: {response.status_code}")
            if response.status_code == 200:
                return f"http://192.168.0.223:{port}"
        except Exception:
            print(f"❌ 포트 {port} 연결 실패")
    
    # 3. 127.0.0.1 테스트
    print(f"\n3. 127.0.0.1 테스트")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"✅ 127.0.0.1:8000 연결 성공: {response.status_code}")
        if response.status_code == 200:
            return "http://127.0.0.1:8000"
    except Exception as e:
        print(f"❌ 127.0.0.1:8000 연결 실패: {e}")
    
    return None

def check_env_settings():
    """환경 설정 확인"""
    
    print("\n⚙️ 환경 설정 확인")
    print("=" * 40)
    
    try:
        # .env 파일 읽기
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # LLM_API_BASE_URL 찾기
        for line in env_content.split('\n'):
            if line.startswith('LLM_API_BASE_URL'):
                print(f"✅ 현재 설정: {line}")
                break
        else:
            print("❌ LLM_API_BASE_URL 설정을 찾을 수 없음")
            
    except FileNotFoundError:
        print("❌ .env 파일을 찾을 수 없음")
    except Exception as e:
        print(f"❌ .env 파일 읽기 실패: {e}")

def generate_solutions():
    """해결 방안 제시"""
    
    print("\n💡 해결 방안")
    print("=" * 40)
    
    print("1. AI팀에게 확인해야 할 사항:")
    print("   - AI 서버가 현재 실행 중인가요?")
    print("   - 실제 서버 주소와 포트는 무엇인가요?")
    print("   - 네트워크 접근 권한이 필요한가요?")
    print("   - 방화벽 설정이 있나요?")
    
    print("\n2. 임시 해결 방법:")
    print("   - AI 서버를 로컬에서 실행")
    print("   - VPN 연결 확인")
    print("   - 다른 네트워크에서 테스트")
    
    print("\n3. .env 파일 수정 방법:")
    print("   LLM_API_BASE_URL을 다음 중 하나로 변경:")
    print("   - http://localhost:8000 (로컬 실행시)")
    print("   - http://127.0.0.1:8000 (로컬 실행시)")
    print("   - AI팀에서 제공한 정확한 주소")

def main():
    print("🚨 AI 서버 연결 문제 진단")
    print(f"진단 시간: {datetime.now()}")
    print("=" * 50)
    
    # 1. 네트워크 연결 진단
    test_network_connectivity()
    
    # 2. 대안 연결 방법 테스트
    working_url = test_alternative_connections()
    
    if working_url:
        print(f"\n🎉 작동하는 URL 발견: {working_url}")
        print(f"   .env 파일의 LLM_API_BASE_URL을 이 주소로 변경하세요!")
    
    # 3. 환경 설정 확인
    check_env_settings()
    
    # 4. 해결 방안 제시
    generate_solutions()
    
    print("\n📞 다음 단계:")
    print("1. 위 진단 결과를 AI팀에게 공유")
    print("2. AI 서버의 정확한 주소와 상태 확인")
    print("3. 필요시 .env 파일 수정")

if __name__ == "__main__":
    main()

# 추가: AI팀에게 보낼 메시지 템플릿
ai_team_message = """
안녕하세요! 백엔드 개발자입니다.

AI 서버 연동 테스트 중 연결 문제가 발생했습니다.

**현재 설정:**
- AI 서버 주소: http://192.168.0.223:8000
- 테스트 시간: {현재시간}

**문제 상황:**
- 연결 타임아웃 발생
- 핑/포트 테스트 필요

**확인 요청사항:**
1. AI 서버가 현재 실행 중인가요?
2. 서버 주소와 포트가 맞나요?
3. 네트워크 접근 권한이 필요한가요?
4. 다른 테스트 방법이 있나요?

백엔드 연동 코드는 준비가 완료되어, 연결만 되면 바로 테스트 가능합니다.

감사합니다!
"""

print(f"\n📧 AI팀 문의 메시지 템플릿:")
print("=" * 50)
print(ai_team_message.format(현재시간=datetime.now().strftime("%Y-%m-%d %H:%M")))