from .database import engine
from .models import Base, SMEOwnership

def seed():
    Base.metadata.create_all(bind=engine)
    # Insert sample SMEs if table empty
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    try:
        count = db.query(SMEOwnership).count()
        if count == 0:
            samples = [
                SMEOwnership(system_name="Loan Service", owner_name="Asha Patel", owner_team="Payments", owner_email="asha@example.com", expertise_tags="loan,service,payments"),
                SMEOwnership(system_name="Kafka Platform", owner_name="Ravi Kumar", owner_team="Platform", owner_email="ravi@example.com", expertise_tags="kafka,streaming"),
                SMEOwnership(system_name="Auth Service", owner_name="Maria Lopez", owner_team="Auth", owner_email="maria@example.com", expertise_tags="auth,oauth"),
            ]
            db.add_all(samples)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
