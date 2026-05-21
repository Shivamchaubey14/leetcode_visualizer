# visualizer/utils/arg_builder.py
from .data_structures import build_linked_list, build_tree, build_graph


def build_args(test_case) -> tuple:
    """
    Convert one test-case dict into a tuple of call arguments.

    Supported hint keys:
        "args"              – list of positional arguments (required)
        "linked_list_args"  – indices to convert to ListNode
        "tree_args"         – indices to convert to TreeNode
        "graph_args"        – indices to convert to GraphNode

    Examples:
        {"args": [[2,7,11,15], 9]}
        {"args": ["abcabcbb"]}
        {"args": [[2,4,3],[5,6,4]], "linked_list_args": [0,1]}
        {"args": [[3,9,20,null,null,15,7]], "tree_args": [0]}
    """
    # Guard: whole list passed instead of single item
    if isinstance(test_case, list):
        test_case = test_case[0] if test_case else {}
    if not isinstance(test_case, dict):
        return ()

    raw_args      = list(test_case.get('args', []))
    ll_indices    = set(test_case.get('linked_list_args', []))
    tree_indices  = set(test_case.get('tree_args', []))
    graph_indices = set(test_case.get('graph_args', []))

    result = []
    for i, arg in enumerate(raw_args):
        if i in ll_indices:
            result.append(build_linked_list(arg))
        elif i in tree_indices:
            result.append(build_tree(arg))
        elif i in graph_indices:
            result.append(build_graph(arg))
        else:
            result.append(arg)

    return tuple(result)