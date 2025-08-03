# tests/test_cli.py

import subprocess
import os

def test_cli_runs():
    # Use a dummy file path (you can use a real one too)
    sample_file = "input_code/SampleController.cs"

    # Check if file exists to avoid false fail
    if not os.path.exists(sample_file):
        # Create an empty file temporarily for test
        with open(sample_file, "w") as f:
            f.write("// dummy C# file")

    result = subprocess.run(["python", "cli.py", sample_file], capture_output=True, text=True)

    # Assert the script exits with 0 (success)
    assert result.returncode == 0
    assert "[CLI] File path received:" in result.stdout
