from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException

from api.models.entry import Entry, EntryCreate
from api.repositories.postgres_repository import PostgresDB
from api.services.entry_service import EntryService
from api.models.analysis_response import AnalysisResponse

router = APIRouter()


async def get_entry_service() -> AsyncGenerator[EntryService, None]:
    async with PostgresDB() as db:
        yield EntryService(db)

@router.post("/entries")
async def create_entry(entry_data: EntryCreate, entry_service: EntryService = Depends(get_entry_service)):
    """Create a new journal entry."""
    try:
        # Create the full entry with auto-generated fields
        entry = Entry(
            work=entry_data.work,
            struggle=entry_data.struggle,
            intention=entry_data.intention
        )

        # Store the entry in the database
        created_entry = await entry_service.create_entry(entry.model_dump())

        # Return success response (FastAPI handles datetime serialization automatically)
        return {
            "detail": "Entry created successfully",
            "entry": created_entry
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating entry: {str(e)}") from e

# Implements GET /entries endpoint to list all journal entries
# Example response: [{"id": "123", "work": "...", "struggle": "...", "intention": "..."}]
@router.get("/entries")
async def get_all_entries(entry_service: EntryService = Depends(get_entry_service)):
    """Get all journal entries."""
    result = await entry_service.get_all_entries()
    return {"entries": result, "count": len(result)}

@router.get("/entries/{entry_id}", response_model=Entry)
async def get_entry(entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """Get a specific journal entry"""
    result = await entry_service.get_entry(entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return result

@router.patch("/entries/{entry_id}")
async def update_entry(entry_id: str, entry_update: dict, entry_service: EntryService = Depends(get_entry_service)):
    """Update a journal entry"""
    result = await entry_service.update_entry(entry_id, entry_update)
    if not result:

        raise HTTPException(status_code=404, detail="Entry not found")

    return result

@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """Delete a specific journal entry"""
    deleted = await entry_service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"detail": "Entry deleted"}

@router.delete("/entries")
async def delete_all_entries(entry_service: EntryService = Depends(get_entry_service)):
    """Delete all journal entries"""
    await entry_service.delete_all_entries()
    return {"detail": "All entries deleted"}

@router.post("/entries/{entry_id}/analyze", response_model=AnalysisResponse, status_code=200)
async def analyze_journal_entry(entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """Analyze a journal entry using LLM."""
    try:
        analysis_result = await entry_service.analyze_journal_entry(entry_id)
        if not analysis_result:
            raise HTTPException(status_code=404, detail="Entry not found")
        return analysis_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing entry: {str(e)}")
