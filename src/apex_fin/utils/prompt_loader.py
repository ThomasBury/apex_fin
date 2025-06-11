from typing import Optional
from pathlib import Path
import logging  # Added for logging

# Configure a logger for this module
logger = logging.getLogger(__name__)

# Assuming apex_fin.yaml and custom_prompts/ are at the project root, one level above 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SRC_APEX_FIN_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(path_str: Optional[str], fallback: str) -> str:
    """Loads a prompt from a file or returns a fallback string.

    Attempts to load a text prompt from a file specified by `path_str`.
    The path is treated as relative to the project root. If `path_str` is None,
    empty, or if the file cannot be loaded for any reason (e.g., not found,
    invalid path, permission issues, security restrictions), the `fallback`
    string is returned.

    This function includes security measures to prevent path traversal attacks
    by ensuring that resolved paths remain within the project root directory
    and by rejecting absolute paths.

    Parameters
    ----------
    path_str : Optional[str]
        The relative path string to the prompt file from the project root.
    fallback : str
        The string to return if the prompt cannot be loaded from `path_str`.

    Returns
    -------
    str
        The content of the prompt file or the fallback string.
    """
    if path_str:
        try:
            # Treat path_str as relative to the project root
            # Path objects from Pydantic for PromptOverrides should be string types now
            if not isinstance(
                path_str, (str, Path)
            ):  # Ensure path_str is a string or Path
                logger.warning(
                    f"Invalid path type for prompt: {path_str}. Using fallback."
                )
                return fallback

            # If it's already a Path object, great. If string, convert.
            relative_path = Path(path_str)

            if relative_path.is_absolute():
                logger.warning(
                    f"Absolute path rejected for prompt: {path_str}. Using fallback."
                )
                return fallback

            # Resolve the path against the project root
            # This assumes 'custom_prompts/' are at project root, and internal defaults might be elsewhere
            # For now, let's assume all paths in config are relative to PROJECT_ROOT
            full_path = (PROJECT_ROOT / relative_path).resolve()

            # Security check: Ensure the resolved path is still within the PROJECT_ROOT
            # This is a basic check. More robust checks might be needed if symlinks are a concern.
            if not str(full_path).startswith(str(PROJECT_ROOT)):
                logger.warning(
                    f"Path traversal attempt rejected for prompt: {path_str}. Path resolved to {full_path}. Using fallback."
                )
                return fallback

            # Additional check for default prompts location if needed, or make all paths from root
            # For example, if internal defaults are always under src/apex_fin/prompts
            # if "default_prompts_identifier" in path_str: # Fictional identifier
            #    full_path = (SRC_APEX_FIN_PROMPTS_DIR / relative_path).resolve()
            #    if not str(full_path).startswith(str(SRC_APEX_FIN_PROMPTS_DIR)):
            #        # ... handle traversal for default prompts ...

            if full_path.exists() and full_path.is_file():
                return full_path.read_text(encoding="utf-8")
            else:
                logger.warning(
                    f"Prompt file not found at resolved path: {full_path} (from input: {path_str}). Using fallback."
                )
        except Exception as e:
            logger.error(
                f"Error loading prompt from '{path_str}': {e}. Using fallback.",
                exc_info=True,
            )
            # Fall through to fallback
    return fallback


# render_template is not used, so commenting it out to remove latent SSTI risk.
# If it's needed later, it should be implemented with sandboxing.
# from jinja2.sandbox import SandboxedEnvironment
# sandboxed_env = SandboxedEnvironment()
# def render_template(template_str: str, context: dict) -> str:
#     template = sandboxed_env.from_string(template_str)
#     return template.render(**context)
