# Coding Standards — C# / Unity

C#-specific rules and idioms for Unity projects. Apply these on top of [`general.md`](general.md).

**Toolchain:** Unity 6 · C# 12 · NUnit · Unity Test Framework

---

## 1. Project Structure

Follow the Unity standard directory layout:

```
Assets/
  Scripts/
    Core/                           # Managers, singletons, bootstrap
    Data/                           # Pure C# data classes (no MonoBehaviour)
    Domain/                         # Domain enums, constants, config types
    Engine/                         # Simulation logic operating on data
    UI/                             # UI controllers, panels, HUD
    World/                          # Zone loading, terrain, procedural gen
    Player/                         # Player controller, input, camera
    NPC/                            # NPC controllers, AI, pathfinding
  Prefabs/
  Materials/
  Scenes/
  Resources/
  Editor/                           # Editor-only scripts (not in builds)
  Tests/
    EditMode/                       # Pure logic tests (no scene required)
    PlayMode/                       # Tests that need a running scene
```

The Data layer must not reference MonoBehaviours, ScriptableObjects, or UnityEngine types beyond value types (`Vector3`, `Color`, etc.). Dependency flows inward toward Data, never outward.

---

## 2. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Namespace | `PascalCase`, matches folder | `Sovereign.Engine`, `Sovereign.Data` |
| Class / Interface | `PascalCase` | `TimeManager`, `IResolvable` |
| Interface | `I` prefix + `PascalCase` | `IDayResolvable`, `IZoneLoader` |
| Enum type | `PascalCase` | `HungerLevel`, `WeatherType` |
| Enum constant | `PascalCase` | `WellRested`, `CriticalSuccess` |
| Method | `PascalCase`, verb-first | `ResolveDay()`, `ComputeEffort()` |
| Property | `PascalCase` | `CurrentHealth`, `IsAlive` |
| Public field | `PascalCase` | `MaxHealth` (prefer properties) |
| Private field | `camelCase` with no prefix | `currentHealth`, `dayCount` |
| Parameter / local | `camelCase` | `effortBudget`, `zoneId` |
| Constant (`const` / `static readonly`) | `PascalCase` | `MaxShelterBonus`, `PopulationFloor` |
| Boolean property | Question form | `IsGifted`, `HasSettlement`, `CanAct` |
| Serialized private field | `camelCase` | `[SerializeField] float moveSpeed` |

---

## 3. C# Language Features

### Records — use for immutable value carriers

Use `record` or `record struct` for small, immutable data that is never serialized by Unity and has no behavior:

```csharp
// Good — pure data snapshot
public record DayResult(int DayNumber, bool SettlementAdvanced, string Summary);

// Good — value type, no heap allocation
public readonly record struct GridCoord(int X, int Y);
```

Do not use records for types that need Unity serialization (`[Serializable]`), MonoBehaviour state, or mutable data.

### Pattern Matching — prefer over cast chains

```csharp
// Good — switch expression
string label = level switch
{
    HungerLevel.Satisfied => "Satisfied",
    HungerLevel.Hungry => "Hungry",
    HungerLevel.Starving => "Starving",
    _ => "Unknown"
};

// Good — pattern matching
if (component is HealthData health)
{
    health.TakeDamage(amount);
}
```

### Nullable Reference Types — enable and use

Enable nullable reference types in project settings. Annotate intentionally nullable parameters and returns:

```csharp
public Character? FindCharacterById(string id)
{
    return characters.FirstOrDefault(c => c.Id == id);
}

public void AddCharacter(Character character)
{
    characters.Add(character);
}
```

### `var` — use when type is obvious from context

```csharp
// Good — type obvious from right-hand side
var characters = new List<CharacterData>();
var result = ResolveDay(state);

// Bad — type not obvious
var x = engine.Process(state);
```

---

## 4. MonoBehaviour vs. Pure C#

### Data/Logic Split

Separate persistent simulation state from Unity scene representation:

| Layer | Base class | Responsibility | Example |
|-------|-----------|----------------|---------|
| Data | Plain C# class | Holds simulation state; no Unity dependencies | `CharacterData`, `JournalData` |
| Engine | Plain C# class | Operates on data classes; pure logic | `DayResolutionEngine`, `EffortEngine` |
| Controller | `MonoBehaviour` | Bridges data to scene; handles Unity lifecycle | `NpcController`, `PlayerController` |
| Manager | `MonoBehaviour` (singleton) | Scene-level coordination; spawning, loading | `TimeManager`, `ZoneManager` |
| Config | `ScriptableObject` | Designer-tunable parameters; asset-based | `BiomeConfig`, `DifficultyConfig` |

**Rules:**
- Data classes must be `[Serializable]` if they need to survive save/load
- Engine classes take data as parameters — they never reference `MonoBehaviour` or `Transform`
- Controllers read from and write to data classes, then update visuals
- Managers use `[SerializeField]` for inspector-configurable references

### ScriptableObject — use for configuration

```csharp
[CreateAssetMenu(fileName = "NewBiomeConfig", menuName = "Sovereign/Biome Config")]
public class BiomeConfig : ScriptableObject
{
    [SerializeField] string biomeName;
    [SerializeField] float baseTemperature;
    [SerializeField] GameObject[] vegetationPrefabs;

    public string BiomeName => biomeName;
    public float BaseTemperature => baseTemperature;
    public IReadOnlyList<GameObject> VegetationPrefabs => vegetationPrefabs;
}
```

---

## 5. Collections

- Return `IReadOnlyList<T>` or `IReadOnlyCollection<T>` from accessors that should not expose mutable internals.
- Prefer `List<T>` over arrays for dynamic collections. Use arrays for fixed-size data in `[Serializable]` types.
- Initialize collections at declaration to avoid null references:
  ```csharp
  List<CharacterData> characters = new();
  ```
- Don't expose raw `List` fields as `public`. Provide controlled accessors or use `IReadOnlyList<T>`.

---

## 6. LINQ

- Use LINQ for **transforming or filtering** collections. Prefer `foreach` for **mutations** or side effects.
- Avoid multi-statement lambdas in LINQ chains — extract a method if the logic is complex.
- In hot paths (Update, FixedUpdate), prefer `foreach` over LINQ to avoid allocations.

```csharp
// Good — query
float totalFood = characters
    .Where(c => c.IsAlive)
    .Sum(c => c.Inventory.Food);

// Bad — LINQ used for side effects
characters.ForEach(c =>
{
    c.IsAlive = false;
    log.Add($"{c.Name} died");
});
```

---

## 7. Serialization / Save System

- Classes that participate in save/load must be marked `[Serializable]`.
- Use `[SerializeField]` on private fields that need Unity inspector access or JSON serialization.
- Computed properties should not be serialized — use `[NonSerialized]` or `[JsonIgnore]` as appropriate.
- New fields added to existing serialized classes must have sensible defaults at declaration — the deserializer will default-initialize missing fields.
- Transient gameplay state (queued actions, combat logs, visual state) must not be serialized.

```csharp
[Serializable]
public class CharacterData
{
    public string Id;
    public string Name;
    public HealthState Health = new();
    public List<string> KnownConcepts = new();

    [NonSerialized]
    public float CachedEffortBudget;
}
```

---

## 8. Enums

- Enums are the right tool for fixed, known sets of values. Prefer them over string constants.
- Use extension methods to attach behavior to enums rather than switch statements scattered through engine code:

```csharp
public enum FatigueLevel
{
    WellRested,
    Rested,
    Tired,
    Exhausted,
    Collapsed
}

public static class FatigueLevelExtensions
{
    public static float EffortMultiplier(this FatigueLevel level) => level switch
    {
        FatigueLevel.WellRested => 1.2f,
        FatigueLevel.Rested => 1.0f,
        FatigueLevel.Tired => 0.85f,
        FatigueLevel.Exhausted => 0.6f,
        FatigueLevel.Collapsed => 0.3f,
        _ => 1.0f
    };
}
```

- Define concept names, action types, and domain identifiers in enums or `static class` constants — never as raw string literals.

---

## 9. Exception Strategy

- Use exceptions for programming errors and genuinely unexpected states.
- In Unity, prefer `Debug.LogError()` over throwing in MonoBehaviour code — thrown exceptions in Update loops crash the frame silently.
- Use `Debug.Assert()` for invariant checks during development.
- Name exceptions after what went wrong: `SaveCorruptedException`, not `PersistenceException`.

---

## 10. Namespace Organization

Namespaces map to architectural layers, matching the folder structure:

| Namespace | Contains |
|-----------|---------|
| `Sovereign.Data` | Pure data classes — no MonoBehaviour, no engine logic |
| `Sovereign.Engine` | Simulation/business logic operating on data classes |
| `Sovereign.Core` | Managers, singletons, bootstrap, scene lifecycle |
| `Sovereign.UI` | UI controllers, panels, HUD elements |
| `Sovereign.World` | Zone loading, terrain generation, world map |
| `Sovereign.Player` | Player controller, input, camera rig |
| `Sovereign.NPC` | NPC controllers, AI, pathfinding |

Cross-cutting concerns (events, utility extensions) belong in `Sovereign.Common`.

---

## 11. Unity-Specific Patterns

### Singleton Managers

Use a base singleton pattern for scene managers. Do not use `DontDestroyOnLoad` unless the manager genuinely persists across scene transitions:

```csharp
public class TimeManager : MonoBehaviour
{
    public static TimeManager Instance { get; private set; }

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
    }
}
```

### Coroutines vs. Async

- Use coroutines for frame-dependent sequences (animations, timed visual effects).
- Use `async`/`await` (with UniTask or Awaitable) for I/O-bound operations (save/load, asset loading).
- Never use `async void` except for Unity event methods that require it.

### Inspector Configuration

- Use `[Header("Section")]` to group related fields in the inspector.
- Use `[Tooltip("description")]` for non-obvious fields.
- Use `[Range(min, max)]` for numeric fields with known bounds.
- Prefer `[SerializeField] private` over `public` fields.
