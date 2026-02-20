# LLM Renderer Adaptability Assessment

## Verdict

The codebase is **moderately adaptable** for an “LLM as semantic renderer” architecture.

- **Good fit areas:** typed contracts, analyzer abstraction, channel-agnostic message API, background jobs, and basic caching.
- **Missing pieces:** render-specific schema, deterministic rendering engine layer, style-pack/asset system, and strict JSON validation/retry loop for composition output.

## Existing strengths you can reuse

1. **Interface-first architecture already exists**
   - Analyzer and provider contracts are explicit and swappable.
   - This reduces migration risk when adding a new `Compositor` or `Renderer` contract.

2. **Typed outputs already normalized for analysis**
   - Existing Pydantic models demonstrate a pattern for strict intermediate formats.
   - The same approach can be extended to a render AST/JSON schema.

3. **Channel-agnostic API design is already present**
   - `/api/v1/messages/analyze` is content-channel neutral.
   - A parallel `/api/v1/render/compose` endpoint could follow similar DTO patterns.

4. **Scaling primitives are present**
   - Batch sync/async flows and job worker tasks already exist.
   - Render tasks (HTML/PDF generation) could plug into current async processing patterns.

5. **Cost optimization mindset exists**
   - Hash-based analysis caching is implemented.
   - Can be expanded to content+style-pack+version caching for render artifacts.

## Main gaps for “LLM as renderer”

1. **No render AST schema yet**
   - Current LLM components return analysis-centric structures.
   - Need a strict compositional schema (`blocks`, `spans`, `decorations`, a11y metadata).

2. **No deterministic rendering layer abstraction**
   - Templates exist for site pages, but there is no renderer service mapping semantic tokens → HTML/SVG/PDF deterministically.

3. **No style-pack system**
   - No registry for motifs, tokenized colors, typography rules, or ornament assets.

4. **Validation/retry loop not formalized for generation outputs**
   - Some local JSON parsing exists, but there isn’t a generalized “schema validation + corrective reprompt” pipeline.

5. **Limited observability for render quality**
   - No snapshot/golden testing for visual or structural render outputs yet.

## Suggested minimal implementation path

1. Add `rendering/contracts.py` with:
   - `CompositorInterface` (LLM → strict JSON)
   - `RendererInterface` (JSON AST → HTML/SVG/PDF)

2. Add Pydantic models in `rendering/types.py`:
   - `DocumentAST`, `Block`, `Span`, `Decoration`, enums for style tokens.

3. Add a `StylePackRegistry`:
   - token-only choices (motif families, palette tokens, font tokens, intensity levels).

4. Add deterministic render service:
   - JSON → componentized HTML with drop-cap component mapping.
   - Optional HTML → PDF via headless browser in async worker.

5. Add cache key strategy:
   - `hash(text + style_pack + schema_version + renderer_version)`.

6. Add tests:
   - schema validation tests
   - golden JSON fixtures for compositor output
   - snapshot tests for generated HTML/SVG

## Overall adaptability score

- **Foundation quality:** 8/10
- **Render-readiness today:** 4/10
- **Effort for MVP (semantic renderer):** moderate (likely 1–2 focused sprints)
- **Effort for pixel-perfect publishing pipeline:** high (requires full layout/render stack)

