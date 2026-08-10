# Experiment 2 — Completion-Only QLoRA + Explicit EOS

## Configuration

- Base model: Qwen/Qwen2.5-Coder-7B-Instruct
- Training examples: 8,486
- Validation examples: 942
- Epochs: 1
- Optimizer steps: 2,122
- Final training loss: 0.1493
- LoRA rank: 16
- LoRA alpha: 32
- Max sequence length: 2048
- Completion-only loss: enabled
- Explicit EOS: <|im_end|>

## First-50 BIRD Validation Results

| Metric | Experiment 1 | Experiment 2 |
|---|---:|---:|
| Strict correct | 6/50 | 16/50 |
| Strict accuracy | 12.00% | 32.00% |
| Execution correct | 15 | 27 |
| Raw execution accuracy | 30.00% | 54.00% |
| Adjusted execution accuracy | 31.25% | 56.25% |
| Invalid predictions | 20 | 3 |
| Invalid prediction rate | 40.00% | 6.00% |
| Giant LIMIT outputs | Present | 0 |
| SQL > 1000 chars | Present | 0 |

Two examples were excluded from adjusted execution accuracy because
the benchmark gold SQL itself failed against the supplied SQLite database.

## Conclusion

Completion-only supervised fine-tuning combined with an explicit EOS
substantially improved both generation stability and NL2SQL accuracy.

Compared with Experiment 1:

- strict accuracy increased from 12.00% to 32.00%;
- adjusted execution accuracy increased from 31.25% to 56.25%;
- invalid SQL decreased from 40.00% to 6.00%;
- runaway giant-LIMIT generation was eliminated.

The remaining errors should now be analyzed primarily as NL2SQL semantic
and schema-grounding failures rather than generation/stopping failures.
