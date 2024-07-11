from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="datapipe_app_")
    show_step_status: bool = False  # "DATAPIPE_APP_SHOW_STEP_STATUS" in .env


API_SETTINGS = APISettings()