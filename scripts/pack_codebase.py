import os
import zipfile
from pathlib import Path

def pack_project():
    project_root = Path(__file__).resolve().parents[1]
    zip_path = project_root / "financial_planner_codebase.zip"
    
    print(f"Scanning project root: {project_root}")
    
    # Exclude directories
    exclude_dirs = {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        ".pytest_cache",
        "__pycache__",
        "scratch",
        ".agents",
        ".gemini"
    }
    
    # Exclude specific files
    exclude_files = {
        "financial_planner_codebase.zip",
        "scratch_test_fetch.py",
        "Financial planner Icon.PNG"
    }

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_root):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith((".pyc", ".pyo", ".pyd")):
                    continue
                
                file_path = Path(root) / file
                relative_path = file_path.relative_to(project_root)
                
                zip_file.write(file_path, relative_path)
                count += 1

    print(f"Successfully packed {count} files into {zip_path}")

if __name__ == "__main__":
    pack_project()
