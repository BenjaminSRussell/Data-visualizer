"""
URL Embeddings using MLX - Create vector representations of URLs for similarity analysis
"""

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter
import re


class URLEmbedder:
    """
    Create embeddings for URLs using MLX.

    This converts URLs into fixed-size vector representations that capture
    semantic similarity, allowing us to find similar URLs and cluster them.
    """

    def __init__(self, embedding_dim=128, max_vocab_size=10000):
        """
        Initialize URL embedder.

        Args:
            embedding_dim: Dimension of embedding vectors
            max_vocab_size: Maximum vocabulary size for tokens
        """
        self.embedding_dim = embedding_dim
        self.max_vocab_size = max_vocab_size
        self.vocab = {}  # token -> id
        self.reverse_vocab = {}  # id -> token
        self.embedding_matrix = None
        self.is_trained = False

    def tokenize_url(self, url: str) -> List[str]:
        """
        Tokenize URL into meaningful components.

        Args:
            url: URL string

        Returns:
            List of tokens
        """
        # remove protocol
        url = re.sub(r'^https?://', '', url)

        # split by common delimiters
        tokens = []

        # split by / . - _
        parts = re.split(r'[/.\-_#?&=]', url)

        for part in parts:
            if part:
                # further split camelcase and numbers
                sub_tokens = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|\d+', part)
                tokens.extend([t.lower() for t in sub_tokens if t])

        return tokens

    def build_vocabulary(self, urls: List[str]):
        """
        Build vocabulary from URLs.

        Args:
            urls: List of URL strings
        """
        print(f"Building vocabulary from {len(urls):,} URLs...")

        # count all tokens
        token_counts = Counter()
        for url in urls:
            tokens = self.tokenize_url(url)
            token_counts.update(tokens)

        # take top n tokens
        most_common = token_counts.most_common(self.max_vocab_size - 2)  # reserve 2 for special tokens

        # build vocabulary
        self.vocab = {'<PAD>': 0, '<UNK>': 1}
        self.reverse_vocab = {0: '<PAD>', 1: '<UNK>'}

        for idx, (token, _) in enumerate(most_common, start=2):
            self.vocab[token] = idx
            self.reverse_vocab[idx] = token

        print(f"✓ Vocabulary built: {len(self.vocab):,} tokens")

    def url_to_ids(self, url: str, max_length=50) -> List[int]:
        """
        Convert URL to list of token IDs.

        Args:
            url: URL string
            max_length: Maximum length (pad or truncate)

        Returns:
            List of token IDs
        """
        tokens = self.tokenize_url(url)

        # convert to ids
        ids = [self.vocab.get(token, 1) for token in tokens]  # 1 = <unk>

        # pad or truncate
        if len(ids) < max_length:
            ids += [0] * (max_length - len(ids))  # 0 = <pad>
        else:
            ids = ids[:max_length]

        return ids

    def initialize_embeddings(self):
        """Initialize embedding matrix with random values"""
        vocab_size = len(self.vocab)

        # random initialization using mlx
        self.embedding_matrix = mx.random.normal(
            shape=(vocab_size, self.embedding_dim),
            scale=0.1
        )

        print(f"✓ Initialized embeddings: {vocab_size} x {self.embedding_dim}")

    def train_embeddings(self, urls: List[str], epochs=5, window_size=3):
        """
        Train embeddings using Skip-gram-like approach.

        Args:
            urls: List of URL strings
            epochs: Number of training epochs
            window_size: Context window size
        """
        print(f"\nTraining URL embeddings on {len(urls):,} URLs...")

        # build vocabulary if not already built
        if not self.vocab:
            self.build_vocabulary(urls)

        # initialize embeddings if not already done
        if self.embedding_matrix is None:
            self.initialize_embeddings()

        # convert urls to token id sequences
        url_sequences = [self.url_to_ids(url) for url in urls]

        # simple training loop (co-occurrence based)
        vocab_size = len(self.vocab)
        co_occurrence = np.zeros((vocab_size, vocab_size))

        # build co-occurrence matrix
        for sequence in url_sequences:
            for i, target in enumerate(sequence):
                if target == 0:  # skip padding
                    continue

                # look at context window
                start = max(0, i - window_size)
                end = min(len(sequence), i + window_size + 1)

                for j in range(start, end):
                    if j != i and sequence[j] != 0:
                        co_occurrence[target, sequence[j]] += 1

        # normalize co-occurrence matrix
        row_sums = co_occurrence.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # avoid division by zero
        co_occurrence_norm = co_occurrence / row_sums

        # use svd-like approach for embeddings (simplified glove)
        # for production, you'd use actual gradient descent with mlx
        from sklearn.decomposition import TruncatedSVD

        svd = TruncatedSVD(n_components=self.embedding_dim, random_state=42)
        embeddings_np = svd.fit_transform(co_occurrence_norm)

        # convert to mlx array
        self.embedding_matrix = mx.array(embeddings_np.astype(np.float32))

        self.is_trained = True
        print(f"✓ Embeddings trained")

    def embed_url(self, url: str) -> mx.array:
        """
        Get embedding vector for a single URL.

        Args:
            url: URL string

        Returns:
            MLX array of shape (embedding_dim,)
        """
        if not self.is_trained:
            raise ValueError("Embeddings not trained yet. Call train_embeddings() first.")

        # get token ids
        ids = self.url_to_ids(url)

        # get embeddings for each token
        token_embeddings = self.embedding_matrix[ids]

        # average pooling (ignore padding)
        mask = mx.array([1.0 if id != 0 else 0.0 for id in ids])
        mask_sum = mx.sum(mask)

        if mask_sum > 0:
            embedding = mx.sum(token_embeddings * mask[:, None], axis=0) / mask_sum
        else:
            embedding = mx.zeros(self.embedding_dim)

        return embedding

    def embed_urls(self, urls: List[str]) -> mx.array:
        """
        Get embeddings for multiple URLs.

        Args:
            urls: List of URL strings

        Returns:
            MLX array of shape (num_urls, embedding_dim)
        """
        embeddings = [self.embed_url(url) for url in urls]
        return mx.stack(embeddings)

    def compute_similarity(self, url1: str, url2: str) -> float:
        """
        Compute cosine similarity between two URLs.

        Args:
            url1, url2: URL strings

        Returns:
            Similarity score (0-1)
        """
        emb1 = self.embed_url(url1)
        emb2 = self.embed_url(url2)

        # cosine similarity
        dot_product = mx.sum(emb1 * emb2)
        norm1 = mx.sqrt(mx.sum(emb1 * emb1))
        norm2 = mx.sqrt(mx.sum(emb2 * emb2))

        similarity = dot_product / (norm1 * norm2 + 1e-8)

        return float(similarity)

    def find_similar_urls(self, url: str, url_list: List[str], top_k=10) -> List[Tuple[str, float]]:
        """
        Find most similar URLs from a list.

        Args:
            url: Query URL
            url_list: List of candidate URLs
            top_k: Number of results to return

        Returns:
            List of (url, similarity_score) tuples
        """
        query_emb = self.embed_url(url)
        candidate_embs = self.embed_urls(url_list)

        # compute similarities
        similarities = []
        for i, candidate_emb in enumerate(candidate_embs):
            dot_product = mx.sum(query_emb * candidate_emb)
            norm1 = mx.sqrt(mx.sum(query_emb * query_emb))
            norm2 = mx.sqrt(mx.sum(candidate_emb * candidate_emb))
            sim = float(dot_product / (norm1 * norm2 + 1e-8))
            similarities.append((url_list[i], sim))

        # sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def save_embeddings(self, filepath: str):
        """Save embeddings to file"""
        import pickle

        data = {
            'vocab': self.vocab,
            'reverse_vocab': self.reverse_vocab,
            'embeddings': np.array(self.embedding_matrix),
            'embedding_dim': self.embedding_dim,
            'is_trained': self.is_trained
        }

        with open(filepath, 'wb') as f:
            pickle.dump(data, f)

        print(f"✓ Embeddings saved to {filepath}")

    def load_embeddings(self, filepath: str):
        """Load embeddings from file"""
        import pickle

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.vocab = data['vocab']
        self.reverse_vocab = data['reverse_vocab']
        self.embedding_matrix = mx.array(data['embeddings'])
        self.embedding_dim = data['embedding_dim']
        self.is_trained = data['is_trained']

        print(f"✓ Embeddings loaded from {filepath}")
