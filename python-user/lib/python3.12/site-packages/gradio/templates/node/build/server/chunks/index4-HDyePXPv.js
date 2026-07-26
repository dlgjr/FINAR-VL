function c(s,t){const n=JSON.stringify(s),e=new Headers(t?.headers);return e.has("content-length")||e.set("content-length",o.encode(n).byteLength.toString()),e.has("content-type")||e.set("content-type","application/json"),new Response(n,{...t,headers:e})}const o=new TextEncoder;function r(s,t){const n=new Headers(t?.headers);if(!n.has("content-length")){const e=o.encode(s);return n.set("content-length",e.byteLength.toString()),new Response(e,{...t,headers:n})}return new Response(s,{...t,headers:n})}

export { c, r };
//# sourceMappingURL=index4-HDyePXPv.js.map
