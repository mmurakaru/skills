// Diff two computed-style captures. Exit 0 = identical, 1 = differs (prints each change).
import { readFileSync } from "node:fs";

const [beforePath, afterPath] = process.argv.slice(2);
const beforeElements = JSON.parse(readFileSync(beforePath));
const afterElements = JSON.parse(readFileSync(afterPath));

let changeCount = 0;
if (beforeElements.length !== afterElements.length) {
  console.log(`structural change: ${beforeElements.length} → ${afterElements.length} elements`);
  changeCount++;
}

const comparableCount = Math.min(beforeElements.length, afterElements.length);

for (const [index, beforeElement] of beforeElements.slice(0, comparableCount).entries()) {
  const beforeStyles = beforeElement.styles;
  const afterStyles = afterElements[index].styles;
  
  for (const property of new Set([...Object.keys(beforeStyles), ...Object.keys(afterStyles)])) {
    if (beforeStyles[property] !== afterStyles[property]) {
      console.log(`[${index} ${beforeElement.tag}] ${property}: ${beforeStyles[property]} → ${afterStyles[property]}`);
      changeCount++;
    }
  }
}

console.log(changeCount ? `\n${changeCount} change(s) → designer decision` : "no computed-style diff");
process.exit(changeCount ? 1 : 0);
