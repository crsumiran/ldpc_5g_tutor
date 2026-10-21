from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    tutor_engine: str = "openrouter"
    opencode_url: str = "http://opencode:4096"
    opencode_timeout_seconds: float = 180
    tutor_model: str = "google/gemma-4-31b-it:free"
    tutor_fallback_models: str = "google/gemma-4-26b-a4b-it:free,cohere/north-mini-code:free,qwen/qwen3.8-27b:free"
    tutor_openrouter_min_interval_seconds: float = 3.2
    planner_model: str = "openai/gpt-4o-mini"
    sandbox_image: str = "de-tutor-sandbox:latest"
    sandbox_timeout_sec: int = 30
    sandbox_mem: str = "512m"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:////home/ranga/opencode/tutor/data/tutor.db"
    allowed_import_roots: str = "/home/ranga/opencode"
    data_dir: str = "/home/ranga/opencode/tutor/data"
    curriculum_dir: str = "/home/ranga/opencode/tutor/curriculum"


settings = Settings()
