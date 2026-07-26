import{j as e}from"./index.BoI39RQH.js";import"./helperFunctions.Ck4K-qjq.js";import"./hdrFilteringFunctions.BAMmBZk2.js";const r="hdrFilteringPixelShader",n=`#include<helperFunctions>
#include<importanceSampling>
#include<pbrBRDFFunctions>
#include<hdrFilteringFunctions>
uniform alphaG: f32;var inputTextureSampler: sampler;var inputTexture: texture_cube<f32>;uniform vFilteringInfo: vec2f;uniform hdrScale: f32;varying direction: vec3f;@fragment
fn main(input: FragmentInputs)->FragmentOutputs {var color: vec3f=radiance(uniforms.alphaG,inputTexture,inputTextureSampler,input.direction,uniforms.vFilteringInfo);fragmentOutputs.color= vec4f(color*uniforms.hdrScale,1.0);}`;e.ShadersStoreWGSL[r]||(e.ShadersStoreWGSL[r]=n);const a={name:r,shader:n};export{a as hdrFilteringPixelShaderWGSL};
//# sourceMappingURL=hdrFiltering.fragment.DSxmCFFd.js.map
