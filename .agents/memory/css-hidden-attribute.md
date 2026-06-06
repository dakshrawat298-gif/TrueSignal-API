---
name: HTML hidden attribute overridden by display rules
description: Why elements with the `hidden` attribute still render, and the fix.
---

The HTML `hidden` attribute only hides an element via the user-agent rule
`[hidden] { display: none }`. Any author CSS rule that sets `display` on that
same element (e.g. `.overlay { display: grid }` or `.banner { display: flex }`)
wins over the UA rule, so the element stays visible even with `hidden` set.

**Why:** this bit us when a full-screen processing overlay and a status banner
both showed on plain page load despite having the `hidden` attribute — their
`.overlay { display: grid }` / `.sandbox-banner { display: flex }` rules
silently overrode `hidden`.

**How to apply:** when an element is toggled via the `hidden` attribute (or
`el.hidden = true` / removeAttribute) but ALSO has a class that sets `display`,
add an explicit guard: `.overlay[hidden] { display: none; }`. Place it before or
with higher/equal specificity than the display rule. Alternatively toggle a
class instead of the attribute.
