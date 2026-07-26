import { c as create_ssr_component, b as createEventDispatcher, v as validate_component, m as missing_component } from './ssr-C3HYbsxA.js';
import { _ as _t, aA as Ce } from './2-2QjpS3e7.js';
import './index-ClteBeTX.js';
import './Component-NmRBwSfF.js';
import 'path';
import 'url';
import 'fs';

const G=create_ssr_component((_,e,t,q)=>{let{value:l}=e,s,{colors:i=[]}=e,{show_label:d}=e,{theme_mode:v}=e,{caption:c}=e,{bokeh_version:m}=e,{show_actions_button:h}=e,{gradio:f}=e,{x_lim:r=null}=e,{_selectable:u}=e,a=null,x=l?.type,P=!1;const M=createEventDispatcher(),k={plotly:()=>import('./PlotlyPlot-D4ZO-WDo.js'),bokeh:()=>import('./BokehPlot-DrxknxTG.js'),altair:()=>import('./AltairPlot-7YM1R3ND.js'),matplotlib:()=>import('./MatplotlibPlot-DZTjkRT7.js')};let n={};const T=typeof window<"u";e.value===void 0&&t.value&&l!==void 0&&t.value(l),e.colors===void 0&&t.colors&&i!==void 0&&t.colors(i),e.show_label===void 0&&t.show_label&&d!==void 0&&t.show_label(d),e.theme_mode===void 0&&t.theme_mode&&v!==void 0&&t.theme_mode(v),e.caption===void 0&&t.caption&&c!==void 0&&t.caption(c),e.bokeh_version===void 0&&t.bokeh_version&&m!==void 0&&t.bokeh_version(m),e.show_actions_button===void 0&&t.show_actions_button&&h!==void 0&&t.show_actions_button(h),e.gradio===void 0&&t.gradio&&f!==void 0&&t.gradio(f),e.x_lim===void 0&&t.x_lim&&r!==void 0&&t.x_lim(r),e._selectable===void 0&&t._selectable&&u!==void 0&&t._selectable(u);let w,E,b=_.head;do{if(w=!0,_.head=b,l!==s){let o=l?.type;o!==x&&(a=null),o&&o in k&&T&&(n[o]?a=n[o]:k[o]().then(p=>{a=p.default,n[o]=a;})),s=l,x=o,M("change");}E=`${l&&a?`${validate_component(a||missing_component,"svelte:component").$$render(_,{value:l,colors:i,theme_mode:v,show_label:d,caption:c,bokeh_version:m,show_actions_button:h,gradio:f,_selectable:u,x_lim:r,loaded_plotly_css:P},{loaded_plotly_css:o=>{P=o,w=!1;}},{})}`:`${validate_component(_t,"Empty").$$render(_,{unpadded_box:!0,size:"large"},{},{default:()=>`${validate_component(Ce,"PlotIcon").$$render(_,{},{},{})}`})}`}`;}while(!w);return E});

export { G as default };
//# sourceMappingURL=Plot-D4xKcFIN.js.map
