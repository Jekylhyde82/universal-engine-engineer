import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const root = new URL("../", import.meta.url);
const html = await readFile(new URL("tools/repository-capability-scout/index.html", root), "utf8");
const schema = JSON.parse(await readFile(new URL("tools/repository-capability-scout/repository-candidate.schema.json", root), "utf8"));
const scriptStart = html.indexOf("<script>");
const scriptEnd = html.indexOf("</script>", scriptStart);
const script = html.slice(scriptStart + 8, scriptEnd);

test("embedded application JavaScript parses", () => {
  assert.ok(scriptStart >= 0 && scriptEnd > scriptStart);
  assert.doesNotThrow(() => new vm.Script(script));
});

test("CSP restricts network access to the GitHub API", () => {
  assert.ok(html.includes("connect-src https://api.github.com"));
  assert.ok(html.includes("base-uri 'none'"));
  assert.ok(html.includes("form-action 'none'"));
});

test("imports are bounded and fail closed", () => {
  assert.ok(script.includes("file.size>2*1024*1024"));
  assert.ok(script.includes("records.length>500"));
  assert.ok(script.includes("!records.every(validRecord)"));
  assert.ok(script.includes("No records were imported"));
});

test("repository URL validation is HTTPS and GitHub-host restricted", () => {
  assert.ok(script.includes('u.protocol==="https:"'));
  assert.ok(script.includes('u.hostname==="github.com"'));
});

test("schema requires the eight evaluation gates and rejects unknown properties", () => {
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.gates.additionalProperties, false);
  assert.equal(schema.properties.gates.required.length, 8);
  assert.deepEqual(schema.properties.gates.properties.G0_SOURCE_IDENTITY.enum,
    ["NOT_ASSESSED", "PASS", "FAIL", "REQUIRES_REVIEW"]);
});
