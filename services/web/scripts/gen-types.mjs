import { readFileSync, writeFileSync } from "node:fs";
import { compile } from "json-schema-to-typescript";

const schema = JSON.parse(readFileSync("../../packages/contracts/site.schema.json", "utf8"));
const wrapper = {
  ...schema,
  title: "SiteModels",
  type: "object",
  properties: Object.fromEntries(Object.keys(schema.$defs).map((k) => [k, { $ref: `#/$defs/${k}` }])),
  required: Object.keys(schema.$defs),
};
const ts = await compile(wrapper, "SiteModels", { additionalProperties: false });
writeFileSync("src/lib/contract.ts", ts);
