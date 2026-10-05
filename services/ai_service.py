import os
import google.generativeai as genai
from flask import current_app

class AIService:
    @staticmethod
    def _get_system_instruction(user, mode="Explain"):
        department = user.department or "General"
        year = user.year or "1st Year"
        style = user.learning_style or "Reading"
        
        base_instruction = (
            f"You are a supportive, knowledgeable AI Academic Mentor. "
            f"Your student is a {year} student in the {department} department. "
            f"Their preferred learning style is {style}. Tailor your explanations accordingly. "
            "IMPORTANT: Be helpful and encouraging. If you are uncertain about a fact, explicitly say: "
            "'I’m not fully certain. Please verify this with your course material or instructor.'"
        )
        
        mode_instructions = {
            "Explain": "Provide a comprehensive explanation. 1. Simple explanation. 2. Technical explanation. 3. Example. 4. Important points. 5. Common mistakes. 6. A follow-up question to check understanding.",
            "Simple Explanation": "Provide a very simple, beginner-friendly explanation using analogies. Avoid heavy jargon.",
            "Detailed Explanation": "Provide a deep, technical, and detailed explanation suitable for an advanced student.",
            "Example": "Focus primarily on providing clear, practical examples or case studies to illustrate the concept.",
            "Quiz Me": "Do not explain the concept. Instead, ask a challenging question about the topic to test the student's knowledge.",
            "Summarize": "Provide a brief, bulleted summary of the topic.",
            "Revision": "Provide quick flashcard-style points for rapid revision of the topic."
        }
        
        instruction = base_instruction + " \n\nMODE INSTRUCTION: " + mode_instructions.get(mode, mode_instructions["Explain"])
        return instruction

    @staticmethod
    def get_response(user, message_history, new_message, mode="Explain"):
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return "Error: GEMINI_API_KEY is not configured in the environment. Please add it to your .env file."
        
        genai.configure(api_key=api_key)
        
        system_instruction = AIService._get_system_instruction(user, mode)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        history = []
        for msg in message_history:
            role = "model" if msg.sender == "ai" else "user"
            history.append({"role": role, "parts": [msg.message]})
            
        chat = model.start_chat(history=history)
        
        try:
            response = chat.send_message(new_message)
            return response.text
        except Exception as e:
            return f"I encountered an error while thinking. Please try again. (Error: {str(e)})"
