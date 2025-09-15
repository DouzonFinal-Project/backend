from sqlalchemy.orm import Session
from models.students import Student
from models.attendance import Attendance
from datetime import datetime, date
import re

async def handle_attendance_query(message: str, db: Session):
    """출석처리 관련 쿼리 처리"""
    user_message = message.lower()

    # 모든 학생 출석처리
    if any(keyword in user_message for keyword in ["모든 학생", "전체 학생", "모든학생", "전체학생", "전부", "모두"]) and any(keyword in user_message for keyword in ["출석처리", "출석", "등록"]):
        return await handle_bulk_attendance(message, db)
    
    # 특정 학생 출석/결석 처리 (사유 포함 명령어도 포함)
    if any(keyword in user_message for keyword in ["출석처리", "결석처리", "지각처리", "조퇴처리", "이유로", "사유로"]):
        return await handle_individual_attendance(message, db)
    
    # 출석 조회
    if any(keyword in user_message for keyword in ["출석", "출결", "출석률", "출석현황"]):
        return await handle_attendance_inquiry(message, db)
    
    return "출석처리 관련 명령어를 인식하지 못했습니다. '모든 학생 출석처리해줘' 또는 '김민수 결석처리해줘'와 같이 입력해주세요."


async def handle_bulk_attendance(message: str, db: Session):
    """모든 학생 출석처리"""
    try:
        # 모든 학생 조회
        students = db.query(Student).all()
        if not students:
            return "등록된 학생이 없습니다."
        
        today = date.today()
        processed_count = 0
        already_processed = 0
        
        for student in students:
            # 이미 오늘 출석처리가 되어있는지 확인
            existing_attendance = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date == today
            ).first()
            
            if existing_attendance:
                already_processed += 1
                continue
            
            # 출석 등록
            new_attendance = Attendance(
                student_id=student.id,
                date=today,
                status="출석"
            )
            db.add(new_attendance)
            processed_count += 1
        
        db.commit()
        
        if processed_count > 0:
            return f"모든 학생이 출석처리되었습니다. (총 {len(students)}명)"
        else:
            return f"모든 학생이 이미 출석처리되어 있습니다. (총 {len(students)}명)"
            
    except Exception as e:
        db.rollback()
        return f"출석처리 중 오류가 발생했습니다: {str(e)}"


async def handle_individual_attendance(message: str, db: Session):
    """특정 학생 출석/결석 처리 (나머지 학생은 출석처리)"""
    try:
        # 학생별 상태와 사유 추출
        student_info_list = extract_student_status_pairs(message)
        
        if not student_info_list:
            return "학생명과 출석 상태를 찾을 수 없습니다. '김민수 결석처리해줘' 또는 '최지연의 지각이유로 늦잠, 김정호의 결석이유로 몸이아픔으로 처리해줘'와 같이 입력해주세요."
        
        # 학생들 조회
        target_students = []
        not_found_students = []
        
        for student_name, status, reason in student_info_list:
            student = db.query(Student).filter(Student.student_name == student_name).first()
            if student:
                target_students.append((student, status, reason))
            else:
                not_found_students.append(student_name)
        
        if not_found_students:
            return f"다음 학생들을 찾을 수 없습니다: {', '.join(not_found_students)}"
        
        today = date.today()
        processed_count = 0
        already_processed = 0
        target_student_ids = [s.id for s, _, _ in target_students]
        
        # 모든 학생 조회
        all_students = db.query(Student).all()
        
        for student in all_students:
            # 이미 오늘 출석처리가 되어있는지 확인
            existing_attendance = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.date == today
            ).first()
            
            if existing_attendance:
                # 기존 출석 상태가 있으면
                if student.id in target_student_ids:
                    # 대상 학생은 요청된 상태로 변경
                    target_info = next((s, status, reason) for s, status, reason in target_students if s.id == student.id)
                    existing_attendance.status = target_info[1]
                    if target_info[2]:  # 사유가 있으면
                        existing_attendance.reason = target_info[2]
                    already_processed += 1
                # 나머지 학생은 기존 상태 유지 (변경하지 않음)
            else:
                # 새 출석 등록
                if student.id in target_student_ids:
                    # 대상 학생은 요청된 상태로 등록
                    target_info = next((s, status, reason) for s, status, reason in target_students if s.id == student.id)
                    status = target_info[1]
                    reason = target_info[2]
                else:
                    # 나머지 학생은 출석으로 등록
                    status = "출석"
                    reason = None
                
                new_attendance = Attendance(
                    student_id=student.id,
                    date=today,
                    status=status,
                    reason=reason
                )
                db.add(new_attendance)
                processed_count += 1
        
        db.commit()
        
        # 결과 메시지 생성 (사용자 입력 순서 보존)
        result_messages = []
        for student_name, status, reason in student_info_list:
            # 해당 학생의 실제 Student 객체 찾기
            student = next((s for s, _, _ in target_students if s.student_name == student_name), None)
            if student:
                if reason:
                    result_messages.append(f"'{student.student_name}' {status} (사유: {reason})")
                else:
                    result_messages.append(f"'{student.student_name}' {status}")
        
        return f"{', '.join(result_messages)} 처리되었습니다."
            
    except Exception as e:
        db.rollback()
        return f"출석처리 중 오류가 발생했습니다: {str(e)}"


async def handle_attendance_inquiry(message: str, db: Session):
    """출석 조회"""
    try:
        today = date.today()
        
        # 오늘 출석 현황 조회
        attendance_records = db.query(Attendance).filter(Attendance.date == today).all()
        
        if not attendance_records:
            return f"오늘({today.strftime('%Y년 %m월 %d일')}) 출석 기록이 없습니다."
        
        # 출석 상태별 집계 및 학생명 수집
        status_count = {}
        status_students = {}
        
        for record in attendance_records:
            status = record.status
            
            # 학생명 조회
            student = db.query(Student).filter(Student.id == record.student_id).first()
            student_name = student.student_name if student else "알 수 없음"
            
            # 카운트
            if status in status_count:
                status_count[status] += 1
                status_students[status].append(student_name)
            else:
                status_count[status] = 1
                status_students[status] = [student_name]
        
        # 결과 메시지 생성
        result = f"오늘({today.strftime('%Y년 %m월 %d일')}) 출석 현황입니다\n"
        
        # 출석 상태별로 정렬하여 표시
        status_order = ['출석', '지각', '조퇴', '결석']
        
        for status in status_order:
            if status in status_count:
                count = status_count[status]
                if status == '출석':
                    # 출석은 숫자만 표시
                    result += f"• {status}: {count}명\n"
                else:
                    # 지각, 조퇴, 결석은 학생명도 표시
                    result += f"• {status}: {count}명\n"
                    for student_name in status_students[status]:
                        result += f"  ({student_name})\n"
        
        return result
        
    except Exception as e:
        return f"출석 조회 중 오류가 발생했습니다: {str(e)}"


def extract_student_name(message: str) -> str:
    """메시지에서 학생명 추출 (단일 학생)"""
    student_names = extract_multiple_student_names(message)
    return student_names[0] if student_names else None


def extract_multiple_student_names(message: str) -> list:
    """메시지에서 여러 학생명 추출"""
    # 연결어만 제거 (단어 경계 고려)
    # "이예은과 김지영" -> "이예은 김지영"
    clean_message = re.sub(r'\s*과\s*', ' ', message)
    clean_message = re.sub(r'\s*와\s*', ' ', clean_message)
    clean_message = re.sub(r'\s*이랑\s*', ' ', clean_message)
    clean_message = re.sub(r'\s*랑\s*', ' ', clean_message)
    
    # 조사 제거 (은, 는, 이, 가, 을, 를, 에, 에서, 로, 으로)
    clean_message = re.sub(r'\s*[은는이가을를에에서로으로]\s*', ' ', clean_message)
    
    # 한글 이름 패턴 (2-4자)
    name_pattern = r'([가-힣]{2,4})'
    matches = re.findall(name_pattern, clean_message)
    
    # 출석처리 관련 키워드 제거
    attendance_keywords = ['출석처리', '결석처리', '지각처리', '조퇴처리', '출석', '결석', '지각', '조퇴', '처리', '해줘']
    
    student_names = []
    for match in matches:
        if match not in attendance_keywords:
            student_names.append(match)
    
    return student_names


def extract_attendance_status(message: str) -> str:
    """메시지에서 출석 상태 추출"""
    if '결석' in message:
        return '결석'
    elif '지각' in message:
        return '지각'
    elif '조퇴' in message:
        return '조퇴'
    elif '출석' in message:
        return '출석'
    else:
        return None


def extract_student_status_pairs(message: str) -> list:
    """메시지에서 학생별 출석 상태 쌍과 사유 추출"""
    # 출석 상태 키워드
    status_keywords = ['출석', '결석', '지각', '조퇴']
    
    # 학생별 정보 추출 (이름, 상태, 사유)
    student_info_list = []
    
    # "최지연의 지각이유로 늦잠, 김정호의 결석이유로 몸이아픔" 패턴 처리
    reason_pattern = r'([가-힣]{2,4})의\s*([가-힣]+)이유로\s*([가-힣\w]+?)(?:으로|로|으로 처리해줘|로 처리해줘|,|$)'
    reason_matches = re.findall(reason_pattern, message)
    
    for student_name, status, reason in reason_matches:
        if status in status_keywords:
            student_info_list.append((student_name, status, reason))
    
    # reason 패턴으로 처리된 학생이 있으면 그것만 반환
    if student_info_list:
        return student_info_list
    
    # 통합 패턴 처리: 쉼표로 구분된 모든 패턴을 한 번에 처리
    # "김준혁 지각, 김혜진 결석처리해줘" 형태
    parts = re.split(r'\s*,\s*', message)
    
    for part in parts:
        part = part.strip()
        
        # "김종수 지각처리해줘" 패턴 처리
        process_pattern = r'([가-힣]{2,4})\s*([가-힣]+)처리(?:해줘)?'
        process_match = re.search(process_pattern, part)
        
        if process_match:
            student_name, status = process_match.groups()
            if status in status_keywords:
                student_info_list.append((student_name, status, None))
                continue
        
        # "김지영 지각" 패턴 처리
        simple_pattern = r'([가-힣]{2,4})\s*([가-힣]+)(?:해줘)?$'
        simple_match = re.search(simple_pattern, part)
        
        if simple_match:
            student_name, status = simple_match.groups()
            if status in status_keywords:
                student_info_list.append((student_name, status, None))
    
    # 패턴으로 처리된 학생이 있으면 그것만 반환
    if student_info_list:
        return student_info_list
    
    # 기존 패턴 처리 ("김정호 지각 김종수 결석" 형태)
    # 연결어, 조사, 쉼표 제거
    clean_message = re.sub(r'\s*[과와이랑랑]\s*', ' ', message)
    clean_message = re.sub(r'\s*[은는이가을를에에서로으로]\s*', ' ', clean_message)
    clean_message = re.sub(r'\s*,\s*', ' ', clean_message)  # 쉼표 제거
    
    words = clean_message.split()
    i = 0
    while i < len(words):
        word = words[i]
        
        # 한글 이름인지 확인 (2-4자)
        if re.match(r'^[가-힣]{2,4}$', word) and word not in ['출석처리', '결석처리', '지각처리', '조퇴처리', '처리', '해줘', '이유로']:
            student_name = word
            
            # 다음 단어가 상태인지 확인
            if i + 1 < len(words) and words[i + 1] in status_keywords:
                status = words[i + 1]
                student_info_list.append((student_name, status, None))  # 사유 없음
                i += 2  # 학생명과 상태를 건너뛰기
            else:
                # 상태가 없으면 기본값으로 '출석' 사용 (결석이 아닌 출석으로 변경)
                student_info_list.append((student_name, '출석', None))
                i += 1
        else:
            i += 1
    
    return student_info_list