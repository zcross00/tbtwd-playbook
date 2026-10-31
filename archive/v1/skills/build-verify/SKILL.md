---
name: build-verify
description: "BUILD VERIFY SKILL — Compile the project and run all tests before committing. USE FOR: pre-commit gate; verifying a fix did not break existing tests; confirming a new test class passes. Provides exact Maven commands, how to read Surefire output, and the pass/fail gate definition. DO NOT USE FOR: writing new tests (use test-writing skill); diagnosing application runtime errors (read source directly)."
---

# Build Verify

Run these commands in the project root (wherever the `pom.xml` lives) before committing.

---

## Gate Rule

**Do not commit if any test fails or the project does not compile.** No exceptions. Fix the failure first.

---

## Step 1 — Compile

```bash
mvn compile
```

Expected: `BUILD SUCCESS`. Any `ERROR` line means a compilation failure — do not proceed to tests until resolved.

```bash
# To see full compiler output without truncation:
mvn compile -e
```

---

## Step 2 — Run All Tests

```bash
mvn test
```

Expected output ends with:
```
Tests run: N, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

If any test fails, Maven prints a summary like:
```
Tests run: 12, Failures: 1, Errors: 0, Skipped: 0
```

---

## Reading Surefire Reports

When a test fails, get the full detail from the Surefire report for that class:

```
target/surefire-reports/{fully.qualified.ClassName}.txt
```

The `.txt` file contains the full failure message, stack trace, and expected vs. actual values.

---

## Running a Single Test Class

To isolate a failing class without running all tests:

```bash
mvn test -Dtest=ClassName
# Example:
mvn test -Dtest=NeedAdvancementTest
mvn test -Dtest=EraTransitionTest
```

To run a single test method:

```bash
mvn test -Dtest=ClassName#methodName
# Example:
mvn test -Dtest=NeedAdvancementTest#advanceNeeds_worsensHungerThirstFatigue
```

---

## Common Failure Causes

| Symptom | Likely cause |
|---|---|
| `package X does not exist` | Import missing or class moved/renamed |
| `cannot find symbol` | Method/field renamed; check the domain class |
