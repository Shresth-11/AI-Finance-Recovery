import re
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.base import ExceptionRecord, Order, Payment, Settlement, Invoice
from app.schemas.copilot import CopilotQueryRequest, CopilotQueryResponse
from app.core.config import settings

class CopilotService:
    def __init__(self, db: Session):
        self.db = db

    def query(self, req: CopilotQueryRequest) -> CopilotQueryResponse:
        query_text = req.query.strip()

        # Check for OPENAI_API_KEY environment configuration
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

        if api_key and api_key.startswith("sk-"):
            try:
                return self._query_openai(query_text, req.context_exception_id, api_key)
            except Exception:
                # Fallback safely to deterministic grounded engine if LLM API call fails
                pass

        # Deterministic Grounded Rules Engine (Default Fallback Mode)
        return self._query_deterministic(query_text, req.context_exception_id)

    def _query_deterministic(self, query: str, context_id: Optional[int] = None) -> CopilotQueryResponse:
        q_lower = query.lower()
        cited_ids: List[str] = []
        suggested_actions: List[str] = []

        # 1. Check for specific exception code or ID query
        exc_match = re.search(r"exc_?(\d+)", q_lower)
        if exc_match or context_id:
            target_id = context_id or int(exc_match.group(1))
            exc = self.db.query(ExceptionRecord).filter(
                (ExceptionRecord.id == target_id) | (ExceptionRecord.exception_code == f"EXC_{target_id}")
            ).first()

            if exc:
                cited_ids.append(exc.exception_code)
                if exc.order_id: cited_ids.append(exc.order_id)
                if exc.payment_id: cited_ids.append(exc.payment_id)
                if exc.settlement_id: cited_ids.append(exc.settlement_id)

                ev_item = exc.evidence_items[0] if exc.evidence_items else None
                summary_text = ev_item.summary if ev_item else ""
                remediation = "Review linked order, payment capture, and settlement advice records."

                exc_type_clean = exc.exception_type.replace("_", " ")
                answer = (
                    f"Exception {exc.exception_code} ({exc_type_clean}) involves an affected discrepancy amount of ₹{exc.discrepancy_amount:,.2f}.\n\n"
                    f"Evidence:\n"
                    f"- {summary_text or f'Flagged due to variance in {exc_type_clean}.'}\n"
                    f"- Linked Entity IDs: Order `{exc.order_id or 'N/A'}`, Payment `{exc.payment_id or 'N/A'}`, Settlement `{exc.settlement_id or 'N/A'}`.\n\n"
                    f"Recommended next step:\n"
                    f"{remediation}\n\n"
                    f"Limits:\n"
                    f"Based on loaded records in the current reconciliation run. Human review is required before updating status."
                )

                if exc.status == "OPEN":
                    suggested_actions.append(f"Review exception {exc.exception_code}")
                    suggested_actions.append(f"Approve resolution for {exc.exception_code}")

                return CopilotQueryResponse(
                    query=query,
                    answer=answer,
                    cited_evidence_ids=cited_ids,
                    confidence_score=float(exc.ai_confidence_score or 0.95),
                    limitations="Analysis strictly grounded in loaded SQLite database records.",
                    fallback_mode=True,
                    suggested_actions=suggested_actions,
                )

        # 2. Highest-value / Money at risk query
        if any(k in q_lower for k in ["highest", "value", "top", "worst", "priority", "critical", "risk", "money"]):
            top_exceptions = (
                self.db.query(ExceptionRecord)
                .filter(ExceptionRecord.status == "OPEN")
                .order_by(desc(ExceptionRecord.discrepancy_amount))
                .limit(5)
                .all()
            )

            if not top_exceptions:
                return CopilotQueryResponse(
                    query=query,
                    answer="No unresolved open exceptions found in the current reconciliation run.",
                    cited_evidence_ids=[],
                    confidence_score=1.0,
                    limitations="No open items in SQLite database.",
                    fallback_mode=True,
                )

            total_risk = sum(e.discrepancy_amount for e in top_exceptions)
            top_item = top_exceptions[0]
            cited_ids = [e.exception_code for e in top_exceptions]

            evidence_lines = []
            for e in top_exceptions[:3]:
                evidence_lines.append(f"- {e.exception_code} ({e.exception_type.replace('_', ' ')}): ₹{e.discrepancy_amount:,.2f} linked to payment `{e.payment_id or 'N/A'}`.")

            answer = (
                f"Money at risk is ₹{total_risk:,.2f} across the top open exceptions. The largest contributor is {top_item.exception_code} ({top_item.exception_type.replace('_', ' ')} of ₹{top_item.discrepancy_amount:,.2f}).\n\n"
                f"Evidence:\n" + "\n".join(evidence_lines) + "\n\n"
                f"Recommended next step:\n"
                f"Review {top_item.exception_code} first because it represents the highest discrepancy amount.\n\n"
                f"Limits:\n"
                f"This summary uses records in the latest loaded reconciliation run."
            )

            suggested_actions = ["Review critical exceptions", "Export filtered CSV report"]

            return CopilotQueryResponse(
                query=query,
                answer=answer,
                cited_evidence_ids=cited_ids,
                confidence_score=0.98,
                limitations="Grounded query from active reconciliation database.",
                fallback_mode=True,
                suggested_actions=suggested_actions,
            )

        # 3. Common exception types / Category breakdown query
        if any(k in q_lower for k in ["common", "type", "category", "breakdown", "distribution"]):
            type_counts = (
                self.db.query(
                    ExceptionRecord.exception_type,
                    func.count(ExceptionRecord.id).label("count"),
                    func.sum(ExceptionRecord.discrepancy_amount).label("total_amount"),
                )
                .group_by(ExceptionRecord.exception_type)
                .order_by(desc("count"))
                .all()
            )

            if not type_counts:
                return CopilotQueryResponse(
                    query=query,
                    answer="I don't have enough data in the current reconciliation run to answer that.",
                    cited_evidence_ids=[],
                    confidence_score=1.0,
                    limitations="Database is empty.",
                    fallback_mode=True,
                )

            evidence_lines = []
            for row in type_counts[:4]:
                t_name = row.exception_type.replace("_", " ")
                amt = row.total_amount or 0.0
                evidence_lines.append(f"- {row.count} {t_name} cases accounting for ₹{amt:,.2f}.")

            answer = (
                f"The current run contains exceptions across {len(type_counts)} categories.\n\n"
                f"Evidence:\n" + "\n".join(evidence_lines) + "\n\n"
                f"Recommended next step:\n"
                f"Filter the exceptions queue by severity to prioritize high-value discrepancies first.\n\n"
                f"Limits:\n"
                f"Based on loaded dataset records."
            )

            return CopilotQueryResponse(
                query=query,
                answer=answer,
                cited_evidence_ids=["227_EXCEPTIONS_AGGREGATE"],
                confidence_score=0.96,
                limitations="Aggregated breakdown across active exceptions.",
                fallback_mode=True,
                suggested_actions=["Filter by severity"],
            )

        # 4. Settlement delay query
        if any(k in q_lower for k in ["settlement", "delay", "payout", "sla", "bank"]):
            delayed_list = (
                self.db.query(ExceptionRecord)
                .filter(ExceptionRecord.exception_type == "DELAYED_SETTLEMENT")
                .all()
            )

            for d in delayed_list[:5]:
                if d.exception_code: cited_ids.append(d.exception_code)

            count = len(delayed_list)
            total_amt = sum(d.discrepancy_amount for d in delayed_list) if delayed_list else 0.0

            answer = (
                f"Detected {count} delayed settlement exceptions accounting for ₹{total_amt:,.2f}.\n\n"
                f"Evidence:\n"
                f"- Payout dates exceeded the standard 2-business-day settlement window.\n"
                f"- Affected records include settlements linked to UTR banking references.\n\n"
                f"Recommended next step:\n"
                f"Review delayed settlement items for vendor SLA review.\n\n"
                f"Limits:\n"
                f"Uses settlement feed dates loaded in current run."
            )

            return CopilotQueryResponse(
                query=query,
                answer=answer,
                cited_evidence_ids=cited_ids or ["DELAYED_SETTLEMENT_SLA"],
                confidence_score=0.95,
                limitations="Filtered on DELAYED_SETTLEMENT category.",
                fallback_mode=True,
                suggested_actions=["View delayed settlements"],
            )

        # 5. Out of domain / Insufficient evidence query
        return CopilotQueryResponse(
            query=query,
            answer="I don't have enough data in the current reconciliation run to answer that.",
            cited_evidence_ids=[],
            confidence_score=0.50,
            limitations="Query outside active financial reconciliation dataset context.",
            fallback_mode=True,
            suggested_actions=["Try: Show the highest-value unresolved issues", "Try: What are the most common exception types?"],
        )

    def _query_openai(self, query: str, context_id: Optional[int], api_key: str) -> CopilotQueryResponse:
        import openai

        # Build context from database
        context_records = self._query_deterministic(query, context_id)

        client = openai.OpenAI(api_key=api_key)
        system_prompt = (
            "You are LedgerGuard AI Copilot, a concise finance operations colleague. "
            "Tone: Calm, professional, concise, honest about uncertainty. "
            "Format: Start with direct answer, followed by short sections: Evidence, Recommended next step, Limits. "
            "Never use filler, emojis, or chatbot phrases ('Great question', 'Absolutely'). "
            "If evidence is insufficient, say exactly: 'I don't have enough data in the current reconciliation run to answer that.' "
            "Never claim certainty without evidence, make up details, claim to execute actions, or offer financial/legal advice. "
            "Always cite exact exception IDs and transaction IDs."
        )

        user_content = f"Database Context:\n{context_records.answer}\n\nUser Question: {query}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=400,
        )

        answer_text = response.choices[0].message.content or context_records.answer

        return CopilotQueryResponse(
            query=query,
            answer=answer_text,
            cited_evidence_ids=context_records.cited_evidence_ids,
            confidence_score=0.99,
            limitations="Response grounded in SQLite database context.",
            fallback_mode=False,
            suggested_actions=context_records.suggested_actions,
        )
