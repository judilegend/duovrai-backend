from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

class PlanType(str, Enum):
    ESSENTIEL = "ESSENTIEL"
    PREMIUM = "PREMIUM"
