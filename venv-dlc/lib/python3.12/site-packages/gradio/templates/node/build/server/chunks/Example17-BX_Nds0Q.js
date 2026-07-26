import { c as create_ssr_component } from './ssr-C3HYbsxA.js';

const c={code:".gallery.svelte-zvfedn{padding:var(--size-2)}",map:'{"version":3,"file":"Example.svelte","sources":["Example.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let value;\\nexport let type;\\nexport let selected = false;\\n<\/script>\\n\\n<div\\n\\tclass:table={type === \\"table\\"}\\n\\tclass:gallery={type === \\"gallery\\"}\\n\\tclass:selected\\n\\tclass=\\"prose\\"\\n>\\n\\t{@html value}\\n</div>\\n\\n<style>\\n\\t.gallery {\\n\\t\\tpadding: var(--size-2);\\n\\t}</style>\\n"],"names":[],"mappings":"AAeC,sBAAS,CACR,OAAO,CAAE,IAAI,QAAQ,CACtB"}'},o=create_ssr_component((v,e,t,d)=>{let{value:s}=e,{type:l}=e,{selected:a=!1}=e;return e.value===void 0&&t.value&&s!==void 0&&t.value(s),e.type===void 0&&t.type&&l!==void 0&&t.type(l),e.selected===void 0&&t.selected&&a!==void 0&&t.selected(a),v.css.add(c),`<div class="${["prose svelte-zvfedn",(l==="table"?"table":"")+" "+(l==="gallery"?"gallery":"")+" "+(a?"selected":"")].join(" ").trim()}"><!-- HTML_TAG_START -->${s}<!-- HTML_TAG_END --> </div>`});

export { o as default };
//# sourceMappingURL=Example17-BX_Nds0Q.js.map
