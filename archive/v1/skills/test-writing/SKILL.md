---
name: test-writing
description: "TEST WRITING SKILL — Write correctly structured JUnit 5 tests that match this project's conventions. USE FOR: adding tests for a new backlog item; flagging missing test coverage; writing tests for engine classes, domain logic, or persistence. Covers class placement, naming conventions, setup patterns, assertion style, and what not to test. DO NOT USE FOR: running tests (use build-verify skill); diagnosing test failures (read the Surefire report directly)."
---

# Test Writing

Conventions for writing correctly structured JUnit 5 tests. Follow these exactly.

---

## Test Framework

- JUnit 5 (`junit-jupiter`)
- No mocking framework — use real domain objects only
- No `AssertJ`, no `Hamcrest` — use `org.junit.jupiter.api.Assertions.*` exclusively

---

## File Placement

| What is under test | Test package | Example |
|---|---|---|
| Engine class in `com.{project}.engine` | `com.{project}.engine` | `EraTransitionTest`, `NeedAdvancementTest` |
| Domain or root class | `com.{project}` | `DecayEngineTest`, `SettlementTest` |
| UI class | Do not test UI classes | — |

File path mirrors the package:
```
src/test/java/com/{project}/engine/EraTransitionTest.java
src/test/java/com/{project}/DecayEngineTest.java
```

---

## Class Structure

```java
package com.{project}.engine;  // match the package of the class under test

import ...;                    // import only what is used

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * {Reference}: {one-line description of what this class tests}.
 * <p>
 * {Optional: key invariants or thresholds being tested, as a short paragraph.}
 */
class {ClassName}Test {        // package-private, NOT public
    // ...
}
```

**Rules:**
- Class is package-private (no `public` modifier)
- One Javadoc comment on the class describing what it tests
- No `@BeforeEach` unless the same setup is shared across 4+ test methods — prefer private helper methods instead

---

## Private Helper Methods

Use private factory/builder methods rather than `@BeforeEach` when setup varies per test:

```java
private World buildWorld() {
    World w = new World();
    // ... minimal setup for this test scenario
    return w;
}
```

---

## Test Method Naming

Pattern: `{methodUnderTest}_{scenario}` or `{methodUnderTest}_{expectedBehavior}`

```java
void advanceNeeds_worsensHungerThirstFatigue()
void advanceNeeds_clampsAtWorstLevels()
void prehistoricToTribal_requiresScoreAndSettlement()
void conceptDecay_floorsAtZero()
```

All test method names must unambiguously state what is being verified. No generic names like `testHunger()` or `test1()`.

---

## Assertion Style

```java
// Preferred: assertEquals with a descriptive failure message
assertEquals(expected, actual, "Descriptive failure message");

assertEquals(0f, concept.getProficiency(), 0.0001f,
        "Proficiency should floor at 0");  // use delta for float comparisons

// Boolean assertions
assertTrue(condition, "Descriptive failure message");
assertFalse(condition, "Descriptive failure message");
```

**Rules:**
- Always include a failure message string on assertions
