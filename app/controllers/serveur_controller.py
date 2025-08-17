from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["Serveur"]
)

@router.get("/", summary="Vérifie si le serveur est en ligne")
def health_check():
    return {"status": "ok"}
