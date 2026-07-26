import{j as r}from"./index-C2d42dEp.js";import"./index-DputZZxm.js";import"./svelte/svelte.js";const e="passPixelShader",t=`varying vUV: vec2f;var textureSamplerSampler: sampler;var textureSampler: texture_2d<f32>;
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {fragmentOutputs.color=textureSample(textureSampler,textureSamplerSampler,input.vUV);}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=t);const m={name:e,shader:t};export{m as passPixelShaderWGSL};
//# sourceMappingURL=pass.fragment-3qtFV6lH.js.map
