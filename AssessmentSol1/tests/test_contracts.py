from assessment_sol1.contracts import STAGES, is_allowed_assessment_write


def test_stage_score_times_are_explicit():
    assert [x.stage for x in STAGES] == ["T0", "T1", "T2"]
    assert all(x.score_time_definition for x in STAGES)


def test_prompt0_write_scope():
    assert is_allowed_assessment_write("AssessmentSol1/README.md")
    assert not is_allowed_assessment_write("experimentos/x.txt")
    assert not is_allowed_assessment_write("data/candidate/csv/leads.csv")
    assert not is_allowed_assessment_write("README.md")
    assert not is_allowed_assessment_write(".github/workflows/x.yml")
