# Style Guide — Documentation

Rules for writing and formatting all markdown documentation in any project. Consistent style makes documents faster to read and easier for both humans and AI agents to parse.

---

## 1. Voice and Tone

**Direct and specific.** Write as if explaining to a capable person who has never seen this project before.

- Use active voice: "The engine resolves actions" not "Actions are resolved by the engine."
- Use the present tense for descriptions of how things work: "The save manager serializes the world state." Past tense is for history ("This was originally implemented as...").
- Do not hedge unnecessarily. "The player can queue up to 3 actions" not "In most cases, the player can typically queue up to approximately 3 actions."
- Avoid filler phrases: "It should be noted that...", "In order to...", "The purpose of this is to..." — start with the substance.

---

## 2. Heading Hierarchy

Use heading levels consistently and don't skip levels.

| Level | Usage |
|-------|-------|
| `#` (H1) | Document title only — one per document |
| `##` (H2) | Major sections (numbered or named) |
| `###` (H3) | Subsections within a major section |
| `####` (H4) | Use sparingly — only when H3 is genuinely insufficient |

Don't use bold text as a pseudo-heading. If something warrants a heading, give it one.

---

## 3. Metadata Block

All primary documents (design docs, roadmaps, findings logs) start with a metadata block immediately after the H1 title:

```markdown
# Document Title — Subtitle

**Field:** Value  
**Field:** Value  
**Field:** Value
```

Use a double-space line break (or `  ` at the end of each line) to keep fields on separate lines within the same paragraph block. Always include at minimum: version/date, and status or branch.

---

## 4. Tables

Use tables for:
- Structured data with a clear relationship between columns (task lists, status trackers, option comparisons).
- Any list of three or more items where two or more attributes per item are being conveyed.

Don't use tables for:
- Simple lists where there's only one attribute per item — use a bullet list.
- Prose that happens to have two columns — that's usually just a description that should be written as paragraphs.

**Column headers** should be brief and title-cased.  
**Cell content** should use code formatting (`` `backticks` ``) for file paths, class names, variable names, and commands.  
**Status columns** may use emoji (✅, 🔄, ⬜) for at-a-glance scanning, but always pair with text for accessibility.

---

## 5. Code and Technical References

- File paths: always use backtick formatting — `src/main/java/`
- Class and method names: backtick formatting — `ResolutionEngine`, `resolveDay()`
- Commands: fenced code blocks with the language specified

```bash
mvn clean compile
```

```java
public int computeEffortBudget() { ... }
```

- Constants and enum values use backtick formatting inline: `CRITICAL_SUCCESS`, `WELL_RESTED`

---

## 6. Lists

**Bullet lists** (`-`) for unordered items. **Numbered lists** (`1.`) only when order matters (steps in a process, priority rankings).

Keep list items parallel in structure: if the first item is a verb phrase, all items should be verb phrases. If the first item is a noun, all items should be nouns.

Bad:
- The player queues actions
- Effort budget matters
- Overnight resolution

Good:
- Player queues actions
- Engine resolves overnight
- Outcomes surface next morning

Avoid nesting lists more than two levels deep. If you need three levels, the content probably wants to be a section with its own heading.

---

## 7. Emphasis

- **Bold** for terms being defined, key concepts being introduced, or critical warnings.
- *Italic* for titles, foreign terms, and light emphasis. Use sparingly.
- Don't bold random phrases for decoration. Bold should mean "this is important; look at this."
- Don't use ALL CAPS for emphasis in prose — it reads as shouting. Use bold instead.

---

## 8. Design Document — Section Conventions

Design documents follow the structure in [`templates/DESIGN_DOCUMENT.md`](../templates/DESIGN_DOCUMENT.md). Within that structure:

- **Section 2 (Pillars):** Each pillar is a single bold title followed by a dash and one clarifying sentence. Don't write paragraphs. Pillars are principles, not essays.
- **Section 5 (Mechanics):** Each mechanic has its own `###` heading. Describe what it is, how it works, and why it exists. End with a *Design note:* italic callout for unresolved questions.
- **Section 9 (Out of Scope):** Use the table format. Be honest. "Not yet designed" is a legitimate note.

---

## 9. Roadmap Conventions

Follow the structure in [`templates/ROADMAP.md`](../templates/ROADMAP.md):

- Milestone headers: `## Milestone N — Name` followed by a completion badge when done.
- Task descriptions inside tables: **bold the task name**, then one sentence of detail after it.
- Every milestone ends with a `**Done when:**` line — a testable, yes/no condition.
- The "Quick Reference" table at the bottom is maintained throughout the project alongside the milestone sections.

---

## 10. Prototype Findings Conventions

Follow the structure in [`templates/PROTOTYPE_FINDINGS.md`](../templates/PROTOTYPE_FINDINGS.md):

- Finding headers: `### [Category] {{Title}}` — the category is always one of: Confirm, Rework, Abandon, Discuss.
- Finding body: What was assumed → what was observed → what it means. In that order.
- Be specific about numbers, thresholds, and mechanics when they are relevant to the observation.
- The Resolution Tracker at the bottom mirrors every finding entry. Keep it in sync.

---

## 11. What Not to Do

| Avoid | Instead |
|-------|---------|
| "As mentioned above..." | Just say it again clearly, or link to the section |
| "TODO: fill this in" | Leave a `{{placeholder}}` with clear instruction |
| Vague section titles ("Notes", "Misc", "Other") | Name the content explicitly |
| Restating the code line by line in design docs | The design doc holds the why (decisions, constraints, workarounds) and names the code it explains; the code itself holds no comments ([standards §4](../standards/general.md#4-no-comments)) |
| Writing one giant paragraph for a complex mechanic | Break into sub-headings or structured list |
| Trailing "etc." | Name the things — or admit you don't know yet |
