from pydantic_settings import BaseSettings, SettingsConfigDict


class ENVSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="datapipe_app_")
    show_step_status: str = "False"  # "DATAPIPE_APP_SHOW_STEP_STATUS" in .env


ENV_SETTINGS = ENVSettings()
