import{j as r}from"./index-C2d42dEp.js";import"./index-DputZZxm.js";import"./svelte/svelte.js";const e="iblCdfxPixelShader",i=`precision highp sampler2D;
#define PI 3.1415927
varying vec2 vUV;uniform sampler2D cdfy;void main(void) {ivec2 cdfyRes=textureSize(cdfy,0);ivec2 currentPixel=ivec2(gl_FragCoord.xy);float cdfx=0.0;for (int x=1; x<=currentPixel.x; x++) {cdfx+=texelFetch(cdfy,ivec2(x-1,cdfyRes.y-1),0).x;}
gl_FragColor=vec4(vec3(cdfx),1.0);}`;r.ShadersStore[e]||(r.ShadersStore[e]=i);const x={name:e,shader:i};export{x as iblCdfxPixelShader};
//# sourceMappingURL=iblCdfx.fragment-QyHPOuHU.js.map
