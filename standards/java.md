# Coding Standards — Java 21

Java-specific rules and idioms. Apply these on top of [`general.md`](general.md).

**Toolchain:** Java 21 LTS · Maven · JUnit 5 · AssertJ

---

## 1. Project Structure

Follow the Maven standard directory layout:

```
src/
  main/java/com/{org}/{project}/     # Source root
    domain/                          # Pure domain model (no framework deps)
      character/
      world/
      journal/
    engine/                          # Business logic / simulation engines
    persistence/                     # I/O, serialization, save/load
    ui/                              # UI layer (screens, widgets, panels)
      screens/
      widgets/
    world/                           # Factories, world generation
  main/resources/                    # Assets, config, data files
  test/java/com/{org}/{project}/     # Mirror of main package structure
```

The domain layer must not import from engine, ui, or persistence. Dependency flows inward toward domain, never outward.

---

## 2. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Package | `lowercase`, no underscores | `com.sovereign.domain.character` |
| Class / Interface | `PascalCase` | `ResolutionEngine`, `CharacterType` |
| Enum type | `PascalCase` | `OutcomeType`, `FatigueLevel` |
| Enum constant | `UPPER_SNAKE_CASE` | `CRITICAL_SUCCESS`, `WELL_RESTED` |
| Method | `camelCase`, verb-first | `resolveDay()`, `computeEffortBudget()` |
| Variable / Field | `camelCase` | `effortBudget`, `daysRequired` |
| Constant (`static final`) | `UPPER_SNAKE_CASE` | `MAX_SHELTER_BONUS`, `POPULATION_FLOOR` |
| Boolean field | Question form | `isGifted`, `hasSettlement` |
| Test method | Sentence form | `playerCannotQueueSameActionTwice()` |

---

## 3. Java 21 Language Features

### Records — use for value/data objects

Use records for domain objects that carry data and have no mutable state or complex behavior. They give `equals`, `hashCode`, `toString`, and immutability for free.

```java
// Good — pure data carrier
public record WorldConfig(
    String playerName,
    boolean magicEnabled,
    boolean deityEnabled,
    int seedPopulation
) {}
```

Do not use records when: the object needs mutable state, requires Jackson parameterized deserialization in complex ways, or has inheritance requirements.

### Sealed classes — use for closed type hierarchies

When a type has a fixed, small set of subtypes that you own and control:

```java
public sealed interface ActionResult
    permits SuccessResult, FailureResult, PartialResult {}
```

This makes exhaustive `switch` expressions compiler-checked rather than runtime-checked.

### Pattern matching — prefer over cast chains

```java
// Old
if (obj instanceof String) {
    String s = (String) obj;
    ...
}

// Good (Java 16+)
if (obj instanceof String s) {
    ...
}

// Better — switch expression (Java 21)
String label = switch (level) {
    case WELL_RESTED -> "Well Rested";
    case RESTED      -> "Rested";
    case TIRED       -> "Tired";
    case EXHAUSTED   -> "Exhausted";
    case COLLAPSED   -> "Collapsed";
};
```

Always prefer switch expressions over switch statements for value-producing switches. The compiler enforces exhaustiveness.

### Text blocks — use for multiline strings

```java
String query = """
    SELECT * FROM characters
    WHERE area_id = ?
    AND is_alive = true
    """;
```

### `var` — use when type is obvious from context

```java
// Good — type is obvious from the right-hand side
var characters = new ArrayList<Character>();
var outcome = resolveAction(action, actor);

// Bad — type is not obvious without knowing the return type
var result = engine.process(state);
```

Do not use `var` in method signatures or when the inferred type is a supertype and the specific type matters.

---

## 4. Optional

- Use `Optional<T>` as a **return type** when a method might not produce a value.
- **Never** use `Optional` as a method parameter — use overloads or nullable parameters with documented contract instead.
- **Never** use `Optional` as a field type — it's not serializable and adds allocation overhead in hot paths.
- Don't call `.get()` without checking — use `.orElse()`, `.orElseThrow()`, `.ifPresent()`, or `.map()`.

```java
// Good
public Optional<Character> findCharacterById(String id) {
    return characters.stream()
        .filter(c -> c.getId().equals(id))
        .findFirst();
}

// Bad — Optional parameter
public void process(Optional<Character> maybeChar) { ... }
```

---

## 5. Collections

- Return unmodifiable views when the caller should not mutate internal collections:
  ```java
  public List<Character> getCharacters() {
      return Collections.unmodifiableList(characters);
  }
  ```
- Prefer `List.of()`, `Map.of()`, `Set.of()` for fixed-content collections.
- Initialize `ArrayList` and `HashMap` with an estimated capacity if the size is known in advance to avoid reallocations.
- Don't expose raw `List` or `Map` fields as `public`. Always provide controlled accessors.

---

## 6. Streams

- Use streams for **transforming or filtering** collections. Prefer traditional loops for **mutations** or side effects.
- Avoid multi-line lambda bodies in stream chains — extract a method if the logic is complex.
- Prefer `stream().filter().findFirst()` over iterating manually for single lookups.

```java
// Good
float totalFood = characters.stream()
    .filter(Character::isAlive)
    .mapToFloat(c -> c.getInventory().getFood())
    .sum();

// Bad — stream used for side effects
characters.stream().forEach(c -> {
    c.setAlive(false);
    log.add(c.getName() + " died");
});
```

---

## 7. Jackson / Serialization

- Annotate **computed / derived methods** with `@JsonIgnore` to prevent them from being serialized:
  ```java
  @JsonIgnore
  public int computeEffortBudget() { ... }
  ```
- Jackson requires a **no-arg constructor** for deserialization. Add one with no comment; why it exists goes in the design doc's serialization section ([general.md §4](general.md#4-no-comments)):
  ```java
  public Character() {}
  ```
- Don't serialize transient UI state or runtime caches. Keep the domain model clean.
- New fields added to existing serialized classes should have sensible defaults at declaration — Jackson will null/zero-initialize missing fields from old saves, so those defaults must be safe.

---

## 8. Enums

- Enums are the right tool for fixed, known sets of values. Prefer them over `String` constants.
- Add fields and methods to enums when values carry data:
  ```java
  public enum FatigueLevel {
      WELL_RESTED(1.2f),
      RESTED(1.0f),
      TIRED(0.85f),
      EXHAUSTED(0.6f),
      COLLAPSED(0.3f);

      public final float effortMultiplier;

      FatigueLevel(float effortMultiplier) {
          this.effortMultiplier = effortMultiplier;
      }
  }
  ```
- Define concept names, action type strings, and other domain identifiers in enums or final constant classes — never as raw string literals scattered through engine code.

---

## 9. Exception Strategy

- Use **unchecked exceptions** (subclasses of `RuntimeException`) for programming errors and invalid internal state.
- Use **checked exceptions** only for genuinely recoverable external failures (file not found on load, corrupted save data).
- Name exceptions after what went wrong, not the layer that threw them: `SaveCorruptedException`, not `PersistenceException`.
- Don't use NullPointerException as a signal — explicit `Objects.requireNonNull()` with a message, or better, design away the nullable path.

---

## 10. Package Organization

Packages map to architectural layers, not feature areas:

| Package | Contains |
|---------|---------|
| `domain.*` | Plain domain objects — no framework imports, no engine logic |
| `engine.*` | Simulation/business logic that operates on domain objects |
| `persistence.*` | Save/load, serialization |
| `ui.*` | Screens, panels, widgets |
| `world.*` | Factories, procedural generation |

Cross-cutting concerns (logging, event listeners) belong in their own package, not slotted into domain or engine.

---

## 11. Test Structure (JUnit 5 + AssertJ)

```java
class ResolutionEngineTest {

    private ResolutionEngine engine;
    private World world;

    @BeforeEach
    void setUp() {
        world = WorldFactory.createTestWorld();
        engine = new ResolutionEngine();
    }

    @Test
    void hungerWorsensWhenCharacterSkipsForageForThreeDays() {
        Character character = world.getPlayer();
        assertThat(character.getHealth().getHunger()).isEqualTo(HungerLevel.SATISFIED);

        for (int i = 0; i < 3; i++) {
            engine.advanceDay(world, List.of());
        }

        assertThat(character.getHealth().getHunger())
            .isEqualTo(HungerLevel.HUNGRY);
    }
}
```

- **Arrange / Act / Assert** structure, with a blank line between the three parts and no comments labelling them. A test too long to read that way is split, or its setup moves into a helper named for what it sets up.
- One test = one observable behavior.
- Test class names: `{ClassName}Test` in the same package as the class under test.
- Use `@BeforeEach` for shared setup; avoid `@BeforeAll` unless the setup is genuinely expensive and stateless.

---

## 12. Maven & Build

- Java version in `pom.xml`:
  ```xml
  <properties>
      <maven.compiler.source>21</maven.compiler.source>
      <maven.compiler.target>21</maven.compiler.target>
      <java.version>21</java.version>
  </properties>
  ```
- Don't commit `target/` — it belongs in `.gitignore`.
- Common lifecycle: `mvn clean compile` to build, `mvn test` to run tests, `mvn package` to produce a runnable jar.
