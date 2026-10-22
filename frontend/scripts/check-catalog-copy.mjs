import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const root = fileURLToPath(new URL("../../", import.meta.url));
const forbidden =
  /\b(?:autoridad(?:es)?|sellad[oa]s?|fuentes?|procedencias?|sin datos?)\b|Referencia\s*·\s*no cotizable/iu;

/** Parse actual literals/JSX, including expressions and template spans. Comments,
 * identifiers and contract property names are not interface copy. */
export function catalogCopyViolations(filename, source, translations = false) {
  const ast = ts.createSourceFile(
    filename,
    source,
    ts.ScriptTarget.Latest,
    true,
    filename.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const findings = [];
  function record(node, text) {
    if (forbidden.test(text))
      findings.push({
        line: ast.getLineAndCharacterOfPosition(node.getStart(ast)).line + 1,
        text: text.trim().replace(/\s+/g, " "),
      });
  }
  function staticText(node) {
    if (ts.isStringLiteralLike(node)) return node.text;
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.PlusToken) {
      const left = staticText(node.left);
      const right = staticText(node.right);
      if (left !== null && right !== null) return left + right;
    }
    return null;
  }
  function visit(node) {
    if (ts.isPropertyAssignment(node) || ts.isMethodDeclaration(node)) {
      if (ts.isPropertyAssignment(node)) visit(node.initializer);
      else if (node.body) visit(node.body);
      return;
    }
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) return;
    const staticValue = staticText(node);
    if (staticValue !== null) {
      record(node, staticValue);
      return;
    }
    if (ts.isTemplateExpression(node)) {
      record(
        node,
        [node.head.text, ...node.templateSpans.map((span) => span.literal.text)].join(" "),
      );
      for (const span of node.templateSpans) visit(span.expression);
      return;
    }
    if (ts.isJsxText(node)) record(node, node.text);
    ts.forEachChild(node, visit);
  }
  if (translations) {
    function keys(node) {
      if (
        ts.isPropertyAssignment(node) &&
        ts.isStringLiteral(node.name) &&
        /^(?:catalog|glass)\./.test(node.name.text)
      )
        visit(node.initializer);
      else ts.forEachChild(node, keys);
    }
    keys(ast);
  } else visit(ast);
  return findings;
}

export function detectorTests() {
  const samples = [
    "<p>Sin dato</p>",
    '<p>{"Autoridad de proceso"}</p>',
    '<input placeholder="Fuente del fabricante" />',
    'const label = missing ? "Completar" : "Procedencia";',
    "const message = `Revisa la fuente de ${name}`;",
    "const message = `${count} fuentes por revisar`;",
    'const messages = { bad: "Referencia · no cotizable" };',
    'const title = "Fuen" + "te";',
    "<p>Revisión sellada</p>",
  ];
  for (const source of samples)
    assert.ok(catalogCopyViolations("sample.tsx", source).length, source);
  assert.equal(
    catalogCopyViolations(
      "sample.tsx",
      '// Sin dato\nconst autoridad = { "fuente": "Del manual" }; const x = <p>{autoridad.fuente}</p>;',
    ).length,
    0,
  );
  assert.equal(
    catalogCopyViolations(
      "es-CL.ts",
      'const copy = { "pricing.source": "Fuente", "catalog.origin": "Del manual", "glass.value": "Completar" };',
      true,
    ).length,
    0,
  );
  assert.equal(
    catalogCopyViolations(
      "es-CL.ts",
      'const copy = { "catalog.origin": "Fuente", "glass.empty": "Sin dato" };',
      true,
    ).length,
    2,
  );
}

function files(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const name = path.join(directory, entry.name);
    return entry.isDirectory()
      ? files(name)
      : /\.tsx?$/.test(name) && !/\.test\./.test(name)
        ? [name]
        : [];
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  detectorTests();
  const candidates = [
    ...files(path.join(root, "frontend/src/features/catalogs")),
    // Shared editors and labels rendered inside catalog surfaces.
    ...[
      "frontend/src/features/projects/ExtraDefinitionEditor.tsx",
      "frontend/src/features/projects/extraModel.ts",
      "frontend/src/i18n/domainLabels.ts",
    ].map((name) => path.join(root, name)),
    path.join(root, "frontend/src/i18n/es-CL.ts"),
  ];
  let count = 0;
  for (const filename of candidates) {
    const findings = catalogCopyViolations(
      filename,
      readFileSync(filename, "utf8"),
      filename.endsWith("es-CL.ts"),
    );
    for (const finding of findings) {
      count++;
      console.error(
        `${path.relative(root, filename)}:${finding.line}: lenguaje de catálogo: ${finding.text}`,
      );
    }
  }
  if (count) process.exitCode = 1;
  else console.info("Catalog interface copy and detector tests PASS");
}
