import re
from datetime import datetime, time
from typing import Any, Dict, List, Optional
from app.schemas.governance import PolicyEvaluationResult, PolicyViolation


class PolicyEngine:
    """
    Enforces business rules and governance policies:
      1. Focus Hours Policy: Prevents auto-scheduling meetings during user-defined focus windows.
      2. External Communication Policy: Flags outbound emails to domains outside the user's primary domain.
      3. Financial/Legal Guardrail: Flags messages containing financial or legal key terms for mandatory human review.
    """

    # Financial key terms triggering guardrails
    FINANCIAL_TERMS = [
        "wire transfer", "bank transfer", "invoice", "payment", "routing number",
        "iban", "swift", "salary", "bonus", "equity grant", "wire funds", "remittance",
        "credit card", "payroll", "budget approval", "pricing discount", "contract value"
    ]

    # Legal key terms triggering guardrails
    LEGAL_TERMS = [
        "nda", "non-disclosure", "confidentiality agreement", "indemnification",
        "liability", "litigation", "lawsuit", "subpoena", "settlement", "power of attorney",
        "intellectual property", "cease and desist", "breach of contract", "terms of service",
        "binding agreement", "arbitration"
    ]

    def __init__(self, primary_domain: str = "company.com"):
        self.primary_domain = primary_domain.lower().strip("@")

    def evaluate(
        self,
        action_type: str,
        payload: Optional[Dict[str, Any]] = None,
        focus_windows: Optional[List[Dict[str, str]]] = None,
        allowed_domains: Optional[List[str]] = None,
    ) -> PolicyEvaluationResult:
        """
        Evaluates an action against all active governance policies.
        """
        payload = payload or {}
        violations: List[PolicyViolation] = []
        requires_human_approval = False

        # 1. Evaluate Focus Hours Policy
        if action_type in ["create_calendar_event", "reschedule_calendar_event", "schedule_meeting"]:
            focus_violation = self.check_focus_hours(
                start_time=payload.get("start_time"),
                end_time=payload.get("end_time"),
                focus_windows=focus_windows,
            )
            if focus_violation:
                violations.append(focus_violation)
                requires_human_approval = True

        # 2. Evaluate External Communication Policy
        if action_type in ["send_email", "send_external_email", "reply_email"]:
            ext_violations = self.check_external_communication(
                recipients=payload.get("to") or payload.get("recipients", []),
                allowed_domains=allowed_domains,
            )
            if ext_violations:
                violations.extend(ext_violations)
                requires_human_approval = True

        # 3. Evaluate Financial/Legal Guardrail
        content = f"{payload.get('subject', '')} {payload.get('body', '')} {payload.get('text', '')} {payload.get('description', '')}"
        guardrail_violations = self.check_financial_and_legal_guardrails(content)
        if guardrail_violations:
            violations.extend(guardrail_violations)
            requires_human_approval = True

        is_compliant = len(violations) == 0

        return PolicyEvaluationResult(
            is_compliant=is_compliant,
            violations=violations,
            requires_human_approval=requires_human_approval,
            metadata={
                "action_type": action_type,
                "primary_domain": self.primary_domain,
            },
        )

    def check_focus_hours(
        self,
        start_time: Optional[Any],
        end_time: Optional[Any] = None,
        focus_windows: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[PolicyViolation]:
        """
        Checks if the event overlaps with defined focus hours.
        Default focus window: 09:00 - 11:30 (deep work morning).
        """
        if not start_time:
            return None

        # Parse start_time if string
        meeting_time: Optional[time] = None
        if isinstance(start_time, str):
            try:
                # Support ISO strings e.g. "2026-09-12T09:30:00Z" or "09:30"
                if "T" in start_time:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    meeting_time = dt.time()
                elif ":" in start_time:
                    parts = start_time.split(":")
                    meeting_time = time(int(parts[0]), int(parts[1]))
            except Exception:
                meeting_time = None
        elif isinstance(start_time, datetime):
            meeting_time = start_time.time()
        elif isinstance(start_time, time):
            meeting_time = start_time

        if not meeting_time:
            return None

        # Windows can be passed as [{"start": "09:00", "end": "11:30"}]
        windows = focus_windows or [{"start": "09:00", "end": "11:30"}]

        for window in windows:
            try:
                w_start_parts = [int(p) for p in window["start"].split(":")]
                w_end_parts = [int(p) for p in window["end"].split(":")]
                w_start = time(w_start_parts[0], w_start_parts[1])
                w_end = time(w_end_parts[0], w_end_parts[1])

                if w_start <= meeting_time <= w_end:
                    return PolicyViolation(
                        policy_name="Focus Hours Policy",
                        rule="no_auto_scheduling_during_focus_hours",
                        description=(
                            f"Proposed meeting at {meeting_time.strftime('%H:%M')} conflicts with "
                            f"Focus Hours window ({window['start']} - {window['end']})."
                        ),
                        severity="high",
                    )
            except Exception:
                continue

        return None

    def check_external_communication(
        self,
        recipients: Any,
        allowed_domains: Optional[List[str]] = None,
    ) -> List[PolicyViolation]:
        """
        Flags any outbound email to domains outside the user's primary domain.
        """
        violations: List[PolicyViolation] = []
        if isinstance(recipients, str):
            recipients = [recipients]
        elif not isinstance(recipients, list):
            return violations

        trusted_domains = {self.primary_domain}
        if allowed_domains:
            trusted_domains.update(d.lower().strip("@") for d in allowed_domains)

        external_recipients: List[str] = []
        for r in recipients:
            if not r or "@" not in str(r):
                continue
            email_clean = str(r).strip()
            # Extract actual email inside angles if formatted like "Name <email@domain.com>"
            if "<" in email_clean and ">" in email_clean:
                email_clean = email_clean[email_clean.index("<") + 1 : email_clean.index(">")]
            
            domain = email_clean.split("@")[-1].lower().strip()
            if domain not in trusted_domains:
                external_recipients.append(email_clean)

        if external_recipients:
            violations.append(
                PolicyViolation(
                    policy_name="External Communication Policy",
                    rule="external_domain_restricted",
                    description=(
                        f"Outbound communication targets external domains outside '{self.primary_domain}': "
                        f"{', '.join(external_recipients)}"
                    ),
                    severity="warning",
                )
            )

        return violations

    def check_financial_and_legal_guardrails(self, text: str) -> List[PolicyViolation]:
        """
        Flags messages containing financial or legal key terms for mandatory human review.
        """
        violations: List[PolicyViolation] = []
        if not text:
            return violations

        text_lower = text.lower()

        # Financial terms check
        matched_financial = [term for term in self.FINANCIAL_TERMS if re.search(r"\b" + re.escape(term) + r"\b", text_lower)]
        if matched_financial:
            violations.append(
                PolicyViolation(
                    policy_name="Financial Guardrail",
                    rule="financial_terms_detected",
                    description=f"Message contains sensitive financial terms: {', '.join(matched_financial)}.",
                    severity="high",
                )
            )

        # Legal terms check
        matched_legal = [term for term in self.LEGAL_TERMS if re.search(r"\b" + re.escape(term) + r"\b", text_lower)]
        if matched_legal:
            violations.append(
                PolicyViolation(
                    policy_name="Legal Guardrail",
                    rule="legal_terms_detected",
                    description=f"Message contains sensitive legal terms: {', '.join(matched_legal)}.",
                    severity="high",
                )
            )

        return violations
