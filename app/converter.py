import warnings
from pathlib import Path

_MARKITDOWN_CLASS = None
_MARKITDOWN_IMPORT_ERROR: ImportError | None = None
_MARKITDOWN_IMPORT_ATTEMPTED = False


def _load_markitdown():
    global _MARKITDOWN_CLASS, _MARKITDOWN_IMPORT_ERROR, _MARKITDOWN_IMPORT_ATTEMPTED

    if _MARKITDOWN_IMPORT_ATTEMPTED:
        return _MARKITDOWN_CLASS

    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Couldn't find ffmpeg or avconv.*",
                category=RuntimeWarning,
            )
            from markitdown import MarkItDown
    except ImportError as exc:
        _MARKITDOWN_IMPORT_ERROR = exc
    else:
        _MARKITDOWN_CLASS = MarkItDown

    _MARKITDOWN_IMPORT_ATTEMPTED = True
    return _MARKITDOWN_CLASS


def get_markitdown_error() -> str | None:
    if _load_markitdown() is not None:
        return None

    return (
        "MarkItDown is not installed or cannot be imported. "
        'Install it from the local markitdown folder with: pip install -e "packages/markitdown[all]". '
        "See Step 2 in README.md for setup details."
    )


def convert_file(input_path: str, output_path: str) -> tuple[bool, str]:
    import_error = get_markitdown_error()
    if import_error:
        return False, import_error

    markitdown_class = _load_markitdown()

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.is_file():
        return False, "Input file does not exist."

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        md = markitdown_class()
        result = md.convert(str(input_file))
        output_file.write_text(result.text_content or "", encoding="utf-8")
        return True, ""
    except Exception as exc:
        return False, str(exc)
