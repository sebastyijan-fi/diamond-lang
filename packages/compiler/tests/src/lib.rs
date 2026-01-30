//! Shared scaffolding used across compiler integration tests.
//!
//! The helpers in this module make it easy to feed source text through the
//! frontend and backend, assert on intermediate representations, and capture
//! emitted artifacts without re-implementing the plumbing in every test.

use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

use anyhow::{Context, Result};
use diamond_backend::{ArtifactFormat, BackendEmitter, BackendOptions};
use diamond_frontend::{compile_source, Compilation, SourceFile, SourceId};
use diamond_hir::Program;

/// Convenient alias for test results.
pub type TestResult<T> = Result<T>;

/// Unique ID generator for synthetic sources.
static NEXT_SOURCE_ID: AtomicU64 = AtomicU64::new(1);

fn fresh_source_id() -> SourceId {
    SourceId::new(NEXT_SOURCE_ID.fetch_add(1, Ordering::Relaxed))
}

/// Output captured from compiling a single Diamond module.
#[derive(Debug)]
pub struct TestCompileOutput {
    /// Metadata about the source file (path, identifier).
    pub source: SourceFile,
    /// Full frontend compilation result (tokens, AST, HIR).
    pub compilation: Compilation,
    /// Optional backend artifact if emission was requested.
    pub artifact: Option<EmittedArtifact>,
}

impl TestCompileOutput {
    /// Returns a reference to the emitted artifact, if present.
    pub fn artifact(&self) -> Option<&EmittedArtifact> {
        self.artifact.as_ref()
    }
}

/// Wrapper around a backend-emitted artifact.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EmittedArtifact {
    pub format: ArtifactFormat,
    pub bytes: Vec<u8>,
}

impl EmittedArtifact {
    /// Saves the artifact to the specified path.
    pub fn write_to_path(&self, path: impl AsRef<Path>) -> Result<()> {
        fs::write(path.as_ref(), &self.bytes)
            .with_context(|| format!("failed to write artifact to {}", path.as_ref().display()))
    }
}

/// Compiles inline source text and returns the frontend compilation, without
/// invoking the backend.
///
/// This is useful for tests that only need to assert on tokens or AST/HIR.
pub fn compile_text(source_name: &str, contents: &str) -> TestResult<TestCompileOutput> {
    compile(source_name, contents, CompileMode::FrontendOnly)
}

/// Compiles inline source text and emits a WebAssembly component via the
/// backend (subject to feature gating in the backend crate).
pub fn compile_text_with_backend(
    source_name: &str,
    contents: &str,
) -> TestResult<TestCompileOutput> {
    compile(source_name, contents, CompileMode::FrontendAndBackend)
}

/// Loads a fixture from disk and compiles it through the frontend.
pub fn compile_fixture(path: impl AsRef<Path>) -> TestResult<TestCompileOutput> {
    let path = path.as_ref();
    let contents = fs::read_to_string(path)
        .with_context(|| format!("failed to read fixture {}", path.display()))?;
    compile(
        path.to_string_lossy().as_ref(),
        &contents,
        CompileMode::FrontendOnly,
    )
}

/// Loads a fixture from disk, compiles it, and emits a backend artifact.
pub fn compile_fixture_with_backend(path: impl AsRef<Path>) -> TestResult<TestCompileOutput> {
    let path = path.as_ref();
    let contents = fs::read_to_string(path)
        .with_context(|| format!("failed to read fixture {}", path.display()))?;
    compile(
        path.to_string_lossy().as_ref(),
        &contents,
        CompileMode::FrontendAndBackend,
    )
}

enum CompileMode {
    FrontendOnly,
    FrontendAndBackend,
}

fn compile(source_name: &str, contents: &str, mode: CompileMode) -> TestResult<TestCompileOutput> {
    let source_path = PathBuf::from(source_name);
    let source_file = if source_path.is_file() || source_path.extension().is_some() {
        SourceFile::with_path(
            fresh_source_id(),
            source_path.to_string_lossy().into_owned(),
        )
    } else {
        SourceFile::anonymous(fresh_source_id())
    };

    let compilation = compile_source(source_file.clone(), contents)?;
    let artifact = match mode {
        CompileMode::FrontendOnly => None,
        CompileMode::FrontendAndBackend => Some(emit_backend(&compilation)?),
    };

    Ok(TestCompileOutput {
        source: source_file,
        compilation,
        artifact,
    })
}

fn emit_backend(compilation: &Compilation) -> TestResult<EmittedArtifact> {
    let mut program = Program::new();
    program.upsert_module(compilation.hir.clone());

    let emitter = BackendEmitter::new(BackendOptions {
        embed_debug_names: true,
    });

    let artifact = emitter.emit_program(&program)?;
    Ok(EmittedArtifact {
        format: artifact.format(),
        bytes: artifact.into_bytes(),
    })
}
