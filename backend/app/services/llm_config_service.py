from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigRead, LLMConfigUpdate


MASK = "********"


class LLMConfigService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_configs(self) -> list[LLMConfig]:
        return self.db.query(LLMConfig).order_by(LLMConfig.updated_at.desc(), LLMConfig.id.desc()).all()

    def get_config(self, config_id: int) -> LLMConfig:
        config = self.db.get(LLMConfig, config_id)
        if not config:
            raise NotFoundError("LLM config not found.")
        return config

    def create_config(self, payload: LLMConfigCreate) -> LLMConfig:
        config = LLMConfig(**payload.model_dump())
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_config(self, config_id: int, payload: LLMConfigUpdate) -> LLMConfig:
        config = self.get_config(config_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field == "api_key" and value == MASK:
                continue
            setattr(config, field, value)
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, config_id: int) -> None:
        config = self.get_config(config_id)
        self.db.delete(config)
        self.db.commit()

    @staticmethod
    def to_read_schema(config: LLMConfig) -> LLMConfigRead:
        return LLMConfigRead(
            id=config.id,
            provider=config.provider,
            display_name=config.display_name,
            base_url=config.base_url,
            model_name=config.model_name,
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
            max_tokens=config.max_tokens,
            enabled=config.enabled,
            masked_api_key=MASK if config.api_key else None,
            has_api_key=bool(config.api_key),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
