# visualizer/utils/data_structures.py
from collections import deque


# ─────────────────────────────────────────────────────────────
#  Linked List
# ─────────────────────────────────────────────────────────────

class ListNode:
    def __init__(self, val=0, next=None):
        self.val  = val
        self.next = next

    def __repr__(self):
        vals, visited, cur = [], set(), self
        while cur and id(cur) not in visited:
            visited.add(id(cur))
            vals.append(cur.val)
            cur = cur.next
        return f"LinkedList({vals})"


def build_linked_list(values: list):
    if not values:
        return None
    dummy = ListNode(0)
    cur   = dummy
    for v in values:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next


# ─────────────────────────────────────────────────────────────
#  Binary Tree
# ─────────────────────────────────────────────────────────────

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val   = val
        self.left  = left
        self.right = right

    def __repr__(self):
        if not self:
            return "TreeNode([])"
        result, queue = [], deque([self])
        while queue:
            node = queue.popleft()
            if node:
                result.append(node.val)
                queue.append(node.left)
                queue.append(node.right)
            else:
                result.append(None)
        while result and result[-1] is None:
            result.pop()
        return f"TreeNode({result})"


def build_tree(values: list):
    if not values or values[0] is None:
        return None
    root  = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root


# ─────────────────────────────────────────────────────────────
#  Graph
# ─────────────────────────────────────────────────────────────

class GraphNode:
    def __init__(self, val=0, neighbors=None):
        self.val       = val
        self.neighbors = neighbors if neighbors is not None else []

    def __repr__(self):
        return f"GraphNode({self.val}, neighbors={[n.val for n in self.neighbors]})"


def build_graph(adj: list):
    if not adj:
        return None
    nodes = {i + 1: GraphNode(i + 1) for i in range(len(adj))}
    for i, neighbours in enumerate(adj):
        nodes[i + 1].neighbors = [nodes[n] for n in neighbours]
    return nodes.get(1)


# ─────────────────────────────────────────────────────────────
#  Names injected by runner that must be hidden from the UI
# ─────────────────────────────────────────────────────────────
INJECTED_NAMES = frozenset({
    'ListNode', 'TreeNode', 'GraphNode',
    'Optional', 'List', 'Dict', 'Tuple', 'Set', 'Any', 'Union',
    'Solution', 'solution',
})