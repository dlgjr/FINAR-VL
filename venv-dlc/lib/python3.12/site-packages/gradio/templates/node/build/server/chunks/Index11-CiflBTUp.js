import { c as create_ssr_component, v as validate_component } from './ssr-C3HYbsxA.js';
import { P } from './JSON-DqGnZuFO.js';
import { I as It, f as Et, as as re, E as Et$1 } from './2-2QjpS3e7.js';
import './index-ClteBeTX.js';
import './Component-NmRBwSfF.js';
import 'path';
import 'url';
import 'fs';

const F=create_ssr_component((o,e,l,z)=>{let{elem_id:_=""}=e,{elem_classes:d=[]}=e,{visible:m=!0}=e,{value:t}=e,O,{loading_status:c}=e,{label:i}=e,{show_label:f}=e,{container:v=!0}=e,{scale:u=null}=e,{min_width:w=void 0}=e,{gradio:a}=e,{open:S=!1}=e,{theme_mode:x}=e,{show_indices:B}=e,{height:J}=e,{min_height:k}=e,{max_height:r}=e,N=0;return e.elem_id===void 0&&l.elem_id&&_!==void 0&&l.elem_id(_),e.elem_classes===void 0&&l.elem_classes&&d!==void 0&&l.elem_classes(d),e.visible===void 0&&l.visible&&m!==void 0&&l.visible(m),e.value===void 0&&l.value&&t!==void 0&&l.value(t),e.loading_status===void 0&&l.loading_status&&c!==void 0&&l.loading_status(c),e.label===void 0&&l.label&&i!==void 0&&l.label(i),e.show_label===void 0&&l.show_label&&f!==void 0&&l.show_label(f),e.container===void 0&&l.container&&v!==void 0&&l.container(v),e.scale===void 0&&l.scale&&u!==void 0&&l.scale(u),e.min_width===void 0&&l.min_width&&w!==void 0&&l.min_width(w),e.gradio===void 0&&l.gradio&&a!==void 0&&l.gradio(a),e.open===void 0&&l.open&&S!==void 0&&l.open(S),e.theme_mode===void 0&&l.theme_mode&&x!==void 0&&l.theme_mode(x),e.show_indices===void 0&&l.show_indices&&B!==void 0&&l.show_indices(B),e.height===void 0&&l.height&&J!==void 0&&l.height(J),e.min_height===void 0&&l.min_height&&k!==void 0&&l.min_height(k),e.max_height===void 0&&l.max_height&&r!==void 0&&l.max_height(r),t!==O&&(O=t,a.dispatch("change")),`${validate_component(It,"Block").$$render(o,{visible:m,test_id:"json",elem_id:_,elem_classes:d,container:v,scale:u,min_width:w,padding:!1,allow_overflow:!0,overflow_behavior:"auto",height:J,min_height:k,max_height:r},{},{default:()=>`<div>${i?`${validate_component(Et,"BlockLabel").$$render(o,{Icon:re,show_label:f,label:i,float:!1,disable:v===!1},{},{})}`:""}</div> ${validate_component(Et$1,"StatusTracker").$$render(o,Object.assign({},{autoscroll:a.autoscroll},{i18n:a.i18n},c),{},{})} ${validate_component(P,"JSON").$$render(o,{value:t,open:S,theme_mode:x,show_indices:B,label_height:N},{},{})}`})}`});

export { P as BaseJSON, F as default };
//# sourceMappingURL=Index11-CiflBTUp.js.map
