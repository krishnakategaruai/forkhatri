# [FR11/FR22] The one file-upload endpoint — HTTP front door only; type and
# size checks plus storage live in app/services/uploads.py.
# Traces to: FR11, FR22
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.errors import ERROR_RESPONSES
from app.identity import AuthzContext, resolve_authz_context
from app.services import uploads as svc
from app.services.uploads import UPLOAD_DIR, UploadOut  # noqa: F401  UPLOAD_DIR is mounted by main.py

router = APIRouter(prefix="/v1/uploads", tags=["uploads"], responses=ERROR_RESPONSES)


@router.post("", status_code=201, response_model=UploadOut, operation_id="uploadFile", summary="Upload an image file and get its public URL")
async def upload_file(
    file: UploadFile = File(...),
    ctx: AuthzContext = Depends(resolve_authz_context),
) -> UploadOut:
    svc.check_extension(file.filename)  # type is rejected before the body is read
    data = await file.read()
    return await svc.store_upload(ctx, file.filename, data, file.content_type)
