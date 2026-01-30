//! High-level intermediate representation (HIR) for the Diamond compiler.
//!
//! The structures in this module model the post-syntax, pre-lowering view of
//! Diamond modules. They intentionally err on the side of being expressive
//! enough for future passes (effects, capabilities, refinement types) while
//! keeping the initial bootstrap light so downstream crates can already depend
//! on the shape of the API.

use std::cmp::Ordering;
use std::fmt;

use indexmap::IndexMap;
use once_cell::sync::Lazy;
use tracing::instrument;

/// Identifier used within the HIR.
///
/// Identifiers preserve the original spelling for diagnostics while also
/// providing a case-sensitive `Ord` implementation to enable deterministic
/// ordering in maps.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Identifier {
    spelling: String,
}

impl Identifier {
    /// Constructs a new identifier from the provided spelling.
    pub fn new(spelling: impl Into<String>) -> Self {
        Self {
            spelling: spelling.into(),
        }
    }

    /// Returns the raw spelling captured from source.
    pub fn as_str(&self) -> &str {
        &self.spelling
    }
}

impl PartialOrd for Identifier {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.spelling.cmp(&other.spelling))
    }
}

impl Ord for Identifier {
    fn cmp(&self, other: &Self) -> Ordering {
        self.partial_cmp(other)
            .expect("identifier ordering is total")
    }
}

/// Stable handle to a module within a program.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct ModuleId(pub u32);

impl ModuleId {
    /// Creates a new module identifier from a raw value.
    pub const fn new(raw: u32) -> Self {
        Self(raw)
    }

    /// Extracts the raw identifier.
    pub const fn raw(self) -> u32 {
        self.0
    }
}

/// Root container for all modules participating in a compilation unit.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Program {
    modules: IndexMap<ModuleId, Module>,
}

impl Program {
    /// Returns an empty program.
    pub fn new() -> Self {
        Self {
            modules: IndexMap::new(),
        }
    }

    /// Inserts or replaces a module with the given identifier.
    pub fn upsert_module(&mut self, module: Module) -> Option<Module> {
        self.modules.insert(module.id, module)
    }

    /// Returns an iterator over all modules in insertion order.
    pub fn modules(&self) -> impl Iterator<Item = (&ModuleId, &Module)> {
        self.modules.iter()
    }
}

/// Single Diamond module described in HIR form.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Module {
    pub id: ModuleId,
    pub name: QualifiedName,
    pub visibility: Visibility,
    pub items: Vec<Item>,
    pub capabilities: CapabilitySet,
    pub span: Span,
}

impl Module {
    /// Constructs an empty module placeholder.
    pub fn empty(id: ModuleId, name: QualifiedName, span: Span) -> Self {
        Self {
            id,
            name,
            visibility: Visibility::Module,
            items: Vec::new(),
            capabilities: CapabilitySet::default(),
            span,
        }
    }
}

/// Combined name parts for modules, effects, types, etc.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct QualifiedName {
    pub components: Vec<Identifier>,
}

impl QualifiedName {
    /// Constructs a qualified name from individual identifier components.
    pub fn new(components: impl Into<Vec<Identifier>>) -> Self {
        Self {
            components: components.into(),
        }
    }

    /// Returns whether the name is top-level (single segment).
    pub fn is_simple(&self) -> bool {
        self.components.len() <= 1
    }

    /// Formats the qualified name using `.` separators.
    pub fn join(&self) -> String {
        self.components
            .iter()
            .map(Identifier::as_str)
            .collect::<Vec<_>>()
            .join(".")
    }
}

/// Visibility of items within a module.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Visibility {
    /// Visible everywhere (public export).
    Public,
    /// Visible within the declaring module and its nested scopes.
    Module,
    /// Visible only within the declaring lexical scope.
    Private,
}

/// Module-level item.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Item {
    Function(Function),
    Effect(EffectDeclaration),
    TypeAlias(TypeAlias),
}

impl Item {
    /// Returns the identifier associated with the item.
    pub fn name(&self) -> &Identifier {
        match self {
            Item::Function(fun) => &fun.name,
            Item::Effect(effect) => &effect.name.components.last().expect("non-empty name"),
            Item::TypeAlias(alias) => &alias.name,
        }
    }
}

/// HIR-level function declaration.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Function {
    pub name: Identifier,
    pub visibility: Visibility,
    pub generics: Vec<GenericParam>,
    pub params: Vec<Parameter>,
    pub result: Type,
    pub effects: EffectSet,
    pub body: Block,
    pub span: Span,
}

/// Effect declaration (algebraic effect signature).
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct EffectDeclaration {
    pub name: QualifiedName,
    pub operations: Vec<EffectOperation>,
    pub span: Span,
}

/// Individual algebraic effect operation.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct EffectOperation {
    pub name: Identifier,
    pub params: Vec<Parameter>,
    pub output: Type,
    pub resumable: bool,
    pub span: Span,
}

/// Type alias item.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct TypeAlias {
    pub name: Identifier,
    pub generics: Vec<GenericParam>,
    pub ty: Type,
    pub span: Span,
}

/// Generic parameter.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct GenericParam {
    pub name: Identifier,
    pub kind: GenericKind,
    pub span: Span,
}

/// Kinds of generics supported by the language.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum GenericKind {
    Type,
    Capability,
    Effect,
}

/// Function or operation parameter.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Parameter {
    pub pattern: Pattern,
    pub ty: Type,
    pub span: Span,
}

/// Pattern supported in parameter positions (more variants will follow).
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Pattern {
    Identifier(Identifier),
    Wildcard,
}

/// Canonical block expression.
#[derive(Clone, Debug, PartialEq, Eq, Default)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Block {
    pub statements: Vec<Statement>,
    pub expr: Option<Box<Expr>>,
    pub span: Span,
}

/// Statement node.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Statement {
    Let(LetBinding),
    Expr(Expr),
}

/// Let-binding statement.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct LetBinding {
    pub pattern: Pattern,
    pub ty: Option<Type>,
    pub value: Expr,
    pub span: Span,
}

/// Expression node (subset for the bootstrap state).
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Expr {
    Block(Block),
    Identifier(Identifier, Span),
    Literal(Literal),
    Call(Call),
    Perform(Perform),
    Handle(Handle),
}

/// Literal constants.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Literal {
    Integer(i64, Span),
    Decimal(String, Span),
    String(String, Span),
    Boolean(bool, Span),
    Unit(Span),
}

/// Function or operation call expression.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Call {
    pub callee: Box<Expr>,
    pub arguments: Vec<Expr>,
    pub span: Span,
}

/// Perform-expression: invokes an effect operation.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Perform {
    pub effect: QualifiedName,
    pub operation: Identifier,
    pub payload: Vec<Expr>,
    pub span: Span,
}

/// Effect handler expression.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Handle {
    pub handler: Box<Expr>,
    pub body: Box<Expr>,
    pub clauses: Vec<HandleClause>,
    pub span: Span,
}

/// Individual clause inside a handle expression.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct HandleClause {
    pub effect: QualifiedName,
    pub operation: Identifier,
    pub params: Vec<Pattern>,
    pub resume: Option<Identifier>,
    pub body: Block,
    pub span: Span,
}

/// Types supported at the HIR level.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub enum Type {
    Name(QualifiedName, Span),
    Unit(Span),
    Bool(Span),
    Integer(Span),
    Float(Span),
    String(Span),
    /// Function type `A ->{E} B`.
    Function {
        params: Vec<Type>,
        effects: EffectSet,
        result: Box<Type>,
        span: Span,
    },
    /// Placeholder for types that desugar to structural forms later.
    Opaque(String, Span),
}

/// Collection of effects referenced by a function signature or type.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct EffectSet {
    pub effects: Vec<EffectRef>,
    pub span: Span,
}

impl EffectSet {
    /// Creates an empty effect set at the provided span.
    pub fn empty(span: Span) -> Self {
        Self {
            effects: Vec::new(),
            span,
        }
    }
}

/// Reference to an effect with optional capability witness.
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct EffectRef {
    pub name: QualifiedName,
    pub capability: Option<Identifier>,
    pub span: Span,
}

/// Set of capabilities required by a module or function.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct CapabilitySet {
    pub entries: Vec<CapabilityRef>,
    pub span: Span,
}

/// Capability requirement (object-capability model).
#[derive(Clone, Debug, PartialEq, Eq)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct CapabilityRef {
    pub name: QualifiedName,
    pub alias: Option<Identifier>,
    pub span: Span,
}

/// Closed-open byte span.
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Span {
    pub start: u32,
    pub end: u32,
}

impl Span {
    /// Creates a new span.
    pub const fn new(start: u32, end: u32) -> Self {
        Self { start, end }
    }

    /// Zero-length span at the provided position.
    pub const fn empty(at: u32) -> Self {
        Self { start: at, end: at }
    }

    /// Merges two spans into the smallest span containing both.
    pub fn merge(self, other: Span) -> Span {
        Span {
            start: self.start.min(other.start),
            end: self.end.max(other.end),
        }
    }
}

impl Default for Span {
    fn default() -> Self {
        Span::empty(0)
    }
}

impl fmt::Debug for Span {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}..{}", self.start, self.end)
    }
}

/// Placeholder lowering pipeline entrypoint.
///
/// The real implementation will consume the frontend AST and produce HIR
/// modules, including capability resolution and initial effect inference.
#[instrument(skip_all)]
pub fn lower_frontend_module(
    _module: &crate::placeholder::FrontendModule,
) -> anyhow::Result<Module> {
    static EMPTY_MODULE: Lazy<Module> = Lazy::new(|| {
        Module::empty(
            ModuleId::new(0),
            QualifiedName::new(vec![Identifier::new("placeholder")]),
            Span::default(),
        )
    });

    Ok(EMPTY_MODULE.clone())
}

/// Namespace for temporary types required until the frontend <-> HIR bridge is
/// implemented. This allows downstream crates to compile without pulling in the
/// actual frontend dependency yet.
pub mod placeholder {
    use super::{Identifier, QualifiedName, Span};

    /// Minimal representation of a frontend module head.
    #[derive(Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
    pub struct FrontendModule {
        pub name: QualifiedName,
        pub span: Span,
        pub items: Vec<FrontendItem>,
    }

    /// Simplified view of frontend items for the bootstrap.
    #[derive(Clone, Debug, PartialEq, Eq)]
    #[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
    pub enum FrontendItem {
        Function { name: Identifier, span: Span },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identifiers_order_by_spelling() {
        let mut ids = vec![
            Identifier::new("beta"),
            Identifier::new("alpha"),
            Identifier::new("gamma"),
        ];
        ids.sort();
        let names: Vec<&str> = ids.iter().map(Identifier::as_str).collect();
        assert_eq!(names, vec!["alpha", "beta", "gamma"]);
    }

    #[test]
    fn effect_sets_merge_spans() {
        let span_a = Span::new(0, 3);
        let span_b = Span::new(5, 8);
        let merged = span_a.merge(span_b);
        assert_eq!(merged.start, 0);
        assert_eq!(merged.end, 8);
    }

    #[test]
    fn placeholder_lowering_returns_clone() {
        let module = placeholder::FrontendModule {
            name: QualifiedName::new(vec![Identifier::new("main")]),
            span: Span::default(),
            items: Vec::new(),
        };
        let lowered = lower_frontend_module(&module).expect("lowering succeeds");
        assert_eq!(lowered.name.join(), "placeholder");
    }
}
