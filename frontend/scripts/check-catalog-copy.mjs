import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const root = fileURLToPath(new URL("../../", import.meta.url));
const forbidden =
  /\b(?:autoridad(?:es)?|sellad[oa]s?|fuentes?|procedencias?|sin datos?|posici[oó]n|posiciones|vanos?|encargos?|recibos?)\b|Referencia\s*·\s*no cotizable/iu;

/** Parse product literals/JSX, including expressions and template spans. Comments,
 * identifiers and contract property names are not interface copy. The historical
 * export name stays stable for the catalog gate's consumers. */
export function catalogCopyViolations(filename, source) {
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
    if (
      ts.isJsxAttribute(node) &&
      [
        "id",
        "className",
        "htmlFor",
        "href",
        "data-region",
        "data-testid",
        "aria-controls",
        "aria-labelledby",
        "aria-describedby",
      ].includes(node.name.getText(ast))
    )
      return;
    if (ts.isPropertyAssignment(node) || ts.isMethodDeclaration(node)) {
      // Search metadata retains old workshop synonyms for existing queries.
      // It is not a displayed label; values rendered as text remain checked.
      if (
        ts.isPropertyAssignment(node) &&
        node.name.getText(ast).replace(/["']/g, "") === "keywords"
      )
        return;
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
  visit(ast);
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
    '<p aria-label="Nueva posición">Ventana</p>',
    "<p>Vanos de la obra</p>",
    "<p>Encargo y recibo</p>",
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
      "sample.tsx",
      '<section id="fuente" data-region="autoridad-cnc" aria-labelledby="fuente"><p>Del manual</p></section>',
    ).length,
    0,
  );
  assert.equal(
    catalogCopyViolations(
      "sample.tsx",
      '<section data-region="autoridad-cnc" aria-label="Autoridad"><p>Fuente</p></section>',
    ).length,
    2,
  );
  assert.equal(
    catalogCopyViolations(
      "es-CL.ts",
      'const copy = { "pricing.source": "Fuente", "catalog.origin": "Del manual", "glass.value": "Completar" };',
    ).length,
    1,
  );
  assert.equal(
    catalogCopyViolations(
      "es-CL.ts",
      'const copy = { "catalog.origin": "Fuente", "glass.empty": "Sin dato" };',
    ).length,
    2,
  );
  assert.equal(
    catalogCopyViolations(
      "sample.tsx",
      'const command = { keywords: ["vano", "posición"] }; const view = <a href="#posicion-2" id="posicion-2">Ventana</a>;',
    ).length,
    0,
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
  const candidates = files(path.join(root, "frontend/src")).filter(
    (filename) => !/[\\/](?:generated|dev)[\\/]/.test(filename),
  );
  let count = 0;
  for (const filename of candidates) {
    const findings = catalogCopyViolations(filename, readFileSync(filename, "utf8"));
    for (const finding of findings) {
      count++;
      console.error(
        `${path.relative(root, filename)}:${finding.line}: lenguaje de interfaz: ${finding.text}`,
      );
    }
  }
  if (count) process.exitCode = 1;
  else console.info("Product interface copy and detector tests PASS");
}
