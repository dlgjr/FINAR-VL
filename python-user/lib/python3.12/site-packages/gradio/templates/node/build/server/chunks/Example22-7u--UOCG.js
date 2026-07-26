import { c as create_ssr_component, e as escape } from './ssr-C3HYbsxA.js';

const n={code:".gallery.svelte-1ayixqk{padding:var(--size-1) var(--size-2)}",map:'{"version":3,"file":"Example.svelte","sources":["Example.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let value;\\nexport let type;\\nexport let selected = false;\\n<\/script>\\n\\n<div\\n\\tclass:table={type === \\"table\\"}\\n\\tclass:gallery={type === \\"gallery\\"}\\n\\tclass:selected\\n>\\n\\t{value ? value : \\"\\"}\\n</div>\\n\\n<style>\\n\\t.gallery {\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t}</style>\\n"],"names":[],"mappings":"AAcC,uBAAS,CACR,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CACpC"}'},i=create_ssr_component((v,e,t,r)=>{let{value:l}=e,{type:a}=e,{selected:s=!1}=e;return e.value===void 0&&t.value&&l!==void 0&&t.value(l),e.type===void 0&&t.type&&a!==void 0&&t.type(a),e.selected===void 0&&t.selected&&s!==void 0&&t.selected(s),v.css.add(n),`<div class="${["svelte-1ayixqk",(a==="table"?"table":"")+" "+(a==="gallery"?"gallery":"")+" "+(s?"selected":"")].join(" ").trim()}">${escape(l||"")} </div>`});

export { i as default };
//# sourceMappingURL=Example22-7u--UOCG.js.map
