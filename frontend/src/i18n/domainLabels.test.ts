import { describe, expect, it } from "vitest";
import ts from "typescript";
import { domainLabel, domainLabels } from "./domainLabels";

function enumValues(source: string): string[] {
  const file = ts.createSourceFile("enum.ts", source, ts.ScriptTarget.Latest, true);
  const values: string[] = [];
  function visit(node: ts.Node): void {
    if (ts.isVariableDeclaration(node) && node.initializer) {
      const initializer = ts.isAsExpression(node.initializer)
        ? node.initializer.expression
        : node.initializer;
      if (ts.isObjectLiteralExpression(initializer))
        for (const property of initializer.properties) {
          if (ts.isPropertyAssignment(property) && ts.isStringLiteral(property.initializer))
            values.push(property.initializer.text);
        }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  return values;
}
function missingLabels(values: readonly string[]): string[] {
  return values.filter((value) => !domainLabels[value]);
}

describe("Orval glossary exhaustiveness", () => {
  const enums = import.meta.glob<string>("../api/generated/models/*Enum.ts", {
    query: "?raw",
    import: "default",
    eager: true,
  });
  it("checks the complete generated enum inventory", () =>
    expect(Object.keys(enums).length).toBeGreaterThan(70));
  for (const [name, source] of Object.entries(enums))
    it(`translates ${name}`, () => {
      expect(missingLabels(enumValues(source))).toEqual([]);
    });
  it("rejects a new API enum until it has an explicit Spanish label", () => {
    const extended =
      'export const State = { READY: "READY", NEW_UNLABELLED_ENUM: "NEW_UNLABELLED_ENUM" } as const;';
    expect(missingLabels(enumValues(extended))).toEqual(["NEW_UNLABELLED_ENUM"]);
    expect(domainLabel("NEW_UNLABELLED_ENUM")).toBe("Sin traducción disponible");
  });
});
