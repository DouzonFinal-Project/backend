import weasyprint
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any

class PDFService:
    def __init__(self):
        # 템플릿 환경 설정
        template_dir = Path("templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """템플릿을 렌더링하여 HTML 생성"""
        template = self.env.get_template(template_name)
        return template.render(**data)
    
    def _html_to_pdf(self, html_content: str) -> bytes:
        """HTML을 PDF로 변환"""
        return weasyprint.HTML(string=html_content).write_pdf()
    
    def generate_counseling_pdf(self, data: Dict[str, Any]) -> bytes:
        """상담 보고서 PDF 생성"""
        html = self._render_template("counseling_report.html", data)
        return self._html_to_pdf(html)
    
    def generate_class_summary_pdf(self, data: Dict[str, Any]) -> bytes:
        """학급 요약 PDF 생성"""
        html = self._render_template("class_summary.html", data)
        return self._html_to_pdf(html)