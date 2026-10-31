---
name: standards-check-java
description: "STANDARDS CHECK JAVA SKILL — Apply standards/general.md and standards/java.md systematically to a Java file or diff. USE FOR: pre-commit standards compliance check; reviewing a file for standards adherence before or after a change. Produces a categorized violation list with the specific rule cited for each. DO NOT USE FOR: general code review (use planner-review skill for implementation review)."
---

# Standards Check — Java

Apply this checklist to a Java file or diff. For each category, note violations with the file path, line reference, and the specific rule being violated. A clean file produces an empty list.

---

## How to Run

Specify what to check:
- **A single file:** Read the file in full, then work through all categories.
- **A diff:** Apply to all new and modified lines. Do not flag pre-existing violations in unchanged lines.
- **A directory sweep:** Work file by file through `src/main/java/`. Skip test files for general standards (test-specific rules are noted below).

---

## Category 1 — Naming (general.md §1)

- [ ] Names answer "what is this?" without needing context. Abbreviations used only if universally known (`id`, `url`, `json` — ok; `cnt`, `tmp`, `val` — not ok).
- [ ] No class or interface named `Manager`, `Handler`, `Util`, or `Helper` without a justification comment.
- [ ] Boolean fields and methods read as questions: `isComplete`, `hasChildren`, `canQueue`.
- [ ] Type not encoded in the name: `characterList` → `characters`; `stringName` → `name`.

**Java-specific (java.md §2):**
- [ ] Classes and interfaces: `PascalCase`
- [ ] Enum types: `PascalCase`; enum constants: `UPPER_SNAKE_CASE`
- [ ] Methods: `camelCase`, verb-first (`resolveDay()`, not `dayResolve()`)
- [ ] Constants (`static final`): `UPPER_SNAKE_CASE`
- [ ] Test methods: sentence form (`playerCannotQueueSameActionTwice()`, not `testQueue()`)

---

## Category 2 — Size and Focus (general.md §2)

- [ ] No method exceeds ~30 lines without a clear reason. If too long: flag and note what could be extracted.
- [ ] No class references more than ~5 other types as a routine dependency (imports and field types). Flag as a potential single-responsibility violation.
- [ ] No method name requires "and" to describe what it does (`validateAndSave` → split into two methods).

---

## Category 3 — Magic Values (general.md §3)

- [ ] No unexplained numeric literals in logic: `if (x < 0.3)` → must be `if (x < HOSTILITY_THRESHOLD)`.
- [ ] No unexplained string literals used in comparisons or dispatch: `if (type.equals("raider"))` → must use an enum.
- [ ] Constants are at class scope (or in a dedicated constants class/enum) and named for *why* the value exists, not what it is.

---

## Category 4 — Comments (general.md §4)

- [ ] No comment that merely restates the code. Delete it.
- [ ] No docstrings (`/** */`) on methods that are not part of a public API surface consumed without reading source.
- [ ] Comments present where the logic is genuinely non-obvious (decisions, constraints, workarounds).

---

## Category 5 — Boundary Validation (general.md §5)

- [ ] No defensive null or range checks inside internal methods called only from internal code.
- [ ] `if (x == null)` deep inside a domain method indicates the real problem is the caller — flag the call site instead.
- [ ] External boundaries (user input, file reads, deserialized values) are validated before use.

---

## Category 6 — Immutability (general.md §6)

- [ ] Value/snapshot objects are immutable where feasible. No setters unless mutation is the explicit purpose.
- [ ] Collections returned from accessors are wrapped in `Collections.unmodifiableList()` (or equivalent) unless the caller genuinely owns the mutation.

---

## Category 7 — Error Handling (general.md §7)

- [ ] Unexpected states throw — do not silently return null or default values.
- [ ] No exception swallowed at a site where it cannot be meaningfully handled.
- [ ] No exceptions used for normal control flow (not-found, not-applicable → model in return type).

---

## Category 8 — Java Records (java.md §3)

- [ ] Value/data objects with no mutable state and no complex behavior are records, not classes.
- [ ] Records not used where: mutable state is required, complex Jackson deserialization is needed, or inheritance is required.

---

## Category 9 — Optional (java.md §4)

- [ ] `Optional<T>` used only as a return type — never as a method parameter.
- [ ] `Optional` never used as a field type.
- [ ] `.get()` never called without a prior `isPresent()` check — use `.orElse()`, `.orElseThrow()`, `.ifPresent()`, or `.map()`.

---

## Category 10 — Collections (java.md §5)

- [ ] `Collections.unmodifiableList()` (or `List.copyOf()`) returned from accessors that should not expose mutable internals.
- [ ] `List.of()`, `Map.of()`, `Set.of()` used for fixed-content collections.

---

## Category 11 — Java 21 Language Features (java.md §3)

- [ ] `instanceof` casts replaced with pattern matching where Java 16+ pattern matching applies.
- [ ] Value-producing switches use switch expressions (not switch statements).
- [ ] `var` used only when the inferred type is obvious from the right-hand side; not in method signatures.

---

## Category 12 — Serialization Safety

- [ ] All computed or transient methods annotated with `@JsonIgnore`.
- [ ] All new fields on serialized classes are intentionally included in serialization (not accidentally serialized).
