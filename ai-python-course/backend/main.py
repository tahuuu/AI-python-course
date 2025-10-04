import io
import sys
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow CORS for the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the generative AI model
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-latest')
except Exception as e:
    print(f"Error configuring generative AI model: {e}")
    model = None

class Code(BaseModel):
    code: str

class Solution(BaseModel):
    code: str
    exercise: dict

@app.post("/api/execute")
async def execute_code(code: Code):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    ai_feedback = ""

    try:
        exec(code.code)
        output = redirected_output.getvalue()
    except Exception as e:
        error_message = str(e)
        output = error_message
        if model and api_key:
            try:
                prompt = f"""You are an expert Python tutor. A student has written the following code which produced an error.

Code:
```python
{code.code}
```

Error:
```
{error_message}
```

Explain the error in a simple, beginner-friendly way. Do not just give the answer, but guide the student to understand the mistake and how to fix it. Keep your explanation concise (2-3 sentences)."""
                
                response = model.generate_content(prompt)
                ai_feedback = response.text
            except Exception as gen_ai_e:
                ai_feedback = f"Could not get AI feedback: {gen_ai_e}"
    finally:
        sys.stdout = old_stdout

    return {"output": output, "ai_feedback": ai_feedback}

@app.get("/api/generate-exercise")
async def generate_exercise():
    if not model or not api_key:
        return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}
    
    try:
        prompt = '''You are a Python instructor. Generate a beginner-level Python exercise.
The exercise should be simple and focus on a fundamental concept (e.g., variables, loops, functions, lists).
Provide the output as a JSON object with two keys: "title" and "description".
The description should clearly explain the task and provide a simple example.

Example format:
{
  "title": "Sum of a List",
  "description": "Write a Python function called `sum_list` that takes a list of numbers as input and returns their sum. For example, `sum_list([1, 2, 3])` should return `6`."
}
'''
        response = model.generate_content(prompt)
        
        # Clean the response to extract the JSON part
        cleaned_text = response.text.strip()
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the AI response.")
            
        json_string = cleaned_text[json_start:json_end]
        
        exercise_json = json.loads(json_string)
        return exercise_json
    except Exception as e:
        # Fallback in case of parsing error
        return {"title": "AI Generation Error", "description": f"Could not generate or parse exercise: {e}"
} 


@app.post("/api/check-solution")
async def check_solution(solution: Solution):
    if not model or not api_key:
        return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}

    try:
        prompt = f"""You are a Python teaching assistant. A student has submitted a solution for an exercise.
Your task is to evaluate it and provide feedback.

**The Exercise:**
Title: {solution.exercise['title']}
Description: {solution.exercise['description']}

**The Student's Code:**
```python
{solution.code}
```

**Your Instructions:**
1.  Analyze the student's code to see if it correctly solves the exercise.
2.  Determine if the solution is correct, incorrect, or partially correct.
3.  Provide a concise, one-paragraph explanation.
4.  Be encouraging. If the code is wrong, gently point out the mistake and give a hint without revealing the full answer. If the code is correct, praise the student and perhaps suggest a small improvement or an alternative way to solve it.
5.  Return your evaluation as a JSON object with two keys:
    - `is_correct`: boolean (true if the solution is completely correct, false otherwise)
    - `feedback`: string (your one-paragraph explanation)

Example of a correct JSON response:
{{
  "is_correct": true,
  "feedback": "Great job! Your function correctly calculates the sum of the list. As a next step, you could think about how you might handle a list that contains non-numeric elements."
}}
"""
        response = model.generate_content(prompt)
        
        # Clean the response to extract the JSON part
        cleaned_text = response.text.strip()
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the AI response.")
            
        json_string = cleaned_text[json_start:json_end]
        
        feedback_json = json.loads(json_string)
        return feedback_json
    except Exception as e:
        return {"is_correct": False, "feedback": f"Sorry, I couldn't check your solution at the moment. Error: {e}"}


@app.get("/")
def read_root():
    return {"message": "AI Python Course Backend"}
