"""Starter DeepEval case. Add new tests beside this file and reuse QueJudge.

    deepeval test run test_example.py
"""

from deepeval import assert_test
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import ConversationalTestCase, MultiTurnParams, Turn

from evals.judge import QueJudge


def test_professionalism():
    professionalism_metric = ConversationalGEval(
        name="Professionalism",
        criteria="Determine whether the assistant has acted professionally based on the content.",
        evaluation_params=[MultiTurnParams.CONTENT, MultiTurnParams.ROLE],
        evaluation_steps=[
            "Read the assistant turns.",
            "Score how professional the tone and content are from 0 to 10.",
        ],
        model=QueJudge(),
        threshold=0.5,
    )
    test_case = ConversationalTestCase(
        turns=[
            Turn(role="user", content="What is DeepEval?"),
            Turn(role="assistant", content="DeepEval is an open-source LLM eval package."),
        ]
    )
    assert_test(test_case, [professionalism_metric])
