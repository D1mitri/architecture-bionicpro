from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional

from ..simple_auth import get_current_user_simple
from ..models import UserReport, DebugResponse

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/me", response_model=UserReport)
async def get_my_report(
    include_history: bool = Query(True, description="Включать историю данных"),
    history_limit: int = Query(5, ge=1, le=50, description="Лимит записей истории"),
    current_user: dict = Depends(get_current_user_simple)
):

    try:
        user_id = current_user.get("user_id", 101)
        username = current_user.get("preferred_username", "unknown")
        user_guid = current_user.get("user_guid", "")
        email = current_user.get("email", f"user{user_id}@example.com")

        import datetime

        report_data = {
            "user_id": user_id,
            "customer_name": username.title(),
            "customer_email": email,
            "region": "Default Region",
            "account_status": "active",
            "subscription_type": "premium",
            "avg_sensor_data": 25.5,
            "avg_battery_level": 95.0,
            "total_readings": 150,
            "first_reading": datetime.datetime.now().isoformat(),
            "last_reading": datetime.datetime.now().isoformat(),
            "data_quality_score": "HIGH",
            "battery_health": "GOOD",
            "load_date": datetime.date.today().isoformat(),
            "etl_timestamp": datetime.datetime.now().isoformat(),
            "user_guid": user_guid,
            "auth_info": {
                "username": username,
                "user_guid": user_guid,
                "generated_user_id": user_id,
                "auth_method": "guid_based"
            }
        }

        history = []
        if include_history:
            for i in range(min(history_limit, 5)):
                history.append({
                    "load_date": (datetime.date.today() - datetime.timedelta(days=i)).isoformat(),
                    "avg_sensor_data": 25.5 - i * 0.5,
                    "avg_battery_level": max(30.0, 95.0 - i * 2),
                    "total_readings": 150 + i * 10,
                    "data_quality_score": "HIGH",
                    "battery_health": "GOOD" if (95.0 - i * 2) > 80 else "WARNING",
                    "etl_timestamp": (datetime.datetime.now() - datetime.timedelta(days=i)).isoformat()
                })

        return UserReport(
            **report_data,
            history=history
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/debug/auth-info", response_model=DebugResponse)
async def debug_auth_info(current_user: dict = Depends(get_current_user_simple)):
    return DebugResponse(
        message="Authentication successful",
        user_info={
            "username": current_user.get("preferred_username"),
            "email": current_user.get("email"),
            "user_guid": current_user.get("user_guid"),
            "user_id": current_user.get("user_id"),
            "token_subject": current_user.get("sub")
        },
        calculation_details={
            "guid_source": f"{current_user.get('preferred_username', '')}:{current_user.get('email', '')}",
            "guid_algorithm": "MD5 -> UUID",
            "user_id_algorithm": "First 8 chars of GUID (hex) mod 1000 + 1"
        }
    )