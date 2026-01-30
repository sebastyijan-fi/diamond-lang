use std::path::Path;

use anyhow::Error as AnyError;
use diamond_hir::{
    lower_frontend_module,
    placeholder::{FrontendItem, FrontendModule},
    Identifier, Module, QualifiedName, Span,
};
use thiserror::Error;

/// Re-export frequently used HIR types so downstream crates can work with a
/// single frontend import.
pub use diamond_hir::{EffectRef, EffectSet};

/// Unique handle assigned to a source input (file, virtual buffer, etc.).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SourceId(u64);

impl SourceId {
    /// Creates a new `SourceId` from the provided raw value.
    pub const fn new(raw: u64) -> Self {
        Self(raw)
    }

    /// Returns the raw identifier.
    pub const fn raw(self) -> u64 {
        self.0
    }
}

/// Metadata describing the origin of a compilation unit.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SourceFile {
    id: SourceId,
    path: Option<String>,
}

impl SourceFile {
    /// Creates a source without a corresponding filesystem path (e.g., REPL).
    pub fn anonymous(id: SourceId) -> Self {
        Self { id, path: None }
    }

    /// Creates a source and attaches a path used for module name inference.
    pub fn with_path(id: SourceId, path: impl Into<String>) -> Self {
        Self {
            id,
            path: Some(path.into()),
        }
    }

    /// Returns the source identifier.
    pub fn id(&self) -> SourceId {
        self.id
    }

    /// Returns the backing path if available.
    pub fn path(&self) -> Option<&str> {
        self.path.as_deref()
    }

    /// Best-effort inference of a Diamond module name from the source path.
    pub fn inferred_module_name(&self) -> QualifiedName {
        if let Some(path) = self.path() {
            let path = Path::new(path);
            if let Some(stem) = path
                .file_stem()
                .and_then(|stem| stem.to_str())
                .filter(|stem| !stem.is_empty())
            {
                let normalized = stem.replace('-', "_");
                return QualifiedName::new(vec![Identifier::new(normalized)]);
            }
        }
        QualifiedName::new(vec![Identifier::new("main")])
    }
}

/// Result of a frontend compilation run.
#[derive(Clone, Debug)]
pub struct Compilation {
    pub source: SourceFile,
    pub tokens: Vec<Token>,
    pub ast: Ast,
    pub hir: Module,
}

impl Compilation {
    /// Consumes the compilation and returns the produced HIR module.
    pub fn into_hir(self) -> Module {
        self.hir
    }
}

/// Errors raised by the frontend pipeline.
#[derive(Debug, Error)]
pub enum FrontendError {
    #[error("frontend diagnostics not yet implemented")]
    DiagnosticsUnavailable,
    #[error("lowering failed: {0}")]
    LoweringFailed(#[from] AnyError),
}

/// Runs the full frontend pipeline (lex/parse/lower) for a given source.
pub fn compile_source(source: SourceFile, input: &str) -> Result<Compilation, FrontendError> {
    let tokens = lex(input)?;
    let ast = parse(&source, input, &tokens)?;
    let frontend_module = synthesize_frontend_module(&ast);
    let hir = lower_frontend_module(&frontend_module)?;
    Ok(Compilation {
        source,
        tokens,
        ast,
        hir,
    })
}

/// Token produced by the lexer.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Token {
    kind: TokenKind,
    span: Span,
}

impl Token {
    pub fn new(kind: TokenKind, span: Span) -> Self {
        Self { kind, span }
    }

    pub fn kind(&self) -> TokenKind {
        self.kind
    }

    pub fn span(&self) -> Span {
        self.span
    }
}

/// Token kinds understood by the lexer.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum TokenKind {
    Layout,
    Ident,
    Number,
    String,
    Keyword,
    Punct,
}

/// Concrete syntax tree produced by the parser.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Ast {
    module: AstModule,
}

impl Ast {
    pub fn module(&self) -> &AstModule {
        &self.module
    }
}

/// Concrete representation of a module before lowering.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AstModule {
    name: QualifiedName,
    span: Span,
    items: Vec<AstItem>,
}

impl AstModule {
    pub fn name(&self) -> &QualifiedName {
        &self.name
    }

    pub fn items(&self) -> &[AstItem] {
        &self.items
    }

    pub fn span(&self) -> Span {
        self.span
    }
}

/// Items contained inside an AST module.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum AstItem {
    Function(AstFunction),
}

/// Function item captured during parsing.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AstFunction {
    name: Identifier,
    span: Span,
}

impl AstFunction {
    pub fn name(&self) -> &Identifier {
        &self.name
    }

    pub fn span(&self) -> Span {
        self.span
    }

    /// Creates a stub main function at the provided span.
    fn stub_main(span: Span) -> Self {
        Self {
            name: Identifier::new("main"),
            span,
        }
    }
}

fn lex(_input: &str) -> Result<Vec<Token>, FrontendError> {
    Ok(Vec::new())
}

fn parse(source: &SourceFile, input: &str, _tokens: &[Token]) -> Result<Ast, FrontendError> {
    let span = Span::new(0, saturating_len(input.len()));
    let module = AstModule {
        name: source.inferred_module_name(),
        span,
        items: vec![AstItem::Function(AstFunction::stub_main(span))],
    };
    Ok(Ast { module })
}

fn synthesize_frontend_module(ast: &Ast) -> FrontendModule {
    let items = ast
        .module()
        .items()
        .iter()
        .map(|item| match item {
            AstItem::Function(func) => FrontendItem::Function {
                name: func.name().clone(),
                span: func.span(),
            },
        })
        .collect();

    FrontendModule {
        name: ast.module().name().clone(),
        span: ast.module().span(),
        items,
    }
}

fn saturating_len(len: usize) -> u32 {
    len.min(u32::MAX as usize) as u32
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compile_source_produces_stub_hir() {
        let source = SourceFile::with_path(SourceId::new(1), "examples/hello.dm");
        let compilation =
            compile_source(source.clone(), "effect main {}").expect("stub compile succeeds");

        assert!(compilation.tokens.is_empty());
        assert_eq!(compilation.source, source);
        assert_eq!(compilation.ast.module().name().join(), "hello");
        assert_eq!(compilation.ast.module().items().len(), 1);

        // HIR lowering is still placeholder-level, but the surface remains stable.
        assert_eq!(compilation.hir.name.join(), "placeholder");
    }

    #[test]
    fn inferred_module_name_falls_back_to_main() {
        let source = SourceFile::anonymous(SourceId::new(7));
        let name = source.inferred_module_name();
        assert_eq!(name.join(), "main");
    }
}
