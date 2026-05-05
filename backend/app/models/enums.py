from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    agent = "agent"
    customer = "customer"


class TicketStatus(StrEnum):
    open = "open"
    pending = "pending"
    solved = "solved"
    closed = "closed"


class TicketPriority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

