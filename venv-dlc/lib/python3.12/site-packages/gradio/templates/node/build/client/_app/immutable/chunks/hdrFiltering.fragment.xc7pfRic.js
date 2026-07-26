import{j as e}from"./index.BoI39RQH.js";import"./helperFunctions.BZ696Q10.js";import"./hdrFilteringFunctions.5uiW-V2V.js";const r="hdrFilteringPixelShader",i=`#include<helperFunctions>
#include<importanceSampling>
#include<pbrBRDFFunctions>
#include<hdrFilteringFunctions>
uniform float alphaG;uniform samplerCube inputTexture;uniform vec2 vFilteringInfo;uniform float hdrScale;varying vec3 direction;void main() {vec3 color=radiance(alphaG,inputTexture,direction,vFilteringInfo);gl_FragColor=vec4(color*hdrScale,1.0);}`;e.ShadersStore[r]||(e.ShadersStore[r]=i);const a={name:r,shader:i};export{a as hdrFilteringPixelShader};
//# sourceMappingURL=hdrFiltering.fragment.xc7pfRic.js.map
