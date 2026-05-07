from collections.abc import Callable

from app.models.ticket import Ticket, TicketDiagnostic


PASSWORD_KEYWORDS = ("password", "login", "log in", "sign in", "signin", "locked", "mfa", "reset")
CAMERA_KEYWORDS = ("camera", "offline", "video", "recording", "stream", "heartbeat")
INSTALL_KEYWORDS = ("install", "installation", "post install", "activation", "setup", "commission")
ROUTER_KEYWORDS = ("router", "robustel", "robustel", "sim", "network", "connection", "store down")


def ticket_text(ticket: Ticket) -> str:
    return f"{ticket.subject} {ticket.description} {ticket.company or ''} {ticket.store or ''}".lower()


def classify_ticket_intent(ticket: Ticket) -> str:
    text = ticket_text(ticket)
    if any(keyword in text for keyword in PASSWORD_KEYWORDS):
        return "password_issue"
    if any(keyword in text for keyword in CAMERA_KEYWORDS):
        return "camera_status"
    if any(keyword in text for keyword in INSTALL_KEYWORDS):
        return "post_install_check"
    if any(keyword in text for keyword in ROUTER_KEYWORDS):
        return "network_or_router"
    return "general_support"


def make_diagnostic(
    ticket: Ticket,
    intent: str,
    playbook: str,
    check_name: str,
    service: str,
    status: str,
    severity: str,
    summary: str,
    details: dict,
) -> TicketDiagnostic:
    return TicketDiagnostic(
        ticket_id=ticket.id,
        intent=intent,
        playbook=playbook,
        check_name=check_name,
        service=service,
        status=status,
        severity=severity,
        summary=summary,
        details=details,
    )


def check_identity_last_login(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    email = ticket.requester_email or (ticket.customer.email if ticket.customer else f"user_id:{ticket.customer_id}")
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "identity_last_login",
        "identity",
        "needs_review" if "password" in ticket_text(ticket) else "ok",
        "warning" if "password" in ticket_text(ticket) else "info",
        f"Mock identity check queued for {email}. Replace with real last-login API.",
        {"email": email, "mock": True, "next_connector": "identity_client.last_login"},
    )


def check_login_status(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "login_status",
        "identity",
        "needs_review",
        "warning",
        "Mock login-status check suggests reviewing failed logins and account lock state.",
        {"mock": True, "next_connector": "identity_client.login_status"},
    )


def check_camera_status(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "camera_status",
        "camera",
        "needs_review",
        "warning",
        "Mock camera status check queued. Real connector should read online state and last heartbeat.",
        {"store": ticket.store, "mock": True, "next_connector": "camera_client.status"},
    )


def check_robustel_status(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "robustel_router_status",
        "robustel",
        "needs_review",
        "warning",
        "Mock Robustel router check queued. Real connector should read router, SIM, and signal state.",
        {"store": ticket.store, "mock": True, "next_connector": "robustel_client.router_status"},
    )


def check_post_install(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "post_install_check",
        "installations",
        "needs_review",
        "info",
        "Mock post-install checklist queued for device activation and install completion.",
        {"company": ticket.company, "store": ticket.store, "mock": True, "next_connector": "post_install_client.check"},
    )


def check_ticket_context(ticket: Ticket, intent: str, playbook: str) -> TicketDiagnostic:
    missing = [field for field, value in {"company": ticket.company, "store": ticket.store, "requester_email": ticket.requester_email}.items() if not value]
    return make_diagnostic(
        ticket,
        intent,
        playbook,
        "ticket_context",
        "ticketdesk",
        "ok" if not missing else "needs_info",
        "info" if not missing else "warning",
        "Ticket has enough routing context." if not missing else f"Ticket is missing: {', '.join(missing)}.",
        {"missing_fields": missing, "mock": False},
    )


DiagnosticCheck = Callable[[Ticket, str, str], TicketDiagnostic]

PLAYBOOKS: dict[str, list[DiagnosticCheck]] = {
    "password_issue": [check_identity_last_login, check_login_status, check_ticket_context],
    "camera_status": [check_camera_status, check_robustel_status, check_ticket_context],
    "post_install_check": [check_post_install, check_camera_status, check_robustel_status, check_ticket_context],
    "network_or_router": [check_robustel_status, check_camera_status, check_ticket_context],
    "general_support": [check_ticket_context],
}


def run_ticket_diagnostics(ticket: Ticket) -> list[TicketDiagnostic]:
    intent = classify_ticket_intent(ticket)
    playbook = intent
    checks = PLAYBOOKS.get(intent, PLAYBOOKS["general_support"])
    return [check(ticket, intent, playbook) for check in checks]
