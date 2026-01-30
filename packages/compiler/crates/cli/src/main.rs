use std::{
    collections::hash_map::DefaultHasher,
    fs,
    hash::{Hash, Hasher},
    path::{Path, PathBuf},
};

use anyhow::{Context, Result};
use clap::Parser;
use diamond_backend::{BackendEmitter, BackendOptions};
use diamond_frontend::{compile_source, Compilation, SourceFile, SourceId};
use diamond_hir::Program;
use tracing::{debug, info};
use tracing_subscriber::EnvFilter;

/// Diamond language command-line compiler.
///
/// This CLI wires together the frontend (lexing/parsing) and backend (Wasm
/// component emission) so contributors can exercise the nascent toolchain while
/// the real compiler functionality is implemented incrementally.
#[derive(Parser, Debug)]
#[command(author, version, about = "Diamond language reference compiler", long_about = None)]
struct Args {
    /// Path to the Diamond source file (.dm) to compile.
    #[arg(value_name = "INPUT")]
    input: PathBuf,

    /// Output path for the emitted WebAssembly component.
    /// Defaults to the input path with a `.wasm` extension.
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Disable embedding human-readable debug names in the emitted component.
    #[arg(long)]
    no_debug_names: bool,
}

fn main() -> Result<()> {
    init_tracing();
    let args = Args::parse();
    run(args)
}

fn run(args: Args) -> Result<()> {
    let Args {
        input,
        output,
        no_debug_names,
    } = args;

    let source_contents = fs::read_to_string(&input)
        .with_context(|| format!("failed to read Diamond source from {}", input.display()))?;

    let source_id = source_id_from_path(&input);
    let source_file = SourceFile::with_path(source_id, input.to_string_lossy().into_owned());

    let compilation: Compilation = compile_source(source_file.clone(), &source_contents)?;

    let token_count = compilation.tokens.len();
    let item_count = compilation.ast.module().items().len();

    debug!(
        module = %source_file.inferred_module_name().join(),
        tokens = token_count,
        items = item_count,
        "frontend pipeline completed"
    );

    let mut program = Program::new();
    program.upsert_module(compilation.into_hir());

    let backend_options = BackendOptions {
        embed_debug_names: !no_debug_names,
    };
    let emitter = BackendEmitter::new(backend_options);
    let artifact = emitter
        .emit_program(&program)
        .with_context(|| "backend emission failed")?;

    let output_path = output.unwrap_or_else(|| default_output_path(&input));

    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("failed to create output directory {}", parent.display()))?;
    }

    fs::write(&output_path, artifact.as_bytes()).with_context(|| {
        format!(
            "failed to write emitted component to {}",
            output_path.display()
        )
    })?;

    info!(
        bytes = artifact.as_bytes().len(),
        path = %output_path.display(),
        "emitted WebAssembly component"
    );

    Ok(())
}

fn init_tracing() {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    let _ = tracing_subscriber::fmt()
        .with_env_filter(env_filter)
        .with_target(false)
        .try_init();
}

fn source_id_from_path(path: &Path) -> SourceId {
    let mut hasher = DefaultHasher::new();
    path.to_string_lossy().hash(&mut hasher);
    SourceId::new(hasher.finish())
}

fn default_output_path(input: &Path) -> PathBuf {
    let mut path = input.to_path_buf();
    path.set_extension("wasm");
    path
}
