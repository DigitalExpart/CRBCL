"""Validation service for Assessment answers, conditional rules, data types, and required questions."""

from __future__ import annotations

import uuid
from typing import Any

from app.models.assessment import AssessmentQuestion, AssessmentTemplateVersion


class AssessmentValidationService:
    @staticmethod
    def evaluate_condition(
        condition: dict[str, Any] | None,
        answers_by_key: dict[str, Any],
    ) -> bool:
        """
        Evaluate safe declarative visibility conditions.
        Format:
        {
            "depends_on_question_key": "substance_use_detected",
            "operator": "equals" | "not_equals" | "is_true" | "is_false" | "contains",
            "value": true
        }
        """
        if not condition:
            return True

        dep_key = condition.get("depends_on_question_key")
        if not dep_key:
            return True

        current_val = answers_by_key.get(dep_key)
        op = condition.get("operator", "equals")
        target_val = condition.get("value")

        if op == "is_true":
            return bool(current_val) is True
        elif op == "is_false":
            return bool(current_val) is False
        elif op == "equals":
            return current_val == target_val
        elif op == "not_equals":
            return current_val != target_val
        elif op == "contains":
            if isinstance(current_val, list):
                return target_val in current_val
            elif isinstance(current_val, str) and target_val:
                return str(target_val).lower() in current_val.lower()
            return False

        return True

    @classmethod
    def validate_answers(
        cls,
        template_version: AssessmentTemplateVersion,
        answers_data: list[dict[str, Any]],
        is_completing: bool = False,
    ) -> list[str]:
        """
        Validate submitted answers against the template version.
        Returns a list of error strings (empty if valid).
        """
        errors: list[str] = []

        # Build lookup maps for questions in this version
        questions_map: dict[uuid.UUID, AssessmentQuestion] = {}
        questions_by_key: dict[str, AssessmentQuestion] = {}
        options_by_key_per_question: dict[uuid.UUID, dict[str, uuid.UUID]] = {}
        for sec in template_version.sections:
            for q in sec.questions:
                questions_map[q.id] = q
                questions_by_key[q.key] = q
                options_by_key_per_question[q.id] = {opt.key: opt.id for opt in q.options}

        # Map answers for condition evaluation
        submitted_by_qid: dict[uuid.UUID, dict[str, Any]] = {}
        answers_by_key: dict[str, Any] = {}

        for item in answers_data:
            qid = item.get("question_id")
            if not qid and item.get("question_key"):
                matched_q = questions_by_key.get(item["question_key"])
                if matched_q:
                    qid = matched_q.id
                    item["question_id"] = qid
            if not qid or qid not in questions_map:
                identifier = qid or item.get("question_key")
                errors.append(
                    f"Question '{identifier}' does not belong to template version {template_version.version_number}."
                )
                continue

            # Auto-resolve selected_option_keys if provided
            if item.get("selected_option_keys") and not item.get("selected_option_ids"):
                opt_map = options_by_key_per_question.get(qid, {})
                item["selected_option_ids"] = [opt_map[k] for k in item["selected_option_keys"] if k in opt_map]

            submitted_by_qid[qid] = item
            q = questions_map[qid]

            # Determine simplified answer value for key lookup
            if q.question_type == "BOOLEAN":
                answers_by_key[q.key] = item.get("boolean_value")
            elif q.question_type in ("NUMBER",):
                answers_by_key[q.key] = item.get("number_value")
            elif q.question_type in ("TEXT", "LONG_TEXT"):
                answers_by_key[q.key] = item.get("text_value")
            elif q.question_type == "SINGLE_SELECT":
                sel = item.get("selected_option_ids", [])
                answers_by_key[q.key] = sel[0] if sel else None
            elif q.question_type == "MULTI_SELECT":
                answers_by_key[q.key] = item.get("selected_option_ids", [])

        # Validate each submitted answer's data type and options
        for qid, ans in submitted_by_qid.items():
            q = questions_map[qid]
            valid_option_ids = {opt.id for opt in q.options}

            if q.question_type == "SINGLE_SELECT":
                selected = ans.get("selected_option_ids", [])
                if len(selected) > 1:
                    errors.append(f"Question '{q.label}' only allows a single selection.")
                for opt_id in selected:
                    if opt_id not in valid_option_ids:
                        errors.append(f"Option ID {opt_id} is not valid for question '{q.label}'.")

            elif q.question_type == "MULTI_SELECT":
                selected = ans.get("selected_option_ids", [])
                for opt_id in selected:
                    if opt_id not in valid_option_ids:
                        errors.append(f"Option ID {opt_id} is not valid for question '{q.label}'.")

        # If completing, verify all visible required questions are answered
        if is_completing:
            for sec in template_version.sections:
                sec_visible = cls.evaluate_condition(sec.visibility_condition, answers_by_key)
                if not sec_visible:
                    continue

                for q in sec.questions:
                    q_visible = cls.evaluate_condition(q.visibility_condition, answers_by_key)
                    if not q_visible:
                        continue

                    if q.is_required:
                        ans = submitted_by_qid.get(q.id)
                        if not ans:
                            errors.append(f"Required question '{q.label}' has not been answered.")
                            continue

                        # Check non-empty
                        if q.question_type == "BOOLEAN" and ans.get("boolean_value") is None:
                            errors.append(f"Required question '{q.label}' must be answered.")
                        elif q.question_type in ("TEXT", "LONG_TEXT") and not (ans.get("text_value") or "").strip():
                            errors.append(f"Required text question '{q.label}' cannot be blank.")
                        elif q.question_type in ("SINGLE_SELECT", "MULTI_SELECT") and not ans.get(
                            "selected_option_ids"
                        ):
                            errors.append(f"Required selection question '{q.label}' must have an option selected.")
                        elif q.question_type == "NUMBER" and ans.get("number_value") is None:
                            errors.append(f"Required numeric question '{q.label}' must have a number.")

        return errors
