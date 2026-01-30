# Diamond (<>) Grammar Specification

This document outlines the lexical and syntactic structure of the Diamond language. It serves as the canonical reference for parser implementers, compiler authors, and tooling builders. The grammar is presented using an extended Backus–Naur Form (EBNF)-like notation with the following conventions:

- `foo ::= bar` defines non-terminal `foo`.
- Literals appear in single quotes (`'keyword'`).
- Optional sequences are enclosed in square brackets (`[ ... ]`).
- Repetition (zero or more) uses braces (`{ ... }`).
- Alternatives are separated by vertical bars (`|`).
- Lexical productions are prefixed with `token`.

---

## 1. Lexical Structure

### 1.1 Whitespace and Layout

Diamond is layout-sensitive with optional braces. The lexer emits INDENT/DEDENT tokens when indentation meaningfully changes block scope.

```
token WHITESPACE   ::= ' ' | '\t'
token NEWLINE      ::= '\n' | '\r\n'
token COMMENT      ::= '#' { any character except NEWLINE }
```

### 1.2 Identifiers

```
token IDENTIFIER   ::= (LETTER | '_') { LETTER | DIGIT | '_' }
token LETTER       ::= 'A'..'Z' | 'a'..'z'
token DIGIT        ::= '0'..'9'
```

### 1.3 Literals

```
token INT_LITERAL      ::= DIGIT { DIGIT } [ ('_' DIGIT { DIGIT })* ]
token FLOAT_LITERAL    ::= DIGIT { DIGIT } '.' DIGIT { DIGIT } [ EXPONENT ]
token STRING_LITERAL   ::= '"' { STRING_CHAR } '"'
token INTERP_STRING    ::= 'f"' { INTERP_CHAR } '"'
token BOOL_LITERAL     ::= 'true' | 'false'
token NULL_LITERAL     ::= 'null'

token EXPONENT         ::= ('e' | 'E') [ '+' | '-' ] DIGIT { DIGIT }
token STRING_CHAR      ::= any character except '"' or '\'
                         | '\' ESCAPE_SEQUENCE
token INTERP_CHAR      ::= STRING_CHAR | INTERPOLATION
token INTERPOLATION    ::= '{{' EXPRESSION '}}'
token ESCAPE_SEQUENCE  ::= '"' | '\' | 'n' | 't' | 'r' | '0' | 'u' HEX HEX HEX HEX
token HEX              ::= DIGIT | 'a'..'f' | 'A'..'F'
```

### 1.4 Operators and Punctuation

```
token OP_ASSIGN        ::= '='
token OP_ARROW         ::= '->'
token OP_FATARROW      ::= '=>'
token OP_COLON         ::= ':'
token OP_SEMICOLON     ::= ';'
token OP_COMMA         ::= ','
token OP_DOT           ::= '.'
token OP_LPAREN        ::= '('
token OP_RPAREN        ::= ')'
token OP_LBRACKET      ::= '['
token OP_RBRACKET      ::= ']'
token OP_LBRACE        ::= '{'
token OP_RBRACE        ::= '}'
token OP_DIAMOND       ::= '<>'
token OP_TILDE_SIM     ::= '<~>'
token OP_PIPE          ::= '|'
token OP_QUESTION      ::= '?'
token OP_DOUBLECOLON   ::= '::'
token OP_BACKSLASH     ::= '\\'
```

---

## 2. Compilation Units

```
Module         ::= { UseDeclaration | CapabilityDeclaration | TopLevelItem }
TopLevelItem   ::= StructDeclaration
                 | TypeDeclaration
                 | EffectDeclaration
                 | PromptDeclaration
                 | FunctionDeclaration
                 | ConstDeclaration
                 | TraitDeclaration
```

---

## 3. Imports and Capabilities

```
UseDeclaration         ::= 'import' ModulePath [ CapabilityClause ] NEWLINE
ModulePath             ::= IDENTIFIER { OP_DOT IDENTIFIER }
CapabilityClause       ::= 'requires' CapabilitySet
CapabilitySet          ::= '{' CapabilityName { OP_COMMA CapabilityName } '}'
CapabilityName         ::= IDENTIFIER
```

---

## 4. Type Declarations

### 4.1 Structs

```
StructDeclaration      ::= 'struct' StructName StructBody
StructName             ::= IDENTIFIER
StructBody             ::= INDENT { StructField } DEDENT
StructField            ::= IDENTIFIER OP_COLON TypeAnnotation [ DefaultValue ] NEWLINE
DefaultValue           ::= OP_ASSIGN Expression
```

### 4.2 Type Aliases and Unions

```
TypeDeclaration        ::= 'type' IDENTIFIER OP_ASSIGN TypeExpr NEWLINE
TypeExpr               ::= UnionType | IntersectionType | PrimaryType

UnionType              ::= PrimaryType { OP_PIPE PrimaryType }
IntersectionType       ::= PrimaryType { '&' PrimaryType }
```

### 4.3 Generic Parameters

```
GenericParams          ::= OP_LBRACKET GenericParam { OP_COMMA GenericParam } OP_RBRACKET
GenericParam           ::= IDENTIFIER [ OP_COLON TypeBound ]
TypeBound              ::= TypeExpr
```

---

## 5. Effects

```
EffectDeclaration      ::= 'effect' IDENTIFIER EffectBody
EffectBody             ::= INDENT { EffectCase } DEDENT
EffectCase             ::= 'func' IDENTIFIER '(' ParameterList? ')' [ OP_ARROW TypeAnnotation ] NEWLINE
```

---

## 6. Prompts

```
PromptDeclaration      ::= 'prompt' IDENTIFIER '(' ParameterList? ')' OP_ARROW TypeAnnotation PromptBody
PromptBody             ::= INDENT PromptConfig PromptTemplate DEDENT
PromptConfig           ::= [ 'model' OP_COLON STRING_LITERAL NEWLINE ]
                           [ 'config' OP_COLON JsonLiteral NEWLINE ]
PromptTemplate         ::= MULTILINE_STRING_LITERAL
```

---

## 7. Functions

```
FunctionDeclaration    ::= 'func' IDENTIFIER '(' ParameterList? ')' [ OP_ARROW TypeAnnotation ] FunctionBody
ParameterList          ::= Parameter { OP_COMMA Parameter }
Parameter              ::= IDENTIFIER OP_COLON TypeAnnotation [ OP_ASSIGN Expression ]
TypeAnnotation         ::= TypeExpr

FunctionBody           ::= Block
Block                  ::= INDENT { Statement } DEDENT
Statement              ::= LetStatement
                         | ReturnStatement
                         | ExpressionStatement
                         | MatchStatement
                         | IfStatement
                         | WhileStatement
                         | PerformStatement
                         | EffectHandler
                         | CapabilityGrant
                         | NEWLINE
```

---

## 8. Statements

### 8.1 Variable Binding

```
LetStatement           ::= 'let' Pattern OP_ASSIGN Expression NEWLINE
Pattern                ::= IDENTIFIER
                         | '_' 
                         | StructPattern
                         | TuplePattern

StructPattern          ::= IDENTIFIER '{' PatternField { OP_COMMA PatternField } '}'
PatternField           ::= IDENTIFIER [ OP_COLON Pattern ]
TuplePattern           ::= '(' Pattern { OP_COMMA Pattern } ')'
```

### 8.2 Return

```
ReturnStatement        ::= 'return' Expression NEWLINE
```

### 8.3 Expression Statement

```
ExpressionStatement    ::= Expression NEWLINE
```

### 8.4 Match

```
MatchStatement         ::= 'match' Expression MatchBody
MatchBody              ::= INDENT { MatchArm } DEDENT
MatchArm               ::= Pattern OP_FATARROW Block
```

### 8.5 Conditional

```
IfStatement            ::= 'if' Expression Block [ 'else' (Block | IfStatement) ]
```

### 8.6 Loop

```
WhileStatement         ::= 'while' Expression Block
```

### 8.7 Perform

```
PerformStatement       ::= 'perform' Expression NEWLINE
```

### 8.8 Effect Handler

```
EffectHandler          ::= 'handle' Expression 'with' HandlerBody
HandlerBody            ::= INDENT { HandlerCase } DEDENT
HandlerCase            ::= 'case' IDENTIFIER '(' HandlerParams ')' OP_FATARROW Block
HandlerParams          ::= IDENTIFIER { OP_COMMA IDENTIFIER }
```

### 8.9 Capability Grant

```
CapabilityGrant        ::= 'with' CapabilityBindings Block
CapabilityBindings     ::= '{' CapabilityBinding { OP_COMMA CapabilityBinding } '}'
CapabilityBinding      ::= CapabilityName OP_ASSIGN Expression
```

---

## 9. Expressions

```
Expression             ::= Assignment
Assignment             ::= DecisionExpression
                         | UnaryExpression OP_ASSIGN Expression

DecisionExpression     ::= SelectionExpression
SelectionExpression    ::= LogicalOrExpression [ OP_DIAMOND DecisionBlock ]

DecisionBlock          ::= OP_LBRACE { DecisionCase } OP_RBRACE
DecisionCase           ::= 'case' DecisionPattern OP_ARROW Expression NEWLINE
                         | 'fallback' OP_ARROW Expression NEWLINE
DecisionPattern        ::= STRING_LITERAL | IDENTIFIER | '_'

LogicalOrExpression    ::= LogicalAndExpression { 'or' LogicalAndExpression }
LogicalAndExpression   ::= EqualityExpression { 'and' EqualityExpression }
EqualityExpression     ::= RelationalExpression { ( '==' | '!=' ) RelationalExpression }
RelationalExpression   ::= AdditiveExpression { ( '<' | '>' | '<=' | '>=' | OP_TILDE_SIM ) AdditiveExpression }
AdditiveExpression     ::= MultiplicativeExpression { ( '+' | '-' ) MultiplicativeExpression }
MultiplicativeExpression ::= UnaryExpression { ( '*' | '/' | '%' ) UnaryExpression }
UnaryExpression        ::= PrimaryExpression
                         | ( '-' | 'not' | OP_BACKSLASH ) UnaryExpression
PrimaryExpression      ::= Literal
                         | IDENTIFIER
                         | CallExpression
                         | MemberExpression
                         | IndexExpression
                         | LambdaExpression
                         | '(' Expression ')'
                         | CastExpression
                         | PromptInvocation
```

### 9.1 Calls and Access

```
CallExpression         ::= PrimaryExpression '(' ArgumentList? ')'
ArgumentList           ::= Argument { OP_COMMA Argument }
Argument               ::= Expression | IDENTIFIER OP_ASSIGN Expression

MemberExpression       ::= PrimaryExpression OP_DOT IDENTIFIER
IndexExpression        ::= PrimaryExpression OP_LBRACKET Expression OP_RBRACKET
```

### 9.2 Lambda

```
LambdaExpression       ::= 'func' '(' ParameterList? ')' OP_ARROW Expression
```

### 9.3 Cast

```
CastExpression         ::= PrimaryExpression 'as' TypeAnnotation
```

### 9.4 Prompt Invocation

```
PromptInvocation       ::= IDENTIFIER '!' '(' ArgumentList? ')'
```

---

## 10. Literals

```
Literal                ::= INT_LITERAL
                         | FLOAT_LITERAL
                         | STRING_LITERAL
                         | INTERP_STRING
                         | BOOL_LITERAL
                         | NULL_LITERAL
                         | ArrayLiteral
                         | DictLiteral

ArrayLiteral           ::= '[' [ Expression { OP_COMMA Expression } ] ']'
DictLiteral            ::= '{' [ DictEntry { OP_COMMA DictEntry } ] '}'
DictEntry              ::= Expression OP_COLON Expression
```

---

## 11. Layout & Braces

The parser must recognize two structural forms:

1. **Layout blocks**: indicated by INDENT/DEDENT pairs.
2. **Explicit braces**: permitted for inline scopes (e.g., decision blocks, inline `if` branches) and take precedence over layout.

The lexer emits INDENT/DEDENT tokens when a NEWLINE is followed by increased or decreased indentation, respectively, except when inside parentheses/brackets/braces.

---

## 12. Error Handling Notes

- The grammar favors LL(1) parsing with limited lookahead for `<>` vs. generics due to generics using square brackets.
- Error productions should prefer resynchronization at NEWLINE or closing braces.
- Decision blocks require braces even inside layout blocks for clarity.

---

## 13. Future Extensions

- `trait` and `impl` details to be specified in subsequent revisions.
- Pattern matching on semantic refinements and effect annotations are under design review.
- Inline capability annotations on functions (e.g., `func foo() requires { Network }`) are currently experimental.

---

*This grammar scaffold will evolve through the RFC process. Implementers should track version identifiers in this document and subscribe to design decision updates.*