import { c as create_ssr_component, o as onDestroy } from './ssr-C3HYbsxA.js';

const _=create_ssr_component((f,e,t,u)=>{let{gradio:v}=e,{value:a=1}=e,{active:i=!0}=e,o,r,l;return onDestroy(()=>{l&&clearInterval(l);}),e.gradio===void 0&&t.gradio&&v!==void 0&&t.gradio(v),e.value===void 0&&t.value&&a!==void 0&&t.value(a),e.active===void 0&&t.active&&i!==void 0&&t.active(i),(o!==a||i!==r)&&(l&&clearInterval(l),i&&(l=setInterval(()=>{document.visibilityState==="visible"&&v.dispatch("tick");},a*1e3)),o=a,r=i),""});

export { _ as default };
//# sourceMappingURL=Index15-DFvG43KK.js.map
