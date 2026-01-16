import collections
from typing import List, Set, Dict, Any, Tuple, Generator

class FPNode:
    """
    Memory-optimized Node for FP-Tree using __slots__.
    """
    __slots__ = ['item', 'count', 'parent', 'children', 'link']
    
    def __init__(self, item, parent=None):
        self.item = item
        self.count = 1
        self.parent = parent
        self.children = {}  # Dict mapping item -> FPNode
        self.link = None    # Pointer to next node with same item

    def increment(self, count=1):
        self.count += count

class FPTree:
    """
    Pure Python FP-Growth Implementation.
    """
    def __init__(self, transactions: List[List[str]], min_sup: int):
        self.min_sup = min_sup
        self.root = FPNode(None)
        # Header Table: item -> head_node of linked list
        self.header_table: Dict[str, FPNode] = {}
        # Count cache for sorting
        self.header_counts: Dict[str, int] = {} 
        
        # 1. Count Frequencies
        # Use simple dictionary for counting
        counts = collections.defaultdict(int)
        for trans in transactions:
            for item in trans:
                counts[item] += 1
                
        # 2. Filter Frequent Items
        # intersection of keys
        self.frequent_items = set(k for k, v in counts.items() if v >= min_sup)
        
        # Cache counts for frequent items only (needed for sorting)
        self.header_counts = {k: v for k, v in counts.items() if k in self.frequent_items}
        
        # 3. Build Tree
        for trans in transactions:
            self.add_transaction(trans)

    def add_transaction(self, transaction: List[str]):
        """
        Inserts a transaction into the tree.
        Items are sorted by global frequency (descending).
        """
        # Filter and Sort
        local_items = [x for x in transaction if x in self.frequent_items]
        # Sort key: (-count, item) -> Most frequent first, then alphabetical for stability
        local_items.sort(key=lambda x: (-self.header_counts[x], x))
        
        if local_items:
            self._insert_tree(local_items, self.root)

    def _insert_tree(self, items: List[str], node: FPNode):
        first = items[0]
        child = node.children.get(first)
        
        if child:
            child.increment()
        else:
            child = FPNode(first, node)
            node.children[first] = child
            self._update_header(first, child)
            
        if len(items) > 1:
            self._insert_tree(items[1:], child)

    def _update_header(self, item: str, target_node: FPNode):
        if item not in self.header_table:
            self.header_table[item] = target_node
        else:
            # Append to end of linked list (O(N) unless we cache tail, but list is usually short)
            # Optimization: Always traverse to end? Or keep tail pointer?
            # Standard impl traverses.
            current = self.header_table[item]
            while current.link:
                current = current.link
            current.link = target_node

    def mine(self) -> Generator[Tuple[Set[str], int], None, None]:
        """
        Public mining entry point.
        Yields (frequent_pattern_set, support_count).
        """
        # Start mining from least frequent item to most frequent
        # Why? Because we build Conditional Pattern Base "upwards"
        sorted_items = sorted(
            self.header_table.keys(), 
            key=lambda k: self.header_counts[k]
            # No reverse=True -> ascending order (least frequent first)
        )
        
        for item in sorted_items:
            yield from self._mine_recursive(set(), item)

    def _mine_recursive(self, prefix: Set[str], item: str) -> Generator[Tuple[Set[str], int], None, None]:
        # Form new pattern
        new_pattern = prefix.copy()
        new_pattern.add(item)
        
        # Structure support is the sum of counts of nodes in the header list for this item
        support = 0
        current = self.header_table[item]
        while current:
            support += current.count
            current = current.link
            
        yield (new_pattern, support)
        
        # Build Conditional Pattern Base
        conditional_transactions = []
        current = self.header_table[item]
        
        while current:
            # Trace path to root
            path = []
            parent = current.parent
            while parent and parent.item is not None:
                path.append(parent.item)
                parent = parent.parent
            
            # The path occurred 'current.count' times
            if path:
                # Add path 'count' times? Or Weighted?
                # FP-Growth optimization: Pass 'counts' to constructor
                # For simplicity here taking naive unrolling, but optimized is:
                # Implement FPTree to accept weighted transactions.
                # Assuming unweighted for this implementation step, effectively:
                for _ in range(current.count):
                    conditional_transactions.append(path)
            
            current = current.link
            
        # Recursive Step
        # Build conditional tree
        if conditional_transactions:
            # Recursion is safe due to log depth limit
            cond_tree = FPTree(conditional_transactions, self.min_sup)
            if cond_tree.header_table:
                for next_item in sorted(cond_tree.header_table.keys(), key=lambda k: cond_tree.header_counts[k]):
                    yield from cond_tree._mine_recursive(new_pattern, next_item)
