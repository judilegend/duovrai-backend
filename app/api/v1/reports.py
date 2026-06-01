import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.order_repository import order_repository
from app.repositories.report_repository import report_repository
from app.schemas.schemas import OrderResponse, ReportResponse
from app.types.enums import OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_status(order_id: str, db: Session = Depends(get_db)):
    """
    Returns the complete order status, allowing the frontend to poll status
    during background PDF generation.
    """
    order = order_repository.get(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.get("/reports/{order_id}", response_model=ReportResponse)
def get_report_details(order_id: str, db: Session = Depends(get_db)):
    """
    Fetches the details of the compatibility report associated with an order.
    """
    order = order_repository.get(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    report = report_repository.get_by_order_id(db, order_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not generated yet or failed. Check order status."
        )
        
    return report


@router.get("/reports/{order_id}/download")
def download_pdf_report(order_id: str, db: Session = Depends(get_db)):
    """
    Downloads the compiled WeasyPrint PDF report as a binary response.
    """
    order = order_repository.get(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready yet. Current status: {order.status.value}"
        )

    report = report_repository.get_by_order_id(db, order_id)
    if not report or not report.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file reference not found."
        )

    if not os.path.exists(report.pdf_path):
        logger.error(f"PDF file exists in DB but not on disk: {report.pdf_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file is missing on storage. Contact support."
        )

    # Format download name
    download_name = f"Duovrai_Analyse_{order.partner1_name}_{order.partner2_name}.pdf"
    
    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=download_name
    )
