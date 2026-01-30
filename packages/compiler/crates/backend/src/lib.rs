use std::borrow::Cow;

use diamond_hir::{Module, Program};
use thiserror::Error;
use tracing::instrument;

/// Result alias for backend emission operations.
pub type BackendResult<T> = Result<T, BackendError>;

/// Options that influence code generation.
///
/// The struct is intentionally minimal for the bootstrap stage; new knobs can
/// be added without breaking callers because `BackendEmitter::new` accepts any
/// value and the type implements `Default`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BackendOptions {
    /// Emit custom sections with human-readable names for debugging.
    pub embed_debug_names: bool,
}

impl Default for BackendOptions {
    fn default() -> Self {
        Self {
            embed_debug_names: true,
        }
    }
}

/// Lightweight artifact container produced by the backend.
///
/// Future iterations will track multiple outputs (e.g., component + metadata),
/// but for now a single byte buffer keeps the API ergonomic.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Artifact {
    bytes: Vec<u8>,
    format: ArtifactFormat,
}

impl Artifact {
    /// Creates a new artifact from raw bytes.
    pub fn new(bytes: Vec<u8>, format: ArtifactFormat) -> Self {
        Self { bytes, format }
    }

    /// Returns the artifact contents as raw bytes.
    pub fn as_bytes(&self) -> &[u8] {
        &self.bytes
    }

    /// Consumes the artifact, yielding the underlying byte vector.
    pub fn into_bytes(self) -> Vec<u8> {
        self.bytes
    }

    /// Indicates the logical format of the emitted artifact.
    pub fn format(&self) -> ArtifactFormat {
        self.format
    }
}

/// Output format tags supported by the backend.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ArtifactFormat {
    /// WebAssembly Component model binary.
    WasmComponent,
}

/// Primary entry point for lowering HIR into runtime artifacts.
#[derive(Debug, Clone)]
pub struct BackendEmitter {
    options: BackendOptions,
}

impl BackendEmitter {
    /// Creates a new emitter with the provided options.
    pub fn new(options: BackendOptions) -> Self {
        Self { options }
    }

    /// Emits the first module within a program as a component artifact.
    ///
    /// The bootstrap compiler only supports single-module emission; multi-module
    /// composition will be layered on later once linking semantics are vetted.
    #[instrument(skip_all)]
    pub fn emit_program(&self, program: &Program) -> BackendResult<Artifact> {
        let module = program
            .modules()
            .next()
            .map(|(_, module)| module)
            .ok_or(BackendError::EmptyProgram)?;

        self.emit_module(module)
    }

    /// Emits a single module.
    #[instrument(skip_all, fields(module = %module.name.join()))]
    pub fn emit_module(&self, module: &Module) -> BackendResult<Artifact> {
        let bytes = encode_component(module, &self.options)?;
        Ok(Artifact::new(bytes, ArtifactFormat::WasmComponent))
    }
}

#[derive(Debug, Error)]
pub enum BackendError {
    #[error("program contains no modules to emit")]
    EmptyProgram,
    #[error("wasm component emission requires the `wasm-components` feature")]
    WasmComponentsDisabled,
    #[error("failed to encode wasm component for module `{module}`: {source}")]
    EncodingFailed {
        module: String,
        #[source]
        source: anyhow::Error,
    },
}

#[cfg(feature = "wasm-components")]
fn encode_component(module: &Module, options: &BackendOptions) -> BackendResult<Vec<u8>> {
    use wasm_encoder::{Component, CustomSection};

    let mut component = Component::new();
    let module_name = module.name.join();
    let debug_payload = if options.embed_debug_names {
        Cow::Owned(module_name.clone())
    } else {
        Cow::Borrowed("")
    };

    if options.embed_debug_names {
        let custom = CustomSection {
            name: Cow::Borrowed("name"),
            data: Cow::Borrowed(debug_payload.as_bytes()),
        };
        component.section(&custom);
    }

    // The bootstrap component is deliberately empty beyond (optional) debug
    // names. Future passes will populate canonical ABI exports, interface
    // types, and component metadata.
    let bytes = component.finish();

    Ok(bytes)
}

#[cfg(not(feature = "wasm-components"))]
fn encode_component(_module: &Module, _options: &BackendOptions) -> BackendResult<Vec<u8>> {
    Err(BackendError::WasmComponentsDisabled)
}

#[cfg(test)]
mod tests {
    use super::*;
    use diamond_hir::{Identifier, ModuleId, QualifiedName, Span};

    fn sample_module(id: u32, name: &str) -> Module {
        let module_id = ModuleId::new(id);
        Module::empty(
            module_id,
            QualifiedName::new(vec![Identifier::new(name)]),
            Span::default(),
        )
    }

    #[cfg(feature = "wasm-components")]
    #[test]
    fn emit_module_produces_component_bytes() {
        let emitter = BackendEmitter::new(BackendOptions::default());
        let module = sample_module(1, "example");

        let artifact = emitter.emit_module(&module).expect("emission succeeds");
        let bytes = artifact.as_bytes();

        // WebAssembly component binaries share the same magic as Wasm modules.
        assert!(bytes.starts_with(b"\0asm"), "expected wasm magic prefix");
        assert_eq!(artifact.format(), ArtifactFormat::WasmComponent);
    }

    #[cfg(not(feature = "wasm-components"))]
    #[test]
    fn emit_module_requires_feature() {
        let emitter = BackendEmitter::new(BackendOptions::default());
        let module = sample_module(1, "example");

        let err = emitter
            .emit_module(&module)
            .expect_err("feature gate enforced");
        matches!(err, BackendError::WasmComponentsDisabled);
    }

    #[test]
    fn emit_program_errors_on_empty_program() {
        let emitter = BackendEmitter::new(BackendOptions::default());
        let program = Program::new();

        let err = emitter
            .emit_program(&program)
            .expect_err("no modules present");
        matches!(err, BackendError::EmptyProgram);
    }
}
