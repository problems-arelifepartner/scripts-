import os
import glob
from google import genai

# Initialize the Gemini client using environment variables
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Define file types for Gemini to scan
EXTENSIONS = [".py", ".js", ".ts", ".json", ".sh", ".html", ".css", ".java", ".cpp"]

def get_code_files():
    code_files = []
    for ext in EXTENSIONS:
        code_files.extend(glob.glob(f"**/*{ext}", recursive=True))
    
    # Exclude virtual environments, dependencies, and hidden system folders
    ignore_dirs = {'.git', '.github', 'node_modules', 'venv', 'env', 'dist', 'build'}
    return [
        f for f in code_files 
        if not any(part in ignore_dirs or part.startswith('.') for part in f.split(os.sep))
    ]

def review_and_fix_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if not content.strip():
        return

    prompt = f"""You are an expert automated code reviewer and repair engine. 
Review the file `{filepath}` for syntax errors, logical bugs, security risks, or anti-patterns.
- If errors exist, rewrite the file completely with proper, optimized code while preserving original intent.
- If the code is already error-free and clean, return the exact original content.

CRITICAL REQUIREMENT: Output ONLY raw source code. Do NOT enclose your output in markdown code fences (```), and do NOT add explanations or prose.

Original Code:
{content}"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    corrected_code = response.text.strip()
    
    # Clean up residual backticks if returned
    if corrected_code.startswith("```"):
        lines = corrected_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        corrected_code = "\n".join(lines).strip()

    if corrected_code and corrected_code != content.strip():
        print(f"[Gemini Fix Applied]: {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(corrected_code + "\n")

if __name__ == "__main__":
    files = get_code_files()
    print(f"Analyzing {len(files)} files in repository...")
    for file in files:
        review_and_fix_file(file)
