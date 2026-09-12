import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from app.schemas.governance import RiskAssessment, RiskLevel


class RiskEngine:
    """
    Evaluates proposed tool actions and assigns a numerical risk score (0 to 100).
    
    Risk Tiers:
      - Low Risk (0-30): Read-only actions (fetching unread emails, searching threads, checking calendar availability).
      - Medium Risk (31-70): Non-destructive internal actions (creating calendar events, saving drafts).
      - High Risk (71-100): Sensitive or irreversible external actions (sending external emails, deleting events, rescheduling critical meetings).
    
    Also runs phishing/malicious content checks against incoming email senders and links.
    """

    # Baseline scores for known actions
    ACTION_BASE_SCORES: Dict[str, int] = {
        # Low risk (read-only): 0 - 30
        "fetch_unread_emails": 10,
        "search_threads": 10,
        "read_email": 10,
        "check_calendar_availability": 15,
        "get_calendar_events": 15,
        "get_contact_info": 10,
        "query_memory": 10,
        "fetch_documents": 15,

        # Medium risk (internal / non-destructive writes): 31 - 70
        "create_calendar_event": 45,
        "save_draft_email": 35,
        "update_draft_email": 40,
        "update_calendar_event": 50,
        "tag_email": 35,
        "create_commitment": 40,
        "store_memory": 35,

        # High risk (sensitive, irreversible, or external actions): 71 - 100
        "send_email": 80,
        "send_external_email": 85,
        "delete_email": 85,
        "delete_calendar_event": 80,
        "reschedule_critical_meeting": 85,
        "execute_transaction": 95,
        "revoke_access": 90,
        "modify_system_config": 95,
    }

    # Suspicious domain TLDs and patterns
    SUSPICIOUS_TLDS = {".xyz", ".top", ".buzz", ".work", ".click", ".surf", ".gq", ".cf", ".tk", ".ml"}
    
    # Suspicious keywords in URLs/links
    SUSPICIOUS_LINK_KEYWORDS = [
        "login", "verify", "secure-account", "update-payment", "banking",
        "confirm-identity", "password-reset", "wallet", "invoice-download"
    ]

    # Phishing/urgent keywords common in attack emails
    PHISHING_KEYWORDS = [
        "urgent wire transfer", "wire funds immediately", "gift card", 
        "account suspended", "immediate action required", "verify your account",
        "unauthorized login detected", "click here to unlock", "crypto payout"
    ]

    # Well-known free/temporary email domains frequently misused in spoofing
    DISPOSABLE_OR_SUSPICIOUS_EMAIL_PATTERNS = [
        r"@.*tempmail.*", r"@.*guerrillamail.*", r"@.*10minutemail.*", r"@.*throwaway.*"
    ]

    def evaluate_action(self, action_type: str, payload: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        Evaluates an action and its payload to determine risk score, level, and flags.
        """
        payload = payload or {}
        reasons: List[str] = []
        security_flags: List[str] = []

        # Determine base score
        base_score = self.ACTION_BASE_SCORES.get(action_type)
        if base_score is None:
            # Heuristic fallback if action is unrecognized
            if any(k in action_type.lower() for k in ["delete", "remove", "drop", "purge"]):
                base_score = 85
                reasons.append(f"Unrecognized destructive action '{action_type}' assigned default high risk.")
            elif any(k in action_type.lower() for k in ["send", "post", "execute", "dispatch"]):
                base_score = 75
                reasons.append(f"Unrecognized external write action '{action_type}' assigned default high risk.")
            elif any(k in action_type.lower() for k in ["create", "add", "update", "draft"]):
                base_score = 50
                reasons.append(f"Unrecognized modification action '{action_type}' assigned default medium risk.")
            else:
                base_score = 20
                reasons.append(f"Unrecognized read-only or query action '{action_type}' assigned default low risk.")
        else:
            reasons.append(f"Base risk for '{action_type}' is {base_score}.")

        score = base_score

        # Check payload specifics
        # 1. External email recipient checks
        if "to" in payload or "recipients" in payload:
            recipients = payload.get("to") or payload.get("recipients")
            if isinstance(recipients, str):
                recipients = [recipients]
            elif not isinstance(recipients, list):
                recipients = []

            if len(recipients) > 10:
                score += 15
                reasons.append(f"High volume recipients ({len(recipients)} recipients).")

        # 2. Critical meeting modifications
        if action_type in ["update_calendar_event", "delete_calendar_event", "reschedule_critical_meeting"]:
            is_critical = payload.get("is_critical", False) or payload.get("critical", False)
            title = str(payload.get("title", "")).lower()
            if is_critical or any(term in title for term in ["board", "investor", "qbr", "all-hands", "executive"]):
                score = max(score, 85)
                reasons.append("Affects a critical/executive calendar meeting.")

        # 3. Phishing and malicious content scans in payload (body, subject, sender)
        content_to_check = f"{payload.get('subject', '')} {payload.get('body', '')} {payload.get('text', '')}"
        sender = payload.get("sender") or payload.get("from")
        
        phishing_results = self.detect_phishing(sender=sender, content=content_to_check)
        if phishing_results["is_suspicious"]:
            score = max(score, 90)
            security_flags.extend(phishing_results["flags"])
            reasons.extend(phishing_results["flags"])

        # Cap score between 0 and 100
        score = max(0, min(100, score))

        # Categorize tier
        if score <= 30:
            level = RiskLevel.LOW
            requires_approval = False
        elif score <= 70:
            level = RiskLevel.MEDIUM
            requires_approval = False
        else:
            level = RiskLevel.HIGH
            requires_approval = True

        return RiskAssessment(
            score=score,
            level=level,
            action_type=action_type,
            reasons=reasons,
            security_flags=security_flags,
            requires_approval=requires_approval,
        )

    def detect_phishing(
        self,
        sender: Optional[str] = None,
        content: Optional[str] = None,
        links: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Scans sender, email content, and links for malicious or phishing patterns.
        """
        flags: List[str] = []
        content = content or ""
        extracted_links = links or []

        # 1. Inspect sender
        if sender:
            sender_lower = sender.lower()
            for pattern in self.DISPOSABLE_OR_SUSPICIOUS_EMAIL_PATTERNS:
                if re.search(pattern, sender_lower):
                    flags.append(f"Suspicious disposable/untrusted email sender: {sender}")

            # Check for suspicious display name spoofing (e.g. "CEO <hacker@gmail.com>")
            if "<" in sender and ">" in sender:
                display_name = sender[: sender.index("<")].lower()
                email_addr = sender[sender.index("<") + 1 : sender.index(">")].lower()
                if any(exec_term in display_name for exec_term in ["ceo", "cfo", "founder", "director", "security"]):
                    if any(public_domain in email_addr for public_domain in ["@gmail.com", "@yahoo.com", "@outlook.com", "@hotmail.com"]):
                        flags.append(f"Executive impersonation flag in sender address: {sender}")

        # 2. Extract and inspect URLs if not explicitly passed
        if not extracted_links and content:
            extracted_links = re.findall(r"https?://[^\s<>\"']+", content)

        for url in extracted_links:
            link_flag = self._inspect_link(url)
            if link_flag:
                flags.append(link_flag)

        # 3. Phishing keywords in text
        content_lower = content.lower()
        for phrase in self.PHISHING_KEYWORDS:
            if phrase in content_lower:
                flags.append(f"Phishing keyword detected in message: '{phrase}'")

        return {
            "is_suspicious": len(flags) > 0,
            "flags": flags,
            "inspected_links_count": len(extracted_links),
        }

    def _inspect_link(self, url: str) -> Optional[str]:
        """Inspects a single link for suspicious traits."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()

            # Check raw IP as hostname
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$", domain):
                return f"Suspicious raw IP host in link: {url}"

            # Check suspicious TLDs
            for tld in self.SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    return f"Link uses high-risk TLD ({tld}): {url}"

            # Check combination of login/banking keywords on non-official domain
            for kw in self.SUSPICIOUS_LINK_KEYWORDS:
                if kw in domain or kw in path:
                    return f"Potential credential harvester link detected ('{kw}'): {url}"

        except Exception:
            return f"Malformed URL detected: {url}"

        return None
