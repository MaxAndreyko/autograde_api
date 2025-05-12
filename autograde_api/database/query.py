from sqlalchemy import select, or_

from autograde_api.database.models import EssayScoring, User
from autograde_api.database.connection import AsyncSessionLocal
from autograde_api.database.utils import hash_password


async def add_user(
    username: str, 
    password: str, 
) -> int | None:
    """
    Asynchronously adds a new user after checking for existing username/email.
    Returns user_id if successful.
    """
    async with AsyncSessionLocal() as session:
        # Check for existing user
        result = await session.execute(
            select(User).where(
                or_(User.username == username)
            )
        )
        if result.scalars().first():
            print("User already exists")
            return None

        # Create new user
        new_user = User(
            username=username,
            password_hash=hash_password(password)
        )
        
        try:
            session.add(new_user)
            await session.commit()
            return new_user.user_id
        except Exception as e:
            await session.rollback()
            print(f"Error adding user: {e}")
            return None

async def save_essay_submission(
    user_id: int,
    input_task: str,
    input_essay: str,
    score_content: int = None,
    score_organization: int = None,
    score_grammar: int = None,
    comment: str = None
) -> int | None:
    """
    Asynchronously saves an essay submission with scores.
    Returns submission_id if successful.
    """
    async with AsyncSessionLocal() as session:
        new_submission = EssayScoring(
            user_id=user_id,
            input_task=input_task,
            input_essay=input_essay,
            score_content=score_content,
            score_organization=score_organization,
            score_grammar=score_grammar,
            comment=comment
        )
        
        try:
            session.add(new_submission)
            await session.commit()
            return new_submission.id
        except Exception as e:
            await session.rollback()
            print(f"Error saving submission: {e}")
            return None
