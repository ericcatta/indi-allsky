"""Normalize only the deliberately changed history-query admission boundary."""
import ast
from copy import deepcopy


def admitted_history_context(node, expected_calls):
    class Normalize(ast.NodeTransformer):
        calls = 0

        def visit_Call(self, call):
            if isinstance(call.func, ast.Name) and call.func.id == 'history_timestamp':
                assert not call.args and not call.keywords
                self.calls += 1
                return ast.parse("int(request.args.get('timestamp', 0))", mode='eval').body
            return self.generic_visit(call)

    normalizer = Normalize()
    normalized = normalizer.visit(deepcopy(node))
    assert normalizer.calls == expected_calls, (node.name, normalizer.calls)
    return normalized
