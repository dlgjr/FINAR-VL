import{j as O,R as Ht,P as Dt,E as Rt,F as Mt,H as kt,U as Ut,Z as Bt,$ as Ft,aL as Ot,a2 as Pt,a4 as Nt,a6 as Wt,S as dt,a8 as Zt,aa as X,bq as Gt,br as Xt,ab as Ne,M as Te,V as T,aU as We,bs as jt,a as W,h as _e,ak as Tt,bt as Re,b as $t,av as ae,bu as Vt,ay as te,bv as Me,aS as q,Q as Kt,C as Ce,az as ce,bw as ee,B as qt,bx as ke,af as Qt}from"./index.BoI39RQH.js";import{_ as we}from"./preload-helper.D6kgxu3v.js";import"./fogFragment.D2zFd_lI.js";import"./logDepthDeclaration.B72K0fi0.js";import"./logDepthVertex.CcEiEiyg.js";import"./helperFunctions.BZ696Q10.js";import"./fogFragment.BUxLzITE.js";import"./logDepthDeclaration.DiRgFK2Q.js";import"./meshUboDeclaration.Bq7Ie8G6.js";import"./helperFunctions.Ck4K-qjq.js";import"./logDepthVertex.MGj6XVNz.js";import{R as be}from"./rawTexture.CJKlnpAh.js";import"./thinInstanceMesh.BW3MxSeP.js";import{A as Jt}from"./assetContainer.w1CRG79i.js";import{Ray as Lt}from"./ray.sJZVblPT.js";import{S as Yt}from"./standardMaterial.Cnq1RvLI.js";const _t="gaussianSplattingFragmentDeclaration",es=`vec4 gaussianColor(vec4 inColor)
{float A=-dot(vPosition,vPosition);if (A<-4.0) discard;float B=exp(A)*inColor.a;
#include<logDepthFragment>
vec3 color=inColor.rgb;
#ifdef FOG
#include<fogFragment>
#endif
return vec4(color,B);}
`;O.IncludesShadersStore[_t]||(O.IncludesShadersStore[_t]=es);const Be="gaussianSplattingPixelShader",At=`#include<clipPlaneFragmentDeclaration>
#include<logDepthDeclaration>
#include<fogFragmentDeclaration>
varying vec4 vColor;varying vec2 vPosition;
#include<gaussianSplattingFragmentDeclaration>
void main () { 
#include<clipPlaneFragment>
gl_FragColor=gaussianColor(vColor);}
`;O.ShadersStore[Be]||(O.ShadersStore[Be]=At);const ts={name:Be,shader:At},ss=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingPixelShader:ts},Symbol.toStringTag,{value:"Module"})),pt="gaussianSplattingVertexDeclaration",rs="attribute vec2 position;uniform mat4 view;uniform mat4 projection;uniform mat4 world;uniform vec4 vEyePosition;";O.IncludesShadersStore[pt]||(O.IncludesShadersStore[pt]=rs);const xt="gaussianSplattingUboDeclaration",os=`#include<sceneUboDeclaration>
#include<meshUboDeclaration>
attribute vec2 position;`;O.IncludesShadersStore[xt]||(O.IncludesShadersStore[xt]=os);const mt="gaussianSplatting",ns=`#if !defined(WEBGL2) && !defined(WEBGPU) && !defined(NATIVE)
mat3 transpose(mat3 matrix) {return mat3(matrix[0][0],matrix[1][0],matrix[2][0],
matrix[0][1],matrix[1][1],matrix[2][1],
matrix[0][2],matrix[1][2],matrix[2][2]);}
#endif
vec2 getDataUV(float index,vec2 textureSize) {float y=floor(index/textureSize.x);float x=index-y*textureSize.x;return vec2((x+0.5)/textureSize.x,(y+0.5)/textureSize.y);}
#if SH_DEGREE>0
ivec2 getDataUVint(float index,vec2 textureSize) {float y=floor(index/textureSize.x);float x=index-y*textureSize.x;return ivec2(uint(x+0.5),uint(y+0.5));}
#endif
struct Splat {vec4 center;vec4 color;vec4 covA;vec4 covB;
#if SH_DEGREE>0
uvec4 sh0; 
#endif
#if SH_DEGREE>1
uvec4 sh1;
#endif
#if SH_DEGREE>2
uvec4 sh2;
#endif
};Splat readSplat(float splatIndex)
{Splat splat;vec2 splatUV=getDataUV(splatIndex,dataTextureSize);splat.center=texture2D(centersTexture,splatUV);splat.color=texture2D(colorsTexture,splatUV);splat.covA=texture2D(covariancesATexture,splatUV)*splat.center.w;splat.covB=texture2D(covariancesBTexture,splatUV)*splat.center.w;
#if SH_DEGREE>0
ivec2 splatUVint=getDataUVint(splatIndex,dataTextureSize);splat.sh0=texelFetch(shTexture0,splatUVint,0);
#endif
#if SH_DEGREE>1
splat.sh1=texelFetch(shTexture1,splatUVint,0);
#endif
#if SH_DEGREE>2
splat.sh2=texelFetch(shTexture2,splatUVint,0);
#endif
return splat;}
#if defined(WEBGL2) || defined(WEBGPU) || defined(NATIVE)
vec3 computeColorFromSHDegree(vec3 dir,const vec3 sh[16])
{const float SH_C0=0.28209479;const float SH_C1=0.48860251;float SH_C2[5];SH_C2[0]=1.092548430;SH_C2[1]=-1.09254843;SH_C2[2]=0.315391565;SH_C2[3]=-1.09254843;SH_C2[4]=0.546274215;float SH_C3[7];SH_C3[0]=-0.59004358;SH_C3[1]=2.890611442;SH_C3[2]=-0.45704579;SH_C3[3]=0.373176332;SH_C3[4]=-0.45704579;SH_C3[5]=1.445305721;SH_C3[6]=-0.59004358;vec3 result=/*SH_C0**/sh[0];
#if SH_DEGREE>0
float x=dir.x;float y=dir.y;float z=dir.z;result+=- SH_C1*y*sh[1]+SH_C1*z*sh[2]-SH_C1*x*sh[3];
#if SH_DEGREE>1
float xx=x*x,yy=y*y,zz=z*z;float xy=x*y,yz=y*z,xz=x*z;result+=
SH_C2[0]*xy*sh[4] +
SH_C2[1]*yz*sh[5] +
SH_C2[2]*(2.0*zz-xx-yy)*sh[6] +
SH_C2[3]*xz*sh[7] +
SH_C2[4]*(xx-yy)*sh[8];
#if SH_DEGREE>2
result+=
SH_C3[0]*y*(3.0*xx-yy)*sh[9] +
SH_C3[1]*xy*z*sh[10] +
SH_C3[2]*y*(4.0*zz-xx-yy)*sh[11] +
SH_C3[3]*z*(2.0*zz-3.0*xx-3.0*yy)*sh[12] +
SH_C3[4]*x*(4.0*zz-xx-yy)*sh[13] +
SH_C3[5]*z*(xx-yy)*sh[14] +
SH_C3[6]*x*(xx-3.0*yy)*sh[15];
#endif
#endif
#endif
return result;}
vec4 decompose(uint value)
{vec4 components=vec4(
float((value ) & 255u),
float((value>>uint( 8)) & 255u),
float((value>>uint(16)) & 255u),
float((value>>uint(24)) & 255u));return components*vec4(2./255.)-vec4(1.);}
vec3 computeSH(Splat splat,vec3 color,vec3 dir)
{vec3 sh[16];sh[0]=color;
#if SH_DEGREE>0
vec4 sh00=decompose(splat.sh0.x);vec4 sh01=decompose(splat.sh0.y);vec4 sh02=decompose(splat.sh0.z);sh[1]=vec3(sh00.x,sh00.y,sh00.z);sh[2]=vec3(sh00.w,sh01.x,sh01.y);sh[3]=vec3(sh01.z,sh01.w,sh02.x);
#endif
#if SH_DEGREE>1
vec4 sh03=decompose(splat.sh0.w);vec4 sh04=decompose(splat.sh1.x);vec4 sh05=decompose(splat.sh1.y);sh[4]=vec3(sh02.y,sh02.z,sh02.w);sh[5]=vec3(sh03.x,sh03.y,sh03.z);sh[6]=vec3(sh03.w,sh04.x,sh04.y);sh[7]=vec3(sh04.z,sh04.w,sh05.x);sh[8]=vec3(sh05.y,sh05.z,sh05.w);
#endif
#if SH_DEGREE>2
vec4 sh06=decompose(splat.sh1.z);vec4 sh07=decompose(splat.sh1.w);vec4 sh08=decompose(splat.sh2.x);vec4 sh09=decompose(splat.sh2.y);vec4 sh10=decompose(splat.sh2.z);vec4 sh11=decompose(splat.sh2.w);sh[9]=vec3(sh06.x,sh06.y,sh06.z);sh[10]=vec3(sh06.w,sh07.x,sh07.y);sh[11]=vec3(sh07.z,sh07.w,sh08.x);sh[12]=vec3(sh08.y,sh08.z,sh08.w);sh[13]=vec3(sh09.x,sh09.y,sh09.z);sh[14]=vec3(sh09.w,sh10.x,sh10.y);sh[15]=vec3(sh10.z,sh10.w,sh11.x); 
#endif
return computeColorFromSHDegree(dir,sh);}
#else
vec3 computeSH(Splat splat,vec3 color,vec3 dir)
{return color;}
#endif
vec4 gaussianSplatting(vec2 meshPos,vec3 worldPos,vec2 scale,vec3 covA,vec3 covB,mat4 worldMatrix,mat4 viewMatrix,mat4 projectionMatrix)
{mat4 modelView=viewMatrix*worldMatrix;vec4 camspace=viewMatrix*vec4(worldPos,1.);vec4 pos2d=projectionMatrix*camspace;float bounds=1.2*pos2d.w;if (pos2d.z<-pos2d.w || pos2d.x<-bounds || pos2d.x>bounds
|| pos2d.y<-bounds || pos2d.y>bounds) {return vec4(0.0,0.0,2.0,1.0);}
mat3 Vrk=mat3(
covA.x,covA.y,covA.z,
covA.y,covB.x,covB.y,
covA.z,covB.y,covB.z
);mat3 J=mat3(
focal.x/camspace.z,0.,-(focal.x*camspace.x)/(camspace.z*camspace.z),
0.,focal.y/camspace.z,-(focal.y*camspace.y)/(camspace.z*camspace.z),
0.,0.,0.
);mat3 invy=mat3(1,0,0,0,-1,0,0,0,1);mat3 T=invy*transpose(mat3(modelView))*J;mat3 cov2d=transpose(T)*Vrk*T;float mid=(cov2d[0][0]+cov2d[1][1])/2.0;float radius=length(vec2((cov2d[0][0]-cov2d[1][1])/2.0,cov2d[0][1]));float epsilon=0.0001;float lambda1=mid+radius+epsilon,lambda2=mid-radius+epsilon;if (lambda2<0.0)
{return vec4(0.0,0.0,2.0,1.0);}
vec2 diagonalVector=normalize(vec2(cov2d[0][1],lambda1-cov2d[0][0]));vec2 majorAxis=min(sqrt(2.0*lambda1),1024.0)*diagonalVector;vec2 minorAxis=min(sqrt(2.0*lambda2),1024.0)*vec2(diagonalVector.y,-diagonalVector.x);vec2 vCenter=vec2(pos2d);return vec4(
vCenter 
+ ((meshPos.x*majorAxis
+ meshPos.y*minorAxis)*invViewport*pos2d.w)*scale,pos2d.zw);}`;O.IncludesShadersStore[mt]||(O.IncludesShadersStore[mt]=ns);const Fe="gaussianSplattingVertexShader",Et=`#include<__decl__gaussianSplattingVertex>
#ifdef LOGARITHMICDEPTH
#extension GL_EXT_frag_depth : enable
#endif
#include<clipPlaneVertexDeclaration>
#include<fogVertexDeclaration>
#include<logDepthDeclaration>
#include<helperFunctions>
attribute float splatIndex;uniform vec2 invViewport;uniform vec2 dataTextureSize;uniform vec2 focal;uniform sampler2D covariancesATexture;uniform sampler2D covariancesBTexture;uniform sampler2D centersTexture;uniform sampler2D colorsTexture;
#if SH_DEGREE>0
uniform highp usampler2D shTexture0;
#endif
#if SH_DEGREE>1
uniform highp usampler2D shTexture1;
#endif
#if SH_DEGREE>2
uniform highp usampler2D shTexture2;
#endif
varying vec4 vColor;varying vec2 vPosition;
#include<gaussianSplatting>
void main () {Splat splat=readSplat(splatIndex);vec3 covA=splat.covA.xyz;vec3 covB=vec3(splat.covA.w,splat.covB.xy);vec4 worldPos=world*vec4(splat.center.xyz,1.0);vColor=splat.color;vPosition=position;
#if SH_DEGREE>0
mat3 worldRot=mat3(world);mat3 normWorldRot=inverseMat3(worldRot);vec3 dir=normalize(normWorldRot*(worldPos.xyz-vEyePosition.xyz));dir*=vec3(1.,1.,-1.); 
vColor.xyz=computeSH(splat,splat.color.xyz,dir);
#endif
gl_Position=gaussianSplatting(position,worldPos.xyz,vec2(1.,1.),covA,covB,world,view,projection);
#include<clipPlaneVertex>
#include<fogVertex>
#include<logDepthVertex>
}
`;O.ShadersStore[Fe]||(O.ShadersStore[Fe]=Et);const is={name:Fe,shader:Et},as=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingVertexShader:is},Symbol.toStringTag,{value:"Module"})),vt="gaussianSplattingFragmentDeclaration",cs=`fn gaussianColor(inColor: vec4f,inPosition: vec2f)->vec4f
{var A : f32=-dot(inPosition,inPosition);if (A>-4.0)
{var B: f32=exp(A)*inColor.a;
#include<logDepthFragment>
var color: vec3f=inColor.rgb;
#ifdef FOG
#include<fogFragment>
#endif
return vec4f(color,B);} else {return vec4f(0.0);}}
`;O.IncludesShadersStoreWGSL[vt]||(O.IncludesShadersStoreWGSL[vt]=cs);const Oe="gaussianSplattingPixelShader",zt=`#include<clipPlaneFragmentDeclaration>
#include<logDepthDeclaration>
#include<fogFragmentDeclaration>
varying vColor: vec4f;varying vPosition: vec2f;
#include<gaussianSplattingFragmentDeclaration>
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {
#include<clipPlaneFragment>
fragmentOutputs.color=gaussianColor(input.vColor,input.vPosition);}
`;O.ShadersStoreWGSL[Oe]||(O.ShadersStoreWGSL[Oe]=zt);const ls={name:Oe,shader:zt},us=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingPixelShaderWGSL:ls},Symbol.toStringTag,{value:"Module"})),gt="gaussianSplatting",hs=`fn getDataUV(index: f32,dataTextureSize: vec2f)->vec2<f32> {let y: f32=floor(index/dataTextureSize.x);let x: f32=index-y*dataTextureSize.x;return vec2f((x+0.5),(y+0.5));}
struct Splat {center: vec4f,
color: vec4f,
covA: vec4f,
covB: vec4f,
#if SH_DEGREE>0
sh0: vec4<u32>,
#endif
#if SH_DEGREE>1
sh1: vec4<u32>,
#endif
#if SH_DEGREE>2
sh2: vec4<u32>,
#endif
};fn readSplat(splatIndex: f32,dataTextureSize: vec2f)->Splat {var splat: Splat;let splatUV=getDataUV(splatIndex,dataTextureSize);let splatUVi32=vec2<i32>(i32(splatUV.x),i32(splatUV.y));splat.center=textureLoad(centersTexture,splatUVi32,0);splat.color=textureLoad(colorsTexture,splatUVi32,0);splat.covA=textureLoad(covariancesATexture,splatUVi32,0)*splat.center.w;splat.covB=textureLoad(covariancesBTexture,splatUVi32,0)*splat.center.w;
#if SH_DEGREE>0
splat.sh0=textureLoad(shTexture0,splatUVi32,0);
#endif
#if SH_DEGREE>1
splat.sh1=textureLoad(shTexture1,splatUVi32,0);
#endif
#if SH_DEGREE>2
splat.sh2=textureLoad(shTexture2,splatUVi32,0);
#endif
return splat;}
fn computeColorFromSHDegree(dir: vec3f,sh: array<vec3<f32>,16>)->vec3f
{let SH_C0: f32=0.28209479;let SH_C1: f32=0.48860251;var SH_C2: array<f32,5>=array<f32,5>(
1.092548430,
-1.09254843,
0.315391565,
-1.09254843,
0.546274215
);var SH_C3: array<f32,7>=array<f32,7>(
-0.59004358,
2.890611442,
-0.45704579,
0.373176332,
-0.45704579,
1.445305721,
-0.59004358
);var result: vec3f=/*SH_C0**/sh[0];
#if SH_DEGREE>0
let x: f32=dir.x;let y: f32=dir.y;let z: f32=dir.z;result+=-SH_C1*y*sh[1]+SH_C1*z*sh[2]-SH_C1*x*sh[3];
#if SH_DEGREE>1
let xx: f32=x*x;let yy: f32=y*y;let zz: f32=z*z;let xy: f32=x*y;let yz: f32=y*z;let xz: f32=x*z;result+=
SH_C2[0]*xy*sh[4] +
SH_C2[1]*yz*sh[5] +
SH_C2[2]*(2.0f*zz-xx-yy)*sh[6] +
SH_C2[3]*xz*sh[7] +
SH_C2[4]*(xx-yy)*sh[8];
#if SH_DEGREE>2
result+=
SH_C3[0]*y*(3.0f*xx-yy)*sh[9] +
SH_C3[1]*xy*z*sh[10] +
SH_C3[2]*y*(4.0f*zz-xx-yy)*sh[11] +
SH_C3[3]*z*(2.0f*zz-3.0f*xx-3.0f*yy)*sh[12] +
SH_C3[4]*x*(4.0f*zz-xx-yy)*sh[13] +
SH_C3[5]*z*(xx-yy)*sh[14] +
SH_C3[6]*x*(xx-3.0f*yy)*sh[15];
#endif
#endif
#endif
return result;}
fn decompose(value: u32)->vec4f
{let components : vec4f=vec4f(
f32((value ) & 255u),
f32((value>>u32( 8)) & 255u),
f32((value>>u32(16)) & 255u),
f32((value>>u32(24)) & 255u));return components*vec4f(2./255.)-vec4f(1.);}
fn computeSH(splat: Splat,color: vec3f,dir: vec3f)->vec3f
{var sh: array<vec3<f32>,16>;sh[0]=color;
#if SH_DEGREE>0
let sh00: vec4f=decompose(splat.sh0.x);let sh01: vec4f=decompose(splat.sh0.y);let sh02: vec4f=decompose(splat.sh0.z);sh[1]=vec3f(sh00.x,sh00.y,sh00.z);sh[2]=vec3f(sh00.w,sh01.x,sh01.y);sh[3]=vec3f(sh01.z,sh01.w,sh02.x);
#endif
#if SH_DEGREE>1
let sh03: vec4f=decompose(splat.sh0.w);let sh04: vec4f=decompose(splat.sh1.x);let sh05: vec4f=decompose(splat.sh1.y);sh[4]=vec3f(sh02.y,sh02.z,sh02.w);sh[5]=vec3f(sh03.x,sh03.y,sh03.z);sh[6]=vec3f(sh03.w,sh04.x,sh04.y);sh[7]=vec3f(sh04.z,sh04.w,sh05.x);sh[8]=vec3f(sh05.y,sh05.z,sh05.w);
#endif
#if SH_DEGREE>2
let sh06: vec4f=decompose(splat.sh1.z);let sh07: vec4f=decompose(splat.sh1.w);let sh08: vec4f=decompose(splat.sh2.x);let sh09: vec4f=decompose(splat.sh2.y);let sh10: vec4f=decompose(splat.sh2.z);let sh11: vec4f=decompose(splat.sh2.w);sh[9]=vec3f(sh06.x,sh06.y,sh06.z);sh[10]=vec3f(sh06.w,sh07.x,sh07.y);sh[11]=vec3f(sh07.z,sh07.w,sh08.x);sh[12]=vec3f(sh08.y,sh08.z,sh08.w);sh[13]=vec3f(sh09.x,sh09.y,sh09.z);sh[14]=vec3f(sh09.w,sh10.x,sh10.y);sh[15]=vec3f(sh10.z,sh10.w,sh11.x); 
#endif
return computeColorFromSHDegree(dir,sh);}
fn gaussianSplatting(
meshPos: vec2<f32>,
worldPos: vec3<f32>,
scale: vec2<f32>,
covA: vec3<f32>,
covB: vec3<f32>,
worldMatrix: mat4x4<f32>,
viewMatrix: mat4x4<f32>,
projectionMatrix: mat4x4<f32>,
focal: vec2f,
invViewport: vec2f
)->vec4f {let modelView=viewMatrix*worldMatrix;let camspace=viewMatrix*vec4f(worldPos,1.0);let pos2d=projectionMatrix*camspace;let bounds=1.2*pos2d.w;if (pos2d.z<0. || pos2d.x<-bounds || pos2d.x>bounds || pos2d.y<-bounds || pos2d.y>bounds) {return vec4f(0.0,0.0,2.0,1.0);}
let Vrk=mat3x3<f32>(
covA.x,covA.y,covA.z,
covA.y,covB.x,covB.y,
covA.z,covB.y,covB.z
);let J=mat3x3<f32>(
focal.x/camspace.z,0.0,-(focal.x*camspace.x)/(camspace.z*camspace.z),
0.0,focal.y/camspace.z,-(focal.y*camspace.y)/(camspace.z*camspace.z),
0.0,0.0,0.0
);let invy=mat3x3<f32>(
1.0,0.0,0.0,
0.0,-1.0,0.0,
0.0,0.0,1.0
);let T=invy*transpose(mat3x3<f32>(
modelView[0].xyz,
modelView[1].xyz,
modelView[2].xyz))*J;let cov2d=transpose(T)*Vrk*T;let mid=(cov2d[0][0]+cov2d[1][1])/2.0;let radius=length(vec2<f32>((cov2d[0][0]-cov2d[1][1])/2.0,cov2d[0][1]));let lambda1=mid+radius;let lambda2=mid-radius;if (lambda2<0.0) {return vec4f(0.0,0.0,2.0,1.0);}
let diagonalVector=normalize(vec2<f32>(cov2d[0][1],lambda1-cov2d[0][0]));let majorAxis=min(sqrt(2.0*lambda1),1024.0)*diagonalVector;let minorAxis=min(sqrt(2.0*lambda2),1024.0)*vec2<f32>(diagonalVector.y,-diagonalVector.x);let vCenter=vec2<f32>(pos2d.x,pos2d.y);return vec4f(
vCenter+((meshPos.x*majorAxis+meshPos.y*minorAxis)*invViewport*pos2d.w)*scale,
pos2d.z,
pos2d.w
);}
`;O.IncludesShadersStoreWGSL[gt]||(O.IncludesShadersStoreWGSL[gt]=hs);const Pe="gaussianSplattingVertexShader",It=`#include<sceneUboDeclaration>
#include<meshUboDeclaration>
#include<helperFunctions>
#include<clipPlaneVertexDeclaration>
#include<fogVertexDeclaration>
#include<logDepthDeclaration>
attribute splatIndex: f32;attribute position: vec2f;uniform invViewport: vec2f;uniform dataTextureSize: vec2f;uniform focal: vec2f;var covariancesATexture: texture_2d<f32>;var covariancesBTexture: texture_2d<f32>;var centersTexture: texture_2d<f32>;var colorsTexture: texture_2d<f32>;
#if SH_DEGREE>0
var shTexture0: texture_2d<u32>;
#endif
#if SH_DEGREE>1
var shTexture1: texture_2d<u32>;
#endif
#if SH_DEGREE>2
var shTexture2: texture_2d<u32>;
#endif
varying vColor: vec4f;varying vPosition: vec2f;
#include<gaussianSplatting>
@vertex
fn main(input : VertexInputs)->FragmentInputs {var splat: Splat=readSplat(input.splatIndex,uniforms.dataTextureSize);var covA: vec3f=splat.covA.xyz;var covB: vec3f=vec3f(splat.covA.w,splat.covB.xy);let worldPos: vec4f=mesh.world*vec4f(splat.center.xyz,1.0);vertexOutputs.vPosition=input.position;
#if SH_DEGREE>0
let worldRot: mat3x3f= mat3x3f(mesh.world[0].xyz,mesh.world[1].xyz,mesh.world[2].xyz);let normWorldRot: mat3x3f=inverseMat3(worldRot);var dir: vec3f=normalize(normWorldRot*(worldPos.xyz-scene.vEyePosition.xyz));dir*=vec3f(1.,1.,-1.); 
vertexOutputs.vColor=vec4f(computeSH(splat,splat.color.xyz,dir),1.0);
#else
vertexOutputs.vColor=splat.color;
#endif
vertexOutputs.position=gaussianSplatting(input.position,worldPos.xyz,vec2f(1.0,1.0),covA,covB,mesh.world,scene.view,scene.projection,uniforms.focal,uniforms.invViewport);
#include<clipPlaneVertex>
#include<fogVertex>
#include<logDepthVertex>
}
`;O.ShadersStoreWGSL[Pe]||(O.ShadersStoreWGSL[Pe]=It);const fs={name:Pe,shader:It},ds=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingVertexShaderWGSL:fs},Symbol.toStringTag,{value:"Module"}));class _s extends Zt{constructor(){super(),this.FOG=!1,this.THIN_INSTANCES=!0,this.LOGARITHMICDEPTH=!1,this.CLIPPLANE=!1,this.CLIPPLANE2=!1,this.CLIPPLANE3=!1,this.CLIPPLANE4=!1,this.CLIPPLANE5=!1,this.CLIPPLANE6=!1,this.SH_DEGREE=0,this.rebuild()}}class le extends Dt{constructor(e,s){super(e,s),this.backFaceCulling=!1}get hasRenderTargetTextures(){return!1}needAlphaTesting(){return!1}needAlphaBlending(){return!0}isReadyForSubMesh(e,s){const i=s._drawWrapper;if(i.effect&&this.isFrozen&&i._wasPreviouslyReady&&i._wasPreviouslyUsingInstances===!0)return!0;s.materialDefines||(s.materialDefines=new _s);const o=this.getScene(),n=s.materialDefines;if(this._isReadyForSubMesh(s))return!0;const h=o.getEngine();if(Rt(e,o,this._useLogarithmicDepth,this.pointsCloud,this.fogEnabled,!1,n),Mt(o,h,this,n,!0,null,!0),kt(e,n,!1,!1),(h.version>1||h.isWebGPU)&&(n.SH_DEGREE=e.shDegree),n.isDirty){n.markAsProcessed(),o.resetCachedMaterial();const d=[X.PositionKind,"splatIndex"];Ut(d,n);const a=["world","view","projection","vFogInfos","vFogColor","logarithmicDepthConstant","invViewport","dataTextureSize","focal","vEyePosition"],u=["covariancesATexture","covariancesBTexture","centersTexture","colorsTexture","shTexture0","shTexture1","shTexture2"],l=["Scene","Mesh"];Bt({uniformsNames:a,uniformBuffersNames:l,samplers:u,defines:n}),Ft(a);const f=n.toString(),_=o.getEngine().createEffect("gaussianSplatting",{attributes:d,uniformsNames:a,uniformBuffersNames:l,samplers:u,defines:f,onCompiled:this.onCompiled,onError:this.onError,indexParameters:{},shaderLanguage:this._shaderLanguage,extraInitializationsAsync:async()=>{this._shaderLanguage===1?await Promise.all([we(()=>Promise.resolve().then(()=>us),void 0,import.meta.url),we(()=>Promise.resolve().then(()=>ds),void 0,import.meta.url)]):await Promise.all([we(()=>Promise.resolve().then(()=>ss),void 0,import.meta.url),we(()=>Promise.resolve().then(()=>as),void 0,import.meta.url)])}},h);s.setEffect(_,n,this._materialContext)}return!s.effect||!s.effect.isReady()?!1:(n._renderId=o.getRenderId(),i._wasPreviouslyReady=!0,i._wasPreviouslyUsingInstances=!0,!0)}static BindEffect(e,s,r){var l,f;const i=r.getEngine(),o=r.activeCamera,n=i.getRenderWidth(),h=i.getRenderHeight(),d=((l=o==null?void 0:o.rigParent)==null?void 0:l.rigCameras.length)||1;s.setFloat2("invViewport",1/(n/d),1/h);let a=1e3;if(o){const _=o.getProjectionMatrix().m[5];o.fovMode==Ot.FOVMODE_VERTICAL_FIXED?a=h*_/2:a=n*_/2}s.setFloat2("focal",a,a);const u=e;if(u.covariancesATexture){const _=u.covariancesATexture.getSize();if(s.setFloat2("dataTextureSize",_.width,_.height),s.setTexture("covariancesATexture",u.covariancesATexture),s.setTexture("covariancesBTexture",u.covariancesBTexture),s.setTexture("centersTexture",u.centersTexture),s.setTexture("colorsTexture",u.colorsTexture),u.shTextures)for(let x=0;x<((f=u.shTextures)==null?void 0:f.length);x++)s.setTexture(`shTexture${x}`,u.shTextures[x])}}bindForSubMesh(e,s,r){const i=this.getScene(),o=r.materialDefines;if(!o)return;const n=r.effect;if(!n)return;this._activeEffect=n,s.getMeshUniformBuffer().bindToEffect(n,"Mesh"),s.transferToEffect(e),this._mustRebind(i,n,r,s.visibility)?(this.bindView(n),this.bindViewProjection(n),le.BindEffect(s,this._activeEffect,i),Pt(n,this,i)):i.getEngine()._features.needToAlwaysBindUniformBuffers&&(this._needToBindSceneUbo=!0),Nt(i,s,n),this.useLogarithmicDepth&&Wt(o,n,i),this._afterBind(s,this._activeEffect,r)}clone(e){return dt.Clone(()=>new le(e,this.getScene()),this)}serialize(){const e=super.serialize();return e.customType="BABYLON.GaussianSplattingMaterial",e}getClassName(){return"GaussianSplattingMaterial"}static Parse(e,s,r){return dt.Parse(()=>new le(e.name,s),e,s,r)}}Ht("BABYLON.GaussianSplattingMaterial",le);const ps=Xt,$={...Gt,TwoPi:Math.PI*2,Sign:Math.sign,Log2:Math.log2,HCF:ps},K=(t,e)=>{const s=(1<<e)-1;return(t&s)/s},yt=(t,e)=>{e.x=K(t>>>21,11),e.y=K(t>>>11,10),e.z=K(t,11)},xs=(t,e)=>{e[0]=K(t>>>24,8)*255,e[1]=K(t>>>16,8)*255,e[2]=K(t>>>8,8)*255,e[3]=K(t,8)*255},ms=(t,e)=>{const s=1/(Math.sqrt(2)*.5),r=(K(t>>>20,10)-.5)*s,i=(K(t>>>10,10)-.5)*s,o=(K(t,10)-.5)*s,n=Math.sqrt(1-(r*r+i*i+o*o));switch(t>>>30){case 0:e.set(n,r,i,o);break;case 1:e.set(r,n,i,o);break;case 2:e.set(r,i,n,o);break;case 3:e.set(r,i,o,n);break}};var St;(function(t){t[t.FLOAT=0]="FLOAT",t[t.INT=1]="INT",t[t.UINT=2]="UINT",t[t.DOUBLE=3]="DOUBLE",t[t.UCHAR=4]="UCHAR",t[t.UNDEFINED=5]="UNDEFINED"})(St||(St={}));var Ct;(function(t){t[t.MIN_X=0]="MIN_X",t[t.MIN_Y=1]="MIN_Y",t[t.MIN_Z=2]="MIN_Z",t[t.MAX_X=3]="MAX_X",t[t.MAX_Y=4]="MAX_Y",t[t.MAX_Z=5]="MAX_Z",t[t.MIN_SCALE_X=6]="MIN_SCALE_X",t[t.MIN_SCALE_Y=7]="MIN_SCALE_Y",t[t.MIN_SCALE_Z=8]="MIN_SCALE_Z",t[t.MAX_SCALE_X=9]="MAX_SCALE_X",t[t.MAX_SCALE_Y=10]="MAX_SCALE_Y",t[t.MAX_SCALE_Z=11]="MAX_SCALE_Z",t[t.PACKED_POSITION=12]="PACKED_POSITION",t[t.PACKED_ROTATION=13]="PACKED_ROTATION",t[t.PACKED_SCALE=14]="PACKED_SCALE",t[t.PACKED_COLOR=15]="PACKED_COLOR",t[t.X=16]="X",t[t.Y=17]="Y",t[t.Z=18]="Z",t[t.SCALE_0=19]="SCALE_0",t[t.SCALE_1=20]="SCALE_1",t[t.SCALE_2=21]="SCALE_2",t[t.DIFFUSE_RED=22]="DIFFUSE_RED",t[t.DIFFUSE_GREEN=23]="DIFFUSE_GREEN",t[t.DIFFUSE_BLUE=24]="DIFFUSE_BLUE",t[t.OPACITY=25]="OPACITY",t[t.F_DC_0=26]="F_DC_0",t[t.F_DC_1=27]="F_DC_1",t[t.F_DC_2=28]="F_DC_2",t[t.F_DC_3=29]="F_DC_3",t[t.ROT_0=30]="ROT_0",t[t.ROT_1=31]="ROT_1",t[t.ROT_2=32]="ROT_2",t[t.ROT_3=33]="ROT_3",t[t.MIN_COLOR_R=34]="MIN_COLOR_R",t[t.MIN_COLOR_G=35]="MIN_COLOR_G",t[t.MIN_COLOR_B=36]="MIN_COLOR_B",t[t.MAX_COLOR_R=37]="MAX_COLOR_R",t[t.MAX_COLOR_G=38]="MAX_COLOR_G",t[t.MAX_COLOR_B=39]="MAX_COLOR_B",t[t.SH_0=40]="SH_0",t[t.SH_1=41]="SH_1",t[t.SH_2=42]="SH_2",t[t.SH_3=43]="SH_3",t[t.SH_4=44]="SH_4",t[t.SH_5=45]="SH_5",t[t.SH_6=46]="SH_6",t[t.SH_7=47]="SH_7",t[t.SH_8=48]="SH_8",t[t.SH_9=49]="SH_9",t[t.SH_10=50]="SH_10",t[t.SH_11=51]="SH_11",t[t.SH_12=52]="SH_12",t[t.SH_13=53]="SH_13",t[t.SH_14=54]="SH_14",t[t.SH_15=55]="SH_15",t[t.SH_16=56]="SH_16",t[t.SH_17=57]="SH_17",t[t.SH_18=58]="SH_18",t[t.SH_19=59]="SH_19",t[t.SH_20=60]="SH_20",t[t.SH_21=61]="SH_21",t[t.SH_22=62]="SH_22",t[t.SH_23=63]="SH_23",t[t.SH_24=64]="SH_24",t[t.SH_25=65]="SH_25",t[t.SH_26=66]="SH_26",t[t.SH_27=67]="SH_27",t[t.SH_28=68]="SH_28",t[t.SH_29=69]="SH_29",t[t.SH_30=70]="SH_30",t[t.SH_31=71]="SH_31",t[t.SH_32=72]="SH_32",t[t.SH_33=73]="SH_33",t[t.SH_34=74]="SH_34",t[t.SH_35=75]="SH_35",t[t.SH_36=76]="SH_36",t[t.SH_37=77]="SH_37",t[t.SH_38=78]="SH_38",t[t.SH_39=79]="SH_39",t[t.SH_40=80]="SH_40",t[t.SH_41=81]="SH_41",t[t.SH_42=82]="SH_42",t[t.SH_43=83]="SH_43",t[t.SH_44=84]="SH_44",t[t.UNDEFINED=85]="UNDEFINED"})(Ct||(Ct={}));class E extends Ne{get shDegree(){return this._shDegree}get splatsData(){return this._splatsData}get covariancesATexture(){return this._covariancesATexture}get covariancesBTexture(){return this._covariancesBTexture}get centersTexture(){return this._centersTexture}get colorsTexture(){return this._colorsTexture}get shTextures(){return this._shTextures}set material(e){this._material=e,this._material.backFaceCulling=!0,this._material.cullBackFaces=!1,e.resetDrawCache()}get material(){return this._material}constructor(e,s=null,r=null,i=!1){super(e,r),this._vertexCount=0,this._worker=null,this._frameIdLastUpdate=-1,this._modelViewMatrix=Te.Identity(),this._canPostToWorker=!0,this._readyToDisplay=!1,this._covariancesATexture=null,this._covariancesBTexture=null,this._centersTexture=null,this._colorsTexture=null,this._splatPositions=null,this._splatIndex=null,this._shTextures=null,this._splatsData=null,this._sh=null,this._keepInRam=!1,this._delayedTextureUpdate=null,this._oldDirection=new T,this._useRGBACovariants=!1,this._material=null,this._tmpCovariances=[0,0,0,0,0,0],this._sortIsDirty=!1,this._shDegree=0;const o=new We;o.positions=[-3,-2,0,3,-2,0,0,4,0],o.indices=[0,1,2],o.applyToMesh(this),this.subMeshes=[],new jt(0,0,3,0,3,this),this.setEnabled(!1),this._useRGBACovariants=!this.getEngine().isWebGPU&&this.getEngine().version===1,this._keepInRam=i,s&&this.loadFileAsync(s),this._material=new le(this.name+"_material",this._scene)}getClassName(){return"GaussianSplattingMesh"}getTotalVertices(){return this._vertexCount}isReady(e=!1){return super.isReady(e,!0)?this._readyToDisplay?!0:(this._postToWorker(!0),!1):!1}_postToWorker(e=!1){const s=this.getScene().getFrameId();if((e||s!==this._frameIdLastUpdate)&&this._worker&&this._scene.activeCamera&&this._canPostToWorker){const r=this._scene.activeCamera.getViewMatrix();this.getWorldMatrix().multiplyToRef(r,this._modelViewMatrix),r.invertToRef(W.Matrix[0]),this.getWorldMatrix().multiplyToRef(W.Matrix[0],W.Matrix[1]),T.TransformNormalToRef(T.Forward(this._scene.useRightHandedSystem),W.Matrix[1],W.Vector3[2]),W.Vector3[2].normalize();const i=T.Dot(W.Vector3[2],this._oldDirection);(e||Math.abs(i-1)>=.01)&&(this._oldDirection.copyFrom(W.Vector3[2]),this._frameIdLastUpdate=s,this._canPostToWorker=!1,this._worker.postMessage({view:this._modelViewMatrix.m,depthMix:this._depthMix,useRightHandedSystem:this._scene.useRightHandedSystem},[this._depthMix.buffer]))}}render(e,s,r){return this._postToWorker(),super.render(e,s,r)}static _TypeNameToEnum(e){switch(e){case"float":return 0;case"int":return 1;case"uint":return 2;case"double":return 3;case"uchar":return 4}return 5}static _ValueNameToEnum(e){switch(e){case"min_x":return 0;case"min_y":return 1;case"min_z":return 2;case"max_x":return 3;case"max_y":return 4;case"max_z":return 5;case"min_scale_x":return 6;case"min_scale_y":return 7;case"min_scale_z":return 8;case"max_scale_x":return 9;case"max_scale_y":return 10;case"max_scale_z":return 11;case"packed_position":return 12;case"packed_rotation":return 13;case"packed_scale":return 14;case"packed_color":return 15;case"x":return 16;case"y":return 17;case"z":return 18;case"scale_0":return 19;case"scale_1":return 20;case"scale_2":return 21;case"diffuse_red":case"red":return 22;case"diffuse_green":case"green":return 23;case"diffuse_blue":case"blue":return 24;case"f_dc_0":return 26;case"f_dc_1":return 27;case"f_dc_2":return 28;case"f_dc_3":return 29;case"opacity":return 25;case"rot_0":return 30;case"rot_1":return 31;case"rot_2":return 32;case"rot_3":return 33;case"min_r":return 34;case"min_g":return 35;case"min_b":return 36;case"max_r":return 37;case"max_g":return 38;case"max_b":return 39;case"f_rest_0":return 40;case"f_rest_1":return 41;case"f_rest_2":return 42;case"f_rest_3":return 43;case"f_rest_4":return 44;case"f_rest_5":return 45;case"f_rest_6":return 46;case"f_rest_7":return 47;case"f_rest_8":return 48;case"f_rest_9":return 49;case"f_rest_10":return 50;case"f_rest_11":return 51;case"f_rest_12":return 52;case"f_rest_13":return 53;case"f_rest_14":return 54;case"f_rest_15":return 55;case"f_rest_16":return 56;case"f_rest_17":return 57;case"f_rest_18":return 58;case"f_rest_19":return 59;case"f_rest_20":return 60;case"f_rest_21":return 61;case"f_rest_22":return 62;case"f_rest_23":return 63;case"f_rest_24":return 64;case"f_rest_25":return 65;case"f_rest_26":return 66;case"f_rest_27":return 67;case"f_rest_28":return 68;case"f_rest_29":return 69;case"f_rest_30":return 70;case"f_rest_31":return 71;case"f_rest_32":return 72;case"f_rest_33":return 73;case"f_rest_34":return 74;case"f_rest_35":return 75;case"f_rest_36":return 76;case"f_rest_37":return 77;case"f_rest_38":return 78;case"f_rest_39":return 79;case"f_rest_40":return 80;case"f_rest_41":return 81;case"f_rest_42":return 82;case"f_rest_43":return 83;case"f_rest_44":return 84}return 85}static ParseHeader(e){const s=new Uint8Array(e),r=new TextDecoder().decode(s.slice(0,1024*10)),i=`end_header
`,o=r.indexOf(i);if(o<0||!r)return null;const n=parseInt(/element vertex (\d+)\n/.exec(r)[1]),h=/element chunk (\d+)\n/.exec(r);let d=0;h&&(d=parseInt(h[1]));let a=0,u=0;const l={double:8,int:4,uint:4,float:4,short:2,ushort:2,uchar:1,list:0};let f;(function(m){m[m.Vertex=0]="Vertex",m[m.Chunk=1]="Chunk"})(f||(f={}));let _=1;const x=[],v=[],p=r.slice(0,o).split(`
`);let S=0;for(const m of p)if(m.startsWith("property ")){const[,c,y]=m.split(" "),z=E._ValueNameToEnum(y);z>=84?S=3:z>=64?S=2:z>=48&&(S=1);const U=E._TypeNameToEnum(c);_==1?(v.push({value:z,type:U,offset:u}),u+=l[c]):_==0&&(x.push({value:z,type:U,offset:a}),a+=l[c]),l[c]||_e.Warn(`Unsupported property type: ${c}.`)}else if(m.startsWith("element ")){const[,c]=m.split(" ");c=="chunk"?_=1:c=="vertex"&&(_=0)}const A=new DataView(e,o+i.length),w=new ArrayBuffer(E._RowOutputLength*n);let g=null,b=0;return S&&(b=((S+1)*(S+1)-1)*3,g=new ArrayBuffer(b*n)),{vertexCount:n,chunkCount:d,rowVertexLength:a,rowChunkLength:u,vertexProperties:x,chunkProperties:v,dataView:A,buffer:w,shDegree:S,shCoefficientCount:b,shBuffer:g}}static _GetCompressedChunks(e,s){if(!e.chunkCount)return null;const r=e.dataView,i=new Array(e.chunkCount);for(let o=0;o<e.chunkCount;o++){const n={min:new T,max:new T,minScale:new T,maxScale:new T,minColor:new T(0,0,0),maxColor:new T(1,1,1)};i[o]=n;for(let h=0;h<e.chunkProperties.length;h++){const d=e.chunkProperties[h];let a;switch(d.type){case 0:a=r.getFloat32(d.offset+s.value,!0);break;default:continue}switch(d.value){case 0:n.min.x=a;break;case 1:n.min.y=a;break;case 2:n.min.z=a;break;case 3:n.max.x=a;break;case 4:n.max.y=a;break;case 5:n.max.z=a;break;case 6:n.minScale.x=a;break;case 7:n.minScale.y=a;break;case 8:n.minScale.z=a;break;case 9:n.maxScale.x=a;break;case 10:n.maxScale.y=a;break;case 11:n.maxScale.z=a;break;case 34:n.minColor.x=a;break;case 35:n.minColor.y=a;break;case 36:n.minColor.z=a;break;case 37:n.maxColor.x=a;break;case 38:n.maxColor.y=a;break;case 39:n.maxColor.z=a;break}}s.value+=e.rowChunkLength}return i}static _GetSplat(e,s,r,i){const o=W.Quaternion[0],n=W.Vector3[0],h=E._RowOutputLength,d=e.buffer,a=e.dataView,u=new Float32Array(d,s*h,3),l=new Float32Array(d,s*h+12,3),f=new Uint8ClampedArray(d,s*h+24,4),_=new Uint8ClampedArray(d,s*h+28,4);let x=null;e.shBuffer&&(x=new Uint8ClampedArray(e.shBuffer,s*e.shCoefficientCount,e.shCoefficientCount));const v=s>>8;let p=255,S=0,A=0,w=0;const g=[];for(let b=0;b<e.vertexProperties.length;b++){const m=e.vertexProperties[b];let c;switch(m.type){case 0:c=a.getFloat32(i.value+m.offset,!0);break;case 1:c=a.getInt32(i.value+m.offset,!0);break;case 2:c=a.getUint32(i.value+m.offset,!0);break;case 3:c=a.getFloat64(i.value+m.offset,!0);break;case 4:c=a.getUint8(i.value+m.offset);break;default:continue}switch(m.value){case 12:{const y=r[v];yt(c,n),u[0]=$.Lerp(y.min.x,y.max.x,n.x),u[1]=-$.Lerp(y.min.y,y.max.y,n.y),u[2]=$.Lerp(y.min.z,y.max.z,n.z)}break;case 13:ms(c,o),p=o.w,S=o.z,A=o.y,w=o.x;break;case 14:{const y=r[v];yt(c,n),l[0]=Math.exp($.Lerp(y.minScale.x,y.maxScale.x,n.x)),l[1]=Math.exp($.Lerp(y.minScale.y,y.maxScale.y,n.y)),l[2]=Math.exp($.Lerp(y.minScale.z,y.maxScale.z,n.z))}break;case 15:{const y=r[v];xs(c,f),f[0]=$.Lerp(y.minColor.x,y.maxColor.x,f[0]/255)*255,f[1]=$.Lerp(y.minColor.y,y.maxColor.y,f[1]/255)*255,f[2]=$.Lerp(y.minColor.z,y.maxColor.z,f[2]/255)*255}break;case 16:u[0]=c;break;case 17:u[1]=-c;break;case 18:u[2]=-c;break;case 19:l[0]=Math.exp(c);break;case 20:l[1]=Math.exp(c);break;case 21:l[2]=Math.exp(c);break;case 22:f[0]=c;break;case 23:f[1]=c;break;case 24:f[2]=c;break;case 26:f[0]=(.5+E._SH_C0*c)*255;break;case 27:f[1]=(.5+E._SH_C0*c)*255;break;case 28:f[2]=(.5+E._SH_C0*c)*255;break;case 29:f[3]=(.5+E._SH_C0*c)*255;break;case 25:f[3]=1/(1+Math.exp(-c))*255;break;case 30:p=c;break;case 31:S=c;break;case 32:A=c;break;case 33:w=c;break}if(x&&m.value>=40&&m.value<=84){const y=$.Clamp(c*127.5+127.5,0,255),z=m.value-40;g[z]=y}}if(x){const b=e.shDegree==1?3:e.shDegree==2?8:15;for(let m=0;m<b;m++)x[m*3+0]=g[m],x[m*3+1]=g[m+b],x[m*3+2]=g[m+b*2]}o.set(S,A,w,p),o.normalize(),_[0]=o.w*128+128,_[1]=o.x*128+128,_[2]=o.y*128+128,_[3]=o.z*128+128,i.value+=e.rowVertexLength}static*ConvertPLYWithSHToSplat(e,s=!1){const r=E.ParseHeader(e);if(!r)return{buffer:e};const i={value:0},o=E._GetCompressedChunks(r,i);for(let h=0;h<r.vertexCount;h++)E._GetSplat(r,h,o,i),h%E._PlyConversionBatchSize===0&&s&&(yield);let n=null;if(r.shDegree&&r.shBuffer){const h=Math.ceil(r.shCoefficientCount/16);let d=0;const a=new Uint8Array(r.shBuffer);n=[];const u=r.vertexCount,l=Tt.LastCreatedEngine;if(l){const f=l.getCaps().maxTextureSize,_=Math.ceil(u/f);for(let x=0;x<h;x++){const v=new Uint8Array(_*f*4*4);n.push(v)}for(let x=0;x<u;x++)for(let v=0;v<r.shCoefficientCount;v++){const p=a[d++],S=Math.floor(v/16),A=n[S],w=v%16,g=x*16;A[w+g]=p}}}return{buffer:r.buffer,sh:n}}static*ConvertPLYToSplat(e,s=!1){const r=E.ParseHeader(e);if(!r)return e;const i={value:0},o=E._GetCompressedChunks(r,i);for(let n=0;n<r.vertexCount;n++)E._GetSplat(r,n,o,i),n%E._PlyConversionBatchSize===0&&s&&(yield);return r.buffer}static async ConvertPLYToSplatAsync(e){return Re(E.ConvertPLYToSplat(e,!0),Me())}static async ConvertPLYWithSHToSplatAsync(e){return Re(E.ConvertPLYWithSHToSplat(e,!0),Me())}loadDataAsync(e){return this.updateDataAsync(e)}loadFileAsync(e){return $t.LoadFileAsync(e,!0).then(async s=>{E.ConvertPLYWithSHToSplatAsync(s).then(r=>{this.updateDataAsync(r.buffer,r.sh)})})}dispose(e){var s,r,i,o,n;(s=this._covariancesATexture)==null||s.dispose(),(r=this._covariancesBTexture)==null||r.dispose(),(i=this._centersTexture)==null||i.dispose(),(o=this._colorsTexture)==null||o.dispose(),this._shTextures&&this._shTextures.forEach(h=>{h.dispose()}),this._covariancesATexture=null,this._covariancesBTexture=null,this._centersTexture=null,this._colorsTexture=null,this._shTextures=null,(n=this._worker)==null||n.terminate(),this._worker=null,super.dispose(e,!0)}_copyTextures(e){var s,r,i,o;this._covariancesATexture=(s=e.covariancesATexture)==null?void 0:s.clone(),this._covariancesBTexture=(r=e.covariancesBTexture)==null?void 0:r.clone(),this._centersTexture=(i=e.centersTexture)==null?void 0:i.clone(),this._colorsTexture=(o=e.colorsTexture)==null?void 0:o.clone(),e._shTextures&&(this._shTextures=[],this._shTextures.forEach(n=>{var h;(h=this._shTextures)==null||h.push(n.clone())}))}clone(e=""){const s=new E(e,void 0,this.getScene());s._copySource(this),s.makeGeometryUnique(),s._vertexCount=this._vertexCount,s._copyTextures(this),s._modelViewMatrix=Te.Identity(),s._splatPositions=this._splatPositions,s._readyToDisplay=!1,s._instanciateWorker();const r=this.getBoundingInfo();return s.getBoundingInfo().reConstruct(r.minimum,r.maximum,this.getWorldMatrix()),s.forcedInstanceCount=s._vertexCount,s.setEnabled(!0),s}_makeSplat(e,s,r,i,o,n,h,d){const a=W.Matrix[0],u=W.Matrix[1],l=W.Quaternion[0],f=this._useRGBACovariants?4:2,_=s[8*e+0],x=-s[8*e+1],v=s[8*e+2];this._splatPositions[4*e+0]=_,this._splatPositions[4*e+1]=x,this._splatPositions[4*e+2]=v,h.minimizeInPlaceFromFloats(_,x,v),d.maximizeInPlaceFromFloats(_,x,v),l.set((r[32*e+28+1]-127.5)/127.5,(r[32*e+28+2]-127.5)/127.5,(r[32*e+28+3]-127.5)/127.5,-(r[32*e+28+0]-127.5)/127.5),l.toRotationMatrix(a),Te.ScalingToRef(s[8*e+3+0]*2,s[8*e+3+1]*2,s[8*e+3+2]*2,u);const p=a.multiplyToRef(u,W.Matrix[0]).m,S=this._tmpCovariances;S[0]=p[0]*p[0]+p[1]*p[1]+p[2]*p[2],S[1]=p[0]*p[4]+p[1]*p[5]+p[2]*p[6],S[2]=p[0]*p[8]+p[1]*p[9]+p[2]*p[10],S[3]=p[4]*p[4]+p[5]*p[5]+p[6]*p[6],S[4]=p[4]*p[8]+p[5]*p[9]+p[6]*p[10],S[5]=p[8]*p[8]+p[9]*p[9]+p[10]*p[10];let A=-1e4;for(let g=0;g<6;g++)A=Math.max(A,Math.abs(S[g]));this._splatPositions[4*e+3]=A;const w=A;i[e*4+0]=ae(S[0]/w),i[e*4+1]=ae(S[1]/w),i[e*4+2]=ae(S[2]/w),i[e*4+3]=ae(S[3]/w),o[e*f+0]=ae(S[4]/w),o[e*f+1]=ae(S[5]/w),n[e*4+0]=r[32*e+24+0],n[e*4+1]=r[32*e+24+1],n[e*4+2]=r[32*e+24+2],n[e*4+3]=r[32*e+24+3]}_updateTextures(e,s,r,i){const o=this._getTextureSize(this._vertexCount),n=(u,l,f,_)=>new be(u,l,f,_,this._scene,!1,!1,2,1),h=(u,l,f,_)=>new be(u,l,f,_,this._scene,!1,!1,2,0),d=(u,l,f,_)=>new be(u,l,f,_,this._scene,!1,!1,1,7),a=(u,l,f,_)=>new be(u,l,f,_,this._scene,!1,!1,2,2);if(this._covariancesATexture){this._delayedTextureUpdate={covA:e,covB:s,colors:r,centers:this._splatPositions,sh:i};const u=Float32Array.from(this._splatPositions),l=this._vertexCount;this._worker.postMessage({positions:u,vertexCount:l},[u.buffer]),this._postToWorker(!0)}else this._covariancesATexture=a(e,o.x,o.y,5),this._covariancesBTexture=a(s,o.x,o.y,this._useRGBACovariants?5:7),this._centersTexture=n(this._splatPositions,o.x,o.y,5),this._colorsTexture=h(r,o.x,o.y,5),i&&(this._shTextures=[],i.forEach(u=>{const l=new Uint32Array(u.buffer),f=d(l,o.x,o.y,11);f.wrapU=0,f.wrapV=0,this._shTextures.push(f)})),this._instanciateWorker()}*_updateData(e,s,r){this._covariancesATexture||(this._readyToDisplay=!1);const i=new Uint8Array(e),o=new Float32Array(i.buffer);this._keepInRam&&(this._splatsData=e,r&&(this._sh=r));const n=i.length/E._RowOutputLength;n!=this._vertexCount&&this._updateSplatIndexBuffer(n),this._vertexCount=n,this._shDegree=r?r.length:0;const h=this._getTextureSize(n),d=h.x*h.y,a=E.ProgressiveUpdateAmount??h.y,u=h.x*a;this._splatPositions=new Float32Array(4*d);const l=new Uint16Array(d*4),f=new Uint16Array((this._useRGBACovariants?4:2)*d),_=new Uint8Array(d*4),x=new T(Number.MAX_VALUE,Number.MAX_VALUE,Number.MAX_VALUE),v=new T(-Number.MAX_VALUE,-Number.MAX_VALUE,-Number.MAX_VALUE);if(E.ProgressiveUpdateAmount){this._updateTextures(l,f,_,r),this.setEnabled(!0);const p=Math.ceil(h.y/a);for(let w=0;w<p;w++){const g=w*a,b=g*h.x;for(let m=0;m<u;m++)this._makeSplat(b+m,o,i,l,f,_,x,v);this._updateSubTextures(this._splatPositions,l,f,_,g,Math.min(a,h.y-g)),this.getBoundingInfo().reConstruct(x,v,this.getWorldMatrix()),s&&(yield)}const S=Float32Array.from(this._splatPositions),A=this._vertexCount;this._worker.postMessage({positions:S,vertexCount:A},[S.buffer]),this._sortIsDirty=!0}else{for(let p=0;p<n;p++)this._makeSplat(p,o,i,l,f,_,x,v),s&&p%E._SplatBatchSize===0&&(yield);this._updateTextures(l,f,_,r),this.getBoundingInfo().reConstruct(x,v,this.getWorldMatrix()),this.setEnabled(!0)}this._postToWorker(!0)}async updateDataAsync(e,s){return Re(this._updateData(e,!0,s),Me())}updateData(e,s){Vt(this._updateData(e,!1,s))}refreshBoundingInfo(){return this.thinInstanceRefreshBoundingInfo(!1),this}_updateSplatIndexBuffer(e){(!this._splatIndex||e>this._splatIndex.length)&&(this._splatIndex=new Float32Array(e),this.thinInstanceSetBuffer("splatIndex",this._splatIndex,1,!1)),this.forcedInstanceCount=e}_updateSubTextures(e,s,r,i,o,n,h){const d=(S,A,w,g,b)=>{this.getEngine().updateTextureData(S.getInternalTexture(),A,0,g,w,b,0,0,!1)},a=this._getTextureSize(this._vertexCount),u=this._useRGBACovariants?4:2,l=o*a.x,f=n*a.x,_=new Uint16Array(s.buffer,l*4*Uint16Array.BYTES_PER_ELEMENT,f*4),x=new Uint16Array(r.buffer,l*u*Uint16Array.BYTES_PER_ELEMENT,f*u),v=new Uint8Array(i.buffer,l*4,f*4),p=new Float32Array(e.buffer,l*4*Float32Array.BYTES_PER_ELEMENT,f*4);if(d(this._covariancesATexture,_,a.x,o,n),d(this._covariancesBTexture,x,a.x,o,n),d(this._centersTexture,p,a.x,o,n),d(this._colorsTexture,v,a.x,o,n),h)for(let S=0;S<h.length;S++){const w=new Uint8Array(this._sh[S].buffer,l*4,f*4);d(this._shTextures[S],w,a.x,o,n)}}_instanciateWorker(){var r;if(!this._vertexCount)return;this._updateSplatIndexBuffer(this._vertexCount),(r=this._worker)==null||r.terminate(),this._worker=new Worker(URL.createObjectURL(new Blob(["(",E._CreateWorker.toString(),")(self)"],{type:"application/javascript"}))),this._depthMix=new BigInt64Array(this._vertexCount);const e=Float32Array.from(this._splatPositions),s=this._vertexCount;this._worker.postMessage({positions:e,vertexCount:s},[e.buffer]),this._worker.onmessage=i=>{this._depthMix=i.data.depthMix;const o=new Uint32Array(i.data.depthMix.buffer);if(this._splatIndex)for(let n=0;n<this._vertexCount;n++)this._splatIndex[n]=o[2*n];if(this._delayedTextureUpdate){const n=this._getTextureSize(s);this._updateSubTextures(this._delayedTextureUpdate.centers,this._delayedTextureUpdate.covA,this._delayedTextureUpdate.covB,this._delayedTextureUpdate.colors,0,n.y,this._delayedTextureUpdate.sh),this._delayedTextureUpdate=null}this.thinInstanceBufferUpdated("splatIndex"),this._canPostToWorker=!0,this._readyToDisplay=!0,this._sortIsDirty&&(this._postToWorker(!0),this._sortIsDirty=!1)}}_getTextureSize(e){const s=this._scene.getEngine(),r=s.getCaps().maxTextureSize;let i=1;if(s.version===1&&!s.isWebGPU)for(;r*i<e;)i*=2;else i=Math.ceil(e/r);return i>r&&(_e.Error("GaussianSplatting texture size: ("+r+", "+i+"), maxTextureSize: "+r),i=r),new te(r,i)}}E._RowOutputLength=3*4+3*4+4+4;E._SH_C0=.28209479177387814;E._SplatBatchSize=327680;E._PlyConversionBatchSize=32768;E.ProgressiveUpdateAmount=0;E._CreateWorker=function(t){let e=0,s,r,i,o;t.onmessage=n=>{if(n.data.positions)s=n.data.positions,e=n.data.vertexCount;else{const h=n.data.view;if(!s||!h)throw new Error("positions or view is not defined!");r=n.data.depthMix,i=new Uint32Array(r.buffer),o=new Float32Array(r.buffer);for(let a=0;a<e;a++)i[2*a]=a;let d=-1;n.data.useRightHandedSystem&&(d=1);for(let a=0;a<e;a++)o[2*a+1]=1e4+(h[2]*s[4*a+0]+h[6]*s[4*a+1]+h[10]*s[4*a+2])*d;r.sort(),t.postMessage({depthMix:r},[r.buffer])}}};class vs{constructor(e,s,r,i,o){this.idx=0,this.color=new q(1,1,1,1),this.position=T.Zero(),this.rotation=T.Zero(),this.uv=new te(0,0),this.velocity=T.Zero(),this.pivot=T.Zero(),this.translateFromPivot=!1,this._pos=0,this._ind=0,this.groupId=0,this.idxInGroup=0,this._stillInvisible=!1,this._rotationMatrix=[1,0,0,0,1,0,0,0,1],this.parentId=null,this._globalPosition=T.Zero(),this.idx=e,this._group=s,this.groupId=r,this.idxInGroup=i,this._pcs=o}get size(){return this.size}set size(e){this.size=e}get quaternion(){return this.rotationQuaternion}set quaternion(e){this.rotationQuaternion=e}intersectsMesh(e,s){if(!e.hasBoundingInfo)return!1;if(!this._pcs.mesh)throw new Error("Point Cloud System doesnt contain the Mesh");if(s)return e.getBoundingInfo().boundingSphere.intersectsPoint(this.position.add(this._pcs.mesh.position));const r=e.getBoundingInfo().boundingBox,i=r.maximumWorld.x,o=r.minimumWorld.x,n=r.maximumWorld.y,h=r.minimumWorld.y,d=r.maximumWorld.z,a=r.minimumWorld.z,u=this.position.x+this._pcs.mesh.position.x,l=this.position.y+this._pcs.mesh.position.y,f=this.position.z+this._pcs.mesh.position.z;return o<=u&&u<=i&&h<=l&&l<=n&&a<=f&&f<=d}getRotationMatrix(e){let s;if(this.rotationQuaternion)s=this.rotationQuaternion;else{s=W.Quaternion[0];const r=this.rotation;Kt.RotationYawPitchRollToRef(r.y,r.x,r.z,s)}s.toRotationMatrix(e)}}class Ue{get groupID(){return this.groupId}set groupID(e){this.groupId=e}constructor(e,s){this.groupId=e,this._positionFunction=s}}var wt;(function(t){t[t.Color=2]="Color",t[t.UV=1]="UV",t[t.Random=0]="Random",t[t.Stated=3]="Stated"})(wt||(wt={}));class gs{get positions(){return this._positions32}get colors(){return this._colors32}get uvs(){return this._uvs32}constructor(e,s,r,i){this.particles=new Array,this.nbParticles=0,this.counter=0,this.vars={},this._promises=[],this._positions=new Array,this._indices=new Array,this._normals=new Array,this._colors=new Array,this._uvs=new Array,this._updatable=!0,this._isVisibilityBoxLocked=!1,this._alwaysVisible=!1,this._groups=new Array,this._groupCounter=0,this._computeParticleColor=!0,this._computeParticleTexture=!0,this._computeParticleRotation=!0,this._computeBoundingBox=!1,this._isReady=!1,this.name=e,this._size=s,this._scene=r||Tt.LastCreatedScene,i&&i.updatable!==void 0?this._updatable=i.updatable:this._updatable=!0}buildMeshAsync(e){return Promise.all(this._promises).then(()=>(this._isReady=!0,this._buildMesh(e)))}_buildMesh(e){this.nbParticles===0&&this.addPoints(1),this._positions32=new Float32Array(this._positions),this._uvs32=new Float32Array(this._uvs),this._colors32=new Float32Array(this._colors);const s=new We;s.set(this._positions32,X.PositionKind),this._uvs32.length>0&&s.set(this._uvs32,X.UVKind);let r=0;this._colors32.length>0&&(r=1,s.set(this._colors32,X.ColorKind));const i=new Ne(this.name,this._scene);s.applyToMesh(i,this._updatable),this.mesh=i,this._positions=null,this._uvs=null,this._colors=null,this._updatable||(this.particles.length=0);let o=e;return o||(o=new Yt("point cloud material",this._scene),o.emissiveColor=new Ce(r,r,r),o.disableLighting=!0,o.pointsCloud=!0,o.pointSize=this._size),i.material=o,new Promise(n=>n(i))}_addParticle(e,s,r,i){const o=new vs(e,s,r,i,this);return this.particles.push(o),o}_randomUnitVector(e){e.position=new T(Math.random(),Math.random(),Math.random()),e.color=new q(1,1,1,1)}_getColorIndicesForCoord(e,s,r,i){const o=e._groupImageData,n=r*(i*4)+s*4,h=[n,n+1,n+2,n+3],d=h[0],a=h[1],u=h[2],l=h[3],f=o[d],_=o[a],x=o[u],v=o[l];return new q(f/255,_/255,x/255,v)}_setPointsColorOrUV(e,s,r,i,o,n,h,d){d=d??0,r&&e.updateFacetData();const u=2*e.getBoundingInfo().boundingSphere.radius;let l=e.getVerticesData(X.PositionKind);const f=e.getIndices(),_=e.getVerticesData(X.UVKind+(d?d+1:"")),x=e.getVerticesData(X.ColorKind),v=T.Zero();e.computeWorldMatrix();const p=e.getWorldMatrix();if(!p.isIdentity()){l=l.slice(0);for(let N=0;N<l.length/3;N++)T.TransformCoordinatesFromFloatsToRef(l[3*N],l[3*N+1],l[3*N+2],p,v),l[3*N]=v.x,l[3*N+1]=v.y,l[3*N+2]=v.z}let S=0,A=0,w=0,g=0,b=0,m=0,c=0,y=0,z=0,U=0,B=0,D=0,P=0;const M=T.Zero(),R=T.Zero(),F=T.Zero(),Z=T.Zero(),j=T.Zero();let V=0,J=0,L=0,k=0,C=0,se=0;const ue=te.Zero(),he=te.Zero(),pe=te.Zero(),I=te.Zero(),Ze=te.Zero();let Ge=0,Xe=0,je=0,$e=0,Ve=0,Ke=0,qe=0,Qe=0,Je=0,Le=0,Ye=0,et=0;const fe=ce.Zero(),Ae=ce.Zero(),tt=ce.Zero(),st=ce.Zero(),rt=ce.Zero();let Y=0,xe=0;h=h||0;let de,me,H=new ce(0,0,0,0),Ee=T.Zero(),ze=T.Zero(),ot=T.Zero(),re=0,nt=T.Zero(),it=0,at=0;const ve=new Lt(T.Zero(),new T(1,0,0));let Ie,ge=T.Zero();for(let N=0;N<f.length/3;N++){A=f[3*N],w=f[3*N+1],g=f[3*N+2],b=l[3*A],m=l[3*A+1],c=l[3*A+2],y=l[3*w],z=l[3*w+1],U=l[3*w+2],B=l[3*g],D=l[3*g+1],P=l[3*g+2],M.set(b,m,c),R.set(y,z,U),F.set(B,D,P),R.subtractToRef(M,Z),F.subtractToRef(R,j),_&&(V=_[2*A],J=_[2*A+1],L=_[2*w],k=_[2*w+1],C=_[2*g],se=_[2*g+1],ue.set(V,J),he.set(L,k),pe.set(C,se),he.subtractToRef(ue,I),pe.subtractToRef(he,Ze)),x&&i&&(Ge=x[4*A],Xe=x[4*A+1],je=x[4*A+2],$e=x[4*A+3],Ve=x[4*w],Ke=x[4*w+1],qe=x[4*w+2],Qe=x[4*w+3],Je=x[4*g],Le=x[4*g+1],Ye=x[4*g+2],et=x[4*g+3],fe.set(Ge,Xe,je,$e),Ae.set(Ve,Ke,qe,Qe),tt.set(Je,Le,Ye,et),Ae.subtractToRef(fe,st),tt.subtractToRef(Ae,rt));let He,ct,lt,ut,ht,oe,ne,ye;const ft=new Ce(0,0,0),Se=new Ce(0,0,0);let ie,G;for(let De=0;De<s._groupDensity[N];De++)S=this.particles.length,this._addParticle(S,s,this._groupCounter,N+De),G=this.particles[S],Y=Math.sqrt(ee(0,1)),xe=ee(0,1),de=M.add(Z.scale(Y)).add(j.scale(Y*xe)),r&&(Ee=e.getFacetNormal(N).normalize().scale(-1),ze=Z.clone().normalize(),ot=T.Cross(Ee,ze),re=ee(0,2*Math.PI),nt=ze.scale(Math.cos(re)).add(ot.scale(Math.sin(re))),re=ee(.1,Math.PI/2),ge=nt.scale(Math.cos(re)).add(Ee.scale(Math.sin(re))),ve.origin=de.add(ge.scale(1e-5)),ve.direction=ge,ve.length=u,Ie=ve.intersectsMesh(e),Ie.hit&&(at=Ie.pickedPoint.subtract(de).length(),it=ee(0,1)*at,de.addInPlace(ge.scale(it)))),G.position=de.clone(),this._positions.push(G.position.x,G.position.y,G.position.z),i!==void 0?_&&(me=ue.add(I.scale(Y)).add(Ze.scale(Y*xe)),i?o&&s._groupImageData!==null?(He=s._groupImgWidth,ct=s._groupImgHeight,ie=this._getColorIndicesForCoord(s,Math.round(me.x*He),Math.round(me.y*ct),He),G.color=ie,this._colors.push(ie.r,ie.g,ie.b,ie.a)):x?(H=fe.add(st.scale(Y)).add(rt.scale(Y*xe)),G.color=new q(H.x,H.y,H.z,H.w),this._colors.push(H.x,H.y,H.z,H.w)):(H=fe.set(Math.random(),Math.random(),Math.random(),1),G.color=new q(H.x,H.y,H.z,H.w),this._colors.push(H.x,H.y,H.z,H.w)):(G.uv=me.clone(),this._uvs.push(G.uv.x,G.uv.y))):(n?(ft.set(n.r,n.g,n.b),lt=ee(-h,h),ut=ee(-h,h),ye=ft.toHSV(),ht=ye.r,oe=ye.g+lt,ne=ye.b+ut,oe<0&&(oe=0),oe>1&&(oe=1),ne<0&&(ne=0),ne>1&&(ne=1),Ce.HSVtoRGBToRef(ht,oe,ne,Se),H.set(Se.r,Se.g,Se.b,1)):H=fe.set(Math.random(),Math.random(),Math.random(),1),G.color=new q(H.x,H.y,H.z,H.w),this._colors.push(H.x,H.y,H.z,H.w))}}_colorFromTexture(e,s,r){if(e.material===null){_e.Warn(e.name+"has no material."),s._groupImageData=null,this._setPointsColorOrUV(e,s,r,!0,!1);return}const o=e.material.getActiveTextures();if(o.length===0){_e.Warn(e.name+"has no usable texture."),s._groupImageData=null,this._setPointsColorOrUV(e,s,r,!0,!1);return}const n=e.clone();n.setEnabled(!1),this._promises.push(new Promise(h=>{qt.WhenAllReady(o,()=>{let d=s._textureNb;d<0&&(d=0),d>o.length-1&&(d=o.length-1);const a=()=>{s._groupImgWidth=o[d].getSize().width,s._groupImgHeight=o[d].getSize().height,this._setPointsColorOrUV(n,s,r,!0,!0,void 0,void 0,o[d].coordinatesIndex),n.dispose(),h()};s._groupImageData=null;const u=o[d].readPixels();u?u.then(l=>{s._groupImageData=l,a()}):a()})}))}_calculateDensity(e,s,r){let i,o,n,h,d,a,u,l,f,_,x,v;const p=T.Zero(),S=T.Zero(),A=T.Zero(),w=T.Zero(),g=T.Zero(),b=T.Zero();let m;const c=[];let y=0;const z=r.length/3;for(let D=0;D<z;D++)i=r[3*D],o=r[3*D+1],n=r[3*D+2],h=s[3*i],d=s[3*i+1],a=s[3*i+2],u=s[3*o],l=s[3*o+1],f=s[3*o+2],_=s[3*n],x=s[3*n+1],v=s[3*n+2],p.set(h,d,a),S.set(u,l,f),A.set(_,x,v),S.subtractToRef(p,w),A.subtractToRef(S,g),T.CrossToRef(w,g,b),m=.5*b.length(),y+=m,c[D]=y;const U=new Array(z);let B=e;for(let D=z-1;D>0;D--){const P=c[D];if(P===0)U[D]=0;else{const R=(P-c[D-1])/P*B,F=Math.floor(R),Z=R-F,j=+(Math.random()<Z),V=F+j;U[D]=V,B-=V}}return U[0]=B,U}addPoints(e,s=this._randomUnitVector){const r=new Ue(this._groupCounter,s);let i,o=this.nbParticles;for(let n=0;n<e;n++)i=this._addParticle(o,r,this._groupCounter,n),r&&r._positionFunction&&r._positionFunction(i,o,n),this._positions.push(i.position.x,i.position.y,i.position.z),i.color&&this._colors.push(i.color.r,i.color.g,i.color.b,i.color.a),i.uv&&this._uvs.push(i.uv.x,i.uv.y),o++;return this.nbParticles+=e,this._groupCounter++,this._groupCounter}addSurfacePoints(e,s,r,i,o){let n=r||0;(isNaN(n)||n<0||n>3)&&(n=0);const h=e.getVerticesData(X.PositionKind),d=e.getIndices();this._groups.push(this._groupCounter);const a=new Ue(this._groupCounter,null);switch(a._groupDensity=this._calculateDensity(s,h,d),n===2?a._textureNb=i||0:i=i||new q(1,1,1,1),n){case 2:this._colorFromTexture(e,a,!1);break;case 1:this._setPointsColorOrUV(e,a,!1,!1,!1);break;case 0:this._setPointsColorOrUV(e,a,!1);break;case 3:this._setPointsColorOrUV(e,a,!1,void 0,void 0,i,o);break}return this.nbParticles+=s,this._groupCounter++,this._groupCounter-1}addVolumePoints(e,s,r,i,o){let n=r||0;(isNaN(n)||n<0||n>3)&&(n=0);const h=e.getVerticesData(X.PositionKind),d=e.getIndices();this._groups.push(this._groupCounter);const a=new Ue(this._groupCounter,null);switch(a._groupDensity=this._calculateDensity(s,h,d),n===2?a._textureNb=i||0:i=i||new q(1,1,1,1),n){case 2:this._colorFromTexture(e,a,!0);break;case 1:this._setPointsColorOrUV(e,a,!0,!1,!1);break;case 0:this._setPointsColorOrUV(e,a,!0);break;case 3:this._setPointsColorOrUV(e,a,!0,void 0,void 0,i,o);break}return this.nbParticles+=s,this._groupCounter++,this._groupCounter-1}setParticles(e=0,s=this.nbParticles-1,r=!0){var w,g;if(!this._updatable||!this._isReady)return this;this.beforeUpdateParticles(e,s,r);const i=W.Matrix[0],o=this.mesh,n=this._colors32,h=this._positions32,d=this._uvs32,a=W.Vector3,u=a[5].copyFromFloats(1,0,0),l=a[6].copyFromFloats(0,1,0),f=a[7].copyFromFloats(0,0,1),_=a[8].setAll(Number.MAX_VALUE),x=a[9].setAll(-Number.MAX_VALUE);Te.IdentityToRef(i);let v=0;if((w=this.mesh)!=null&&w.isFacetDataEnabled&&(this._computeBoundingBox=!0),s=s>=this.nbParticles?this.nbParticles-1:s,this._computeBoundingBox&&(e!=0||s!=this.nbParticles-1)){const b=(g=this.mesh)==null?void 0:g.getBoundingInfo();b&&(_.copyFrom(b.minimum),x.copyFrom(b.maximum))}v=0;let p=0,S=0,A=0;for(let b=e;b<=s;b++){const m=this.particles[b];v=m.idx,p=3*v,S=4*v,A=2*v,this.updateParticle(m);const c=m._rotationMatrix,y=m.position,z=m._globalPosition;if(this._computeParticleRotation&&m.getRotationMatrix(i),m.parentId!==null){const k=this.particles[m.parentId],C=k._rotationMatrix,se=k._globalPosition,ue=y.x*C[1]+y.y*C[4]+y.z*C[7],he=y.x*C[0]+y.y*C[3]+y.z*C[6],pe=y.x*C[2]+y.y*C[5]+y.z*C[8];if(z.x=se.x+he,z.y=se.y+ue,z.z=se.z+pe,this._computeParticleRotation){const I=i.m;c[0]=I[0]*C[0]+I[1]*C[3]+I[2]*C[6],c[1]=I[0]*C[1]+I[1]*C[4]+I[2]*C[7],c[2]=I[0]*C[2]+I[1]*C[5]+I[2]*C[8],c[3]=I[4]*C[0]+I[5]*C[3]+I[6]*C[6],c[4]=I[4]*C[1]+I[5]*C[4]+I[6]*C[7],c[5]=I[4]*C[2]+I[5]*C[5]+I[6]*C[8],c[6]=I[8]*C[0]+I[9]*C[3]+I[10]*C[6],c[7]=I[8]*C[1]+I[9]*C[4]+I[10]*C[7],c[8]=I[8]*C[2]+I[9]*C[5]+I[10]*C[8]}}else if(z.x=0,z.y=0,z.z=0,this._computeParticleRotation){const k=i.m;c[0]=k[0],c[1]=k[1],c[2]=k[2],c[3]=k[4],c[4]=k[5],c[5]=k[6],c[6]=k[8],c[7]=k[9],c[8]=k[10]}const B=a[11];m.translateFromPivot?B.setAll(0):B.copyFrom(m.pivot);const D=a[0];D.copyFrom(m.position);const P=D.x-m.pivot.x,M=D.y-m.pivot.y,R=D.z-m.pivot.z;let F=P*c[0]+M*c[3]+R*c[6],Z=P*c[1]+M*c[4]+R*c[7],j=P*c[2]+M*c[5]+R*c[8];F+=B.x,Z+=B.y,j+=B.z;const V=h[p]=z.x+u.x*F+l.x*Z+f.x*j,J=h[p+1]=z.y+u.y*F+l.y*Z+f.y*j,L=h[p+2]=z.z+u.z*F+l.z*Z+f.z*j;if(this._computeBoundingBox&&(_.minimizeInPlaceFromFloats(V,J,L),x.maximizeInPlaceFromFloats(V,J,L)),this._computeParticleColor&&m.color){const k=m.color,C=this._colors32;C[S]=k.r,C[S+1]=k.g,C[S+2]=k.b,C[S+3]=k.a}if(this._computeParticleTexture&&m.uv){const k=m.uv,C=this._uvs32;C[A]=k.x,C[A+1]=k.y}}return o&&(r&&(this._computeParticleColor&&o.updateVerticesData(X.ColorKind,n,!1,!1),this._computeParticleTexture&&o.updateVerticesData(X.UVKind,d,!1,!1),o.updateVerticesData(X.PositionKind,h,!1,!1)),this._computeBoundingBox&&(o.hasBoundingInfo?o.getBoundingInfo().reConstruct(_,x,o._worldMatrix):o.buildBoundingInfo(_,x,o._worldMatrix))),this.afterUpdateParticles(e,s,r),this}dispose(){var e;(e=this.mesh)==null||e.dispose(),this.vars=null,this._positions=null,this._indices=null,this._normals=null,this._uvs=null,this._colors=null,this._indices32=null,this._positions32=null,this._uvs32=null,this._colors32=null}refreshVisibleSize(){var e;return this._isVisibilityBoxLocked||(e=this.mesh)==null||e.refreshBoundingInfo(),this}setVisibilityBox(e){if(!this.mesh)return;const s=e/2;this.mesh.buildBoundingInfo(new T(-s,-s,-s),new T(s,s,s))}get isAlwaysVisible(){return this._alwaysVisible}set isAlwaysVisible(e){this.mesh&&(this._alwaysVisible=e,this.mesh.alwaysSelectAsActiveMesh=e)}set computeParticleRotation(e){this._computeParticleRotation=e}set computeParticleColor(e){this._computeParticleColor=e}set computeParticleTexture(e){this._computeParticleTexture=e}get computeParticleColor(){return this._computeParticleColor}get computeParticleTexture(){return this._computeParticleTexture}set computeBoundingBox(e){this._computeBoundingBox=e}get computeBoundingBox(){return this._computeBoundingBox}initParticles(){}recycleParticle(e){return e}updateParticle(e){return e}beforeUpdateParticles(e,s,r){}afterUpdateParticles(e,s,r){}}var bt;(function(t){t[t.Splat=0]="Splat",t[t.PointCloud=1]="PointCloud",t[t.Mesh=2]="Mesh",t[t.Reject=3]="Reject"})(bt||(bt={}));class Q{constructor(e=Q._DefaultLoadingOptions){this.name=ke.name,this._assetContainer=null,this.extensions=ke.extensions,this._loadingOptions=e}createPlugin(e){return new Q(e[ke.name])}async importMeshAsync(e,s,r,i,o,n){return this._parse(e,s,r,i).then(h=>({meshes:h,particleSystems:[],skeletons:[],animationGroups:[],transformNodes:[],geometries:[],lights:[],spriteManagers:[]}))}static _BuildPointCloud(e,s){if(!s.byteLength)return!1;const r=new Uint8Array(s),i=new Float32Array(s),o=3*4+3*4+4+4,n=r.length/o,h=function(d,a){const u=i[8*a+0],l=i[8*a+1],f=i[8*a+2];d.position=new T(u,l,f);const _=r[o*a+24+0]/255,x=r[o*a+24+1]/255,v=r[o*a+24+2]/255;d.color=new q(_,x,v,1)};return e.addPoints(n,h),!0}static _BuildMesh(e,s){const r=new Ne("PLYMesh",e),i=new Uint8Array(s.data),o=new Float32Array(s.data),n=3*4+3*4+4+4,h=i.length/n,d=[],a=new We;for(let u=0;u<h;u++){const l=o[8*u+0],f=o[8*u+1],_=o[8*u+2];d.push(l,f,_)}if(s.hasVertexColors){const u=new Float32Array(h*4);for(let l=0;l<h;l++){const f=i[n*l+24+0]/255,_=i[n*l+24+1]/255,x=i[n*l+24+2]/255;u[l*4+0]=f,u[l*4+1]=_,u[l*4+2]=x,u[l*4+3]=1}a.colors=u}return a.positions=d,a.indices=s.faces,a.applyToMesh(r),r}_parseSPZ(e,s){const r=new Uint8Array(e),i=new Uint32Array(e.slice(0,12)),o=i[2],n=r[12],h=r[13];if(r[15]||i[0]!=1347635022||i[1]!=2)return new Promise(c=>{c({mode:3,data:u,hasVertexColors:!1})});const a=3*4+3*4+4+4,u=new ArrayBuffer(a*o),l=1/(1<<h),f=new Int32Array(1),_=new Uint8Array(f.buffer),x=function(c,y){return _[0]=c[y+0],_[1]=c[y+1],_[2]=c[y+2],_[3]=c[y+2]&128?255:0,f[0]*l};let v=16;const p=new Float32Array(u),S=new Float32Array(u),A=new Uint8ClampedArray(u),w=new Uint8ClampedArray(u);let g=1,b=0;this._loadingOptions.flipY||(g=-1,b=255);for(let c=0;c<o;c++)p[c*8+0]=x(r,v+0),p[c*8+1]=g*x(r,v+3),p[c*8+2]=g*x(r,v+6),v+=9;const m=.282;for(let c=0;c<o;c++){for(let y=0;y<3;y++){const U=(r[v+o+c*3+y]-127.5)/(.15*255);A[c*32+24+y]=$.Clamp((.5+m*U)*255,0,255)}A[c*32+24+3]=r[v+c]}v+=o*4;for(let c=0;c<o;c++)S[c*8+3+0]=Math.exp(r[v+0]/16-10),S[c*8+3+1]=Math.exp(r[v+1]/16-10),S[c*8+3+2]=Math.exp(r[v+2]/16-10),v+=3;for(let c=0;c<o;c++){const y=r[v+0],z=r[v+1]*g+b,U=r[v+2]*g+b,B=y/127.5-1,D=z/127.5-1,P=U/127.5-1;w[c*32+28+1]=y,w[c*32+28+2]=z,w[c*32+28+3]=U;const M=1-(B*B+D*D+P*P);w[c*32+28+0]=127.5+Math.sqrt(M<0?0:M)*127.5,v+=3}if(n){const y=((n+1)*(n+1)-1)*3,z=Math.ceil(y/16);let U=v;const B=[],P=s.getEngine().getCaps().maxTextureSize,M=Math.ceil(o/P);for(let R=0;R<z;R++){const F=new Uint8Array(M*P*4*4);B.push(F)}for(let R=0;R<o;R++)for(let F=0;F<y;F++){const Z=r[U++],j=Math.floor(F/16),V=B[j],J=F%16,L=R*16;V[J+L]=Z}return new Promise(R=>{R({mode:0,data:u,hasVertexColors:!1,sh:B})})}return new Promise(c=>{c({mode:0,data:u,hasVertexColors:!1})})}_parse(e,s,r,i){const o=[],n=new ReadableStream({start(a){a.enqueue(new Uint8Array(r)),a.close()}}),h=new DecompressionStream("gzip"),d=n.pipeThrough(h);return new Promise(a=>{new Response(d).arrayBuffer().then(u=>{this._parseSPZ(u,s).then(l=>{s._blockEntityCollection=!!this._assetContainer;const f=new E("GaussianSplatting",null,s,this._loadingOptions.keepInRam);f._parentContainer=this._assetContainer,o.push(f),f.updateData(l.data,l.sh),s._blockEntityCollection=!1,a(o)})}).catch(()=>{Q._ConvertPLYToSplat(r).then(async u=>{switch(s._blockEntityCollection=!!this._assetContainer,u.mode){case 0:{const l=new E("GaussianSplatting",null,s,this._loadingOptions.keepInRam);l._parentContainer=this._assetContainer,o.push(l),l.updateData(u.data,u.sh)}break;case 1:{const l=new gs("PointCloud",1,s);Q._BuildPointCloud(l,u.data)?await l.buildMeshAsync().then(f=>{o.push(f)}):l.dispose()}break;case 2:if(u.faces)o.push(Q._BuildMesh(s,u));else throw new Error("PLY mesh doesn't contain face informations.");break;default:throw new Error("Unsupported Splat mode")}s._blockEntityCollection=!1,a(o)})})})}loadAssetContainerAsync(e,s,r){const i=new Jt(e);return this._assetContainer=i,this.importMeshAsync(null,e,s,r).then(o=>(o.meshes.forEach(n=>i.meshes.push(n)),this._assetContainer=null,i)).catch(o=>{throw this._assetContainer=null,o})}loadAsync(e,s,r){return this.importMeshAsync(null,e,s,r).then(()=>{})}static _ConvertPLYToSplat(e){const s=new Uint8Array(e),r=new TextDecoder().decode(s.slice(0,1024*10)),i=`end_header
`,o=r.indexOf(i);if(o<0||!r)return new Promise(g=>{g({mode:0,data:e})});const n=parseInt(/element vertex (\d+)\n/.exec(r)[1]),h=/element face (\d+)\n/.exec(r);let d=0;h&&(d=parseInt(h[1]));const a=/element chunk (\d+)\n/.exec(r);let u=0;a&&(u=parseInt(a[1]));let l=0,f=0;const _={double:8,int:4,uint:4,float:4,short:2,ushort:2,uchar:1,list:0};let x;(function(g){g[g.Vertex=0]="Vertex",g[g.Chunk=1]="Chunk"})(x||(x={}));let v=1;const p=[],S=r.slice(0,o).split(`
`);for(const g of S)if(g.startsWith("property ")){const[,b,m]=g.split(" ");v==1?f+=_[b]:v==0&&(p.push({name:m,type:b,offset:l}),l+=_[b]),_[b]||_e.Warn(`Unsupported property type: ${b}.`)}else if(g.startsWith("element ")){const[,b]=g.split(" ");b=="chunk"?v=1:b=="vertex"&&(v=0)}const A=l,w=f;return E.ConvertPLYWithSHToSplatAsync(e).then(g=>{const b=new DataView(e,o+i.length);let m=w*u+A*n;const c=[];if(d)for(let M=0;M<d;M++){const R=b.getUint8(m);if(R==3){m+=1;for(let F=0;F<R;F++){const Z=b.getUint32(m+(2-F)*4,!0);c.push(Z)}m+=12}}if(u)return new Promise(M=>{M({mode:0,data:g.buffer,sh:g.sh,faces:c,hasVertexColors:!1})});let y=0,z=0;const U=["x","y","z","scale_0","scale_1","scale_2","opacity","rot_0","rot_1","rot_2","rot_3"],B=["red","green","blue","f_dc_0","f_dc_1","f_dc_2"];for(let M=0;M<p.length;M++){const R=p[M];U.includes(R.name)&&y++,B.includes(R.name)&&z++}const D=y==U.length&&z==3,P=d?2:D?0:1;return new Promise(M=>{M({mode:P,data:g.buffer,sh:g.sh,faces:c,hasVertexColors:!!z})})})}}Q._DefaultLoadingOptions={keepInRam:!1,flipY:!1};Qt(new Q);export{Q as SPLATFileLoader};
//# sourceMappingURL=splatFileLoader.DiNDmZCz.js.map
