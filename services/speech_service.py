import os
import uuid
import google.generativeai as genai
from gtts import gTTS
from flask import current_app

class SpeechService:
    @staticmethod
    def speech_to_text(audio_file_path):
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return {"transcript": "", "status": "error", "error": "API key not configured."}
            
        genai.configure(api_key=api_key)
        
        try:
            audio_file = genai.upload_file(path=audio_file_path)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([
                "Please accurately transcribe this audio. Output ONLY the transcript without any extra text or formatting.",
                audio_file
            ])
            
            # Clean up the file from Gemini servers
            genai.delete_file(audio_file.name)
            
            # Calculate simple stats
            words = response.text.split()
            word_count = len(words)
            
            return {
                "transcript": response.text.strip(),
                "status": "success",
                "word_count": word_count,
                "detected_language": "Unknown (Auto-detected)"
            }
        except Exception as e:
            return {"transcript": "", "status": "error", "error": str(e)}

    @staticmethod
    def text_to_speech(text, output_dir):
        try:
            tts = gTTS(text=text, lang='en')
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(output_dir, filename)
            tts.save(filepath)
            return {"audio_url": f"/uploads/{filename}", "status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
