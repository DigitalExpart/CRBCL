"""Unit test suite for AssessmentValidationService."""

import uuid

from app.models.assessment import (
    AssessmentQuestion,
    AssessmentQuestionOption,
    AssessmentSection,
    AssessmentTemplateVersion,
)
from app.services.assessment_validation_service import AssessmentValidationService


def test_evaluate_condition():
    # 1. No condition -> True
    assert AssessmentValidationService.evaluate_condition(None, {}) is True

    # 2. Boolean equals
    cond_true = {"depends_on_question_key": "substance_use", "operator": "equals", "value": True}
    assert AssessmentValidationService.evaluate_condition(cond_true, {"substance_use": True}) is True
    assert AssessmentValidationService.evaluate_condition(cond_true, {"substance_use": False}) is False
    assert AssessmentValidationService.evaluate_condition(cond_true, {}) is False

    # 3. is_true / is_false
    cond_is_true = {"depends_on_question_key": "flag", "operator": "is_true"}
    assert AssessmentValidationService.evaluate_condition(cond_is_true, {"flag": True}) is True
    assert AssessmentValidationService.evaluate_condition(cond_is_true, {"flag": False}) is False

    # 4. not_equals
    cond_neq = {"depends_on_question_key": "status", "operator": "not_equals", "value": "NONE"}
    assert AssessmentValidationService.evaluate_condition(cond_neq, {"status": "HIGH"}) is True
    assert AssessmentValidationService.evaluate_condition(cond_neq, {"status": "NONE"}) is False

    # 5. contains (list & string)
    cond_contains_opt = {"depends_on_question_key": "services", "operator": "contains", "value": "HOUSING"}
    assert AssessmentValidationService.evaluate_condition(cond_contains_opt, {"services": ["HOUSING", "FOOD"]}) is True
    assert AssessmentValidationService.evaluate_condition(cond_contains_opt, {"services": ["FOOD"]}) is False


def test_validate_answers_types_and_required():
    # Construct mock template version structure
    v_id = uuid.uuid4()
    sec_id = uuid.uuid4()
    q1_id = uuid.uuid4()
    q2_id = uuid.uuid4()
    opt1_id = uuid.uuid4()
    opt2_id = uuid.uuid4()

    q1 = AssessmentQuestion(
        id=q1_id,
        section_id=sec_id,
        key="has_concern",
        label="Has Concern?",
        question_type="BOOLEAN",
        is_required=True,
    )
    q1.options = []

    q2 = AssessmentQuestion(
        id=q2_id,
        section_id=sec_id,
        key="concern_level",
        label="Concern Level",
        question_type="SINGLE_SELECT",
        is_required=True,
        visibility_condition={"depends_on_question_key": "has_concern", "operator": "equals", "value": True},
    )
    opt1 = AssessmentQuestionOption(id=opt1_id, question_id=q2_id, key="LOW", label="Low")
    opt2 = AssessmentQuestionOption(id=opt2_id, question_id=q2_id, key="HIGH", label="High")
    q2.options = [opt1, opt2]

    sec = AssessmentSection(
        id=sec_id,
        template_version_id=v_id,
        key="SEC_1",
        title="Section 1",
        is_required=True,
    )
    sec.questions = [q1, q2]

    version = AssessmentTemplateVersion(
        id=v_id,
        version_number=1,
        status="PUBLISHED",
    )
    version.sections = [sec]

    # 1. Foreign question ID -> error
    bad_answers = [{"question_id": uuid.uuid4(), "boolean_value": True}]
    errs = AssessmentValidationService.validate_answers(version, bad_answers, is_completing=False)
    assert len(errs) == 1
    assert "does not belong" in errs[0]

    # 2. Invalid option ID -> error
    bad_opt_answers = [
        {"question_id": q1_id, "boolean_value": True},
        {"question_id": q2_id, "selected_option_ids": [uuid.uuid4()]},
    ]
    errs = AssessmentValidationService.validate_answers(version, bad_opt_answers, is_completing=False)
    assert len(errs) == 1
    assert "not valid" in errs[0]

    # 3. Single select with multiple options -> error
    multi_opt_answers = [
        {"question_id": q1_id, "boolean_value": True},
        {"question_id": q2_id, "selected_option_ids": [opt1_id, opt2_id]},
    ]
    errs = AssessmentValidationService.validate_answers(version, multi_opt_answers, is_completing=False)
    assert len(errs) == 1
    assert "only allows a single selection" in errs[0]

    # 4. Incomplete required field during completion
    incomplete_answers = [
        {"question_id": q1_id, "boolean_value": True},
        # q2 is visible (has_concern = True) but not answered
    ]
    errs = AssessmentValidationService.validate_answers(version, incomplete_answers, is_completing=True)
    assert len(errs) == 1
    assert "Concern Level" in errs[0]

    # 5. When condition is False, conditionally required question is skipped
    cond_false_answers = [
        {"question_id": q1_id, "boolean_value": False},
        # q2 is hidden because has_concern = False
    ]
    errs = AssessmentValidationService.validate_answers(version, cond_false_answers, is_completing=True)
    assert len(errs) == 0

    # 6. Valid completion
    valid_answers = [
        {"question_id": q1_id, "boolean_value": True},
        {"question_id": q2_id, "selected_option_ids": [opt1_id]},
    ]
    errs = AssessmentValidationService.validate_answers(version, valid_answers, is_completing=True)
    assert len(errs) == 0
