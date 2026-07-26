import { c as create_ssr_component, v as validate_component } from './ssr-C3HYbsxA.js';
import { A as Aa } from './2-2QjpS3e7.js';
import './index-ClteBeTX.js';
import './Component-NmRBwSfF.js';
import 'path';
import 'url';
import 'fs';

const v={code:".gallery.svelte-1ayixqk{padding:var(--size-1) var(--size-2)}",map:'{"version":3,"file":"Example.svelte","sources":["Example.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { MarkdownCode } from \\"@gradio/markdown-code\\";\\nexport let value;\\nexport let type;\\nexport let selected = false;\\nexport let sanitize_html;\\nexport let line_breaks;\\nexport let latex_delimiters;\\nfunction truncate_text(text, max_length = 60) {\\n    if (!text)\\n        return \\"\\";\\n    const str = String(text);\\n    if (str.length <= max_length)\\n        return str;\\n    return str.slice(0, max_length) + \\"...\\";\\n}\\n<\/script>\\n\\n<div\\n\\tclass:table={type === \\"table\\"}\\n\\tclass:gallery={type === \\"gallery\\"}\\n\\tclass:selected\\n\\tclass=\\"prose\\"\\n>\\n\\t<MarkdownCode\\n\\t\\tmessage={truncate_text(value)}\\n\\t\\t{latex_delimiters}\\n\\t\\t{sanitize_html}\\n\\t\\t{line_breaks}\\n\\t\\tchatbot={false}\\n\\t/>\\n</div>\\n\\n<style>\\n\\t.gallery {\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t}</style>\\n"],"names":[],"mappings":"AAiCC,uBAAS,CACR,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CACpC"}'};function _(l,t=60){if(!l)return "";const e=String(l);return e.length<=t?e:e.slice(0,t)+"..."}const u=create_ssr_component((l,t,e,x)=>{let{value:n}=t,{type:a}=t,{selected:r=!1}=t,{sanitize_html:s}=t,{line_breaks:i}=t,{latex_delimiters:o}=t;return t.value===void 0&&e.value&&n!==void 0&&e.value(n),t.type===void 0&&e.type&&a!==void 0&&e.type(a),t.selected===void 0&&e.selected&&r!==void 0&&e.selected(r),t.sanitize_html===void 0&&e.sanitize_html&&s!==void 0&&e.sanitize_html(s),t.line_breaks===void 0&&e.line_breaks&&i!==void 0&&e.line_breaks(i),t.latex_delimiters===void 0&&e.latex_delimiters&&o!==void 0&&e.latex_delimiters(o),l.css.add(v),`<div class="${["prose svelte-1ayixqk",(a==="table"?"table":"")+" "+(a==="gallery"?"gallery":"")+" "+(r?"selected":"")].join(" ").trim()}">${validate_component(Aa,"MarkdownCode").$$render(l,{message:_(n),latex_delimiters:o,sanitize_html:s,line_breaks:i,chatbot:!1},{},{})} </div>`});

export { u as default };
//# sourceMappingURL=Example21-uz6Wj3xI.js.map
