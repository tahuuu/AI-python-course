import io
import sys
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv

import asyncio
from fastapi.responses import StreamingResponse

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
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    print(f"Error configuring generative AI model: {e}")
    model = None

class Code(BaseModel):
    code: str

class Solution(BaseModel):
    code: str
    exercise: dict

class ProjectInterest(BaseModel):
    interest: str

class ExerciseRequest(BaseModel):
    difficulty: str

@app.post("/api/execute")
async def execute_code(code: Code):
    
    async def stream_generator():
        # The -u flag is important for unbuffered output
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-u', '-c', code.code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Await both streams concurrently
        async def read_stream(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                yield f"{line.decode('utf-8')}"

        try:
            # Merge stdout and stderr for simplicity
            async for line in read_stream(process.stdout, 'stdout'):
                yield line
            async for line in read_stream(process.stderr, 'stderr'):
                yield line
        finally:
            # Ensure the process is cleaned up
            await process.wait()

    return StreamingResponse(stream_generator(), media_type="text/plain")

@app.post("/api/generate-exercise")
async def generate_exercise(request: ExerciseRequest):
    if not model or not api_key:
        return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}
    
    try:
        prompt = f'''You are a Python instructor. Generate a {request.difficulty}-level Python exercise.
For Intermediate or Advanced, this may involve concepts like object-oriented programming, data structures, algorithms, or file I/O.
The exercise should be simple and focus on a fundamental concept (e.g., variables, loops, functions, lists).
Provide the output as a JSON object with two keys: "title" and "description".
The description should clearly explain the task and provide a simple example.

Example format:
{{
  "title": "Sum of a List",
  "description": "Write a Python function called `sum_list` that takes a list of numbers as input and returns their sum. For example, `sum_list([1, 2, 3])` should return `6`."
}}
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
        return {"title": "AI Generation Error", "description": f"Could not generate or parse exercise: {e}"} 


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


@app.post("/api/generate-project")
async def generate_project(project_interest: ProjectInterest):
    if not model or not api_key:
        return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}

    try:
        prompt = f"""You are a creative mentor for a new Python programmer.
A student has expressed an interest in the topic of: "{project_interest.interest}"

Your task is to generate a simple, beginner-friendly project idea related to this topic. The project should be something a beginner can build in a single Python script.

**Your Instructions:**
1.  Create a catchy and descriptive `title` for the project.
2.  Write a one-paragraph `description` of what the project is.
3.  List 3-5 key `features` for the project as an array of strings. These should be actionable steps the student can take.
4.  Return your response as a single JSON object with the keys "title", "description", and "features".

**Example JSON Response for the interest "space":**
{{
  "title": "Solar System Fact Explorer",
  "description": "Build a simple interactive program that lets users ask for facts about planets in our solar system. The program will have a small database of facts and will respond to user input.",
  "features": [
    "Create a dictionary to store facts about each planet (e.g., diameter, distance from sun).",
    "Prompt the user to enter a planet's name.",
    "Retrieve and display the facts for the requested planet.",
    "Include a loop so the user can ask about multiple planets.",
    "Add error handling for when a user enters a non-existent planet."
  ]
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
        
        project_json = json.loads(json_string)
        return project_json
    except Exception as e:
        return {"title": "AI Generation Error", "description": f"Could not generate project idea: {e}", "features": []}


@app.post("/api/explain-code")
async def explain_code(code: Code):
    if not model or not api_key:
        return {"error": "AI model not configured. Please check GOOGLE_API_KEY."}

    try:
        prompt = f"""You are an expert Python programmer and a patient teacher.
A student has asked for an explanation of the following code.

**The Student's Code:**
```python
{code.code}
```

**Your Instructions:**
1.  Analyze the code step by step.
2.  Provide a clear, concise, and easy-to-understand explanation.
3.  If the code is simple, explain the basic concepts.
4.  If the code is more complex, break it down into logical parts and explain each one.
5.  Use markdown for formatting, such as bullet points or numbered lists, to make the explanation easy to read.
"""
        response = model.generate_content(prompt)
        return {"explanation": response.text}
    except Exception as e:
        return {"explanation": f"Sorry, I couldn't provide an explanation at this time. Error: {e}"}


@app.get("/")
def read_root():
    return {"message": "AI Python Course Backend"}
