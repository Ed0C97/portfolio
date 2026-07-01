"""INT8 static quantization for transformer inference. Portfolio excerpt, adapted.

Shows the shape of a post-training static-quantization pipeline for ONNX
transformer models: a calibration data reader, an op skip-list that keeps
precision-sensitive layers in floating point, per-channel weight quantization
with per-tensor static activation ranges baked in from calibration, and a
validation pass that compares FP32 vs INT8 embeddings by cosine similarity.

The ONNX Runtime quantization backend, the real export step, the curated
calibration corpus (a sample of production traffic), the tuned acceptance
thresholds, and the exact model names are stubbed. The static-activation
calibration statistics are the proprietary half and are represented here by a
small illustrative range collector rather than the production implementation.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Precision-sensitive ops kept in floating point. Quantizing these tends to cost
# more accuracy than the memory it saves: layer norm and softmax are numerically
# delicate, and embedding lookups (Gather) index a table where INT8 rounding
# shows up directly in the output. MatMul and Attention, which dominate compute
# and memory, are what we actually want in INT8.
OPS_TO_SKIP: frozenset[str] = frozenset(
    {"LayerNormalization", "Softmax", "Gelu", "Gather"}
)

# Placeholder calibration corpus. The real reader draws from a sample of the
# production query distribution; representativeness is what makes static ranges
# match deployment. These generic strings only exercise the code path.
DEFAULT_CALIBRATION_TEXTS: tuple[str, ...] = (
    "Machine learning is a subset of artificial intelligence.",
    "The quick brown fox jumps over the lazy dog.",
    "what is attention",
    "GPU memory bandwidth",
)


class CalibrationDataReader:
    """Feeds calibration batches to the quantizer.

    Static quantization needs the typical range of activations at each layer
    before deployment. We get that by running representative text through the
    FP32 model once and recording min/max per tensor. This reader implements the
    get_next / rewind interface the ONNX Runtime quantizer consumes: one batch of
    tokenized numpy arrays per call, None when exhausted.
    """

    def __init__(
        self,
        tokenizer_name: str,
        texts: list[str] | None = None,
        max_length: int = 512,
        batch_size: int = 1,
    ) -> None:
        # Real code loads a HuggingFace tokenizer here; stubbed to keep the
        # excerpt dependency-free. _tokenize below stands in for it.
        self.tokenizer_name = tokenizer_name
        self.texts = list(texts) if texts is not None else list(DEFAULT_CALIBRATION_TEXTS)
        self.max_length = max_length
        self.batch_size = batch_size
        self._index = 0

        # Pre-tokenize up front so get_next stays cheap during calibration.
        self._batches = self._prepare_batches()
        logger.info(
            "Calibration: %d texts to %d batches (batch_size=%d)",
            len(self.texts),
            len(self._batches),
            batch_size,
        )

    def _tokenize(self, batch_texts: list[str]) -> dict[str, np.ndarray]:
        """Stub tokenizer: deterministic fixed-length int64 ids and mask.

        The production path calls a real subword tokenizer with padding and
        truncation to max_length. We only need arrays of the right dtype and
        shape for the quantizer, so a hash-based fill is enough.
        """
        n = len(batch_texts)
        ids = np.zeros((n, self.max_length), dtype=np.int64)
        mask = np.zeros((n, self.max_length), dtype=np.int64)
        for row, text in enumerate(batch_texts):
            length = min(len(text.split()), self.max_length)
            for col in range(length):
                ids[row, col] = (hash((text, col)) % 30000) + 1
            mask[row, :length] = 1
        return {"input_ids": ids, "attention_mask": mask}

    def _prepare_batches(self) -> list[dict[str, np.ndarray]]:
        """Tokenize and group all calibration texts into batches."""
        batches: list[dict[str, np.ndarray]] = []
        for start in range(0, len(self.texts), self.batch_size):
            batch_texts = self.texts[start : start + self.batch_size]
            batches.append(self._tokenize(batch_texts))
        return batches

    def get_next(self) -> dict[str, np.ndarray] | None:
        """Return the next calibration batch, or None once exhausted."""
        if self._index >= len(self._batches):
            return None
        batch = self._batches[self._index]
        self._index += 1
        return batch

    def rewind(self) -> None:
        """Reset to the start so the quantizer can make multiple passes."""
        self._index = 0

    def __iter__(self) -> Iterator[dict[str, np.ndarray]]:
        self.rewind()
        return self

    def __next__(self) -> dict[str, np.ndarray]:
        result = self.get_next()
        if result is None:
            raise StopIteration
        return result


@dataclass
class ActivationRange:
    """Per-tensor min/max accumulated across calibration batches.

    This is the static half of static quantization: the range is fixed here,
    at calibration time, so there is zero per-request range computation at
    serving time (the reason we prefer static over dynamic for a serving
    workload with a predictable input distribution). The production collector,
    with its moving-average smoothing and outlier handling, is stubbed; this
    keeps a plain running min/max to show the structure.
    """

    lo: float = float("inf")
    hi: float = float("-inf")

    def observe(self, tensor: np.ndarray) -> None:
        self.lo = min(self.lo, float(tensor.min()))
        self.hi = max(self.hi, float(tensor.max()))

    def symmetric_scale(self, qmax: int = 127) -> float:
        """Symmetric INT8 scale for this range (zero-point fixed at 0)."""
        amax = max(abs(self.lo), abs(self.hi))
        # Guard the all-zero tensor: a zero range would divide by zero.
        return (amax / qmax) if amax > 0.0 else 1.0


@dataclass
class QuantConfig:
    """Knobs for the quantization run. Real defaults are tuned per model."""

    per_channel: bool = True  # per-channel weights, standard best practice
    weight_symmetric: bool = True
    activation_symmetric: bool = False
    ops_to_skip: frozenset[str] = OPS_TO_SKIP
    # Acceptance threshold on mean cosine similarity. The production value is
    # tuned per model family; this placeholder is deliberately loose.
    cosine_threshold: float = 0.99
    excluded_nodes: list[str] = field(default_factory=list)


def collect_activation_ranges(
    reader: CalibrationDataReader,
    forward_fp32,
) -> dict[str, ActivationRange]:
    """Run calibration data through the FP32 model and record activation ranges.

    forward_fp32 is injected (the real export/session wiring is stubbed): given a
    batch, it returns a mapping of tensor name to activation array. We fold each
    batch into a running range per tensor. These ranges are what get baked into
    the INT8 model so no range is computed at request time.
    """
    ranges: dict[str, ActivationRange] = {}
    reader.rewind()
    for batch in reader:
        for name, activation in forward_fp32(batch).items():
            ranges.setdefault(name, ActivationRange()).observe(activation)
    logger.info("Collected activation ranges for %d tensors", len(ranges))
    return ranges


def select_nodes_to_exclude(op_types: list[str], config: QuantConfig) -> list[str]:
    """Return indices of graph nodes to leave in floating point.

    In the real pipeline this walks an ONNX graph and matches node.op_type
    against the skip-list; here op_types is a plain list so the excerpt runs
    without an ONNX dependency. Same decision, smaller surface.
    """
    excluded = [
        f"node_{i}"
        for i, op in enumerate(op_types)
        if op in config.ops_to_skip
    ]
    logger.info(
        "Quantizing: %d ops total, %d excluded (precision-sensitive)",
        len(op_types),
        len(excluded),
    )
    return excluded


def quantize_model_int8(
    input_onnx_path: str | Path,
    output_onnx_path: str | Path,
    reader: CalibrationDataReader,
    config: QuantConfig | None = None,
) -> Path:
    """Apply static INT8 quantization to an ONNX model.

    The real function pre-processes the graph (shape inference), collects static
    activation ranges from the reader, then hands everything to the ONNX Runtime
    static quantizer with per-channel symmetric weights and per-tensor
    asymmetric activations. That backend call, the tuned extra_options, and the
    graph rewrite are the proprietary core and are stubbed here: this version
    validates inputs, drives the calibration collector, and writes a placeholder
    artifact so the control flow is faithful without shipping the engine.
    """
    config = config or QuantConfig()
    input_path = Path(input_onnx_path)
    output_path = Path(output_onnx_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calibration drives the static activation ranges. In this excerpt the FP32
    # forward is a stub, so we only exercise the reader to show the wiring.
    reader.rewind()
    n_batches = sum(1 for _ in reader)
    logger.info("Static calibration over %d batches", n_batches)

    # <<< proprietary quantize_static(...) call omitted >>>
    # Backend, weight_type/activation_type, and tuned extra_options are stubbed.
    output_path.write_bytes(b"INT8_STUB")

    logger.info("Quantization complete (stub artifact): %s", output_path)
    return output_path


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors, with a small epsilon guard."""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a.ravel(), b.ravel()) / denom)


def validate_quantized_model(
    embed_fp32,
    embed_int8,
    texts: list[str],
    config: QuantConfig | None = None,
) -> dict[str, float | bool | int]:
    """Compare FP32 and INT8 embeddings and pass/fail on cosine similarity.

    A correct INT8 conversion should barely move the embeddings. embed_fp32 and
    embed_int8 are injected callables (real code builds two ONNX Runtime
    sessions with mean pooling over the attention mask). We report mean/min/max
    cosine similarity and compare the mean against the configured threshold.
    """
    config = config or QuantConfig()
    sims = [cosine_similarity(embed_fp32(t), embed_int8(t)) for t in texts]
    mean_sim = float(np.mean(sims))

    result: dict[str, float | bool | int] = {
        "mean_cosine_similarity": mean_sim,
        "min_cosine_similarity": float(np.min(sims)),
        "max_cosine_similarity": float(np.max(sims)),
        "n_samples": len(sims),
        "threshold": config.cosine_threshold,
        "passed": bool(mean_sim >= config.cosine_threshold),
    }
    logger.info(
        "Validation: mean_cos=%.4f, min=%.4f (threshold=%.3f) -> %s",
        result["mean_cosine_similarity"],
        result["min_cosine_similarity"],
        config.cosine_threshold,
        "PASS" if result["passed"] else "FAIL",
    )
    return result


if __name__ == "__main__":
    # Tiny demo: drive calibration end to end with stubbed model forwards, then
    # validate against a near-identical INT8 stand-in to show the pass path.
    logging.basicConfig(level=logging.INFO)
    rng = np.random.default_rng(0)

    reader = CalibrationDataReader(tokenizer_name="stub/tokenizer", batch_size=2)

    def forward_fp32(batch: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        # One synthetic activation tensor derived from the batch shape.
        return {"encoder.output": rng.standard_normal(batch["input_ids"].shape)}

    ranges = collect_activation_ranges(reader, forward_fp32)
    for name, rng_stats in ranges.items():
        print(f"{name}: scale={rng_stats.symmetric_scale():.5f}")

    excluded = select_nodes_to_exclude(["MatMul", "Softmax", "Gather"], QuantConfig())
    assert excluded == ["node_1", "node_2"], excluded

    # Zero tensor must not blow up the scale computation.
    zero_range = ActivationRange()
    zero_range.observe(np.zeros(8, dtype=np.float32))
    assert zero_range.symmetric_scale() == 1.0

    base = rng.standard_normal(64).astype(np.float32)
    report = validate_quantized_model(
        embed_fp32=lambda _t: base,
        embed_int8=lambda _t: base + 1e-3 * rng.standard_normal(64).astype(np.float32),
        texts=list(DEFAULT_CALIBRATION_TEXTS),
    )
    assert report["passed"], report
    print("demo ok:", report)
