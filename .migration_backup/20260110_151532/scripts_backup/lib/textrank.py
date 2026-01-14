import math
from typing import Dict, List, Set, Tuple

# --- Cosine Similarity ---

def cosine_similarity(vec1: Dict[str, int], vec2: Dict[str, int]) -> float:
    """
    Computes cosine similarity between two sparse vectors (dicts).
    """
    # 1. Intersect Keys: Only multiply non-zero dimensions
    common_words = set(vec1.keys()) & set(vec2.keys())
    
    if not common_words:
        return 0.0
    
    # 2. Dot Product
    dot_product = sum(vec1[word] * vec2[word] for word in common_words)
    
    # 3. Magnitudes
    mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
        
    return dot_product / (mag1 * mag2)

def build_vector(tokens: List[str]) -> Dict[str, int]:
    """Converts token list to sparse frequency vector."""
    vec = {}
    for t in tokens:
        vec[t] = vec.get(t, 0) + 1
    return vec

# --- PageRank ---

def pagerank(graph: Dict[int, Dict[int, float]], damping: float = 0.85, epsilon: float = 1.0e-4, max_iter: int = 100) -> Dict[int, float]:
    """
    Computes PageRank for an undirected graph represented as dict of dicts.
    graph[i][j] = weight
    
    Returns: Dict[node_index, score]
    """
    nodes = list(graph.keys())
    if not nodes:
        return {}
        
    # Init scores
    scores = {n: 1.0 for n in nodes}
    
    # Pre-calculate out strength (sum of weights for each node)
    out_strength = {n: sum(graph[n].values()) for n in nodes}
    
    for _ in range(max_iter):
        new_scores = {}
        diff = 0.0
        
        for node in nodes:
            rank_sum = 0.0
            
            # For undirected semantic graph, neighbors are effectively incoming links
            # We iterate over neighbors of 'node'
            # Formula: sum( (weight_ji / Sum_weights_j) * Score_j )
            neighbors = graph.get(node, {})
            
            for neighbor, weight in neighbors.items():
                if out_strength[neighbor] == 0:
                    continue
                rank_sum += (weight / out_strength[neighbor]) * scores[neighbor]
            
            new_scores[node] = (1 - damping) + (damping * rank_sum)
            diff += abs(new_scores[node] - scores[node])
            
        scores = new_scores
        if diff < epsilon:
            break
            
    return scores

def extract_summary(unique_sentences: List[str], top_n: int = 1) -> str:
    """
    Main TextRank pipeline.
    Input: List of unique sentences/logs.
    Output: Most representative sentence.
    """
    from scripts.ontology.learning.algorithms.preprocessing import tokenize
    
    n = len(unique_sentences)
    if n == 0: return ""
    if n == 1: return unique_sentences[0]
    
    # 1. Vectorize
    vectors = [build_vector(tokenize(s)) for s in unique_sentences]
    
    # 2. Build Graph (Similarity Matrix)
    # Graph: {node_idx: {neighbor_idx: similarity}}
    graph = {i: {} for i in range(n)}
    
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(vectors[i], vectors[j])
            if sim > 0.1: # Pruning threshold
                graph[i][j] = sim
                graph[j][i] = sim
                
    # 3. Rank
    scores = pagerank(graph)
    
    # 4. Sort
    ranked_indices = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    
    return unique_sentences[ranked_indices[0]] if ranked_indices else unique_sentences[0]
