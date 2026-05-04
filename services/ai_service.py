import openai
from typing import List, Dict, Any
import json

class AIService:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
    
    async def summarize_lesson(self, content: str, language: str = "uz") -> str:
        """Summarize lesson content"""
        prompt = f"""
        Quyidagi dars mazmunini qisqacha va tushunarli qilib {language} tilida summarize qiling:
        
        {content[:3000]}
        
        Summary (3-5 qator):
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Siz yaxshi o'qituvchi va yordamchi assistantsiz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    async def generate_quiz(self, content: str, num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions from lesson content"""
        prompt = f"""
        Quyidagi dars mazmunidan {num_questions} ta test savoli yarating.
        Har bir savolga 4 ta variant (A, B, C, D) va to'g'ri javobni qo'shing.
        Javoblar JSON formatida bo'lsin:
        
        {{
            "questions": [
                {{
                    "question": "savol matni",
                    "options": ["A) variant1", "B) variant2", "C) variant3", "D) variant4"],
                    "correct_answer": "A",
                    "explanation": "tushuntirish"
                }}
            ]
        }}
        
        Dars mazmuni:
        {content[:3000]}
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Siz test yaratuvchi assistantsiz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result.get("questions", [])
        except:
            return []
    
    async def explain_concept(self, concept: str, difficulty: str = "simple") -> str:
        """Explain a concept in simple terms"""
        prompt = f"""
        "{concept}" tushunchasini {difficulty} tarzda tushuntirib bering.
        Misollar va tushuntirishlar bilan.
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Siz yaxshi o'qituvchi assistantsiz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        return response.choices[0].message.content.strip()
    
    async def extract_text_from_file(self, file_content: bytes, file_type: str) -> str:
        """Extract text from uploaded files (PDF, DOCX, etc.)"""
        # Implementation depends on file type
        # For PDF: use PyPDF2 or pdfplumber
        # For DOCX: use python-docx
        # This is a placeholder
        return "Extracted text from file"