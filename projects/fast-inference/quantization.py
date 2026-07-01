"""Symmetric INT8 quantization with a precision-protection policy. Portfolio excerpt, adapted.

Post-training weight quantization to signed INT8. Two scale granularities are shown:
per-tensor (one scale for the whole weight) and per-channel (one scale per output
row), which is the usual choice for linear layers because per-row dynamic range
varies enough that a single scale wastes resolution.

The interesting part is not the arithmetic, it is knowing where NOT to apply it.
Some tensors (normalization gains/biases, embedding tables, the final projection into
logits) are numerically sensitive: quantizing them costs far more quality than the
memory they save. A policy decides, by name and shape, which tensors pass through in
full precision. The real calibration ranges, the per-layer sensitivity thresholds, and
the fused INT8 GEMM kernels are proprietary and omitted here; this module is the
correctness-critical scaffolding around them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

# Signed 8-bit symmetric range is [-127, 127], deliberately not [-128, 127].
# Dropping -128 keeps the quantization grid symmetric about zero, so quantize and
# dequantize are exact inverses of scaling and 0.0 always maps to integer 0. This
# is the standard convention for symmetric weight quantization (TensorRT, PyTorch).
INT8_QMAX = 127

# Absmax below this is treated as an all-zero (or denormal) tensor. The scale would
# otherwise be zero and the reciprocal would blow up; we substitute a positive absmax
# so the tensor round-trips to all zeros instead of NaN.
_ABSMAX_EPS = 1e-12


@dataclass(frozen=True)
class QuantizedTensor:
    """An INT8 tensor plus the scales needed to reconstruct it.

    axis is None for per-tensor quantization (scale is a scalar), or the axis along
    which each slice has its own scale for per-channel (scale is 1-D). Keeping the
    axis with the payload means dequantize does not have to guess the layout.
    """

    values: np.ndarray  # dtype int8
    scale: np.ndarray  # float32, scalar or 1-D
    axis: int | None


def _absmax_scale(absmax: np.ndarray) -> np.ndarray:
    """Map an absolute-maximum magnitude to a float32 scale, guarding zeros.

    scale = absmax / 127, so a value at the extreme maps to +-127. Where absmax is
    effectively zero we substitute an absmax of 1.0 (giving a scale of 1/127) to avoid
    a divide-by-zero in quantize; the slice is all zeros anyway, so any positive scale
    reconstructs it exactly.
    """
    safe = np.where(absmax < _ABSMAX_EPS, 1.0, absmax)
    return (safe / INT8_QMAX).astype(np.float32)


def compute_scale_per_tensor(weight: np.ndarray) -> np.ndarray:
    """One scale for the whole tensor, from its global absolute maximum."""
    absmax = np.max(np.abs(weight)).astype(np.float32)
    return _absmax_scale(np.asarray(absmax))


def compute_scale_per_channel(weight: np.ndarray, axis: int = 0) -> np.ndarray:
    """One scale per slice along axis, from each slice's absolute maximum.

    For a Linear weight of shape (out_features, in_features), axis=0 gives a scale
    per output channel. Reducing over every axis except axis keeps the result
    broadcastable against the original tensor.
    """
    # Normalize a negative axis before comparing, otherwise axis=-1 matches nothing in
    # range(ndim) and the reduction collapses over every axis into a scalar.
    axis = axis % weight.ndim
    reduce_axes = tuple(a for a in range(weight.ndim) if a != axis)
    absmax = np.max(np.abs(weight), axis=reduce_axes)
    return _absmax_scale(absmax)


def _reshape_scale_for_axis(scale: np.ndarray, ndim: int, axis: int) -> np.ndarray:
    """Reshape a 1-D per-channel scale so it broadcasts along axis."""
    axis = axis % ndim
    shape = [1] * ndim
    shape[axis] = scale.shape[0]
    return scale.reshape(shape)


def quantize(
    weight: np.ndarray,
    scale: np.ndarray,
    axis: int | None,
) -> np.ndarray:
    """Quantize to int8: round-to-nearest, then clamp to [-127, 127].

    The clamp matters even though scale is derived from absmax: floating-point error
    in the division can push the extreme value to 127.0000001, and rounding that
    without clamping overflows int8. np.rint uses banker's rounding (round-half-to-even),
    which is the same tie rule most INT8 kernels assume.
    """
    if axis is not None:
        scale = _reshape_scale_for_axis(scale, weight.ndim, axis)
    q = np.rint(weight / scale)
    q = np.clip(q, -INT8_QMAX, INT8_QMAX)
    return q.astype(np.int8)


def dequantize(values: np.ndarray, scale: np.ndarray, axis: int | None) -> np.ndarray:
    """Reconstruct float32 from int8 by multiplying back through the scale."""
    scale = np.asarray(scale, dtype=np.float32)
    if axis is not None:
        scale = _reshape_scale_for_axis(scale, values.ndim, axis)
    return values.astype(np.float32) * scale


def quantize_tensor(
    weight: np.ndarray,
    per_channel: bool = True,
    axis: int = 0,
) -> QuantizedTensor:
    """Compute scales and quantize in one step. Per-channel by default for weights."""
    weight = np.asarray(weight, dtype=np.float32)
    if per_channel:
        scale = compute_scale_per_channel(weight, axis=axis)
        return QuantizedTensor(quantize(weight, scale, axis), scale, axis)
    scale = compute_scale_per_tensor(weight)
    return QuantizedTensor(quantize(weight, scale, None), scale, None)


@dataclass(frozen=True)
class QuantError:
    """Round-trip error between an original tensor and its dequantized form."""

    max_abs_error: float  # worst-case elementwise deviation
    mean_abs_error: float
    relative_error: float  # ||q - w|| / ||w||, the signal-to-quantization-noise proxy


def quantization_error(original: np.ndarray, reconstructed: np.ndarray) -> QuantError:
    """Measure how much information the round-trip lost.

    Relative error is the Frobenius norm of the residual over the norm of the input,
    which is scale-invariant and comparable across layers of different magnitude. A
    fully-zero input gives 0.0 relative error rather than a NaN.
    """
    original = np.asarray(original, dtype=np.float32)
    diff = np.abs(original - reconstructed)
    denom = np.linalg.norm(original)
    relative = float(np.linalg.norm(diff) / denom) if denom > _ABSMAX_EPS else 0.0
    return QuantError(
        max_abs_error=float(np.max(diff)) if diff.size else 0.0,
        mean_abs_error=float(np.mean(diff)) if diff.size else 0.0,
        relative_error=relative,
    )


@dataclass
class QuantPolicy:
    """Decides which tensors stay in full precision.

    Two independent skip rules, because sensitivity shows up in two ways. Name patterns
    catch tensors known a priori to be sensitive (layer norms, embeddings, the LM head).
    A minimum element count skips tensors too small for INT8 to pay off: the per-channel
    scale metadata and the dequantize overhead can exceed the memory saved. Real
    deployments also skip on measured per-layer error above a tuned threshold; that
    calibration data is proprietary and not included here.
    """

    # Substrings matched case-insensitively against the tensor name. These names are
    # illustrative of the usual suspects, not tuned to any specific model. Substring
    # matching is coarse: "bias" also skips a 2-D weight whose name merely contains it
    # (a fused "...attn_bias_proj.weight"), which a real deployment tightens with
    # word-boundary or exact-suffix rules.
    skip_name_patterns: list[str] = field(
        default_factory=lambda: ["norm", "ln_", "embed", "lm_head", "bias"]
    )
    min_elements: int = 4096

    def __post_init__(self) -> None:
        joined = "|".join(re.escape(p) for p in self.skip_name_patterns)
        self._name_re = re.compile(joined, re.IGNORECASE) if joined else None

    def should_skip(self, name: str, shape: tuple[int, ...]) -> bool:
        """True if this tensor must be kept in higher precision."""
        if self._name_re is not None and self._name_re.search(name):
            return True
        return int(np.prod(shape)) < self.min_elements

    def sensitivity_score(self, name: str, weight: np.ndarray) -> float:
        """Per-tensor sensitivity used to gate quantization by measured error.

        The real scorer combines calibration statistics, activation ranges, and a
        tuned threshold. Omitted from the portfolio excerpt.
        """
        raise NotImplementedError(
            "sensitivity scoring omitted from portfolio excerpt"
        )


def quantize_state_dict(
    weights: dict[str, np.ndarray],
    policy: QuantPolicy | None = None,
) -> dict[str, QuantizedTensor | np.ndarray]:
    """Quantize a whole state dict, honoring the skip policy.

    Skipped tensors are returned as their original float32 array so a caller can write
    a mixed-precision checkpoint without special-casing lookups. Quantized tensors are
    returned as QuantizedTensor.
    """
    policy = policy or QuantPolicy()
    out: dict[str, QuantizedTensor | np.ndarray] = {}
    for name, weight in weights.items():
        weight = np.asarray(weight, dtype=np.float32)
        if policy.should_skip(name, weight.shape) or weight.ndim < 2:
            # 1-D tensors have no output channel to quantize per-channel over, and
            # are cheap to keep in full precision regardless.
            out[name] = weight
        else:
            out[name] = quantize_tensor(weight, per_channel=True, axis=0)
    return out


if __name__ == "__main__":
    # Show the per-channel path and the round-trip error on a synthetic linear weight.
    rng = np.random.default_rng(0)
    w = rng.standard_normal((256, 512)).astype(np.float32)
    w[0] *= 40.0  # one high-range row: this is what per-channel handles well

    qt = quantize_tensor(w, per_channel=True, axis=0)
    recon = dequantize(qt.values, qt.scale, qt.axis)
    err = quantization_error(w, recon)
    print(f"per-channel relative error: {err.relative_error:.5f}")
    print(f"per-channel max abs error:  {err.max_abs_error:.5f}")

    # Contrast with per-tensor, where the one loud row inflates the single scale and
    # coarsens every other row.
    qt1 = quantize_tensor(w, per_channel=False)
    err1 = quantization_error(w, dequantize(qt1.values, qt1.scale, qt1.axis))
    print(f"per-tensor relative error:  {err1.relative_error:.5f}")
