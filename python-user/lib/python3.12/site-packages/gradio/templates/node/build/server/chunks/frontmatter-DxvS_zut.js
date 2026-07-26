import { s as Kp, t as m, f as hm, c as qy, p as Fy, S as Lt } from './Index17-BN-GAMZQ.js';
import { yaml as a } from './yaml-C6fZICTl.js';
import './ssr-C3HYbsxA.js';
import './2-2QjpS3e7.js';
import './index-ClteBeTX.js';
import './Component-NmRBwSfF.js';
import 'path';
import 'url';
import 'fs';
import './Example9-BgAxc6bX.js';

const n=/^---\s*$/m,F={defineNodes:[{name:"Frontmatter",block:!0},"FrontmatterMark"],props:[Kp({Frontmatter:[m.documentMeta,m.monospace],FrontmatterMark:m.processingInstruction}),hm.add({Frontmatter:qy,FrontmatterMark:()=>null})],wrap:Fy(t=>{const{parser:e}=Lt.define(a);return t.type.name==="Frontmatter"?{parser:e,overlay:[{from:t.from+4,to:t.to-4}]}:null}),parseBlock:[{name:"Frontmatter",before:"HorizontalRule",parse:(t,e)=>{let r;const a=new Array;if(t.lineStart===0&&n.test(e.text)){for(a.push(t.elt("FrontmatterMark",0,4));t.nextLine();)if(n.test(e.text)){r=t.lineStart+4;break}return r!==void 0&&(a.push(t.elt("FrontmatterMark",r-4,r)),t.addElement(t.elt("Frontmatter",0,r,a))),!0}return !1}}]};

export { F as frontmatter };
//# sourceMappingURL=frontmatter-DxvS_zut.js.map
