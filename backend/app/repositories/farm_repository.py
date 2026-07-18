from sqlalchemy.orm import Session

from backend.app.models import Farm


class FarmRepository:
    def create(self, db: Session, user_id: int, **kwargs) -> Farm:
        farm = Farm(user_id=user_id, **kwargs)
        db.add(farm)
        db.commit()
        db.refresh(farm)
        return farm

    def list_for_user(self, db: Session, user_id: int) -> list[Farm]:
        return db.query(Farm).filter(Farm.user_id == user_id).order_by(Farm.id.desc()).all()

    def get_for_user(self, db: Session, user_id: int, farm_id: int) -> Farm | None:
        return (
            db.query(Farm)
            .filter(Farm.user_id == user_id, Farm.id == farm_id)
            .first()
        )
