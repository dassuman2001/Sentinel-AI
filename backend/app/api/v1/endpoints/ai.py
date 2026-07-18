from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.secret import Secret
from app.models.ai_analysis import AIAnalysis
from app.schemas.ai import AIExplanationResponse, AIRemediationResponse, AIChatRequest, AIChatResponse
from app.services.ai_service import AIService
from app.security.auth import get_current_user
from app.models.user import User
import json

router = APIRouter()

@router.get("/explain/{secret_id}", status_code=status.HTTP_200_OK)
def get_secret_explanation_and_remediation(
    secret_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-generated explanation and remediation for a leaked secret.
    Saves the result in the database (ai_analyses table) to cache future requests.
    """
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    # Verify access
    from app.models.repository import Repository
    repo = db.query(Repository).filter(Repository.id == secret.repository_id).first()
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if analysis already exists
    analysis = db.query(AIAnalysis).filter(AIAnalysis.secret_id == secret_id).first()
    if analysis:
        try:
            exp_data = json.loads(analysis.explanation)
            rem_data = json.loads(analysis.remediation)
            return {
                "secret_id": secret_id,
                "explanation": exp_data,
                "remediation": rem_data
            }
        except Exception:
            # Fallback to recreate if corrupt JSON
            pass

    # Call AI Service to generate explanation and remediation
    context = secret.raw_context or f"Type: {secret.secret_type}\nMasked value: {secret.masked_value}"
    explanation_dict = AIService.explain_secret(secret.secret_type, context)
    remediation_dict = AIService.generate_remediation(secret.secret_type, secret.file_path, context)

    # Cache/Save to database
    analysis_entry = AIAnalysis(
        secret_id=secret_id,
        explanation=json.dumps(explanation_dict),
        remediation=json.dumps(remediation_dict)
    )
    db.add(analysis_entry)
    db.commit()
    db.refresh(analysis_entry)

    return {
        "secret_id": secret_id,
        "explanation": explanation_dict,
        "remediation": remediation_dict
    }


@router.post("/chat/{secret_id}", response_model=AIChatResponse)
def ask_ai_about_secret(
    secret_id: int,
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ask a security question about a specific leaked secret and get an answer.
    """
    secret = db.query(Secret).filter(Secret.id == secret_id).first()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    # Verify access
    from app.models.repository import Repository
    repo = db.query(Repository).filter(Repository.id == secret.repository_id).first()
    if repo.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    context = secret.raw_context or f"Type: {secret.secret_type}\nMasked value: {secret.masked_value}"
    answer = AIService.ask_security_question(secret.secret_type, context, req.question)
    
    return AIChatResponse(answer=answer)
