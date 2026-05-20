"""
Semantic Analyzer for Document Clustering and Knowledge Graph Creation
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import math


@dataclass
class Token:
    """Semantic token extracted from text"""
    text: str
    term_frequency: float
    context: str
    position: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Cluster:
    """Domain expertise cluster"""
    cluster_id: str
    label: str
    tokens: List[Token]
    centroid_embedding: List[float]
    confidence: float
    related_clusters: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "tokens": [t.to_dict() for t in self.tokens],
            "centroid_embedding": self.centroid_embedding,
            "confidence": self.confidence,
            "related_clusters": self.related_clusters,
        }


class SimpleEmbedding:
    """Lightweight embedding generator without external dependencies"""

    @staticmethod
    def embed(text: str, dim: int = 128) -> List[float]:
        """
        Generate a deterministic embedding for text using hash-based approach.
        Not ML-based, but reproducible and suitable for semantic grouping.
        """
        words = re.findall(r'\w+', text.lower())
        if not words:
            return [0.0] * dim

        # Create a base vector from word frequencies
        embedding = [0.0] * dim

        for word in words:
            # Hash word to dimension indices
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for i in range(min(3, dim)):
                idx = (word_hash + i) % dim
                embedding[idx] += 1.0 / (len(words) + 1)

        # Normalize
        magnitude = math.sqrt(sum(x ** 2 for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(x ** 2 for x in vec1))
        mag2 = math.sqrt(sum(x ** 2 for x in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)


class SemanticAnalyzer:
    """Analyzes documents and creates domain expertise clusters"""

    DOMAIN_KEYWORDS = {
        "backend": ["api", "server", "database", "sql", "orm", "authentication", "authorization", "rest"],
        "frontend": ["ui", "react", "vue", "angular", "css", "html", "javascript", "component", "state"],
        "devops": ["docker", "kubernetes", "ci/cd", "pipeline", "deployment", "cloud", "infrastructure", "terraform"],
        "data": ["analytics", "data lake", "warehouse", "pipeline", "etl", "query", "aggregation", "spark"],
        "ml": ["model", "training", "inference", "neural", "deep learning", "classification", "nlp", "cv"],
        "security": ["authentication", "encryption", "tls", "oauth", "jwt", "vulnerability", "compliance", "audit"],
        "testing": ["unit test", "integration test", "e2e", "mock", "assert", "coverage", "ci test"],
        "documentation": ["readme", "api docs", "architecture", "guide", "tutorial", "spec", "requirements"],
    }

    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.embedder = SimpleEmbedding()
        self.clusters: Dict[str, Cluster] = {}
        self.token_index: Dict[str, List[Token]] = {}

    def extract_semantic_tokens(self, text: str, context: str = "") -> List[Token]:
        """Extract meaningful semantic tokens from text"""
        tokens = []

        # Sentence tokenization
        sentences = re.split(r'[.!?]\s+', text)

        for sent_idx, sentence in enumerate(sentences):
            # Extract phrases (multi-word terms)
            phrases = self._extract_phrases(sentence)

            for phrase in phrases:
                # Calculate term frequency
                phrase_lower = phrase.lower()
                tf = text.lower().count(phrase_lower) / max(len(text.split()), 1)

                token = Token(
                    text=phrase,
                    term_frequency=tf,
                    context=context or sentence[:100],
                    position=sent_idx
                )
                tokens.append(token)

        return tokens

    def _extract_phrases(self, text: str) -> List[str]:
        """Extract noun phrases and meaningful multi-word terms"""
        phrases = []

        # Multi-word patterns
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # CamelCase or Title phrases
            r'\b(?:API|REST|OAuth|JWT|SQL|NoSQL|CRUD|CI/CD|ETL|NLP|CV)\b',  # Acronyms
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            phrases.extend(matches)

        # Single important words
        important_words = set()
        for word in text.split():
            word_clean = word.lower().strip('.,;:')
            if len(word_clean) > 4 and word_clean not in ['this', 'that', 'with', 'from', 'into']:
                important_words.add(word_clean)

        phrases.extend(list(important_words)[:10])

        return list(set(phrases))

    def classify_domains(self, tokens: List[Token]) -> Dict[str, float]:
        """Classify tokens into domain expertise areas"""
        domain_scores = {domain: 0.0 for domain in self.DOMAIN_KEYWORDS}

        for token in tokens:
            token_lower = token.text.lower()
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in token_lower:
                        domain_scores[domain] += token.term_frequency

        # Normalize
        total = sum(domain_scores.values())
        if total > 0:
            domain_scores = {k: v / total for k, v in domain_scores.items()}

        return domain_scores

    def create_clusters(self, document_text: str, doc_name: str = "document") -> List[Cluster]:
        """Create domain expertise clusters from document"""
        tokens = self.extract_semantic_tokens(document_text, context=doc_name)

        if not tokens:
            return []

        domain_scores = self.classify_domains(tokens)

        # Create a cluster for each significant domain
        clusters = []
        for domain, score in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.1:  # Threshold
                # Filter tokens relevant to this domain
                domain_tokens = self._filter_tokens_for_domain(tokens, domain)

                if domain_tokens:
                    cluster_id = f"{domain}_{hashlib.md5(doc_name.encode()).hexdigest()[:8]}"
                    centroid = self._compute_centroid(domain_tokens)

                    cluster = Cluster(
                        cluster_id=cluster_id,
                        label=f"{domain.title()} (from {doc_name})",
                        tokens=domain_tokens,
                        centroid_embedding=centroid,
                        confidence=score,
                        related_clusters=[]
                    )
                    clusters.append(cluster)

        self._update_cluster_relationships(clusters)
        return clusters

    def _filter_tokens_for_domain(self, tokens: List[Token], domain: str) -> List[Token]:
        """Filter tokens relevant to a specific domain"""
        keywords = self.DOMAIN_KEYWORDS.get(domain, [])
        filtered = []

        for token in tokens:
            token_lower = token.text.lower()
            if any(kw in token_lower for kw in keywords):
                filtered.append(token)

        # If no exact matches, take highest frequency tokens
        if not filtered:
            filtered = sorted(tokens, key=lambda t: t.term_frequency, reverse=True)[:5]

        return filtered[:10]

    def _compute_centroid(self, tokens: List[Token]) -> List[float]:
        """Compute centroid embedding from tokens"""
        if not tokens:
            return [0.0] * self.embedding_dim

        embeddings = [self.embedder.embed(t.text, self.embedding_dim) for t in tokens]

        # Average embeddings
        centroid = [sum(e[i] for e in embeddings) / len(embeddings) for i in range(self.embedding_dim)]

        # Normalize
        magnitude = math.sqrt(sum(x ** 2 for x in centroid))
        if magnitude > 0:
            centroid = [x / magnitude for x in centroid]

        return centroid

    def _update_cluster_relationships(self, clusters: List[Cluster]):
        """Find and update related clusters based on embedding similarity"""
        for i, cluster1 in enumerate(clusters):
            for j, cluster2 in enumerate(clusters):
                if i != j:
                    similarity = self.embedder.cosine_similarity(
                        cluster1.centroid_embedding,
                        cluster2.centroid_embedding
                    )
                    if similarity > 0.6:
                        if cluster2.cluster_id not in cluster1.related_clusters:
                            cluster1.related_clusters.append(cluster2.cluster_id)

    def build_knowledge_graph(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete knowledge graph from multiple documents"""
        all_clusters = []

        for doc_name, doc_text in documents.items():
            clusters = self.create_clusters(doc_text, doc_name)
            all_clusters.extend(clusters)

        # Deduplicate and merge similar clusters
        merged_clusters = self._merge_similar_clusters(all_clusters)

        # Build adjacency graph
        graph = {
            "nodes": [],
            "edges": [],
            "clusters": {},
        }

        for cluster in merged_clusters:
            graph["nodes"].append({
                "id": cluster.cluster_id,
                "label": cluster.label,
                "confidence": cluster.confidence,
                "token_count": len(cluster.tokens),
            })
            graph["clusters"][cluster.cluster_id] = cluster.to_dict()

            # Add edges for relationships
            for related_id in cluster.related_clusters:
                graph["edges"].append({
                    "source": cluster.cluster_id,
                    "target": related_id,
                    "type": "related"
                })

        return graph

    def _merge_similar_clusters(self, clusters: List[Cluster]) -> List[Cluster]:
        """Merge highly similar clusters"""
        if not clusters:
            return []

        merged = []
        used = set()

        for i, cluster1 in enumerate(clusters):
            if i in used:
                continue

            merged_tokens = list(cluster1.tokens)
            similar_ids = [cluster1.cluster_id]

            # Find similar clusters
            for j, cluster2 in enumerate(clusters[i + 1:], start=i + 1):
                if j in used:
                    continue

                similarity = self.embedder.cosine_similarity(
                    cluster1.centroid_embedding,
                    cluster2.centroid_embedding
                )

                if similarity > 0.7:  # High similarity threshold
                    merged_tokens.extend(cluster2.tokens)
                    similar_ids.append(cluster2.cluster_id)
                    used.add(j)

            # Create merged cluster
            merged_cluster = Cluster(
                cluster_id=cluster1.cluster_id,
                label=cluster1.label,
                tokens=merged_tokens,
                centroid_embedding=self._compute_centroid(merged_tokens),
                confidence=cluster1.confidence,
                related_clusters=similar_ids[1:]
            )
            merged.append(merged_cluster)

        return merged
