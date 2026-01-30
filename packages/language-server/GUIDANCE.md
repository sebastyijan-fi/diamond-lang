# Language Server Package Guidance

## Purpose
The `packages/language-server/` package provides the Diamond Language Server Protocol (LSP) implementation—enabling IDE integrations, real-time diagnostics, code completion, and developer productivity features. This package bridges the Diamond compiler with editor environments to deliver a first-class development experience. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, tooling integration, and developer experience requirements.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection.

The language server is the primary touchpoint for Diamond developers—responsiveness, accuracy, and helpfulness here directly impact adoption.

---

## Directory Contract

| Path | Scope & Expectations |
| --- | --- |
| `src/` | LSP server implementation. |
| `src/main.rs` | Server entry point, transport setup (stdio/TCP). |
| `src/server.rs` | Main server logic, request routing, lifecycle management. |
| `src/capabilities.rs` | LSP capability negotiation and registration. |
| `src/handlers/` | Request and notification handlers organized by feature. |
| `src/analysis/` | Semantic analysis integration with compiler crates. |
| `src/diagnostics/` | Diagnostic collection, formatting, and publishing. |
| `src/completion/` | Code completion provider implementation. |
| `src/hover/` | Hover information provider. |
| `src/navigation/` | Go-to-definition, find references, symbol search. |
| `src/formatting/` | Code formatting and range formatting. |
| `src/actions/` | Code actions, quick fixes, refactorings. |
| `tests/` | Integration tests with fixture workspaces. |
| `README.md` | Usage documentation, client configuration guides. |
| `GUIDANCE.md` | This file—contribution and quality standards. |

---

## LSP Feature Matrix

### Core Features (Phase 1)

| Feature | LSP Method | Priority |
| --- | --- | --- |
| Diagnostics | `textDocument/publishDiagnostics` | Critical |
| Hover | `textDocument/hover` | High |
| Go to Definition | `textDocument/definition` | High |
| Completion | `textDocument/completion` | High |
| Document Symbols | `textDocument/documentSymbol` | Medium |
| Formatting | `textDocument/formatting` | Medium |

### Advanced Features (Phase 2)

| Feature | LSP Method | Priority |
| --- | --- | --- |
| Find References | `textDocument/references` | High |
| Rename | `textDocument/rename` | Medium |
| Code Actions | `textDocument/codeAction` | Medium |
| Signature Help | `textDocument/signatureHelp` | Medium |
| Workspace Symbols | `workspace/symbol` | Medium |
| Semantic Tokens | `textDocument/semanticTokens` | Medium |
| Inlay Hints | `textDocument/inlayHint` | Low |
| Call Hierarchy | `textDocument/prepareCallHierarchy` | Low |

### Diamond-Specific Features (Phase 3)

| Feature | Description | Priority |
| --- | --- | --- |
| Effect Navigation | Navigate to effect declarations and handlers | High |
| Capability Inspection | Show required capabilities for functions | High |
| Decision Block Insights | Visualize decision operator branches | Medium |
| Semantic Type Info | Display refinement predicates on hover | Medium |
| Capability Manifest Preview | Generate and preview capability manifests | Low |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Editor/IDE                              │
│               (VS Code, Neovim, JetBrains)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ LSP (JSON-RPC over stdio/TCP)
┌──────────────────────▼──────────────────────────────────────┐
│                  Diamond Language Server                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Transport  │  │  Dispatcher │  │  Document Manager   │  │
│  │  (stdio/TCP)│  │  (routing)  │  │  (file sync)        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────▼────────────────▼─────────────────────▼──────────┐ │
│  │                   Handler Layer                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │ │
│  │  │Diagnostics│ │Completion│ │  Hover   │ │Navigation │  │ │
│  │  └─────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │ │
│  └────────┼───────────┼────────────┼─────────────┼────────┘ │
│           │           │            │             │           │
│  ┌────────▼───────────▼────────────▼─────────────▼────────┐ │
│  │                  Analysis Layer                         │ │
│  │  (Integrates with compiler: frontend, hir crates)       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration with Compiler

The language server uses the compiler crates as libraries:

```rust
use diamond_frontend::{parse, Ast};
use diamond_hir::{lower_module, type_check, TypedHir};

pub struct Analysis {
    /// Parsed AST for each open document.
    asts: HashMap<Url, Ast>,
    /// Type-checked HIR for semantic features.
    hirs: HashMap<Url, TypedHir>,
    /// Collected diagnostics per document.
    diagnostics: HashMap<Url, Vec<Diagnostic>>,
}

impl Analysis {
    /// Reanalyze a document after changes.
    pub fn update(&mut self, uri: &Url, content: &str) {
        // 1. Parse to AST
        let parse_result = parse(content);
        self.asts.insert(uri.clone(), parse_result.ast);
        
        // 2. Collect parse diagnostics
        let mut diags = parse_result.diagnostics;
        
        // 3. Lower to HIR and type-check
        if let Some(ast) = &parse_result.ast {
            match lower_module(ast).and_then(|hir| type_check(hir)) {
                Ok(typed_hir) => {
                    self.hirs.insert(uri.clone(), typed_hir);
                }
                Err(type_errors) => {
                    diags.extend(type_errors);
                }
            }
        }
        
        self.diagnostics.insert(uri.clone(), diags);
    }
}
```

---

## Responsiveness Requirements

The language server must be responsive to maintain developer productivity:

| Operation | Latency Target | Notes |
| --- | --- | --- |
| Diagnostics (on change) | < 100ms | Debounce rapid changes |
| Hover | < 50ms | Use cached analysis |
| Completion | < 100ms | Limit suggestion count |
| Go to Definition | < 50ms | Index symbols |
| Formatting | < 200ms | Stream for large files |
| Find References | < 500ms | Workspace-wide search |

### Incremental Analysis

Implement incremental analysis to meet latency targets:

1. **Parse Incrementally**: Reparse only changed regions when possible.
2. **Cache Aggressively**: Cache AST, HIR, and type information.
3. **Invalidate Precisely**: Track dependencies to invalidate only affected analysis.
4. **Background Processing**: Perform heavy analysis in background threads.

---

## Document Management

```rust
/// Manages synchronized document state with editors.
pub struct DocumentManager {
    documents: HashMap<Url, Document>,
}

pub struct Document {
    pub uri: Url,
    pub content: Rope,
    pub version: i32,
    pub language_id: String,
}

impl DocumentManager {
    /// Handle textDocument/didOpen notification.
    pub fn open(&mut self, params: DidOpenTextDocumentParams);
    
    /// Handle textDocument/didChange notification.
    pub fn change(&mut self, params: DidChangeTextDocumentParams);
    
    /// Handle textDocument/didClose notification.
    pub fn close(&mut self, params: DidCloseTextDocumentParams);
    
    /// Get current document content.
    pub fn get(&self, uri: &Url) -> Option<&Document>;
}
```

---

## Diagnostic Publishing

```rust
/// Diagnostic publisher with debouncing.
pub struct DiagnosticPublisher {
    client: Client,
    pending: HashMap<Url, Vec<Diagnostic>>,
    debounce_timer: Timer,
}

impl DiagnosticPublisher {
    /// Queue diagnostics for publishing.
    pub fn queue(&mut self, uri: Url, diagnostics: Vec<Diagnostic>) {
        self.pending.insert(uri, diagnostics);
        self.debounce_timer.reset(Duration::from_millis(100));
    }
    
    /// Publish all pending diagnostics.
    pub async fn flush(&mut self) {
        for (uri, diagnostics) in self.pending.drain() {
            self.client.publish_diagnostics(uri, diagnostics, None).await;
        }
    }
}
```

---

## Completion Provider

```rust
pub struct CompletionProvider {
    analysis: Arc<RwLock<Analysis>>,
}

impl CompletionProvider {
    pub fn provide(&self, params: CompletionParams) -> Option<CompletionResponse> {
        let analysis = self.analysis.read();
        let uri = &params.text_document_position.text_document.uri;
        let position = params.text_document_position.position;
        
        // Determine completion context
        let context = self.analyze_context(uri, position)?;
        
        let items = match context {
            CompletionContext::Import => self.complete_imports(),
            CompletionContext::Type => self.complete_types(&analysis),
            CompletionContext::Effect => self.complete_effects(&analysis),
            CompletionContext::Identifier => self.complete_identifiers(&analysis, position),
            CompletionContext::FieldAccess(ty) => self.complete_fields(ty),
            CompletionContext::EffectOperation(effect) => self.complete_operations(effect),
        };
        
        Some(CompletionResponse::Array(items))
    }
}
```

---

## Testing Strategy

### Unit Tests
- Test individual handlers in isolation.
- Mock compiler analysis results.
- Verify correct LSP response formatting.

### Integration Tests
Use fixture workspaces with known structures:

```rust
#[tokio::test]
async fn test_hover_on_function() {
    let server = TestServer::new();
    server.open_file("fixtures/simple.dm", r#"
        fn greet(name: String) -> String {
            "Hello, " + name
        }
    "#);
    
    let hover = server.hover("fixtures/simple.dm", Position::new(1, 7)).await;
    
    assert!(hover.contents.contains("fn greet(name: String) -> String"));
}
```

### Client Compatibility Tests
- Test with VS Code, Neovim, and JetBrains protocol implementations.
- Verify capability negotiation works correctly.
- Test edge cases in LSP transport.

---

## Editor Integration

### VS Code Extension
```json
{
  "name": "diamond-lang",
  "displayName": "Diamond Language",
  "description": "Diamond language support",
  "main": "./out/extension.js",
  "activationEvents": ["onLanguage:diamond"],
  "contributes": {
    "languages": [{
      "id": "diamond",
      "extensions": [".dm", ".dia"],
      "configuration": "./language-configuration.json"
    }],
    "configuration": {
      "title": "Diamond",
      "properties": {
        "diamond.server.path": {
          "type": "string",
          "description": "Path to the Diamond language server executable"
        }
      }
    }
  }
}
```

### Neovim Configuration
```lua
require('lspconfig').diamond.setup {
    cmd = { 'diamond-lsp' },
    filetypes = { 'diamond' },
    root_dir = require('lspconfig.util').root_pattern('diamond.toml', '.git'),
}
```

---

## Dependencies

```toml
[dependencies]
# LSP framework
tower-lsp = "0.20"
lsp-types = "0.95"

# Async runtime
tokio = { version = "1", features = ["full"] }

# Compiler integration
diamond-frontend = { path = "../compiler/crates/frontend" }
diamond-hir = { path = "../compiler/crates/hir" }

# Text handling
ropey = "1.6"  # Efficient text rope for document editing

# Utilities
dashmap = "5"  # Concurrent hash map
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tracing = "0.1"
```

---

## Coding Standards

1. **Async Everywhere**: Use async/await for all I/O and potentially slow operations.
2. **Cancellation Support**: Respect LSP cancellation requests for long-running operations.
3. **Error Recovery**: Never crash; return appropriate errors or empty results.
4. **Logging**: Use structured logging with request correlation IDs.
5. **Testing**: Every handler must have corresponding integration tests.

---

## Quality Checklist (Pre-Merge)

- [ ] Handler correctly implements LSP specification.
- [ ] Response latency meets targets for the operation.
- [ ] Errors are handled gracefully without crashes.
- [ ] Logging includes request IDs for debugging.
- [ ] Integration tests cover happy path and error cases.
- [ ] Client compatibility verified (VS Code at minimum).
- [ ] Documentation updated for new features.
- [ ] Memory usage is reasonable for large workspaces.
- [ ] Cancellation is respected for long-running operations.
- [ ] Telemetry spans added for performance monitoring.

---

## Future Enhancements

- Watch mode for file system changes outside editor.
- Multi-root workspace support.
- Project-wide rename with preview.
- Extract function/variable refactorings.
- AI-assisted code actions using Diamond's semantic types.
- Integrated REPL/evaluation in editor.
- Debugger adapter protocol (DAP) integration.
- Notebook support for exploratory Diamond development.

---

The language server is where Diamond meets developers. Every millisecond of latency, every missing completion, every confusing diagnostic impacts productivity and adoption. Build with obsessive attention to responsiveness, accuracy, and helpfulness.