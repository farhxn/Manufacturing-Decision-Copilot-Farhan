"""Supplier API routes."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_supplier_service
from app.core.exceptions import AppHTTPException
from app.schemas.common import APIResponse
from app.schemas.supplier import (
    SupplierCompareRequest,
    SupplierDetailSchema,
    SupplierSummarySchema,
    SupplierCreateSchema,
    SupplierUpdateSchema,
)
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

DEFAULT_PROJECT_ID = "00000000-0000-4000-a000-000000000002"


@router.get("", response_model=APIResponse[list[SupplierSummarySchema]])
async def list_suppliers(
    project_id: str = Query(DEFAULT_PROJECT_ID),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    country: str | None = Query(None),
    service: SupplierService = Depends(get_supplier_service),
):
    suppliers, meta = await service.list_suppliers(
        project_id,
        page=page,
        limit=limit,
        search=search,
        country=country,
    )
    return APIResponse(
        success=True,
        message="Suppliers retrieved successfully.",
        data=suppliers,
        meta=meta,
    )


@router.get("/{supplier_id}", response_model=APIResponse[SupplierDetailSchema])
async def get_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
):
    supplier = await service.get_supplier(supplier_id)
    if not supplier:
        raise AppHTTPException(
            status_code=404,
            code="SUPPLIER_NOT_FOUND",
            message=f"Supplier {supplier_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Supplier retrieved successfully.",
        data=supplier,
    )


@router.post("/compare", response_model=APIResponse[list[SupplierDetailSchema]])
async def compare_suppliers(
    payload: SupplierCompareRequest,
    service: SupplierService = Depends(get_supplier_service),
):
    suppliers = []
    for supplier_id in payload.supplier_ids:
        supplier = await service.get_supplier(supplier_id)
        if not supplier:
            raise AppHTTPException(
                status_code=404,
                code="SUPPLIER_NOT_FOUND",
                message=f"Supplier {supplier_id} was not found.",
            )
        suppliers.append(supplier)

    return APIResponse(
        success=True,
        message="Supplier comparison generated successfully.",
        data=suppliers,
    )

@router.post("", response_model=APIResponse[SupplierSummarySchema], status_code=201)
async def create_supplier(
    payload: SupplierCreateSchema,
    service: SupplierService = Depends(get_supplier_service),
):
    supplier = await service.create_supplier(payload)
    return APIResponse(
        success=True,
        message="Supplier created successfully.",
        data=supplier,
    )


@router.patch("/{supplier_id}", response_model=APIResponse[SupplierSummarySchema])
async def update_supplier(
    supplier_id: str,
    payload: SupplierUpdateSchema,
    service: SupplierService = Depends(get_supplier_service),
):
    supplier = await service.update_supplier(supplier_id, payload)
    if not supplier:
        raise AppHTTPException(
            status_code=404,
            code="SUPPLIER_NOT_FOUND",
            message=f"Supplier {supplier_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Supplier updated successfully.",
        data=supplier,
    )


@router.delete("/{supplier_id}", response_model=APIResponse[None])
async def delete_supplier(
    supplier_id: str,
    service: SupplierService = Depends(get_supplier_service),
):
    success = await service.delete_supplier(supplier_id)
    if not success:
        raise AppHTTPException(
            status_code=404,
            code="SUPPLIER_NOT_FOUND",
            message=f"Supplier {supplier_id} was not found.",
        )
    return APIResponse(
        success=True,
        message="Supplier deleted successfully.",
        data=None,
    )
