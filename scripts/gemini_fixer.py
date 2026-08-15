import os
from google import genai

# Ensure the Gemini API key is configured
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    exit(1)

# Initialize the Gemini client
client = genai.Client()

# Define file extensions to scan
EXTENSIONS = {".py", ".js", ".ts", ".json", ".sh", ".html", ".css", ".java", ".cpp"}

def get_code_files():
    code_files = []
    ignore_dirs = {'.git', '.github', 'node_modules', 'venv', 'env', 'dist', 'build'}
    current_script = os.path.basename(__file__)

    for root, dirs, files in os.walk("."):
        # Prune ignored directories in-place to optimize traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in EXTENSIONS and file != current_script:
                code_files.append(os.path.normpath(os.path.join(root, file)))
                
    return code_files

def review_and_fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    if not content.strip():
        return

    prompt = f"""You are an expert automated code reviewer and repair engine. 
Review the file `{filepath}` for syntax errors, logical bugs, security risks, or anti-patterns.
- If errors exist, rewrite the file completely with proper, optimized code while preserving original intent.
- If the code is already error-free and clean, return the exact original content.

CRITICAL REQUIREMENT: Output ONLY raw source code. Do NOT enclose your output in markdown code fences (```), and do NOT add explanations or prose.

Original Code:
{content}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        corrected_code = response.text
    except Exception as e:
        print(f"Error calling Gemini API for {filepath}: {e}")
        return

    if not corrected_code:
        return

    corrected_code = corrected_code.strip()
    
    # Clean up residual backticks if returned
    if corrected_code.startswith("```"):
        lines = corrected_code.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        corrected_code = "\n".join(lines).strip()

    if corrected_code and corrected_code != content.strip():
        print(f"[Gemini Fix Applied]: {filepath}")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(corrected_code + "\n")
        except Exception as e:
            print(f"Error writing to {filepath}: {e}")

if __name__ == "__main__":
    files = get_code_files()
    print(f"Analyzing {len(files)} files in repository...")
    for file in files:
        review_and_fix_file(file)


