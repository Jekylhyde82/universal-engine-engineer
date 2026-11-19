import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const root = new URL("../", import.meta.url);
const html = await readFile(new URL("tools/repository-capability-scout/index.html", root), "utf8");
const schema = JSON.parse(await readFile(new URL("tools/repository-capability-scout/repository-candidate.schema.json", root), "utf8"));
const script = html.match(/<script>([\\s\\S]*?)<\\/script>/i)?.[1];

test("embedded application JavaScript parses", () => {
  assert.ok(script, "inline application script exists");
  assert.doesNotThrow(() => new vm.Script(script));
});

test("CSP restricts network access to the GitHub API", () => {
  assert.match(html, /connect-src https:\/\/api\\.github\\.com/);
  assert.match(html, /base-uri 'none'/);
  assert.match(html, /form-action 'none'/);
});

test("imports are bounded and fail closed", () => {
  assert.match(script, /file\\.size>2\\*1024\\*1024/);
  assert.match(script, /records\\.length>500/);
  assert.match(script, /!records\\.every\\(validRecord\\)/);
  assert.match(script, /No records were imported/);
});

test("repository URL validation is HTTPS and GitHub-host restricted", () => {
  assert.match(script, /u\\.protocol==="https:"/);
  assert.match(script, /u\\.hostname==="github\\.com"/);
});

test("schema requires the eight evaluation gates and rejects unknown properties", () => {
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.gates.additionalProperties, false);
  assert.equal(schema.properties.gates.required.length, 8);
  assert.deepEqual(schema.properties.gates.properties.G0_SOURCE_IDENTITY.enum,
    ["NOT_ASSESSED", "PASS", "FAIL", "REQUIRES_REVIEW"]);
});
