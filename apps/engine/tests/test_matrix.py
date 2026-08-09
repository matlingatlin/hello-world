import pytest

from scio_engine.execution.matrix import CapabilityMatrix, UnknownTaskError, default_matrix
from scio_engine.execution.narration import narrate, plan_models


class TestMatrixSelection:
    def test_top_3_returns_ranked_models_best_first(self):
        matrix = default_matrix()
        picks = matrix.top_n("codegen", n=3)
        assert len(picks) == 3
        assert [m.id for m in picks] == matrix.tasks["codegen"].ranking[:3]

    def test_top_n_respects_n(self):
        assert len(default_matrix().top_n("review", n=1)) == 1
        assert len(default_matrix().top_n("review", n=2)) == 2

    def test_model_cards_carry_metadata(self):
        best = default_matrix().top_n("architecture", n=1)[0]
        assert best.context_limit > 0
        assert best.cost_per_mtok > 0
        assert best.latency and best.strength

    def test_unknown_task_raises_with_known_tasks_listed(self):
        with pytest.raises(UnknownTaskError) as err:
            default_matrix().top_n("teleportation")
        assert "codegen" in str(err.value)

    def test_every_task_ranks_at_least_three_models(self):
        matrix = default_matrix()
        for task in matrix.task_types:
            assert len(matrix.tasks[task].ranking) >= 3, task

    def test_matrix_rejects_rankings_with_unknown_models(self, tmp_path):
        bad = tmp_path / "matrix.yaml"
        bad.write_text(
            "models:\n"
            "  - id: real-model\n"
            "    vendor: anthropic\n"
            "    context_limit: 1000\n"
            "    cost_per_mtok: 1.0\n"
            "    latency: fast\n"
            "    strength: test\n"
            "tasks:\n"
            "  codegen:\n"
            "    ranking: [real-model, ghost-model]\n"
        )
        with pytest.raises(ValueError, match="ghost-model"):
            CapabilityMatrix.load(bad)


class TestPlanAndNarration:
    def test_plan_cycles_models_and_returns_to_the_best(self):
        models = default_matrix().top_n("codegen", n=3)
        plan = plan_models(models, 4)
        assert [m.id for m in plan] == [
            models[0].id,
            models[1].id,
            models[2].id,
            models[0].id,
        ]

    def test_single_pass_plan_is_just_the_best_model(self):
        models = default_matrix().top_n("light_edit", n=3)
        assert [m.id for m in plan_models(models, 1)] == [models[0].id]

    def test_narration_names_every_model_in_order(self):
        models = default_matrix().top_n("codegen", n=3)
        text = narrate("codegen", models, 4)
        assert "run this prompt 4 times" in text
        assert f"first in {models[0].id}" in text
        assert f"into {models[1].id} to review, rewrite and complement" in text
        assert f"final pass back in {models[0].id}" in text

    def test_single_pass_narration_says_once(self):
        models = default_matrix().top_n("light_edit", n=3)
        text = narrate("light_edit", models, 1)
        assert "run this once" in text
        assert models[0].id in text

    def test_narration_handles_no_models(self):
        assert "no model available" in narrate("codegen", [], 4)
