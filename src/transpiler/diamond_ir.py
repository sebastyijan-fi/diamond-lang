"""Language-agnostic Diamond IR for transpiler backends."""

from __future__ import annotations

from dataclasses import dataclass

IR_VERSION = "0.1.0"


@dataclass(frozen=True)
class Param:
    name: str
    type_expr: TypeExpr


@dataclass(frozen=True)
class TypeName:
    name: str


@dataclass(frozen=True)
class TypeList:
    inner: TypeExpr


@dataclass(frozen=True)
class TypeField:
    name: str
    type_expr: TypeExpr


@dataclass(frozen=True)
class TypeRecord:
    fields: list[TypeField]


TypeExpr = TypeName | TypeList | TypeRecord


@dataclass(frozen=True)
class NumberExpr:
    value: str


@dataclass(frozen=True)
class StringExpr:
    value: str


@dataclass(frozen=True)
class BoolExpr:
    value: bool


LiteralExpr = NumberExpr | StringExpr | BoolExpr


@dataclass(frozen=True)
class PatternWild:
    pass


@dataclass(frozen=True)
class PatternIdent:
    name: str


@dataclass(frozen=True)
class PatternLiteral:
    literal: Expr


Pattern = PatternWild | PatternIdent | PatternLiteral


@dataclass(frozen=True)
class NameExpr:
    name: str


@dataclass(frozen=True)
class ListExpr:
    items: list[Expr]


@dataclass(frozen=True)
class MapItem:
    key: str
    key_is_string: bool
    value: Expr


@dataclass(frozen=True)
class MapExpr:
    items: list[MapItem]


@dataclass(frozen=True)
class UnaryExpr:
    op: str
    expr: Expr


@dataclass(frozen=True)
class BinaryExpr:
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class TernaryExpr:
    cond: Expr
    then_expr: Expr
    else_expr: Expr


@dataclass(frozen=True)
class SequenceExpr:
    items: list[Expr]


@dataclass(frozen=True)
class MatchArm:
    pattern: Pattern
    expr: Expr


@dataclass(frozen=True)
class MatchExpr:
    subject: Expr
    arms: list[MatchArm]


@dataclass(frozen=True)
class CallExpr:
    func: Expr
    args: list[Expr]


@dataclass(frozen=True)
class MemberExpr:
    obj: Expr
    name: str


@dataclass(frozen=True)
class IndexExpr:
    obj: Expr
    index: Expr


@dataclass(frozen=True)
class SliceExpr:
    obj: Expr
    start: Expr | None
    end: Expr | None


@dataclass(frozen=True)
class PatchExpr:
    obj: Expr
    items: list[MapItem]


@dataclass(frozen=True)
class MapBindExpr:
    base: Expr
    key: str
    value: Expr


@dataclass(frozen=True)
class RangeExpr:
    start: Expr
    end: Expr


@dataclass(frozen=True)
class PropagateExpr:
    expr: Expr


@dataclass(frozen=True)
class ExceptionMatchExpr:
    exc: Expr
    types: list[Expr]


@dataclass(frozen=True)
class ReraiseExpr:
    pass


@dataclass(frozen=True)
class TryCatchExpr:
    body: Expr
    err_name: str
    handler: Expr


@dataclass(frozen=True)
class DecoratorExpr:
    decorator: Expr
    target: Expr


Expr = (
    NameExpr
    | NumberExpr
    | StringExpr
    | BoolExpr
    | ListExpr
    | MapExpr
    | UnaryExpr
    | BinaryExpr
    | TernaryExpr
    | SequenceExpr
    | MatchExpr
    | CallExpr
    | MemberExpr
    | IndexExpr
    | SliceExpr
    | PatchExpr
    | MapBindExpr
    | RangeExpr
    | PropagateExpr
    | ExceptionMatchExpr
    | ReraiseExpr
    | TryCatchExpr
    | DecoratorExpr
)


@dataclass(frozen=True)
class TraceEntryOp:
    pass


@dataclass(frozen=True)
class TraceExitOp:
    pass


@dataclass(frozen=True)
class CapabilityCheckOp:
    required: list[str]


@dataclass(frozen=True)
class ResourceIncrementOp:
    counter: str


@dataclass(frozen=True)
class ErrorContextOp:
    pass


ToolOp = TraceEntryOp | TraceExitOp | CapabilityCheckOp | ResourceIncrementOp | ErrorContextOp


@dataclass(frozen=True)
class FuncDecl:
    name: str
    params: list[Param]
    return_type: TypeExpr
    body: Expr
    tools: list[str]
    tool_ops: list[ToolOp]


@dataclass(frozen=True)
class ClassDecl:
    name: str
    params: list[Param]
    body: Expr


@dataclass(frozen=True)
class MethodDecl:
    class_name: str
    func_decl: FuncDecl


TopLevelDecl = FuncDecl | ClassDecl | MethodDecl


@dataclass(frozen=True)
class Program:
    module_name: str
    decls: list[TopLevelDecl]
    ir_version: str = IR_VERSION
