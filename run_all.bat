@echo off
echo 🚀 Starting all Rasa servers and Flask API...
echo ==============================================
echo.

:: ===== ENGLISH MODEL =====
start cmd /k "cd /d D:\Umang_Coding\AI_chatbot\Rasa\data\en && rasa run --port 5005 --endpoints endpoints.yml"
start cmd /k "cd /d cd /d D:\Umang_Coding\AI_chatbot\Rasa\data\en && rasa run actions --port 5055"

:: ===== HINDI MODEL =====
start cmd /k "cd /d D:\Umang_Coding\AI_chatbot\Rasa\data\hn && rasa run --port 5006 --endpoints endpoints.yml"
start cmd /k "cd /d D:\Umang_Coding\AI_chatbot\Rasa\data\hn && rasa run actions --port 5057"

:: ===== MARATHI MODEL =====
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\marathi && rasa run --port 5007 --endpoints endpoints.yml"
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\marathi && rasa run actions --port 5057"

:: ===== BENGALI MODEL =====
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\bengali && rasa run --port 5008 --endpoints endpoints.yml"
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\bengali && rasa run actions --port 5058"

:: ===== RAJASTHANI MODEL =====
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\rajasthani && rasa run --port 5009 --endpoints endpoints.yml"
start cmd /k "cd /d D:\Umang_Coding\college_chatbot\rajasthani && rasa run actions --port 5059"

:: ===== FLASK API =====
start cmd /k "cd /d D:\Umang_Coding\college_chatbot && python app.py"

echo.
echo ✅ All servers launched successfully!
pause
