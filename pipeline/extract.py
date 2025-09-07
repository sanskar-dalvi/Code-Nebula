import os
import zipfile
import shutil
from typing import List, Tuple

# Default folder where ZIPs or raw folders are dropped
DEFAULT_INPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input_code')
)

# Default raw output directory
RAW_DIR_DEFAULT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'raw')
)


def extract_source(input_path: str = None, raw_dir: str = None) -> List[str]:
    """Extracts a ZIP (or multiple ZIPs) or copies a folder into raw_dir.
       If input_path is None, uses the project’s input_code folder.
    """
    # pick up default input_code folder if none provided
    if input_path is None:
        input_path = DEFAULT_INPUT_DIR

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path not found: {input_path}")

    # default raw_dir if not provided
    if raw_dir is None:
        raw_dir = RAW_DIR_DEFAULT

    os.makedirs(raw_dir, exist_ok=True)

    try:
        if zipfile.is_zipfile(input_path):
            # directly extract a single zip
            with zipfile.ZipFile(input_path, 'r') as zf:
                zf.extractall(raw_dir)

        elif os.path.isdir(input_path):
            # first, extract any .zip files in that folder
            zip_files = [
                name for name in os.listdir(input_path)
                if name.lower().endswith('.zip')
            ]
            if zip_files:
                for zname in zip_files:
                    zpath = os.path.join(input_path, zname)
                    with zipfile.ZipFile(zpath, 'r') as zf:
                        zf.extractall(raw_dir)
            else:
                # no zips found → copy all files/dirs as raw
                for name in os.listdir(input_path):
                    src = os.path.join(input_path, name)
                    dst = os.path.join(raw_dir, name)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
        else:
            raise RuntimeError(f"Unsupported input type: {input_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to extract {input_path}: {e}") from e

    # collect and return file list
    extracted_files: List[str] = []
    for root, _, files in os.walk(raw_dir):
        for fname in files:
            extracted_files.append(os.path.join(root, fname))
    print("Extraction successful")
    return extracted_files


def validate_raw(raw_dir: str, allowed_exts: Tuple[str, ...] = ('.cs',)) -> None:
    """Validates that raw_dir contains at least one file with allowed extensions.

    Args:
        raw_dir: Directory to validate.
        allowed_exts: Tuple of allowed file extensions.

    Raises:
        ValueError: if no allowed files are found.
    """
    if not os.path.isdir(raw_dir):
        raise ValueError(f"Raw directory does not exist: {raw_dir}")

    found = False
    for root, _, files in os.walk(raw_dir):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in allowed_exts:
                found = True
                break
        if found:
            break

    if not found:
        raise ValueError(
            f"No files with extensions {allowed_exts} found in {raw_dir}"
        )


# Add CLI support
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Extract a zip or folder into raw/ and validate its contents"
    )
    parser.add_argument(
        "-i", "--input", dest="input_path",
        help="Path to input .zip or folder (defaults to input_code/)", default=None
    )
    parser.add_argument(
        "-o", "--output", dest="raw_dir",
        help="Raw output directory (defaults to raw/)", default=None
    )
    args = parser.parse_args()

    # determine the actual raw_dir to use
    raw_dir = args.raw_dir or RAW_DIR_DEFAULT

    try:
        files = extract_source(args.input_path, raw_dir)
        validate_raw(raw_dir)
        print(f"Extracted {len(files)} files into {raw_dir}")
    except Exception as e:
        print(f"Error during extraction: {e}")
