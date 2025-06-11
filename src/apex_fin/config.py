from typing import Optional
from pathlib import Path
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


# Environment Settings (.env)
class EnvSettings(BaseSettings):
    GEMINI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RiskConfig(BaseModel):
    enabled: list[str] = []
    guidelines: dict[str, str] = {}
    tools: dict[str, list[str]] = {}

    @field_validator("guidelines", mode="before")
    @classmethod
    def check_guidelines_not_empty(cls, v: dict[str, Optional[str]]):
        if isinstance(v, dict):
            for key, value in v.items():
                if value is None:
                    raise ValueError(
                        f"Guideline for '{key}' cannot be null. Please provide a non-empty string or remove the key."
                    )
                if isinstance(value, str) and not value.strip():
                    raise ValueError(
                        f"Guideline for '{key}' cannot be an empty string or contain only whitespace. Please provide content or remove the key."
                    )
                # Ensure it's a string, as YAML might load other simple types if not quoted
                if not isinstance(value, str):
                    raise ValueError(
                        f"Guideline for '{key}' must be a string. Found type: {type(value).__name__}."
                    )
        return v


# YAML Configuration Schema
class LLMOverrides(BaseModel):
    model: Optional[str] = None
    base_url: Optional[str] = None


class ReportOverrides(BaseModel):
    markdown_template_path: Optional[str] = None
    enable_polishing: bool = True
    include_context: bool = True
    include_news: bool = True


class PromptOverrides(BaseModel):
    team: Optional[str] = None
    analysis: Optional[str] = None
    comparison: Optional[str] = None
    evaluation: Optional[str] = None
    analysis_markdown: Optional[str] = None
    analysis_structured: Optional[str] = None


class UserOverrides(BaseModel):
    llm: LLMOverrides = LLMOverrides()
    report: ReportOverrides = ReportOverrides()
    prompts: PromptOverrides = PromptOverrides()
    risk: RiskConfig = RiskConfig()


# YAML Loader
def load_user_config(path: Optional[str] = None) -> UserOverrides:
    config_path = Path(path or "apex_fin.yaml")
    if not config_path.exists():
        return UserOverrides()
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return UserOverrides(**raw)


# Merged Runtime Settings
class MergedSettings:
    def __init__(self, env: EnvSettings, user: UserOverrides):
        self.env = env
        self.user = user

    @property
    def LLM_MODEL(self) -> str:
        # LLM_MODEL is now only configured in apex_fin.yaml
        if not self.user.llm.model:
             raise ValueError("LLM model must be specified in apex_fin.yaml")
        return self.user.llm.model

    @property
    def BASE_URL(self) -> Optional[str]:
        # BASE_URL is now only configured in apex_fin.yaml
        return self.user.llm.base_url

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.env.GEMINI_API_KEY  # Always from .env

    @property
    def markdown_template_path(self) -> Optional[str]:
        return self.user.report.markdown_template_path

    @property
    def report_enable_polishing(self) -> bool:
        return self.user.report.enable_polishing

    @property
    def report_include_context(self) -> bool:
        return self.user.report.include_context
    
    @property
    def report_include_news(self) -> bool:
        return self.user.report.include_news

    @property
    def prompt_paths(self) -> PromptOverrides:
        return self.user.prompts

    @property
    def enabled_risks(self) -> list[str]:
        return self.user.risk.enabled

    @property
    def risk_guidelines(self) -> dict[str, str]:
        return self.user.risk.guidelines

    @property
    def risk_tools(self) -> dict[str, list[str]]:
        return self.user.risk.tools


# Singleton Instantiation
env_settings = EnvSettings()
user_config = load_user_config()
settings = MergedSettings(env_settings, user_config)
