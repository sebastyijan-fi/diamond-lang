use diamond_backend::ArtifactFormat;
use diamond_compiler_tests::{
    compile_text, compile_text_with_backend, EmittedArtifact, TestCompileOutput,
};
use tempfile::tempdir;

fn assert_frontend_stub(output: &TestCompileOutput) {
    assert!(
        output.source.path().is_none(),
        "unexpected path on anonymous source"
    );
    assert_eq!(
        output.compilation.ast.module().name().join(),
        "main",
        "module name should fall back to `main`"
    );
    assert!(
        output.artifact.is_none(),
        "frontend-only compilation should not emit an artifact"
    );
    assert_eq!(
        output.compilation.hir.name.join(),
        "placeholder",
        "placeholder lowering should be returned for now"
    );
}

#[test]
fn frontend_smoke_compiles_basic_module() {
    let output =
        compile_text("smoke:basic", "effect main {}").expect("frontend compilation should succeed");
    assert_frontend_stub(&output);
}

#[test]
fn backend_smoke_emits_wasm_component() {
    let output = compile_text_with_backend("examples/hello.dm", "effect main {}")
        .expect("backend emission should succeed");

    let artifact = output
        .artifact()
        .expect("backend compilation should produce an artifact");

    assert_eq!(
        output.source.path(),
        Some("examples/hello.dm"),
        "source path should be preserved"
    );
    assert_eq!(
        output.compilation.ast.module().name().join(),
        "hello",
        "module name should derive from file stem"
    );
    assert_eq!(
        artifact.format,
        ArtifactFormat::WasmComponent,
        "expected wasm component artifact"
    );
    assert!(
        artifact.bytes.starts_with(b"\0asm"),
        "component bytes must start with the wasm magic"
    );
    assert!(
        artifact.bytes.len() > 8,
        "component should contain more than the header"
    );
}

#[test]
fn backend_artifact_can_be_persisted_to_disk() {
    let output =
        compile_text_with_backend("examples/persist.dm", "effect main {}").expect("compiles");

    let artifact: &EmittedArtifact = output
        .artifact()
        .expect("artifact should be available for backend builds");

    let dir = tempdir().expect("tempdir creation");
    let artifact_path = dir.path().join("module.wasm");

    artifact
        .write_to_path(&artifact_path)
        .expect("writing artifact must succeed");

    let written = std::fs::read(&artifact_path).expect("artifact should exist on disk");
    assert_eq!(
        written, artifact.bytes,
        "persisted bytes must equal the in-memory artifact"
    );
}
