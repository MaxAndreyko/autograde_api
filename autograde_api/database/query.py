from typing import List
from sqlalchemy import select, or_, and_, desc
from autograde_api.database.models import EssaySubmissions, User
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
        
        # Check for uniqueness
        result = await session.execute(
            select(EssaySubmissions).where(
                and_(
                    EssaySubmissions.user_id == user_id,
                    EssaySubmissions.input_task == input_task,
                    EssaySubmissions.input_essay == input_essay
                )
            )
        )
        existing = result.scalars().first()
        if existing:
            print("Duplicate submission detected. Not saving.")
            return None
        
        new_submission = EssaySubmissions(
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

async def get_last_n_essay_submissions(
    user_id: int,
    n: int
) -> List[EssaySubmissions]:
    """
    Retrieves the last n essay submissions for a given user_id, ordered by most recent.

    Args:
        session: Async SQLAlchemy session.
        user_id: The user's ID.
        n: Number of submissions to retrieve.

    Returns:
        List of EssaySubmissions objects (can be empty if none found).
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EssaySubmissions)
            .where(EssaySubmissions.user_id == user_id)
            .order_by(desc(EssaySubmissions.submitted_at))
            .limit(n)
        )
        submissions = result.scalars().all()
    return submissions

async def get_user_id_by_username(username: str) -> int | None:
    """
    Returns the user_id for the given username, or None if not found.

    Args:
        session: Async SQLAlchemy session.
        username: The username to look up.

    Returns:
        The user_id if found, else None.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.user_id).where(User.username == username)
        )
        user_id = result.scalar_one_or_none()
    return user_id