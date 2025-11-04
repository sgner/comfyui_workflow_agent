**Read this in other languages: [English](README.md), [中文](README_CN.md).**

# comfy-ui-workflow-agent

An intelligent agent designed for **ComfyUI**, providing workflow generation, debugging, optimization, and parameter testing capabilities.

## Main Problems and Solutions

| Problem                                      | Solution                                                        |
| -------------------------------------------- | --------------------------------------------------------------- |
| JSON too large and complex                   | Split into intermediate IR + incremental generation             |
| Complex node dependencies                    | Graph structure management (Node Graph)                         |
| Tedious node parameters                      | Node Registry + auto-completion                                 |
| Difficult for models to directly output JSON | Generate structural instructions (DSL) instead                  |
| Poor maintainability                         | Multi-agent layered collaboration (Builder / Validator / Fixer) |

Let the large model **avoid generating JSON directly**, and instead generate **operations that construct the JSON**.

Program logic ensures structural correctness, while multi-agent collaboration ensures task completeness.

In this approach, the final JSON is **the result**, not the **generation target**.

## Workflow

```text
User input: “Create a workflow that denoises and then upscales an image”
↓
LLM → Outputs semantic IR (intermediate step description)
↓
Node Matcher → Matches actual ComfyUI nodes
↓
Graph Builder → Assembles into valid workflow JSON
↓
Validator → Verifies and corrects
↓
Outputs final JSON that can be imported into ComfyUI
```

## License

MIT License

