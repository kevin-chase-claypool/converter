import { readFileSync } from "node:fs";

const artifactToolUrl = process.env.ARTIFACT_TOOL_URL;
if (!artifactToolUrl) {
  throw new Error("ARTIFACT_TOOL_URL is required");
}

const payload = JSON.parse(readFileSync(0, "utf8"));
if (!Array.isArray(payload) || payload.some((item) => typeof item !== "string")) {
  throw new Error("Expected a JSON array of LaTeX strings on stdin");
}

const { mathFromLatex, mathToMathMl } = await import(artifactToolUrl);
const mathml = payload.map((latex) =>
  mathToMathMl(
    mathFromLatex({
      // The bundled equation parser does not understand these two common TeX
      // aliases, so normalize them to their Unicode glyph or a preserved space.
      latex: latex
        .replace(/\\approx\b/g, "≈")
        .replace(/\\[,;]/g, "\u00a0"),
      displayMode: "block",
    }),
  ),
);

process.stdout.write(JSON.stringify(mathml));
