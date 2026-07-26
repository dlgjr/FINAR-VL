import { n as noop, l as get_store_value, c as create_ssr_component, s as subscribe, e as escape, h as add_styles, d as add_attribute, f as each, v as validate_component, B as compute_rest_props, b as createEventDispatcher, C as spread, D as escape_attribute_value, E as escape_object, m as missing_component, j as null_to_empty, o as onDestroy, k as setContext } from './ssr-C3HYbsxA.js';
import { d as derived, w as writable } from './index-ClteBeTX.js';
import { t as tick, b as binding_callbacks, a as bind } from './Component-NmRBwSfF.js';
import require$$2 from 'path';
import require$$1$1 from 'url';
import require$$1 from 'fs';

const s$1=!1,a$1=!1;

const is_client = typeof window !== 'undefined';

/** @type {() => number} */
let now = is_client ? () => window.performance.now() : () => Date.now();

let raf = is_client ? (cb) => requestAnimationFrame(cb) : noop;

const tasks = new Set();

/**
 * @param {number} now
 * @returns {void}
 */
function run_tasks(now) {
	tasks.forEach((task) => {
		if (!task.c(now)) {
			tasks.delete(task);
			task.f();
		}
	});
	if (tasks.size !== 0) raf(run_tasks);
}

/**
 * Creates a new task that runs on each raf frame
 * until it returns a falsy value or is aborted
 * @param {import('./private.js').TaskCallback} callback
 * @returns {import('./private.js').Task}
 */
function loop(callback) {
	/** @type {import('./private.js').TaskEntry} */
	let task;
	if (tasks.size === 0) raf(run_tasks);
	return {
		promise: new Promise((fulfill) => {
			tasks.add((task = { c: callback, f: fulfill }));
		}),
		abort() {
			tasks.delete(task);
		}
	};
}

/** @type {typeof globalThis} */
const globals =
	typeof window !== 'undefined'
		? window
		: typeof globalThis !== 'undefined'
		? globalThis
		: // @ts-ignore Node typings have this
		  global;

/** regex of all html void element names */
const void_element_names =
	/^(?:area|base|br|col|command|embed|hr|img|input|keygen|link|meta|param|source|track|wbr)$/;

/**
 * @param {string} name
 * @returns {boolean}
 */
function is_void(name) {
	return void_element_names.test(name) || name.toLowerCase() === '!doctype';
}

var Xs=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof global<"u"?global:typeof self<"u"?self:{};function Hr$1(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}function Ks(e){if(e.__esModule)return e;var t=e.default;if(typeof t=="function"){var n=function r(){return this instanceof r?Reflect.construct(t,arguments,this.constructor):t.apply(this,arguments)};n.prototype=t.prototype;}else n={};return Object.defineProperty(n,"__esModule",{value:!0}),Object.keys(e).forEach(function(r){var i=Object.getOwnPropertyDescriptor(e,r);Object.defineProperty(n,r,i.get?i:{enumerable:!0,get:function(){return e[r]}});}),n}const Pr$1="data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='10'%20height='10'%20fill='none'%3e%3cpath%20fill='%23FF3270'%20d='M1.93%206.03v2.04h2.04V6.03H1.93Z'/%3e%3cpath%20fill='%23861FFF'%20d='M6.03%206.03v2.04h2.04V6.03H6.03Z'/%3e%3cpath%20fill='%23097EFF'%20d='M1.93%201.93v2.04h2.04V1.93H1.93Z'/%3e%3cpath%20fill='%23000'%20fill-rule='evenodd'%20d='M.5%201.4c0-.5.4-.9.9-.9h3.1a.9.9%200%200%201%20.87.67A2.44%202.44%200%200%201%209.5%202.95c0%20.65-.25%201.24-.67%201.68.39.1.67.46.67.88v3.08c0%20.5-.4.91-.9.91H1.4a.9.9%200%200%201-.9-.9V1.4Zm1.43.53v2.04h2.04V1.93H1.93Zm0%206.14V6.03h2.04v2.04H1.93Zm4.1%200V6.03h2.04v2.04H6.03Zm0-5.12a1.02%201.02%200%201%201%202.04%200%201.02%201.02%200%200%201-2.04%200Z'%20clip-rule='evenodd'/%3e%3cpath%20fill='%23FFD702'%20d='M7.05%201.93a1.02%201.02%200%201%200%200%202.04%201.02%201.02%200%200%200%200-2.04Z'/%3e%3c/svg%3e";var Nr$1=function(t){return kr$1(t)&&!Mr$1(t)};function kr$1(e){return !!e&&typeof e=="object"}function Mr$1(e){var t=Object.prototype.toString.call(e);return t==="[object RegExp]"||t==="[object Date]"||Dr$1(e)}var Lr$1=typeof Symbol=="function"&&Symbol.for,Rr$1=Lr$1?Symbol.for("react.element"):60103;function Dr$1(e){return e.$$typeof===Rr$1}function Ur$1(e){return Array.isArray(e)?[]:{}}function De$1(e,t){return t.clone!==!1&&t.isMergeableObject(e)?we$2(Ur$1(e),e,t):e}function jr$1(e,t,n){return e.concat(t).map(function(r){return De$1(r,n)})}function Gr$1(e,t){if(!t.customMerge)return we$2;var n=t.customMerge(e);return typeof n=="function"?n:we$2}function Fr$1(e){return Object.getOwnPropertySymbols?Object.getOwnPropertySymbols(e).filter(function(t){return Object.propertyIsEnumerable.call(e,t)}):[]}function Gt$1(e){return Object.keys(e).concat(Fr$1(e))}function Cn$1(e,t){try{return t in e}catch{return !1}}function zr$1(e,t){return Cn$1(e,t)&&!(Object.hasOwnProperty.call(e,t)&&Object.propertyIsEnumerable.call(e,t))}function $r$1(e,t,n){var r={};return n.isMergeableObject(e)&&Gt$1(e).forEach(function(i){r[i]=De$1(e[i],n);}),Gt$1(t).forEach(function(i){zr$1(e,i)||(Cn$1(e,i)&&n.isMergeableObject(t[i])?r[i]=Gr$1(i,n)(e[i],t[i],n):r[i]=De$1(t[i],n));}),r}function we$2(e,t,n){n=n||{},n.arrayMerge=n.arrayMerge||jr$1,n.isMergeableObject=n.isMergeableObject||Nr$1,n.cloneUnlessOtherwiseSpecified=De$1;var r=Array.isArray(t),i=Array.isArray(e),o=r===i;return o?r?n.arrayMerge(e,t,n):$r$1(e,t,n):De$1(t,n)}we$2.all=function(t,n){if(!Array.isArray(t))throw new Error("first argument should be an array");return t.reduce(function(r,i){return we$2(r,i,n)},{})};var Wr$1=we$2,Vr$1=Wr$1;const qr$1=Hr$1(Vr$1);var pt$2=function(e,t){return pt$2=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(n,r){n.__proto__=r;}||function(n,r){for(var i in r)Object.prototype.hasOwnProperty.call(r,i)&&(n[i]=r[i]);},pt$2(e,t)};function Ke$1(e,t){if(typeof t!="function"&&t!==null)throw new TypeError("Class extends value "+String(t)+" is not a constructor or null");pt$2(e,t);function n(){this.constructor=e;}e.prototype=t===null?Object.create(t):(n.prototype=t.prototype,new n);}var H=function(){return H=Object.assign||function(t){for(var n,r=1,i=arguments.length;r<i;r++){n=arguments[r];for(var o in n)Object.prototype.hasOwnProperty.call(n,o)&&(t[o]=n[o]);}return t},H.apply(this,arguments)};function Qr$1(e,t){var n={};for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&typeof Object.getOwnPropertySymbols=="function")for(var i=0,r=Object.getOwnPropertySymbols(e);i<r.length;i++)t.indexOf(r[i])<0&&Object.prototype.propertyIsEnumerable.call(e,r[i])&&(n[r[i]]=e[r[i]]);return n}function nt$2(e,t,n){if(arguments.length===2)for(var r=0,i=t.length,o;r<i;r++)(o||!(r in t))&&(o||(o=Array.prototype.slice.call(t,0,r)),o[r]=t[r]);return e.concat(o||Array.prototype.slice.call(t))}function rt$2(e,t){var n=t&&t.cache?t.cache:ti,r=t&&t.serializer?t.serializer:Jr$1,i=t&&t.strategy?t.strategy:Kr$1;return i(e,{cache:n,serializer:r})}function Xr$1(e){return e==null||typeof e=="number"||typeof e=="boolean"}function En$1(e,t,n,r){var i=Xr$1(r)?r:n(r),o=t.get(i);return typeof o>"u"&&(o=e.call(this,r),t.set(i,o)),o}function xn$1(e,t,n){var r=Array.prototype.slice.call(arguments,3),i=n(r),o=t.get(i);return typeof o>"u"&&(o=e.apply(this,r),t.set(i,o)),o}function It$2(e,t,n,r,i){return n.bind(t,e,r,i)}function Kr$1(e,t){var n=e.length===1?En$1:xn$1;return It$2(e,this,n,t.cache.create(),t.serializer)}function Zr$1(e,t){return It$2(e,this,xn$1,t.cache.create(),t.serializer)}function Yr$1(e,t){return It$2(e,this,En$1,t.cache.create(),t.serializer)}var Jr$1=function(){return JSON.stringify(arguments)},ei=function(){function e(){this.cache=Object.create(null);}return e.prototype.get=function(t){return this.cache[t]},e.prototype.set=function(t,n){this.cache[t]=n;},e}(),ti={create:function(){return new ei}},it$3={variadic:Zr$1,monadic:Yr$1},I$1;(function(e){e[e.EXPECT_ARGUMENT_CLOSING_BRACE=1]="EXPECT_ARGUMENT_CLOSING_BRACE",e[e.EMPTY_ARGUMENT=2]="EMPTY_ARGUMENT",e[e.MALFORMED_ARGUMENT=3]="MALFORMED_ARGUMENT",e[e.EXPECT_ARGUMENT_TYPE=4]="EXPECT_ARGUMENT_TYPE",e[e.INVALID_ARGUMENT_TYPE=5]="INVALID_ARGUMENT_TYPE",e[e.EXPECT_ARGUMENT_STYLE=6]="EXPECT_ARGUMENT_STYLE",e[e.INVALID_NUMBER_SKELETON=7]="INVALID_NUMBER_SKELETON",e[e.INVALID_DATE_TIME_SKELETON=8]="INVALID_DATE_TIME_SKELETON",e[e.EXPECT_NUMBER_SKELETON=9]="EXPECT_NUMBER_SKELETON",e[e.EXPECT_DATE_TIME_SKELETON=10]="EXPECT_DATE_TIME_SKELETON",e[e.UNCLOSED_QUOTE_IN_ARGUMENT_STYLE=11]="UNCLOSED_QUOTE_IN_ARGUMENT_STYLE",e[e.EXPECT_SELECT_ARGUMENT_OPTIONS=12]="EXPECT_SELECT_ARGUMENT_OPTIONS",e[e.EXPECT_PLURAL_ARGUMENT_OFFSET_VALUE=13]="EXPECT_PLURAL_ARGUMENT_OFFSET_VALUE",e[e.INVALID_PLURAL_ARGUMENT_OFFSET_VALUE=14]="INVALID_PLURAL_ARGUMENT_OFFSET_VALUE",e[e.EXPECT_SELECT_ARGUMENT_SELECTOR=15]="EXPECT_SELECT_ARGUMENT_SELECTOR",e[e.EXPECT_PLURAL_ARGUMENT_SELECTOR=16]="EXPECT_PLURAL_ARGUMENT_SELECTOR",e[e.EXPECT_SELECT_ARGUMENT_SELECTOR_FRAGMENT=17]="EXPECT_SELECT_ARGUMENT_SELECTOR_FRAGMENT",e[e.EXPECT_PLURAL_ARGUMENT_SELECTOR_FRAGMENT=18]="EXPECT_PLURAL_ARGUMENT_SELECTOR_FRAGMENT",e[e.INVALID_PLURAL_ARGUMENT_SELECTOR=19]="INVALID_PLURAL_ARGUMENT_SELECTOR",e[e.DUPLICATE_PLURAL_ARGUMENT_SELECTOR=20]="DUPLICATE_PLURAL_ARGUMENT_SELECTOR",e[e.DUPLICATE_SELECT_ARGUMENT_SELECTOR=21]="DUPLICATE_SELECT_ARGUMENT_SELECTOR",e[e.MISSING_OTHER_CLAUSE=22]="MISSING_OTHER_CLAUSE",e[e.INVALID_TAG=23]="INVALID_TAG",e[e.INVALID_TAG_NAME=25]="INVALID_TAG_NAME",e[e.UNMATCHED_CLOSING_TAG=26]="UNMATCHED_CLOSING_TAG",e[e.UNCLOSED_TAG=27]="UNCLOSED_TAG";})(I$1||(I$1={}));var M;(function(e){e[e.literal=0]="literal",e[e.argument=1]="argument",e[e.number=2]="number",e[e.date=3]="date",e[e.time=4]="time",e[e.select=5]="select",e[e.plural=6]="plural",e[e.pound=7]="pound",e[e.tag=8]="tag";})(M||(M={}));var Ce$2;(function(e){e[e.number=0]="number",e[e.dateTime=1]="dateTime";})(Ce$2||(Ce$2={}));function Ft$1(e){return e.type===M.literal}function ni(e){return e.type===M.argument}function Sn$1(e){return e.type===M.number}function Bn$2(e){return e.type===M.date}function In$1(e){return e.type===M.time}function Tn$1(e){return e.type===M.select}function On$1(e){return e.type===M.plural}function ri(e){return e.type===M.pound}function Hn$1(e){return e.type===M.tag}function Pn$1(e){return !!(e&&typeof e=="object"&&e.type===Ce$2.number)}function dt$3(e){return !!(e&&typeof e=="object"&&e.type===Ce$2.dateTime)}var Nn$1=/[ \xA0\u1680\u2000-\u200A\u202F\u205F\u3000]/,ii=/(?:[Eec]{1,6}|G{1,5}|[Qq]{1,5}|(?:[yYur]+|U{1,5})|[ML]{1,5}|d{1,2}|D{1,3}|F{1}|[abB]{1,5}|[hkHK]{1,2}|w{1,2}|W{1}|m{1,2}|s{1,2}|[zZOvVxX]{1,4})(?=([^']*'[^']*')*[^']*$)/g;function oi(e){var t={};return e.replace(ii,function(n){var r=n.length;switch(n[0]){case"G":t.era=r===4?"long":r===5?"narrow":"short";break;case"y":t.year=r===2?"2-digit":"numeric";break;case"Y":case"u":case"U":case"r":throw new RangeError("`Y/u/U/r` (year) patterns are not supported, use `y` instead");case"q":case"Q":throw new RangeError("`q/Q` (quarter) patterns are not supported");case"M":case"L":t.month=["numeric","2-digit","short","long","narrow"][r-1];break;case"w":case"W":throw new RangeError("`w/W` (week) patterns are not supported");case"d":t.day=["numeric","2-digit"][r-1];break;case"D":case"F":case"g":throw new RangeError("`D/F/g` (day) patterns are not supported, use `d` instead");case"E":t.weekday=r===4?"long":r===5?"narrow":"short";break;case"e":if(r<4)throw new RangeError("`e..eee` (weekday) patterns are not supported");t.weekday=["short","long","narrow","short"][r-4];break;case"c":if(r<4)throw new RangeError("`c..ccc` (weekday) patterns are not supported");t.weekday=["short","long","narrow","short"][r-4];break;case"a":t.hour12=!0;break;case"b":case"B":throw new RangeError("`b/B` (period) patterns are not supported, use `a` instead");case"h":t.hourCycle="h12",t.hour=["numeric","2-digit"][r-1];break;case"H":t.hourCycle="h23",t.hour=["numeric","2-digit"][r-1];break;case"K":t.hourCycle="h11",t.hour=["numeric","2-digit"][r-1];break;case"k":t.hourCycle="h24",t.hour=["numeric","2-digit"][r-1];break;case"j":case"J":case"C":throw new RangeError("`j/J/C` (hour) patterns are not supported, use `h/H/K/k` instead");case"m":t.minute=["numeric","2-digit"][r-1];break;case"s":t.second=["numeric","2-digit"][r-1];break;case"S":case"A":throw new RangeError("`S/A` (second) patterns are not supported, use `s` instead");case"z":t.timeZoneName=r<4?"short":"long";break;case"Z":case"O":case"v":case"V":case"X":case"x":throw new RangeError("`Z/O/v/V/X/x` (timeZone) patterns are not supported, use `z` instead")}return ""}),t}var si=/[\t-\r \x85\u200E\u200F\u2028\u2029]/i;function ai(e){if(e.length===0)throw new Error("Number skeleton cannot be empty");for(var t=e.split(si).filter(function(f){return f.length>0}),n=[],r=0,i=t;r<i.length;r++){var o=i[r],s=o.split("/");if(s.length===0)throw new Error("Invalid number skeleton");for(var a=s[0],h=s.slice(1),l=0,c=h;l<c.length;l++){var u=c[l];if(u.length===0)throw new Error("Invalid number skeleton")}n.push({stem:a,options:h});}return n}function li(e){return e.replace(/^(.*?)-/,"")}var zt=/^\.(?:(0+)(\*)?|(#+)|(0+)(#+))$/g,kn$1=/^(@+)?(\+|#+)?[rs]?$/g,ci=/(\*)(0+)|(#+)(0+)|(0+)/g,Mn$1=/^(0+)$/;function $t$1(e){var t={};return e[e.length-1]==="r"?t.roundingPriority="morePrecision":e[e.length-1]==="s"&&(t.roundingPriority="lessPrecision"),e.replace(kn$1,function(n,r,i){return typeof i!="string"?(t.minimumSignificantDigits=r.length,t.maximumSignificantDigits=r.length):i==="+"?t.minimumSignificantDigits=r.length:r[0]==="#"?t.maximumSignificantDigits=r.length:(t.minimumSignificantDigits=r.length,t.maximumSignificantDigits=r.length+(typeof i=="string"?i.length:0)),""}),t}function Ln$1(e){switch(e){case"sign-auto":return {signDisplay:"auto"};case"sign-accounting":case"()":return {currencySign:"accounting"};case"sign-always":case"+!":return {signDisplay:"always"};case"sign-accounting-always":case"()!":return {signDisplay:"always",currencySign:"accounting"};case"sign-except-zero":case"+?":return {signDisplay:"exceptZero"};case"sign-accounting-except-zero":case"()?":return {signDisplay:"exceptZero",currencySign:"accounting"};case"sign-never":case"+_":return {signDisplay:"never"}}}function ui(e){var t;if(e[0]==="E"&&e[1]==="E"?(t={notation:"engineering"},e=e.slice(2)):e[0]==="E"&&(t={notation:"scientific"},e=e.slice(1)),t){var n=e.slice(0,2);if(n==="+!"?(t.signDisplay="always",e=e.slice(2)):n==="+?"&&(t.signDisplay="exceptZero",e=e.slice(2)),!Mn$1.test(e))throw new Error("Malformed concise eng/scientific notation");t.minimumIntegerDigits=e.length;}return t}function Wt$2(e){var t={},n=Ln$1(e);return n||t}function hi(e){for(var t={},n=0,r=e;n<r.length;n++){var i=r[n];switch(i.stem){case"percent":case"%":t.style="percent";continue;case"%x100":t.style="percent",t.scale=100;continue;case"currency":t.style="currency",t.currency=i.options[0];continue;case"group-off":case",_":t.useGrouping=!1;continue;case"precision-integer":case".":t.maximumFractionDigits=0;continue;case"measure-unit":case"unit":t.style="unit",t.unit=li(i.options[0]);continue;case"compact-short":case"K":t.notation="compact",t.compactDisplay="short";continue;case"compact-long":case"KK":t.notation="compact",t.compactDisplay="long";continue;case"scientific":t=H(H(H({},t),{notation:"scientific"}),i.options.reduce(function(h,l){return H(H({},h),Wt$2(l))},{}));continue;case"engineering":t=H(H(H({},t),{notation:"engineering"}),i.options.reduce(function(h,l){return H(H({},h),Wt$2(l))},{}));continue;case"notation-simple":t.notation="standard";continue;case"unit-width-narrow":t.currencyDisplay="narrowSymbol",t.unitDisplay="narrow";continue;case"unit-width-short":t.currencyDisplay="code",t.unitDisplay="short";continue;case"unit-width-full-name":t.currencyDisplay="name",t.unitDisplay="long";continue;case"unit-width-iso-code":t.currencyDisplay="symbol";continue;case"scale":t.scale=parseFloat(i.options[0]);continue;case"rounding-mode-floor":t.roundingMode="floor";continue;case"rounding-mode-ceiling":t.roundingMode="ceil";continue;case"rounding-mode-down":t.roundingMode="trunc";continue;case"rounding-mode-up":t.roundingMode="expand";continue;case"rounding-mode-half-even":t.roundingMode="halfEven";continue;case"rounding-mode-half-down":t.roundingMode="halfTrunc";continue;case"rounding-mode-half-up":t.roundingMode="halfExpand";continue;case"integer-width":if(i.options.length>1)throw new RangeError("integer-width stems only accept a single optional option");i.options[0].replace(ci,function(h,l,c,u,f,A){if(l)t.minimumIntegerDigits=c.length;else {if(u&&f)throw new Error("We currently do not support maximum integer digits");if(A)throw new Error("We currently do not support exact integer digits")}return ""});continue}if(Mn$1.test(i.stem)){t.minimumIntegerDigits=i.stem.length;continue}if(zt.test(i.stem)){if(i.options.length>1)throw new RangeError("Fraction-precision stems only accept a single optional option");i.stem.replace(zt,function(h,l,c,u,f,A){return c==="*"?t.minimumFractionDigits=l.length:u&&u[0]==="#"?t.maximumFractionDigits=u.length:f&&A?(t.minimumFractionDigits=f.length,t.maximumFractionDigits=f.length+A.length):(t.minimumFractionDigits=l.length,t.maximumFractionDigits=l.length),""});var o=i.options[0];o==="w"?t=H(H({},t),{trailingZeroDisplay:"stripIfInteger"}):o&&(t=H(H({},t),$t$1(o)));continue}if(kn$1.test(i.stem)){t=H(H({},t),$t$1(i.stem));continue}var s=Ln$1(i.stem);s&&(t=H(H({},t),s));var a=ui(i.stem);a&&(t=H(H({},t),a));}return t}var Fe$1={"001":["H","h"],419:["h","H","hB","hb"],AC:["H","h","hb","hB"],AD:["H","hB"],AE:["h","hB","hb","H"],AF:["H","hb","hB","h"],AG:["h","hb","H","hB"],AI:["H","h","hb","hB"],AL:["h","H","hB"],AM:["H","hB"],AO:["H","hB"],AR:["h","H","hB","hb"],AS:["h","H"],AT:["H","hB"],AU:["h","hb","H","hB"],AW:["H","hB"],AX:["H"],AZ:["H","hB","h"],BA:["H","hB","h"],BB:["h","hb","H","hB"],BD:["h","hB","H"],BE:["H","hB"],BF:["H","hB"],BG:["H","hB","h"],BH:["h","hB","hb","H"],BI:["H","h"],BJ:["H","hB"],BL:["H","hB"],BM:["h","hb","H","hB"],BN:["hb","hB","h","H"],BO:["h","H","hB","hb"],BQ:["H"],BR:["H","hB"],BS:["h","hb","H","hB"],BT:["h","H"],BW:["H","h","hb","hB"],BY:["H","h"],BZ:["H","h","hb","hB"],CA:["h","hb","H","hB"],CC:["H","h","hb","hB"],CD:["hB","H"],CF:["H","h","hB"],CG:["H","hB"],CH:["H","hB","h"],CI:["H","hB"],CK:["H","h","hb","hB"],CL:["h","H","hB","hb"],CM:["H","h","hB"],CN:["H","hB","hb","h"],CO:["h","H","hB","hb"],CP:["H"],CR:["h","H","hB","hb"],CU:["h","H","hB","hb"],CV:["H","hB"],CW:["H","hB"],CX:["H","h","hb","hB"],CY:["h","H","hb","hB"],CZ:["H"],DE:["H","hB"],DG:["H","h","hb","hB"],DJ:["h","H"],DK:["H"],DM:["h","hb","H","hB"],DO:["h","H","hB","hb"],DZ:["h","hB","hb","H"],EA:["H","h","hB","hb"],EC:["h","H","hB","hb"],EE:["H","hB"],EG:["h","hB","hb","H"],EH:["h","hB","hb","H"],ER:["h","H"],ES:["H","hB","h","hb"],ET:["hB","hb","h","H"],FI:["H"],FJ:["h","hb","H","hB"],FK:["H","h","hb","hB"],FM:["h","hb","H","hB"],FO:["H","h"],FR:["H","hB"],GA:["H","hB"],GB:["H","h","hb","hB"],GD:["h","hb","H","hB"],GE:["H","hB","h"],GF:["H","hB"],GG:["H","h","hb","hB"],GH:["h","H"],GI:["H","h","hb","hB"],GL:["H","h"],GM:["h","hb","H","hB"],GN:["H","hB"],GP:["H","hB"],GQ:["H","hB","h","hb"],GR:["h","H","hb","hB"],GT:["h","H","hB","hb"],GU:["h","hb","H","hB"],GW:["H","hB"],GY:["h","hb","H","hB"],HK:["h","hB","hb","H"],HN:["h","H","hB","hb"],HR:["H","hB"],HU:["H","h"],IC:["H","h","hB","hb"],ID:["H"],IE:["H","h","hb","hB"],IL:["H","hB"],IM:["H","h","hb","hB"],IN:["h","H"],IO:["H","h","hb","hB"],IQ:["h","hB","hb","H"],IR:["hB","H"],IS:["H"],IT:["H","hB"],JE:["H","h","hb","hB"],JM:["h","hb","H","hB"],JO:["h","hB","hb","H"],JP:["H","K","h"],KE:["hB","hb","H","h"],KG:["H","h","hB","hb"],KH:["hB","h","H","hb"],KI:["h","hb","H","hB"],KM:["H","h","hB","hb"],KN:["h","hb","H","hB"],KP:["h","H","hB","hb"],KR:["h","H","hB","hb"],KW:["h","hB","hb","H"],KY:["h","hb","H","hB"],KZ:["H","hB"],LA:["H","hb","hB","h"],LB:["h","hB","hb","H"],LC:["h","hb","H","hB"],LI:["H","hB","h"],LK:["H","h","hB","hb"],LR:["h","hb","H","hB"],LS:["h","H"],LT:["H","h","hb","hB"],LU:["H","h","hB"],LV:["H","hB","hb","h"],LY:["h","hB","hb","H"],MA:["H","h","hB","hb"],MC:["H","hB"],MD:["H","hB"],ME:["H","hB","h"],MF:["H","hB"],MG:["H","h"],MH:["h","hb","H","hB"],MK:["H","h","hb","hB"],ML:["H"],MM:["hB","hb","H","h"],MN:["H","h","hb","hB"],MO:["h","hB","hb","H"],MP:["h","hb","H","hB"],MQ:["H","hB"],MR:["h","hB","hb","H"],MS:["H","h","hb","hB"],MT:["H","h"],MU:["H","h"],MV:["H","h"],MW:["h","hb","H","hB"],MX:["h","H","hB","hb"],MY:["hb","hB","h","H"],MZ:["H","hB"],NA:["h","H","hB","hb"],NC:["H","hB"],NE:["H"],NF:["H","h","hb","hB"],NG:["H","h","hb","hB"],NI:["h","H","hB","hb"],NL:["H","hB"],NO:["H","h"],NP:["H","h","hB"],NR:["H","h","hb","hB"],NU:["H","h","hb","hB"],NZ:["h","hb","H","hB"],OM:["h","hB","hb","H"],PA:["h","H","hB","hb"],PE:["h","H","hB","hb"],PF:["H","h","hB"],PG:["h","H"],PH:["h","hB","hb","H"],PK:["h","hB","H"],PL:["H","h"],PM:["H","hB"],PN:["H","h","hb","hB"],PR:["h","H","hB","hb"],PS:["h","hB","hb","H"],PT:["H","hB"],PW:["h","H"],PY:["h","H","hB","hb"],QA:["h","hB","hb","H"],RE:["H","hB"],RO:["H","hB"],RS:["H","hB","h"],RU:["H"],RW:["H","h"],SA:["h","hB","hb","H"],SB:["h","hb","H","hB"],SC:["H","h","hB"],SD:["h","hB","hb","H"],SE:["H"],SG:["h","hb","H","hB"],SH:["H","h","hb","hB"],SI:["H","hB"],SJ:["H"],SK:["H"],SL:["h","hb","H","hB"],SM:["H","h","hB"],SN:["H","h","hB"],SO:["h","H"],SR:["H","hB"],SS:["h","hb","H","hB"],ST:["H","hB"],SV:["h","H","hB","hb"],SX:["H","h","hb","hB"],SY:["h","hB","hb","H"],SZ:["h","hb","H","hB"],TA:["H","h","hb","hB"],TC:["h","hb","H","hB"],TD:["h","H","hB"],TF:["H","h","hB"],TG:["H","hB"],TH:["H","h"],TJ:["H","h"],TL:["H","hB","hb","h"],TM:["H","h"],TN:["h","hB","hb","H"],TO:["h","H"],TR:["H","hB"],TT:["h","hb","H","hB"],TW:["hB","hb","h","H"],TZ:["hB","hb","H","h"],UA:["H","hB","h"],UG:["hB","hb","H","h"],UM:["h","hb","H","hB"],US:["h","hb","H","hB"],UY:["h","H","hB","hb"],UZ:["H","hB","h"],VA:["H","h","hB"],VC:["h","hb","H","hB"],VE:["h","H","hB","hb"],VG:["h","hb","H","hB"],VI:["h","hb","H","hB"],VN:["H","h"],VU:["h","H"],WF:["H","hB"],WS:["h","H"],XK:["H","hB","h"],YE:["h","hB","hb","H"],YT:["H","hB"],ZA:["H","h","hb","hB"],ZM:["h","hb","H","hB"],ZW:["H","h"],"af-ZA":["H","h","hB","hb"],"ar-001":["h","hB","hb","H"],"ca-ES":["H","h","hB"],"en-001":["h","hb","H","hB"],"en-HK":["h","hb","H","hB"],"en-IL":["H","h","hb","hB"],"en-MY":["h","hb","H","hB"],"es-BR":["H","h","hB","hb"],"es-ES":["H","h","hB","hb"],"es-GQ":["H","h","hB","hb"],"fr-CA":["H","h","hB"],"gl-ES":["H","h","hB"],"gu-IN":["hB","hb","h","H"],"hi-IN":["hB","h","H"],"it-CH":["H","h","hB"],"it-IT":["H","h","hB"],"kn-IN":["hB","h","H"],"ml-IN":["hB","h","H"],"mr-IN":["hB","hb","h","H"],"pa-IN":["hB","hb","h","H"],"ta-IN":["hB","h","hb","H"],"te-IN":["hB","h","H"],"zu-ZA":["H","hB","hb","h"]};function fi(e,t){for(var n="",r=0;r<e.length;r++){var i=e.charAt(r);if(i==="j"){for(var o=0;r+1<e.length&&e.charAt(r+1)===i;)o++,r++;var s=1+(o&1),a=o<2?1:3+(o>>1),h="a",l=pi(t);for((l=="H"||l=="k")&&(a=0);a-- >0;)n+=h;for(;s-- >0;)n=l+n;}else i==="J"?n+="H":n+=i;}return n}function pi(e){var t=e.hourCycle;if(t===void 0&&e.hourCycles&&e.hourCycles.length&&(t=e.hourCycles[0]),t)switch(t){case"h24":return "k";case"h23":return "H";case"h12":return "h";case"h11":return "K";default:throw new Error("Invalid hourCycle")}var n=e.language,r;n!=="root"&&(r=e.maximize().region);var i=Fe$1[r||""]||Fe$1[n||""]||Fe$1["".concat(n,"-001")]||Fe$1["001"];return i[0]}var ot$3,di=new RegExp("^".concat(Nn$1.source,"*")),mi=new RegExp("".concat(Nn$1.source,"*$"));function T(e,t){return {start:e,end:t}}var _i=!!String.prototype.startsWith&&"_a".startsWith("a",1),Ai=!!String.fromCodePoint,gi=!!Object.fromEntries,bi=!!String.prototype.codePointAt,vi=!!String.prototype.trimStart,yi=!!String.prototype.trimEnd,wi=!!Number.isSafeInteger,Ci=wi?Number.isSafeInteger:function(e){return typeof e=="number"&&isFinite(e)&&Math.floor(e)===e&&Math.abs(e)<=9007199254740991},mt$2=!0;try{var Ei=Dn$1("([^\\p{White_Space}\\p{Pattern_Syntax}]*)","yu");mt$2=((ot$3=Ei.exec("a"))===null||ot$3===void 0?void 0:ot$3[0])==="a";}catch{mt$2=!1;}var Vt$2=_i?function(t,n,r){return t.startsWith(n,r)}:function(t,n,r){return t.slice(r,r+n.length)===n},_t$2=Ai?String.fromCodePoint:function(){for(var t=[],n=0;n<arguments.length;n++)t[n]=arguments[n];for(var r="",i=t.length,o=0,s;i>o;){if(s=t[o++],s>1114111)throw RangeError(s+" is not a valid code point");r+=s<65536?String.fromCharCode(s):String.fromCharCode(((s-=65536)>>10)+55296,s%1024+56320);}return r},qt=gi?Object.fromEntries:function(t){for(var n={},r=0,i=t;r<i.length;r++){var o=i[r],s=o[0],a=o[1];n[s]=a;}return n},Rn$1=bi?function(t,n){return t.codePointAt(n)}:function(t,n){var r=t.length;if(!(n<0||n>=r)){var i=t.charCodeAt(n),o;return i<55296||i>56319||n+1===r||(o=t.charCodeAt(n+1))<56320||o>57343?i:(i-55296<<10)+(o-56320)+65536}},xi=vi?function(t){return t.trimStart()}:function(t){return t.replace(di,"")},Si=yi?function(t){return t.trimEnd()}:function(t){return t.replace(mi,"")};function Dn$1(e,t){return new RegExp(e,t)}var At$2;if(mt$2){var Qt$1=Dn$1("([^\\p{White_Space}\\p{Pattern_Syntax}]*)","yu");At$2=function(t,n){var r;Qt$1.lastIndex=n;var i=Qt$1.exec(t);return (r=i[1])!==null&&r!==void 0?r:""};}else At$2=function(t,n){for(var r=[];;){var i=Rn$1(t,n);if(i===void 0||Un$1(i)||Oi(i))break;r.push(i),n+=i>=65536?2:1;}return _t$2.apply(void 0,r)};var Bi=function(){function e(t,n){n===void 0&&(n={}),this.message=t,this.position={offset:0,line:1,column:1},this.ignoreTag=!!n.ignoreTag,this.locale=n.locale,this.requiresOtherClause=!!n.requiresOtherClause,this.shouldParseSkeletons=!!n.shouldParseSkeletons;}return e.prototype.parse=function(){if(this.offset()!==0)throw Error("parser can only be used once");return this.parseMessage(0,"",!1)},e.prototype.parseMessage=function(t,n,r){for(var i=[];!this.isEOF();){var o=this.char();if(o===123){var s=this.parseArgument(t,r);if(s.err)return s;i.push(s.val);}else {if(o===125&&t>0)break;if(o===35&&(n==="plural"||n==="selectordinal")){var a=this.clonePosition();this.bump(),i.push({type:M.pound,location:T(a,this.clonePosition())});}else if(o===60&&!this.ignoreTag&&this.peek()===47){if(r)break;return this.error(I$1.UNMATCHED_CLOSING_TAG,T(this.clonePosition(),this.clonePosition()))}else if(o===60&&!this.ignoreTag&&gt$2(this.peek()||0)){var s=this.parseTag(t,n);if(s.err)return s;i.push(s.val);}else {var s=this.parseLiteral(t,n);if(s.err)return s;i.push(s.val);}}}return {val:i,err:null}},e.prototype.parseTag=function(t,n){var r=this.clonePosition();this.bump();var i=this.parseTagName();if(this.bumpSpace(),this.bumpIf("/>"))return {val:{type:M.literal,value:"<".concat(i,"/>"),location:T(r,this.clonePosition())},err:null};if(this.bumpIf(">")){var o=this.parseMessage(t+1,n,!0);if(o.err)return o;var s=o.val,a=this.clonePosition();if(this.bumpIf("</")){if(this.isEOF()||!gt$2(this.char()))return this.error(I$1.INVALID_TAG,T(a,this.clonePosition()));var h=this.clonePosition(),l=this.parseTagName();return i!==l?this.error(I$1.UNMATCHED_CLOSING_TAG,T(h,this.clonePosition())):(this.bumpSpace(),this.bumpIf(">")?{val:{type:M.tag,value:i,children:s,location:T(r,this.clonePosition())},err:null}:this.error(I$1.INVALID_TAG,T(a,this.clonePosition())))}else return this.error(I$1.UNCLOSED_TAG,T(r,this.clonePosition()))}else return this.error(I$1.INVALID_TAG,T(r,this.clonePosition()))},e.prototype.parseTagName=function(){var t=this.offset();for(this.bump();!this.isEOF()&&Ti(this.char());)this.bump();return this.message.slice(t,this.offset())},e.prototype.parseLiteral=function(t,n){for(var r=this.clonePosition(),i="";;){var o=this.tryParseQuote(n);if(o){i+=o;continue}var s=this.tryParseUnquoted(t,n);if(s){i+=s;continue}var a=this.tryParseLeftAngleBracket();if(a){i+=a;continue}break}var h=T(r,this.clonePosition());return {val:{type:M.literal,value:i,location:h},err:null}},e.prototype.tryParseLeftAngleBracket=function(){return !this.isEOF()&&this.char()===60&&(this.ignoreTag||!Ii(this.peek()||0))?(this.bump(),"<"):null},e.prototype.tryParseQuote=function(t){if(this.isEOF()||this.char()!==39)return null;switch(this.peek()){case 39:return this.bump(),this.bump(),"'";case 123:case 60:case 62:case 125:break;case 35:if(t==="plural"||t==="selectordinal")break;return null;default:return null}this.bump();var n=[this.char()];for(this.bump();!this.isEOF();){var r=this.char();if(r===39)if(this.peek()===39)n.push(39),this.bump();else {this.bump();break}else n.push(r);this.bump();}return _t$2.apply(void 0,n)},e.prototype.tryParseUnquoted=function(t,n){if(this.isEOF())return null;var r=this.char();return r===60||r===123||r===35&&(n==="plural"||n==="selectordinal")||r===125&&t>0?null:(this.bump(),_t$2(r))},e.prototype.parseArgument=function(t,n){var r=this.clonePosition();if(this.bump(),this.bumpSpace(),this.isEOF())return this.error(I$1.EXPECT_ARGUMENT_CLOSING_BRACE,T(r,this.clonePosition()));if(this.char()===125)return this.bump(),this.error(I$1.EMPTY_ARGUMENT,T(r,this.clonePosition()));var i=this.parseIdentifierIfPossible().value;if(!i)return this.error(I$1.MALFORMED_ARGUMENT,T(r,this.clonePosition()));if(this.bumpSpace(),this.isEOF())return this.error(I$1.EXPECT_ARGUMENT_CLOSING_BRACE,T(r,this.clonePosition()));switch(this.char()){case 125:return this.bump(),{val:{type:M.argument,value:i,location:T(r,this.clonePosition())},err:null};case 44:return this.bump(),this.bumpSpace(),this.isEOF()?this.error(I$1.EXPECT_ARGUMENT_CLOSING_BRACE,T(r,this.clonePosition())):this.parseArgumentOptions(t,n,i,r);default:return this.error(I$1.MALFORMED_ARGUMENT,T(r,this.clonePosition()))}},e.prototype.parseIdentifierIfPossible=function(){var t=this.clonePosition(),n=this.offset(),r=At$2(this.message,n),i=n+r.length;this.bumpTo(i);var o=this.clonePosition(),s=T(t,o);return {value:r,location:s}},e.prototype.parseArgumentOptions=function(t,n,r,i){var o,s=this.clonePosition(),a=this.parseIdentifierIfPossible().value,h=this.clonePosition();switch(a){case"":return this.error(I$1.EXPECT_ARGUMENT_TYPE,T(s,h));case"number":case"date":case"time":{this.bumpSpace();var l=null;if(this.bumpIf(",")){this.bumpSpace();var c=this.clonePosition(),u=this.parseSimpleArgStyleIfPossible();if(u.err)return u;var f=Si(u.val);if(f.length===0)return this.error(I$1.EXPECT_ARGUMENT_STYLE,T(this.clonePosition(),this.clonePosition()));var A=T(c,this.clonePosition());l={style:f,styleLocation:A};}var _=this.tryParseArgumentClose(i);if(_.err)return _;var S=T(i,this.clonePosition());if(l&&Vt$2(l?.style,"::",0)){var w=xi(l.style.slice(2));if(a==="number"){var u=this.parseNumberSkeletonFromString(w,l.styleLocation);return u.err?u:{val:{type:M.number,value:r,location:S,style:u.val},err:null}}else {if(w.length===0)return this.error(I$1.EXPECT_DATE_TIME_SKELETON,S);var D=w;this.locale&&(D=fi(w,this.locale));var f={type:Ce$2.dateTime,pattern:D,location:l.styleLocation,parsedOptions:this.shouldParseSkeletons?oi(D):{}},R=a==="date"?M.date:M.time;return {val:{type:R,value:r,location:S,style:f},err:null}}}return {val:{type:a==="number"?M.number:a==="date"?M.date:M.time,value:r,location:S,style:(o=l?.style)!==null&&o!==void 0?o:null},err:null}}case"plural":case"selectordinal":case"select":{var L=this.clonePosition();if(this.bumpSpace(),!this.bumpIf(","))return this.error(I$1.EXPECT_SELECT_ARGUMENT_OPTIONS,T(L,H({},L)));this.bumpSpace();var F=this.parseIdentifierIfPossible(),k=0;if(a!=="select"&&F.value==="offset"){if(!this.bumpIf(":"))return this.error(I$1.EXPECT_PLURAL_ARGUMENT_OFFSET_VALUE,T(this.clonePosition(),this.clonePosition()));this.bumpSpace();var u=this.tryParseDecimalInteger(I$1.EXPECT_PLURAL_ARGUMENT_OFFSET_VALUE,I$1.INVALID_PLURAL_ARGUMENT_OFFSET_VALUE);if(u.err)return u;this.bumpSpace(),F=this.parseIdentifierIfPossible(),k=u.val;}var z=this.tryParsePluralOrSelectOptions(t,a,n,F);if(z.err)return z;var _=this.tryParseArgumentClose(i);if(_.err)return _;var P=T(i,this.clonePosition());return a==="select"?{val:{type:M.select,value:r,options:qt(z.val),location:P},err:null}:{val:{type:M.plural,value:r,options:qt(z.val),offset:k,pluralType:a==="plural"?"cardinal":"ordinal",location:P},err:null}}default:return this.error(I$1.INVALID_ARGUMENT_TYPE,T(s,h))}},e.prototype.tryParseArgumentClose=function(t){return this.isEOF()||this.char()!==125?this.error(I$1.EXPECT_ARGUMENT_CLOSING_BRACE,T(t,this.clonePosition())):(this.bump(),{val:!0,err:null})},e.prototype.parseSimpleArgStyleIfPossible=function(){for(var t=0,n=this.clonePosition();!this.isEOF();){var r=this.char();switch(r){case 39:{this.bump();var i=this.clonePosition();if(!this.bumpUntil("'"))return this.error(I$1.UNCLOSED_QUOTE_IN_ARGUMENT_STYLE,T(i,this.clonePosition()));this.bump();break}case 123:{t+=1,this.bump();break}case 125:{if(t>0)t-=1;else return {val:this.message.slice(n.offset,this.offset()),err:null};break}default:this.bump();break}}return {val:this.message.slice(n.offset,this.offset()),err:null}},e.prototype.parseNumberSkeletonFromString=function(t,n){var r=[];try{r=ai(t);}catch{return this.error(I$1.INVALID_NUMBER_SKELETON,n)}return {val:{type:Ce$2.number,tokens:r,location:n,parsedOptions:this.shouldParseSkeletons?hi(r):{}},err:null}},e.prototype.tryParsePluralOrSelectOptions=function(t,n,r,i){for(var o,s=!1,a=[],h=new Set,l=i.value,c=i.location;;){if(l.length===0){var u=this.clonePosition();if(n!=="select"&&this.bumpIf("=")){var f=this.tryParseDecimalInteger(I$1.EXPECT_PLURAL_ARGUMENT_SELECTOR,I$1.INVALID_PLURAL_ARGUMENT_SELECTOR);if(f.err)return f;c=T(u,this.clonePosition()),l=this.message.slice(u.offset,this.offset());}else break}if(h.has(l))return this.error(n==="select"?I$1.DUPLICATE_SELECT_ARGUMENT_SELECTOR:I$1.DUPLICATE_PLURAL_ARGUMENT_SELECTOR,c);l==="other"&&(s=!0),this.bumpSpace();var A=this.clonePosition();if(!this.bumpIf("{"))return this.error(n==="select"?I$1.EXPECT_SELECT_ARGUMENT_SELECTOR_FRAGMENT:I$1.EXPECT_PLURAL_ARGUMENT_SELECTOR_FRAGMENT,T(this.clonePosition(),this.clonePosition()));var _=this.parseMessage(t+1,n,r);if(_.err)return _;var S=this.tryParseArgumentClose(A);if(S.err)return S;a.push([l,{value:_.val,location:T(A,this.clonePosition())}]),h.add(l),this.bumpSpace(),o=this.parseIdentifierIfPossible(),l=o.value,c=o.location;}return a.length===0?this.error(n==="select"?I$1.EXPECT_SELECT_ARGUMENT_SELECTOR:I$1.EXPECT_PLURAL_ARGUMENT_SELECTOR,T(this.clonePosition(),this.clonePosition())):this.requiresOtherClause&&!s?this.error(I$1.MISSING_OTHER_CLAUSE,T(this.clonePosition(),this.clonePosition())):{val:a,err:null}},e.prototype.tryParseDecimalInteger=function(t,n){var r=1,i=this.clonePosition();this.bumpIf("+")||this.bumpIf("-")&&(r=-1);for(var o=!1,s=0;!this.isEOF();){var a=this.char();if(a>=48&&a<=57)o=!0,s=s*10+(a-48),this.bump();else break}var h=T(i,this.clonePosition());return o?(s*=r,Ci(s)?{val:s,err:null}:this.error(n,h)):this.error(t,h)},e.prototype.offset=function(){return this.position.offset},e.prototype.isEOF=function(){return this.offset()===this.message.length},e.prototype.clonePosition=function(){return {offset:this.position.offset,line:this.position.line,column:this.position.column}},e.prototype.char=function(){var t=this.position.offset;if(t>=this.message.length)throw Error("out of bound");var n=Rn$1(this.message,t);if(n===void 0)throw Error("Offset ".concat(t," is at invalid UTF-16 code unit boundary"));return n},e.prototype.error=function(t,n){return {val:null,err:{kind:t,message:this.message,location:n}}},e.prototype.bump=function(){if(!this.isEOF()){var t=this.char();t===10?(this.position.line+=1,this.position.column=1,this.position.offset+=1):(this.position.column+=1,this.position.offset+=t<65536?1:2);}},e.prototype.bumpIf=function(t){if(Vt$2(this.message,t,this.offset())){for(var n=0;n<t.length;n++)this.bump();return !0}return !1},e.prototype.bumpUntil=function(t){var n=this.offset(),r=this.message.indexOf(t,n);return r>=0?(this.bumpTo(r),!0):(this.bumpTo(this.message.length),!1)},e.prototype.bumpTo=function(t){if(this.offset()>t)throw Error("targetOffset ".concat(t," must be greater than or equal to the current offset ").concat(this.offset()));for(t=Math.min(t,this.message.length);;){var n=this.offset();if(n===t)break;if(n>t)throw Error("targetOffset ".concat(t," is at invalid UTF-16 code unit boundary"));if(this.bump(),this.isEOF())break}},e.prototype.bumpSpace=function(){for(;!this.isEOF()&&Un$1(this.char());)this.bump();},e.prototype.peek=function(){if(this.isEOF())return null;var t=this.char(),n=this.offset(),r=this.message.charCodeAt(n+(t>=65536?2:1));return r??null},e}();function gt$2(e){return e>=97&&e<=122||e>=65&&e<=90}function Ii(e){return gt$2(e)||e===47}function Ti(e){return e===45||e===46||e>=48&&e<=57||e===95||e>=97&&e<=122||e>=65&&e<=90||e==183||e>=192&&e<=214||e>=216&&e<=246||e>=248&&e<=893||e>=895&&e<=8191||e>=8204&&e<=8205||e>=8255&&e<=8256||e>=8304&&e<=8591||e>=11264&&e<=12271||e>=12289&&e<=55295||e>=63744&&e<=64975||e>=65008&&e<=65533||e>=65536&&e<=983039}function Un$1(e){return e>=9&&e<=13||e===32||e===133||e>=8206&&e<=8207||e===8232||e===8233}function Oi(e){return e>=33&&e<=35||e===36||e>=37&&e<=39||e===40||e===41||e===42||e===43||e===44||e===45||e>=46&&e<=47||e>=58&&e<=59||e>=60&&e<=62||e>=63&&e<=64||e===91||e===92||e===93||e===94||e===96||e===123||e===124||e===125||e===126||e===161||e>=162&&e<=165||e===166||e===167||e===169||e===171||e===172||e===174||e===176||e===177||e===182||e===187||e===191||e===215||e===247||e>=8208&&e<=8213||e>=8214&&e<=8215||e===8216||e===8217||e===8218||e>=8219&&e<=8220||e===8221||e===8222||e===8223||e>=8224&&e<=8231||e>=8240&&e<=8248||e===8249||e===8250||e>=8251&&e<=8254||e>=8257&&e<=8259||e===8260||e===8261||e===8262||e>=8263&&e<=8273||e===8274||e===8275||e>=8277&&e<=8286||e>=8592&&e<=8596||e>=8597&&e<=8601||e>=8602&&e<=8603||e>=8604&&e<=8607||e===8608||e>=8609&&e<=8610||e===8611||e>=8612&&e<=8613||e===8614||e>=8615&&e<=8621||e===8622||e>=8623&&e<=8653||e>=8654&&e<=8655||e>=8656&&e<=8657||e===8658||e===8659||e===8660||e>=8661&&e<=8691||e>=8692&&e<=8959||e>=8960&&e<=8967||e===8968||e===8969||e===8970||e===8971||e>=8972&&e<=8991||e>=8992&&e<=8993||e>=8994&&e<=9e3||e===9001||e===9002||e>=9003&&e<=9083||e===9084||e>=9085&&e<=9114||e>=9115&&e<=9139||e>=9140&&e<=9179||e>=9180&&e<=9185||e>=9186&&e<=9254||e>=9255&&e<=9279||e>=9280&&e<=9290||e>=9291&&e<=9311||e>=9472&&e<=9654||e===9655||e>=9656&&e<=9664||e===9665||e>=9666&&e<=9719||e>=9720&&e<=9727||e>=9728&&e<=9838||e===9839||e>=9840&&e<=10087||e===10088||e===10089||e===10090||e===10091||e===10092||e===10093||e===10094||e===10095||e===10096||e===10097||e===10098||e===10099||e===10100||e===10101||e>=10132&&e<=10175||e>=10176&&e<=10180||e===10181||e===10182||e>=10183&&e<=10213||e===10214||e===10215||e===10216||e===10217||e===10218||e===10219||e===10220||e===10221||e===10222||e===10223||e>=10224&&e<=10239||e>=10240&&e<=10495||e>=10496&&e<=10626||e===10627||e===10628||e===10629||e===10630||e===10631||e===10632||e===10633||e===10634||e===10635||e===10636||e===10637||e===10638||e===10639||e===10640||e===10641||e===10642||e===10643||e===10644||e===10645||e===10646||e===10647||e===10648||e>=10649&&e<=10711||e===10712||e===10713||e===10714||e===10715||e>=10716&&e<=10747||e===10748||e===10749||e>=10750&&e<=11007||e>=11008&&e<=11055||e>=11056&&e<=11076||e>=11077&&e<=11078||e>=11079&&e<=11084||e>=11085&&e<=11123||e>=11124&&e<=11125||e>=11126&&e<=11157||e===11158||e>=11159&&e<=11263||e>=11776&&e<=11777||e===11778||e===11779||e===11780||e===11781||e>=11782&&e<=11784||e===11785||e===11786||e===11787||e===11788||e===11789||e>=11790&&e<=11798||e===11799||e>=11800&&e<=11801||e===11802||e===11803||e===11804||e===11805||e>=11806&&e<=11807||e===11808||e===11809||e===11810||e===11811||e===11812||e===11813||e===11814||e===11815||e===11816||e===11817||e>=11818&&e<=11822||e===11823||e>=11824&&e<=11833||e>=11834&&e<=11835||e>=11836&&e<=11839||e===11840||e===11841||e===11842||e>=11843&&e<=11855||e>=11856&&e<=11857||e===11858||e>=11859&&e<=11903||e>=12289&&e<=12291||e===12296||e===12297||e===12298||e===12299||e===12300||e===12301||e===12302||e===12303||e===12304||e===12305||e>=12306&&e<=12307||e===12308||e===12309||e===12310||e===12311||e===12312||e===12313||e===12314||e===12315||e===12316||e===12317||e>=12318&&e<=12319||e===12320||e===12336||e===64830||e===64831||e>=65093&&e<=65094}function bt$1(e){e.forEach(function(t){if(delete t.location,Tn$1(t)||On$1(t))for(var n in t.options)delete t.options[n].location,bt$1(t.options[n].value);else Sn$1(t)&&Pn$1(t.style)||(Bn$2(t)||In$1(t))&&dt$3(t.style)?delete t.style.location:Hn$1(t)&&bt$1(t.children);});}function Hi(e,t){t===void 0&&(t={}),t=H({shouldParseSkeletons:!0,requiresOtherClause:!0},t);var n=new Bi(e,t).parse();if(n.err){var r=SyntaxError(I$1[n.err.kind]);throw r.location=n.err.location,r.originalMessage=n.err.message,r}return t?.captureLocation||bt$1(n.val),n.val}var Ee$2;(function(e){e.MISSING_VALUE="MISSING_VALUE",e.INVALID_VALUE="INVALID_VALUE",e.MISSING_INTL_API="MISSING_INTL_API";})(Ee$2||(Ee$2={}));var Ze$2=function(e){Ke$1(t,e);function t(n,r,i){var o=e.call(this,n)||this;return o.code=r,o.originalMessage=i,o}return t.prototype.toString=function(){return "[formatjs Error: ".concat(this.code,"] ").concat(this.message)},t}(Error),Xt$1=function(e){Ke$1(t,e);function t(n,r,i,o){return e.call(this,'Invalid values for "'.concat(n,'": "').concat(r,'". Options are "').concat(Object.keys(i).join('", "'),'"'),Ee$2.INVALID_VALUE,o)||this}return t}(Ze$2),Pi=function(e){Ke$1(t,e);function t(n,r,i){return e.call(this,'Value for "'.concat(n,'" must be of type ').concat(r),Ee$2.INVALID_VALUE,i)||this}return t}(Ze$2),Ni=function(e){Ke$1(t,e);function t(n,r){return e.call(this,'The intl string context variable "'.concat(n,'" was not provided to the string "').concat(r,'"'),Ee$2.MISSING_VALUE,r)||this}return t}(Ze$2),q;(function(e){e[e.literal=0]="literal",e[e.object=1]="object";})(q||(q={}));function ki(e){return e.length<2?e:e.reduce(function(t,n){var r=t[t.length-1];return !r||r.type!==q.literal||n.type!==q.literal?t.push(n):r.value+=n.value,t},[])}function Mi(e){return typeof e=="function"}function $e$1(e,t,n,r,i,o,s){if(e.length===1&&Ft$1(e[0]))return [{type:q.literal,value:e[0].value}];for(var a=[],h=0,l=e;h<l.length;h++){var c=l[h];if(Ft$1(c)){a.push({type:q.literal,value:c.value});continue}if(ri(c)){typeof o=="number"&&a.push({type:q.literal,value:n.getNumberFormat(t).format(o)});continue}var u=c.value;if(!(i&&u in i))throw new Ni(u,s);var f=i[u];if(ni(c)){(!f||typeof f=="string"||typeof f=="number")&&(f=typeof f=="string"||typeof f=="number"?String(f):""),a.push({type:typeof f=="string"?q.literal:q.object,value:f});continue}if(Bn$2(c)){var A=typeof c.style=="string"?r.date[c.style]:dt$3(c.style)?c.style.parsedOptions:void 0;a.push({type:q.literal,value:n.getDateTimeFormat(t,A).format(f)});continue}if(In$1(c)){var A=typeof c.style=="string"?r.time[c.style]:dt$3(c.style)?c.style.parsedOptions:r.time.medium;a.push({type:q.literal,value:n.getDateTimeFormat(t,A).format(f)});continue}if(Sn$1(c)){var A=typeof c.style=="string"?r.number[c.style]:Pn$1(c.style)?c.style.parsedOptions:void 0;A&&A.scale&&(f=f*(A.scale||1)),a.push({type:q.literal,value:n.getNumberFormat(t,A).format(f)});continue}if(Hn$1(c)){var _=c.children,S=c.value,w=i[S];if(!Mi(w))throw new Pi(S,"function",s);var D=$e$1(_,t,n,r,i,o),R=w(D.map(function(k){return k.value}));Array.isArray(R)||(R=[R]),a.push.apply(a,R.map(function(k){return {type:typeof k=="string"?q.literal:q.object,value:k}}));}if(Tn$1(c)){var L=c.options[f]||c.options.other;if(!L)throw new Xt$1(c.value,f,Object.keys(c.options),s);a.push.apply(a,$e$1(L.value,t,n,r,i));continue}if(On$1(c)){var L=c.options["=".concat(f)];if(!L){if(!Intl.PluralRules)throw new Ze$2(`Intl.PluralRules is not available in this environment.
Try polyfilling it using "@formatjs/intl-pluralrules"
`,Ee$2.MISSING_INTL_API,s);var F=n.getPluralRules(t,{type:c.pluralType}).select(f-(c.offset||0));L=c.options[F]||c.options.other;}if(!L)throw new Xt$1(c.value,f,Object.keys(c.options),s);a.push.apply(a,$e$1(L.value,t,n,r,i,f-(c.offset||0)));continue}}return ki(a)}function Li(e,t){return t?H(H(H({},e||{}),t||{}),Object.keys(e).reduce(function(n,r){return n[r]=H(H({},e[r]),t[r]||{}),n},{})):e}function Ri(e,t){return t?Object.keys(e).reduce(function(n,r){return n[r]=Li(e[r],t[r]),n},H({},e)):e}function st$3(e){return {create:function(){return {get:function(t){return e[t]},set:function(t,n){e[t]=n;}}}}}function Di(e){return e===void 0&&(e={number:{},dateTime:{},pluralRules:{}}),{getNumberFormat:rt$2(function(){for(var t,n=[],r=0;r<arguments.length;r++)n[r]=arguments[r];return new((t=Intl.NumberFormat).bind.apply(t,nt$2([void 0],n,!1)))},{cache:st$3(e.number),strategy:it$3.variadic}),getDateTimeFormat:rt$2(function(){for(var t,n=[],r=0;r<arguments.length;r++)n[r]=arguments[r];return new((t=Intl.DateTimeFormat).bind.apply(t,nt$2([void 0],n,!1)))},{cache:st$3(e.dateTime),strategy:it$3.variadic}),getPluralRules:rt$2(function(){for(var t,n=[],r=0;r<arguments.length;r++)n[r]=arguments[r];return new((t=Intl.PluralRules).bind.apply(t,nt$2([void 0],n,!1)))},{cache:st$3(e.pluralRules),strategy:it$3.variadic})}}var jn$1=function(){function e(t,n,r,i){n===void 0&&(n=e.defaultLocale);var o=this;if(this.formatterCache={number:{},dateTime:{},pluralRules:{}},this.format=function(h){var l=o.formatToParts(h);if(l.length===1)return l[0].value;var c=l.reduce(function(u,f){return !u.length||f.type!==q.literal||typeof u[u.length-1]!="string"?u.push(f.value):u[u.length-1]+=f.value,u},[]);return c.length<=1?c[0]||"":c},this.formatToParts=function(h){return $e$1(o.ast,o.locales,o.formatters,o.formats,h,void 0,o.message)},this.resolvedOptions=function(){var h;return {locale:((h=o.resolvedLocale)===null||h===void 0?void 0:h.toString())||Intl.NumberFormat.supportedLocalesOf(o.locales)[0]}},this.getAst=function(){return o.ast},this.locales=n,this.resolvedLocale=e.resolveLocale(n),typeof t=="string"){if(this.message=t,!e.__parse)throw new TypeError("IntlMessageFormat.__parse must be set to process `message` of type `string`");var s=i||{};s.formatters;var a=Qr$1(s,["formatters"]);this.ast=e.__parse(t,H(H({},a),{locale:this.resolvedLocale}));}else this.ast=t;if(!Array.isArray(this.ast))throw new TypeError("A message must be provided as a String or AST.");this.formats=Ri(e.formats,r),this.formatters=i&&i.formatters||Di(this.formatterCache);}return Object.defineProperty(e,"defaultLocale",{get:function(){return e.memoizedDefaultLocale||(e.memoizedDefaultLocale=new Intl.NumberFormat().resolvedOptions().locale),e.memoizedDefaultLocale},enumerable:!1,configurable:!0}),e.memoizedDefaultLocale=null,e.resolveLocale=function(t){if(!(typeof Intl.Locale>"u")){var n=Intl.NumberFormat.supportedLocalesOf(t);return n.length>0?new Intl.Locale(n[0]):new Intl.Locale(typeof t=="string"?t:t[0])}},e.__parse=Hi,e.formats={number:{integer:{maximumFractionDigits:0},currency:{style:"currency"},percent:{style:"percent"}},date:{short:{month:"numeric",day:"numeric",year:"2-digit"},medium:{month:"short",day:"numeric",year:"numeric"},long:{month:"long",day:"numeric",year:"numeric"},full:{weekday:"long",month:"long",day:"numeric",year:"numeric"}},time:{short:{hour:"numeric",minute:"numeric"},medium:{hour:"numeric",minute:"numeric",second:"numeric"},long:{hour:"numeric",minute:"numeric",second:"numeric",timeZoneName:"short"},full:{hour:"numeric",minute:"numeric",second:"numeric",timeZoneName:"short"}}},e}();function Ui(e,t){if(t==null)return;if(t in e)return e[t];const n=t.split(".");let r=e;for(let i=0;i<n.length;i++)if(typeof r=="object"){if(i>0){const o=n.slice(i,n.length).join(".");if(o in r){r=r[o];break}}r=r[n[i]];}else r=void 0;return r}const pe$2={},ji=(e,t,n)=>n&&(t in pe$2||(pe$2[t]={}),e in pe$2[t]||(pe$2[t][e]=n),n),Gn$1=(e,t)=>{if(t==null)return;if(t in pe$2&&e in pe$2[t])return pe$2[t][e];const n=je$2(t);for(let r=0;r<n.length;r++){const i=n[r],o=Fi(i,e);if(o)return ji(e,t,o)}};let Tt$2;const Be$1=writable({});function Gi(e){return Tt$2[e]||null}function Ot$2(e){return e in Tt$2}function Fi(e,t){if(!Ot$2(e))return null;const n=Gi(e);return Ui(n,t)}function zi(e){if(e==null)return;const t=je$2(e);for(let n=0;n<t.length;n++){const r=t[n];if(Ot$2(r))return r}}function We$2(e,...t){delete pe$2[e],Be$1.update(n=>(n[e]=qr$1.all([n[e]||{},...t]),n));}derived([Be$1],([e])=>Object.keys(e));Be$1.subscribe(e=>Tt$2=e);const ke$1={};function $i(e){ke$1[e]=new Set;}function Wi(e,t){ke$1[e].delete(t),ke$1[e].size===0&&delete ke$1[e];}function Me$2(e){return ke$1[e]}function Vi(e){return je$2(e).map(t=>{const n=Me$2(t);return [t,n?[...n]:[]]}).filter(([,t])=>t.length>0)}function Ve$2(e){return e==null?!1:je$2(e).some(t=>{var n;return (n=Me$2(t))==null?void 0:n.size})}function qi(e,t){return Promise.all(t.map(r=>(Wi(e,r),r().then(i=>i.default||i)))).then(r=>We$2(e,...r))}const He$1={};function Fn$1(e){if(!Ve$2(e))return e in He$1?He$1[e]:Promise.resolve();const t=Vi(e);return He$1[e]=Promise.all(t.map(([n,r])=>qi(n,r))).then(()=>{if(Ve$2(e))return Fn$1(e);delete He$1[e];}),He$1[e]}function Qi(e,t){Me$2(e)||$i(e);const n=Me$2(e);Me$2(e).has(t)||(Ot$2(e)||Be$1.update(r=>(r[e]={},r)),n.add(t));}var Kt$2=Object.getOwnPropertySymbols,Xi=Object.prototype.hasOwnProperty,Ki=Object.prototype.propertyIsEnumerable,Zi=(e,t)=>{var n={};for(var r in e)Xi.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&Kt$2)for(var r of Kt$2(e))t.indexOf(r)<0&&Ki.call(e,r)&&(n[r]=e[r]);return n};const Yi={number:{scientific:{notation:"scientific"},engineering:{notation:"engineering"},compactLong:{notation:"compact",compactDisplay:"long"},compactShort:{notation:"compact",compactDisplay:"short"}},date:{short:{month:"numeric",day:"numeric",year:"2-digit"},medium:{month:"short",day:"numeric",year:"numeric"},long:{month:"long",day:"numeric",year:"numeric"},full:{weekday:"long",month:"long",day:"numeric",year:"numeric"}},time:{short:{hour:"numeric",minute:"numeric"},medium:{hour:"numeric",minute:"numeric",second:"numeric"},long:{hour:"numeric",minute:"numeric",second:"numeric",timeZoneName:"short"},full:{hour:"numeric",minute:"numeric",second:"numeric",timeZoneName:"short"}}};function Ji({locale:e,id:t}){console.warn(`[svelte-i18n] The message "${t}" was not found in "${je$2(e).join('", "')}".${Ve$2(me$2())?`

Note: there are at least one loader still registered to this locale that wasn't executed.`:""}`);}const eo={fallbackLocale:null,loadingDelay:200,formats:Yi,warnOnMissingMessages:!0,handleMissingMessage:void 0,ignoreTag:!0},Ne$1=eo;function xe$2(){return Ne$1}function to(e){const t=e,{formats:n}=t,r=Zi(t,["formats"]);let i=e.fallbackLocale;if(e.initialLocale)try{jn$1.resolveLocale(e.initialLocale)&&(i=e.initialLocale);}catch{console.warn(`[svelte-i18n] The initial locale "${e.initialLocale}" is not a valid locale.`);}return r.warnOnMissingMessages&&(delete r.warnOnMissingMessages,r.handleMissingMessage==null?r.handleMissingMessage=Ji:console.warn('[svelte-i18n] The "warnOnMissingMessages" option is deprecated. Please use the "handleMissingMessage" option instead.')),Object.assign(Ne$1,r,{initialLocale:i}),n&&("number"in n&&Object.assign(Ne$1.formats.number,n.number),"date"in n&&Object.assign(Ne$1.formats.date,n.date),"time"in n&&Object.assign(Ne$1.formats.time,n.time)),be$2.set(i)}const at$5=writable(!1);var no=Object.defineProperty,ro=Object.defineProperties,io=Object.getOwnPropertyDescriptors,Zt$2=Object.getOwnPropertySymbols,oo=Object.prototype.hasOwnProperty,so=Object.prototype.propertyIsEnumerable,Yt$2=(e,t,n)=>t in e?no(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n,ao=(e,t)=>{for(var n in t||(t={}))oo.call(t,n)&&Yt$2(e,n,t[n]);if(Zt$2)for(var n of Zt$2(t))so.call(t,n)&&Yt$2(e,n,t[n]);return e},lo=(e,t)=>ro(e,io(t));let vt$3;const qe$1=writable(null);function Jt$2(e){return e.split("-").map((t,n,r)=>r.slice(0,n+1).join("-")).reverse()}function je$2(e,t=xe$2().fallbackLocale){const n=Jt$2(e);return t?[...new Set([...n,...Jt$2(t)])]:n}function me$2(){return vt$3??void 0}qe$1.subscribe(e=>{vt$3=e??void 0,typeof window<"u"&&e!=null&&document.documentElement.setAttribute("lang",e);});const co=e=>{if(e&&zi(e)&&Ve$2(e)){const{loadingDelay:t}=xe$2();let n;return typeof window<"u"&&me$2()!=null&&t?n=window.setTimeout(()=>at$5.set(!0),t):at$5.set(!0),Fn$1(e).then(()=>{qe$1.set(e);}).finally(()=>{clearTimeout(n),at$5.set(!1);})}return qe$1.set(e)},be$2=lo(ao({},qe$1),{set:co}),uo=()=>typeof window>"u"?null:window.navigator.language||window.navigator.languages[0],Ye=e=>{const t=Object.create(null);return r=>{const i=JSON.stringify(r);return i in t?t[i]:t[i]=e(r)}};var ho=Object.defineProperty,Qe$1=Object.getOwnPropertySymbols,zn$1=Object.prototype.hasOwnProperty,$n$1=Object.prototype.propertyIsEnumerable,en$1=(e,t,n)=>t in e?ho(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n,Ht=(e,t)=>{for(var n in t||(t={}))zn$1.call(t,n)&&en$1(e,n,t[n]);if(Qe$1)for(var n of Qe$1(t))$n$1.call(t,n)&&en$1(e,n,t[n]);return e},Ie$2=(e,t)=>{var n={};for(var r in e)zn$1.call(e,r)&&t.indexOf(r)<0&&(n[r]=e[r]);if(e!=null&&Qe$1)for(var r of Qe$1(e))t.indexOf(r)<0&&$n$1.call(e,r)&&(n[r]=e[r]);return n};const Ue$2=(e,t)=>{const{formats:n}=xe$2();if(e in n&&t in n[e])return n[e][t];throw new Error(`[svelte-i18n] Unknown "${t}" ${e} format.`)},fo=Ye(e=>{var t=e,{locale:n,format:r}=t,i=Ie$2(t,["locale","format"]);if(n==null)throw new Error('[svelte-i18n] A "locale" must be set to format numbers');return r&&(i=Ue$2("number",r)),new Intl.NumberFormat(n,i)}),po=Ye(e=>{var t=e,{locale:n,format:r}=t,i=Ie$2(t,["locale","format"]);if(n==null)throw new Error('[svelte-i18n] A "locale" must be set to format dates');return r?i=Ue$2("date",r):Object.keys(i).length===0&&(i=Ue$2("date","short")),new Intl.DateTimeFormat(n,i)}),mo=Ye(e=>{var t=e,{locale:n,format:r}=t,i=Ie$2(t,["locale","format"]);if(n==null)throw new Error('[svelte-i18n] A "locale" must be set to format time values');return r?i=Ue$2("time",r):Object.keys(i).length===0&&(i=Ue$2("time","short")),new Intl.DateTimeFormat(n,i)}),_o=(e={})=>{var t=e,{locale:n=me$2()}=t,r=Ie$2(t,["locale"]);return fo(Ht({locale:n},r))},Ao=(e={})=>{var t=e,{locale:n=me$2()}=t,r=Ie$2(t,["locale"]);return po(Ht({locale:n},r))},go=(e={})=>{var t=e,{locale:n=me$2()}=t,r=Ie$2(t,["locale"]);return mo(Ht({locale:n},r))},bo=Ye((e,t=me$2())=>new jn$1(e,t,xe$2().formats,{ignoreTag:xe$2().ignoreTag})),vo=(e,t={})=>{var n,r,i,o;let s=t;typeof e=="object"&&(s=e,e=s.id);const{values:a,locale:h=me$2(),default:l}=s;if(h==null)throw new Error("[svelte-i18n] Cannot format a message without first setting the initial locale.");let c=Gn$1(e,h);if(!c)c=(o=(i=(r=(n=xe$2()).handleMissingMessage)==null?void 0:r.call(n,{locale:h,id:e,defaultValue:l}))!=null?i:l)!=null?o:e;else if(typeof c!="string")return console.warn(`[svelte-i18n] Message with id "${e}" must be of type "string", found: "${typeof c}". Gettin its value through the "$format" method is deprecated; use the "json" method instead.`),c;if(!a)return c;let u=c;try{u=bo(c,h).format(a);}catch(f){f instanceof Error&&console.warn(`[svelte-i18n] Message "${e}" has syntax error:`,f.message);}return u},yo=(e,t)=>go(t).format(e),wo=(e,t)=>Ao(t).format(e),Co=(e,t)=>_o(t).format(e),Eo=(e,t=me$2())=>Gn$1(e,t),Pt$2=derived([be$2,Be$1],()=>vo);derived([be$2],()=>yo);derived([be$2],()=>wo);derived([be$2],()=>Co);derived([be$2,Be$1],()=>Eo);const yt$3=writable(null),Zs=Object.freeze(Object.defineProperty({__proto__:null,navbar_config:yt$3},Symbol.toStringTag,{value:"Module"})),xo={code:".nav-holder.svelte-18evea3.svelte-18evea3{padding:var(--size-2) 0;border-bottom:solid 1px var(--border-color-primary)}nav.svelte-18evea3.svelte-18evea3{display:flex;flex-wrap:wrap;gap:var(--size-2);justify-content:flex-end;margin:0 auto;padding:0 var(--size-8)}nav.svelte-18evea3 a.svelte-18evea3{padding:var(--size-1) var(--size-2);border-radius:var(--block-radius);border-width:var(--block-border-width);border-color:transparent;color:var(--body-text-color-subdued)}nav.svelte-18evea3 a.active.svelte-18evea3{color:var(--body-text-color);border-color:var(--block-border-color);background-color:var(--block-background-fill)}.gradio-container-5-49-1.svelte-18evea3.svelte-18evea3{display:flex;position:relative;flex-direction:column;padding:0;min-height:1px;overflow:hidden;color:var(--button-secondary-text-color)}.embed-container.svelte-18evea3.svelte-18evea3{margin:var(--size-4) 0px;border:1px solid var(--button-secondary-border-color);border-radius:var(--embed-radius)}.with-info.svelte-18evea3.svelte-18evea3{padding-bottom:var(--size-7)}.embed-container.svelte-18evea3>main.svelte-18evea3{padding:var(--size-4)}main.svelte-18evea3.svelte-18evea3{display:flex;flex-grow:1;flex-direction:column}.app.svelte-18evea3.svelte-18evea3{position:relative;margin:auto;padding:var(--size-4) var(--size-8);width:100%;height:100%}@media(min-width: 640px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:640px}}@media(min-width: 768px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:768px}}@media(min-width: 1024px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:1024px}}@media(min-width: 1280px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:1280px}}@media(min-width: 1536px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:1536px}}@media(min-width: 1920px){.fillable.svelte-18evea3.svelte-18evea3:not(.fill_width){max-width:1920px}}.info.svelte-18evea3.svelte-18evea3{display:flex;position:absolute;bottom:0;justify-content:flex-start;border-top:1px solid var(--button-secondary-border-color);padding:var(--size-1) var(--size-5);width:100%;color:var(--body-text-color-subdued);font-size:var(--text-md);white-space:nowrap}.info.svelte-18evea3>span.svelte-18evea3{word-wrap:break-word;-break:keep-all;display:block;word-break:keep-all}.info.svelte-18evea3>span.svelte-18evea3:nth-child(1){margin-right:4px;min-width:0px;max-width:max-content;overflow:hidden;color:var(--body-text-color);text-overflow:ellipsis;white-space:nowrap}.info.svelte-18evea3>span.svelte-18evea3:nth-child(2){margin-right:3px}.info.svelte-18evea3>span.svelte-18evea3:nth-child(2),.info.svelte-18evea3>span.svelte-18evea3:nth-child(3){width:max-content}.info.svelte-18evea3>span.svelte-18evea3:nth-child(3){align-self:flex-end;justify-self:flex-end;margin-left:auto;text-align:right}.info.svelte-18evea3>span.svelte-18evea3:nth-child(1){flex-shrink:9}.hidden-title.svelte-18evea3.svelte-18evea3{position:absolute;left:var(--size-5);opacity:0;background:var(--button-secondary-background-fill);padding-right:4px}.info.svelte-18evea3 a.svelte-18evea3{color:var(--body-text-color)}.title.svelte-18evea3.svelte-18evea3{font-size:var(--text-sm);font-family:var(--font-mono)}.hf.svelte-18evea3.svelte-18evea3{margin-left:5px}.space-logo.svelte-18evea3 img.svelte-18evea3{display:inline-block;margin-bottom:4px;height:12px}main.svelte-18evea3 a.svelte-18evea3:hover{text-decoration:underline}",map:'{"version":3,"file":"Embed.svelte","sources":["Embed.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { getContext, onMount } from \\"svelte\\";\\nimport space_logo from \\"./images/spaces.svg\\";\\nimport { _ } from \\"svelte-i18n\\";\\nimport { navbar_config } from \\"./navbar_store\\";\\nexport let wrapper;\\nexport let version;\\nexport let initial_height;\\nexport let fill_width;\\nexport let is_embed;\\nexport let space;\\nexport let display;\\nexport let info;\\nexport let loaded;\\nexport let pages = [];\\nexport let current_page = \\"\\";\\nexport let root;\\nexport let components = [];\\nlet navbar_component = components.find((c) => c.type === \\"navbar\\");\\nlet navbar = navbar_component ? {\\n    visible: navbar_component.props.visible,\\n    main_page_name: navbar_component.props.main_page_name,\\n    value: navbar_component.props.value\\n} : null;\\nif (navbar) {\\n    navbar_config.set(navbar);\\n}\\n$: if ($navbar_config) {\\n    navbar = {\\n        visible: $navbar_config.visible ?? true,\\n        main_page_name: $navbar_config.main_page_name ?? \\"Home\\",\\n        value: $navbar_config.value ?? null\\n    };\\n}\\n$: show_navbar = pages.length > 1 && (navbar === null || navbar.visible !== false);\\n$: effective_pages = (() => {\\n    let visible_pages = pages.filter(([route, label, show], index) => {\\n        if (index === 0 && route === \\"\\") {\\n            return navbar?.main_page_name !== false;\\n        }\\n        return show !== false;\\n    });\\n    let base_pages = navbar && navbar.main_page_name !== false && navbar.main_page_name !== \\"Home\\" ? visible_pages.map(([route, label, show], index) => index === 0 && route === \\"\\" && label === \\"Home\\" ? [route, navbar.main_page_name] : [route, label]) : visible_pages.map(([route, label]) => [route, label]);\\n    if (navbar?.value && navbar.value.length > 0) {\\n        const existing_routes = new Set(base_pages.map(([route]) => route));\\n        const additional_pages = navbar.value.map(([page_name, page_path]) => [page_path, page_name]).filter(([route]) => !existing_routes.has(route));\\n        return [...base_pages, ...additional_pages];\\n    }\\n    return base_pages;\\n})();\\n<\/script>\\n\\n<div\\n\\tbind:this={wrapper}\\n\\tclass:fill_width\\n\\tclass:embed-container={display}\\n\\tclass:with-info={info}\\n\\tclass=\\"gradio-container gradio-container-{version}\\"\\n\\tstyle:min-height={loaded ? \\"initial\\" : initial_height}\\n\\tstyle:flex-grow={!display ? \\"1\\" : \\"auto\\"}\\n\\tdata-iframe-height\\n>\\n\\t{#if show_navbar}\\n\\t\\t<div class=\\"nav-holder\\">\\n\\t\\t\\t<nav class=\\"fillable\\" class:fill_width>\\n\\t\\t\\t\\t{#each effective_pages as [route, label], i}\\n\\t\\t\\t\\t\\t<a\\n\\t\\t\\t\\t\\t\\thref={route.startsWith(\\"http://\\") || route.startsWith(\\"https://\\")\\n\\t\\t\\t\\t\\t\\t\\t? route\\n\\t\\t\\t\\t\\t\\t\\t: `${root}/${route}`}\\n\\t\\t\\t\\t\\t\\tclass:active={route === current_page}\\n\\t\\t\\t\\t\\t\\tdata-sveltekit-reload\\n\\t\\t\\t\\t\\t\\ttarget={route.startsWith(\\"http://\\") || route.startsWith(\\"https://\\")\\n\\t\\t\\t\\t\\t\\t\\t? \\"_blank\\"\\n\\t\\t\\t\\t\\t\\t\\t: \\"_self\\"}\\n\\t\\t\\t\\t\\t\\trel={route.startsWith(\\"http://\\") || route.startsWith(\\"https://\\")\\n\\t\\t\\t\\t\\t\\t\\t? \\"noopener noreferrer\\"\\n\\t\\t\\t\\t\\t\\t\\t: \\"\\"}\\n\\t\\t\\t\\t\\t\\t>{label}\\n\\t\\t\\t\\t\\t</a>\\n\\t\\t\\t\\t{/each}\\n\\t\\t\\t</nav>\\n\\t\\t</div>\\n\\t{/if}\\n\\t<main class=\\"fillable\\" class:fill_width class:app={!display && !is_embed}>\\n\\t\\t<slot />\\n\\t\\t<div>\\n\\t\\t\\t{#if display && space && info}\\n\\t\\t\\t\\t<div class=\\"info\\">\\n\\t\\t\\t\\t\\t<span>\\n\\t\\t\\t\\t\\t\\t<a href=\\"https://huggingface.co/spaces/{space}\\" class=\\"title\\"\\n\\t\\t\\t\\t\\t\\t\\t>{space}</a\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t<span>\\n\\t\\t\\t\\t\\t\\t{$_(\\"common.built_with\\")}\\n\\t\\t\\t\\t\\t\\t<a class=\\"gradio\\" href=\\"https://gradio.app\\">Gradio</a>.\\n\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t<span>\\n\\t\\t\\t\\t\\t\\t{$_(\\"common.hosted_on\\")}\\n\\t\\t\\t\\t\\t\\t<a class=\\"hf\\" href=\\"https://huggingface.co/spaces\\"\\n\\t\\t\\t\\t\\t\\t\\t><span class=\\"space-logo\\">\\n\\t\\t\\t\\t\\t\\t\\t\\t<img src={space_logo} alt=\\"Hugging Face Space\\" />\\n\\t\\t\\t\\t\\t\\t\\t</span> Spaces</a\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t{/if}\\n\\t\\t</div>\\n\\t</main>\\n</div>\\n\\n<style>\\n\\t.nav-holder {\\n\\t\\tpadding: var(--size-2) 0;\\n\\t\\tborder-bottom: solid 1px var(--border-color-primary);\\n\\t}\\n\\tnav {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-wrap: wrap;\\n\\t\\tgap: var(--size-2);\\n\\t\\tjustify-content: flex-end;\\n\\t\\tmargin: 0 auto;\\n\\t\\tpadding: 0 var(--size-8);\\n\\t}\\n\\tnav a {\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t\\tborder-radius: var(--block-radius);\\n\\t\\tborder-width: var(--block-border-width);\\n\\t\\tborder-color: transparent;\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t}\\n\\tnav a.active {\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\tborder-color: var(--block-border-color);\\n\\t\\tbackground-color: var(--block-background-fill);\\n\\t}\\n\\t.gradio-container-5-49-1 {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: relative;\\n\\t\\tflex-direction: column;\\n\\t\\tpadding: 0;\\n\\t\\tmin-height: 1px;\\n\\t\\toverflow: hidden;\\n\\t\\tcolor: var(--button-secondary-text-color);\\n\\t}\\n\\n\\t.embed-container {\\n\\t\\tmargin: var(--size-4) 0px;\\n\\t\\tborder: 1px solid var(--button-secondary-border-color);\\n\\t\\tborder-radius: var(--embed-radius);\\n\\t}\\n\\n\\t.with-info {\\n\\t\\tpadding-bottom: var(--size-7);\\n\\t}\\n\\n\\t.embed-container > main {\\n\\t\\tpadding: var(--size-4);\\n\\t}\\n\\n\\tmain {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-grow: 1;\\n\\t\\tflex-direction: column;\\n\\t}\\n\\n\\t.app {\\n\\t\\tposition: relative;\\n\\t\\tmargin: auto;\\n\\t\\tpadding: var(--size-4) var(--size-8);\\n\\t\\twidth: 100%;\\n\\t\\theight: 100%;\\n\\t}\\n\\n\\t@media (min-width: 640px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 640px;\\n\\t\\t}\\n\\t}\\n\\t@media (min-width: 768px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 768px;\\n\\t\\t}\\n\\t}\\n\\t@media (min-width: 1024px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 1024px;\\n\\t\\t}\\n\\t}\\n\\t@media (min-width: 1280px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 1280px;\\n\\t\\t}\\n\\t}\\n\\t@media (min-width: 1536px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 1536px;\\n\\t\\t}\\n\\t}\\n\\t@media (min-width: 1920px) {\\n\\t\\t.fillable:not(.fill_width) {\\n\\t\\t\\tmax-width: 1920px;\\n\\t\\t}\\n\\t}\\n\\n\\t.info {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: absolute;\\n\\t\\tbottom: 0;\\n\\t\\tjustify-content: flex-start;\\n\\t\\tborder-top: 1px solid var(--button-secondary-border-color);\\n\\t\\tpadding: var(--size-1) var(--size-5);\\n\\t\\twidth: 100%;\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t\\tfont-size: var(--text-md);\\n\\t\\twhite-space: nowrap;\\n\\t}\\n\\n\\t.info > span {\\n\\t\\tword-wrap: break-word;\\n\\t\\t-break: keep-all;\\n\\t\\tdisplay: block;\\n\\t\\tword-break: keep-all;\\n\\t}\\n\\n\\t.info > span:nth-child(1) {\\n\\t\\tmargin-right: 4px;\\n\\t\\tmin-width: 0px;\\n\\t\\tmax-width: max-content;\\n\\t\\toverflow: hidden;\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\ttext-overflow: ellipsis;\\n\\t\\twhite-space: nowrap;\\n\\t}\\n\\n\\t.info > span:nth-child(2) {\\n\\t\\tmargin-right: 3px;\\n\\t}\\n\\n\\t.info > span:nth-child(2),\\n\\t.info > span:nth-child(3) {\\n\\t\\twidth: max-content;\\n\\t}\\n\\n\\t.info > span:nth-child(3) {\\n\\t\\talign-self: flex-end;\\n\\t\\tjustify-self: flex-end;\\n\\t\\tmargin-left: auto;\\n\\t\\ttext-align: right;\\n\\t}\\n\\n\\t.info > span:nth-child(1) {\\n\\t\\tflex-shrink: 9;\\n\\t}\\n\\n\\t.hidden-title {\\n\\t\\tposition: absolute;\\n\\t\\tleft: var(--size-5);\\n\\t\\topacity: 0;\\n\\t\\tbackground: var(--button-secondary-background-fill);\\n\\t\\tpadding-right: 4px;\\n\\t}\\n\\n\\t.info a {\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.title {\\n\\t\\tfont-size: var(--text-sm);\\n\\t\\tfont-family: var(--font-mono);\\n\\t}\\n\\n\\t.hf {\\n\\t\\tmargin-left: 5px;\\n\\t}\\n\\n\\t.space-logo img {\\n\\t\\tdisplay: inline-block;\\n\\t\\tmargin-bottom: 4px;\\n\\t\\theight: 12px;\\n\\t}\\n\\n\\tmain a:hover {\\n\\t\\ttext-decoration: underline;\\n\\t}</style>\\n"],"names":[],"mappings":"AAgHC,yCAAY,CACX,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,CAAC,CACxB,aAAa,CAAE,KAAK,CAAC,GAAG,CAAC,IAAI,sBAAsB,CACpD,CACA,iCAAI,CACH,OAAO,CAAE,IAAI,CACb,SAAS,CAAE,IAAI,CACf,GAAG,CAAE,IAAI,QAAQ,CAAC,CAClB,eAAe,CAAE,QAAQ,CACzB,MAAM,CAAE,CAAC,CAAC,IAAI,CACd,OAAO,CAAE,CAAC,CAAC,IAAI,QAAQ,CACxB,CACA,kBAAG,CAAC,gBAAE,CACL,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,aAAa,CAAE,IAAI,cAAc,CAAC,CAClC,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,YAAY,CAAE,WAAW,CACzB,KAAK,CAAE,IAAI,yBAAyB,CACrC,CACA,kBAAG,CAAC,CAAC,sBAAQ,CACZ,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,gBAAgB,CAAE,IAAI,uBAAuB,CAC9C,CACA,sDAAyB,CACxB,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,cAAc,CAAE,MAAM,CACtB,OAAO,CAAE,CAAC,CACV,UAAU,CAAE,GAAG,CACf,QAAQ,CAAE,MAAM,CAChB,KAAK,CAAE,IAAI,6BAA6B,CACzC,CAEA,8CAAiB,CAChB,MAAM,CAAE,IAAI,QAAQ,CAAC,CAAC,GAAG,CACzB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,+BAA+B,CAAC,CACtD,aAAa,CAAE,IAAI,cAAc,CAClC,CAEA,wCAAW,CACV,cAAc,CAAE,IAAI,QAAQ,CAC7B,CAEA,+BAAgB,CAAG,mBAAK,CACvB,OAAO,CAAE,IAAI,QAAQ,CACtB,CAEA,kCAAK,CACJ,OAAO,CAAE,IAAI,CACb,SAAS,CAAE,CAAC,CACZ,cAAc,CAAE,MACjB,CAEA,kCAAK,CACJ,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,IAAI,CACZ,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,KACZ,CACD,CACA,MAAO,YAAY,KAAK,CAAE,CACzB,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,KACZ,CACD,CACA,MAAO,YAAY,MAAM,CAAE,CAC1B,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,MACZ,CACD,CACA,MAAO,YAAY,MAAM,CAAE,CAC1B,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,MACZ,CACD,CACA,MAAO,YAAY,MAAM,CAAE,CAC1B,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,MACZ,CACD,CACA,MAAO,YAAY,MAAM,CAAE,CAC1B,uCAAS,KAAK,WAAW,CAAE,CAC1B,SAAS,CAAE,MACZ,CACD,CAEA,mCAAM,CACL,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,eAAe,CAAE,UAAU,CAC3B,UAAU,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,+BAA+B,CAAC,CAC1D,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,KAAK,CAAE,IAAI,CACX,KAAK,CAAE,IAAI,yBAAyB,CAAC,CACrC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,MACd,CAEA,oBAAK,CAAG,mBAAK,CACZ,SAAS,CAAE,UAAU,CACrB,MAAM,CAAE,QAAQ,CAChB,OAAO,CAAE,KAAK,CACd,UAAU,CAAE,QACb,CAEA,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAE,CACzB,YAAY,CAAE,GAAG,CACjB,SAAS,CAAE,GAAG,CACd,SAAS,CAAE,WAAW,CACtB,QAAQ,CAAE,MAAM,CAChB,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,aAAa,CAAE,QAAQ,CACvB,WAAW,CAAE,MACd,CAEA,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAE,CACzB,YAAY,CAAE,GACf,CAEA,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAC,CACzB,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAE,CACzB,KAAK,CAAE,WACR,CAEA,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAE,CACzB,UAAU,CAAE,QAAQ,CACpB,YAAY,CAAE,QAAQ,CACtB,WAAW,CAAE,IAAI,CACjB,UAAU,CAAE,KACb,CAEA,oBAAK,CAAG,mBAAI,WAAW,CAAC,CAAE,CACzB,WAAW,CAAE,CACd,CAEA,2CAAc,CACb,QAAQ,CAAE,QAAQ,CAClB,IAAI,CAAE,IAAI,QAAQ,CAAC,CACnB,OAAO,CAAE,CAAC,CACV,UAAU,CAAE,IAAI,kCAAkC,CAAC,CACnD,aAAa,CAAE,GAChB,CAEA,oBAAK,CAAC,gBAAE,CACP,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,oCAAO,CACN,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,WAAW,CAC7B,CAEA,iCAAI,CACH,WAAW,CAAE,GACd,CAEA,0BAAW,CAAC,kBAAI,CACf,OAAO,CAAE,YAAY,CACrB,aAAa,CAAE,GAAG,CAClB,MAAM,CAAE,IACT,CAEA,mBAAI,CAAC,gBAAC,MAAO,CACZ,eAAe,CAAE,SAClB"}'},Ys=create_ssr_component((e,t,n,r)=>{let i,o,s,a,h,l;a=subscribe(yt$3,B=>s=B),l=subscribe(Pt$2,B=>h=B);let{wrapper:c}=t,{version:u}=t,{initial_height:f}=t,{fill_width:A}=t,{is_embed:_}=t,{space:S}=t,{display:w}=t,{info:D}=t,{loaded:R}=t,{pages:L=[]}=t,{current_page:F=""}=t,{root:k}=t,{components:z=[]}=t,P=z.find(B=>B.type==="navbar"),O=P?{visible:P.props.visible,main_page_name:P.props.main_page_name,value:P.props.value}:null;return O&&yt$3.set(O),t.wrapper===void 0&&n.wrapper&&c!==void 0&&n.wrapper(c),t.version===void 0&&n.version&&u!==void 0&&n.version(u),t.initial_height===void 0&&n.initial_height&&f!==void 0&&n.initial_height(f),t.fill_width===void 0&&n.fill_width&&A!==void 0&&n.fill_width(A),t.is_embed===void 0&&n.is_embed&&_!==void 0&&n.is_embed(_),t.space===void 0&&n.space&&S!==void 0&&n.space(S),t.display===void 0&&n.display&&w!==void 0&&n.display(w),t.info===void 0&&n.info&&D!==void 0&&n.info(D),t.loaded===void 0&&n.loaded&&R!==void 0&&n.loaded(R),t.pages===void 0&&n.pages&&L!==void 0&&n.pages(L),t.current_page===void 0&&n.current_page&&F!==void 0&&n.current_page(F),t.root===void 0&&n.root&&k!==void 0&&n.root(k),t.components===void 0&&n.components&&z!==void 0&&n.components(z),e.css.add(xo),s&&(O={visible:s.visible??!0,main_page_name:s.main_page_name??"Home",value:s.value??null}),i=L.length>1&&(O===null||O.visible!==!1),o=(()=>{let B=L.filter(([g,Q,j],J)=>J===0&&g===""?O?.main_page_name!==!1:j!==!1),$=O&&O.main_page_name!==!1&&O.main_page_name!=="Home"?B.map(([g,Q,j],J)=>J===0&&g===""&&Q==="Home"?[g,O.main_page_name]:[g,Q]):B.map(([g,Q])=>[g,Q]);if(O?.value&&O.value.length>0){const g=new Set($.map(([j])=>j)),Q=O.value.map(([j,J])=>[J,j]).filter(([j])=>!g.has(j));return [...$,...Q]}return $})(),a(),l(),`<div class="${["gradio-container gradio-container-"+escape(u,!0)+" svelte-18evea3",(A?"fill_width":"")+" "+(w?"embed-container":"")+" "+(D?"with-info":"")].join(" ").trim()}" data-iframe-height${add_styles({"min-height":R?"initial":f,"flex-grow":w?"auto":"1"})}${add_attribute("this",c,0)}>${i?`<div class="nav-holder svelte-18evea3"><nav class="${["fillable svelte-18evea3",A?"fill_width":""].join(" ").trim()}">${each(o,([B,$],g)=>`<a${add_attribute("href",B.startsWith("http://")||B.startsWith("https://")?B:`${k}/${B}`,0)} data-sveltekit-reload${add_attribute("target",B.startsWith("http://")||B.startsWith("https://")?"_blank":"_self",0)}${add_attribute("rel",B.startsWith("http://")||B.startsWith("https://")?"noopener noreferrer":"",0)} class="${["svelte-18evea3",B===F?"active":""].join(" ").trim()}">${escape($)} </a>`)}</nav></div>`:""} <main class="${["fillable svelte-18evea3",(A?"fill_width":"")+" "+(!w&&!_?"app":"")].join(" ").trim()}">${r.default?r.default({}):""} <div>${w&&S&&D?`<div class="info svelte-18evea3"><span class="svelte-18evea3"><a href="${"https://huggingface.co/spaces/"+escape(S,!0)}" class="title svelte-18evea3">${escape(S)}</a></span> <span class="svelte-18evea3">${escape(h("common.built_with"))} <a class="gradio svelte-18evea3" href="https://gradio.app" data-svelte-h="svelte-jht9bl">Gradio</a>.</span> <span class="svelte-18evea3">${escape(h("common.hosted_on"))} <a class="hf svelte-18evea3" href="https://huggingface.co/spaces" data-svelte-h="svelte-d5sowi"><span class="space-logo svelte-18evea3"><img${add_attribute("src",Pr$1,0)} alt="Hugging Face Space" class="svelte-18evea3"></span> Spaces</a></span></div>`:""}</div></main> </div>`});let Wn$1=!1;typeof window<"u"&&"attachShadow"in Element.prototype&&"adoptedStyleSheets"in Document.prototype&&(Wn$1="adoptedStyleSheets"in document.createElement("div").attachShadow({mode:"open"}));function Js(e,t){const n=new URL(import.meta.url).origin;var r=e;if(window.location.origin!==n&&(r=new URL(e,n).href),document.querySelector(`link[href='${r}']`))return Promise.resolve();const o=document.createElement("link");return o.rel="stylesheet",o.href=r,new Promise((s,a)=>{o.addEventListener("load",()=>s()),o.addEventListener("error",()=>{console.error(`Unable to preload CSS for ${r}`),s();}),t.appendChild(o);})}function ea$1(e,t,n){if(!Wn$1)return e;n||(n=document.createElement("style")),n.remove();const r=new CSSStyleSheet;r.replaceSync(e);let i="";e=e.replace(/@import\s+url\((.*?)\);\s*/g,(h,l)=>(i+=`@import url(${l});
`,""));const o=r.cssRules;let s="",a=`.gradio-container.gradio-container-${t} .contain `;for(let h=0;h<o.length;h++){const l=o[h];let c=l.cssText.includes(".dark");if(l instanceof CSSStyleRule){const u=l.selectorText;if(u){const f=u.replace(".dark","").split(",").map(A=>`${c?".dark":""} ${a} ${A.trim()} `).join(",");s+=l.cssText,s+=l.cssText.replace(u,f);}}else if(l instanceof CSSMediaRule){let u=`@media ${l.media.mediaText} {`;for(let f=0;f<l.cssRules.length;f++){const A=l.cssRules[f];if(A instanceof CSSStyleRule){let _=A.cssText.includes(".dark ");const S=A.selectorText,w=S.replace(".dark","").split(",").map(D=>`${_?".dark":""} ${a} ${D.trim()} `).join(",");u+=A.cssText.replace(S,w);}}u+="}",s+=u;}else if(l instanceof CSSKeyframesRule){s+=`@keyframes ${l.name} {`;for(let u=0;u<l.cssRules.length;u++){const f=l.cssRules[u];f instanceof CSSKeyframeRule&&(s+=`${f.keyText} { ${f.style.cssText} }`);}s+="}";}else l instanceof CSSFontFaceRule&&(s+=`@font-face { ${l.style.cssText} }`);}return i+s}var tn$2=Object.prototype.hasOwnProperty;function nn$2(e,t,n){for(n of e.keys())if(Le$1(n,t))return n}function Le$1(e,t){var n,r,i;if(e===t)return !0;if(e&&t&&(n=e.constructor)===t.constructor){if(n===Date)return e.getTime()===t.getTime();if(n===RegExp)return e.toString()===t.toString();if(n===Array){if((r=e.length)===t.length)for(;r--&&Le$1(e[r],t[r]););return r===-1}if(n===Set){if(e.size!==t.size)return !1;for(r of e)if(i=r,i&&typeof i=="object"&&(i=nn$2(t,i),!i)||!t.has(i))return !1;return !0}if(n===Map){if(e.size!==t.size)return !1;for(r of e)if(i=r[0],i&&typeof i=="object"&&(i=nn$2(t,i),!i)||!Le$1(r[1],t.get(i)))return !1;return !0}if(n===ArrayBuffer)e=new Uint8Array(e),t=new Uint8Array(t);else if(n===DataView){if((r=e.byteLength)===t.byteLength)for(;r--&&e.getInt8(r)===t.getInt8(r););return r===-1}if(ArrayBuffer.isView(e)){if((r=e.byteLength)===t.byteLength)for(;r--&&e[r]===t[r];);return r===-1}if(!n||typeof e=="object"){r=0;for(n in e)if(tn$2.call(e,n)&&++r&&!tn$2.call(t,n)||!(n in t)||!Le$1(e[n],t[n]))return !1;return Object.keys(t).length===r}}return e!==e&&t!==t}const So={accordion:{component:()=>import('./Index43-ChjjuSzg.js')},annotatedimage:{component:()=>import('./Index21-dm_cbYH_.js')},audio:{base:()=>import('./StaticAudio-6eyiqKRV.js'),example:()=>import('./Example6-7u--UOCG.js'),component:()=>import('./index22-Bu3XhRRH.js')},box:{component:()=>import('./Index6-BQIkyqu7.js')},browserstate:{component:()=>import('./Index66-BT_wCfAY.js')},button:{component:()=>Promise.resolve().then(function () { return Index36; })},chatbot:{component:()=>import('./Index64-dK3pb0Ha.js')},checkbox:{example:()=>import('./Example7-BY36bKUd.js'),component:()=>import('./Index44-Bn1tFeA3.js')},checkboxgroup:{example:()=>import('./Example8-CtF03CXA.js'),component:()=>import('./Index23-I-jXs_Pm.js')},code:{example:()=>import('./Example9-BgAxc6bX.js'),component:()=>import('./Index17-BN-GAMZQ.js').then(e=>e.K)},colorpicker:{example:()=>import('./Example10-DUw5ngWN.js'),component:()=>import('./Index53-B_iLe6EW.js')},column:{component:()=>Promise.resolve().then(function () { return Index20; })},core:{component:()=>import('./index-C94nxEv_.js')},dataframe:{example:()=>import('./Example11-DbSY_4re.js'),component:()=>import('./Index65-Dp12pKmz.js')},dataset:{component:()=>import('./Index24-DpKxUqly.js')},datetime:{example:()=>import('./Example-CmZTmcbg.js'),component:()=>import('./Index57-Bca_UpPh.js')},dialogue:{example:()=>import('./Example13-DKMNurZL.js'),component:()=>import('./Index58-Lq6UQMA_.js')},downloadbutton:{component:()=>import('./Index45-Du2TAant.js')},draggable:{component:()=>import('./Index26-CK4B0gSY.js')},dropdown:{example:()=>import('./Example14-Dm_QueAJ.js'),component:()=>import('./Index59-87V3dxMW.js')},file:{example:()=>import('./Example15-QUrFCQ6n.js'),component:()=>import('./Index10-Bco55gHe.js')},fileexplorer:{example:()=>import('./Example16-DvaAOKL5.js'),component:()=>import('./Index63-CCGS6IKs.js')},form:{component:()=>Promise.resolve().then(function () { return Index19; })},gallery:{base:()=>import('./Gallery-DwewYNOL.js'),example:()=>import('./Example2-DF9c7LSI.js'),component:()=>import('./Index9-D7555p8a.js')},group:{component:()=>import('./Index27-yqg76A6k.js')},highlightedtext:{component:()=>import('./Index62-DPL7i5i_.js')},html:{base:()=>import('./Index54-CnLpc1YV.js'),example:()=>import('./Example17-BX_Nds0Q.js'),component:()=>import('./Index54-CnLpc1YV.js')},image:{base:()=>import('./ImagePreview-CkivoaK1.js'),example:()=>import('./Example12-_jhlwqC-.js'),component:()=>import('./Index28-DJN_cVP2.js')},imageeditor:{example:()=>import('./Example18-DsisKUSa.js'),component:()=>import('./Index3-DezoQBCD.js').then(e=>e.as)},imageslider:{example:()=>import('./Example19-BSaUMSck.js'),component:()=>import('./Index67-C2nyfLhf.js')},json:{example:()=>import('./Example20-CFDouFEG.js'),component:()=>import('./Index11-CiflBTUp.js')},label:{component:()=>import('./Index46-DWMPmKH6.js')},markdown:{example:()=>import('./Example21-uz6Wj3xI.js'),component:()=>import('./Index35-BdTDRCom.js')},model3d:{example:()=>import('./Example22-7u--UOCG.js'),component:()=>import('./Index60-TLxCPky9.js')},multimodaltextbox:{example:()=>import('./Example23-JmT8Yk3A.js'),component:()=>import('./Index47-4e3cSZs8.js')},nativeplot:{example:()=>import('./Example3-Biy8EGGC.js'),component:()=>import('./Index29-B7uK_Jl3.js')},navbar:{base:()=>import('./Index12-Bu5WKBZZ.js'),example:()=>import('./Example4-BB_DQ8Ql.js'),component:()=>import('./Index12-Bu5WKBZZ.js')},number:{example:()=>import('./Example24-C9X-oh6t.js'),component:()=>import('./Index30-CTzNUBZk.js')},paramviewer:{example:()=>import('./Example25-DUXZ9Y7A.js'),component:()=>import('./Index61-BBRZRllP.js')},plot:{base:()=>import('./Plot-D4xKcFIN.js'),component:()=>import('./Index13-CVAomUgM.js')},radio:{example:()=>import('./Example26-DpqwuJHm.js'),component:()=>import('./Index55-D9T9fC57.js')},row:{component:()=>import('./Index31-g7Qq22JS.js')},sidebar:{component:()=>import('./Index48-Dyg47yOt.js')},sketchbox:{component:()=>import('./Index32-7_fo2y5l.js')},slider:{example:()=>import('./Example27-DKMNurZL.js'),component:()=>import('./Index33-BRRWgmb1.js')},state:{component:()=>import('./Index14-D3zgy-z7.js')},statustracker:{component:()=>import('./index2-ihSmwCiq.js')},tabitem:{component:()=>import('./Index49-9fG8c8Wg.js')},tabs:{component:()=>import('./Index50-GZfrLJcs.js')},textbox:{example:()=>Promise.resolve().then(function () { return Example5; }),component:()=>Promise.resolve().then(function () { return Index25; })},timer:{component:()=>import('./Index15-DFvG43KK.js')},uploadbutton:{component:()=>import('./Index51-C9z37drs.js')},vibeeditor:{component:()=>import('./Index34-Do-wGrBJ.js')},video:{base:()=>import('./VideoPreview-L9YlhEoC.js').then(e=>e.b),example:()=>import('./Example28-DrLN6-P6.js'),component:()=>import('./index56-DRAeGH6H.js')},walkthrough:{component:()=>import('./Index50-GZfrLJcs.js')},walkthroughstep:{component:()=>import('./Index49-9fG8c8Wg.js')}},he$2={},Nt$2=typeof window<"u";function rn$2({api_url:e,name:t,id:n,variant:r}){const i=Nt$2&&window.__GRADIO__CC__,o={...So,...i||{}};let s=n||t;if(he$2[`${s}-${r}`])return {component:he$2[`${s}-${r}`],name:t};try{if(!o?.[s]?.[r]&&!o?.[t]?.[r])throw new Error;return he$2[`${s}-${r}`]=(o?.[s]?.[r]||o?.[t]?.[r])(),{name:t,component:he$2[`${s}-${r}`]}}catch{if(!s)throw new Error(`Component not found: ${t}`);try{return he$2[`${s}-${r}`]=Bo(e,s,r),{name:t,component:he$2[`${s}-${r}`]}}catch(h){if(r==="example")return he$2[`${s}-${r}`]=import('./Example29-DKMNurZL.js'),{name:t,component:he$2[`${s}-${r}`]};throw console.error(`failed to load: ${t}`),console.error(h),h}}}function on$2(e){return Nt$2?new Promise((t,n)=>{const r=document.createElement("link");r.rel="stylesheet",r.href=e,document.head.appendChild(r),r.onload=()=>t(),r.onerror=()=>n();}):Promise.resolve()}function Bo(e,t,n){const r=Nt$2?"client":"server";let i;return r==="server"?Promise.all([on$2(`${e}/custom_component/${t}/${n}/style.css`),import('./Index52-ZpJ-z0Q3.js')]).then(([o,s])=>s):(i=`${e}/custom_component/${t}/${r}/${n}/index.js`,Promise.all([on$2(`${e}/custom_component/${t}/${r}/${n}/style.css`),import(i)]).then(([o,s])=>s))}function Io(){const e=writable({}),t={},n={},r=new Map,i=new Map,o=new Map,s={};function a({fn_index:c,status:u,queue:f=!0,size:A,position:_=null,eta:S=null,message:w=null,progress:D,time_limit:R=null}){const L=n[c],F=t[c],k=s[c],z=L.map(P=>{let O;const B=r.get(P)||0;if(k==="pending"&&u!=="pending"){let $=B-1;r.set(P,$<0?0:$),O=$>0?"pending":u;}else k==="pending"&&u==="pending"?O="pending":k!=="pending"&&u==="pending"?(O="pending",r.set(P,B+1)):O=u;return {id:P,queue_position:_,queue_size:A,eta:S,status:O,message:w,progress:D}});F.forEach(P=>{const O=i.get(P)||0;if(k==="pending"&&u!=="pending"){let B=O-1;i.set(P,B<0?0:B),o.set(P,u);}else k!=="pending"&&u==="pending"?(i.set(P,O+1),o.set(P,u)):o.delete(P);}),e.update(P=>(z.forEach(({id:O,queue_position:B,queue_size:$,eta:g,status:Q,message:j,progress:J})=>{P[O]={queue:f,queue_size:$,queue_position:B,eta:g,message:j,progress:J,status:Q,fn_index:c};}),P)),s[c]=u;}function h(c,u,f){t[c]=u,n[c]=f;}function l(c,u){e.update(f=>(f[c]={...f[c],...u},f));}return {update:a,update_component_status:l,register:h,subscribe:e.subscribe,get_status_for_fn(c){return s[c]},get_inputs_to_update(){return o}}}const ta$1=["red","green","blue","yellow","purple","teal","orange","cyan","lime","pink"],To=[{color:"red",primary:600,secondary:100},{color:"green",primary:600,secondary:100},{color:"blue",primary:600,secondary:100},{color:"yellow",primary:500,secondary:100},{color:"purple",primary:600,secondary:100},{color:"teal",primary:600,secondary:100},{color:"orange",primary:600,secondary:100},{color:"cyan",primary:600,secondary:100},{color:"lime",primary:500,secondary:100},{color:"pink",primary:600,secondary:100}],sn$2={inherit:"inherit",current:"currentColor",transparent:"transparent",black:"#000",white:"#fff",slate:{50:"#f8fafc",100:"#f1f5f9",200:"#e2e8f0",300:"#cbd5e1",400:"#94a3b8",500:"#64748b",600:"#475569",700:"#334155",800:"#1e293b",900:"#0f172a",950:"#020617"},gray:{50:"#f9fafb",100:"#f3f4f6",200:"#e5e7eb",300:"#d1d5db",400:"#9ca3af",500:"#6b7280",600:"#4b5563",700:"#374151",800:"#1f2937",900:"#111827",950:"#030712"},zinc:{50:"#fafafa",100:"#f4f4f5",200:"#e4e4e7",300:"#d4d4d8",400:"#a1a1aa",500:"#71717a",600:"#52525b",700:"#3f3f46",800:"#27272a",900:"#18181b",950:"#09090b"},neutral:{50:"#fafafa",100:"#f5f5f5",200:"#e5e5e5",300:"#d4d4d4",400:"#a3a3a3",500:"#737373",600:"#525252",700:"#404040",800:"#262626",900:"#171717",950:"#0a0a0a"},stone:{50:"#fafaf9",100:"#f5f5f4",200:"#e7e5e4",300:"#d6d3d1",400:"#a8a29e",500:"#78716c",600:"#57534e",700:"#44403c",800:"#292524",900:"#1c1917",950:"#0c0a09"},red:{50:"#fef2f2",100:"#fee2e2",200:"#fecaca",300:"#fca5a5",400:"#f87171",500:"#ef4444",600:"#dc2626",700:"#b91c1c",800:"#991b1b",900:"#7f1d1d",950:"#450a0a"},orange:{50:"#fff7ed",100:"#ffedd5",200:"#fed7aa",300:"#fdba74",400:"#fb923c",500:"#f97316",600:"#ea580c",700:"#c2410c",800:"#9a3412",900:"#7c2d12",950:"#431407"},amber:{50:"#fffbeb",100:"#fef3c7",200:"#fde68a",300:"#fcd34d",400:"#fbbf24",500:"#f59e0b",600:"#d97706",700:"#b45309",800:"#92400e",900:"#78350f",950:"#451a03"},yellow:{50:"#fefce8",100:"#fef9c3",200:"#fef08a",300:"#fde047",400:"#facc15",500:"#eab308",600:"#ca8a04",700:"#a16207",800:"#854d0e",900:"#713f12",950:"#422006"},lime:{50:"#f7fee7",100:"#ecfccb",200:"#d9f99d",300:"#bef264",400:"#a3e635",500:"#84cc16",600:"#65a30d",700:"#4d7c0f",800:"#3f6212",900:"#365314",950:"#1a2e05"},green:{50:"#f0fdf4",100:"#dcfce7",200:"#bbf7d0",300:"#86efac",400:"#4ade80",500:"#22c55e",600:"#16a34a",700:"#15803d",800:"#166534",900:"#14532d",950:"#052e16"},emerald:{50:"#ecfdf5",100:"#d1fae5",200:"#a7f3d0",300:"#6ee7b7",400:"#34d399",500:"#10b981",600:"#059669",700:"#047857",800:"#065f46",900:"#064e3b",950:"#022c22"},teal:{50:"#f0fdfa",100:"#ccfbf1",200:"#99f6e4",300:"#5eead4",400:"#2dd4bf",500:"#14b8a6",600:"#0d9488",700:"#0f766e",800:"#115e59",900:"#134e4a",950:"#042f2e"},cyan:{50:"#ecfeff",100:"#cffafe",200:"#a5f3fc",300:"#67e8f9",400:"#22d3ee",500:"#06b6d4",600:"#0891b2",700:"#0e7490",800:"#155e75",900:"#164e63",950:"#083344"},sky:{50:"#f0f9ff",100:"#e0f2fe",200:"#bae6fd",300:"#7dd3fc",400:"#38bdf8",500:"#0ea5e9",600:"#0284c7",700:"#0369a1",800:"#075985",900:"#0c4a6e",950:"#082f49"},blue:{50:"#eff6ff",100:"#dbeafe",200:"#bfdbfe",300:"#93c5fd",400:"#60a5fa",500:"#3b82f6",600:"#2563eb",700:"#1d4ed8",800:"#1e40af",900:"#1e3a8a",950:"#172554"},indigo:{50:"#eef2ff",100:"#e0e7ff",200:"#c7d2fe",300:"#a5b4fc",400:"#818cf8",500:"#6366f1",600:"#4f46e5",700:"#4338ca",800:"#3730a3",900:"#312e81",950:"#1e1b4b"},violet:{50:"#f5f3ff",100:"#ede9fe",200:"#ddd6fe",300:"#c4b5fd",400:"#a78bfa",500:"#8b5cf6",600:"#7c3aed",700:"#6d28d9",800:"#5b21b6",900:"#4c1d95",950:"#2e1065"},purple:{50:"#faf5ff",100:"#f3e8ff",200:"#e9d5ff",300:"#d8b4fe",400:"#c084fc",500:"#a855f7",600:"#9333ea",700:"#7e22ce",800:"#6b21a8",900:"#581c87",950:"#3b0764"},fuchsia:{50:"#fdf4ff",100:"#fae8ff",200:"#f5d0fe",300:"#f0abfc",400:"#e879f9",500:"#d946ef",600:"#c026d3",700:"#a21caf",800:"#86198f",900:"#701a75",950:"#4a044e"},pink:{50:"#fdf2f8",100:"#fce7f3",200:"#fbcfe8",300:"#f9a8d4",400:"#f472b6",500:"#ec4899",600:"#db2777",700:"#be185d",800:"#9d174d",900:"#831843",950:"#500724"},rose:{50:"#fff1f2",100:"#ffe4e6",200:"#fecdd3",300:"#fda4af",400:"#fb7185",500:"#f43f5e",600:"#e11d48",700:"#be123c",800:"#9f1239",900:"#881337",950:"#4c0519"}},na$1=To.reduce((e,{color:t,primary:n,secondary:r})=>({...e,[t]:{primary:sn$2[t][n],secondary:sn$2[t][r]}}),{});function Vn$1(e){if(e==null)return "";const t=String(e),n=get_store_value(Pt$2);let r=n(t);if(r!==t)return r;const i=t.toLowerCase();for(const o of ko){const s=o.substring(o.indexOf(".")+1);if(i===s){const a=n(o);if(a!==o)return a;break}}return t}const ra$1=derived(Pt$2,()=>Vn$1),an$2={ar:"جاري التحميل",ca:"S'està carregant",ckb:"بارکردن",de:"Laden",en:"Loading",es:"Cargando",eu:"Kargatzen",fa:"در حال بارگذاری",fi:"Ladataan",fr:"Chargement",he:"טוען",hi:"लोड हो रहा है",ja:"読み込み中",ko:"로딩 중",lt:"Kraunama",nb:"Laster",nl:"Laden",pl:"Ładowanie","pt-BR":"Carregando",pt:"A carregar",ro:"Se încarcă",ru:"Загрузка",sv:"Laddar",ta:"ஏற்றுகிறது",th:"กำลังโหลด",tr:"Yükleniyor",uk:"Завантаження",ur:"لوڈ ہو رہا ہے",uz:"Yuklanmoqda","zh-CN":"加载中","zh-TW":"載入中"},qn$1="English",Qn$1={annotated_image:"Annotated Image"},Xn$1={allow_recording_access:"Please allow access to the microphone for recording.",audio:"Audio",drop_to_upload:"Drop an audio file here to upload",record_from_microphone:"Record from microphone",stop_recording:"Stop recording",no_device_support:"Media devices could not be accessed. Check that you are running on a secure origin (https) or localhost (or you have passed a valid SSL certificate to ssl_verify), and you have allowed browser access to your device.",stop:"Stop",resume:"Resume",record:"Record",no_microphone:"No microphone found",pause:"Pause",play:"Play",waiting:"Waiting"},Kn$1={connection_can_break:"On mobile, the connection can break if this tab is unfocused or the device sleeps, losing your position in queue.",long_requests_queue:"There is a long queue of requests pending. Duplicate this Space to skip.",lost_connection:"Lost connection due to leaving page. Rejoining queue...",waiting_for_inputs:"Waiting for file(s) to finish uploading, please retry."},Zn$1={edit:"Edit",retry:"Retry",undo:"Undo",submit:"Submit",cancel:"Cancel",like:"Like",dislike:"Dislike",clear:"Clear"},Yn$1={checkbox:"Checkbox",checkbox_group:"Checkbox Group"},Jn$1={code:"Code"},er$1={color_picker:"Color Picker"},tr$1={built_with:"built with",built_with_gradio:"Built with Gradio",clear:"Clear",download:"Download",edit:"Edit",empty:"Empty",error:"Error",hosted_on:"Hosted on",loading:"Loading",logo:"logo",or:"or",remove:"Remove",settings:"Settings",share:"Share",submit:"Submit",undo:"Undo",no_devices:"No devices found",language:"Language",display_theme:"Display Theme",pwa:"Progressive Web App",record:"Record",stop_recording:"Stop Recording",screen_studio:"Screen Studio",share_gradio_tab:"[Sharing] Gradio Tab",run:"Run"},nr$1={incorrect_format:"Incorrect format, only CSV and TSV files are supported",new_column:"Add column",new_row:"New row",add_row_above:"Add row above",add_row_below:"Add row below",delete_row:"Delete row",delete_column:"Delete column",add_column_left:"Add column to the left",add_column_right:"Add column to the right",sort_column:"Sort column",sort_ascending:"Sort ascending",sort_descending:"Sort descending",drop_to_upload:"Drop CSV or TSV files here to import data into dataframe",clear_sort:"Clear sort",filter:"Filter",clear_filter:"Clear filters"},rr$1={dropdown:"Dropdown"},ir$1={build_error:"there is a build error",config_error:"there is a config error",contact_page_author:"Please contact the author of the page to let them know.",no_app_file:"there is no app file",runtime_error:"there is a runtime error",space_not_working:`"Space isn't working because" {0}`,space_paused:"the space is paused",use_via_api:"Use via API",use_via_api_or_mcp:"Use via API or MCP"},or$1={uploading:"Uploading..."},sr$1={highlighted_text:"Highlighted Text"},ar$1={allow_webcam_access:"Please allow access to the webcam for recording.",brush_color:"Brush color",brush_radius:"Brush radius",image:"Image",remove_image:"Remove Image",select_brush_color:"Select brush color",start_drawing:"Start drawing",use_brush:"Use brush",drop_to_upload:"Drop an image file here to upload"},lr$1={label:"Label"},cr$1={enable_cookies:"If you are visiting a HuggingFace Space in Incognito mode, you must enable third party cookies.",incorrect_credentials:"Incorrect Credentials",username:"username",password:"password",login:"Login"},ur$1={number:"Number"},hr$1={plot:"Plot"},fr$1={radio:"Radio"},pr$1={slider:"Slider"},dr$1={click_to_upload:"Click to Upload",drop_audio:"Drop Audio Here",drop_csv:"Drop CSV Here",drop_file:"Drop File Here",drop_image:"Drop Image Here",drop_video:"Drop Video Here",drop_gallery:"Drop Media Here",paste_clipboard:"Paste from Clipboard"},mr$1={drop_to_upload:"Drop a video file here to upload"},kt$1={_name:qn$1,"3D_model":{"3d_model":"3D Model",drop_to_upload:"Drop a 3D model (.obj, .glb, .stl, .gltf, .splat, or .ply) file here to upload"},annotated_image:Qn$1,audio:Xn$1,blocks:Kn$1,chatbot:Zn$1,checkbox:Yn$1,code:Jn$1,color_picker:er$1,common:tr$1,dataframe:nr$1,dropdown:rr$1,errors:ir$1,file:or$1,highlighted_text:sr$1,image:ar$1,label:lr$1,login:cr$1,number:ur$1,plot:hr$1,radio:fr$1,slider:pr$1,upload_text:dr$1,video:mr$1},Oo=Object.freeze(Object.defineProperty({__proto__:null,_name:qn$1,annotated_image:Qn$1,audio:Xn$1,blocks:Kn$1,chatbot:Zn$1,checkbox:Yn$1,code:Jn$1,color_picker:er$1,common:tr$1,dataframe:nr$1,default:kt$1,dropdown:rr$1,errors:ir$1,file:or$1,highlighted_text:sr$1,image:ar$1,label:lr$1,login:cr$1,number:ur$1,plot:hr$1,radio:fr$1,slider:pr$1,upload_text:dr$1,video:mr$1},Symbol.toStringTag,{value:"Module"})),Ho={ar:"العربية",ca:"Català",ckb:"کوردی",de:"Deutsch",en:"English",es:"Español",eu:"Euskara",fa:"فارسی",fi:"Suomi",fr:"Français",he:"עברית",hi:"हिंदी",ja:"日本語",ko:"한국어",lt:"Lietuvių",nb:"Norsk bokmål",nl:"Nederlands",pl:"Polski","pt-BR":"Português do Brasil",pt:"Português",ro:"Română",ru:"Русский",sv:"Svenska",ta:"தமிழ்",th:"ภาษาไทย",tr:"Türkçe",uk:"Українська",ur:"اردو",uz:"O'zbek","zh-CN":"简体中文","zh-TW":"繁體中文"},Po=Object.assign({"./lang/ar.json":()=>import('./ar-Cwk59jlo.js'),"./lang/ca.json":()=>import('./ca-BvH50zSS.js'),"./lang/ckb.json":()=>import('./ckb-l7nR8ql7.js'),"./lang/de.json":()=>import('./de-B1wU7-Ch.js'),"./lang/en.json":()=>Promise.resolve().then(()=>Oo),"./lang/es.json":()=>import('./es-B2LmZtQQ.js'),"./lang/eu.json":()=>import('./eu-DQN2mBJJ.js'),"./lang/fa.json":()=>import('./fa-DJTEw8mO.js'),"./lang/fi.json":()=>import('./fi-BJkPVS_L.js'),"./lang/fr.json":()=>import('./fr-Doonyoep.js'),"./lang/he.json":()=>import('./he-C5xAKd5S.js'),"./lang/hi.json":()=>import('./hi-DKgm37B9.js'),"./lang/id.json":()=>import('./id-CeonQf4M.js'),"./lang/ja.json":()=>import('./ja-IeX0ScdE.js'),"./lang/ko.json":()=>import('./ko-CWBcxRwV.js'),"./lang/lt.json":()=>import('./lt-DuVbsrrG.js'),"./lang/nb.json":()=>import('./nb-D08346Tf.js'),"./lang/nl.json":()=>import('./nl-C9vqu2l6.js'),"./lang/pl.json":()=>import('./pl-CCZ3iBe5.js'),"./lang/pt-BR.json":()=>import('./pt-BR-DPuva9n4.js'),"./lang/pt.json":()=>import('./pt-B_nt5bpZ.js'),"./lang/ro.json":()=>import('./ro-Ddw_SWeO.js'),"./lang/ru.json":()=>import('./ru-hxtnGKGc.js'),"./lang/sv.json":()=>import('./sv-CBaAzwhi.js'),"./lang/ta.json":()=>import('./ta-CIRcMeU1.js'),"./lang/th.json":()=>import('./th-CWKCe4yc.js'),"./lang/tr.json":()=>import('./tr-BjNdPtGX.js'),"./lang/uk.json":()=>import('./uk-DxkC9TjY.js'),"./lang/ur.json":()=>import('./ur-DPrEFG9j.js'),"./lang/uz.json":()=>import('./uz-BUySSN8V.js'),"./lang/zh-CN.json":()=>import('./zh-CN-CPutFXEq.js'),"./lang/zh-TW.json":()=>import('./zh-TW-CFo1-iyM.js')});function ia$1(e){return e&&typeof e=="object"&&e.__type__==="translation_metadata"&&typeof e.key=="string"}const wt$1="__i18n__";function oa$1(e){if(typeof e!="string")return e;const t=e.indexOf(wt$1);if(t===-1)return e;try{const n=t>0?e.substring(0,t):"",r=t+wt$1.length,i=e.indexOf("{",r);let o=-1,s=0;for(let l=i;l<e.length;l++)if(e[l]==="{"&&s++,e[l]==="}"&&s--,s===0){o=l+1;break}if(o===-1)return console.error("Could not find end of JSON in i18n string"),e;const a=e.substring(i,o),h=o<e.length?e.substring(o):"";try{const l=JSON.parse(a);if(l&&l.key){const c=Vn$1(l.key);return n+c+h}}catch(l){console.error("Error parsing i18n JSON:",l);}return e}catch(n){return console.error("Error processing translation:",n),e}}function No(){return {...Object.fromEntries(Object.entries(Po).map(([t,n])=>[t.split("/").pop().split(".")[0],{type:"lazy",data:n}])),en:{type:"static",data:kt$1}}}const Mt$2=No(),Ct$3=Object.keys(Mt$2),sa$1=Object.entries(Mt$2).map(([e])=>[Ho[e]||e,e]);let ko=new Set,lt$3=!1,ln$2;function Mo(e){const t=e.split(",").map(n=>n.includes(";")?n.split(";").slice(0,2):[n,1]);t.sort((n,r)=>parseFloat(r[1])-parseFloat(n[1]));for(const[n,r]of t)if(Ct$3.includes(n))return n;return null}async function aa$1(e,t){if(lt$3&&!(lt$3&&e!==ln$2))return;ln$2=e,Lo({processed_langs:Mt$2,custom_translations:e??{}});let r=null;const i=uo();if(t?r=Mo(t):r=i&&Ct$3.includes(i)?i:null,!r){const o=i?.split("-")[0];r=o&&Ct$3.includes(o)?o:"en";}await to({fallbackLocale:"en",initialLocale:r}),lt$3=!0;}function la$1(e){be$2.set(e);}function ca$1(e,t,n="en"){return e&&t.includes(e)?e:n}function Lo(e){if(e){try{for(const t in e.custom_translations)We$2(t,e.custom_translations[t]);for(const t in e.processed_langs)t==="en"&&e.processed_langs[t].type==="static"?We$2(t,kt$1):e.processed_langs[t].type==="lazy"&&Qi(t,e.processed_langs[t].data);}catch(t){console.error("Error loading translations:",t);}for(const t in an$2)We$2(t,{common:{loading:an$2[t]}});}}let Ae$2=[];const Ro=typeof window<"u",cn$2=Ro?requestAnimationFrame:async e=>await e();function ua$1({initial_layout:e=void 0}={initial_layout:void 0}){let t,n=writable({}),r={},i,o,s,a,h=Io();const l=writable(e);let c=[],u,f={},A,_=null;function S(b){_=b;}let w,D;function R(b){b.forEach(v=>{v.targets.forEach(x=>{const p=a?.[x[0]];p&&v.event_specific_args?.length>0&&v.event_specific_args?.forEach(m=>{p.props[m]=v[m];});});});}async function L({app:b,components:v,layout:x,dependencies:p,root:m,options:C}){$(),u=b,a&&v.forEach(d=>{if(d.props.value==null&&d.key){const U=Object.values(a).find(y=>y.key===d.key);U&&(d.props.value=U.props.value);}}),c=v,i=new Set,o=new Set,Ae$2=[],s=new Map,t=new Map,a={},w=x,D=m,A={id:x.id,type:"column",props:{interactive:!1,scale:C.fill_height?1:null,visible:!0},has_modes:!1,instance:null,component:null,component_class_id:"",key:null},v.push(A),p.forEach(d=>{h.register(d.id,d.inputs,d.show_progress_on||d.outputs),d.frontend_fn=un$2(d.js,!!d.backend_fn,d.inputs.length,d.outputs.length),hn$1(d.targets,d.id,r),fn$2(d,i,o);}),n.set(r),s=pn$2(v,x,m),a=v.reduce((d,U)=>(d[U.id]=U,d),{}),await k(x,m,c),l.set(A),R(p);}function F({render_id:b,components:v,layout:x,root:p,dependencies:m}){v.forEach(E=>{for(const X in E.props)E.props[X]===null&&(E.props[X]=void 0);});let C=[],d=[];v.forEach(E=>{E.key==null||!f[b]?.includes(E.key)?d.push(E):C.push(E);}),pn$2(d,x,p).forEach((E,X)=>{s.set(X,E);}),r={},m.forEach(E=>{h.register(E.id,E.inputs,E.outputs),E.frontend_fn=un$2(E.js,!!E.backend_fn,E.inputs.length,E.outputs.length),hn$1(E.targets,E.id,r),fn$2(E,i,o);}),n.set(r);let y=a?.[x.id];const ce=E=>{E.children&&E.children.forEach(X=>{ce(X);});};ce(y),Object.entries(a).forEach(([E,X])=>{let Te=Number(E);if(X.rendered_in===b){let ue=C.find(se=>se.key===X.key);if(X.key!=null&&ue!==void 0){const se=a?.[X.id];for(const ve in ue.props)ue.props.preserved_by_key?.includes(ve)||(se.props[ve]=ue.props[ve]);}else a&&delete a[Te],t.has(Te)&&t.delete(Te);}}),d.concat(C.filter(E=>!a?.[E.id])).forEach(E=>{a[E.id]=E,t.set(E.id,E);}),y.parent&&(y.parent.children[y.parent.children.indexOf(y)]=a?.[x.id]),k(x,p,c.concat(v),y.parent).then(()=>{l.set(A),f[b]=v.map(E=>E.key).filter(E=>E!=null);}),R(m);}async function k(b,v,x,p){const m=a?.[b.id];if(!m.component){const C=m.component_class_id||m.type;let d=s.get(C);d&&(m.component=(await d)?.default);}if(m.parent=p,m.type==="dataset"&&(m.props.component_map=Et$3(m.type,m.component_class_id,v,x,m.props.components).example_components),r[m.id]&&(m.props.attached_events=Object.keys(r[m.id])),m.props.interactive=jo(m.id,m.props.interactive,m.props.value,i,o),m.props.server=Go(m.id,m.props.server_fns,u),t.set(m.id,m),b.children&&(m.children=await Promise.all(b.children.map(C=>k(C,v,x,m)))),m.type==="tabs"&&!m.props.initial_tabs||m.type==="walkthrough"&&!m.props.initial_tabs){const C=b.children?.map((y,ce)=>{const _e=a?.[y.id];return _e.props.id??=y.id,{type:_e.type,props:{..._e.props,id:_e.props.id,order:ce}}})||[],d=m.type==="walkthrough"?"walkthroughstep":"tabitem",U=C.filter(y=>y.type===d);m.props.initial_tabs=U?.map(y=>({label:y.props.label.includes(wt$1)?"":y.props.label,id:y.props.id,visible:typeof y.props.visible=="boolean"||y.props.visible==="hidden"?y.props.visible:!0,interactive:y.props.interactive,order:y.props.order}));}return (m.type==="tabs"||m.type==="walkthrough")&&b.children?.forEach((C,d)=>{const U=a?.[C.id];U.props.order=d;}),m}let z=!1,P=writable(!1);async function O(b,v){if(b.size===0)return;const x=v.filter(p=>b.has(p.id));for(const p of x){const m=p.component_class_id||p.type;if(s.has(m))p.component=(await s.get(m))?.default??p.component;else {const{component:C,example_components:d}=Et$3(p.type,p.component_class_id,D,v);if(s.set(m,C),d)for(const[U,y]of d)s.set(U,y);p.component||(p.component=(await C)?.default);}}}function B(b){return b.some(v=>v.some(x=>{const p=a?.[x.id];return p?x.prop==="visible"||x.prop==="selected"&&p.type==="tabs":!1}))}function $(){const b=B(Ae$2);let v;const x=t?[...t.values()]:c;b&&w&&(v=Xe$1(w,x)),l.update(p=>{for(let m=0;m<Ae$2.length;m++)for(let C=0;C<Ae$2[m].length;C++){const d=Ae$2[m][C];if(!d)continue;const U=a?.[d.id];if(!U)continue;let y;const ce=U.props[d.prop];d.value instanceof Map?y=new Map(d.value):d.value instanceof Set?y=new Set(d.value):Array.isArray(d.value)?y=[...d.value]:d.value==null?y=null:typeof d.value=="object"?y={...d.value}:y=d.value,U.props[d.prop]=y,d.prop==="value"&&!xt$2(U)&&!Le$1(ce,y)&&_?.(d.id,y);}return p}),b&&w&&v&&cn$2(async()=>{const p=Xe$1(w,x),m=new Set;for(const C of p)v.has(C)||m.add(C);await O(m,x),m.size>0&&l.update(C=>C);}),Ae$2=[],z=!1,P.set(!1);}function g(b){b&&(Ae$2.push(b),z||(z=!0,P.set(!0),cn$2($)));}function Q(b){let v=t.get(b);if(!v){const x=get_store_value(l);v=j(x,b);}return v?v.instance?.get_value?v.instance.get_value():v.props.value:null}function j(b,v){if(b.id===v)return b;if(b.children)for(const x of b.children){const p=j(x,v);if(p)return p}}function J(b,v){const x=t.get(b);x&&x.instance?.modify_stream_state&&x.instance.modify_stream_state(v);}function W(b){const v=t.get(b);return v?.instance?.get_stream_state?v.instance.get_stream_state():"not_set"}function le(b,v){const x=t.get(b);x?.instance?.set_time_limit&&x.instance.set_time_limit(v);}return {layout:l,targets:n,update_value:g,get_data:Q,modify_stream:J,get_stream_state:W,set_time_limit:le,loading_status:h,scheduled_updates:P,create_layout:L,rerender_layout:F,value_change:S}}const Do=Object.getPrototypeOf(async function(){}).constructor;function un$2(e,t,n,r){if(!e||e===!0)return null;const i=t?n===1:r===1;try{return new Do("__fn_args",`  let result = await (${e})(...__fn_args);
  if (typeof result === "undefined") return [];
  return (${i} && !Array.isArray(result)) ? [result] : result;`)}catch(o){return console.error("Could not parse custom js method."),console.error(o),null}}function hn$1(e,t,n){return e.forEach(([r,i])=>{n[r]||(n[r]={}),n[r]?.[i]&&!n[r]?.[i].includes(t)?n[r][i].push(t):n[r][i]=[t];}),n}function fn$2(e,t,n){return e.inputs.forEach(r=>t.add(r)),e.outputs.forEach(r=>n.add(r)),[t,n]}function Uo(e){return Array.isArray(e)&&e.length===0||e===""||e===0||!e}function jo(e,t,n,r,i){return t===!1?!1:t===!0?!0:!!(r.has(e)||!i.has(e)&&Uo(n))}function Go(e,t,n){return t?t.reduce((r,i)=>(r[i]=async(...o)=>(o.length===1&&(o=o[0]),await n.component_server(e,i,o)),r),{}):{}}function Et$3(e,t,n,r,i){let o=new Map;e==="api"&&(e="state"),e==="dataset"&&i&&i.forEach(a=>{if(o.has(a))return;let h;const l=r.find(c=>c.type===a);l&&(h=rn$2({api_url:n,name:a,id:l.component_class_id,variant:"example"}),o.set(a,h.component));});const s=rn$2({api_url:n,name:e,id:t,variant:"component"});return {component:s.component,name:s.name,example_components:o.size>0?o:void 0}}function _r$1(e,t,n){const r=n?.selected_tab_id===e.id||n?.selected_tab_id===e.props.id;return t&&r}function Fo(e,t,n){const r=e.props.selected;if(typeof r=="string"||typeof r=="number")return r;if(t.children)for(const i of t.children){const o=n.find(s=>s.id===i.id);if(o?.type==="tabitem"&&o.props.visible!==!1&&o.props.interactive!==!1)return o.id||o.props.id}}function ct$4(e,t,n){const r=new Set;if(e.children){const i=t.find(o=>o.id===e.id);for(const o of e.children)Xe$1(o,t,i?.type==="tabitem"?i.props.children_visible!==!1:!0,n).forEach(a=>r.add(a));}return r}function Xe$1(e,t,n=!0,r){const i=new Set,o=t.find(h=>h.id===e.id);if(!o)return i;const s=o.props.visible!==!1&&o.props.visible!=="hidden"&&n;if(!(o.props.visible==="hidden"||s))return i;if(o.type==="tabs"){const l={selected_tab_id:Fo(o,e,t)};i.add(e.id),ct$4(e,t,l).forEach(u=>i.add(u));}else if(o.type==="tabitem"){const h=_r$1(o,s,r);(h||!h&&o.props.render_children)&&(i.add(e.id),ct$4(e,t,r).forEach(c=>i.add(c)));}else i.add(e.id),ct$4(e,t,r).forEach(l=>i.add(l));return i}function pn$2(e,t,n){let r=new Map;const i=Xe$1(t,e);return e.forEach(o=>{if(i.has(o.id)){const{component:s,example_components:a}=Et$3(o.type,o.component_class_id,n,e);if(r.set(o.component_class_id||o.type,s),a)for(const[h,l]of a)r.set(h,l);}}),r}function xt$2(e){return e.props.visible==="hidden"?!0:typeof e.props.visible=="boolean"&&e.props.visible===!1?!1:e.parent?e.parent.type==="tabitem"?_r$1(e.parent,xt$2(e.parent)):xt$2(e.parent):!0}var ut$3=new Intl.Collator(0,{numeric:1}).compare;function Ar$1(e,t,n){return e=e.split("."),t=t.split("."),ut$3(e[0],t[0])||ut$3(e[1],t[1])||(t[2]=t.slice(2).join("."),n=/[.-]/.test(e[2]=e.slice(2).join(".")),n==/[.-]/.test(t[2])?ut$3(e[2],t[2]):n?-1:1)}const zo="host",gr$1="queue/data",$o="queue/join",dn$2="upload",Wo="login",ze$1="config",Vo="info",qo="runtime",Qo="sleeptime",Xo="heartbeat",Ko="component_server",Zo="reset",Yo="cancel",Jo="app_id",es="https://gradio-space-api-fetcher-v2.hf.space/api",br$1="This application is currently busy. Please try again. ",Se$1="Connection errored out. ",fe$2="Could not resolve app config. ",ts="Could not get space status. ",ns="Could not get API info. ",Lt$1="Space metadata could not be loaded. ",rs="Invalid URL. A full URL path is required.",is="Not authorized to access this space. ",vr$1="Invalid credentials. Could not login. ",os="Login credentials are required to access this space.",ss="File system access is only available in Node.js environments",yr$1="Root URL not found in client config",as="Error uploading file";function ls(e,t,n){return t.startsWith("http://")||t.startsWith("https://")?n?e:t:e+t}async function mn$1(e,t,n){try{return (await(await fetch(`https://huggingface.co/api/spaces/${e}/jwt`,{headers:{Authorization:`Bearer ${t}`,...n?{Cookie:n}:{}}})).json()).token||!1}catch{return !1}}function cs(e){let t={};return e.forEach(({api_name:n,id:r})=>{n&&(t[n]=r);}),t}async function us(e){const t=this.options.hf_token?{Authorization:`Bearer ${this.options.hf_token}`}:{};if(t["Content-Type"]="application/json",typeof window<"u"&&window.gradio_config&&location.origin!=="http://localhost:9876"){if(window.gradio_config.current_page&&(e=e.substring(0,e.lastIndexOf("/"))),window.gradio_config.dev_mode){let n=St$2(e,this.deep_link?ze$1+"?deep_link="+this.deep_link:ze$1);const r=await this.fetch(n,{headers:t,credentials:"include"}),i=await _n$2(r,e,!!this.options.auth);window.gradio_config={...i,current_page:window.gradio_config.current_page};}return window.gradio_config.root=e,{...window.gradio_config}}else if(e){let n=St$2(e,this.deep_link?ze$1+"?deep_link="+this.deep_link:ze$1);const r=await this.fetch(n,{headers:t,credentials:"include"});return _n$2(r,e,!!this.options.auth)}throw new Error(fe$2)}async function _n$2(e,t,n){if(e?.status===401&&!n){const i=(await e.json())?.detail?.auth_message;throw new Error(i||os)}else if(e?.status===401&&n)throw new Error(vr$1);if(e?.status===200){let r=await e.json();return r.root=t,r.dependencies?.forEach((i,o)=>{i.id===void 0&&(i.id=o);}),r}else if(e?.status===401)throw new Error(is);throw new Error(fe$2)}async function hs(){const{http_protocol:e,host:t}=await Je(this.app_reference,this.options.hf_token);try{if(this.options.auth){const n=await wr$1(e,t,this.options.auth,this.fetch,this.options.hf_token);n&&this.set_cookies(n);}}catch(n){throw Error(n.message)}}async function wr$1(e,t,n,r,i){const o=new FormData;o.append("username",n?.[0]),o.append("password",n?.[1]);let s={};i&&(s.Authorization=`Bearer ${i}`);const a=await r(`${e}//${t}/${Wo}`,{headers:s,method:"POST",body:o,credentials:"include"});if(a.status===200)return a.headers.get("set-cookie");throw a.status===401?new Error(vr$1):new Error(Lt$1)}function ht$2(e){if(e.startsWith("http")){const{protocol:t,host:n,pathname:r}=new URL(e);return {ws_protocol:t==="https:"?"wss":"ws",http_protocol:t,host:n+(r!=="/"?r:"")}}return {ws_protocol:"wss",http_protocol:"https:",host:new URL(e).host}}const Cr$1=e=>{let t=[];return e.split(/,(?=\s*[^\s=;]+=[^\s=;]+)/).forEach(r=>{const[i,o]=r.split(";")[0].split("=");i&&o&&t.push(`${i.trim()}=${o.trim()}`);}),t},Rt$2=/^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$/,fs=/.*hf\.space\/{0,1}.*$/;async function Je(e,t){const n={};t&&(n.Authorization=`Bearer ${t}`);const r=e.trim().replace(/\/$/,"");if(Rt$2.test(r))try{const o=(await(await fetch(`https://huggingface.co/api/spaces/${r}/${zo}`,{headers:n})).json()).host;return {space_id:e,...ht$2(o)}}catch{throw new Error(Lt$1)}if(fs.test(r)){const{ws_protocol:i,http_protocol:o,host:s}=ht$2(r);return {space_id:s.split("/")[0].replace(".hf.space",""),ws_protocol:i,http_protocol:o,host:s}}return {space_id:!1,...ht$2(r)}}const St$2=(...e)=>{try{return e.reduce((t,n)=>(t=t.replace(/\/+$/,""),n=n.replace(/^\/+/,""),new URL(n,t+"/").toString()))}catch{throw new Error(rs)}};function ps(e,t,n){const r={named_endpoints:{},unnamed_endpoints:{}};return Object.keys(e).forEach(i=>{(i==="named_endpoints"||i==="unnamed_endpoints")&&(r[i]={},Object.entries(e[i]).forEach(([o,{parameters:s,returns:a}])=>{const h=t.dependencies.find(u=>u.api_name===o||u.api_name===o.replace("/",""))?.id||n[o.replace("/","")]||-1,l=h!==-1?t.dependencies.find(u=>u.id==h)?.types:{generator:!1,cancel:!1};if(h!==-1&&t.dependencies.find(u=>u.id==h)?.inputs?.length!==s.length){const u=t.dependencies.find(f=>f.id==h).inputs.map(f=>t.components.find(A=>A.id===f)?.type);try{u.forEach((f,A)=>{if(f==="state"){const _={component:"state",example:null,parameter_default:null,parameter_has_default:!0,parameter_name:null,hidden:!0};s.splice(A,0,_);}});}catch(f){console.error(f);}}const c=(u,f,A,_)=>({...u,description:ms(u?.type,A),type:ds(u?.type,f,A,_)||""});r[i][o]={parameters:s.map(u=>c(u,u?.component,u?.serializer,"parameter")),returns:a.map(u=>c(u,u?.component,u?.serializer,"return")),type:l};}));}),r}function ds(e,t,n,r){if(t==="Api")return e.type;switch(e?.type){case"string":return "string";case"boolean":return "boolean";case"number":return "number"}if(n==="JSONSerializable"||n==="StringSerializable")return "any";if(n==="ListStringSerializable")return "string[]";if(t==="Image")return r==="parameter"?"Blob | File | Buffer":"string";if(n==="FileSerializable")return e?.type==="array"?r==="parameter"?"(Blob | File | Buffer)[]":"{ name: string; data: string; size?: number; is_file?: boolean; orig_name?: string}[]":r==="parameter"?"Blob | File | Buffer":"{ name: string; data: string; size?: number; is_file?: boolean; orig_name?: string}";if(n==="GallerySerializable")return r==="parameter"?"[(Blob | File | Buffer), (string | null)][]":"[{ name: string; data: string; size?: number; is_file?: boolean; orig_name?: string}, (string | null))][]"}function ms(e,t){return t==="GallerySerializable"?"array of [file, label] tuples":t==="ListStringSerializable"?"array of strings":t==="FileSerializable"?"array of files or single file":e?.description}function ft$2(e,t){switch(e.msg){case"send_data":return {type:"data"};case"send_hash":return {type:"hash"};case"queue_full":return {type:"update",status:{queue:!0,message:br$1,stage:"error",code:e.code,success:e.success}};case"heartbeat":return {type:"heartbeat"};case"unexpected_error":return {type:"unexpected_error",status:{queue:!0,message:e.message,session_not_found:e.session_not_found,stage:"error",success:!1}};case"broken_connection":return {type:"broken_connection",status:{queue:!0,message:e.message,stage:"error",success:!1}};case"estimation":return {type:"update",status:{queue:!0,stage:t||"pending",code:e.code,size:e.queue_size,position:e.rank,eta:e.rank_eta,success:e.success}};case"progress":return {type:"update",status:{queue:!0,stage:"pending",code:e.code,progress_data:e.progress_data,success:e.success}};case"log":return {type:"log",data:e};case"process_generating":return {type:"generating",status:{queue:!0,message:e.success?null:e.output.error,stage:e.success?"generating":"error",code:e.code,progress_data:e.progress_data,eta:e.average_duration,changed_state_ids:e.success?e.output.changed_state_ids:void 0},data:e.success?e.output:null};case"process_streaming":return {type:"streaming",status:{queue:!0,message:e.output.error,stage:"streaming",time_limit:e.time_limit,code:e.code,progress_data:e.progress_data,eta:e.eta},data:e.output};case"process_completed":return "error"in e.output?{type:"update",status:{queue:!0,title:e.output.title,message:e.output.error,visible:e.output.visible,duration:e.output.duration,stage:"error",code:e.code,success:e.success}}:{type:"complete",status:{queue:!0,message:e.success?void 0:e.output.error,stage:e.success?"complete":"error",code:e.code,progress_data:e.progress_data,changed_state_ids:e.success?e.output.changed_state_ids:void 0},data:e.success?e.output:null};case"process_starts":return {type:"update",status:{queue:!0,stage:"pending",code:e.code,size:e.rank,position:0,success:e.success,eta:e.eta},original_msg:"process_starts"}}return {type:"none",status:{stage:"error",queue:!0}}}const _s=(e=[],t)=>{const n=t?t.parameters:[];if(Array.isArray(e))return t&&n.length>0&&e.length>n.length&&console.warn("Too many arguments provided for the endpoint."),e;const r=[],i=Object.keys(e);return n.forEach((o,s)=>{if(e.hasOwnProperty(o.parameter_name))r[s]=e[o.parameter_name];else if(o.parameter_has_default)r[s]=o.parameter_default;else throw new Error(`No value provided for required parameter: ${o.parameter_name}`)}),i.forEach(o=>{if(!n.some(s=>s.parameter_name===o))throw new Error(`Parameter \`${o}\` is not a valid keyword argument. Please refer to the API for usage.`)}),r.forEach((o,s)=>{if(o===void 0&&!n[s].parameter_has_default)throw new Error(`No value provided for required parameter: ${n[s].parameter_name}`)}),r};async function As(){if(this.api_info)return this.api_info;const{hf_token:e}=this.options,{config:t}=this,n={"Content-Type":"application/json"};if(e&&(n.Authorization=`Bearer ${e}`),!!t)try{let r,i;if(typeof window<"u"&&window.gradio_api_info)i=window.gradio_api_info;else {if(Ar$1(t?.version||"2.0.0","3.30")<0)r=await this.fetch(es,{method:"POST",body:JSON.stringify({serialize:!1,config:JSON.stringify(t)}),headers:n,credentials:"include"});else {const o=St$2(t.root,this.api_prefix,Vo);r=await this.fetch(o,{headers:n,credentials:"include"});}if(!r.ok)throw new Error(Se$1);i=await r.json();}return "api"in i&&(i=i.api),i.named_endpoints["/predict"]&&!i.unnamed_endpoints[0]&&(i.unnamed_endpoints[0]=i.named_endpoints["/predict"]),ps(i,t,this.api_map)}catch(r){throw new Error("Could not get API info. "+r.message)}}async function gs(e,t,n){const r={};this?.options?.hf_token&&(r.Authorization=`Bearer ${this.options.hf_token}`);const i=1e3,o=[];let s;for(let a=0;a<t.length;a+=i){const h=t.slice(a,a+i),l=new FormData;h.forEach(u=>{l.append("files",u);});try{const u=n?`${e}${this.api_prefix}/${dn$2}?upload_id=${n}`:`${e}${this.api_prefix}/${dn$2}`;s=await this.fetch(u,{method:"POST",body:l,headers:r,credentials:"include"});}catch(u){throw new Error(Se$1+u.message)}if(!s.ok){const u=await s.text();return {error:`HTTP ${s.status}: ${u}`}}const c=await s.json();c&&o.push(...c);}return {files:o}}async function bs(e,t,n,r){let i=(Array.isArray(e)?e:[e]).map(s=>s.blob);const o=i.filter(s=>s.size>(r??1/0));if(o.length)throw new Error(`File size exceeds the maximum allowed size of ${r} bytes: ${o.map(s=>s.name).join(", ")}`);return await Promise.all(await this.upload_files(t,i,n).then(async s=>{if(s.error)throw new Error(s.error);return s.files?s.files.map((a,h)=>new et$2({...e[h],path:a,url:`${t}${this.api_prefix}/file=${a}`})):[]}))}async function ha(e,t){return e.map(n=>new et$2({path:n.name,orig_name:n.name,blob:n,size:n.size,mime_type:n.type,is_stream:t}))}let et$2 = class et{path;url;orig_name;size;blob;is_stream;mime_type;alt_text;b64;meta={_type:"gradio.FileData"};constructor({path:t,url:n,orig_name:r,size:i,blob:o,is_stream:s,mime_type:a,alt_text:h,b64:l}){this.path=t,this.url=n,this.orig_name=r,this.size=i,this.blob=n?void 0:o,this.is_stream=s,this.mime_type=a,this.alt_text=h,this.b64=l;}};class vs{type;command;meta;fileData;constructor(t,n){this.type="command",this.command=t,this.meta=n;}}typeof process<"u"&&process.versions&&process.versions.node;function An$2(e,t,n){for(;n.length>1;){const i=n.shift();if(typeof i=="string"||typeof i=="number")e=e[i];else throw new Error("Invalid key type")}const r=n.shift();if(typeof r=="string"||typeof r=="number")e[r]=t;else throw new Error("Invalid key type")}async function Bt$1(e,t=void 0,n=[],r=!1,i=void 0){if(Array.isArray(e)){let o=[];return await Promise.all(e.map(async(s,a)=>{let h=n.slice();h.push(String(a));const l=await Bt$1(e[a],r?i?.parameters[a]?.component||void 0:t,h,!1,i);o=o.concat(l);})),o}else {if(globalThis.Buffer&&e instanceof globalThis.Buffer||e instanceof Blob)return [{path:n,blob:new Blob([e]),type:t}];if(typeof e=="object"&&e!==null){let o=[];for(const s of Object.keys(e)){const a=[...n,s],h=e[s];o=o.concat(await Bt$1(h,void 0,a,!1,i));}return o}}return []}function ys(e,t){let n=t?.dependencies?.find(r=>r.id==e)?.queue;return n!=null?!n:!t.enable_queue}function ws(e,t){return new Promise((n,r)=>{const i=new MessageChannel;i.port1.onmessage=({data:o})=>{i.port1.close(),n(o);},window.parent.postMessage(e,t,[i.port2]);})}function Pe$1(e,t,n,r,i=!1){if(r==="input"&&!i)throw new Error("Invalid code path. Cannot skip state inputs for input.");if(r==="output"&&i)return e;let o=[],s=0;const a=r==="input"?t.inputs:t.outputs;for(let h=0;h<a.length;h++){const l=a[h];if(n.find(u=>u.id===l)?.type==="state"){if(i)if(e.length===a.length){const u=e[s];o.push(u),s++;}else o.push(null);else {s++;continue}continue}else {const u=e[s];o.push(u),s++;}}return o}async function Cs(e,t,n){const r=this;await Es(r,t);const i=await Bt$1(t,void 0,[],!0,n);return (await Promise.all(i.map(async({path:s,blob:a,type:h})=>{if(!a)return {path:s,type:h};const l=await r.upload_files(e,[a]),c=l.files&&l.files[0];return {path:s,file_url:c,type:h,name:typeof File<"u"&&a instanceof File?a?.name:void 0}}))).forEach(({path:s,file_url:a,type:h,name:l})=>{if(h==="Gallery")An$2(t,a,s);else if(a){const c=new et$2({path:a,orig_name:l});An$2(t,c,s);}}),t}async function Es(e,t){if(!(e.config?.root||e.config?.root_url))throw new Error(yr$1);await Er$1(e,t);}async function Er$1(e,t,n=[]){for(const r in t)t[r]instanceof vs?await xs(e,t,r):typeof t[r]=="object"&&t[r]!==null&&await Er$1(e,t[r],[...n,r]);}async function xs(e,t,n){let r=t[n];const i=e.config?.root||e.config?.root_url;if(!i)throw new Error(yr$1);try{let o,s;if(typeof process<"u"&&process.versions&&process.versions.node){const c=await import('fs/promises');s=(await import('path')).resolve(process.cwd(),r.meta.path),o=await c.readFile(s);}else throw new Error(ss);const a=new Blob([o],{type:"application/octet-stream"}),h=await e.upload_files(i,[a]),l=h.files&&h.files[0];if(l){const c=new et$2({path:l,orig_name:r.meta.name||""});t[n]=c;}}catch(o){console.error(as,o);}}async function Ss(e,t,n){const r={"Content-Type":"application/json"};this.options.hf_token&&(r.Authorization=`Bearer ${this.options.hf_token}`);try{var i=await this.fetch(e,{method:"POST",body:JSON.stringify(t),headers:{...r,...n},credentials:"include"});}catch{return [{error:Se$1},500]}let o,s;try{o=await i.json(),s=i.status;}catch(a){o={error:`Could not parse server response: ${a}`},s=500;}return [o,s]}async function Bs(e,t={}){let n=!1,r=!1;if(!this.config)throw new Error("Could not resolve app config");if(typeof e=="number")this.config.dependencies.find(i=>i.id==e);else {const i=e.replace(/^\//,"");this.config.dependencies.find(o=>o.id==this.api_map[i]);}return new Promise(async(i,o)=>{const s=this.submit(e,t,null,null,!0);let a;for await(const h of s)h.type==="data"&&(r&&i(a),n=!0,a=h),h.type==="status"&&(h.stage==="error"&&o(h),h.stage==="complete"&&(r=!0,n&&i(a)));})}async function Re$1(e,t,n){let r=t==="subdomain"?`https://huggingface.co/api/spaces/by-subdomain/${e}`:`https://huggingface.co/api/spaces/${e}`,i,o;try{if(i=await fetch(r),o=i.status,o!==200)throw new Error;i=await i.json();}catch{n({status:"error",load_status:"error",message:ts,detail:"NOT_FOUND"});return}if(!i||o!==200)return;const{runtime:{stage:s},id:a}=i;switch(s){case"STOPPED":case"SLEEPING":n({status:"sleeping",load_status:"pending",message:"Space is asleep. Waking it up...",detail:s}),setTimeout(()=>{Re$1(e,t,n);},1e3);break;case"PAUSED":n({status:"paused",load_status:"error",message:"This space has been paused by the author. If you would like to try this demo, consider duplicating the space.",detail:s,discussions_enabled:await gn$1(a)});break;case"RUNNING":case"RUNNING_BUILDING":n({status:"running",load_status:"complete",message:"Space is running.",detail:s});break;case"BUILDING":n({status:"building",load_status:"pending",message:"Space is building...",detail:s}),setTimeout(()=>{Re$1(e,t,n);},1e3);break;case"APP_STARTING":n({status:"starting",load_status:"pending",message:"Space is starting...",detail:s}),setTimeout(()=>{Re$1(e,t,n);},1e3);break;default:n({status:"space_error",load_status:"error",message:"This space is experiencing an issue.",detail:s,discussions_enabled:await gn$1(a)});break}}const xr$1=async(e,t)=>{let n=0;const r=12,i=5e3;return new Promise(o=>{Re$1(e,Rt$2.test(e)?"space_name":"subdomain",s=>{t(s),s.status==="running"||s.status==="error"||s.status==="paused"||s.status==="space_error"?o():(s.status==="sleeping"||s.status==="building")&&(n<r?(n++,setTimeout(()=>{xr$1(e,t).then(o);},i)):o());});})},Is=/^(?=[^]*\b[dD]iscussions{0,1}\b)(?=[^]*\b[dD]isabled\b)[^]*$/;async function gn$1(e){try{const t=await fetch(`https://huggingface.co/api/spaces/${e}/discussions`,{method:"HEAD"}),n=t.headers.get("x-error-message");return !(!t.ok||n&&Is.test(n))}catch{return !1}}async function Ts(e,t){const n={};t&&(n.Authorization=`Bearer ${t}`);try{const r=await fetch(`https://huggingface.co/api/spaces/${e}/${qo}`,{headers:n});if(r.status!==200)throw new Error("Space hardware could not be obtained.");const{hardware:i}=await r.json();return i.current}catch(r){throw new Error(r.message)}}async function Os(e,t,n){const r={};n&&(r.Authorization=`Bearer ${n}`);const i={seconds:t};try{const o=await fetch(`https://huggingface.co/api/spaces/${e}/${Qo}`,{method:"POST",headers:{"Content-Type":"application/json",...r},body:JSON.stringify(i)});if(o.status!==200)throw new Error("Could not set sleep timeout on duplicated Space. Please visit *ADD HF LINK TO SETTINGS* to set a timeout manually to reduce billing charges.");return await o.json()}catch(o){throw new Error(o.message)}}const bn$1=["cpu-basic","cpu-upgrade","cpu-xl","t4-small","t4-medium","a10g-small","a10g-large","a10g-largex2","a10g-largex4","a100-large","zero-a10g","h100","h100x8"];async function Hs(e,t){const{hf_token:n,private:r,hardware:i,timeout:o,auth:s}=t;if(i&&!bn$1.includes(i))throw new Error(`Invalid hardware type provided. Valid types are: ${bn$1.map(w=>`"${w}"`).join(",")}.`);const{http_protocol:a,host:h}=await Je(e,n);let l=null;if(s){const w=await wr$1(a,h,s,fetch);w&&(l=Cr$1(w));}const c={Authorization:`Bearer ${n}`,"Content-Type":"application/json",...l?{Cookie:l.join("; ")}:{}},u=(await(await fetch("https://huggingface.co/api/whoami-v2",{headers:c})).json()).name,f=e.split("/")[1],A={repository:`${u}/${f}`};r&&(A.private=!0);let _;try{i||(_=await Ts(e,n));}catch(w){throw Error(Lt$1+w.message)}const S=i||_||"cpu-basic";A.hardware=S;try{const w=await fetch(`https://huggingface.co/api/spaces/${e}/duplicate`,{method:"POST",headers:c,body:JSON.stringify(A)});if(w.status===409)try{return await yn$1.connect(`${u}/${f}`,t)}catch(R){throw console.error("Failed to connect Client instance:",R),R}else if(w.status!==200)throw new Error(w.statusText);const D=await w.json();return await Os(`${u}/${f}`,o||300,n),await yn$1.connect(Ps(D.url),t)}catch(w){throw new Error(w)}}function Ps(e){const t=/https:\/\/huggingface.co\/spaces\/([^/]+\/[^/]+)/,n=e.match(t);if(n)return n[1]}class Ns extends TransformStream{#e="";constructor(t={allowCR:!1}){super({transform:(n,r)=>{for(n=this.#e+n;;){const i=n.indexOf(`
`),o=t.allowCR?n.indexOf("\r"):-1;if(o!==-1&&o!==n.length-1&&(i===-1||i-1>o)){r.enqueue(n.slice(0,o)),n=n.slice(o+1);continue}if(i===-1)break;const s=n[i-1]==="\r"?i-1:i;r.enqueue(n.slice(0,s)),n=n.slice(i+1);}this.#e=n;},flush:n=>{if(this.#e==="")return;const r=t.allowCR&&this.#e.endsWith("\r")?this.#e.slice(0,-1):this.#e;n.enqueue(r);}});}}function ks(e){let t=new TextDecoderStream,n=new Ns({allowCR:!0});return e.pipeThrough(t).pipeThrough(n)}function Ms(e){let n=/[:]\s*/.exec(e),r=n&&n.index;if(r)return [e.substring(0,r),e.substring(r+n[0].length)]}function vn$2(e,t,n){e.get(t)||e.set(t,n);}async function*Ls(e,t){if(!e.body)return;let n=ks(e.body),r,i=n.getReader(),o;for(;;){if(t&&t.aborted)return i.cancel();if(r=await i.read(),r.done)return;if(!r.value){o&&(yield o),o=void 0;continue}let[s,a]=Ms(r.value)||[];s&&(s==="data"?(o||={},o[s]=o[s]?o[s]+`
`+a:a):s==="event"?(o||={},o[s]=a):s==="id"?(o||={},o[s]=+a||a):s==="retry"&&(o||={},o[s]=+a||void 0));}}async function Rs(e,t){let n=new Request(e,t);vn$2(n.headers,"Accept","text/event-stream"),vn$2(n.headers,"Content-Type","application/json");let r=await fetch(n);if(!r.ok)throw r;return Ls(r,n.signal)}async function Ds(){let{event_callbacks:e,unclosed_events:t,pending_stream_messages:n,stream_status:r,config:i,jwt:o}=this;const s=this;if(!i)throw new Error("Could not resolve app config");r.open=!0;let a=null,h=new URLSearchParams({session_hash:this.session_hash}).toString(),l=new URL(`${i.root}${this.api_prefix}/${gr$1}?${h}`);if(o&&l.searchParams.set("__sign",o),a=this.stream(l),!a){console.warn("Cannot connect to SSE endpoint: "+l.toString());return}a.onmessage=async function(c){let u=JSON.parse(c.data);if(u.msg==="close_stream"){Dt$2(r,s.abort_controller);return}const f=u.event_id;if(!f)await Promise.all(Object.keys(e).map(A=>e[A](u)));else if(e[f]&&i){u.msg==="process_completed"&&["sse","sse_v1","sse_v2","sse_v2.1","sse_v3"].includes(i.protocol)&&t.delete(f);let A=e[f];typeof window<"u"&&typeof document<"u"?setTimeout(A,0,u):A(u);}else n[f]||(n[f]=[]),n[f].push(u);},a.onerror=async function(c){console.error(c),await Promise.all(Object.keys(e).map(u=>e[u]({msg:"broken_connection",message:Se$1})));};}function Dt$2(e,t){e&&(e.open=!1,t?.abort());}function Us(e,t,n){!e[t]?(e[t]=[],n.data.forEach((i,o)=>{e[t][o]=i;})):n.data.forEach((i,o)=>{let s=js(e[t][o],i);e[t][o]=s,n.data[o]=s;});}function js(e,t){return t.forEach(([n,r,i])=>{e=Gs(e,r,n,i);}),e}function Gs(e,t,n,r){if(t.length===0){if(n==="replace")return r;if(n==="append")return e+r;throw new Error(`Unsupported action: ${n}`)}let i=e;for(let s=0;s<t.length-1;s++)i=i[t[s]];const o=t[t.length-1];switch(n){case"replace":i[o]=r;break;case"append":i[o]+=r;break;case"add":Array.isArray(i)?i.splice(Number(o),0,r):i[o]=r;break;case"delete":Array.isArray(i)?i.splice(Number(o),1):delete i[o];break;default:throw new Error(`Unknown action: ${n}`)}return e}function Fs(e,t={}){const n={close:()=>{console.warn("Method not implemented.");},onerror:null,onmessage:null,onopen:null,readyState:0,url:e.toString(),withCredentials:!1,CONNECTING:0,OPEN:1,CLOSED:2,addEventListener:()=>{throw new Error("Method not implemented.")},dispatchEvent:()=>{throw new Error("Method not implemented.")},removeEventListener:()=>{throw new Error("Method not implemented.")}};return Rs(e,t).then(async r=>{n.readyState=n.OPEN;try{for await(const i of r)n.onmessage&&n.onmessage(i);n.readyState=n.CLOSED;}catch(i){n.onerror&&n.onerror(i),n.readyState=n.CLOSED;}}).catch(r=>{console.error(r),n.onerror&&n.onerror(r),n.readyState=n.CLOSED;}),n}function zs(e,t={},n,r,i){try{let o=function(N){(i||ce[N.type])&&l(N);},s=function(){for(Te=!0;se.length>0;)se.shift()({value:void 0,done:!0});},a=function(N){se.length>0?se.shift()(N):ue.push(N);},h=function(N){a($s(N)),s();},l=function(N){a({value:N,done:!1});},c=function(){return ue.length>0?Promise.resolve(ue.shift()):new Promise(N=>se.push(N))};const{hf_token:u}=this.options,{fetch:f,app_reference:A,config:_,session_hash:S,api_info:w,api_map:D,stream_status:R,pending_stream_messages:L,pending_diff_streams:F,event_callbacks:k,unclosed_events:z,post_data:P,options:O,api_prefix:B}=this,$=this;if(!w)throw new Error("No API found");if(!_)throw new Error("Could not resolve app config");let{fn_index:g,endpoint_info:Q,dependency:j}=Ws(w,e,D,_),J=_s(t,Q),W,le,b=_.protocol??"ws",v="",x=()=>v;const p=typeof e=="number"?"/predict":e;let m,C=null,d=!1,U={},y=typeof window<"u"&&typeof document<"u"?new URLSearchParams(window.location.search).toString():"";const ce=O?.events?.reduce((N,ae)=>(N[ae]=!0,N),{})||{};async function _e(){let N={},ae={};b==="ws"?(W&&W.readyState===0?W.addEventListener("open",()=>{W.close();}):W.close(),N={fn_index:g,session_hash:S}):(N={event_id:C},ae={event_id:C,session_hash:S,fn_index:g});try{if(!_)throw new Error("Could not resolve app config");"event_id"in ae&&await f(`${_.root}${B}/${Yo}`,{headers:{"Content-Type":"application/json"},method:"POST",body:JSON.stringify(ae)}),await f(`${_.root}${B}/${Zo}`,{headers:{"Content-Type":"application/json"},method:"POST",body:JSON.stringify(N)});}catch{console.warn("The `/reset` endpoint could not be called. Subsequent endpoint results may be unreliable.");}}const E=async N=>{await this._resolve_heartbeat(N);};async function X(N){if(!_)return;let ae=N.render_id;_.components=[..._.components.filter(K=>K.props.rendered_in!==ae),...N.components],_.dependencies=[..._.dependencies.filter(K=>K.rendered_in!==ae),...N.dependencies];const Ge=_.components.some(K=>K.type==="state"),G=_.dependencies.some(K=>K.targets.some(ie=>ie[1]==="unload"));_.connect_heartbeat=Ge||G,await E(_),o({type:"render",data:N,endpoint:p,fn_index:g});}this.handle_blob(_.root,J,Q).then(async N=>{if(m={data:Pe$1(N,j,_.components,"input",!0)||[],event_data:n,fn_index:g,trigger_id:r},ys(g,_))o({type:"status",endpoint:p,stage:"pending",queue:!1,fn_index:g,time:new Date}),P(`${_.root}${B}/run${p.startsWith("/")?p:`/${p}`}${y?"?"+y:""}`,{...m,session_hash:S}).then(([G,K])=>{const ie=G.data;K==200?(o({type:"data",endpoint:p,fn_index:g,data:Pe$1(ie,j,_.components,"output",O.with_null_state),time:new Date,event_data:n,trigger_id:r}),G.render_config&&X(G.render_config),o({type:"status",endpoint:p,fn_index:g,stage:"complete",eta:G.average_duration,queue:!1,time:new Date})):o({type:"status",stage:"error",endpoint:p,fn_index:g,message:G.error,queue:!1,time:new Date});}).catch(G=>{o({type:"status",stage:"error",message:G.message,endpoint:p,fn_index:g,queue:!1,time:new Date});});else if(b=="ws"){const{ws_protocol:G,host:K}=await Je(A,u);o({type:"status",stage:"pending",queue:!0,endpoint:p,fn_index:g,time:new Date});let ie=new URL(`${G}://${ls(K,_.root,!0)}/queue/join${y?"?"+y:""}`);this.jwt&&ie.searchParams.set("__sign",this.jwt),W=new WebSocket(ie),W.onclose=ee=>{ee.wasClean||o({type:"status",stage:"error",broken:!0,message:Se$1,queue:!0,endpoint:p,fn_index:g,time:new Date});},W.onmessage=function(ee){const oe=JSON.parse(ee.data),{type:V,status:Z,data:Y}=ft$2(oe,U[g]);if(V==="update"&&Z&&!d)o({type:"status",endpoint:p,fn_index:g,time:new Date,...Z}),Z.stage==="error"&&W.close();else if(V==="hash"){W.send(JSON.stringify({fn_index:g,session_hash:S}));return}else V==="data"?W.send(JSON.stringify({...m,session_hash:S})):V==="complete"?d=Z:V==="log"?o({type:"log",title:Y.title,log:Y.log,level:Y.level,endpoint:p,duration:Y.duration,visible:Y.visible,fn_index:g}):V==="generating"&&o({type:"status",time:new Date,...Z,stage:Z?.stage,queue:!0,endpoint:p,fn_index:g});Y&&(o({type:"data",time:new Date,data:Pe$1(Y.data,j,_.components,"output",O.with_null_state),endpoint:p,fn_index:g,event_data:n,trigger_id:r}),d&&(o({type:"status",time:new Date,...d,stage:Z?.stage,queue:!0,endpoint:p,fn_index:g}),W.close()));},Ar$1(_.version||"2.0.0","3.6")<0&&addEventListener("open",()=>W.send(JSON.stringify({hash:S})));}else if(b=="sse"){o({type:"status",stage:"pending",queue:!0,endpoint:p,fn_index:g,time:new Date});var Ge=new URLSearchParams({fn_index:g.toString(),session_hash:S}).toString();let G=new URL(`${_.root}${B}/${gr$1}?${y?y+"&":""}${Ge}`);if(this.jwt&&G.searchParams.set("__sign",this.jwt),le=this.stream(G),!le)return Promise.reject(new Error("Cannot connect to SSE endpoint: "+G.toString()));le.onmessage=async function(K){const ie=JSON.parse(K.data),{type:ee,status:oe,data:V}=ft$2(ie,U[g]);if(ee==="update"&&oe&&!d)o({type:"status",endpoint:p,fn_index:g,time:new Date,...oe}),oe.stage==="error"&&(le?.close(),s());else if(ee==="data"){let[Z,Y]=await P(`${_.root}${B}/queue/data`,{...m,session_hash:S,event_id:C});Y!==200&&(o({type:"status",stage:"error",message:Se$1,queue:!0,endpoint:p,fn_index:g,time:new Date}),le?.close(),s());}else ee==="complete"?d=oe:ee==="log"?o({type:"log",title:V.title,log:V.log,level:V.level,endpoint:p,duration:V.duration,visible:V.visible,fn_index:g}):(ee==="generating"||ee==="streaming")&&o({type:"status",time:new Date,...oe,stage:oe?.stage,queue:!0,endpoint:p,fn_index:g});V&&(o({type:"data",time:new Date,data:Pe$1(V.data,j,_.components,"output",O.with_null_state),endpoint:p,fn_index:g,event_data:n,trigger_id:r}),d&&(o({type:"status",time:new Date,...d,stage:oe?.stage,queue:!0,endpoint:p,fn_index:g}),le?.close(),s()));};}else if(b=="sse_v1"||b=="sse_v2"||b=="sse_v2.1"||b=="sse_v3"){o({type:"status",stage:"pending",queue:!0,endpoint:p,fn_index:g,time:new Date});let G="";typeof window<"u"&&typeof document<"u"&&(G=window?.location?.hostname);const ie=G.includes(".dev.")?`https://moon-${G.split(".")[1]}.dev.spaces.huggingface.tech`:"https://huggingface.co";(typeof window<"u"&&typeof document<"u"&&window.parent!=window&&window.supports_zerogpu_headers?ws("zerogpu-headers",ie):Promise.resolve(null)).then(Z=>P(`${_.root}${B}/${$o}?${y}`,{...m,session_hash:S},Z)).then(async([Z,Y])=>{if(Y===503)o({type:"status",stage:"error",message:br$1,queue:!0,endpoint:p,fn_index:g,time:new Date});else if(Y===422)o({type:"status",stage:"error",message:Z.detail,queue:!0,endpoint:p,fn_index:g,code:"validation_error",time:new Date}),s();else if(Y!==200)o({type:"status",stage:"error",broken:!1,message:Z.detail,queue:!0,endpoint:p,fn_index:g,time:new Date});else {C=Z.event_id,v=C;let Ut=async function(tt){try{const{type:te,status:ne,data:re,original_msg:Sr}=ft$2(tt,U[g]);if(te=="heartbeat")return;if(te==="update"&&ne&&!d)o({type:"status",endpoint:p,fn_index:g,time:new Date,original_msg:Sr,...ne});else if(te==="complete")d=ne;else if(te=="unexpected_error"||te=="broken_connection"){console.error("Unexpected error",ne?.message);const Br=te==="broken_connection";o({type:"status",stage:"error",message:ne?.message||"An Unexpected Error Occurred!",queue:!0,endpoint:p,broken:Br,session_not_found:ne?.session_not_found,fn_index:g,time:new Date});}else if(te==="log"){o({type:"log",title:re.title,log:re.log,level:re.level,endpoint:p,duration:re.duration,visible:re.visible,fn_index:g});return}else (te==="generating"||te==="streaming")&&(o({type:"status",time:new Date,...ne,stage:ne?.stage,queue:!0,endpoint:p,fn_index:g}),re&&j.connection!=="stream"&&["sse_v2","sse_v2.1","sse_v3"].includes(b)&&Us(F,C,re));re&&(o({type:"data",time:new Date,data:Pe$1(re.data,j,_.components,"output",O.with_null_state),endpoint:p,fn_index:g}),re.render_config&&await X(re.render_config),d&&(o({type:"status",time:new Date,...d,stage:ne?.stage,queue:!0,endpoint:p,fn_index:g}),s())),(ne?.stage==="complete"||ne?.stage==="error")&&(k[C]&&delete k[C],C in F&&delete F[C]);}catch(te){console.error("Unexpected client exception",te),o({type:"status",stage:"error",message:"An Unexpected Error Occurred!",queue:!0,endpoint:p,fn_index:g,time:new Date}),["sse_v2","sse_v2.1","sse_v3"].includes(b)&&(Dt$2(R,$.abort_controller),R.open=!1,s());}};C in L&&(L[C].forEach(tt=>Ut(tt)),delete L[C]),k[C]=Ut,z.add(C),R.open||await this.open_stream();}});}});let Te=!1;const ue=[],se=[],ve={[Symbol.asyncIterator]:()=>ve,next:c,throw:async N=>(h(N),c()),return:async()=>(s(),c()),cancel:_e,event_id:x};return ve}catch(o){throw console.error("Submit function encountered an error:",o),o}}function $s(e){return {then:(t,n)=>n(e)}}function Ws(e,t,n,r){let i,o,s;if(typeof t=="number")i=t,o=e.unnamed_endpoints[i],s=r.dependencies.find(a=>a.id==t);else {const a=t.replace(/^\//,"");i=n[a],o=e.named_endpoints[t.trim()],s=r.dependencies.find(h=>h.id==n[a]);}if(typeof i!="number")throw new Error("There is no endpoint matching that name of fn_index matching that number.");return {fn_index:i,endpoint_info:o,dependency:s}}let yn$1 = class yn{app_reference;options;deep_link=null;config;api_prefix="";api_info;api_map={};session_hash=Math.random().toString(36).substring(2);jwt=!1;last_status={};cookies=null;stream_status={open:!1};closed=!1;pending_stream_messages={};pending_diff_streams={};event_callbacks={};unclosed_events=new Set;heartbeat_event=null;abort_controller=null;stream_instance=null;current_payload;ws_map={};get_url_config(t=null){if(!this.config)throw new Error(fe$2);t===null&&(t=window.location.href);const n=s=>s.replace(/^\/+|\/+$/g,"");let r=n(new URL(this.config.root).pathname),i=n(new URL(t).pathname),o;return i.startsWith(r)?o=n(i.substring(r.length)):o="",this.get_page_config(o)}get_page_config(t){if(!this.config)throw new Error(fe$2);let n=this.config;return t in n.page||(t=""),{...n,current_page:t,layout:n.page[t].layout,components:n.components.filter(r=>n.page[t].components.includes(r.id)),dependencies:this.config.dependencies.filter(r=>n.page[t].dependencies.includes(r.id))}}fetch(t,n){const r=new Headers(n?.headers||{});if(this&&this.cookies&&r.append("Cookie",this.cookies),this&&this.options.headers)for(const i in this.options.headers)r.append(i,this.options.headers[i]);return fetch(t,{...n,headers:r})}stream(t){const n=new Headers;if(this&&this.cookies&&n.append("Cookie",this.cookies),this&&this.options.headers)for(const r in this.options.headers)n.append(r,this.options.headers[r]);return this&&this.options.hf_token&&n.append("Authorization",`Bearer ${this.options.hf_token}`),this.abort_controller=new AbortController,this.stream_instance=Fs(t.toString(),{credentials:"include",headers:n,signal:this.abort_controller.signal}),this.stream_instance}view_api;upload_files;upload;handle_blob;post_data;submit;predict;open_stream;resolve_config;resolve_cookies;constructor(t,n={events:["data"]}){this.app_reference=t,this.deep_link=n.query_params?.deep_link||null,n.events||(n.events=["data"]),this.options=n,this.current_payload={},this.view_api=As.bind(this),this.upload_files=gs.bind(this),this.handle_blob=Cs.bind(this),this.post_data=Ss.bind(this),this.submit=zs.bind(this),this.predict=Bs.bind(this),this.open_stream=Ds.bind(this),this.resolve_config=us.bind(this),this.resolve_cookies=hs.bind(this),this.upload=bs.bind(this),this.fetch=this.fetch.bind(this),this.handle_space_success=this.handle_space_success.bind(this),this.stream=this.stream.bind(this);}async init(){if((typeof window>"u"||!("WebSocket"in window))&&!global.WebSocket){const t=await import('./wrapper-CYei9jbK.js');global.WebSocket=t.WebSocket;}this.options.auth&&await this.resolve_cookies(),await this._resolve_config().then(({config:t})=>this._resolve_heartbeat(t)),this.api_info=await this.view_api(),this.api_map=cs(this.config?.dependencies||[]);}async _resolve_heartbeat(t){if(t&&(this.config=t,this.api_prefix=t.api_prefix||"",this.config&&this.config.connect_heartbeat&&this.config.space_id&&this.options.hf_token&&(this.jwt=await mn$1(this.config.space_id,this.options.hf_token,this.cookies))),t.space_id&&this.options.hf_token&&(this.jwt=await mn$1(t.space_id,this.options.hf_token)),this.config&&this.config.connect_heartbeat){const n=new URL(`${this.config.root}${this.api_prefix}/${Xo}/${this.session_hash}`);this.jwt&&n.searchParams.set("__sign",this.jwt),this.heartbeat_event||(this.heartbeat_event=this.stream(n));}}static async connect(t,n={events:["data"]}){const r=new this(t,n);return n.session_hash&&(r.session_hash=n.session_hash),await r.init(),r}async reconnect(){const t=new URL(`${this.config.root}${this.api_prefix}/${Jo}`);let n;try{const r=await this.fetch(t);if(!r.ok)throw new Error;n=(await r.json()).app_id;}catch{return "broken"}return n!==this.config.app_id?"changed":"connected"}close(){this.closed=!0,Dt$2(this.stream_status,this.abort_controller);}set_current_payload(t){this.current_payload=t;}static async duplicate(t,n={events:["data"]}){return Hs(t,n)}async _resolve_config(){const{http_protocol:t,host:n,space_id:r}=await Je(this.app_reference,this.options.hf_token),{status_callback:i}=this.options;r&&i&&await xr$1(r,i);let o;try{let s=`${t}//${n}`;if(o=await this.resolve_config(s),!o)throw new Error(fe$2);return this.config_success(o)}catch(s){if(r&&i)Re$1(r,Rt$2.test(r)?"space_name":"subdomain",this.handle_space_success);else throw i&&i({status:"error",message:"Could not load this space.",load_status:"error",detail:"NOT_FOUND"}),Error(s)}}async config_success(t){if(this.config=t,this.api_prefix=t.api_prefix||"",this.config.auth_required)return this.prepare_return_obj();try{this.api_info=await this.view_api();}catch(n){console.error(ns+n.message);}return this.prepare_return_obj()}async handle_space_success(t){if(!this)throw new Error(fe$2);const{status_callback:n}=this.options;if(n&&n(t),t.status==="running")try{if(this.config=await this._resolve_config(),this.api_prefix=this?.config?.api_prefix||"",!this.config)throw new Error(fe$2);return await this.config_success(this.config)}catch(r){throw n&&n({status:"error",message:"Could not load this space.",load_status:"error",detail:"NOT_FOUND"}),r}}async component_server(t,n,r){if(!this.config)throw new Error(fe$2);const i={},{hf_token:o}=this.options,{session_hash:s}=this;o&&(i.Authorization=`Bearer ${this.options.hf_token}`);let a,h=this.config.components.find(c=>c.id===t);h?.props?.root_url?a=h.props.root_url:a=this.config.root;let l;if("binary"in r){l=new FormData;for(const c in r.data)c!=="binary"&&l.append(c,r.data[c]);l.set("component_id",t.toString()),l.set("fn_name",n),l.set("session_hash",s);}else l=JSON.stringify({data:r,component_id:t,fn_name:n,session_hash:s}),i["Content-Type"]="application/json";o&&(i.Authorization=`Bearer ${o}`);try{const c=await this.fetch(`${a}${this.api_prefix}/${Ko}/`,{method:"POST",body:l,headers:i,credentials:"include"});if(!c.ok)throw new Error("Could not connect to component server: "+c.statusText);return await c.json()}catch(c){console.warn(c);}}set_cookies(t){this.cookies=Cr$1(t).join("; ");}prepare_return_obj(){return {config:this.config,predict:this.predict,submit:this.submit,view_api:this.view_api,component_server:this.component_server}}async connect_ws(t){return new Promise((n,r)=>{let i;try{i=new WebSocket(t);}catch{this.ws_map[t]="failed";return}this.ws_map[t]="pending",i.onopen=()=>{this.ws_map[t]=i,n();},i.onerror=o=>{console.error("WebSocket error:",o),this.close_ws(t),this.ws_map[t]="failed",n();},i.onclose=()=>{this.ws_map[t]="closed";},i.onmessage=o=>{};})}async send_ws_message(t,n){if(!(t in this.ws_map))await this.connect_ws(t);else if(this.ws_map[t]==="pending"||this.ws_map[t]==="closed"||this.ws_map[t]==="failed")return;const r=this.ws_map[t];r instanceof WebSocket?r.send(JSON.stringify(n)):this.post_data(t,n);}async close_ws(t){if(t in this.ws_map){const n=this.ws_map[t];n instanceof WebSocket&&(n.close(),delete this.ws_map[t]);}}};

var client = /*#__PURE__*/Object.freeze({
	__proto__: null,
	$: Pt$2,
	A: Do,
	C: yn$1,
	E: Ys,
	F: et$2,
	M: os,
	a: wt$1,
	b: No,
	c: ua$1,
	d: ko,
	e: la$1,
	f: Lo,
	g: ca$1,
	h: Xs,
	i: ia$1,
	j: Hr$1,
	k: Le$1,
	l: sa$1,
	m: Js,
	n: yt$3,
	o: ta$1,
	p: ea$1,
	q: be$2,
	r: ha,
	s: aa$1,
	t: oa$1,
	u: na$1,
	v: ra$1,
	w: rn$2,
	x: Ks,
	y: Vr$1,
	z: Zs
});

/**
 * @param {any} obj
 * @returns {boolean}
 */
function is_date(obj) {
	return Object.prototype.toString.call(obj) === '[object Date]';
}

/**
 * @template T
 * @param {import('./private.js').TickContext<T>} ctx
 * @param {T} last_value
 * @param {T} current_value
 * @param {T} target_value
 * @returns {T}
 */
function tick_spring(ctx, last_value, current_value, target_value) {
	if (typeof current_value === 'number' || is_date(current_value)) {
		// @ts-ignore
		const delta = target_value - current_value;
		// @ts-ignore
		const velocity = (current_value - last_value) / (ctx.dt || 1 / 60); // guard div by 0
		const spring = ctx.opts.stiffness * delta;
		const damper = ctx.opts.damping * velocity;
		const acceleration = (spring - damper) * ctx.inv_mass;
		const d = (velocity + acceleration) * ctx.dt;
		if (Math.abs(d) < ctx.opts.precision && Math.abs(delta) < ctx.opts.precision) {
			return target_value; // settled
		} else {
			ctx.settled = false; // signal loop to keep ticking
			// @ts-ignore
			return is_date(current_value) ? new Date(current_value.getTime() + d) : current_value + d;
		}
	} else if (Array.isArray(current_value)) {
		// @ts-ignore
		return current_value.map((_, i) =>
			tick_spring(ctx, last_value[i], current_value[i], target_value[i])
		);
	} else if (typeof current_value === 'object') {
		const next_value = {};
		for (const k in current_value) {
			// @ts-ignore
			next_value[k] = tick_spring(ctx, last_value[k], current_value[k], target_value[k]);
		}
		// @ts-ignore
		return next_value;
	} else {
		throw new Error(`Cannot spring ${typeof current_value} values`);
	}
}

/**
 * The spring function in Svelte creates a store whose value is animated, with a motion that simulates the behavior of a spring. This means when the value changes, instead of transitioning at a steady rate, it "bounces" like a spring would, depending on the physics parameters provided. This adds a level of realism to the transitions and can enhance the user experience.
 *
 * https://svelte.dev/docs/svelte-motion#spring
 * @template [T=any]
 * @param {T} [value]
 * @param {import('./private.js').SpringOpts} [opts]
 * @returns {import('./public.js').Spring<T>}
 */
function spring(value, opts = {}) {
	const store = writable(value);
	const { stiffness = 0.15, damping = 0.8, precision = 0.01 } = opts;
	/** @type {number} */
	let last_time;
	/** @type {import('../internal/private.js').Task} */
	let task;
	/** @type {object} */
	let current_token;
	/** @type {T} */
	let last_value = value;
	/** @type {T} */
	let target_value = value;
	let inv_mass = 1;
	let inv_mass_recovery_rate = 0;
	let cancel_task = false;
	/**
	 * @param {T} new_value
	 * @param {import('./private.js').SpringUpdateOpts} opts
	 * @returns {Promise<void>}
	 */
	function set(new_value, opts = {}) {
		target_value = new_value;
		const token = (current_token = {});
		if (value == null || opts.hard || (spring.stiffness >= 1 && spring.damping >= 1)) {
			cancel_task = true; // cancel any running animation
			last_time = now();
			last_value = new_value;
			store.set((value = target_value));
			return Promise.resolve();
		} else if (opts.soft) {
			const rate = opts.soft === true ? 0.5 : +opts.soft;
			inv_mass_recovery_rate = 1 / (rate * 60);
			inv_mass = 0; // infinite mass, unaffected by spring forces
		}
		if (!task) {
			last_time = now();
			cancel_task = false;
			task = loop((now) => {
				if (cancel_task) {
					cancel_task = false;
					task = null;
					return false;
				}
				inv_mass = Math.min(inv_mass + inv_mass_recovery_rate, 1);
				const ctx = {
					inv_mass,
					opts: spring,
					settled: true,
					dt: ((now - last_time) * 60) / 1000
				};
				const next_value = tick_spring(ctx, last_value, value, target_value);
				last_time = now;
				last_value = value;
				store.set((value = next_value));
				if (ctx.settled) {
					task = null;
				}
				return !ctx.settled;
			});
		}
		return new Promise((fulfil) => {
			task.promise.then(() => {
				if (token === current_token) fulfil();
			});
		});
	}
	/** @type {import('./public.js').Spring<T>} */
	const spring = {
		set,
		update: (fn, opts) => set(fn(target_value, value), opts),
		subscribe: store.subscribe,
		stiffness,
		damping,
		precision
	};
	return spring;
}

var W={exports:{}};(function(G){var X=typeof window<"u"?window:typeof WorkerGlobalScope<"u"&&self instanceof WorkerGlobalScope?self:{};/**
 * Prism: Lightweight, robust, elegant syntax highlighting
 *
 * @license MIT <https://opensource.org/licenses/MIT>
 * @author Lea Verou <https://lea.verou.me>
 * @namespace
 * @public
 */var i=function(g){var h=/(?:^|\s)lang(?:uage)?-([\w-]+)(?=\s|$)/i,y=0,F={},s={manual:g.Prism&&g.Prism.manual,disableWorkerMessageHandler:g.Prism&&g.Prism.disableWorkerMessageHandler,util:{encode:function t(e){return e instanceof b?new b(e.type,t(e.content),e.alias):Array.isArray(e)?e.map(t):e.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/\u00a0/g," ")},type:function(t){return Object.prototype.toString.call(t).slice(8,-1)},objId:function(t){return t.__id||Object.defineProperty(t,"__id",{value:++y}),t.__id},clone:function t(e,a){a=a||{};var n,r;switch(s.util.type(e)){case"Object":if(r=s.util.objId(e),a[r])return a[r];n={},a[r]=n;for(var l in e)e.hasOwnProperty(l)&&(n[l]=t(e[l],a));return n;case"Array":return r=s.util.objId(e),a[r]?a[r]:(n=[],a[r]=n,e.forEach(function(o,u){n[u]=t(o,a);}),n);default:return e}},getLanguage:function(t){for(;t;){var e=h.exec(t.className);if(e)return e[1].toLowerCase();t=t.parentElement;}return "none"},setLanguage:function(t,e){t.className=t.className.replace(RegExp(h,"gi"),""),t.classList.add("language-"+e);},currentScript:function(){if(typeof document>"u")return null;if(document.currentScript&&document.currentScript.tagName==="SCRIPT")return document.currentScript;try{throw new Error}catch(n){var t=(/at [^(\r\n]*\((.*):[^:]+:[^:]+\)$/i.exec(n.stack)||[])[1];if(t){var e=document.getElementsByTagName("script");for(var a in e)if(e[a].src==t)return e[a]}return null}},isActive:function(t,e,a){for(var n="no-"+e;t;){var r=t.classList;if(r.contains(e))return !0;if(r.contains(n))return !1;t=t.parentElement;}return !!a}},languages:{plain:F,plaintext:F,text:F,txt:F,extend:function(t,e){var a=s.util.clone(s.languages[t]);for(var n in e)a[n]=e[n];return a},insertBefore:function(t,e,a,n){n=n||s.languages;var r=n[t],l={};for(var o in r)if(r.hasOwnProperty(o)){if(o==e)for(var u in a)a.hasOwnProperty(u)&&(l[u]=a[u]);a.hasOwnProperty(o)||(l[o]=r[o]);}var d=n[t];return n[t]=l,s.languages.DFS(s.languages,function(m,A){A===d&&m!=t&&(this[m]=l);}),l},DFS:function t(e,a,n,r){r=r||{};var l=s.util.objId;for(var o in e)if(e.hasOwnProperty(o)){a.call(e,o,e[o],n||o);var u=e[o],d=s.util.type(u);d==="Object"&&!r[l(u)]?(r[l(u)]=!0,t(u,a,null,r)):d==="Array"&&!r[l(u)]&&(r[l(u)]=!0,t(u,a,o,r));}}},plugins:{},highlightAll:function(t,e){s.highlightAllUnder(document,t,e);},highlightAllUnder:function(t,e,a){var n={callback:a,container:t,selector:'code[class*="language-"], [class*="language-"] code, code[class*="lang-"], [class*="lang-"] code'};s.hooks.run("before-highlightall",n),n.elements=Array.prototype.slice.apply(n.container.querySelectorAll(n.selector)),s.hooks.run("before-all-elements-highlight",n);for(var r=0,l;l=n.elements[r++];)s.highlightElement(l,e===!0,n.callback);},highlightElement:function(t,e,a){var n=s.util.getLanguage(t),r=s.languages[n];s.util.setLanguage(t,n);var l=t.parentElement;l&&l.nodeName.toLowerCase()==="pre"&&s.util.setLanguage(l,n);var o=t.textContent,u={element:t,language:n,grammar:r,code:o};function d(A){u.highlightedCode=A,s.hooks.run("before-insert",u),u.element.innerHTML=u.highlightedCode,s.hooks.run("after-highlight",u),s.hooks.run("complete",u),a&&a.call(u.element);}if(s.hooks.run("before-sanity-check",u),l=u.element.parentElement,l&&l.nodeName.toLowerCase()==="pre"&&!l.hasAttribute("tabindex")&&l.setAttribute("tabindex","0"),!u.code){s.hooks.run("complete",u),a&&a.call(u.element);return}if(s.hooks.run("before-highlight",u),!u.grammar){d(s.util.encode(u.code));return}if(e&&g.Worker){var m=new Worker(s.filename);m.onmessage=function(A){d(A.data);},m.postMessage(JSON.stringify({language:u.language,code:u.code,immediateClose:!0}));}else d(s.highlight(u.code,u.grammar,u.language));},highlight:function(t,e,a){var n={code:t,grammar:e,language:a};if(s.hooks.run("before-tokenize",n),!n.grammar)throw new Error('The language "'+n.language+'" has no grammar.');return n.tokens=s.tokenize(n.code,n.grammar),s.hooks.run("after-tokenize",n),b.stringify(s.util.encode(n.tokens),n.language)},tokenize:function(t,e){var a=e.rest;if(a){for(var n in a)e[n]=a[n];delete e.rest;}var r=new _;return S(r,r.head,t),C(t,r,e,r.head,0),P(r)},hooks:{all:{},add:function(t,e){var a=s.hooks.all;a[t]=a[t]||[],a[t].push(e);},run:function(t,e){var a=s.hooks.all[t];if(!(!a||!a.length))for(var n=0,r;r=a[n++];)r(e);}},Token:b};g.Prism=s;function b(t,e,a,n){this.type=t,this.content=e,this.alias=a,this.length=(n||"").length|0;}b.stringify=function t(e,a){if(typeof e=="string")return e;if(Array.isArray(e)){var n="";return e.forEach(function(d){n+=t(d,a);}),n}var r={type:e.type,content:t(e.content,a),tag:"span",classes:["token",e.type],attributes:{},language:a},l=e.alias;l&&(Array.isArray(l)?Array.prototype.push.apply(r.classes,l):r.classes.push(l)),s.hooks.run("wrap",r);var o="";for(var u in r.attributes)o+=" "+u+'="'+(r.attributes[u]||"").replace(/"/g,"&quot;")+'"';return "<"+r.tag+' class="'+r.classes.join(" ")+'"'+o+">"+r.content+"</"+r.tag+">"};function E(t,e,a,n){t.lastIndex=e;var r=t.exec(a);if(r&&n&&r[1]){var l=r[1].length;r.index+=l,r[0]=r[0].slice(l);}return r}function C(t,e,a,n,r,l){for(var o in a)if(!(!a.hasOwnProperty(o)||!a[o])){var u=a[o];u=Array.isArray(u)?u:[u];for(var d=0;d<u.length;++d){if(l&&l.cause==o+","+d)return;var m=u[d],A=m.inside,H=!!m.lookbehind,q=!!m.greedy,Y=m.alias;if(q&&!m.pattern.global){var J=m.pattern.toString().match(/[imsuy]*$/)[0];m.pattern=RegExp(m.pattern.source,J+"g");}for(var Z=m.pattern||m,v=n.next,w=r;v!==e.tail&&!(l&&w>=l.reach);w+=v.value.length,v=v.next){var $=v.value;if(e.length>t.length)return;if(!($ instanceof b)){var z=1,x;if(q){if(x=E(Z,w,t,H),!x||x.index>=t.length)break;var L=x.index,N=x.index+x[0].length,k=w;for(k+=v.value.length;L>=k;)v=v.next,k+=v.value.length;if(k-=v.value.length,w=k,v.value instanceof b)continue;for(var T=v;T!==e.tail&&(k<N||typeof T.value=="string");T=T.next)z++,k+=T.value.length;z--,$=t.slice(w,k),x.index-=w;}else if(x=E(Z,0,$,H),!x)continue;var L=x.index,I=x[0],M=$.slice(0,L),B=$.slice(L+I.length),R=w+$.length;l&&R>l.reach&&(l.reach=R);var j=v.prev;M&&(j=S(e,j,M),w+=M.length),D(e,j,z);var K=new b(o,A?s.tokenize(I,A):I,Y,I);if(v=S(e,j,K),B&&S(e,v,B),z>1){var O={cause:o+","+d,reach:R};C(t,e,a,v.prev,w,O),l&&O.reach>l.reach&&(l.reach=O.reach);}}}}}}function _(){var t={value:null,prev:null,next:null},e={value:null,prev:t,next:null};t.next=e,this.head=t,this.tail=e,this.length=0;}function S(t,e,a){var n=e.next,r={value:a,prev:e,next:n};return e.next=r,n.prev=r,t.length++,r}function D(t,e,a){for(var n=e.next,r=0;r<a&&n!==t.tail;r++)n=n.next;e.next=n,n.prev=e,t.length-=r;}function P(t){for(var e=[],a=t.head.next;a!==t.tail;)e.push(a.value),a=a.next;return e}if(!g.document)return g.addEventListener&&(s.disableWorkerMessageHandler||g.addEventListener("message",function(t){var e=JSON.parse(t.data),a=e.language,n=e.code,r=e.immediateClose;g.postMessage(s.highlight(n,s.languages[a],a)),r&&g.close();},!1)),s;var p=s.util.currentScript();p&&(s.filename=p.src,p.hasAttribute("data-manual")&&(s.manual=!0));function c(){s.manual||s.highlightAll();}if(!s.manual){var f=document.readyState;f==="loading"||f==="interactive"&&p&&p.defer?document.addEventListener("DOMContentLoaded",c):window.requestAnimationFrame?window.requestAnimationFrame(c):window.setTimeout(c,16);}return s}(X);G.exports&&(G.exports=i),typeof Xs<"u"&&(Xs.Prism=i),i.languages.markup={comment:{pattern:/<!--(?:(?!<!--)[\s\S])*?-->/,greedy:!0},prolog:{pattern:/<\?[\s\S]+?\?>/,greedy:!0},doctype:{pattern:/<!DOCTYPE(?:[^>"'[\]]|"[^"]*"|'[^']*')+(?:\[(?:[^<"'\]]|"[^"]*"|'[^']*'|<(?!!--)|<!--(?:[^-]|-(?!->))*-->)*\]\s*)?>/i,greedy:!0,inside:{"internal-subset":{pattern:/(^[^\[]*\[)[\s\S]+(?=\]>$)/,lookbehind:!0,greedy:!0,inside:null},string:{pattern:/"[^"]*"|'[^']*'/,greedy:!0},punctuation:/^<!|>$|[[\]]/,"doctype-tag":/^DOCTYPE/i,name:/[^\s<>'"]+/}},cdata:{pattern:/<!\[CDATA\[[\s\S]*?\]\]>/i,greedy:!0},tag:{pattern:/<\/?(?!\d)[^\s>\/=$<%]+(?:\s(?:\s*[^\s>\/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s'">=]+(?=[\s>]))|(?=[\s/>])))+)?\s*\/?>/,greedy:!0,inside:{tag:{pattern:/^<\/?[^\s>\/]+/,inside:{punctuation:/^<\/?/,namespace:/^[^\s>\/:]+:/}},"special-attr":[],"attr-value":{pattern:/=\s*(?:"[^"]*"|'[^']*'|[^\s'">=]+)/,inside:{punctuation:[{pattern:/^=/,alias:"attr-equals"},{pattern:/^(\s*)["']|["']$/,lookbehind:!0}]}},punctuation:/\/?>/,"attr-name":{pattern:/[^\s>\/]+/,inside:{namespace:/^[^\s>\/:]+:/}}}},entity:[{pattern:/&[\da-z]{1,8};/i,alias:"named-entity"},/&#x?[\da-f]{1,8};/i]},i.languages.markup.tag.inside["attr-value"].inside.entity=i.languages.markup.entity,i.languages.markup.doctype.inside["internal-subset"].inside=i.languages.markup,i.hooks.add("wrap",function(g){g.type==="entity"&&(g.attributes.title=g.content.replace(/&amp;/,"&"));}),Object.defineProperty(i.languages.markup.tag,"addInlined",{value:function(h,y){var F={};F["language-"+y]={pattern:/(^<!\[CDATA\[)[\s\S]+?(?=\]\]>$)/i,lookbehind:!0,inside:i.languages[y]},F.cdata=/^<!\[CDATA\[|\]\]>$/i;var s={"included-cdata":{pattern:/<!\[CDATA\[[\s\S]*?\]\]>/i,inside:F}};s["language-"+y]={pattern:/[\s\S]+/,inside:i.languages[y]};var b={};b[h]={pattern:RegExp(/(<__[^>]*>)(?:<!\[CDATA\[(?:[^\]]|\](?!\]>))*\]\]>|(?!<!\[CDATA\[)[\s\S])*?(?=<\/__>)/.source.replace(/__/g,function(){return h}),"i"),lookbehind:!0,greedy:!0,inside:s},i.languages.insertBefore("markup","cdata",b);}}),Object.defineProperty(i.languages.markup.tag,"addAttribute",{value:function(g,h){i.languages.markup.tag.inside["special-attr"].push({pattern:RegExp(/(^|["'\s])/.source+"(?:"+g+")"+/\s*=\s*(?:"[^"]*"|'[^']*'|[^\s'">=]+(?=[\s>]))/.source,"i"),lookbehind:!0,inside:{"attr-name":/^[^\s=]+/,"attr-value":{pattern:/=[\s\S]+/,inside:{value:{pattern:/(^=\s*(["']|(?!["'])))\S[\s\S]*(?=\2$)/,lookbehind:!0,alias:[h,"language-"+h],inside:i.languages[h]},punctuation:[{pattern:/^=/,alias:"attr-equals"},/"|'/]}}}});}}),i.languages.html=i.languages.markup,i.languages.mathml=i.languages.markup,i.languages.svg=i.languages.markup,i.languages.xml=i.languages.extend("markup",{}),i.languages.ssml=i.languages.xml,i.languages.atom=i.languages.xml,i.languages.rss=i.languages.xml,function(g){var h=/(?:"(?:\\(?:\r\n|[\s\S])|[^"\\\r\n])*"|'(?:\\(?:\r\n|[\s\S])|[^'\\\r\n])*')/;g.languages.css={comment:/\/\*[\s\S]*?\*\//,atrule:{pattern:RegExp("@[\\w-](?:"+/[^;{\s"']|\s+(?!\s)/.source+"|"+h.source+")*?"+/(?:;|(?=\s*\{))/.source),inside:{rule:/^@[\w-]+/,"selector-function-argument":{pattern:/(\bselector\s*\(\s*(?![\s)]))(?:[^()\s]|\s+(?![\s)])|\((?:[^()]|\([^()]*\))*\))+(?=\s*\))/,lookbehind:!0,alias:"selector"},keyword:{pattern:/(^|[^\w-])(?:and|not|only|or)(?![\w-])/,lookbehind:!0}}},url:{pattern:RegExp("\\burl\\((?:"+h.source+"|"+/(?:[^\\\r\n()"']|\\[\s\S])*/.source+")\\)","i"),greedy:!0,inside:{function:/^url/i,punctuation:/^\(|\)$/,string:{pattern:RegExp("^"+h.source+"$"),alias:"url"}}},selector:{pattern:RegExp(`(^|[{}\\s])[^{}\\s](?:[^{};"'\\s]|\\s+(?![\\s{])|`+h.source+")*(?=\\s*\\{)"),lookbehind:!0},string:{pattern:h,greedy:!0},property:{pattern:/(^|[^-\w\xA0-\uFFFF])(?!\s)[-_a-z\xA0-\uFFFF](?:(?!\s)[-\w\xA0-\uFFFF])*(?=\s*:)/i,lookbehind:!0},important:/!important\b/i,function:{pattern:/(^|[^-a-z0-9])[-a-z0-9]+(?=\()/i,lookbehind:!0},punctuation:/[(){};:,]/},g.languages.css.atrule.inside.rest=g.languages.css;var y=g.languages.markup;y&&(y.tag.addInlined("style","css"),y.tag.addAttribute("style","css"));}(i),i.languages.clike={comment:[{pattern:/(^|[^\\])\/\*[\s\S]*?(?:\*\/|$)/,lookbehind:!0,greedy:!0},{pattern:/(^|[^\\:])\/\/.*/,lookbehind:!0,greedy:!0}],string:{pattern:/(["'])(?:\\(?:\r\n|[\s\S])|(?!\1)[^\\\r\n])*\1/,greedy:!0},"class-name":{pattern:/(\b(?:class|extends|implements|instanceof|interface|new|trait)\s+|\bcatch\s+\()[\w.\\]+/i,lookbehind:!0,inside:{punctuation:/[.\\]/}},keyword:/\b(?:break|catch|continue|do|else|finally|for|function|if|in|instanceof|new|null|return|throw|try|while)\b/,boolean:/\b(?:false|true)\b/,function:/\b\w+(?=\()/,number:/\b0x[\da-f]+\b|(?:\b\d+(?:\.\d*)?|\B\.\d+)(?:e[+-]?\d+)?/i,operator:/[<>]=?|[!=]=?=?|--?|\+\+?|&&?|\|\|?|[?*/~^%]/,punctuation:/[{}[\];(),.:]/},i.languages.javascript=i.languages.extend("clike",{"class-name":[i.languages.clike["class-name"],{pattern:/(^|[^$\w\xA0-\uFFFF])(?!\s)[_$A-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*(?=\.(?:constructor|prototype))/,lookbehind:!0}],keyword:[{pattern:/((?:^|\})\s*)catch\b/,lookbehind:!0},{pattern:/(^|[^.]|\.\.\.\s*)\b(?:as|assert(?=\s*\{)|async(?=\s*(?:function\b|\(|[$\w\xA0-\uFFFF]|$))|await|break|case|class|const|continue|debugger|default|delete|do|else|enum|export|extends|finally(?=\s*(?:\{|$))|for|from(?=\s*(?:['"]|$))|function|(?:get|set)(?=\s*(?:[#\[$\w\xA0-\uFFFF]|$))|if|implements|import|in|instanceof|interface|let|new|null|of|package|private|protected|public|return|static|super|switch|this|throw|try|typeof|undefined|var|void|while|with|yield)\b/,lookbehind:!0}],function:/#?(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*(?=\s*(?:\.\s*(?:apply|bind|call)\s*)?\()/,number:{pattern:RegExp(/(^|[^\w$])/.source+"(?:"+(/NaN|Infinity/.source+"|"+/0[bB][01]+(?:_[01]+)*n?/.source+"|"+/0[oO][0-7]+(?:_[0-7]+)*n?/.source+"|"+/0[xX][\dA-Fa-f]+(?:_[\dA-Fa-f]+)*n?/.source+"|"+/\d+(?:_\d+)*n/.source+"|"+/(?:\d+(?:_\d+)*(?:\.(?:\d+(?:_\d+)*)?)?|\.\d+(?:_\d+)*)(?:[Ee][+-]?\d+(?:_\d+)*)?/.source)+")"+/(?![\w$])/.source),lookbehind:!0},operator:/--|\+\+|\*\*=?|=>|&&=?|\|\|=?|[!=]==|<<=?|>>>?=?|[-+*/%&|^!=<>]=?|\.{3}|\?\?=?|\?\.?|[~:]/}),i.languages.javascript["class-name"][0].pattern=/(\b(?:class|extends|implements|instanceof|interface|new)\s+)[\w.\\]+/,i.languages.insertBefore("javascript","keyword",{regex:{pattern:RegExp(/((?:^|[^$\w\xA0-\uFFFF."'\])\s]|\b(?:return|yield))\s*)/.source+/\//.source+"(?:"+/(?:\[(?:[^\]\\\r\n]|\\.)*\]|\\.|[^/\\\[\r\n])+\/[dgimyus]{0,7}/.source+"|"+/(?:\[(?:[^[\]\\\r\n]|\\.|\[(?:[^[\]\\\r\n]|\\.|\[(?:[^[\]\\\r\n]|\\.)*\])*\])*\]|\\.|[^/\\\[\r\n])+\/[dgimyus]{0,7}v[dgimyus]{0,7}/.source+")"+/(?=(?:\s|\/\*(?:[^*]|\*(?!\/))*\*\/)*(?:$|[\r\n,.;:})\]]|\/\/))/.source),lookbehind:!0,greedy:!0,inside:{"regex-source":{pattern:/^(\/)[\s\S]+(?=\/[a-z]*$)/,lookbehind:!0,alias:"language-regex",inside:i.languages.regex},"regex-delimiter":/^\/|\/$/,"regex-flags":/^[a-z]+$/}},"function-variable":{pattern:/#?(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*(?=\s*[=:]\s*(?:async\s*)?(?:\bfunction\b|(?:\((?:[^()]|\([^()]*\))*\)|(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*)\s*=>))/,alias:"function"},parameter:[{pattern:/(function(?:\s+(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*)?\s*\(\s*)(?!\s)(?:[^()\s]|\s+(?![\s)])|\([^()]*\))+(?=\s*\))/,lookbehind:!0,inside:i.languages.javascript},{pattern:/(^|[^$\w\xA0-\uFFFF])(?!\s)[_$a-z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*(?=\s*=>)/i,lookbehind:!0,inside:i.languages.javascript},{pattern:/(\(\s*)(?!\s)(?:[^()\s]|\s+(?![\s)])|\([^()]*\))+(?=\s*\)\s*=>)/,lookbehind:!0,inside:i.languages.javascript},{pattern:/((?:\b|\s|^)(?!(?:as|async|await|break|case|catch|class|const|continue|debugger|default|delete|do|else|enum|export|extends|finally|for|from|function|get|if|implements|import|in|instanceof|interface|let|new|null|of|package|private|protected|public|return|set|static|super|switch|this|throw|try|typeof|undefined|var|void|while|with|yield)(?![$\w\xA0-\uFFFF]))(?:(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*\s*)\(\s*|\]\s*\(\s*)(?!\s)(?:[^()\s]|\s+(?![\s)])|\([^()]*\))+(?=\s*\)\s*\{)/,lookbehind:!0,inside:i.languages.javascript}],constant:/\b[A-Z](?:[A-Z_]|\dx?)*\b/}),i.languages.insertBefore("javascript","string",{hashbang:{pattern:/^#!.*/,greedy:!0,alias:"comment"},"template-string":{pattern:/`(?:\\[\s\S]|\$\{(?:[^{}]|\{(?:[^{}]|\{[^}]*\})*\})+\}|(?!\$\{)[^\\`])*`/,greedy:!0,inside:{"template-punctuation":{pattern:/^`|`$/,alias:"string"},interpolation:{pattern:/((?:^|[^\\])(?:\\{2})*)\$\{(?:[^{}]|\{(?:[^{}]|\{[^}]*\})*\})+\}/,lookbehind:!0,inside:{"interpolation-punctuation":{pattern:/^\$\{|\}$/,alias:"punctuation"},rest:i.languages.javascript}},string:/[\s\S]+/}},"string-property":{pattern:/((?:^|[,{])[ \t]*)(["'])(?:\\(?:\r\n|[\s\S])|(?!\2)[^\\\r\n])*\2(?=\s*:)/m,lookbehind:!0,greedy:!0,alias:"property"}}),i.languages.insertBefore("javascript","operator",{"literal-property":{pattern:/((?:^|[,{])[ \t]*)(?!\s)[_$a-zA-Z\xA0-\uFFFF](?:(?!\s)[$\w\xA0-\uFFFF])*(?=\s*:)/m,lookbehind:!0,alias:"property"}}),i.languages.markup&&(i.languages.markup.tag.addInlined("script","javascript"),i.languages.markup.tag.addAttribute(/on(?:abort|blur|change|click|composition(?:end|start|update)|dblclick|error|focus(?:in|out)?|key(?:down|up)|load|mouse(?:down|enter|leave|move|out|over|up)|reset|resize|scroll|select|slotchange|submit|unload|wheel)/.source,"javascript")),i.languages.js=i.languages.javascript,function(){if(typeof i>"u"||typeof document>"u")return;Element.prototype.matches||(Element.prototype.matches=Element.prototype.msMatchesSelector||Element.prototype.webkitMatchesSelector);var g="Loading…",h=function(p,c){return "✖ Error "+p+" while fetching file: "+c},y="✖ Error: File does not exist or is empty",F={js:"javascript",py:"python",rb:"ruby",ps1:"powershell",psm1:"powershell",sh:"bash",bat:"batch",h:"c",tex:"latex"},s="data-src-status",b="loading",E="loaded",C="failed",_="pre[data-src]:not(["+s+'="'+E+'"]):not(['+s+'="'+b+'"])';function S(p,c,f){var t=new XMLHttpRequest;t.open("GET",p,!0),t.onreadystatechange=function(){t.readyState==4&&(t.status<400&&t.responseText?c(t.responseText):t.status>=400?f(h(t.status,t.statusText)):f(y));},t.send(null);}function D(p){var c=/^\s*(\d+)\s*(?:(,)\s*(?:(\d+)\s*)?)?$/.exec(p||"");if(c){var f=Number(c[1]),t=c[2],e=c[3];return t?e?[f,Number(e)]:[f,void 0]:[f,f]}}i.hooks.add("before-highlightall",function(p){p.selector+=", "+_;}),i.hooks.add("before-sanity-check",function(p){var c=p.element;if(c.matches(_)){p.code="",c.setAttribute(s,b);var f=c.appendChild(document.createElement("CODE"));f.textContent=g;var t=c.getAttribute("data-src"),e=p.language;if(e==="none"){var a=(/\.(\w+)$/.exec(t)||[,"none"])[1];e=F[a]||a;}i.util.setLanguage(f,e),i.util.setLanguage(c,e);var n=i.plugins.autoloader;n&&n.loadLanguages(e),S(t,function(r){c.setAttribute(s,E);var l=D(c.getAttribute("data-range"));if(l){var o=r.split(/\r\n?|\n/g),u=l[0],d=l[1]==null?o.length:l[1];u<0&&(u+=o.length),u=Math.max(0,Math.min(u-1,o.length)),d<0&&(d+=o.length),d=Math.max(0,Math.min(d,o.length)),r=o.slice(u,d).join(`
`),c.hasAttribute("data-start")||c.setAttribute("data-start",String(u+1));}f.textContent=r,i.highlightElement(f);},function(r){c.setAttribute(s,C),f.textContent=r;});}}),i.plugins.fileHighlight={highlight:function(c){for(var f=(c||document).querySelectorAll(_),t=0,e;e=f[t++];)i.highlightElement(e);}};var P=!1;i.fileHighlight=function(){P||(console.warn("Prism.fileHighlight is deprecated. Use `Prism.plugins.fileHighlight.highlight` instead."),P=!0),i.plugins.fileHighlight.highlight.apply(this,arguments);};}();})(W);var V$1=W.exports;const te$2=Hr$1(V$1);Prism.languages.python={comment:{pattern:/(^|[^\\])#.*/,lookbehind:!0,greedy:!0},"string-interpolation":{pattern:/(?:f|fr|rf)(?:("""|''')[\s\S]*?\1|("|')(?:\\.|(?!\2)[^\\\r\n])*\2)/i,greedy:!0,inside:{interpolation:{pattern:/((?:^|[^{])(?:\{\{)*)\{(?!\{)(?:[^{}]|\{(?!\{)(?:[^{}]|\{(?!\{)(?:[^{}])+\})+\})+\}/,lookbehind:!0,inside:{"format-spec":{pattern:/(:)[^:(){}]+(?=\}$)/,lookbehind:!0},"conversion-option":{pattern:/![sra](?=[:}]$)/,alias:"punctuation"},rest:null}},string:/[\s\S]+/}},"triple-quoted-string":{pattern:/(?:[rub]|br|rb)?("""|''')[\s\S]*?\1/i,greedy:!0,alias:"string"},string:{pattern:/(?:[rub]|br|rb)?("|')(?:\\.|(?!\1)[^\\\r\n])*\1/i,greedy:!0},function:{pattern:/((?:^|\s)def[ \t]+)[a-zA-Z_]\w*(?=\s*\()/g,lookbehind:!0},"class-name":{pattern:/(\bclass\s+)\w+/i,lookbehind:!0},decorator:{pattern:/(^[\t ]*)@\w+(?:\.\w+)*/m,lookbehind:!0,alias:["annotation","punctuation"],inside:{punctuation:/\./}},keyword:/\b(?:_(?=\s*:)|and|as|assert|async|await|break|case|class|continue|def|del|elif|else|except|exec|finally|for|from|global|if|import|in|is|lambda|match|nonlocal|not|or|pass|print|raise|return|try|while|with|yield)\b/,builtin:/\b(?:__import__|abs|all|any|apply|ascii|basestring|bin|bool|buffer|bytearray|bytes|callable|chr|classmethod|cmp|coerce|compile|complex|delattr|dict|dir|divmod|enumerate|eval|execfile|file|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|intern|isinstance|issubclass|iter|len|list|locals|long|map|max|memoryview|min|next|object|oct|open|ord|pow|property|range|raw_input|reduce|reload|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|unichr|unicode|vars|xrange|zip)\b/,boolean:/\b(?:False|None|True)\b/,number:/\b0(?:b(?:_?[01])+|o(?:_?[0-7])+|x(?:_?[a-f0-9])+)\b|(?:\b\d+(?:_\d+)*(?:\.(?:\d+(?:_\d+)*)?)?|\B\.\d+(?:_\d+)*)(?:e[+-]?\d+(?:_\d+)*)?j?(?!\w)/i,operator:/[-+%=]=?|!=|:=|\*\*?=?|\/\/?=?|<[<=>]?|>[=>]?|[&|^~]/,punctuation:/[{}[\];(),.:]/};Prism.languages.python["string-interpolation"].inside.interpolation.inside.rest=Prism.languages.python;Prism.languages.py=Prism.languages.python;

function getDefaultExportFromCjs (x) {
	return x && x.__esModule && Object.prototype.hasOwnProperty.call(x, 'default') ? x['default'] : x;
}

var picocolors = {exports: {}};

var hasRequiredPicocolors;

function requirePicocolors () {
	if (hasRequiredPicocolors) return picocolors.exports;
	hasRequiredPicocolors = 1;
	let p = process || {}, argv = p.argv || [], env = p.env || {};
	let isColorSupported =
		!(!!env.NO_COLOR || argv.includes("--no-color")) &&
		(!!env.FORCE_COLOR || argv.includes("--color") || p.platform === "win32" || ((p.stdout || {}).isTTY && env.TERM !== "dumb") || !!env.CI);

	let formatter = (open, close, replace = open) =>
		input => {
			let string = "" + input, index = string.indexOf(close, open.length);
			return ~index ? open + replaceClose(string, close, replace, index) + close : open + string + close
		};

	let replaceClose = (string, close, replace, index) => {
		let result = "", cursor = 0;
		do {
			result += string.substring(cursor, index) + replace;
			cursor = index + close.length;
			index = string.indexOf(close, cursor);
		} while (~index)
		return result + string.substring(cursor)
	};

	let createColors = (enabled = isColorSupported) => {
		let f = enabled ? formatter : () => String;
		return {
			isColorSupported: enabled,
			reset: f("\x1b[0m", "\x1b[0m"),
			bold: f("\x1b[1m", "\x1b[22m", "\x1b[22m\x1b[1m"),
			dim: f("\x1b[2m", "\x1b[22m", "\x1b[22m\x1b[2m"),
			italic: f("\x1b[3m", "\x1b[23m"),
			underline: f("\x1b[4m", "\x1b[24m"),
			inverse: f("\x1b[7m", "\x1b[27m"),
			hidden: f("\x1b[8m", "\x1b[28m"),
			strikethrough: f("\x1b[9m", "\x1b[29m"),

			black: f("\x1b[30m", "\x1b[39m"),
			red: f("\x1b[31m", "\x1b[39m"),
			green: f("\x1b[32m", "\x1b[39m"),
			yellow: f("\x1b[33m", "\x1b[39m"),
			blue: f("\x1b[34m", "\x1b[39m"),
			magenta: f("\x1b[35m", "\x1b[39m"),
			cyan: f("\x1b[36m", "\x1b[39m"),
			white: f("\x1b[37m", "\x1b[39m"),
			gray: f("\x1b[90m", "\x1b[39m"),

			bgBlack: f("\x1b[40m", "\x1b[49m"),
			bgRed: f("\x1b[41m", "\x1b[49m"),
			bgGreen: f("\x1b[42m", "\x1b[49m"),
			bgYellow: f("\x1b[43m", "\x1b[49m"),
			bgBlue: f("\x1b[44m", "\x1b[49m"),
			bgMagenta: f("\x1b[45m", "\x1b[49m"),
			bgCyan: f("\x1b[46m", "\x1b[49m"),
			bgWhite: f("\x1b[47m", "\x1b[49m"),

			blackBright: f("\x1b[90m", "\x1b[39m"),
			redBright: f("\x1b[91m", "\x1b[39m"),
			greenBright: f("\x1b[92m", "\x1b[39m"),
			yellowBright: f("\x1b[93m", "\x1b[39m"),
			blueBright: f("\x1b[94m", "\x1b[39m"),
			magentaBright: f("\x1b[95m", "\x1b[39m"),
			cyanBright: f("\x1b[96m", "\x1b[39m"),
			whiteBright: f("\x1b[97m", "\x1b[39m"),

			bgBlackBright: f("\x1b[100m", "\x1b[49m"),
			bgRedBright: f("\x1b[101m", "\x1b[49m"),
			bgGreenBright: f("\x1b[102m", "\x1b[49m"),
			bgYellowBright: f("\x1b[103m", "\x1b[49m"),
			bgBlueBright: f("\x1b[104m", "\x1b[49m"),
			bgMagentaBright: f("\x1b[105m", "\x1b[49m"),
			bgCyanBright: f("\x1b[106m", "\x1b[49m"),
			bgWhiteBright: f("\x1b[107m", "\x1b[49m"),
		}
	};

	picocolors.exports = createColors();
	picocolors.exports.createColors = createColors;
	return picocolors.exports;
}

var tokenize;
var hasRequiredTokenize;

function requireTokenize () {
	if (hasRequiredTokenize) return tokenize;
	hasRequiredTokenize = 1;

	const SINGLE_QUOTE = "'".charCodeAt(0);
	const DOUBLE_QUOTE = '"'.charCodeAt(0);
	const BACKSLASH = '\\'.charCodeAt(0);
	const SLASH = '/'.charCodeAt(0);
	const NEWLINE = '\n'.charCodeAt(0);
	const SPACE = ' '.charCodeAt(0);
	const FEED = '\f'.charCodeAt(0);
	const TAB = '\t'.charCodeAt(0);
	const CR = '\r'.charCodeAt(0);
	const OPEN_SQUARE = '['.charCodeAt(0);
	const CLOSE_SQUARE = ']'.charCodeAt(0);
	const OPEN_PARENTHESES = '('.charCodeAt(0);
	const CLOSE_PARENTHESES = ')'.charCodeAt(0);
	const OPEN_CURLY = '{'.charCodeAt(0);
	const CLOSE_CURLY = '}'.charCodeAt(0);
	const SEMICOLON = ';'.charCodeAt(0);
	const ASTERISK = '*'.charCodeAt(0);
	const COLON = ':'.charCodeAt(0);
	const AT = '@'.charCodeAt(0);

	const RE_AT_END = /[\t\n\f\r "#'()/;[\\\]{}]/g;
	const RE_WORD_END = /[\t\n\f\r !"#'():;@[\\\]{}]|\/(?=\*)/g;
	const RE_BAD_BRACKET = /.[\r\n"'(/\\]/;
	const RE_HEX_ESCAPE = /[\da-f]/i;

	tokenize = function tokenizer(input, options = {}) {
	  let css = input.css.valueOf();
	  let ignore = options.ignoreErrors;

	  let code, next, quote, content, escape;
	  let escaped, escapePos, prev, n, currentToken;

	  let length = css.length;
	  let pos = 0;
	  let buffer = [];
	  let returned = [];

	  function position() {
	    return pos
	  }

	  function unclosed(what) {
	    throw input.error('Unclosed ' + what, pos)
	  }

	  function endOfFile() {
	    return returned.length === 0 && pos >= length
	  }

	  function nextToken(opts) {
	    if (returned.length) return returned.pop()
	    if (pos >= length) return

	    let ignoreUnclosed = opts ? opts.ignoreUnclosed : false;

	    code = css.charCodeAt(pos);

	    switch (code) {
	      case NEWLINE:
	      case SPACE:
	      case TAB:
	      case CR:
	      case FEED: {
	        next = pos;
	        do {
	          next += 1;
	          code = css.charCodeAt(next);
	        } while (
	          code === SPACE ||
	          code === NEWLINE ||
	          code === TAB ||
	          code === CR ||
	          code === FEED
	        )

	        currentToken = ['space', css.slice(pos, next)];
	        pos = next - 1;
	        break
	      }

	      case OPEN_SQUARE:
	      case CLOSE_SQUARE:
	      case OPEN_CURLY:
	      case CLOSE_CURLY:
	      case COLON:
	      case SEMICOLON:
	      case CLOSE_PARENTHESES: {
	        let controlChar = String.fromCharCode(code);
	        currentToken = [controlChar, controlChar, pos];
	        break
	      }

	      case OPEN_PARENTHESES: {
	        prev = buffer.length ? buffer.pop()[1] : '';
	        n = css.charCodeAt(pos + 1);
	        if (
	          prev === 'url' &&
	          n !== SINGLE_QUOTE &&
	          n !== DOUBLE_QUOTE &&
	          n !== SPACE &&
	          n !== NEWLINE &&
	          n !== TAB &&
	          n !== FEED &&
	          n !== CR
	        ) {
	          next = pos;
	          do {
	            escaped = false;
	            next = css.indexOf(')', next + 1);
	            if (next === -1) {
	              if (ignore || ignoreUnclosed) {
	                next = pos;
	                break
	              } else {
	                unclosed('bracket');
	              }
	            }
	            escapePos = next;
	            while (css.charCodeAt(escapePos - 1) === BACKSLASH) {
	              escapePos -= 1;
	              escaped = !escaped;
	            }
	          } while (escaped)

	          currentToken = ['brackets', css.slice(pos, next + 1), pos, next];

	          pos = next;
	        } else {
	          next = css.indexOf(')', pos + 1);
	          content = css.slice(pos, next + 1);

	          if (next === -1 || RE_BAD_BRACKET.test(content)) {
	            currentToken = ['(', '(', pos];
	          } else {
	            currentToken = ['brackets', content, pos, next];
	            pos = next;
	          }
	        }

	        break
	      }

	      case SINGLE_QUOTE:
	      case DOUBLE_QUOTE: {
	        quote = code === SINGLE_QUOTE ? "'" : '"';
	        next = pos;
	        do {
	          escaped = false;
	          next = css.indexOf(quote, next + 1);
	          if (next === -1) {
	            if (ignore || ignoreUnclosed) {
	              next = pos + 1;
	              break
	            } else {
	              unclosed('string');
	            }
	          }
	          escapePos = next;
	          while (css.charCodeAt(escapePos - 1) === BACKSLASH) {
	            escapePos -= 1;
	            escaped = !escaped;
	          }
	        } while (escaped)

	        currentToken = ['string', css.slice(pos, next + 1), pos, next];
	        pos = next;
	        break
	      }

	      case AT: {
	        RE_AT_END.lastIndex = pos + 1;
	        RE_AT_END.test(css);
	        if (RE_AT_END.lastIndex === 0) {
	          next = css.length - 1;
	        } else {
	          next = RE_AT_END.lastIndex - 2;
	        }

	        currentToken = ['at-word', css.slice(pos, next + 1), pos, next];

	        pos = next;
	        break
	      }

	      case BACKSLASH: {
	        next = pos;
	        escape = true;
	        while (css.charCodeAt(next + 1) === BACKSLASH) {
	          next += 1;
	          escape = !escape;
	        }
	        code = css.charCodeAt(next + 1);
	        if (
	          escape &&
	          code !== SLASH &&
	          code !== SPACE &&
	          code !== NEWLINE &&
	          code !== TAB &&
	          code !== CR &&
	          code !== FEED
	        ) {
	          next += 1;
	          if (RE_HEX_ESCAPE.test(css.charAt(next))) {
	            while (RE_HEX_ESCAPE.test(css.charAt(next + 1))) {
	              next += 1;
	            }
	            if (css.charCodeAt(next + 1) === SPACE) {
	              next += 1;
	            }
	          }
	        }

	        currentToken = ['word', css.slice(pos, next + 1), pos, next];

	        pos = next;
	        break
	      }

	      default: {
	        if (code === SLASH && css.charCodeAt(pos + 1) === ASTERISK) {
	          next = css.indexOf('*/', pos + 2) + 1;
	          if (next === 0) {
	            if (ignore || ignoreUnclosed) {
	              next = css.length;
	            } else {
	              unclosed('comment');
	            }
	          }

	          currentToken = ['comment', css.slice(pos, next + 1), pos, next];
	          pos = next;
	        } else {
	          RE_WORD_END.lastIndex = pos + 1;
	          RE_WORD_END.test(css);
	          if (RE_WORD_END.lastIndex === 0) {
	            next = css.length - 1;
	          } else {
	            next = RE_WORD_END.lastIndex - 2;
	          }

	          currentToken = ['word', css.slice(pos, next + 1), pos, next];
	          buffer.push(currentToken);
	          pos = next;
	        }

	        break
	      }
	    }

	    pos++;
	    return currentToken
	  }

	  function back(token) {
	    returned.push(token);
	  }

	  return {
	    back,
	    endOfFile,
	    nextToken,
	    position
	  }
	};
	return tokenize;
}

var terminalHighlight_1;
var hasRequiredTerminalHighlight;

function requireTerminalHighlight () {
	if (hasRequiredTerminalHighlight) return terminalHighlight_1;
	hasRequiredTerminalHighlight = 1;

	let pico = requirePicocolors();

	let tokenizer = requireTokenize();

	let Input;

	function registerInput(dependant) {
	  Input = dependant;
	}

	const HIGHLIGHT_THEME = {
	  ';': pico.yellow,
	  ':': pico.yellow,
	  '(': pico.cyan,
	  ')': pico.cyan,
	  '[': pico.yellow,
	  ']': pico.yellow,
	  '{': pico.yellow,
	  '}': pico.yellow,
	  'at-word': pico.cyan,
	  'brackets': pico.cyan,
	  'call': pico.cyan,
	  'class': pico.yellow,
	  'comment': pico.gray,
	  'hash': pico.magenta,
	  'string': pico.green
	};

	function getTokenType([type, value], processor) {
	  if (type === 'word') {
	    if (value[0] === '.') {
	      return 'class'
	    }
	    if (value[0] === '#') {
	      return 'hash'
	    }
	  }

	  if (!processor.endOfFile()) {
	    let next = processor.nextToken();
	    processor.back(next);
	    if (next[0] === 'brackets' || next[0] === '(') return 'call'
	  }

	  return type
	}

	function terminalHighlight(css) {
	  let processor = tokenizer(new Input(css), { ignoreErrors: true });
	  let result = '';
	  while (!processor.endOfFile()) {
	    let token = processor.nextToken();
	    let color = HIGHLIGHT_THEME[getTokenType(token, processor)];
	    if (color) {
	      result += token[1]
	        .split(/\r?\n/)
	        .map(i => color(i))
	        .join('\n');
	    } else {
	      result += token[1];
	    }
	  }
	  return result
	}

	terminalHighlight.registerInput = registerInput;

	terminalHighlight_1 = terminalHighlight;
	return terminalHighlight_1;
}

var cssSyntaxError;
var hasRequiredCssSyntaxError;

function requireCssSyntaxError () {
	if (hasRequiredCssSyntaxError) return cssSyntaxError;
	hasRequiredCssSyntaxError = 1;

	let pico = requirePicocolors();

	let terminalHighlight = requireTerminalHighlight();

	class CssSyntaxError extends Error {
	  constructor(message, line, column, source, file, plugin) {
	    super(message);
	    this.name = 'CssSyntaxError';
	    this.reason = message;

	    if (file) {
	      this.file = file;
	    }
	    if (source) {
	      this.source = source;
	    }
	    if (plugin) {
	      this.plugin = plugin;
	    }
	    if (typeof line !== 'undefined' && typeof column !== 'undefined') {
	      if (typeof line === 'number') {
	        this.line = line;
	        this.column = column;
	      } else {
	        this.line = line.line;
	        this.column = line.column;
	        this.endLine = column.line;
	        this.endColumn = column.column;
	      }
	    }

	    this.setMessage();

	    if (Error.captureStackTrace) {
	      Error.captureStackTrace(this, CssSyntaxError);
	    }
	  }

	  setMessage() {
	    this.message = this.plugin ? this.plugin + ': ' : '';
	    this.message += this.file ? this.file : '<css input>';
	    if (typeof this.line !== 'undefined') {
	      this.message += ':' + this.line + ':' + this.column;
	    }
	    this.message += ': ' + this.reason;
	  }

	  showSourceCode(color) {
	    if (!this.source) return ''

	    let css = this.source;
	    if (color == null) color = pico.isColorSupported;
	    if (terminalHighlight) {
	      if (color) css = terminalHighlight(css);
	    }

	    let lines = css.split(/\r?\n/);
	    let start = Math.max(this.line - 3, 0);
	    let end = Math.min(this.line + 2, lines.length);

	    let maxWidth = String(end).length;

	    let mark, aside;
	    if (color) {
	      let { bold, gray, red } = pico.createColors(true);
	      mark = text => bold(red(text));
	      aside = text => gray(text);
	    } else {
	      mark = aside = str => str;
	    }

	    return lines
	      .slice(start, end)
	      .map((line, index) => {
	        let number = start + 1 + index;
	        let gutter = ' ' + (' ' + number).slice(-maxWidth) + ' | ';
	        if (number === this.line) {
	          let spacing =
	            aside(gutter.replace(/\d/g, ' ')) +
	            line.slice(0, this.column - 1).replace(/[^\t]/g, ' ');
	          return mark('>') + aside(gutter) + line + '\n ' + spacing + mark('^')
	        }
	        return ' ' + aside(gutter) + line
	      })
	      .join('\n')
	  }

	  toString() {
	    let code = this.showSourceCode();
	    if (code) {
	      code = '\n\n' + code + '\n';
	    }
	    return this.name + ': ' + this.message + code
	  }
	}

	cssSyntaxError = CssSyntaxError;
	CssSyntaxError.default = CssSyntaxError;
	return cssSyntaxError;
}

var symbols = {};

var hasRequiredSymbols;

function requireSymbols () {
	if (hasRequiredSymbols) return symbols;
	hasRequiredSymbols = 1;

	symbols.isClean = Symbol('isClean');

	symbols.my = Symbol('my');
	return symbols;
}

var stringifier;
var hasRequiredStringifier;

function requireStringifier () {
	if (hasRequiredStringifier) return stringifier;
	hasRequiredStringifier = 1;

	const DEFAULT_RAW = {
	  after: '\n',
	  beforeClose: '\n',
	  beforeComment: '\n',
	  beforeDecl: '\n',
	  beforeOpen: ' ',
	  beforeRule: '\n',
	  colon: ': ',
	  commentLeft: ' ',
	  commentRight: ' ',
	  emptyBody: '',
	  indent: '    ',
	  semicolon: false
	};

	function capitalize(str) {
	  return str[0].toUpperCase() + str.slice(1)
	}

	class Stringifier {
	  constructor(builder) {
	    this.builder = builder;
	  }

	  atrule(node, semicolon) {
	    let name = '@' + node.name;
	    let params = node.params ? this.rawValue(node, 'params') : '';

	    if (typeof node.raws.afterName !== 'undefined') {
	      name += node.raws.afterName;
	    } else if (params) {
	      name += ' ';
	    }

	    if (node.nodes) {
	      this.block(node, name + params);
	    } else {
	      let end = (node.raws.between || '') + (semicolon ? ';' : '');
	      this.builder(name + params + end, node);
	    }
	  }

	  beforeAfter(node, detect) {
	    let value;
	    if (node.type === 'decl') {
	      value = this.raw(node, null, 'beforeDecl');
	    } else if (node.type === 'comment') {
	      value = this.raw(node, null, 'beforeComment');
	    } else if (detect === 'before') {
	      value = this.raw(node, null, 'beforeRule');
	    } else {
	      value = this.raw(node, null, 'beforeClose');
	    }

	    let buf = node.parent;
	    let depth = 0;
	    while (buf && buf.type !== 'root') {
	      depth += 1;
	      buf = buf.parent;
	    }

	    if (value.includes('\n')) {
	      let indent = this.raw(node, null, 'indent');
	      if (indent.length) {
	        for (let step = 0; step < depth; step++) value += indent;
	      }
	    }

	    return value
	  }

	  block(node, start) {
	    let between = this.raw(node, 'between', 'beforeOpen');
	    this.builder(start + between + '{', node, 'start');

	    let after;
	    if (node.nodes && node.nodes.length) {
	      this.body(node);
	      after = this.raw(node, 'after');
	    } else {
	      after = this.raw(node, 'after', 'emptyBody');
	    }

	    if (after) this.builder(after);
	    this.builder('}', node, 'end');
	  }

	  body(node) {
	    let last = node.nodes.length - 1;
	    while (last > 0) {
	      if (node.nodes[last].type !== 'comment') break
	      last -= 1;
	    }

	    let semicolon = this.raw(node, 'semicolon');
	    for (let i = 0; i < node.nodes.length; i++) {
	      let child = node.nodes[i];
	      let before = this.raw(child, 'before');
	      if (before) this.builder(before);
	      this.stringify(child, last !== i || semicolon);
	    }
	  }

	  comment(node) {
	    let left = this.raw(node, 'left', 'commentLeft');
	    let right = this.raw(node, 'right', 'commentRight');
	    this.builder('/*' + left + node.text + right + '*/', node);
	  }

	  decl(node, semicolon) {
	    let between = this.raw(node, 'between', 'colon');
	    let string = node.prop + between + this.rawValue(node, 'value');

	    if (node.important) {
	      string += node.raws.important || ' !important';
	    }

	    if (semicolon) string += ';';
	    this.builder(string, node);
	  }

	  document(node) {
	    this.body(node);
	  }

	  raw(node, own, detect) {
	    let value;
	    if (!detect) detect = own;

	    // Already had
	    if (own) {
	      value = node.raws[own];
	      if (typeof value !== 'undefined') return value
	    }

	    let parent = node.parent;

	    if (detect === 'before') {
	      // Hack for first rule in CSS
	      if (!parent || (parent.type === 'root' && parent.first === node)) {
	        return ''
	      }

	      // `root` nodes in `document` should use only their own raws
	      if (parent && parent.type === 'document') {
	        return ''
	      }
	    }

	    // Floating child without parent
	    if (!parent) return DEFAULT_RAW[detect]

	    // Detect style by other nodes
	    let root = node.root();
	    if (!root.rawCache) root.rawCache = {};
	    if (typeof root.rawCache[detect] !== 'undefined') {
	      return root.rawCache[detect]
	    }

	    if (detect === 'before' || detect === 'after') {
	      return this.beforeAfter(node, detect)
	    } else {
	      let method = 'raw' + capitalize(detect);
	      if (this[method]) {
	        value = this[method](root, node);
	      } else {
	        root.walk(i => {
	          value = i.raws[own];
	          if (typeof value !== 'undefined') return false
	        });
	      }
	    }

	    if (typeof value === 'undefined') value = DEFAULT_RAW[detect];

	    root.rawCache[detect] = value;
	    return value
	  }

	  rawBeforeClose(root) {
	    let value;
	    root.walk(i => {
	      if (i.nodes && i.nodes.length > 0) {
	        if (typeof i.raws.after !== 'undefined') {
	          value = i.raws.after;
	          if (value.includes('\n')) {
	            value = value.replace(/[^\n]+$/, '');
	          }
	          return false
	        }
	      }
	    });
	    if (value) value = value.replace(/\S/g, '');
	    return value
	  }

	  rawBeforeComment(root, node) {
	    let value;
	    root.walkComments(i => {
	      if (typeof i.raws.before !== 'undefined') {
	        value = i.raws.before;
	        if (value.includes('\n')) {
	          value = value.replace(/[^\n]+$/, '');
	        }
	        return false
	      }
	    });
	    if (typeof value === 'undefined') {
	      value = this.raw(node, null, 'beforeDecl');
	    } else if (value) {
	      value = value.replace(/\S/g, '');
	    }
	    return value
	  }

	  rawBeforeDecl(root, node) {
	    let value;
	    root.walkDecls(i => {
	      if (typeof i.raws.before !== 'undefined') {
	        value = i.raws.before;
	        if (value.includes('\n')) {
	          value = value.replace(/[^\n]+$/, '');
	        }
	        return false
	      }
	    });
	    if (typeof value === 'undefined') {
	      value = this.raw(node, null, 'beforeRule');
	    } else if (value) {
	      value = value.replace(/\S/g, '');
	    }
	    return value
	  }

	  rawBeforeOpen(root) {
	    let value;
	    root.walk(i => {
	      if (i.type !== 'decl') {
	        value = i.raws.between;
	        if (typeof value !== 'undefined') return false
	      }
	    });
	    return value
	  }

	  rawBeforeRule(root) {
	    let value;
	    root.walk(i => {
	      if (i.nodes && (i.parent !== root || root.first !== i)) {
	        if (typeof i.raws.before !== 'undefined') {
	          value = i.raws.before;
	          if (value.includes('\n')) {
	            value = value.replace(/[^\n]+$/, '');
	          }
	          return false
	        }
	      }
	    });
	    if (value) value = value.replace(/\S/g, '');
	    return value
	  }

	  rawColon(root) {
	    let value;
	    root.walkDecls(i => {
	      if (typeof i.raws.between !== 'undefined') {
	        value = i.raws.between.replace(/[^\s:]/g, '');
	        return false
	      }
	    });
	    return value
	  }

	  rawEmptyBody(root) {
	    let value;
	    root.walk(i => {
	      if (i.nodes && i.nodes.length === 0) {
	        value = i.raws.after;
	        if (typeof value !== 'undefined') return false
	      }
	    });
	    return value
	  }

	  rawIndent(root) {
	    if (root.raws.indent) return root.raws.indent
	    let value;
	    root.walk(i => {
	      let p = i.parent;
	      if (p && p !== root && p.parent && p.parent === root) {
	        if (typeof i.raws.before !== 'undefined') {
	          let parts = i.raws.before.split('\n');
	          value = parts[parts.length - 1];
	          value = value.replace(/\S/g, '');
	          return false
	        }
	      }
	    });
	    return value
	  }

	  rawSemicolon(root) {
	    let value;
	    root.walk(i => {
	      if (i.nodes && i.nodes.length && i.last.type === 'decl') {
	        value = i.raws.semicolon;
	        if (typeof value !== 'undefined') return false
	      }
	    });
	    return value
	  }

	  rawValue(node, prop) {
	    let value = node[prop];
	    let raw = node.raws[prop];
	    if (raw && raw.value === value) {
	      return raw.raw
	    }

	    return value
	  }

	  root(node) {
	    this.body(node);
	    if (node.raws.after) this.builder(node.raws.after);
	  }

	  rule(node) {
	    this.block(node, this.rawValue(node, 'selector'));
	    if (node.raws.ownSemicolon) {
	      this.builder(node.raws.ownSemicolon, node, 'end');
	    }
	  }

	  stringify(node, semicolon) {
	    /* c8 ignore start */
	    if (!this[node.type]) {
	      throw new Error(
	        'Unknown AST node type ' +
	          node.type +
	          '. ' +
	          'Maybe you need to change PostCSS stringifier.'
	      )
	    }
	    /* c8 ignore stop */
	    this[node.type](node, semicolon);
	  }
	}

	stringifier = Stringifier;
	Stringifier.default = Stringifier;
	return stringifier;
}

var stringify_1;
var hasRequiredStringify;

function requireStringify () {
	if (hasRequiredStringify) return stringify_1;
	hasRequiredStringify = 1;

	let Stringifier = requireStringifier();

	function stringify(node, builder) {
	  let str = new Stringifier(builder);
	  str.stringify(node);
	}

	stringify_1 = stringify;
	stringify.default = stringify;
	return stringify_1;
}

var node;
var hasRequiredNode;

function requireNode () {
	if (hasRequiredNode) return node;
	hasRequiredNode = 1;

	let { isClean, my } = requireSymbols();
	let CssSyntaxError = requireCssSyntaxError();
	let Stringifier = requireStringifier();
	let stringify = requireStringify();

	function cloneNode(obj, parent) {
	  let cloned = new obj.constructor();

	  for (let i in obj) {
	    if (!Object.prototype.hasOwnProperty.call(obj, i)) {
	      /* c8 ignore next 2 */
	      continue
	    }
	    if (i === 'proxyCache') continue
	    let value = obj[i];
	    let type = typeof value;

	    if (i === 'parent' && type === 'object') {
	      if (parent) cloned[i] = parent;
	    } else if (i === 'source') {
	      cloned[i] = value;
	    } else if (Array.isArray(value)) {
	      cloned[i] = value.map(j => cloneNode(j, cloned));
	    } else {
	      if (type === 'object' && value !== null) value = cloneNode(value);
	      cloned[i] = value;
	    }
	  }

	  return cloned
	}

	class Node {
	  constructor(defaults = {}) {
	    this.raws = {};
	    this[isClean] = false;
	    this[my] = true;

	    for (let name in defaults) {
	      if (name === 'nodes') {
	        this.nodes = [];
	        for (let node of defaults[name]) {
	          if (typeof node.clone === 'function') {
	            this.append(node.clone());
	          } else {
	            this.append(node);
	          }
	        }
	      } else {
	        this[name] = defaults[name];
	      }
	    }
	  }

	  addToError(error) {
	    error.postcssNode = this;
	    if (error.stack && this.source && /\n\s{4}at /.test(error.stack)) {
	      let s = this.source;
	      error.stack = error.stack.replace(
	        /\n\s{4}at /,
	        `$&${s.input.from}:${s.start.line}:${s.start.column}$&`
	      );
	    }
	    return error
	  }

	  after(add) {
	    this.parent.insertAfter(this, add);
	    return this
	  }

	  assign(overrides = {}) {
	    for (let name in overrides) {
	      this[name] = overrides[name];
	    }
	    return this
	  }

	  before(add) {
	    this.parent.insertBefore(this, add);
	    return this
	  }

	  cleanRaws(keepBetween) {
	    delete this.raws.before;
	    delete this.raws.after;
	    if (!keepBetween) delete this.raws.between;
	  }

	  clone(overrides = {}) {
	    let cloned = cloneNode(this);
	    for (let name in overrides) {
	      cloned[name] = overrides[name];
	    }
	    return cloned
	  }

	  cloneAfter(overrides = {}) {
	    let cloned = this.clone(overrides);
	    this.parent.insertAfter(this, cloned);
	    return cloned
	  }

	  cloneBefore(overrides = {}) {
	    let cloned = this.clone(overrides);
	    this.parent.insertBefore(this, cloned);
	    return cloned
	  }

	  error(message, opts = {}) {
	    if (this.source) {
	      let { end, start } = this.rangeBy(opts);
	      return this.source.input.error(
	        message,
	        { column: start.column, line: start.line },
	        { column: end.column, line: end.line },
	        opts
	      )
	    }
	    return new CssSyntaxError(message)
	  }

	  getProxyProcessor() {
	    return {
	      get(node, prop) {
	        if (prop === 'proxyOf') {
	          return node
	        } else if (prop === 'root') {
	          return () => node.root().toProxy()
	        } else {
	          return node[prop]
	        }
	      },

	      set(node, prop, value) {
	        if (node[prop] === value) return true
	        node[prop] = value;
	        if (
	          prop === 'prop' ||
	          prop === 'value' ||
	          prop === 'name' ||
	          prop === 'params' ||
	          prop === 'important' ||
	          /* c8 ignore next */
	          prop === 'text'
	        ) {
	          node.markDirty();
	        }
	        return true
	      }
	    }
	  }

	  markDirty() {
	    if (this[isClean]) {
	      this[isClean] = false;
	      let next = this;
	      while ((next = next.parent)) {
	        next[isClean] = false;
	      }
	    }
	  }

	  next() {
	    if (!this.parent) return undefined
	    let index = this.parent.index(this);
	    return this.parent.nodes[index + 1]
	  }

	  positionBy(opts, stringRepresentation) {
	    let pos = this.source.start;
	    if (opts.index) {
	      pos = this.positionInside(opts.index, stringRepresentation);
	    } else if (opts.word) {
	      stringRepresentation = this.toString();
	      let index = stringRepresentation.indexOf(opts.word);
	      if (index !== -1) pos = this.positionInside(index, stringRepresentation);
	    }
	    return pos
	  }

	  positionInside(index, stringRepresentation) {
	    let string = stringRepresentation || this.toString();
	    let column = this.source.start.column;
	    let line = this.source.start.line;

	    for (let i = 0; i < index; i++) {
	      if (string[i] === '\n') {
	        column = 1;
	        line += 1;
	      } else {
	        column += 1;
	      }
	    }

	    return { column, line }
	  }

	  prev() {
	    if (!this.parent) return undefined
	    let index = this.parent.index(this);
	    return this.parent.nodes[index - 1]
	  }

	  rangeBy(opts) {
	    let start = {
	      column: this.source.start.column,
	      line: this.source.start.line
	    };
	    let end = this.source.end
	      ? {
	        column: this.source.end.column + 1,
	        line: this.source.end.line
	      }
	      : {
	        column: start.column + 1,
	        line: start.line
	      };

	    if (opts.word) {
	      let stringRepresentation = this.toString();
	      let index = stringRepresentation.indexOf(opts.word);
	      if (index !== -1) {
	        start = this.positionInside(index, stringRepresentation);
	        end = this.positionInside(index + opts.word.length, stringRepresentation);
	      }
	    } else {
	      if (opts.start) {
	        start = {
	          column: opts.start.column,
	          line: opts.start.line
	        };
	      } else if (opts.index) {
	        start = this.positionInside(opts.index);
	      }

	      if (opts.end) {
	        end = {
	          column: opts.end.column,
	          line: opts.end.line
	        };
	      } else if (typeof opts.endIndex === 'number') {
	        end = this.positionInside(opts.endIndex);
	      } else if (opts.index) {
	        end = this.positionInside(opts.index + 1);
	      }
	    }

	    if (
	      end.line < start.line ||
	      (end.line === start.line && end.column <= start.column)
	    ) {
	      end = { column: start.column + 1, line: start.line };
	    }

	    return { end, start }
	  }

	  raw(prop, defaultType) {
	    let str = new Stringifier();
	    return str.raw(this, prop, defaultType)
	  }

	  remove() {
	    if (this.parent) {
	      this.parent.removeChild(this);
	    }
	    this.parent = undefined;
	    return this
	  }

	  replaceWith(...nodes) {
	    if (this.parent) {
	      let bookmark = this;
	      let foundSelf = false;
	      for (let node of nodes) {
	        if (node === this) {
	          foundSelf = true;
	        } else if (foundSelf) {
	          this.parent.insertAfter(bookmark, node);
	          bookmark = node;
	        } else {
	          this.parent.insertBefore(bookmark, node);
	        }
	      }

	      if (!foundSelf) {
	        this.remove();
	      }
	    }

	    return this
	  }

	  root() {
	    let result = this;
	    while (result.parent && result.parent.type !== 'document') {
	      result = result.parent;
	    }
	    return result
	  }

	  toJSON(_, inputs) {
	    let fixed = {};
	    let emitInputs = inputs == null;
	    inputs = inputs || new Map();
	    let inputsNextIndex = 0;

	    for (let name in this) {
	      if (!Object.prototype.hasOwnProperty.call(this, name)) {
	        /* c8 ignore next 2 */
	        continue
	      }
	      if (name === 'parent' || name === 'proxyCache') continue
	      let value = this[name];

	      if (Array.isArray(value)) {
	        fixed[name] = value.map(i => {
	          if (typeof i === 'object' && i.toJSON) {
	            return i.toJSON(null, inputs)
	          } else {
	            return i
	          }
	        });
	      } else if (typeof value === 'object' && value.toJSON) {
	        fixed[name] = value.toJSON(null, inputs);
	      } else if (name === 'source') {
	        let inputId = inputs.get(value.input);
	        if (inputId == null) {
	          inputId = inputsNextIndex;
	          inputs.set(value.input, inputsNextIndex);
	          inputsNextIndex++;
	        }
	        fixed[name] = {
	          end: value.end,
	          inputId,
	          start: value.start
	        };
	      } else {
	        fixed[name] = value;
	      }
	    }

	    if (emitInputs) {
	      fixed.inputs = [...inputs.keys()].map(input => input.toJSON());
	    }

	    return fixed
	  }

	  toProxy() {
	    if (!this.proxyCache) {
	      this.proxyCache = new Proxy(this, this.getProxyProcessor());
	    }
	    return this.proxyCache
	  }

	  toString(stringifier = stringify) {
	    if (stringifier.stringify) stringifier = stringifier.stringify;
	    let result = '';
	    stringifier(this, i => {
	      result += i;
	    });
	    return result
	  }

	  warn(result, text, opts) {
	    let data = { node: this };
	    for (let i in opts) data[i] = opts[i];
	    return result.warn(text, data)
	  }

	  get proxyOf() {
	    return this
	  }
	}

	node = Node;
	Node.default = Node;
	return node;
}

var declaration;
var hasRequiredDeclaration;

function requireDeclaration () {
	if (hasRequiredDeclaration) return declaration;
	hasRequiredDeclaration = 1;

	let Node = requireNode();

	class Declaration extends Node {
	  constructor(defaults) {
	    if (
	      defaults &&
	      typeof defaults.value !== 'undefined' &&
	      typeof defaults.value !== 'string'
	    ) {
	      defaults = { ...defaults, value: String(defaults.value) };
	    }
	    super(defaults);
	    this.type = 'decl';
	  }

	  get variable() {
	    return this.prop.startsWith('--') || this.prop[0] === '$'
	  }
	}

	declaration = Declaration;
	Declaration.default = Declaration;
	return declaration;
}

var sourceMap = {};

var sourceMapGenerator = {};

var base64Vlq = {};

var base64 = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredBase64;

function requireBase64 () {
	if (hasRequiredBase64) return base64;
	hasRequiredBase64 = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var intToCharMap = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'.split('');

	/**
	 * Encode an integer in the range of 0 to 63 to a single base 64 digit.
	 */
	base64.encode = function (number) {
	  if (0 <= number && number < intToCharMap.length) {
	    return intToCharMap[number];
	  }
	  throw new TypeError("Must be between 0 and 63: " + number);
	};

	/**
	 * Decode a single base 64 character code digit to an integer. Returns -1 on
	 * failure.
	 */
	base64.decode = function (charCode) {
	  var bigA = 65;     // 'A'
	  var bigZ = 90;     // 'Z'

	  var littleA = 97;  // 'a'
	  var littleZ = 122; // 'z'

	  var zero = 48;     // '0'
	  var nine = 57;     // '9'

	  var plus = 43;     // '+'
	  var slash = 47;    // '/'

	  var littleOffset = 26;
	  var numberOffset = 52;

	  // 0 - 25: ABCDEFGHIJKLMNOPQRSTUVWXYZ
	  if (bigA <= charCode && charCode <= bigZ) {
	    return (charCode - bigA);
	  }

	  // 26 - 51: abcdefghijklmnopqrstuvwxyz
	  if (littleA <= charCode && charCode <= littleZ) {
	    return (charCode - littleA + littleOffset);
	  }

	  // 52 - 61: 0123456789
	  if (zero <= charCode && charCode <= nine) {
	    return (charCode - zero + numberOffset);
	  }

	  // 62: +
	  if (charCode == plus) {
	    return 62;
	  }

	  // 63: /
	  if (charCode == slash) {
	    return 63;
	  }

	  // Invalid base64 digit.
	  return -1;
	};
	return base64;
}

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredBase64Vlq;

function requireBase64Vlq () {
	if (hasRequiredBase64Vlq) return base64Vlq;
	hasRequiredBase64Vlq = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 *
	 * Based on the Base 64 VLQ implementation in Closure Compiler:
	 * https://code.google.com/p/closure-compiler/source/browse/trunk/src/com/google/debugging/sourcemap/Base64VLQ.java
	 *
	 * Copyright 2011 The Closure Compiler Authors. All rights reserved.
	 * Redistribution and use in source and binary forms, with or without
	 * modification, are permitted provided that the following conditions are
	 * met:
	 *
	 *  * Redistributions of source code must retain the above copyright
	 *    notice, this list of conditions and the following disclaimer.
	 *  * Redistributions in binary form must reproduce the above
	 *    copyright notice, this list of conditions and the following
	 *    disclaimer in the documentation and/or other materials provided
	 *    with the distribution.
	 *  * Neither the name of Google Inc. nor the names of its
	 *    contributors may be used to endorse or promote products derived
	 *    from this software without specific prior written permission.
	 *
	 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
	 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
	 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
	 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
	 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
	 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
	 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
	 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
	 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	 */

	var base64 = requireBase64();

	// A single base 64 digit can contain 6 bits of data. For the base 64 variable
	// length quantities we use in the source map spec, the first bit is the sign,
	// the next four bits are the actual value, and the 6th bit is the
	// continuation bit. The continuation bit tells us whether there are more
	// digits in this value following this digit.
	//
	//   Continuation
	//   |    Sign
	//   |    |
	//   V    V
	//   101011

	var VLQ_BASE_SHIFT = 5;

	// binary: 100000
	var VLQ_BASE = 1 << VLQ_BASE_SHIFT;

	// binary: 011111
	var VLQ_BASE_MASK = VLQ_BASE - 1;

	// binary: 100000
	var VLQ_CONTINUATION_BIT = VLQ_BASE;

	/**
	 * Converts from a two-complement value to a value where the sign bit is
	 * placed in the least significant bit.  For example, as decimals:
	 *   1 becomes 2 (10 binary), -1 becomes 3 (11 binary)
	 *   2 becomes 4 (100 binary), -2 becomes 5 (101 binary)
	 */
	function toVLQSigned(aValue) {
	  return aValue < 0
	    ? ((-aValue) << 1) + 1
	    : (aValue << 1) + 0;
	}

	/**
	 * Converts to a two-complement value from a value where the sign bit is
	 * placed in the least significant bit.  For example, as decimals:
	 *   2 (10 binary) becomes 1, 3 (11 binary) becomes -1
	 *   4 (100 binary) becomes 2, 5 (101 binary) becomes -2
	 */
	function fromVLQSigned(aValue) {
	  var isNegative = (aValue & 1) === 1;
	  var shifted = aValue >> 1;
	  return isNegative
	    ? -shifted
	    : shifted;
	}

	/**
	 * Returns the base 64 VLQ encoded value.
	 */
	base64Vlq.encode = function base64VLQ_encode(aValue) {
	  var encoded = "";
	  var digit;

	  var vlq = toVLQSigned(aValue);

	  do {
	    digit = vlq & VLQ_BASE_MASK;
	    vlq >>>= VLQ_BASE_SHIFT;
	    if (vlq > 0) {
	      // There are still more digits in this value, so we must make sure the
	      // continuation bit is marked.
	      digit |= VLQ_CONTINUATION_BIT;
	    }
	    encoded += base64.encode(digit);
	  } while (vlq > 0);

	  return encoded;
	};

	/**
	 * Decodes the next base 64 VLQ value from the given string and returns the
	 * value and the rest of the string via the out parameter.
	 */
	base64Vlq.decode = function base64VLQ_decode(aStr, aIndex, aOutParam) {
	  var strLen = aStr.length;
	  var result = 0;
	  var shift = 0;
	  var continuation, digit;

	  do {
	    if (aIndex >= strLen) {
	      throw new Error("Expected more digits in base 64 VLQ value.");
	    }

	    digit = base64.decode(aStr.charCodeAt(aIndex++));
	    if (digit === -1) {
	      throw new Error("Invalid base64 digit: " + aStr.charAt(aIndex - 1));
	    }

	    continuation = !!(digit & VLQ_CONTINUATION_BIT);
	    digit &= VLQ_BASE_MASK;
	    result = result + (digit << shift);
	    shift += VLQ_BASE_SHIFT;
	  } while (continuation);

	  aOutParam.value = fromVLQSigned(result);
	  aOutParam.rest = aIndex;
	};
	return base64Vlq;
}

var util = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredUtil;

function requireUtil () {
	if (hasRequiredUtil) return util;
	hasRequiredUtil = 1;
	(function (exports) {
		/*
		 * Copyright 2011 Mozilla Foundation and contributors
		 * Licensed under the New BSD license. See LICENSE or:
		 * http://opensource.org/licenses/BSD-3-Clause
		 */

		/**
		 * This is a helper function for getting values from parameter/options
		 * objects.
		 *
		 * @param args The object we are extracting values from
		 * @param name The name of the property we are getting.
		 * @param defaultValue An optional value to return if the property is missing
		 * from the object. If this is not specified and the property is missing, an
		 * error will be thrown.
		 */
		function getArg(aArgs, aName, aDefaultValue) {
		  if (aName in aArgs) {
		    return aArgs[aName];
		  } else if (arguments.length === 3) {
		    return aDefaultValue;
		  } else {
		    throw new Error('"' + aName + '" is a required argument.');
		  }
		}
		exports.getArg = getArg;

		var urlRegexp = /^(?:([\w+\-.]+):)?\/\/(?:(\w+:\w+)@)?([\w.-]*)(?::(\d+))?(.*)$/;
		var dataUrlRegexp = /^data:.+\,.+$/;

		function urlParse(aUrl) {
		  var match = aUrl.match(urlRegexp);
		  if (!match) {
		    return null;
		  }
		  return {
		    scheme: match[1],
		    auth: match[2],
		    host: match[3],
		    port: match[4],
		    path: match[5]
		  };
		}
		exports.urlParse = urlParse;

		function urlGenerate(aParsedUrl) {
		  var url = '';
		  if (aParsedUrl.scheme) {
		    url += aParsedUrl.scheme + ':';
		  }
		  url += '//';
		  if (aParsedUrl.auth) {
		    url += aParsedUrl.auth + '@';
		  }
		  if (aParsedUrl.host) {
		    url += aParsedUrl.host;
		  }
		  if (aParsedUrl.port) {
		    url += ":" + aParsedUrl.port;
		  }
		  if (aParsedUrl.path) {
		    url += aParsedUrl.path;
		  }
		  return url;
		}
		exports.urlGenerate = urlGenerate;

		var MAX_CACHED_INPUTS = 32;

		/**
		 * Takes some function `f(input) -> result` and returns a memoized version of
		 * `f`.
		 *
		 * We keep at most `MAX_CACHED_INPUTS` memoized results of `f` alive. The
		 * memoization is a dumb-simple, linear least-recently-used cache.
		 */
		function lruMemoize(f) {
		  var cache = [];

		  return function(input) {
		    for (var i = 0; i < cache.length; i++) {
		      if (cache[i].input === input) {
		        var temp = cache[0];
		        cache[0] = cache[i];
		        cache[i] = temp;
		        return cache[0].result;
		      }
		    }

		    var result = f(input);

		    cache.unshift({
		      input,
		      result,
		    });

		    if (cache.length > MAX_CACHED_INPUTS) {
		      cache.pop();
		    }

		    return result;
		  };
		}

		/**
		 * Normalizes a path, or the path portion of a URL:
		 *
		 * - Replaces consecutive slashes with one slash.
		 * - Removes unnecessary '.' parts.
		 * - Removes unnecessary '<dir>/..' parts.
		 *
		 * Based on code in the Node.js 'path' core module.
		 *
		 * @param aPath The path or url to normalize.
		 */
		var normalize = lruMemoize(function normalize(aPath) {
		  var path = aPath;
		  var url = urlParse(aPath);
		  if (url) {
		    if (!url.path) {
		      return aPath;
		    }
		    path = url.path;
		  }
		  var isAbsolute = exports.isAbsolute(path);
		  // Split the path into parts between `/` characters. This is much faster than
		  // using `.split(/\/+/g)`.
		  var parts = [];
		  var start = 0;
		  var i = 0;
		  while (true) {
		    start = i;
		    i = path.indexOf("/", start);
		    if (i === -1) {
		      parts.push(path.slice(start));
		      break;
		    } else {
		      parts.push(path.slice(start, i));
		      while (i < path.length && path[i] === "/") {
		        i++;
		      }
		    }
		  }

		  for (var part, up = 0, i = parts.length - 1; i >= 0; i--) {
		    part = parts[i];
		    if (part === '.') {
		      parts.splice(i, 1);
		    } else if (part === '..') {
		      up++;
		    } else if (up > 0) {
		      if (part === '') {
		        // The first part is blank if the path is absolute. Trying to go
		        // above the root is a no-op. Therefore we can remove all '..' parts
		        // directly after the root.
		        parts.splice(i + 1, up);
		        up = 0;
		      } else {
		        parts.splice(i, 2);
		        up--;
		      }
		    }
		  }
		  path = parts.join('/');

		  if (path === '') {
		    path = isAbsolute ? '/' : '.';
		  }

		  if (url) {
		    url.path = path;
		    return urlGenerate(url);
		  }
		  return path;
		});
		exports.normalize = normalize;

		/**
		 * Joins two paths/URLs.
		 *
		 * @param aRoot The root path or URL.
		 * @param aPath The path or URL to be joined with the root.
		 *
		 * - If aPath is a URL or a data URI, aPath is returned, unless aPath is a
		 *   scheme-relative URL: Then the scheme of aRoot, if any, is prepended
		 *   first.
		 * - Otherwise aPath is a path. If aRoot is a URL, then its path portion
		 *   is updated with the result and aRoot is returned. Otherwise the result
		 *   is returned.
		 *   - If aPath is absolute, the result is aPath.
		 *   - Otherwise the two paths are joined with a slash.
		 * - Joining for example 'http://' and 'www.example.com' is also supported.
		 */
		function join(aRoot, aPath) {
		  if (aRoot === "") {
		    aRoot = ".";
		  }
		  if (aPath === "") {
		    aPath = ".";
		  }
		  var aPathUrl = urlParse(aPath);
		  var aRootUrl = urlParse(aRoot);
		  if (aRootUrl) {
		    aRoot = aRootUrl.path || '/';
		  }

		  // `join(foo, '//www.example.org')`
		  if (aPathUrl && !aPathUrl.scheme) {
		    if (aRootUrl) {
		      aPathUrl.scheme = aRootUrl.scheme;
		    }
		    return urlGenerate(aPathUrl);
		  }

		  if (aPathUrl || aPath.match(dataUrlRegexp)) {
		    return aPath;
		  }

		  // `join('http://', 'www.example.com')`
		  if (aRootUrl && !aRootUrl.host && !aRootUrl.path) {
		    aRootUrl.host = aPath;
		    return urlGenerate(aRootUrl);
		  }

		  var joined = aPath.charAt(0) === '/'
		    ? aPath
		    : normalize(aRoot.replace(/\/+$/, '') + '/' + aPath);

		  if (aRootUrl) {
		    aRootUrl.path = joined;
		    return urlGenerate(aRootUrl);
		  }
		  return joined;
		}
		exports.join = join;

		exports.isAbsolute = function (aPath) {
		  return aPath.charAt(0) === '/' || urlRegexp.test(aPath);
		};

		/**
		 * Make a path relative to a URL or another path.
		 *
		 * @param aRoot The root path or URL.
		 * @param aPath The path or URL to be made relative to aRoot.
		 */
		function relative(aRoot, aPath) {
		  if (aRoot === "") {
		    aRoot = ".";
		  }

		  aRoot = aRoot.replace(/\/$/, '');

		  // It is possible for the path to be above the root. In this case, simply
		  // checking whether the root is a prefix of the path won't work. Instead, we
		  // need to remove components from the root one by one, until either we find
		  // a prefix that fits, or we run out of components to remove.
		  var level = 0;
		  while (aPath.indexOf(aRoot + '/') !== 0) {
		    var index = aRoot.lastIndexOf("/");
		    if (index < 0) {
		      return aPath;
		    }

		    // If the only part of the root that is left is the scheme (i.e. http://,
		    // file:///, etc.), one or more slashes (/), or simply nothing at all, we
		    // have exhausted all components, so the path is not relative to the root.
		    aRoot = aRoot.slice(0, index);
		    if (aRoot.match(/^([^\/]+:\/)?\/*$/)) {
		      return aPath;
		    }

		    ++level;
		  }

		  // Make sure we add a "../" for each component we removed from the root.
		  return Array(level + 1).join("../") + aPath.substr(aRoot.length + 1);
		}
		exports.relative = relative;

		var supportsNullProto = (function () {
		  var obj = Object.create(null);
		  return !('__proto__' in obj);
		}());

		function identity (s) {
		  return s;
		}

		/**
		 * Because behavior goes wacky when you set `__proto__` on objects, we
		 * have to prefix all the strings in our set with an arbitrary character.
		 *
		 * See https://github.com/mozilla/source-map/pull/31 and
		 * https://github.com/mozilla/source-map/issues/30
		 *
		 * @param String aStr
		 */
		function toSetString(aStr) {
		  if (isProtoString(aStr)) {
		    return '$' + aStr;
		  }

		  return aStr;
		}
		exports.toSetString = supportsNullProto ? identity : toSetString;

		function fromSetString(aStr) {
		  if (isProtoString(aStr)) {
		    return aStr.slice(1);
		  }

		  return aStr;
		}
		exports.fromSetString = supportsNullProto ? identity : fromSetString;

		function isProtoString(s) {
		  if (!s) {
		    return false;
		  }

		  var length = s.length;

		  if (length < 9 /* "__proto__".length */) {
		    return false;
		  }

		  if (s.charCodeAt(length - 1) !== 95  /* '_' */ ||
		      s.charCodeAt(length - 2) !== 95  /* '_' */ ||
		      s.charCodeAt(length - 3) !== 111 /* 'o' */ ||
		      s.charCodeAt(length - 4) !== 116 /* 't' */ ||
		      s.charCodeAt(length - 5) !== 111 /* 'o' */ ||
		      s.charCodeAt(length - 6) !== 114 /* 'r' */ ||
		      s.charCodeAt(length - 7) !== 112 /* 'p' */ ||
		      s.charCodeAt(length - 8) !== 95  /* '_' */ ||
		      s.charCodeAt(length - 9) !== 95  /* '_' */) {
		    return false;
		  }

		  for (var i = length - 10; i >= 0; i--) {
		    if (s.charCodeAt(i) !== 36 /* '$' */) {
		      return false;
		    }
		  }

		  return true;
		}

		/**
		 * Comparator between two mappings where the original positions are compared.
		 *
		 * Optionally pass in `true` as `onlyCompareGenerated` to consider two
		 * mappings with the same original source/line/column, but different generated
		 * line and column the same. Useful when searching for a mapping with a
		 * stubbed out mapping.
		 */
		function compareByOriginalPositions(mappingA, mappingB, onlyCompareOriginal) {
		  var cmp = strcmp(mappingA.source, mappingB.source);
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalLine - mappingB.originalLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalColumn - mappingB.originalColumn;
		  if (cmp !== 0 || onlyCompareOriginal) {
		    return cmp;
		  }

		  cmp = mappingA.generatedColumn - mappingB.generatedColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.generatedLine - mappingB.generatedLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  return strcmp(mappingA.name, mappingB.name);
		}
		exports.compareByOriginalPositions = compareByOriginalPositions;

		function compareByOriginalPositionsNoSource(mappingA, mappingB, onlyCompareOriginal) {
		  var cmp;

		  cmp = mappingA.originalLine - mappingB.originalLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalColumn - mappingB.originalColumn;
		  if (cmp !== 0 || onlyCompareOriginal) {
		    return cmp;
		  }

		  cmp = mappingA.generatedColumn - mappingB.generatedColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.generatedLine - mappingB.generatedLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  return strcmp(mappingA.name, mappingB.name);
		}
		exports.compareByOriginalPositionsNoSource = compareByOriginalPositionsNoSource;

		/**
		 * Comparator between two mappings with deflated source and name indices where
		 * the generated positions are compared.
		 *
		 * Optionally pass in `true` as `onlyCompareGenerated` to consider two
		 * mappings with the same generated line and column, but different
		 * source/name/original line and column the same. Useful when searching for a
		 * mapping with a stubbed out mapping.
		 */
		function compareByGeneratedPositionsDeflated(mappingA, mappingB, onlyCompareGenerated) {
		  var cmp = mappingA.generatedLine - mappingB.generatedLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.generatedColumn - mappingB.generatedColumn;
		  if (cmp !== 0 || onlyCompareGenerated) {
		    return cmp;
		  }

		  cmp = strcmp(mappingA.source, mappingB.source);
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalLine - mappingB.originalLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalColumn - mappingB.originalColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  return strcmp(mappingA.name, mappingB.name);
		}
		exports.compareByGeneratedPositionsDeflated = compareByGeneratedPositionsDeflated;

		function compareByGeneratedPositionsDeflatedNoLine(mappingA, mappingB, onlyCompareGenerated) {
		  var cmp = mappingA.generatedColumn - mappingB.generatedColumn;
		  if (cmp !== 0 || onlyCompareGenerated) {
		    return cmp;
		  }

		  cmp = strcmp(mappingA.source, mappingB.source);
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalLine - mappingB.originalLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalColumn - mappingB.originalColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  return strcmp(mappingA.name, mappingB.name);
		}
		exports.compareByGeneratedPositionsDeflatedNoLine = compareByGeneratedPositionsDeflatedNoLine;

		function strcmp(aStr1, aStr2) {
		  if (aStr1 === aStr2) {
		    return 0;
		  }

		  if (aStr1 === null) {
		    return 1; // aStr2 !== null
		  }

		  if (aStr2 === null) {
		    return -1; // aStr1 !== null
		  }

		  if (aStr1 > aStr2) {
		    return 1;
		  }

		  return -1;
		}

		/**
		 * Comparator between two mappings with inflated source and name strings where
		 * the generated positions are compared.
		 */
		function compareByGeneratedPositionsInflated(mappingA, mappingB) {
		  var cmp = mappingA.generatedLine - mappingB.generatedLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.generatedColumn - mappingB.generatedColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = strcmp(mappingA.source, mappingB.source);
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalLine - mappingB.originalLine;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  cmp = mappingA.originalColumn - mappingB.originalColumn;
		  if (cmp !== 0) {
		    return cmp;
		  }

		  return strcmp(mappingA.name, mappingB.name);
		}
		exports.compareByGeneratedPositionsInflated = compareByGeneratedPositionsInflated;

		/**
		 * Strip any JSON XSSI avoidance prefix from the string (as documented
		 * in the source maps specification), and then parse the string as
		 * JSON.
		 */
		function parseSourceMapInput(str) {
		  return JSON.parse(str.replace(/^\)]}'[^\n]*\n/, ''));
		}
		exports.parseSourceMapInput = parseSourceMapInput;

		/**
		 * Compute the URL of a source given the the source root, the source's
		 * URL, and the source map's URL.
		 */
		function computeSourceURL(sourceRoot, sourceURL, sourceMapURL) {
		  sourceURL = sourceURL || '';

		  if (sourceRoot) {
		    // This follows what Chrome does.
		    if (sourceRoot[sourceRoot.length - 1] !== '/' && sourceURL[0] !== '/') {
		      sourceRoot += '/';
		    }
		    // The spec says:
		    //   Line 4: An optional source root, useful for relocating source
		    //   files on a server or removing repeated values in the
		    //   “sources” entry.  This value is prepended to the individual
		    //   entries in the “source” field.
		    sourceURL = sourceRoot + sourceURL;
		  }

		  // Historically, SourceMapConsumer did not take the sourceMapURL as
		  // a parameter.  This mode is still somewhat supported, which is why
		  // this code block is conditional.  However, it's preferable to pass
		  // the source map URL to SourceMapConsumer, so that this function
		  // can implement the source URL resolution algorithm as outlined in
		  // the spec.  This block is basically the equivalent of:
		  //    new URL(sourceURL, sourceMapURL).toString()
		  // ... except it avoids using URL, which wasn't available in the
		  // older releases of node still supported by this library.
		  //
		  // The spec says:
		  //   If the sources are not absolute URLs after prepending of the
		  //   “sourceRoot”, the sources are resolved relative to the
		  //   SourceMap (like resolving script src in a html document).
		  if (sourceMapURL) {
		    var parsed = urlParse(sourceMapURL);
		    if (!parsed) {
		      throw new Error("sourceMapURL could not be parsed");
		    }
		    if (parsed.path) {
		      // Strip the last path component, but keep the "/".
		      var index = parsed.path.lastIndexOf('/');
		      if (index >= 0) {
		        parsed.path = parsed.path.substring(0, index + 1);
		      }
		    }
		    sourceURL = join(urlGenerate(parsed), sourceURL);
		  }

		  return normalize(sourceURL);
		}
		exports.computeSourceURL = computeSourceURL; 
	} (util));
	return util;
}

var arraySet = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredArraySet;

function requireArraySet () {
	if (hasRequiredArraySet) return arraySet;
	hasRequiredArraySet = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var util = requireUtil();
	var has = Object.prototype.hasOwnProperty;
	var hasNativeMap = typeof Map !== "undefined";

	/**
	 * A data structure which is a combination of an array and a set. Adding a new
	 * member is O(1), testing for membership is O(1), and finding the index of an
	 * element is O(1). Removing elements from the set is not supported. Only
	 * strings are supported for membership.
	 */
	function ArraySet() {
	  this._array = [];
	  this._set = hasNativeMap ? new Map() : Object.create(null);
	}

	/**
	 * Static method for creating ArraySet instances from an existing array.
	 */
	ArraySet.fromArray = function ArraySet_fromArray(aArray, aAllowDuplicates) {
	  var set = new ArraySet();
	  for (var i = 0, len = aArray.length; i < len; i++) {
	    set.add(aArray[i], aAllowDuplicates);
	  }
	  return set;
	};

	/**
	 * Return how many unique items are in this ArraySet. If duplicates have been
	 * added, than those do not count towards the size.
	 *
	 * @returns Number
	 */
	ArraySet.prototype.size = function ArraySet_size() {
	  return hasNativeMap ? this._set.size : Object.getOwnPropertyNames(this._set).length;
	};

	/**
	 * Add the given string to this set.
	 *
	 * @param String aStr
	 */
	ArraySet.prototype.add = function ArraySet_add(aStr, aAllowDuplicates) {
	  var sStr = hasNativeMap ? aStr : util.toSetString(aStr);
	  var isDuplicate = hasNativeMap ? this.has(aStr) : has.call(this._set, sStr);
	  var idx = this._array.length;
	  if (!isDuplicate || aAllowDuplicates) {
	    this._array.push(aStr);
	  }
	  if (!isDuplicate) {
	    if (hasNativeMap) {
	      this._set.set(aStr, idx);
	    } else {
	      this._set[sStr] = idx;
	    }
	  }
	};

	/**
	 * Is the given string a member of this set?
	 *
	 * @param String aStr
	 */
	ArraySet.prototype.has = function ArraySet_has(aStr) {
	  if (hasNativeMap) {
	    return this._set.has(aStr);
	  } else {
	    var sStr = util.toSetString(aStr);
	    return has.call(this._set, sStr);
	  }
	};

	/**
	 * What is the index of the given string in the array?
	 *
	 * @param String aStr
	 */
	ArraySet.prototype.indexOf = function ArraySet_indexOf(aStr) {
	  if (hasNativeMap) {
	    var idx = this._set.get(aStr);
	    if (idx >= 0) {
	        return idx;
	    }
	  } else {
	    var sStr = util.toSetString(aStr);
	    if (has.call(this._set, sStr)) {
	      return this._set[sStr];
	    }
	  }

	  throw new Error('"' + aStr + '" is not in the set.');
	};

	/**
	 * What is the element at the given index?
	 *
	 * @param Number aIdx
	 */
	ArraySet.prototype.at = function ArraySet_at(aIdx) {
	  if (aIdx >= 0 && aIdx < this._array.length) {
	    return this._array[aIdx];
	  }
	  throw new Error('No element indexed by ' + aIdx);
	};

	/**
	 * Returns the array representation of this set (which has the proper indices
	 * indicated by indexOf). Note that this is a copy of the internal array used
	 * for storing the members so that no one can mess with internal state.
	 */
	ArraySet.prototype.toArray = function ArraySet_toArray() {
	  return this._array.slice();
	};

	arraySet.ArraySet = ArraySet;
	return arraySet;
}

var mappingList = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredMappingList;

function requireMappingList () {
	if (hasRequiredMappingList) return mappingList;
	hasRequiredMappingList = 1;
	/*
	 * Copyright 2014 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var util = requireUtil();

	/**
	 * Determine whether mappingB is after mappingA with respect to generated
	 * position.
	 */
	function generatedPositionAfter(mappingA, mappingB) {
	  // Optimized for most common case
	  var lineA = mappingA.generatedLine;
	  var lineB = mappingB.generatedLine;
	  var columnA = mappingA.generatedColumn;
	  var columnB = mappingB.generatedColumn;
	  return lineB > lineA || lineB == lineA && columnB >= columnA ||
	         util.compareByGeneratedPositionsInflated(mappingA, mappingB) <= 0;
	}

	/**
	 * A data structure to provide a sorted view of accumulated mappings in a
	 * performance conscious manner. It trades a neglibable overhead in general
	 * case for a large speedup in case of mappings being added in order.
	 */
	function MappingList() {
	  this._array = [];
	  this._sorted = true;
	  // Serves as infimum
	  this._last = {generatedLine: -1, generatedColumn: 0};
	}

	/**
	 * Iterate through internal items. This method takes the same arguments that
	 * `Array.prototype.forEach` takes.
	 *
	 * NOTE: The order of the mappings is NOT guaranteed.
	 */
	MappingList.prototype.unsortedForEach =
	  function MappingList_forEach(aCallback, aThisArg) {
	    this._array.forEach(aCallback, aThisArg);
	  };

	/**
	 * Add the given source mapping.
	 *
	 * @param Object aMapping
	 */
	MappingList.prototype.add = function MappingList_add(aMapping) {
	  if (generatedPositionAfter(this._last, aMapping)) {
	    this._last = aMapping;
	    this._array.push(aMapping);
	  } else {
	    this._sorted = false;
	    this._array.push(aMapping);
	  }
	};

	/**
	 * Returns the flat, sorted array of mappings. The mappings are sorted by
	 * generated position.
	 *
	 * WARNING: This method returns internal data without copying, for
	 * performance. The return value must NOT be mutated, and should be treated as
	 * an immutable borrow. If you want to take ownership, you must make your own
	 * copy.
	 */
	MappingList.prototype.toArray = function MappingList_toArray() {
	  if (!this._sorted) {
	    this._array.sort(util.compareByGeneratedPositionsInflated);
	    this._sorted = true;
	  }
	  return this._array;
	};

	mappingList.MappingList = MappingList;
	return mappingList;
}

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredSourceMapGenerator;

function requireSourceMapGenerator () {
	if (hasRequiredSourceMapGenerator) return sourceMapGenerator;
	hasRequiredSourceMapGenerator = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var base64VLQ = requireBase64Vlq();
	var util = requireUtil();
	var ArraySet = requireArraySet().ArraySet;
	var MappingList = requireMappingList().MappingList;

	/**
	 * An instance of the SourceMapGenerator represents a source map which is
	 * being built incrementally. You may pass an object with the following
	 * properties:
	 *
	 *   - file: The filename of the generated source.
	 *   - sourceRoot: A root for all relative URLs in this source map.
	 */
	function SourceMapGenerator(aArgs) {
	  if (!aArgs) {
	    aArgs = {};
	  }
	  this._file = util.getArg(aArgs, 'file', null);
	  this._sourceRoot = util.getArg(aArgs, 'sourceRoot', null);
	  this._skipValidation = util.getArg(aArgs, 'skipValidation', false);
	  this._ignoreInvalidMapping = util.getArg(aArgs, 'ignoreInvalidMapping', false);
	  this._sources = new ArraySet();
	  this._names = new ArraySet();
	  this._mappings = new MappingList();
	  this._sourcesContents = null;
	}

	SourceMapGenerator.prototype._version = 3;

	/**
	 * Creates a new SourceMapGenerator based on a SourceMapConsumer
	 *
	 * @param aSourceMapConsumer The SourceMap.
	 */
	SourceMapGenerator.fromSourceMap =
	  function SourceMapGenerator_fromSourceMap(aSourceMapConsumer, generatorOps) {
	    var sourceRoot = aSourceMapConsumer.sourceRoot;
	    var generator = new SourceMapGenerator(Object.assign(generatorOps || {}, {
	      file: aSourceMapConsumer.file,
	      sourceRoot: sourceRoot
	    }));
	    aSourceMapConsumer.eachMapping(function (mapping) {
	      var newMapping = {
	        generated: {
	          line: mapping.generatedLine,
	          column: mapping.generatedColumn
	        }
	      };

	      if (mapping.source != null) {
	        newMapping.source = mapping.source;
	        if (sourceRoot != null) {
	          newMapping.source = util.relative(sourceRoot, newMapping.source);
	        }

	        newMapping.original = {
	          line: mapping.originalLine,
	          column: mapping.originalColumn
	        };

	        if (mapping.name != null) {
	          newMapping.name = mapping.name;
	        }
	      }

	      generator.addMapping(newMapping);
	    });
	    aSourceMapConsumer.sources.forEach(function (sourceFile) {
	      var sourceRelative = sourceFile;
	      if (sourceRoot !== null) {
	        sourceRelative = util.relative(sourceRoot, sourceFile);
	      }

	      if (!generator._sources.has(sourceRelative)) {
	        generator._sources.add(sourceRelative);
	      }

	      var content = aSourceMapConsumer.sourceContentFor(sourceFile);
	      if (content != null) {
	        generator.setSourceContent(sourceFile, content);
	      }
	    });
	    return generator;
	  };

	/**
	 * Add a single mapping from original source line and column to the generated
	 * source's line and column for this source map being created. The mapping
	 * object should have the following properties:
	 *
	 *   - generated: An object with the generated line and column positions.
	 *   - original: An object with the original line and column positions.
	 *   - source: The original source file (relative to the sourceRoot).
	 *   - name: An optional original token name for this mapping.
	 */
	SourceMapGenerator.prototype.addMapping =
	  function SourceMapGenerator_addMapping(aArgs) {
	    var generated = util.getArg(aArgs, 'generated');
	    var original = util.getArg(aArgs, 'original', null);
	    var source = util.getArg(aArgs, 'source', null);
	    var name = util.getArg(aArgs, 'name', null);

	    if (!this._skipValidation) {
	      if (this._validateMapping(generated, original, source, name) === false) {
	        return;
	      }
	    }

	    if (source != null) {
	      source = String(source);
	      if (!this._sources.has(source)) {
	        this._sources.add(source);
	      }
	    }

	    if (name != null) {
	      name = String(name);
	      if (!this._names.has(name)) {
	        this._names.add(name);
	      }
	    }

	    this._mappings.add({
	      generatedLine: generated.line,
	      generatedColumn: generated.column,
	      originalLine: original != null && original.line,
	      originalColumn: original != null && original.column,
	      source: source,
	      name: name
	    });
	  };

	/**
	 * Set the source content for a source file.
	 */
	SourceMapGenerator.prototype.setSourceContent =
	  function SourceMapGenerator_setSourceContent(aSourceFile, aSourceContent) {
	    var source = aSourceFile;
	    if (this._sourceRoot != null) {
	      source = util.relative(this._sourceRoot, source);
	    }

	    if (aSourceContent != null) {
	      // Add the source content to the _sourcesContents map.
	      // Create a new _sourcesContents map if the property is null.
	      if (!this._sourcesContents) {
	        this._sourcesContents = Object.create(null);
	      }
	      this._sourcesContents[util.toSetString(source)] = aSourceContent;
	    } else if (this._sourcesContents) {
	      // Remove the source file from the _sourcesContents map.
	      // If the _sourcesContents map is empty, set the property to null.
	      delete this._sourcesContents[util.toSetString(source)];
	      if (Object.keys(this._sourcesContents).length === 0) {
	        this._sourcesContents = null;
	      }
	    }
	  };

	/**
	 * Applies the mappings of a sub-source-map for a specific source file to the
	 * source map being generated. Each mapping to the supplied source file is
	 * rewritten using the supplied source map. Note: The resolution for the
	 * resulting mappings is the minimium of this map and the supplied map.
	 *
	 * @param aSourceMapConsumer The source map to be applied.
	 * @param aSourceFile Optional. The filename of the source file.
	 *        If omitted, SourceMapConsumer's file property will be used.
	 * @param aSourceMapPath Optional. The dirname of the path to the source map
	 *        to be applied. If relative, it is relative to the SourceMapConsumer.
	 *        This parameter is needed when the two source maps aren't in the same
	 *        directory, and the source map to be applied contains relative source
	 *        paths. If so, those relative source paths need to be rewritten
	 *        relative to the SourceMapGenerator.
	 */
	SourceMapGenerator.prototype.applySourceMap =
	  function SourceMapGenerator_applySourceMap(aSourceMapConsumer, aSourceFile, aSourceMapPath) {
	    var sourceFile = aSourceFile;
	    // If aSourceFile is omitted, we will use the file property of the SourceMap
	    if (aSourceFile == null) {
	      if (aSourceMapConsumer.file == null) {
	        throw new Error(
	          'SourceMapGenerator.prototype.applySourceMap requires either an explicit source file, ' +
	          'or the source map\'s "file" property. Both were omitted.'
	        );
	      }
	      sourceFile = aSourceMapConsumer.file;
	    }
	    var sourceRoot = this._sourceRoot;
	    // Make "sourceFile" relative if an absolute Url is passed.
	    if (sourceRoot != null) {
	      sourceFile = util.relative(sourceRoot, sourceFile);
	    }
	    // Applying the SourceMap can add and remove items from the sources and
	    // the names array.
	    var newSources = new ArraySet();
	    var newNames = new ArraySet();

	    // Find mappings for the "sourceFile"
	    this._mappings.unsortedForEach(function (mapping) {
	      if (mapping.source === sourceFile && mapping.originalLine != null) {
	        // Check if it can be mapped by the source map, then update the mapping.
	        var original = aSourceMapConsumer.originalPositionFor({
	          line: mapping.originalLine,
	          column: mapping.originalColumn
	        });
	        if (original.source != null) {
	          // Copy mapping
	          mapping.source = original.source;
	          if (aSourceMapPath != null) {
	            mapping.source = util.join(aSourceMapPath, mapping.source);
	          }
	          if (sourceRoot != null) {
	            mapping.source = util.relative(sourceRoot, mapping.source);
	          }
	          mapping.originalLine = original.line;
	          mapping.originalColumn = original.column;
	          if (original.name != null) {
	            mapping.name = original.name;
	          }
	        }
	      }

	      var source = mapping.source;
	      if (source != null && !newSources.has(source)) {
	        newSources.add(source);
	      }

	      var name = mapping.name;
	      if (name != null && !newNames.has(name)) {
	        newNames.add(name);
	      }

	    }, this);
	    this._sources = newSources;
	    this._names = newNames;

	    // Copy sourcesContents of applied map.
	    aSourceMapConsumer.sources.forEach(function (sourceFile) {
	      var content = aSourceMapConsumer.sourceContentFor(sourceFile);
	      if (content != null) {
	        if (aSourceMapPath != null) {
	          sourceFile = util.join(aSourceMapPath, sourceFile);
	        }
	        if (sourceRoot != null) {
	          sourceFile = util.relative(sourceRoot, sourceFile);
	        }
	        this.setSourceContent(sourceFile, content);
	      }
	    }, this);
	  };

	/**
	 * A mapping can have one of the three levels of data:
	 *
	 *   1. Just the generated position.
	 *   2. The Generated position, original position, and original source.
	 *   3. Generated and original position, original source, as well as a name
	 *      token.
	 *
	 * To maintain consistency, we validate that any new mapping being added falls
	 * in to one of these categories.
	 */
	SourceMapGenerator.prototype._validateMapping =
	  function SourceMapGenerator_validateMapping(aGenerated, aOriginal, aSource,
	                                              aName) {
	    // When aOriginal is truthy but has empty values for .line and .column,
	    // it is most likely a programmer error. In this case we throw a very
	    // specific error message to try to guide them the right way.
	    // For example: https://github.com/Polymer/polymer-bundler/pull/519
	    if (aOriginal && typeof aOriginal.line !== 'number' && typeof aOriginal.column !== 'number') {
	      var message = 'original.line and original.column are not numbers -- you probably meant to omit ' +
	      'the original mapping entirely and only map the generated position. If so, pass ' +
	      'null for the original mapping instead of an object with empty or null values.';

	      if (this._ignoreInvalidMapping) {
	        if (typeof console !== 'undefined' && console.warn) {
	          console.warn(message);
	        }
	        return false;
	      } else {
	        throw new Error(message);
	      }
	    }

	    if (aGenerated && 'line' in aGenerated && 'column' in aGenerated
	        && aGenerated.line > 0 && aGenerated.column >= 0
	        && !aOriginal && !aSource && !aName) {
	      // Case 1.
	      return;
	    }
	    else if (aGenerated && 'line' in aGenerated && 'column' in aGenerated
	             && aOriginal && 'line' in aOriginal && 'column' in aOriginal
	             && aGenerated.line > 0 && aGenerated.column >= 0
	             && aOriginal.line > 0 && aOriginal.column >= 0
	             && aSource) {
	      // Cases 2 and 3.
	      return;
	    }
	    else {
	      var message = 'Invalid mapping: ' + JSON.stringify({
	        generated: aGenerated,
	        source: aSource,
	        original: aOriginal,
	        name: aName
	      });

	      if (this._ignoreInvalidMapping) {
	        if (typeof console !== 'undefined' && console.warn) {
	          console.warn(message);
	        }
	        return false;
	      } else {
	        throw new Error(message)
	      }
	    }
	  };

	/**
	 * Serialize the accumulated mappings in to the stream of base 64 VLQs
	 * specified by the source map format.
	 */
	SourceMapGenerator.prototype._serializeMappings =
	  function SourceMapGenerator_serializeMappings() {
	    var previousGeneratedColumn = 0;
	    var previousGeneratedLine = 1;
	    var previousOriginalColumn = 0;
	    var previousOriginalLine = 0;
	    var previousName = 0;
	    var previousSource = 0;
	    var result = '';
	    var next;
	    var mapping;
	    var nameIdx;
	    var sourceIdx;

	    var mappings = this._mappings.toArray();
	    for (var i = 0, len = mappings.length; i < len; i++) {
	      mapping = mappings[i];
	      next = '';

	      if (mapping.generatedLine !== previousGeneratedLine) {
	        previousGeneratedColumn = 0;
	        while (mapping.generatedLine !== previousGeneratedLine) {
	          next += ';';
	          previousGeneratedLine++;
	        }
	      }
	      else {
	        if (i > 0) {
	          if (!util.compareByGeneratedPositionsInflated(mapping, mappings[i - 1])) {
	            continue;
	          }
	          next += ',';
	        }
	      }

	      next += base64VLQ.encode(mapping.generatedColumn
	                                 - previousGeneratedColumn);
	      previousGeneratedColumn = mapping.generatedColumn;

	      if (mapping.source != null) {
	        sourceIdx = this._sources.indexOf(mapping.source);
	        next += base64VLQ.encode(sourceIdx - previousSource);
	        previousSource = sourceIdx;

	        // lines are stored 0-based in SourceMap spec version 3
	        next += base64VLQ.encode(mapping.originalLine - 1
	                                   - previousOriginalLine);
	        previousOriginalLine = mapping.originalLine - 1;

	        next += base64VLQ.encode(mapping.originalColumn
	                                   - previousOriginalColumn);
	        previousOriginalColumn = mapping.originalColumn;

	        if (mapping.name != null) {
	          nameIdx = this._names.indexOf(mapping.name);
	          next += base64VLQ.encode(nameIdx - previousName);
	          previousName = nameIdx;
	        }
	      }

	      result += next;
	    }

	    return result;
	  };

	SourceMapGenerator.prototype._generateSourcesContent =
	  function SourceMapGenerator_generateSourcesContent(aSources, aSourceRoot) {
	    return aSources.map(function (source) {
	      if (!this._sourcesContents) {
	        return null;
	      }
	      if (aSourceRoot != null) {
	        source = util.relative(aSourceRoot, source);
	      }
	      var key = util.toSetString(source);
	      return Object.prototype.hasOwnProperty.call(this._sourcesContents, key)
	        ? this._sourcesContents[key]
	        : null;
	    }, this);
	  };

	/**
	 * Externalize the source map.
	 */
	SourceMapGenerator.prototype.toJSON =
	  function SourceMapGenerator_toJSON() {
	    var map = {
	      version: this._version,
	      sources: this._sources.toArray(),
	      names: this._names.toArray(),
	      mappings: this._serializeMappings()
	    };
	    if (this._file != null) {
	      map.file = this._file;
	    }
	    if (this._sourceRoot != null) {
	      map.sourceRoot = this._sourceRoot;
	    }
	    if (this._sourcesContents) {
	      map.sourcesContent = this._generateSourcesContent(map.sources, map.sourceRoot);
	    }

	    return map;
	  };

	/**
	 * Render the source map being generated to a string.
	 */
	SourceMapGenerator.prototype.toString =
	  function SourceMapGenerator_toString() {
	    return JSON.stringify(this.toJSON());
	  };

	sourceMapGenerator.SourceMapGenerator = SourceMapGenerator;
	return sourceMapGenerator;
}

var sourceMapConsumer = {};

var binarySearch = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredBinarySearch;

function requireBinarySearch () {
	if (hasRequiredBinarySearch) return binarySearch;
	hasRequiredBinarySearch = 1;
	(function (exports) {
		/*
		 * Copyright 2011 Mozilla Foundation and contributors
		 * Licensed under the New BSD license. See LICENSE or:
		 * http://opensource.org/licenses/BSD-3-Clause
		 */

		exports.GREATEST_LOWER_BOUND = 1;
		exports.LEAST_UPPER_BOUND = 2;

		/**
		 * Recursive implementation of binary search.
		 *
		 * @param aLow Indices here and lower do not contain the needle.
		 * @param aHigh Indices here and higher do not contain the needle.
		 * @param aNeedle The element being searched for.
		 * @param aHaystack The non-empty array being searched.
		 * @param aCompare Function which takes two elements and returns -1, 0, or 1.
		 * @param aBias Either 'binarySearch.GREATEST_LOWER_BOUND' or
		 *     'binarySearch.LEAST_UPPER_BOUND'. Specifies whether to return the
		 *     closest element that is smaller than or greater than the one we are
		 *     searching for, respectively, if the exact element cannot be found.
		 */
		function recursiveSearch(aLow, aHigh, aNeedle, aHaystack, aCompare, aBias) {
		  // This function terminates when one of the following is true:
		  //
		  //   1. We find the exact element we are looking for.
		  //
		  //   2. We did not find the exact element, but we can return the index of
		  //      the next-closest element.
		  //
		  //   3. We did not find the exact element, and there is no next-closest
		  //      element than the one we are searching for, so we return -1.
		  var mid = Math.floor((aHigh - aLow) / 2) + aLow;
		  var cmp = aCompare(aNeedle, aHaystack[mid], true);
		  if (cmp === 0) {
		    // Found the element we are looking for.
		    return mid;
		  }
		  else if (cmp > 0) {
		    // Our needle is greater than aHaystack[mid].
		    if (aHigh - mid > 1) {
		      // The element is in the upper half.
		      return recursiveSearch(mid, aHigh, aNeedle, aHaystack, aCompare, aBias);
		    }

		    // The exact needle element was not found in this haystack. Determine if
		    // we are in termination case (3) or (2) and return the appropriate thing.
		    if (aBias == exports.LEAST_UPPER_BOUND) {
		      return aHigh < aHaystack.length ? aHigh : -1;
		    } else {
		      return mid;
		    }
		  }
		  else {
		    // Our needle is less than aHaystack[mid].
		    if (mid - aLow > 1) {
		      // The element is in the lower half.
		      return recursiveSearch(aLow, mid, aNeedle, aHaystack, aCompare, aBias);
		    }

		    // we are in termination case (3) or (2) and return the appropriate thing.
		    if (aBias == exports.LEAST_UPPER_BOUND) {
		      return mid;
		    } else {
		      return aLow < 0 ? -1 : aLow;
		    }
		  }
		}

		/**
		 * This is an implementation of binary search which will always try and return
		 * the index of the closest element if there is no exact hit. This is because
		 * mappings between original and generated line/col pairs are single points,
		 * and there is an implicit region between each of them, so a miss just means
		 * that you aren't on the very start of a region.
		 *
		 * @param aNeedle The element you are looking for.
		 * @param aHaystack The array that is being searched.
		 * @param aCompare A function which takes the needle and an element in the
		 *     array and returns -1, 0, or 1 depending on whether the needle is less
		 *     than, equal to, or greater than the element, respectively.
		 * @param aBias Either 'binarySearch.GREATEST_LOWER_BOUND' or
		 *     'binarySearch.LEAST_UPPER_BOUND'. Specifies whether to return the
		 *     closest element that is smaller than or greater than the one we are
		 *     searching for, respectively, if the exact element cannot be found.
		 *     Defaults to 'binarySearch.GREATEST_LOWER_BOUND'.
		 */
		exports.search = function search(aNeedle, aHaystack, aCompare, aBias) {
		  if (aHaystack.length === 0) {
		    return -1;
		  }

		  var index = recursiveSearch(-1, aHaystack.length, aNeedle, aHaystack,
		                              aCompare, aBias || exports.GREATEST_LOWER_BOUND);
		  if (index < 0) {
		    return -1;
		  }

		  // We have found either the exact element, or the next-closest element than
		  // the one we are searching for. However, there may be more than one such
		  // element. Make sure we always return the smallest of these.
		  while (index - 1 >= 0) {
		    if (aCompare(aHaystack[index], aHaystack[index - 1], true) !== 0) {
		      break;
		    }
		    --index;
		  }

		  return index;
		}; 
	} (binarySearch));
	return binarySearch;
}

var quickSort = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredQuickSort;

function requireQuickSort () {
	if (hasRequiredQuickSort) return quickSort;
	hasRequiredQuickSort = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	// It turns out that some (most?) JavaScript engines don't self-host
	// `Array.prototype.sort`. This makes sense because C++ will likely remain
	// faster than JS when doing raw CPU-intensive sorting. However, when using a
	// custom comparator function, calling back and forth between the VM's C++ and
	// JIT'd JS is rather slow *and* loses JIT type information, resulting in
	// worse generated code for the comparator function than would be optimal. In
	// fact, when sorting with a comparator, these costs outweigh the benefits of
	// sorting in C++. By using our own JS-implemented Quick Sort (below), we get
	// a ~3500ms mean speed-up in `bench/bench.html`.

	function SortTemplate(comparator) {

	/**
	 * Swap the elements indexed by `x` and `y` in the array `ary`.
	 *
	 * @param {Array} ary
	 *        The array.
	 * @param {Number} x
	 *        The index of the first item.
	 * @param {Number} y
	 *        The index of the second item.
	 */
	function swap(ary, x, y) {
	  var temp = ary[x];
	  ary[x] = ary[y];
	  ary[y] = temp;
	}

	/**
	 * Returns a random integer within the range `low .. high` inclusive.
	 *
	 * @param {Number} low
	 *        The lower bound on the range.
	 * @param {Number} high
	 *        The upper bound on the range.
	 */
	function randomIntInRange(low, high) {
	  return Math.round(low + (Math.random() * (high - low)));
	}

	/**
	 * The Quick Sort algorithm.
	 *
	 * @param {Array} ary
	 *        An array to sort.
	 * @param {function} comparator
	 *        Function to use to compare two items.
	 * @param {Number} p
	 *        Start index of the array
	 * @param {Number} r
	 *        End index of the array
	 */
	function doQuickSort(ary, comparator, p, r) {
	  // If our lower bound is less than our upper bound, we (1) partition the
	  // array into two pieces and (2) recurse on each half. If it is not, this is
	  // the empty array and our base case.

	  if (p < r) {
	    // (1) Partitioning.
	    //
	    // The partitioning chooses a pivot between `p` and `r` and moves all
	    // elements that are less than or equal to the pivot to the before it, and
	    // all the elements that are greater than it after it. The effect is that
	    // once partition is done, the pivot is in the exact place it will be when
	    // the array is put in sorted order, and it will not need to be moved
	    // again. This runs in O(n) time.

	    // Always choose a random pivot so that an input array which is reverse
	    // sorted does not cause O(n^2) running time.
	    var pivotIndex = randomIntInRange(p, r);
	    var i = p - 1;

	    swap(ary, pivotIndex, r);
	    var pivot = ary[r];

	    // Immediately after `j` is incremented in this loop, the following hold
	    // true:
	    //
	    //   * Every element in `ary[p .. i]` is less than or equal to the pivot.
	    //
	    //   * Every element in `ary[i+1 .. j-1]` is greater than the pivot.
	    for (var j = p; j < r; j++) {
	      if (comparator(ary[j], pivot, false) <= 0) {
	        i += 1;
	        swap(ary, i, j);
	      }
	    }

	    swap(ary, i + 1, j);
	    var q = i + 1;

	    // (2) Recurse on each half.

	    doQuickSort(ary, comparator, p, q - 1);
	    doQuickSort(ary, comparator, q + 1, r);
	  }
	}

	  return doQuickSort;
	}

	function cloneSort(comparator) {
	  let template = SortTemplate.toString();
	  let templateFn = new Function(`return ${template}`)();
	  return templateFn(comparator);
	}

	/**
	 * Sort the given array in-place with the given comparator function.
	 *
	 * @param {Array} ary
	 *        An array to sort.
	 * @param {function} comparator
	 *        Function to use to compare two items.
	 */

	let sortCache = new WeakMap();
	quickSort.quickSort = function (ary, comparator, start = 0) {
	  let doQuickSort = sortCache.get(comparator);
	  if (doQuickSort === void 0) {
	    doQuickSort = cloneSort(comparator);
	    sortCache.set(comparator, doQuickSort);
	  }
	  doQuickSort(ary, comparator, start, ary.length - 1);
	};
	return quickSort;
}

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredSourceMapConsumer;

function requireSourceMapConsumer () {
	if (hasRequiredSourceMapConsumer) return sourceMapConsumer;
	hasRequiredSourceMapConsumer = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var util = requireUtil();
	var binarySearch = requireBinarySearch();
	var ArraySet = requireArraySet().ArraySet;
	var base64VLQ = requireBase64Vlq();
	var quickSort = requireQuickSort().quickSort;

	function SourceMapConsumer(aSourceMap, aSourceMapURL) {
	  var sourceMap = aSourceMap;
	  if (typeof aSourceMap === 'string') {
	    sourceMap = util.parseSourceMapInput(aSourceMap);
	  }

	  return sourceMap.sections != null
	    ? new IndexedSourceMapConsumer(sourceMap, aSourceMapURL)
	    : new BasicSourceMapConsumer(sourceMap, aSourceMapURL);
	}

	SourceMapConsumer.fromSourceMap = function(aSourceMap, aSourceMapURL) {
	  return BasicSourceMapConsumer.fromSourceMap(aSourceMap, aSourceMapURL);
	};

	/**
	 * The version of the source mapping spec that we are consuming.
	 */
	SourceMapConsumer.prototype._version = 3;

	// `__generatedMappings` and `__originalMappings` are arrays that hold the
	// parsed mapping coordinates from the source map's "mappings" attribute. They
	// are lazily instantiated, accessed via the `_generatedMappings` and
	// `_originalMappings` getters respectively, and we only parse the mappings
	// and create these arrays once queried for a source location. We jump through
	// these hoops because there can be many thousands of mappings, and parsing
	// them is expensive, so we only want to do it if we must.
	//
	// Each object in the arrays is of the form:
	//
	//     {
	//       generatedLine: The line number in the generated code,
	//       generatedColumn: The column number in the generated code,
	//       source: The path to the original source file that generated this
	//               chunk of code,
	//       originalLine: The line number in the original source that
	//                     corresponds to this chunk of generated code,
	//       originalColumn: The column number in the original source that
	//                       corresponds to this chunk of generated code,
	//       name: The name of the original symbol which generated this chunk of
	//             code.
	//     }
	//
	// All properties except for `generatedLine` and `generatedColumn` can be
	// `null`.
	//
	// `_generatedMappings` is ordered by the generated positions.
	//
	// `_originalMappings` is ordered by the original positions.

	SourceMapConsumer.prototype.__generatedMappings = null;
	Object.defineProperty(SourceMapConsumer.prototype, '_generatedMappings', {
	  configurable: true,
	  enumerable: true,
	  get: function () {
	    if (!this.__generatedMappings) {
	      this._parseMappings(this._mappings, this.sourceRoot);
	    }

	    return this.__generatedMappings;
	  }
	});

	SourceMapConsumer.prototype.__originalMappings = null;
	Object.defineProperty(SourceMapConsumer.prototype, '_originalMappings', {
	  configurable: true,
	  enumerable: true,
	  get: function () {
	    if (!this.__originalMappings) {
	      this._parseMappings(this._mappings, this.sourceRoot);
	    }

	    return this.__originalMappings;
	  }
	});

	SourceMapConsumer.prototype._charIsMappingSeparator =
	  function SourceMapConsumer_charIsMappingSeparator(aStr, index) {
	    var c = aStr.charAt(index);
	    return c === ";" || c === ",";
	  };

	/**
	 * Parse the mappings in a string in to a data structure which we can easily
	 * query (the ordered arrays in the `this.__generatedMappings` and
	 * `this.__originalMappings` properties).
	 */
	SourceMapConsumer.prototype._parseMappings =
	  function SourceMapConsumer_parseMappings(aStr, aSourceRoot) {
	    throw new Error("Subclasses must implement _parseMappings");
	  };

	SourceMapConsumer.GENERATED_ORDER = 1;
	SourceMapConsumer.ORIGINAL_ORDER = 2;

	SourceMapConsumer.GREATEST_LOWER_BOUND = 1;
	SourceMapConsumer.LEAST_UPPER_BOUND = 2;

	/**
	 * Iterate over each mapping between an original source/line/column and a
	 * generated line/column in this source map.
	 *
	 * @param Function aCallback
	 *        The function that is called with each mapping.
	 * @param Object aContext
	 *        Optional. If specified, this object will be the value of `this` every
	 *        time that `aCallback` is called.
	 * @param aOrder
	 *        Either `SourceMapConsumer.GENERATED_ORDER` or
	 *        `SourceMapConsumer.ORIGINAL_ORDER`. Specifies whether you want to
	 *        iterate over the mappings sorted by the generated file's line/column
	 *        order or the original's source/line/column order, respectively. Defaults to
	 *        `SourceMapConsumer.GENERATED_ORDER`.
	 */
	SourceMapConsumer.prototype.eachMapping =
	  function SourceMapConsumer_eachMapping(aCallback, aContext, aOrder) {
	    var context = aContext || null;
	    var order = aOrder || SourceMapConsumer.GENERATED_ORDER;

	    var mappings;
	    switch (order) {
	    case SourceMapConsumer.GENERATED_ORDER:
	      mappings = this._generatedMappings;
	      break;
	    case SourceMapConsumer.ORIGINAL_ORDER:
	      mappings = this._originalMappings;
	      break;
	    default:
	      throw new Error("Unknown order of iteration.");
	    }

	    var sourceRoot = this.sourceRoot;
	    var boundCallback = aCallback.bind(context);
	    var names = this._names;
	    var sources = this._sources;
	    var sourceMapURL = this._sourceMapURL;

	    for (var i = 0, n = mappings.length; i < n; i++) {
	      var mapping = mappings[i];
	      var source = mapping.source === null ? null : sources.at(mapping.source);
	      if(source !== null) {
	        source = util.computeSourceURL(sourceRoot, source, sourceMapURL);
	      }
	      boundCallback({
	        source: source,
	        generatedLine: mapping.generatedLine,
	        generatedColumn: mapping.generatedColumn,
	        originalLine: mapping.originalLine,
	        originalColumn: mapping.originalColumn,
	        name: mapping.name === null ? null : names.at(mapping.name)
	      });
	    }
	  };

	/**
	 * Returns all generated line and column information for the original source,
	 * line, and column provided. If no column is provided, returns all mappings
	 * corresponding to a either the line we are searching for or the next
	 * closest line that has any mappings. Otherwise, returns all mappings
	 * corresponding to the given line and either the column we are searching for
	 * or the next closest column that has any offsets.
	 *
	 * The only argument is an object with the following properties:
	 *
	 *   - source: The filename of the original source.
	 *   - line: The line number in the original source.  The line number is 1-based.
	 *   - column: Optional. the column number in the original source.
	 *    The column number is 0-based.
	 *
	 * and an array of objects is returned, each with the following properties:
	 *
	 *   - line: The line number in the generated source, or null.  The
	 *    line number is 1-based.
	 *   - column: The column number in the generated source, or null.
	 *    The column number is 0-based.
	 */
	SourceMapConsumer.prototype.allGeneratedPositionsFor =
	  function SourceMapConsumer_allGeneratedPositionsFor(aArgs) {
	    var line = util.getArg(aArgs, 'line');

	    // When there is no exact match, BasicSourceMapConsumer.prototype._findMapping
	    // returns the index of the closest mapping less than the needle. By
	    // setting needle.originalColumn to 0, we thus find the last mapping for
	    // the given line, provided such a mapping exists.
	    var needle = {
	      source: util.getArg(aArgs, 'source'),
	      originalLine: line,
	      originalColumn: util.getArg(aArgs, 'column', 0)
	    };

	    needle.source = this._findSourceIndex(needle.source);
	    if (needle.source < 0) {
	      return [];
	    }

	    var mappings = [];

	    var index = this._findMapping(needle,
	                                  this._originalMappings,
	                                  "originalLine",
	                                  "originalColumn",
	                                  util.compareByOriginalPositions,
	                                  binarySearch.LEAST_UPPER_BOUND);
	    if (index >= 0) {
	      var mapping = this._originalMappings[index];

	      if (aArgs.column === undefined) {
	        var originalLine = mapping.originalLine;

	        // Iterate until either we run out of mappings, or we run into
	        // a mapping for a different line than the one we found. Since
	        // mappings are sorted, this is guaranteed to find all mappings for
	        // the line we found.
	        while (mapping && mapping.originalLine === originalLine) {
	          mappings.push({
	            line: util.getArg(mapping, 'generatedLine', null),
	            column: util.getArg(mapping, 'generatedColumn', null),
	            lastColumn: util.getArg(mapping, 'lastGeneratedColumn', null)
	          });

	          mapping = this._originalMappings[++index];
	        }
	      } else {
	        var originalColumn = mapping.originalColumn;

	        // Iterate until either we run out of mappings, or we run into
	        // a mapping for a different line than the one we were searching for.
	        // Since mappings are sorted, this is guaranteed to find all mappings for
	        // the line we are searching for.
	        while (mapping &&
	               mapping.originalLine === line &&
	               mapping.originalColumn == originalColumn) {
	          mappings.push({
	            line: util.getArg(mapping, 'generatedLine', null),
	            column: util.getArg(mapping, 'generatedColumn', null),
	            lastColumn: util.getArg(mapping, 'lastGeneratedColumn', null)
	          });

	          mapping = this._originalMappings[++index];
	        }
	      }
	    }

	    return mappings;
	  };

	sourceMapConsumer.SourceMapConsumer = SourceMapConsumer;

	/**
	 * A BasicSourceMapConsumer instance represents a parsed source map which we can
	 * query for information about the original file positions by giving it a file
	 * position in the generated source.
	 *
	 * The first parameter is the raw source map (either as a JSON string, or
	 * already parsed to an object). According to the spec, source maps have the
	 * following attributes:
	 *
	 *   - version: Which version of the source map spec this map is following.
	 *   - sources: An array of URLs to the original source files.
	 *   - names: An array of identifiers which can be referrenced by individual mappings.
	 *   - sourceRoot: Optional. The URL root from which all sources are relative.
	 *   - sourcesContent: Optional. An array of contents of the original source files.
	 *   - mappings: A string of base64 VLQs which contain the actual mappings.
	 *   - file: Optional. The generated file this source map is associated with.
	 *
	 * Here is an example source map, taken from the source map spec[0]:
	 *
	 *     {
	 *       version : 3,
	 *       file: "out.js",
	 *       sourceRoot : "",
	 *       sources: ["foo.js", "bar.js"],
	 *       names: ["src", "maps", "are", "fun"],
	 *       mappings: "AA,AB;;ABCDE;"
	 *     }
	 *
	 * The second parameter, if given, is a string whose value is the URL
	 * at which the source map was found.  This URL is used to compute the
	 * sources array.
	 *
	 * [0]: https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit?pli=1#
	 */
	function BasicSourceMapConsumer(aSourceMap, aSourceMapURL) {
	  var sourceMap = aSourceMap;
	  if (typeof aSourceMap === 'string') {
	    sourceMap = util.parseSourceMapInput(aSourceMap);
	  }

	  var version = util.getArg(sourceMap, 'version');
	  var sources = util.getArg(sourceMap, 'sources');
	  // Sass 3.3 leaves out the 'names' array, so we deviate from the spec (which
	  // requires the array) to play nice here.
	  var names = util.getArg(sourceMap, 'names', []);
	  var sourceRoot = util.getArg(sourceMap, 'sourceRoot', null);
	  var sourcesContent = util.getArg(sourceMap, 'sourcesContent', null);
	  var mappings = util.getArg(sourceMap, 'mappings');
	  var file = util.getArg(sourceMap, 'file', null);

	  // Once again, Sass deviates from the spec and supplies the version as a
	  // string rather than a number, so we use loose equality checking here.
	  if (version != this._version) {
	    throw new Error('Unsupported version: ' + version);
	  }

	  if (sourceRoot) {
	    sourceRoot = util.normalize(sourceRoot);
	  }

	  sources = sources
	    .map(String)
	    // Some source maps produce relative source paths like "./foo.js" instead of
	    // "foo.js".  Normalize these first so that future comparisons will succeed.
	    // See bugzil.la/1090768.
	    .map(util.normalize)
	    // Always ensure that absolute sources are internally stored relative to
	    // the source root, if the source root is absolute. Not doing this would
	    // be particularly problematic when the source root is a prefix of the
	    // source (valid, but why??). See github issue #199 and bugzil.la/1188982.
	    .map(function (source) {
	      return sourceRoot && util.isAbsolute(sourceRoot) && util.isAbsolute(source)
	        ? util.relative(sourceRoot, source)
	        : source;
	    });

	  // Pass `true` below to allow duplicate names and sources. While source maps
	  // are intended to be compressed and deduplicated, the TypeScript compiler
	  // sometimes generates source maps with duplicates in them. See Github issue
	  // #72 and bugzil.la/889492.
	  this._names = ArraySet.fromArray(names.map(String), true);
	  this._sources = ArraySet.fromArray(sources, true);

	  this._absoluteSources = this._sources.toArray().map(function (s) {
	    return util.computeSourceURL(sourceRoot, s, aSourceMapURL);
	  });

	  this.sourceRoot = sourceRoot;
	  this.sourcesContent = sourcesContent;
	  this._mappings = mappings;
	  this._sourceMapURL = aSourceMapURL;
	  this.file = file;
	}

	BasicSourceMapConsumer.prototype = Object.create(SourceMapConsumer.prototype);
	BasicSourceMapConsumer.prototype.consumer = SourceMapConsumer;

	/**
	 * Utility function to find the index of a source.  Returns -1 if not
	 * found.
	 */
	BasicSourceMapConsumer.prototype._findSourceIndex = function(aSource) {
	  var relativeSource = aSource;
	  if (this.sourceRoot != null) {
	    relativeSource = util.relative(this.sourceRoot, relativeSource);
	  }

	  if (this._sources.has(relativeSource)) {
	    return this._sources.indexOf(relativeSource);
	  }

	  // Maybe aSource is an absolute URL as returned by |sources|.  In
	  // this case we can't simply undo the transform.
	  var i;
	  for (i = 0; i < this._absoluteSources.length; ++i) {
	    if (this._absoluteSources[i] == aSource) {
	      return i;
	    }
	  }

	  return -1;
	};

	/**
	 * Create a BasicSourceMapConsumer from a SourceMapGenerator.
	 *
	 * @param SourceMapGenerator aSourceMap
	 *        The source map that will be consumed.
	 * @param String aSourceMapURL
	 *        The URL at which the source map can be found (optional)
	 * @returns BasicSourceMapConsumer
	 */
	BasicSourceMapConsumer.fromSourceMap =
	  function SourceMapConsumer_fromSourceMap(aSourceMap, aSourceMapURL) {
	    var smc = Object.create(BasicSourceMapConsumer.prototype);

	    var names = smc._names = ArraySet.fromArray(aSourceMap._names.toArray(), true);
	    var sources = smc._sources = ArraySet.fromArray(aSourceMap._sources.toArray(), true);
	    smc.sourceRoot = aSourceMap._sourceRoot;
	    smc.sourcesContent = aSourceMap._generateSourcesContent(smc._sources.toArray(),
	                                                            smc.sourceRoot);
	    smc.file = aSourceMap._file;
	    smc._sourceMapURL = aSourceMapURL;
	    smc._absoluteSources = smc._sources.toArray().map(function (s) {
	      return util.computeSourceURL(smc.sourceRoot, s, aSourceMapURL);
	    });

	    // Because we are modifying the entries (by converting string sources and
	    // names to indices into the sources and names ArraySets), we have to make
	    // a copy of the entry or else bad things happen. Shared mutable state
	    // strikes again! See github issue #191.

	    var generatedMappings = aSourceMap._mappings.toArray().slice();
	    var destGeneratedMappings = smc.__generatedMappings = [];
	    var destOriginalMappings = smc.__originalMappings = [];

	    for (var i = 0, length = generatedMappings.length; i < length; i++) {
	      var srcMapping = generatedMappings[i];
	      var destMapping = new Mapping;
	      destMapping.generatedLine = srcMapping.generatedLine;
	      destMapping.generatedColumn = srcMapping.generatedColumn;

	      if (srcMapping.source) {
	        destMapping.source = sources.indexOf(srcMapping.source);
	        destMapping.originalLine = srcMapping.originalLine;
	        destMapping.originalColumn = srcMapping.originalColumn;

	        if (srcMapping.name) {
	          destMapping.name = names.indexOf(srcMapping.name);
	        }

	        destOriginalMappings.push(destMapping);
	      }

	      destGeneratedMappings.push(destMapping);
	    }

	    quickSort(smc.__originalMappings, util.compareByOriginalPositions);

	    return smc;
	  };

	/**
	 * The version of the source mapping spec that we are consuming.
	 */
	BasicSourceMapConsumer.prototype._version = 3;

	/**
	 * The list of original sources.
	 */
	Object.defineProperty(BasicSourceMapConsumer.prototype, 'sources', {
	  get: function () {
	    return this._absoluteSources.slice();
	  }
	});

	/**
	 * Provide the JIT with a nice shape / hidden class.
	 */
	function Mapping() {
	  this.generatedLine = 0;
	  this.generatedColumn = 0;
	  this.source = null;
	  this.originalLine = null;
	  this.originalColumn = null;
	  this.name = null;
	}

	/**
	 * Parse the mappings in a string in to a data structure which we can easily
	 * query (the ordered arrays in the `this.__generatedMappings` and
	 * `this.__originalMappings` properties).
	 */

	const compareGenerated = util.compareByGeneratedPositionsDeflatedNoLine;
	function sortGenerated(array, start) {
	  let l = array.length;
	  let n = array.length - start;
	  if (n <= 1) {
	    return;
	  } else if (n == 2) {
	    let a = array[start];
	    let b = array[start + 1];
	    if (compareGenerated(a, b) > 0) {
	      array[start] = b;
	      array[start + 1] = a;
	    }
	  } else if (n < 20) {
	    for (let i = start; i < l; i++) {
	      for (let j = i; j > start; j--) {
	        let a = array[j - 1];
	        let b = array[j];
	        if (compareGenerated(a, b) <= 0) {
	          break;
	        }
	        array[j - 1] = b;
	        array[j] = a;
	      }
	    }
	  } else {
	    quickSort(array, compareGenerated, start);
	  }
	}
	BasicSourceMapConsumer.prototype._parseMappings =
	  function SourceMapConsumer_parseMappings(aStr, aSourceRoot) {
	    var generatedLine = 1;
	    var previousGeneratedColumn = 0;
	    var previousOriginalLine = 0;
	    var previousOriginalColumn = 0;
	    var previousSource = 0;
	    var previousName = 0;
	    var length = aStr.length;
	    var index = 0;
	    var temp = {};
	    var originalMappings = [];
	    var generatedMappings = [];
	    var mapping, segment, end, value;

	    let subarrayStart = 0;
	    while (index < length) {
	      if (aStr.charAt(index) === ';') {
	        generatedLine++;
	        index++;
	        previousGeneratedColumn = 0;

	        sortGenerated(generatedMappings, subarrayStart);
	        subarrayStart = generatedMappings.length;
	      }
	      else if (aStr.charAt(index) === ',') {
	        index++;
	      }
	      else {
	        mapping = new Mapping();
	        mapping.generatedLine = generatedLine;

	        for (end = index; end < length; end++) {
	          if (this._charIsMappingSeparator(aStr, end)) {
	            break;
	          }
	        }
	        aStr.slice(index, end);

	        segment = [];
	        while (index < end) {
	          base64VLQ.decode(aStr, index, temp);
	          value = temp.value;
	          index = temp.rest;
	          segment.push(value);
	        }

	        if (segment.length === 2) {
	          throw new Error('Found a source, but no line and column');
	        }

	        if (segment.length === 3) {
	          throw new Error('Found a source and line, but no column');
	        }

	        // Generated column.
	        mapping.generatedColumn = previousGeneratedColumn + segment[0];
	        previousGeneratedColumn = mapping.generatedColumn;

	        if (segment.length > 1) {
	          // Original source.
	          mapping.source = previousSource + segment[1];
	          previousSource += segment[1];

	          // Original line.
	          mapping.originalLine = previousOriginalLine + segment[2];
	          previousOriginalLine = mapping.originalLine;
	          // Lines are stored 0-based
	          mapping.originalLine += 1;

	          // Original column.
	          mapping.originalColumn = previousOriginalColumn + segment[3];
	          previousOriginalColumn = mapping.originalColumn;

	          if (segment.length > 4) {
	            // Original name.
	            mapping.name = previousName + segment[4];
	            previousName += segment[4];
	          }
	        }

	        generatedMappings.push(mapping);
	        if (typeof mapping.originalLine === 'number') {
	          let currentSource = mapping.source;
	          while (originalMappings.length <= currentSource) {
	            originalMappings.push(null);
	          }
	          if (originalMappings[currentSource] === null) {
	            originalMappings[currentSource] = [];
	          }
	          originalMappings[currentSource].push(mapping);
	        }
	      }
	    }

	    sortGenerated(generatedMappings, subarrayStart);
	    this.__generatedMappings = generatedMappings;

	    for (var i = 0; i < originalMappings.length; i++) {
	      if (originalMappings[i] != null) {
	        quickSort(originalMappings[i], util.compareByOriginalPositionsNoSource);
	      }
	    }
	    this.__originalMappings = [].concat(...originalMappings);
	  };

	/**
	 * Find the mapping that best matches the hypothetical "needle" mapping that
	 * we are searching for in the given "haystack" of mappings.
	 */
	BasicSourceMapConsumer.prototype._findMapping =
	  function SourceMapConsumer_findMapping(aNeedle, aMappings, aLineName,
	                                         aColumnName, aComparator, aBias) {
	    // To return the position we are searching for, we must first find the
	    // mapping for the given position and then return the opposite position it
	    // points to. Because the mappings are sorted, we can use binary search to
	    // find the best mapping.

	    if (aNeedle[aLineName] <= 0) {
	      throw new TypeError('Line must be greater than or equal to 1, got '
	                          + aNeedle[aLineName]);
	    }
	    if (aNeedle[aColumnName] < 0) {
	      throw new TypeError('Column must be greater than or equal to 0, got '
	                          + aNeedle[aColumnName]);
	    }

	    return binarySearch.search(aNeedle, aMappings, aComparator, aBias);
	  };

	/**
	 * Compute the last column for each generated mapping. The last column is
	 * inclusive.
	 */
	BasicSourceMapConsumer.prototype.computeColumnSpans =
	  function SourceMapConsumer_computeColumnSpans() {
	    for (var index = 0; index < this._generatedMappings.length; ++index) {
	      var mapping = this._generatedMappings[index];

	      // Mappings do not contain a field for the last generated columnt. We
	      // can come up with an optimistic estimate, however, by assuming that
	      // mappings are contiguous (i.e. given two consecutive mappings, the
	      // first mapping ends where the second one starts).
	      if (index + 1 < this._generatedMappings.length) {
	        var nextMapping = this._generatedMappings[index + 1];

	        if (mapping.generatedLine === nextMapping.generatedLine) {
	          mapping.lastGeneratedColumn = nextMapping.generatedColumn - 1;
	          continue;
	        }
	      }

	      // The last mapping for each line spans the entire line.
	      mapping.lastGeneratedColumn = Infinity;
	    }
	  };

	/**
	 * Returns the original source, line, and column information for the generated
	 * source's line and column positions provided. The only argument is an object
	 * with the following properties:
	 *
	 *   - line: The line number in the generated source.  The line number
	 *     is 1-based.
	 *   - column: The column number in the generated source.  The column
	 *     number is 0-based.
	 *   - bias: Either 'SourceMapConsumer.GREATEST_LOWER_BOUND' or
	 *     'SourceMapConsumer.LEAST_UPPER_BOUND'. Specifies whether to return the
	 *     closest element that is smaller than or greater than the one we are
	 *     searching for, respectively, if the exact element cannot be found.
	 *     Defaults to 'SourceMapConsumer.GREATEST_LOWER_BOUND'.
	 *
	 * and an object is returned with the following properties:
	 *
	 *   - source: The original source file, or null.
	 *   - line: The line number in the original source, or null.  The
	 *     line number is 1-based.
	 *   - column: The column number in the original source, or null.  The
	 *     column number is 0-based.
	 *   - name: The original identifier, or null.
	 */
	BasicSourceMapConsumer.prototype.originalPositionFor =
	  function SourceMapConsumer_originalPositionFor(aArgs) {
	    var needle = {
	      generatedLine: util.getArg(aArgs, 'line'),
	      generatedColumn: util.getArg(aArgs, 'column')
	    };

	    var index = this._findMapping(
	      needle,
	      this._generatedMappings,
	      "generatedLine",
	      "generatedColumn",
	      util.compareByGeneratedPositionsDeflated,
	      util.getArg(aArgs, 'bias', SourceMapConsumer.GREATEST_LOWER_BOUND)
	    );

	    if (index >= 0) {
	      var mapping = this._generatedMappings[index];

	      if (mapping.generatedLine === needle.generatedLine) {
	        var source = util.getArg(mapping, 'source', null);
	        if (source !== null) {
	          source = this._sources.at(source);
	          source = util.computeSourceURL(this.sourceRoot, source, this._sourceMapURL);
	        }
	        var name = util.getArg(mapping, 'name', null);
	        if (name !== null) {
	          name = this._names.at(name);
	        }
	        return {
	          source: source,
	          line: util.getArg(mapping, 'originalLine', null),
	          column: util.getArg(mapping, 'originalColumn', null),
	          name: name
	        };
	      }
	    }

	    return {
	      source: null,
	      line: null,
	      column: null,
	      name: null
	    };
	  };

	/**
	 * Return true if we have the source content for every source in the source
	 * map, false otherwise.
	 */
	BasicSourceMapConsumer.prototype.hasContentsOfAllSources =
	  function BasicSourceMapConsumer_hasContentsOfAllSources() {
	    if (!this.sourcesContent) {
	      return false;
	    }
	    return this.sourcesContent.length >= this._sources.size() &&
	      !this.sourcesContent.some(function (sc) { return sc == null; });
	  };

	/**
	 * Returns the original source content. The only argument is the url of the
	 * original source file. Returns null if no original source content is
	 * available.
	 */
	BasicSourceMapConsumer.prototype.sourceContentFor =
	  function SourceMapConsumer_sourceContentFor(aSource, nullOnMissing) {
	    if (!this.sourcesContent) {
	      return null;
	    }

	    var index = this._findSourceIndex(aSource);
	    if (index >= 0) {
	      return this.sourcesContent[index];
	    }

	    var relativeSource = aSource;
	    if (this.sourceRoot != null) {
	      relativeSource = util.relative(this.sourceRoot, relativeSource);
	    }

	    var url;
	    if (this.sourceRoot != null
	        && (url = util.urlParse(this.sourceRoot))) {
	      // XXX: file:// URIs and absolute paths lead to unexpected behavior for
	      // many users. We can help them out when they expect file:// URIs to
	      // behave like it would if they were running a local HTTP server. See
	      // https://bugzilla.mozilla.org/show_bug.cgi?id=885597.
	      var fileUriAbsPath = relativeSource.replace(/^file:\/\//, "");
	      if (url.scheme == "file"
	          && this._sources.has(fileUriAbsPath)) {
	        return this.sourcesContent[this._sources.indexOf(fileUriAbsPath)]
	      }

	      if ((!url.path || url.path == "/")
	          && this._sources.has("/" + relativeSource)) {
	        return this.sourcesContent[this._sources.indexOf("/" + relativeSource)];
	      }
	    }

	    // This function is used recursively from
	    // IndexedSourceMapConsumer.prototype.sourceContentFor. In that case, we
	    // don't want to throw if we can't find the source - we just want to
	    // return null, so we provide a flag to exit gracefully.
	    if (nullOnMissing) {
	      return null;
	    }
	    else {
	      throw new Error('"' + relativeSource + '" is not in the SourceMap.');
	    }
	  };

	/**
	 * Returns the generated line and column information for the original source,
	 * line, and column positions provided. The only argument is an object with
	 * the following properties:
	 *
	 *   - source: The filename of the original source.
	 *   - line: The line number in the original source.  The line number
	 *     is 1-based.
	 *   - column: The column number in the original source.  The column
	 *     number is 0-based.
	 *   - bias: Either 'SourceMapConsumer.GREATEST_LOWER_BOUND' or
	 *     'SourceMapConsumer.LEAST_UPPER_BOUND'. Specifies whether to return the
	 *     closest element that is smaller than or greater than the one we are
	 *     searching for, respectively, if the exact element cannot be found.
	 *     Defaults to 'SourceMapConsumer.GREATEST_LOWER_BOUND'.
	 *
	 * and an object is returned with the following properties:
	 *
	 *   - line: The line number in the generated source, or null.  The
	 *     line number is 1-based.
	 *   - column: The column number in the generated source, or null.
	 *     The column number is 0-based.
	 */
	BasicSourceMapConsumer.prototype.generatedPositionFor =
	  function SourceMapConsumer_generatedPositionFor(aArgs) {
	    var source = util.getArg(aArgs, 'source');
	    source = this._findSourceIndex(source);
	    if (source < 0) {
	      return {
	        line: null,
	        column: null,
	        lastColumn: null
	      };
	    }

	    var needle = {
	      source: source,
	      originalLine: util.getArg(aArgs, 'line'),
	      originalColumn: util.getArg(aArgs, 'column')
	    };

	    var index = this._findMapping(
	      needle,
	      this._originalMappings,
	      "originalLine",
	      "originalColumn",
	      util.compareByOriginalPositions,
	      util.getArg(aArgs, 'bias', SourceMapConsumer.GREATEST_LOWER_BOUND)
	    );

	    if (index >= 0) {
	      var mapping = this._originalMappings[index];

	      if (mapping.source === needle.source) {
	        return {
	          line: util.getArg(mapping, 'generatedLine', null),
	          column: util.getArg(mapping, 'generatedColumn', null),
	          lastColumn: util.getArg(mapping, 'lastGeneratedColumn', null)
	        };
	      }
	    }

	    return {
	      line: null,
	      column: null,
	      lastColumn: null
	    };
	  };

	sourceMapConsumer.BasicSourceMapConsumer = BasicSourceMapConsumer;

	/**
	 * An IndexedSourceMapConsumer instance represents a parsed source map which
	 * we can query for information. It differs from BasicSourceMapConsumer in
	 * that it takes "indexed" source maps (i.e. ones with a "sections" field) as
	 * input.
	 *
	 * The first parameter is a raw source map (either as a JSON string, or already
	 * parsed to an object). According to the spec for indexed source maps, they
	 * have the following attributes:
	 *
	 *   - version: Which version of the source map spec this map is following.
	 *   - file: Optional. The generated file this source map is associated with.
	 *   - sections: A list of section definitions.
	 *
	 * Each value under the "sections" field has two fields:
	 *   - offset: The offset into the original specified at which this section
	 *       begins to apply, defined as an object with a "line" and "column"
	 *       field.
	 *   - map: A source map definition. This source map could also be indexed,
	 *       but doesn't have to be.
	 *
	 * Instead of the "map" field, it's also possible to have a "url" field
	 * specifying a URL to retrieve a source map from, but that's currently
	 * unsupported.
	 *
	 * Here's an example source map, taken from the source map spec[0], but
	 * modified to omit a section which uses the "url" field.
	 *
	 *  {
	 *    version : 3,
	 *    file: "app.js",
	 *    sections: [{
	 *      offset: {line:100, column:10},
	 *      map: {
	 *        version : 3,
	 *        file: "section.js",
	 *        sources: ["foo.js", "bar.js"],
	 *        names: ["src", "maps", "are", "fun"],
	 *        mappings: "AAAA,E;;ABCDE;"
	 *      }
	 *    }],
	 *  }
	 *
	 * The second parameter, if given, is a string whose value is the URL
	 * at which the source map was found.  This URL is used to compute the
	 * sources array.
	 *
	 * [0]: https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit#heading=h.535es3xeprgt
	 */
	function IndexedSourceMapConsumer(aSourceMap, aSourceMapURL) {
	  var sourceMap = aSourceMap;
	  if (typeof aSourceMap === 'string') {
	    sourceMap = util.parseSourceMapInput(aSourceMap);
	  }

	  var version = util.getArg(sourceMap, 'version');
	  var sections = util.getArg(sourceMap, 'sections');

	  if (version != this._version) {
	    throw new Error('Unsupported version: ' + version);
	  }

	  this._sources = new ArraySet();
	  this._names = new ArraySet();

	  var lastOffset = {
	    line: -1,
	    column: 0
	  };
	  this._sections = sections.map(function (s) {
	    if (s.url) {
	      // The url field will require support for asynchronicity.
	      // See https://github.com/mozilla/source-map/issues/16
	      throw new Error('Support for url field in sections not implemented.');
	    }
	    var offset = util.getArg(s, 'offset');
	    var offsetLine = util.getArg(offset, 'line');
	    var offsetColumn = util.getArg(offset, 'column');

	    if (offsetLine < lastOffset.line ||
	        (offsetLine === lastOffset.line && offsetColumn < lastOffset.column)) {
	      throw new Error('Section offsets must be ordered and non-overlapping.');
	    }
	    lastOffset = offset;

	    return {
	      generatedOffset: {
	        // The offset fields are 0-based, but we use 1-based indices when
	        // encoding/decoding from VLQ.
	        generatedLine: offsetLine + 1,
	        generatedColumn: offsetColumn + 1
	      },
	      consumer: new SourceMapConsumer(util.getArg(s, 'map'), aSourceMapURL)
	    }
	  });
	}

	IndexedSourceMapConsumer.prototype = Object.create(SourceMapConsumer.prototype);
	IndexedSourceMapConsumer.prototype.constructor = SourceMapConsumer;

	/**
	 * The version of the source mapping spec that we are consuming.
	 */
	IndexedSourceMapConsumer.prototype._version = 3;

	/**
	 * The list of original sources.
	 */
	Object.defineProperty(IndexedSourceMapConsumer.prototype, 'sources', {
	  get: function () {
	    var sources = [];
	    for (var i = 0; i < this._sections.length; i++) {
	      for (var j = 0; j < this._sections[i].consumer.sources.length; j++) {
	        sources.push(this._sections[i].consumer.sources[j]);
	      }
	    }
	    return sources;
	  }
	});

	/**
	 * Returns the original source, line, and column information for the generated
	 * source's line and column positions provided. The only argument is an object
	 * with the following properties:
	 *
	 *   - line: The line number in the generated source.  The line number
	 *     is 1-based.
	 *   - column: The column number in the generated source.  The column
	 *     number is 0-based.
	 *
	 * and an object is returned with the following properties:
	 *
	 *   - source: The original source file, or null.
	 *   - line: The line number in the original source, or null.  The
	 *     line number is 1-based.
	 *   - column: The column number in the original source, or null.  The
	 *     column number is 0-based.
	 *   - name: The original identifier, or null.
	 */
	IndexedSourceMapConsumer.prototype.originalPositionFor =
	  function IndexedSourceMapConsumer_originalPositionFor(aArgs) {
	    var needle = {
	      generatedLine: util.getArg(aArgs, 'line'),
	      generatedColumn: util.getArg(aArgs, 'column')
	    };

	    // Find the section containing the generated position we're trying to map
	    // to an original position.
	    var sectionIndex = binarySearch.search(needle, this._sections,
	      function(needle, section) {
	        var cmp = needle.generatedLine - section.generatedOffset.generatedLine;
	        if (cmp) {
	          return cmp;
	        }

	        return (needle.generatedColumn -
	                section.generatedOffset.generatedColumn);
	      });
	    var section = this._sections[sectionIndex];

	    if (!section) {
	      return {
	        source: null,
	        line: null,
	        column: null,
	        name: null
	      };
	    }

	    return section.consumer.originalPositionFor({
	      line: needle.generatedLine -
	        (section.generatedOffset.generatedLine - 1),
	      column: needle.generatedColumn -
	        (section.generatedOffset.generatedLine === needle.generatedLine
	         ? section.generatedOffset.generatedColumn - 1
	         : 0),
	      bias: aArgs.bias
	    });
	  };

	/**
	 * Return true if we have the source content for every source in the source
	 * map, false otherwise.
	 */
	IndexedSourceMapConsumer.prototype.hasContentsOfAllSources =
	  function IndexedSourceMapConsumer_hasContentsOfAllSources() {
	    return this._sections.every(function (s) {
	      return s.consumer.hasContentsOfAllSources();
	    });
	  };

	/**
	 * Returns the original source content. The only argument is the url of the
	 * original source file. Returns null if no original source content is
	 * available.
	 */
	IndexedSourceMapConsumer.prototype.sourceContentFor =
	  function IndexedSourceMapConsumer_sourceContentFor(aSource, nullOnMissing) {
	    for (var i = 0; i < this._sections.length; i++) {
	      var section = this._sections[i];

	      var content = section.consumer.sourceContentFor(aSource, true);
	      if (content || content === '') {
	        return content;
	      }
	    }
	    if (nullOnMissing) {
	      return null;
	    }
	    else {
	      throw new Error('"' + aSource + '" is not in the SourceMap.');
	    }
	  };

	/**
	 * Returns the generated line and column information for the original source,
	 * line, and column positions provided. The only argument is an object with
	 * the following properties:
	 *
	 *   - source: The filename of the original source.
	 *   - line: The line number in the original source.  The line number
	 *     is 1-based.
	 *   - column: The column number in the original source.  The column
	 *     number is 0-based.
	 *
	 * and an object is returned with the following properties:
	 *
	 *   - line: The line number in the generated source, or null.  The
	 *     line number is 1-based. 
	 *   - column: The column number in the generated source, or null.
	 *     The column number is 0-based.
	 */
	IndexedSourceMapConsumer.prototype.generatedPositionFor =
	  function IndexedSourceMapConsumer_generatedPositionFor(aArgs) {
	    for (var i = 0; i < this._sections.length; i++) {
	      var section = this._sections[i];

	      // Only consider this section if the requested source is in the list of
	      // sources of the consumer.
	      if (section.consumer._findSourceIndex(util.getArg(aArgs, 'source')) === -1) {
	        continue;
	      }
	      var generatedPosition = section.consumer.generatedPositionFor(aArgs);
	      if (generatedPosition) {
	        var ret = {
	          line: generatedPosition.line +
	            (section.generatedOffset.generatedLine - 1),
	          column: generatedPosition.column +
	            (section.generatedOffset.generatedLine === generatedPosition.line
	             ? section.generatedOffset.generatedColumn - 1
	             : 0)
	        };
	        return ret;
	      }
	    }

	    return {
	      line: null,
	      column: null
	    };
	  };

	/**
	 * Parse the mappings in a string in to a data structure which we can easily
	 * query (the ordered arrays in the `this.__generatedMappings` and
	 * `this.__originalMappings` properties).
	 */
	IndexedSourceMapConsumer.prototype._parseMappings =
	  function IndexedSourceMapConsumer_parseMappings(aStr, aSourceRoot) {
	    this.__generatedMappings = [];
	    this.__originalMappings = [];
	    for (var i = 0; i < this._sections.length; i++) {
	      var section = this._sections[i];
	      var sectionMappings = section.consumer._generatedMappings;
	      for (var j = 0; j < sectionMappings.length; j++) {
	        var mapping = sectionMappings[j];

	        var source = section.consumer._sources.at(mapping.source);
	        if(source !== null) {
	          source = util.computeSourceURL(section.consumer.sourceRoot, source, this._sourceMapURL);
	        }
	        this._sources.add(source);
	        source = this._sources.indexOf(source);

	        var name = null;
	        if (mapping.name) {
	          name = section.consumer._names.at(mapping.name);
	          this._names.add(name);
	          name = this._names.indexOf(name);
	        }

	        // The mappings coming from the consumer for the section have
	        // generated positions relative to the start of the section, so we
	        // need to offset them to be relative to the start of the concatenated
	        // generated file.
	        var adjustedMapping = {
	          source: source,
	          generatedLine: mapping.generatedLine +
	            (section.generatedOffset.generatedLine - 1),
	          generatedColumn: mapping.generatedColumn +
	            (section.generatedOffset.generatedLine === mapping.generatedLine
	            ? section.generatedOffset.generatedColumn - 1
	            : 0),
	          originalLine: mapping.originalLine,
	          originalColumn: mapping.originalColumn,
	          name: name
	        };

	        this.__generatedMappings.push(adjustedMapping);
	        if (typeof adjustedMapping.originalLine === 'number') {
	          this.__originalMappings.push(adjustedMapping);
	        }
	      }
	    }

	    quickSort(this.__generatedMappings, util.compareByGeneratedPositionsDeflated);
	    quickSort(this.__originalMappings, util.compareByOriginalPositions);
	  };

	sourceMapConsumer.IndexedSourceMapConsumer = IndexedSourceMapConsumer;
	return sourceMapConsumer;
}

var sourceNode = {};

/* -*- Mode: js; js-indent-level: 2; -*- */

var hasRequiredSourceNode;

function requireSourceNode () {
	if (hasRequiredSourceNode) return sourceNode;
	hasRequiredSourceNode = 1;
	/*
	 * Copyright 2011 Mozilla Foundation and contributors
	 * Licensed under the New BSD license. See LICENSE or:
	 * http://opensource.org/licenses/BSD-3-Clause
	 */

	var SourceMapGenerator = requireSourceMapGenerator().SourceMapGenerator;
	var util = requireUtil();

	// Matches a Windows-style `\r\n` newline or a `\n` newline used by all other
	// operating systems these days (capturing the result).
	var REGEX_NEWLINE = /(\r?\n)/;

	// Newline character code for charCodeAt() comparisons
	var NEWLINE_CODE = 10;

	// Private symbol for identifying `SourceNode`s when multiple versions of
	// the source-map library are loaded. This MUST NOT CHANGE across
	// versions!
	var isSourceNode = "$$$isSourceNode$$$";

	/**
	 * SourceNodes provide a way to abstract over interpolating/concatenating
	 * snippets of generated JavaScript source code while maintaining the line and
	 * column information associated with the original source code.
	 *
	 * @param aLine The original line number.
	 * @param aColumn The original column number.
	 * @param aSource The original source's filename.
	 * @param aChunks Optional. An array of strings which are snippets of
	 *        generated JS, or other SourceNodes.
	 * @param aName The original identifier.
	 */
	function SourceNode(aLine, aColumn, aSource, aChunks, aName) {
	  this.children = [];
	  this.sourceContents = {};
	  this.line = aLine == null ? null : aLine;
	  this.column = aColumn == null ? null : aColumn;
	  this.source = aSource == null ? null : aSource;
	  this.name = aName == null ? null : aName;
	  this[isSourceNode] = true;
	  if (aChunks != null) this.add(aChunks);
	}

	/**
	 * Creates a SourceNode from generated code and a SourceMapConsumer.
	 *
	 * @param aGeneratedCode The generated code
	 * @param aSourceMapConsumer The SourceMap for the generated code
	 * @param aRelativePath Optional. The path that relative sources in the
	 *        SourceMapConsumer should be relative to.
	 */
	SourceNode.fromStringWithSourceMap =
	  function SourceNode_fromStringWithSourceMap(aGeneratedCode, aSourceMapConsumer, aRelativePath) {
	    // The SourceNode we want to fill with the generated code
	    // and the SourceMap
	    var node = new SourceNode();

	    // All even indices of this array are one line of the generated code,
	    // while all odd indices are the newlines between two adjacent lines
	    // (since `REGEX_NEWLINE` captures its match).
	    // Processed fragments are accessed by calling `shiftNextLine`.
	    var remainingLines = aGeneratedCode.split(REGEX_NEWLINE);
	    var remainingLinesIndex = 0;
	    var shiftNextLine = function() {
	      var lineContents = getNextLine();
	      // The last line of a file might not have a newline.
	      var newLine = getNextLine() || "";
	      return lineContents + newLine;

	      function getNextLine() {
	        return remainingLinesIndex < remainingLines.length ?
	            remainingLines[remainingLinesIndex++] : undefined;
	      }
	    };

	    // We need to remember the position of "remainingLines"
	    var lastGeneratedLine = 1, lastGeneratedColumn = 0;

	    // The generate SourceNodes we need a code range.
	    // To extract it current and last mapping is used.
	    // Here we store the last mapping.
	    var lastMapping = null;

	    aSourceMapConsumer.eachMapping(function (mapping) {
	      if (lastMapping !== null) {
	        // We add the code from "lastMapping" to "mapping":
	        // First check if there is a new line in between.
	        if (lastGeneratedLine < mapping.generatedLine) {
	          // Associate first line with "lastMapping"
	          addMappingWithCode(lastMapping, shiftNextLine());
	          lastGeneratedLine++;
	          lastGeneratedColumn = 0;
	          // The remaining code is added without mapping
	        } else {
	          // There is no new line in between.
	          // Associate the code between "lastGeneratedColumn" and
	          // "mapping.generatedColumn" with "lastMapping"
	          var nextLine = remainingLines[remainingLinesIndex] || '';
	          var code = nextLine.substr(0, mapping.generatedColumn -
	                                        lastGeneratedColumn);
	          remainingLines[remainingLinesIndex] = nextLine.substr(mapping.generatedColumn -
	                                              lastGeneratedColumn);
	          lastGeneratedColumn = mapping.generatedColumn;
	          addMappingWithCode(lastMapping, code);
	          // No more remaining code, continue
	          lastMapping = mapping;
	          return;
	        }
	      }
	      // We add the generated code until the first mapping
	      // to the SourceNode without any mapping.
	      // Each line is added as separate string.
	      while (lastGeneratedLine < mapping.generatedLine) {
	        node.add(shiftNextLine());
	        lastGeneratedLine++;
	      }
	      if (lastGeneratedColumn < mapping.generatedColumn) {
	        var nextLine = remainingLines[remainingLinesIndex] || '';
	        node.add(nextLine.substr(0, mapping.generatedColumn));
	        remainingLines[remainingLinesIndex] = nextLine.substr(mapping.generatedColumn);
	        lastGeneratedColumn = mapping.generatedColumn;
	      }
	      lastMapping = mapping;
	    }, this);
	    // We have processed all mappings.
	    if (remainingLinesIndex < remainingLines.length) {
	      if (lastMapping) {
	        // Associate the remaining code in the current line with "lastMapping"
	        addMappingWithCode(lastMapping, shiftNextLine());
	      }
	      // and add the remaining lines without any mapping
	      node.add(remainingLines.splice(remainingLinesIndex).join(""));
	    }

	    // Copy sourcesContent into SourceNode
	    aSourceMapConsumer.sources.forEach(function (sourceFile) {
	      var content = aSourceMapConsumer.sourceContentFor(sourceFile);
	      if (content != null) {
	        if (aRelativePath != null) {
	          sourceFile = util.join(aRelativePath, sourceFile);
	        }
	        node.setSourceContent(sourceFile, content);
	      }
	    });

	    return node;

	    function addMappingWithCode(mapping, code) {
	      if (mapping === null || mapping.source === undefined) {
	        node.add(code);
	      } else {
	        var source = aRelativePath
	          ? util.join(aRelativePath, mapping.source)
	          : mapping.source;
	        node.add(new SourceNode(mapping.originalLine,
	                                mapping.originalColumn,
	                                source,
	                                code,
	                                mapping.name));
	      }
	    }
	  };

	/**
	 * Add a chunk of generated JS to this source node.
	 *
	 * @param aChunk A string snippet of generated JS code, another instance of
	 *        SourceNode, or an array where each member is one of those things.
	 */
	SourceNode.prototype.add = function SourceNode_add(aChunk) {
	  if (Array.isArray(aChunk)) {
	    aChunk.forEach(function (chunk) {
	      this.add(chunk);
	    }, this);
	  }
	  else if (aChunk[isSourceNode] || typeof aChunk === "string") {
	    if (aChunk) {
	      this.children.push(aChunk);
	    }
	  }
	  else {
	    throw new TypeError(
	      "Expected a SourceNode, string, or an array of SourceNodes and strings. Got " + aChunk
	    );
	  }
	  return this;
	};

	/**
	 * Add a chunk of generated JS to the beginning of this source node.
	 *
	 * @param aChunk A string snippet of generated JS code, another instance of
	 *        SourceNode, or an array where each member is one of those things.
	 */
	SourceNode.prototype.prepend = function SourceNode_prepend(aChunk) {
	  if (Array.isArray(aChunk)) {
	    for (var i = aChunk.length-1; i >= 0; i--) {
	      this.prepend(aChunk[i]);
	    }
	  }
	  else if (aChunk[isSourceNode] || typeof aChunk === "string") {
	    this.children.unshift(aChunk);
	  }
	  else {
	    throw new TypeError(
	      "Expected a SourceNode, string, or an array of SourceNodes and strings. Got " + aChunk
	    );
	  }
	  return this;
	};

	/**
	 * Walk over the tree of JS snippets in this node and its children. The
	 * walking function is called once for each snippet of JS and is passed that
	 * snippet and the its original associated source's line/column location.
	 *
	 * @param aFn The traversal function.
	 */
	SourceNode.prototype.walk = function SourceNode_walk(aFn) {
	  var chunk;
	  for (var i = 0, len = this.children.length; i < len; i++) {
	    chunk = this.children[i];
	    if (chunk[isSourceNode]) {
	      chunk.walk(aFn);
	    }
	    else {
	      if (chunk !== '') {
	        aFn(chunk, { source: this.source,
	                     line: this.line,
	                     column: this.column,
	                     name: this.name });
	      }
	    }
	  }
	};

	/**
	 * Like `String.prototype.join` except for SourceNodes. Inserts `aStr` between
	 * each of `this.children`.
	 *
	 * @param aSep The separator.
	 */
	SourceNode.prototype.join = function SourceNode_join(aSep) {
	  var newChildren;
	  var i;
	  var len = this.children.length;
	  if (len > 0) {
	    newChildren = [];
	    for (i = 0; i < len-1; i++) {
	      newChildren.push(this.children[i]);
	      newChildren.push(aSep);
	    }
	    newChildren.push(this.children[i]);
	    this.children = newChildren;
	  }
	  return this;
	};

	/**
	 * Call String.prototype.replace on the very right-most source snippet. Useful
	 * for trimming whitespace from the end of a source node, etc.
	 *
	 * @param aPattern The pattern to replace.
	 * @param aReplacement The thing to replace the pattern with.
	 */
	SourceNode.prototype.replaceRight = function SourceNode_replaceRight(aPattern, aReplacement) {
	  var lastChild = this.children[this.children.length - 1];
	  if (lastChild[isSourceNode]) {
	    lastChild.replaceRight(aPattern, aReplacement);
	  }
	  else if (typeof lastChild === 'string') {
	    this.children[this.children.length - 1] = lastChild.replace(aPattern, aReplacement);
	  }
	  else {
	    this.children.push(''.replace(aPattern, aReplacement));
	  }
	  return this;
	};

	/**
	 * Set the source content for a source file. This will be added to the SourceMapGenerator
	 * in the sourcesContent field.
	 *
	 * @param aSourceFile The filename of the source file
	 * @param aSourceContent The content of the source file
	 */
	SourceNode.prototype.setSourceContent =
	  function SourceNode_setSourceContent(aSourceFile, aSourceContent) {
	    this.sourceContents[util.toSetString(aSourceFile)] = aSourceContent;
	  };

	/**
	 * Walk over the tree of SourceNodes. The walking function is called for each
	 * source file content and is passed the filename and source content.
	 *
	 * @param aFn The traversal function.
	 */
	SourceNode.prototype.walkSourceContents =
	  function SourceNode_walkSourceContents(aFn) {
	    for (var i = 0, len = this.children.length; i < len; i++) {
	      if (this.children[i][isSourceNode]) {
	        this.children[i].walkSourceContents(aFn);
	      }
	    }

	    var sources = Object.keys(this.sourceContents);
	    for (var i = 0, len = sources.length; i < len; i++) {
	      aFn(util.fromSetString(sources[i]), this.sourceContents[sources[i]]);
	    }
	  };

	/**
	 * Return the string representation of this source node. Walks over the tree
	 * and concatenates all the various snippets together to one string.
	 */
	SourceNode.prototype.toString = function SourceNode_toString() {
	  var str = "";
	  this.walk(function (chunk) {
	    str += chunk;
	  });
	  return str;
	};

	/**
	 * Returns the string representation of this source node along with a source
	 * map.
	 */
	SourceNode.prototype.toStringWithSourceMap = function SourceNode_toStringWithSourceMap(aArgs) {
	  var generated = {
	    code: "",
	    line: 1,
	    column: 0
	  };
	  var map = new SourceMapGenerator(aArgs);
	  var sourceMappingActive = false;
	  var lastOriginalSource = null;
	  var lastOriginalLine = null;
	  var lastOriginalColumn = null;
	  var lastOriginalName = null;
	  this.walk(function (chunk, original) {
	    generated.code += chunk;
	    if (original.source !== null
	        && original.line !== null
	        && original.column !== null) {
	      if(lastOriginalSource !== original.source
	         || lastOriginalLine !== original.line
	         || lastOriginalColumn !== original.column
	         || lastOriginalName !== original.name) {
	        map.addMapping({
	          source: original.source,
	          original: {
	            line: original.line,
	            column: original.column
	          },
	          generated: {
	            line: generated.line,
	            column: generated.column
	          },
	          name: original.name
	        });
	      }
	      lastOriginalSource = original.source;
	      lastOriginalLine = original.line;
	      lastOriginalColumn = original.column;
	      lastOriginalName = original.name;
	      sourceMappingActive = true;
	    } else if (sourceMappingActive) {
	      map.addMapping({
	        generated: {
	          line: generated.line,
	          column: generated.column
	        }
	      });
	      lastOriginalSource = null;
	      sourceMappingActive = false;
	    }
	    for (var idx = 0, length = chunk.length; idx < length; idx++) {
	      if (chunk.charCodeAt(idx) === NEWLINE_CODE) {
	        generated.line++;
	        generated.column = 0;
	        // Mappings end at eol
	        if (idx + 1 === length) {
	          lastOriginalSource = null;
	          sourceMappingActive = false;
	        } else if (sourceMappingActive) {
	          map.addMapping({
	            source: original.source,
	            original: {
	              line: original.line,
	              column: original.column
	            },
	            generated: {
	              line: generated.line,
	              column: generated.column
	            },
	            name: original.name
	          });
	        }
	      } else {
	        generated.column++;
	      }
	    }
	  });
	  this.walkSourceContents(function (sourceFile, sourceContent) {
	    map.setSourceContent(sourceFile, sourceContent);
	  });

	  return { code: generated.code, map: map };
	};

	sourceNode.SourceNode = SourceNode;
	return sourceNode;
}

/*
 * Copyright 2009-2011 Mozilla Foundation and contributors
 * Licensed under the New BSD license. See LICENSE.txt or:
 * http://opensource.org/licenses/BSD-3-Clause
 */

var hasRequiredSourceMap;

function requireSourceMap () {
	if (hasRequiredSourceMap) return sourceMap;
	hasRequiredSourceMap = 1;
	sourceMap.SourceMapGenerator = requireSourceMapGenerator().SourceMapGenerator;
	sourceMap.SourceMapConsumer = requireSourceMapConsumer().SourceMapConsumer;
	sourceMap.SourceNode = requireSourceNode().SourceNode;
	return sourceMap;
}

var nonSecure;
var hasRequiredNonSecure;

function requireNonSecure () {
	if (hasRequiredNonSecure) return nonSecure;
	hasRequiredNonSecure = 1;
	// This alphabet uses `A-Za-z0-9_-` symbols.
	// The order of characters is optimized for better gzip and brotli compression.
	// References to the same file (works both for gzip and brotli):
	// `'use`, `andom`, and `rict'`
	// References to the brotli default dictionary:
	// `-26T`, `1983`, `40px`, `75px`, `bush`, `jack`, `mind`, `very`, and `wolf`
	let urlAlphabet =
	  'useandom-26T198340PX75pxJACKVERYMINDBUSHWOLF_GQZbfghjklqvwyzrict';

	let customAlphabet = (alphabet, defaultSize = 21) => {
	  return (size = defaultSize) => {
	    let id = '';
	    // A compact alternative for `for (var i = 0; i < step; i++)`.
	    let i = size | 0;
	    while (i--) {
	      // `| 0` is more compact and faster than `Math.floor()`.
	      id += alphabet[(Math.random() * alphabet.length) | 0];
	    }
	    return id
	  }
	};

	let nanoid = (size = 21) => {
	  let id = '';
	  // A compact alternative for `for (var i = 0; i < step; i++)`.
	  let i = size | 0;
	  while (i--) {
	    // `| 0` is more compact and faster than `Math.floor()`.
	    id += urlAlphabet[(Math.random() * 64) | 0];
	  }
	  return id
	};

	nonSecure = { nanoid, customAlphabet };
	return nonSecure;
}

var previousMap;
var hasRequiredPreviousMap;

function requirePreviousMap () {
	if (hasRequiredPreviousMap) return previousMap;
	hasRequiredPreviousMap = 1;

	let { SourceMapConsumer, SourceMapGenerator } = requireSourceMap();
	let { existsSync, readFileSync } = require$$1;
	let { dirname, join } = require$$2;

	function fromBase64(str) {
	  if (Buffer) {
	    return Buffer.from(str, 'base64').toString()
	  } else {
	    /* c8 ignore next 2 */
	    return window.atob(str)
	  }
	}

	class PreviousMap {
	  constructor(css, opts) {
	    if (opts.map === false) return
	    this.loadAnnotation(css);
	    this.inline = this.startWith(this.annotation, 'data:');

	    let prev = opts.map ? opts.map.prev : undefined;
	    let text = this.loadMap(opts.from, prev);
	    if (!this.mapFile && opts.from) {
	      this.mapFile = opts.from;
	    }
	    if (this.mapFile) this.root = dirname(this.mapFile);
	    if (text) this.text = text;
	  }

	  consumer() {
	    if (!this.consumerCache) {
	      this.consumerCache = new SourceMapConsumer(this.text);
	    }
	    return this.consumerCache
	  }

	  decodeInline(text) {
	    let baseCharsetUri = /^data:application\/json;charset=utf-?8;base64,/;
	    let baseUri = /^data:application\/json;base64,/;
	    let charsetUri = /^data:application\/json;charset=utf-?8,/;
	    let uri = /^data:application\/json,/;

	    if (charsetUri.test(text) || uri.test(text)) {
	      return decodeURIComponent(text.substr(RegExp.lastMatch.length))
	    }

	    if (baseCharsetUri.test(text) || baseUri.test(text)) {
	      return fromBase64(text.substr(RegExp.lastMatch.length))
	    }

	    let encoding = text.match(/data:application\/json;([^,]+),/)[1];
	    throw new Error('Unsupported source map encoding ' + encoding)
	  }

	  getAnnotationURL(sourceMapString) {
	    return sourceMapString.replace(/^\/\*\s*# sourceMappingURL=/, '').trim()
	  }

	  isMap(map) {
	    if (typeof map !== 'object') return false
	    return (
	      typeof map.mappings === 'string' ||
	      typeof map._mappings === 'string' ||
	      Array.isArray(map.sections)
	    )
	  }

	  loadAnnotation(css) {
	    let comments = css.match(/\/\*\s*# sourceMappingURL=/gm);
	    if (!comments) return

	    // sourceMappingURLs from comments, strings, etc.
	    let start = css.lastIndexOf(comments.pop());
	    let end = css.indexOf('*/', start);

	    if (start > -1 && end > -1) {
	      // Locate the last sourceMappingURL to avoid pickin
	      this.annotation = this.getAnnotationURL(css.substring(start, end));
	    }
	  }

	  loadFile(path) {
	    this.root = dirname(path);
	    if (existsSync(path)) {
	      this.mapFile = path;
	      return readFileSync(path, 'utf-8').toString().trim()
	    }
	  }

	  loadMap(file, prev) {
	    if (prev === false) return false

	    if (prev) {
	      if (typeof prev === 'string') {
	        return prev
	      } else if (typeof prev === 'function') {
	        let prevPath = prev(file);
	        if (prevPath) {
	          let map = this.loadFile(prevPath);
	          if (!map) {
	            throw new Error(
	              'Unable to load previous source map: ' + prevPath.toString()
	            )
	          }
	          return map
	        }
	      } else if (prev instanceof SourceMapConsumer) {
	        return SourceMapGenerator.fromSourceMap(prev).toString()
	      } else if (prev instanceof SourceMapGenerator) {
	        return prev.toString()
	      } else if (this.isMap(prev)) {
	        return JSON.stringify(prev)
	      } else {
	        throw new Error(
	          'Unsupported previous source map format: ' + prev.toString()
	        )
	      }
	    } else if (this.inline) {
	      return this.decodeInline(this.annotation)
	    } else if (this.annotation) {
	      let map = this.annotation;
	      if (file) map = join(dirname(file), map);
	      return this.loadFile(map)
	    }
	  }

	  startWith(string, start) {
	    if (!string) return false
	    return string.substr(0, start.length) === start
	  }

	  withContent() {
	    return !!(
	      this.consumer().sourcesContent &&
	      this.consumer().sourcesContent.length > 0
	    )
	  }
	}

	previousMap = PreviousMap;
	PreviousMap.default = PreviousMap;
	return previousMap;
}

var input;
var hasRequiredInput;

function requireInput () {
	if (hasRequiredInput) return input;
	hasRequiredInput = 1;

	let { SourceMapConsumer, SourceMapGenerator } = requireSourceMap();
	let { fileURLToPath, pathToFileURL } = require$$1$1;
	let { isAbsolute, resolve } = require$$2;
	let { nanoid } = requireNonSecure();

	let terminalHighlight = requireTerminalHighlight();
	let CssSyntaxError = requireCssSyntaxError();
	let PreviousMap = requirePreviousMap();

	let fromOffsetCache = Symbol('fromOffsetCache');

	let sourceMapAvailable = Boolean(SourceMapConsumer && SourceMapGenerator);
	let pathAvailable = Boolean(resolve && isAbsolute);

	class Input {
	  constructor(css, opts = {}) {
	    if (
	      css === null ||
	      typeof css === 'undefined' ||
	      (typeof css === 'object' && !css.toString)
	    ) {
	      throw new Error(`PostCSS received ${css} instead of CSS string`)
	    }

	    this.css = css.toString();

	    if (this.css[0] === '\uFEFF' || this.css[0] === '\uFFFE') {
	      this.hasBOM = true;
	      this.css = this.css.slice(1);
	    } else {
	      this.hasBOM = false;
	    }

	    if (opts.from) {
	      if (
	        !pathAvailable ||
	        /^\w+:\/\//.test(opts.from) ||
	        isAbsolute(opts.from)
	      ) {
	        this.file = opts.from;
	      } else {
	        this.file = resolve(opts.from);
	      }
	    }

	    if (pathAvailable && sourceMapAvailable) {
	      let map = new PreviousMap(this.css, opts);
	      if (map.text) {
	        this.map = map;
	        let file = map.consumer().file;
	        if (!this.file && file) this.file = this.mapResolve(file);
	      }
	    }

	    if (!this.file) {
	      this.id = '<input css ' + nanoid(6) + '>';
	    }
	    if (this.map) this.map.file = this.from;
	  }

	  error(message, line, column, opts = {}) {
	    let result, endLine, endColumn;

	    if (line && typeof line === 'object') {
	      let start = line;
	      let end = column;
	      if (typeof start.offset === 'number') {
	        let pos = this.fromOffset(start.offset);
	        line = pos.line;
	        column = pos.col;
	      } else {
	        line = start.line;
	        column = start.column;
	      }
	      if (typeof end.offset === 'number') {
	        let pos = this.fromOffset(end.offset);
	        endLine = pos.line;
	        endColumn = pos.col;
	      } else {
	        endLine = end.line;
	        endColumn = end.column;
	      }
	    } else if (!column) {
	      let pos = this.fromOffset(line);
	      line = pos.line;
	      column = pos.col;
	    }

	    let origin = this.origin(line, column, endLine, endColumn);
	    if (origin) {
	      result = new CssSyntaxError(
	        message,
	        origin.endLine === undefined
	          ? origin.line
	          : { column: origin.column, line: origin.line },
	        origin.endLine === undefined
	          ? origin.column
	          : { column: origin.endColumn, line: origin.endLine },
	        origin.source,
	        origin.file,
	        opts.plugin
	      );
	    } else {
	      result = new CssSyntaxError(
	        message,
	        endLine === undefined ? line : { column, line },
	        endLine === undefined ? column : { column: endColumn, line: endLine },
	        this.css,
	        this.file,
	        opts.plugin
	      );
	    }

	    result.input = { column, endColumn, endLine, line, source: this.css };
	    if (this.file) {
	      if (pathToFileURL) {
	        result.input.url = pathToFileURL(this.file).toString();
	      }
	      result.input.file = this.file;
	    }

	    return result
	  }

	  fromOffset(offset) {
	    let lastLine, lineToIndex;
	    if (!this[fromOffsetCache]) {
	      let lines = this.css.split('\n');
	      lineToIndex = new Array(lines.length);
	      let prevIndex = 0;

	      for (let i = 0, l = lines.length; i < l; i++) {
	        lineToIndex[i] = prevIndex;
	        prevIndex += lines[i].length + 1;
	      }

	      this[fromOffsetCache] = lineToIndex;
	    } else {
	      lineToIndex = this[fromOffsetCache];
	    }
	    lastLine = lineToIndex[lineToIndex.length - 1];

	    let min = 0;
	    if (offset >= lastLine) {
	      min = lineToIndex.length - 1;
	    } else {
	      let max = lineToIndex.length - 2;
	      let mid;
	      while (min < max) {
	        mid = min + ((max - min) >> 1);
	        if (offset < lineToIndex[mid]) {
	          max = mid - 1;
	        } else if (offset >= lineToIndex[mid + 1]) {
	          min = mid + 1;
	        } else {
	          min = mid;
	          break
	        }
	      }
	    }
	    return {
	      col: offset - lineToIndex[min] + 1,
	      line: min + 1
	    }
	  }

	  mapResolve(file) {
	    if (/^\w+:\/\//.test(file)) {
	      return file
	    }
	    return resolve(this.map.consumer().sourceRoot || this.map.root || '.', file)
	  }

	  origin(line, column, endLine, endColumn) {
	    if (!this.map) return false
	    let consumer = this.map.consumer();

	    let from = consumer.originalPositionFor({ column, line });
	    if (!from.source) return false

	    let to;
	    if (typeof endLine === 'number') {
	      to = consumer.originalPositionFor({ column: endColumn, line: endLine });
	    }

	    let fromUrl;

	    if (isAbsolute(from.source)) {
	      fromUrl = pathToFileURL(from.source);
	    } else {
	      fromUrl = new URL(
	        from.source,
	        this.map.consumer().sourceRoot || pathToFileURL(this.map.mapFile)
	      );
	    }

	    let result = {
	      column: from.column,
	      endColumn: to && to.column,
	      endLine: to && to.line,
	      line: from.line,
	      url: fromUrl.toString()
	    };

	    if (fromUrl.protocol === 'file:') {
	      if (fileURLToPath) {
	        result.file = fileURLToPath(fromUrl);
	      } else {
	        /* c8 ignore next 2 */
	        throw new Error(`file: protocol is not available in this PostCSS build`)
	      }
	    }

	    let source = consumer.sourceContentFor(from.source);
	    if (source) result.source = source;

	    return result
	  }

	  toJSON() {
	    let json = {};
	    for (let name of ['hasBOM', 'css', 'file', 'id']) {
	      if (this[name] != null) {
	        json[name] = this[name];
	      }
	    }
	    if (this.map) {
	      json.map = { ...this.map };
	      if (json.map.consumerCache) {
	        json.map.consumerCache = undefined;
	      }
	    }
	    return json
	  }

	  get from() {
	    return this.file || this.id
	  }
	}

	input = Input;
	Input.default = Input;

	if (terminalHighlight && terminalHighlight.registerInput) {
	  terminalHighlight.registerInput(Input);
	}
	return input;
}

var mapGenerator;
var hasRequiredMapGenerator;

function requireMapGenerator () {
	if (hasRequiredMapGenerator) return mapGenerator;
	hasRequiredMapGenerator = 1;

	let { SourceMapConsumer, SourceMapGenerator } = requireSourceMap();
	let { dirname, relative, resolve, sep } = require$$2;
	let { pathToFileURL } = require$$1$1;

	let Input = requireInput();

	let sourceMapAvailable = Boolean(SourceMapConsumer && SourceMapGenerator);
	let pathAvailable = Boolean(dirname && resolve && relative && sep);

	class MapGenerator {
	  constructor(stringify, root, opts, cssString) {
	    this.stringify = stringify;
	    this.mapOpts = opts.map || {};
	    this.root = root;
	    this.opts = opts;
	    this.css = cssString;
	    this.originalCSS = cssString;
	    this.usesFileUrls = !this.mapOpts.from && this.mapOpts.absolute;

	    this.memoizedFileURLs = new Map();
	    this.memoizedPaths = new Map();
	    this.memoizedURLs = new Map();
	  }

	  addAnnotation() {
	    let content;

	    if (this.isInline()) {
	      content =
	        'data:application/json;base64,' + this.toBase64(this.map.toString());
	    } else if (typeof this.mapOpts.annotation === 'string') {
	      content = this.mapOpts.annotation;
	    } else if (typeof this.mapOpts.annotation === 'function') {
	      content = this.mapOpts.annotation(this.opts.to, this.root);
	    } else {
	      content = this.outputFile() + '.map';
	    }
	    let eol = '\n';
	    if (this.css.includes('\r\n')) eol = '\r\n';

	    this.css += eol + '/*# sourceMappingURL=' + content + ' */';
	  }

	  applyPrevMaps() {
	    for (let prev of this.previous()) {
	      let from = this.toUrl(this.path(prev.file));
	      let root = prev.root || dirname(prev.file);
	      let map;

	      if (this.mapOpts.sourcesContent === false) {
	        map = new SourceMapConsumer(prev.text);
	        if (map.sourcesContent) {
	          map.sourcesContent = null;
	        }
	      } else {
	        map = prev.consumer();
	      }

	      this.map.applySourceMap(map, from, this.toUrl(this.path(root)));
	    }
	  }

	  clearAnnotation() {
	    if (this.mapOpts.annotation === false) return

	    if (this.root) {
	      let node;
	      for (let i = this.root.nodes.length - 1; i >= 0; i--) {
	        node = this.root.nodes[i];
	        if (node.type !== 'comment') continue
	        if (node.text.indexOf('# sourceMappingURL=') === 0) {
	          this.root.removeChild(i);
	        }
	      }
	    } else if (this.css) {
	      this.css = this.css.replace(/\n*?\/\*#[\S\s]*?\*\/$/gm, '');
	    }
	  }

	  generate() {
	    this.clearAnnotation();
	    if (pathAvailable && sourceMapAvailable && this.isMap()) {
	      return this.generateMap()
	    } else {
	      let result = '';
	      this.stringify(this.root, i => {
	        result += i;
	      });
	      return [result]
	    }
	  }

	  generateMap() {
	    if (this.root) {
	      this.generateString();
	    } else if (this.previous().length === 1) {
	      let prev = this.previous()[0].consumer();
	      prev.file = this.outputFile();
	      this.map = SourceMapGenerator.fromSourceMap(prev, {
	        ignoreInvalidMapping: true
	      });
	    } else {
	      this.map = new SourceMapGenerator({
	        file: this.outputFile(),
	        ignoreInvalidMapping: true
	      });
	      this.map.addMapping({
	        generated: { column: 0, line: 1 },
	        original: { column: 0, line: 1 },
	        source: this.opts.from
	          ? this.toUrl(this.path(this.opts.from))
	          : '<no source>'
	      });
	    }

	    if (this.isSourcesContent()) this.setSourcesContent();
	    if (this.root && this.previous().length > 0) this.applyPrevMaps();
	    if (this.isAnnotation()) this.addAnnotation();

	    if (this.isInline()) {
	      return [this.css]
	    } else {
	      return [this.css, this.map]
	    }
	  }

	  generateString() {
	    this.css = '';
	    this.map = new SourceMapGenerator({
	      file: this.outputFile(),
	      ignoreInvalidMapping: true
	    });

	    let line = 1;
	    let column = 1;

	    let noSource = '<no source>';
	    let mapping = {
	      generated: { column: 0, line: 0 },
	      original: { column: 0, line: 0 },
	      source: ''
	    };

	    let lines, last;
	    this.stringify(this.root, (str, node, type) => {
	      this.css += str;

	      if (node && type !== 'end') {
	        mapping.generated.line = line;
	        mapping.generated.column = column - 1;
	        if (node.source && node.source.start) {
	          mapping.source = this.sourcePath(node);
	          mapping.original.line = node.source.start.line;
	          mapping.original.column = node.source.start.column - 1;
	          this.map.addMapping(mapping);
	        } else {
	          mapping.source = noSource;
	          mapping.original.line = 1;
	          mapping.original.column = 0;
	          this.map.addMapping(mapping);
	        }
	      }

	      lines = str.match(/\n/g);
	      if (lines) {
	        line += lines.length;
	        last = str.lastIndexOf('\n');
	        column = str.length - last;
	      } else {
	        column += str.length;
	      }

	      if (node && type !== 'start') {
	        let p = node.parent || { raws: {} };
	        let childless =
	          node.type === 'decl' || (node.type === 'atrule' && !node.nodes);
	        if (!childless || node !== p.last || p.raws.semicolon) {
	          if (node.source && node.source.end) {
	            mapping.source = this.sourcePath(node);
	            mapping.original.line = node.source.end.line;
	            mapping.original.column = node.source.end.column - 1;
	            mapping.generated.line = line;
	            mapping.generated.column = column - 2;
	            this.map.addMapping(mapping);
	          } else {
	            mapping.source = noSource;
	            mapping.original.line = 1;
	            mapping.original.column = 0;
	            mapping.generated.line = line;
	            mapping.generated.column = column - 1;
	            this.map.addMapping(mapping);
	          }
	        }
	      }
	    });
	  }

	  isAnnotation() {
	    if (this.isInline()) {
	      return true
	    }
	    if (typeof this.mapOpts.annotation !== 'undefined') {
	      return this.mapOpts.annotation
	    }
	    if (this.previous().length) {
	      return this.previous().some(i => i.annotation)
	    }
	    return true
	  }

	  isInline() {
	    if (typeof this.mapOpts.inline !== 'undefined') {
	      return this.mapOpts.inline
	    }

	    let annotation = this.mapOpts.annotation;
	    if (typeof annotation !== 'undefined' && annotation !== true) {
	      return false
	    }

	    if (this.previous().length) {
	      return this.previous().some(i => i.inline)
	    }
	    return true
	  }

	  isMap() {
	    if (typeof this.opts.map !== 'undefined') {
	      return !!this.opts.map
	    }
	    return this.previous().length > 0
	  }

	  isSourcesContent() {
	    if (typeof this.mapOpts.sourcesContent !== 'undefined') {
	      return this.mapOpts.sourcesContent
	    }
	    if (this.previous().length) {
	      return this.previous().some(i => i.withContent())
	    }
	    return true
	  }

	  outputFile() {
	    if (this.opts.to) {
	      return this.path(this.opts.to)
	    } else if (this.opts.from) {
	      return this.path(this.opts.from)
	    } else {
	      return 'to.css'
	    }
	  }

	  path(file) {
	    if (this.mapOpts.absolute) return file
	    if (file.charCodeAt(0) === 60 /* `<` */) return file
	    if (/^\w+:\/\//.test(file)) return file
	    let cached = this.memoizedPaths.get(file);
	    if (cached) return cached

	    let from = this.opts.to ? dirname(this.opts.to) : '.';

	    if (typeof this.mapOpts.annotation === 'string') {
	      from = dirname(resolve(from, this.mapOpts.annotation));
	    }

	    let path = relative(from, file);
	    this.memoizedPaths.set(file, path);

	    return path
	  }

	  previous() {
	    if (!this.previousMaps) {
	      this.previousMaps = [];
	      if (this.root) {
	        this.root.walk(node => {
	          if (node.source && node.source.input.map) {
	            let map = node.source.input.map;
	            if (!this.previousMaps.includes(map)) {
	              this.previousMaps.push(map);
	            }
	          }
	        });
	      } else {
	        let input = new Input(this.originalCSS, this.opts);
	        if (input.map) this.previousMaps.push(input.map);
	      }
	    }

	    return this.previousMaps
	  }

	  setSourcesContent() {
	    let already = {};
	    if (this.root) {
	      this.root.walk(node => {
	        if (node.source) {
	          let from = node.source.input.from;
	          if (from && !already[from]) {
	            already[from] = true;
	            let fromUrl = this.usesFileUrls
	              ? this.toFileUrl(from)
	              : this.toUrl(this.path(from));
	            this.map.setSourceContent(fromUrl, node.source.input.css);
	          }
	        }
	      });
	    } else if (this.css) {
	      let from = this.opts.from
	        ? this.toUrl(this.path(this.opts.from))
	        : '<no source>';
	      this.map.setSourceContent(from, this.css);
	    }
	  }

	  sourcePath(node) {
	    if (this.mapOpts.from) {
	      return this.toUrl(this.mapOpts.from)
	    } else if (this.usesFileUrls) {
	      return this.toFileUrl(node.source.input.from)
	    } else {
	      return this.toUrl(this.path(node.source.input.from))
	    }
	  }

	  toBase64(str) {
	    if (Buffer) {
	      return Buffer.from(str).toString('base64')
	    } else {
	      return window.btoa(unescape(encodeURIComponent(str)))
	    }
	  }

	  toFileUrl(path) {
	    let cached = this.memoizedFileURLs.get(path);
	    if (cached) return cached

	    if (pathToFileURL) {
	      let fileURL = pathToFileURL(path).toString();
	      this.memoizedFileURLs.set(path, fileURL);

	      return fileURL
	    } else {
	      throw new Error(
	        '`map.absolute` option is not available in this PostCSS build'
	      )
	    }
	  }

	  toUrl(path) {
	    let cached = this.memoizedURLs.get(path);
	    if (cached) return cached

	    if (sep === '\\') {
	      path = path.replace(/\\/g, '/');
	    }

	    let url = encodeURI(path).replace(/[#?]/g, encodeURIComponent);
	    this.memoizedURLs.set(path, url);

	    return url
	  }
	}

	mapGenerator = MapGenerator;
	return mapGenerator;
}

var comment;
var hasRequiredComment;

function requireComment () {
	if (hasRequiredComment) return comment;
	hasRequiredComment = 1;

	let Node = requireNode();

	class Comment extends Node {
	  constructor(defaults) {
	    super(defaults);
	    this.type = 'comment';
	  }
	}

	comment = Comment;
	Comment.default = Comment;
	return comment;
}

var container;
var hasRequiredContainer;

function requireContainer () {
	if (hasRequiredContainer) return container;
	hasRequiredContainer = 1;

	let { isClean, my } = requireSymbols();
	let Declaration = requireDeclaration();
	let Comment = requireComment();
	let Node = requireNode();

	let parse, Rule, AtRule, Root;

	function cleanSource(nodes) {
	  return nodes.map(i => {
	    if (i.nodes) i.nodes = cleanSource(i.nodes);
	    delete i.source;
	    return i
	  })
	}

	function markDirtyUp(node) {
	  node[isClean] = false;
	  if (node.proxyOf.nodes) {
	    for (let i of node.proxyOf.nodes) {
	      markDirtyUp(i);
	    }
	  }
	}

	class Container extends Node {
	  append(...children) {
	    for (let child of children) {
	      let nodes = this.normalize(child, this.last);
	      for (let node of nodes) this.proxyOf.nodes.push(node);
	    }

	    this.markDirty();

	    return this
	  }

	  cleanRaws(keepBetween) {
	    super.cleanRaws(keepBetween);
	    if (this.nodes) {
	      for (let node of this.nodes) node.cleanRaws(keepBetween);
	    }
	  }

	  each(callback) {
	    if (!this.proxyOf.nodes) return undefined
	    let iterator = this.getIterator();

	    let index, result;
	    while (this.indexes[iterator] < this.proxyOf.nodes.length) {
	      index = this.indexes[iterator];
	      result = callback(this.proxyOf.nodes[index], index);
	      if (result === false) break

	      this.indexes[iterator] += 1;
	    }

	    delete this.indexes[iterator];
	    return result
	  }

	  every(condition) {
	    return this.nodes.every(condition)
	  }

	  getIterator() {
	    if (!this.lastEach) this.lastEach = 0;
	    if (!this.indexes) this.indexes = {};

	    this.lastEach += 1;
	    let iterator = this.lastEach;
	    this.indexes[iterator] = 0;

	    return iterator
	  }

	  getProxyProcessor() {
	    return {
	      get(node, prop) {
	        if (prop === 'proxyOf') {
	          return node
	        } else if (!node[prop]) {
	          return node[prop]
	        } else if (
	          prop === 'each' ||
	          (typeof prop === 'string' && prop.startsWith('walk'))
	        ) {
	          return (...args) => {
	            return node[prop](
	              ...args.map(i => {
	                if (typeof i === 'function') {
	                  return (child, index) => i(child.toProxy(), index)
	                } else {
	                  return i
	                }
	              })
	            )
	          }
	        } else if (prop === 'every' || prop === 'some') {
	          return cb => {
	            return node[prop]((child, ...other) =>
	              cb(child.toProxy(), ...other)
	            )
	          }
	        } else if (prop === 'root') {
	          return () => node.root().toProxy()
	        } else if (prop === 'nodes') {
	          return node.nodes.map(i => i.toProxy())
	        } else if (prop === 'first' || prop === 'last') {
	          return node[prop].toProxy()
	        } else {
	          return node[prop]
	        }
	      },

	      set(node, prop, value) {
	        if (node[prop] === value) return true
	        node[prop] = value;
	        if (prop === 'name' || prop === 'params' || prop === 'selector') {
	          node.markDirty();
	        }
	        return true
	      }
	    }
	  }

	  index(child) {
	    if (typeof child === 'number') return child
	    if (child.proxyOf) child = child.proxyOf;
	    return this.proxyOf.nodes.indexOf(child)
	  }

	  insertAfter(exist, add) {
	    let existIndex = this.index(exist);
	    let nodes = this.normalize(add, this.proxyOf.nodes[existIndex]).reverse();
	    existIndex = this.index(exist);
	    for (let node of nodes) this.proxyOf.nodes.splice(existIndex + 1, 0, node);

	    let index;
	    for (let id in this.indexes) {
	      index = this.indexes[id];
	      if (existIndex < index) {
	        this.indexes[id] = index + nodes.length;
	      }
	    }

	    this.markDirty();

	    return this
	  }

	  insertBefore(exist, add) {
	    let existIndex = this.index(exist);
	    let type = existIndex === 0 ? 'prepend' : false;
	    let nodes = this.normalize(add, this.proxyOf.nodes[existIndex], type).reverse();
	    existIndex = this.index(exist);
	    for (let node of nodes) this.proxyOf.nodes.splice(existIndex, 0, node);

	    let index;
	    for (let id in this.indexes) {
	      index = this.indexes[id];
	      if (existIndex <= index) {
	        this.indexes[id] = index + nodes.length;
	      }
	    }

	    this.markDirty();

	    return this
	  }

	  normalize(nodes, sample) {
	    if (typeof nodes === 'string') {
	      nodes = cleanSource(parse(nodes).nodes);
	    } else if (typeof nodes === 'undefined') {
	      nodes = [];
	    } else if (Array.isArray(nodes)) {
	      nodes = nodes.slice(0);
	      for (let i of nodes) {
	        if (i.parent) i.parent.removeChild(i, 'ignore');
	      }
	    } else if (nodes.type === 'root' && this.type !== 'document') {
	      nodes = nodes.nodes.slice(0);
	      for (let i of nodes) {
	        if (i.parent) i.parent.removeChild(i, 'ignore');
	      }
	    } else if (nodes.type) {
	      nodes = [nodes];
	    } else if (nodes.prop) {
	      if (typeof nodes.value === 'undefined') {
	        throw new Error('Value field is missed in node creation')
	      } else if (typeof nodes.value !== 'string') {
	        nodes.value = String(nodes.value);
	      }
	      nodes = [new Declaration(nodes)];
	    } else if (nodes.selector) {
	      nodes = [new Rule(nodes)];
	    } else if (nodes.name) {
	      nodes = [new AtRule(nodes)];
	    } else if (nodes.text) {
	      nodes = [new Comment(nodes)];
	    } else {
	      throw new Error('Unknown node type in node creation')
	    }

	    let processed = nodes.map(i => {
	      /* c8 ignore next */
	      if (!i[my]) Container.rebuild(i);
	      i = i.proxyOf;
	      if (i.parent) i.parent.removeChild(i);
	      if (i[isClean]) markDirtyUp(i);
	      if (typeof i.raws.before === 'undefined') {
	        if (sample && typeof sample.raws.before !== 'undefined') {
	          i.raws.before = sample.raws.before.replace(/\S/g, '');
	        }
	      }
	      i.parent = this.proxyOf;
	      return i
	    });

	    return processed
	  }

	  prepend(...children) {
	    children = children.reverse();
	    for (let child of children) {
	      let nodes = this.normalize(child, this.first, 'prepend').reverse();
	      for (let node of nodes) this.proxyOf.nodes.unshift(node);
	      for (let id in this.indexes) {
	        this.indexes[id] = this.indexes[id] + nodes.length;
	      }
	    }

	    this.markDirty();

	    return this
	  }

	  push(child) {
	    child.parent = this;
	    this.proxyOf.nodes.push(child);
	    return this
	  }

	  removeAll() {
	    for (let node of this.proxyOf.nodes) node.parent = undefined;
	    this.proxyOf.nodes = [];

	    this.markDirty();

	    return this
	  }

	  removeChild(child) {
	    child = this.index(child);
	    this.proxyOf.nodes[child].parent = undefined;
	    this.proxyOf.nodes.splice(child, 1);

	    let index;
	    for (let id in this.indexes) {
	      index = this.indexes[id];
	      if (index >= child) {
	        this.indexes[id] = index - 1;
	      }
	    }

	    this.markDirty();

	    return this
	  }

	  replaceValues(pattern, opts, callback) {
	    if (!callback) {
	      callback = opts;
	      opts = {};
	    }

	    this.walkDecls(decl => {
	      if (opts.props && !opts.props.includes(decl.prop)) return
	      if (opts.fast && !decl.value.includes(opts.fast)) return

	      decl.value = decl.value.replace(pattern, callback);
	    });

	    this.markDirty();

	    return this
	  }

	  some(condition) {
	    return this.nodes.some(condition)
	  }

	  walk(callback) {
	    return this.each((child, i) => {
	      let result;
	      try {
	        result = callback(child, i);
	      } catch (e) {
	        throw child.addToError(e)
	      }
	      if (result !== false && child.walk) {
	        result = child.walk(callback);
	      }

	      return result
	    })
	  }

	  walkAtRules(name, callback) {
	    if (!callback) {
	      callback = name;
	      return this.walk((child, i) => {
	        if (child.type === 'atrule') {
	          return callback(child, i)
	        }
	      })
	    }
	    if (name instanceof RegExp) {
	      return this.walk((child, i) => {
	        if (child.type === 'atrule' && name.test(child.name)) {
	          return callback(child, i)
	        }
	      })
	    }
	    return this.walk((child, i) => {
	      if (child.type === 'atrule' && child.name === name) {
	        return callback(child, i)
	      }
	    })
	  }

	  walkComments(callback) {
	    return this.walk((child, i) => {
	      if (child.type === 'comment') {
	        return callback(child, i)
	      }
	    })
	  }

	  walkDecls(prop, callback) {
	    if (!callback) {
	      callback = prop;
	      return this.walk((child, i) => {
	        if (child.type === 'decl') {
	          return callback(child, i)
	        }
	      })
	    }
	    if (prop instanceof RegExp) {
	      return this.walk((child, i) => {
	        if (child.type === 'decl' && prop.test(child.prop)) {
	          return callback(child, i)
	        }
	      })
	    }
	    return this.walk((child, i) => {
	      if (child.type === 'decl' && child.prop === prop) {
	        return callback(child, i)
	      }
	    })
	  }

	  walkRules(selector, callback) {
	    if (!callback) {
	      callback = selector;

	      return this.walk((child, i) => {
	        if (child.type === 'rule') {
	          return callback(child, i)
	        }
	      })
	    }
	    if (selector instanceof RegExp) {
	      return this.walk((child, i) => {
	        if (child.type === 'rule' && selector.test(child.selector)) {
	          return callback(child, i)
	        }
	      })
	    }
	    return this.walk((child, i) => {
	      if (child.type === 'rule' && child.selector === selector) {
	        return callback(child, i)
	      }
	    })
	  }

	  get first() {
	    if (!this.proxyOf.nodes) return undefined
	    return this.proxyOf.nodes[0]
	  }

	  get last() {
	    if (!this.proxyOf.nodes) return undefined
	    return this.proxyOf.nodes[this.proxyOf.nodes.length - 1]
	  }
	}

	Container.registerParse = dependant => {
	  parse = dependant;
	};

	Container.registerRule = dependant => {
	  Rule = dependant;
	};

	Container.registerAtRule = dependant => {
	  AtRule = dependant;
	};

	Container.registerRoot = dependant => {
	  Root = dependant;
	};

	container = Container;
	Container.default = Container;

	/* c8 ignore start */
	Container.rebuild = node => {
	  if (node.type === 'atrule') {
	    Object.setPrototypeOf(node, AtRule.prototype);
	  } else if (node.type === 'rule') {
	    Object.setPrototypeOf(node, Rule.prototype);
	  } else if (node.type === 'decl') {
	    Object.setPrototypeOf(node, Declaration.prototype);
	  } else if (node.type === 'comment') {
	    Object.setPrototypeOf(node, Comment.prototype);
	  } else if (node.type === 'root') {
	    Object.setPrototypeOf(node, Root.prototype);
	  }

	  node[my] = true;

	  if (node.nodes) {
	    node.nodes.forEach(child => {
	      Container.rebuild(child);
	    });
	  }
	};
	/* c8 ignore stop */
	return container;
}

var document$1;
var hasRequiredDocument;

function requireDocument () {
	if (hasRequiredDocument) return document$1;
	hasRequiredDocument = 1;

	let Container = requireContainer();

	let LazyResult, Processor;

	class Document extends Container {
	  constructor(defaults) {
	    // type needs to be passed to super, otherwise child roots won't be normalized correctly
	    super({ type: 'document', ...defaults });

	    if (!this.nodes) {
	      this.nodes = [];
	    }
	  }

	  toResult(opts = {}) {
	    let lazy = new LazyResult(new Processor(), this, opts);

	    return lazy.stringify()
	  }
	}

	Document.registerLazyResult = dependant => {
	  LazyResult = dependant;
	};

	Document.registerProcessor = dependant => {
	  Processor = dependant;
	};

	document$1 = Document;
	Document.default = Document;
	return document$1;
}

/* eslint-disable no-console */

var warnOnce;
var hasRequiredWarnOnce;

function requireWarnOnce () {
	if (hasRequiredWarnOnce) return warnOnce;
	hasRequiredWarnOnce = 1;

	let printed = {};

	warnOnce = function warnOnce(message) {
	  if (printed[message]) return
	  printed[message] = true;

	  if (typeof console !== 'undefined' && console.warn) {
	    console.warn(message);
	  }
	};
	return warnOnce;
}

var warning;
var hasRequiredWarning;

function requireWarning () {
	if (hasRequiredWarning) return warning;
	hasRequiredWarning = 1;

	class Warning {
	  constructor(text, opts = {}) {
	    this.type = 'warning';
	    this.text = text;

	    if (opts.node && opts.node.source) {
	      let range = opts.node.rangeBy(opts);
	      this.line = range.start.line;
	      this.column = range.start.column;
	      this.endLine = range.end.line;
	      this.endColumn = range.end.column;
	    }

	    for (let opt in opts) this[opt] = opts[opt];
	  }

	  toString() {
	    if (this.node) {
	      return this.node.error(this.text, {
	        index: this.index,
	        plugin: this.plugin,
	        word: this.word
	      }).message
	    }

	    if (this.plugin) {
	      return this.plugin + ': ' + this.text
	    }

	    return this.text
	  }
	}

	warning = Warning;
	Warning.default = Warning;
	return warning;
}

var result;
var hasRequiredResult;

function requireResult () {
	if (hasRequiredResult) return result;
	hasRequiredResult = 1;

	let Warning = requireWarning();

	class Result {
	  constructor(processor, root, opts) {
	    this.processor = processor;
	    this.messages = [];
	    this.root = root;
	    this.opts = opts;
	    this.css = undefined;
	    this.map = undefined;
	  }

	  toString() {
	    return this.css
	  }

	  warn(text, opts = {}) {
	    if (!opts.plugin) {
	      if (this.lastPlugin && this.lastPlugin.postcssPlugin) {
	        opts.plugin = this.lastPlugin.postcssPlugin;
	      }
	    }

	    let warning = new Warning(text, opts);
	    this.messages.push(warning);

	    return warning
	  }

	  warnings() {
	    return this.messages.filter(i => i.type === 'warning')
	  }

	  get content() {
	    return this.css
	  }
	}

	result = Result;
	Result.default = Result;
	return result;
}

var atRule;
var hasRequiredAtRule;

function requireAtRule () {
	if (hasRequiredAtRule) return atRule;
	hasRequiredAtRule = 1;

	let Container = requireContainer();

	class AtRule extends Container {
	  constructor(defaults) {
	    super(defaults);
	    this.type = 'atrule';
	  }

	  append(...children) {
	    if (!this.proxyOf.nodes) this.nodes = [];
	    return super.append(...children)
	  }

	  prepend(...children) {
	    if (!this.proxyOf.nodes) this.nodes = [];
	    return super.prepend(...children)
	  }
	}

	atRule = AtRule;
	AtRule.default = AtRule;

	Container.registerAtRule(AtRule);
	return atRule;
}

var root;
var hasRequiredRoot;

function requireRoot () {
	if (hasRequiredRoot) return root;
	hasRequiredRoot = 1;

	let Container = requireContainer();

	let LazyResult, Processor;

	class Root extends Container {
	  constructor(defaults) {
	    super(defaults);
	    this.type = 'root';
	    if (!this.nodes) this.nodes = [];
	  }

	  normalize(child, sample, type) {
	    let nodes = super.normalize(child);

	    if (sample) {
	      if (type === 'prepend') {
	        if (this.nodes.length > 1) {
	          sample.raws.before = this.nodes[1].raws.before;
	        } else {
	          delete sample.raws.before;
	        }
	      } else if (this.first !== sample) {
	        for (let node of nodes) {
	          node.raws.before = sample.raws.before;
	        }
	      }
	    }

	    return nodes
	  }

	  removeChild(child, ignore) {
	    let index = this.index(child);

	    if (!ignore && index === 0 && this.nodes.length > 1) {
	      this.nodes[1].raws.before = this.nodes[index].raws.before;
	    }

	    return super.removeChild(child)
	  }

	  toResult(opts = {}) {
	    let lazy = new LazyResult(new Processor(), this, opts);
	    return lazy.stringify()
	  }
	}

	Root.registerLazyResult = dependant => {
	  LazyResult = dependant;
	};

	Root.registerProcessor = dependant => {
	  Processor = dependant;
	};

	root = Root;
	Root.default = Root;

	Container.registerRoot(Root);
	return root;
}

var list_1;
var hasRequiredList;

function requireList () {
	if (hasRequiredList) return list_1;
	hasRequiredList = 1;

	let list = {
	  comma(string) {
	    return list.split(string, [','], true)
	  },

	  space(string) {
	    let spaces = [' ', '\n', '\t'];
	    return list.split(string, spaces)
	  },

	  split(string, separators, last) {
	    let array = [];
	    let current = '';
	    let split = false;

	    let func = 0;
	    let inQuote = false;
	    let prevQuote = '';
	    let escape = false;

	    for (let letter of string) {
	      if (escape) {
	        escape = false;
	      } else if (letter === '\\') {
	        escape = true;
	      } else if (inQuote) {
	        if (letter === prevQuote) {
	          inQuote = false;
	        }
	      } else if (letter === '"' || letter === "'") {
	        inQuote = true;
	        prevQuote = letter;
	      } else if (letter === '(') {
	        func += 1;
	      } else if (letter === ')') {
	        if (func > 0) func -= 1;
	      } else if (func === 0) {
	        if (separators.includes(letter)) split = true;
	      }

	      if (split) {
	        if (current !== '') array.push(current.trim());
	        current = '';
	        split = false;
	      } else {
	        current += letter;
	      }
	    }

	    if (last || current !== '') array.push(current.trim());
	    return array
	  }
	};

	list_1 = list;
	list.default = list;
	return list_1;
}

var rule;
var hasRequiredRule;

function requireRule () {
	if (hasRequiredRule) return rule;
	hasRequiredRule = 1;

	let Container = requireContainer();
	let list = requireList();

	class Rule extends Container {
	  constructor(defaults) {
	    super(defaults);
	    this.type = 'rule';
	    if (!this.nodes) this.nodes = [];
	  }

	  get selectors() {
	    return list.comma(this.selector)
	  }

	  set selectors(values) {
	    let match = this.selector ? this.selector.match(/,\s*/) : null;
	    let sep = match ? match[0] : ',' + this.raw('between', 'beforeOpen');
	    this.selector = values.join(sep);
	  }
	}

	rule = Rule;
	Rule.default = Rule;

	Container.registerRule(Rule);
	return rule;
}

var parser;
var hasRequiredParser;

function requireParser () {
	if (hasRequiredParser) return parser;
	hasRequiredParser = 1;

	let Declaration = requireDeclaration();
	let tokenizer = requireTokenize();
	let Comment = requireComment();
	let AtRule = requireAtRule();
	let Root = requireRoot();
	let Rule = requireRule();

	const SAFE_COMMENT_NEIGHBOR = {
	  empty: true,
	  space: true
	};

	function findLastWithPosition(tokens) {
	  for (let i = tokens.length - 1; i >= 0; i--) {
	    let token = tokens[i];
	    let pos = token[3] || token[2];
	    if (pos) return pos
	  }
	}

	class Parser {
	  constructor(input) {
	    this.input = input;

	    this.root = new Root();
	    this.current = this.root;
	    this.spaces = '';
	    this.semicolon = false;

	    this.createTokenizer();
	    this.root.source = { input, start: { column: 1, line: 1, offset: 0 } };
	  }

	  atrule(token) {
	    let node = new AtRule();
	    node.name = token[1].slice(1);
	    if (node.name === '') {
	      this.unnamedAtrule(node, token);
	    }
	    this.init(node, token[2]);

	    let type;
	    let prev;
	    let shift;
	    let last = false;
	    let open = false;
	    let params = [];
	    let brackets = [];

	    while (!this.tokenizer.endOfFile()) {
	      token = this.tokenizer.nextToken();
	      type = token[0];

	      if (type === '(' || type === '[') {
	        brackets.push(type === '(' ? ')' : ']');
	      } else if (type === '{' && brackets.length > 0) {
	        brackets.push('}');
	      } else if (type === brackets[brackets.length - 1]) {
	        brackets.pop();
	      }

	      if (brackets.length === 0) {
	        if (type === ';') {
	          node.source.end = this.getPosition(token[2]);
	          node.source.end.offset++;
	          this.semicolon = true;
	          break
	        } else if (type === '{') {
	          open = true;
	          break
	        } else if (type === '}') {
	          if (params.length > 0) {
	            shift = params.length - 1;
	            prev = params[shift];
	            while (prev && prev[0] === 'space') {
	              prev = params[--shift];
	            }
	            if (prev) {
	              node.source.end = this.getPosition(prev[3] || prev[2]);
	              node.source.end.offset++;
	            }
	          }
	          this.end(token);
	          break
	        } else {
	          params.push(token);
	        }
	      } else {
	        params.push(token);
	      }

	      if (this.tokenizer.endOfFile()) {
	        last = true;
	        break
	      }
	    }

	    node.raws.between = this.spacesAndCommentsFromEnd(params);
	    if (params.length) {
	      node.raws.afterName = this.spacesAndCommentsFromStart(params);
	      this.raw(node, 'params', params);
	      if (last) {
	        token = params[params.length - 1];
	        node.source.end = this.getPosition(token[3] || token[2]);
	        node.source.end.offset++;
	        this.spaces = node.raws.between;
	        node.raws.between = '';
	      }
	    } else {
	      node.raws.afterName = '';
	      node.params = '';
	    }

	    if (open) {
	      node.nodes = [];
	      this.current = node;
	    }
	  }

	  checkMissedSemicolon(tokens) {
	    let colon = this.colon(tokens);
	    if (colon === false) return

	    let founded = 0;
	    let token;
	    for (let j = colon - 1; j >= 0; j--) {
	      token = tokens[j];
	      if (token[0] !== 'space') {
	        founded += 1;
	        if (founded === 2) break
	      }
	    }
	    // If the token is a word, e.g. `!important`, `red` or any other valid property's value.
	    // Then we need to return the colon after that word token. [3] is the "end" colon of that word.
	    // And because we need it after that one we do +1 to get the next one.
	    throw this.input.error(
	      'Missed semicolon',
	      token[0] === 'word' ? token[3] + 1 : token[2]
	    )
	  }

	  colon(tokens) {
	    let brackets = 0;
	    let token, type, prev;
	    for (let [i, element] of tokens.entries()) {
	      token = element;
	      type = token[0];

	      if (type === '(') {
	        brackets += 1;
	      }
	      if (type === ')') {
	        brackets -= 1;
	      }
	      if (brackets === 0 && type === ':') {
	        if (!prev) {
	          this.doubleColon(token);
	        } else if (prev[0] === 'word' && prev[1] === 'progid') {
	          continue
	        } else {
	          return i
	        }
	      }

	      prev = token;
	    }
	    return false
	  }

	  comment(token) {
	    let node = new Comment();
	    this.init(node, token[2]);
	    node.source.end = this.getPosition(token[3] || token[2]);
	    node.source.end.offset++;

	    let text = token[1].slice(2, -2);
	    if (/^\s*$/.test(text)) {
	      node.text = '';
	      node.raws.left = text;
	      node.raws.right = '';
	    } else {
	      let match = text.match(/^(\s*)([^]*\S)(\s*)$/);
	      node.text = match[2];
	      node.raws.left = match[1];
	      node.raws.right = match[3];
	    }
	  }

	  createTokenizer() {
	    this.tokenizer = tokenizer(this.input);
	  }

	  decl(tokens, customProperty) {
	    let node = new Declaration();
	    this.init(node, tokens[0][2]);

	    let last = tokens[tokens.length - 1];
	    if (last[0] === ';') {
	      this.semicolon = true;
	      tokens.pop();
	    }

	    node.source.end = this.getPosition(
	      last[3] || last[2] || findLastWithPosition(tokens)
	    );
	    node.source.end.offset++;

	    while (tokens[0][0] !== 'word') {
	      if (tokens.length === 1) this.unknownWord(tokens);
	      node.raws.before += tokens.shift()[1];
	    }
	    node.source.start = this.getPosition(tokens[0][2]);

	    node.prop = '';
	    while (tokens.length) {
	      let type = tokens[0][0];
	      if (type === ':' || type === 'space' || type === 'comment') {
	        break
	      }
	      node.prop += tokens.shift()[1];
	    }

	    node.raws.between = '';

	    let token;
	    while (tokens.length) {
	      token = tokens.shift();

	      if (token[0] === ':') {
	        node.raws.between += token[1];
	        break
	      } else {
	        if (token[0] === 'word' && /\w/.test(token[1])) {
	          this.unknownWord([token]);
	        }
	        node.raws.between += token[1];
	      }
	    }

	    if (node.prop[0] === '_' || node.prop[0] === '*') {
	      node.raws.before += node.prop[0];
	      node.prop = node.prop.slice(1);
	    }

	    let firstSpaces = [];
	    let next;
	    while (tokens.length) {
	      next = tokens[0][0];
	      if (next !== 'space' && next !== 'comment') break
	      firstSpaces.push(tokens.shift());
	    }

	    this.precheckMissedSemicolon(tokens);

	    for (let i = tokens.length - 1; i >= 0; i--) {
	      token = tokens[i];
	      if (token[1].toLowerCase() === '!important') {
	        node.important = true;
	        let string = this.stringFrom(tokens, i);
	        string = this.spacesFromEnd(tokens) + string;
	        if (string !== ' !important') node.raws.important = string;
	        break
	      } else if (token[1].toLowerCase() === 'important') {
	        let cache = tokens.slice(0);
	        let str = '';
	        for (let j = i; j > 0; j--) {
	          let type = cache[j][0];
	          if (str.trim().indexOf('!') === 0 && type !== 'space') {
	            break
	          }
	          str = cache.pop()[1] + str;
	        }
	        if (str.trim().indexOf('!') === 0) {
	          node.important = true;
	          node.raws.important = str;
	          tokens = cache;
	        }
	      }

	      if (token[0] !== 'space' && token[0] !== 'comment') {
	        break
	      }
	    }

	    let hasWord = tokens.some(i => i[0] !== 'space' && i[0] !== 'comment');

	    if (hasWord) {
	      node.raws.between += firstSpaces.map(i => i[1]).join('');
	      firstSpaces = [];
	    }
	    this.raw(node, 'value', firstSpaces.concat(tokens), customProperty);

	    if (node.value.includes(':') && !customProperty) {
	      this.checkMissedSemicolon(tokens);
	    }
	  }

	  doubleColon(token) {
	    throw this.input.error(
	      'Double colon',
	      { offset: token[2] },
	      { offset: token[2] + token[1].length }
	    )
	  }

	  emptyRule(token) {
	    let node = new Rule();
	    this.init(node, token[2]);
	    node.selector = '';
	    node.raws.between = '';
	    this.current = node;
	  }

	  end(token) {
	    if (this.current.nodes && this.current.nodes.length) {
	      this.current.raws.semicolon = this.semicolon;
	    }
	    this.semicolon = false;

	    this.current.raws.after = (this.current.raws.after || '') + this.spaces;
	    this.spaces = '';

	    if (this.current.parent) {
	      this.current.source.end = this.getPosition(token[2]);
	      this.current.source.end.offset++;
	      this.current = this.current.parent;
	    } else {
	      this.unexpectedClose(token);
	    }
	  }

	  endFile() {
	    if (this.current.parent) this.unclosedBlock();
	    if (this.current.nodes && this.current.nodes.length) {
	      this.current.raws.semicolon = this.semicolon;
	    }
	    this.current.raws.after = (this.current.raws.after || '') + this.spaces;
	    this.root.source.end = this.getPosition(this.tokenizer.position());
	  }

	  freeSemicolon(token) {
	    this.spaces += token[1];
	    if (this.current.nodes) {
	      let prev = this.current.nodes[this.current.nodes.length - 1];
	      if (prev && prev.type === 'rule' && !prev.raws.ownSemicolon) {
	        prev.raws.ownSemicolon = this.spaces;
	        this.spaces = '';
	      }
	    }
	  }

	  // Helpers

	  getPosition(offset) {
	    let pos = this.input.fromOffset(offset);
	    return {
	      column: pos.col,
	      line: pos.line,
	      offset
	    }
	  }

	  init(node, offset) {
	    this.current.push(node);
	    node.source = {
	      input: this.input,
	      start: this.getPosition(offset)
	    };
	    node.raws.before = this.spaces;
	    this.spaces = '';
	    if (node.type !== 'comment') this.semicolon = false;
	  }

	  other(start) {
	    let end = false;
	    let type = null;
	    let colon = false;
	    let bracket = null;
	    let brackets = [];
	    let customProperty = start[1].startsWith('--');

	    let tokens = [];
	    let token = start;
	    while (token) {
	      type = token[0];
	      tokens.push(token);

	      if (type === '(' || type === '[') {
	        if (!bracket) bracket = token;
	        brackets.push(type === '(' ? ')' : ']');
	      } else if (customProperty && colon && type === '{') {
	        if (!bracket) bracket = token;
	        brackets.push('}');
	      } else if (brackets.length === 0) {
	        if (type === ';') {
	          if (colon) {
	            this.decl(tokens, customProperty);
	            return
	          } else {
	            break
	          }
	        } else if (type === '{') {
	          this.rule(tokens);
	          return
	        } else if (type === '}') {
	          this.tokenizer.back(tokens.pop());
	          end = true;
	          break
	        } else if (type === ':') {
	          colon = true;
	        }
	      } else if (type === brackets[brackets.length - 1]) {
	        brackets.pop();
	        if (brackets.length === 0) bracket = null;
	      }

	      token = this.tokenizer.nextToken();
	    }

	    if (this.tokenizer.endOfFile()) end = true;
	    if (brackets.length > 0) this.unclosedBracket(bracket);

	    if (end && colon) {
	      if (!customProperty) {
	        while (tokens.length) {
	          token = tokens[tokens.length - 1][0];
	          if (token !== 'space' && token !== 'comment') break
	          this.tokenizer.back(tokens.pop());
	        }
	      }
	      this.decl(tokens, customProperty);
	    } else {
	      this.unknownWord(tokens);
	    }
	  }

	  parse() {
	    let token;
	    while (!this.tokenizer.endOfFile()) {
	      token = this.tokenizer.nextToken();

	      switch (token[0]) {
	        case 'space':
	          this.spaces += token[1];
	          break

	        case ';':
	          this.freeSemicolon(token);
	          break

	        case '}':
	          this.end(token);
	          break

	        case 'comment':
	          this.comment(token);
	          break

	        case 'at-word':
	          this.atrule(token);
	          break

	        case '{':
	          this.emptyRule(token);
	          break

	        default:
	          this.other(token);
	          break
	      }
	    }
	    this.endFile();
	  }

	  precheckMissedSemicolon(/* tokens */) {
	    // Hook for Safe Parser
	  }

	  raw(node, prop, tokens, customProperty) {
	    let token, type;
	    let length = tokens.length;
	    let value = '';
	    let clean = true;
	    let next, prev;

	    for (let i = 0; i < length; i += 1) {
	      token = tokens[i];
	      type = token[0];
	      if (type === 'space' && i === length - 1 && !customProperty) {
	        clean = false;
	      } else if (type === 'comment') {
	        prev = tokens[i - 1] ? tokens[i - 1][0] : 'empty';
	        next = tokens[i + 1] ? tokens[i + 1][0] : 'empty';
	        if (!SAFE_COMMENT_NEIGHBOR[prev] && !SAFE_COMMENT_NEIGHBOR[next]) {
	          if (value.slice(-1) === ',') {
	            clean = false;
	          } else {
	            value += token[1];
	          }
	        } else {
	          clean = false;
	        }
	      } else {
	        value += token[1];
	      }
	    }
	    if (!clean) {
	      let raw = tokens.reduce((all, i) => all + i[1], '');
	      node.raws[prop] = { raw, value };
	    }
	    node[prop] = value;
	  }

	  rule(tokens) {
	    tokens.pop();

	    let node = new Rule();
	    this.init(node, tokens[0][2]);

	    node.raws.between = this.spacesAndCommentsFromEnd(tokens);
	    this.raw(node, 'selector', tokens);
	    this.current = node;
	  }

	  spacesAndCommentsFromEnd(tokens) {
	    let lastTokenType;
	    let spaces = '';
	    while (tokens.length) {
	      lastTokenType = tokens[tokens.length - 1][0];
	      if (lastTokenType !== 'space' && lastTokenType !== 'comment') break
	      spaces = tokens.pop()[1] + spaces;
	    }
	    return spaces
	  }

	  // Errors

	  spacesAndCommentsFromStart(tokens) {
	    let next;
	    let spaces = '';
	    while (tokens.length) {
	      next = tokens[0][0];
	      if (next !== 'space' && next !== 'comment') break
	      spaces += tokens.shift()[1];
	    }
	    return spaces
	  }

	  spacesFromEnd(tokens) {
	    let lastTokenType;
	    let spaces = '';
	    while (tokens.length) {
	      lastTokenType = tokens[tokens.length - 1][0];
	      if (lastTokenType !== 'space') break
	      spaces = tokens.pop()[1] + spaces;
	    }
	    return spaces
	  }

	  stringFrom(tokens, from) {
	    let result = '';
	    for (let i = from; i < tokens.length; i++) {
	      result += tokens[i][1];
	    }
	    tokens.splice(from, tokens.length - from);
	    return result
	  }

	  unclosedBlock() {
	    let pos = this.current.source.start;
	    throw this.input.error('Unclosed block', pos.line, pos.column)
	  }

	  unclosedBracket(bracket) {
	    throw this.input.error(
	      'Unclosed bracket',
	      { offset: bracket[2] },
	      { offset: bracket[2] + 1 }
	    )
	  }

	  unexpectedClose(token) {
	    throw this.input.error(
	      'Unexpected }',
	      { offset: token[2] },
	      { offset: token[2] + 1 }
	    )
	  }

	  unknownWord(tokens) {
	    throw this.input.error(
	      'Unknown word',
	      { offset: tokens[0][2] },
	      { offset: tokens[0][2] + tokens[0][1].length }
	    )
	  }

	  unnamedAtrule(node, token) {
	    throw this.input.error(
	      'At-rule without name',
	      { offset: token[2] },
	      { offset: token[2] + token[1].length }
	    )
	  }
	}

	parser = Parser;
	return parser;
}

var parse_1;
var hasRequiredParse;

function requireParse () {
	if (hasRequiredParse) return parse_1;
	hasRequiredParse = 1;

	let Container = requireContainer();
	let Parser = requireParser();
	let Input = requireInput();

	function parse(css, opts) {
	  let input = new Input(css, opts);
	  let parser = new Parser(input);
	  try {
	    parser.parse();
	  } catch (e) {
	    if (process.env.NODE_ENV !== 'production') {
	      if (e.name === 'CssSyntaxError' && opts && opts.from) {
	        if (/\.scss$/i.test(opts.from)) {
	          e.message +=
	            '\nYou tried to parse SCSS with ' +
	            'the standard CSS parser; ' +
	            'try again with the postcss-scss parser';
	        } else if (/\.sass/i.test(opts.from)) {
	          e.message +=
	            '\nYou tried to parse Sass with ' +
	            'the standard CSS parser; ' +
	            'try again with the postcss-sass parser';
	        } else if (/\.less$/i.test(opts.from)) {
	          e.message +=
	            '\nYou tried to parse Less with ' +
	            'the standard CSS parser; ' +
	            'try again with the postcss-less parser';
	        }
	      }
	    }
	    throw e
	  }

	  return parser.root
	}

	parse_1 = parse;
	parse.default = parse;

	Container.registerParse(parse);
	return parse_1;
}

var lazyResult;
var hasRequiredLazyResult;

function requireLazyResult () {
	if (hasRequiredLazyResult) return lazyResult;
	hasRequiredLazyResult = 1;

	let { isClean, my } = requireSymbols();
	let MapGenerator = requireMapGenerator();
	let stringify = requireStringify();
	let Container = requireContainer();
	let Document = requireDocument();
	let warnOnce = requireWarnOnce();
	let Result = requireResult();
	let parse = requireParse();
	let Root = requireRoot();

	const TYPE_TO_CLASS_NAME = {
	  atrule: 'AtRule',
	  comment: 'Comment',
	  decl: 'Declaration',
	  document: 'Document',
	  root: 'Root',
	  rule: 'Rule'
	};

	const PLUGIN_PROPS = {
	  AtRule: true,
	  AtRuleExit: true,
	  Comment: true,
	  CommentExit: true,
	  Declaration: true,
	  DeclarationExit: true,
	  Document: true,
	  DocumentExit: true,
	  Once: true,
	  OnceExit: true,
	  postcssPlugin: true,
	  prepare: true,
	  Root: true,
	  RootExit: true,
	  Rule: true,
	  RuleExit: true
	};

	const NOT_VISITORS = {
	  Once: true,
	  postcssPlugin: true,
	  prepare: true
	};

	const CHILDREN = 0;

	function isPromise(obj) {
	  return typeof obj === 'object' && typeof obj.then === 'function'
	}

	function getEvents(node) {
	  let key = false;
	  let type = TYPE_TO_CLASS_NAME[node.type];
	  if (node.type === 'decl') {
	    key = node.prop.toLowerCase();
	  } else if (node.type === 'atrule') {
	    key = node.name.toLowerCase();
	  }

	  if (key && node.append) {
	    return [
	      type,
	      type + '-' + key,
	      CHILDREN,
	      type + 'Exit',
	      type + 'Exit-' + key
	    ]
	  } else if (key) {
	    return [type, type + '-' + key, type + 'Exit', type + 'Exit-' + key]
	  } else if (node.append) {
	    return [type, CHILDREN, type + 'Exit']
	  } else {
	    return [type, type + 'Exit']
	  }
	}

	function toStack(node) {
	  let events;
	  if (node.type === 'document') {
	    events = ['Document', CHILDREN, 'DocumentExit'];
	  } else if (node.type === 'root') {
	    events = ['Root', CHILDREN, 'RootExit'];
	  } else {
	    events = getEvents(node);
	  }

	  return {
	    eventIndex: 0,
	    events,
	    iterator: 0,
	    node,
	    visitorIndex: 0,
	    visitors: []
	  }
	}

	function cleanMarks(node) {
	  node[isClean] = false;
	  if (node.nodes) node.nodes.forEach(i => cleanMarks(i));
	  return node
	}

	let postcss = {};

	class LazyResult {
	  constructor(processor, css, opts) {
	    this.stringified = false;
	    this.processed = false;

	    let root;
	    if (
	      typeof css === 'object' &&
	      css !== null &&
	      (css.type === 'root' || css.type === 'document')
	    ) {
	      root = cleanMarks(css);
	    } else if (css instanceof LazyResult || css instanceof Result) {
	      root = cleanMarks(css.root);
	      if (css.map) {
	        if (typeof opts.map === 'undefined') opts.map = {};
	        if (!opts.map.inline) opts.map.inline = false;
	        opts.map.prev = css.map;
	      }
	    } else {
	      let parser = parse;
	      if (opts.syntax) parser = opts.syntax.parse;
	      if (opts.parser) parser = opts.parser;
	      if (parser.parse) parser = parser.parse;

	      try {
	        root = parser(css, opts);
	      } catch (error) {
	        this.processed = true;
	        this.error = error;
	      }

	      if (root && !root[my]) {
	        /* c8 ignore next 2 */
	        Container.rebuild(root);
	      }
	    }

	    this.result = new Result(processor, root, opts);
	    this.helpers = { ...postcss, postcss, result: this.result };
	    this.plugins = this.processor.plugins.map(plugin => {
	      if (typeof plugin === 'object' && plugin.prepare) {
	        return { ...plugin, ...plugin.prepare(this.result) }
	      } else {
	        return plugin
	      }
	    });
	  }

	  async() {
	    if (this.error) return Promise.reject(this.error)
	    if (this.processed) return Promise.resolve(this.result)
	    if (!this.processing) {
	      this.processing = this.runAsync();
	    }
	    return this.processing
	  }

	  catch(onRejected) {
	    return this.async().catch(onRejected)
	  }

	  finally(onFinally) {
	    return this.async().then(onFinally, onFinally)
	  }

	  getAsyncError() {
	    throw new Error('Use process(css).then(cb) to work with async plugins')
	  }

	  handleError(error, node) {
	    let plugin = this.result.lastPlugin;
	    try {
	      if (node) node.addToError(error);
	      this.error = error;
	      if (error.name === 'CssSyntaxError' && !error.plugin) {
	        error.plugin = plugin.postcssPlugin;
	        error.setMessage();
	      } else if (plugin.postcssVersion) {
	        if (process.env.NODE_ENV !== 'production') {
	          let pluginName = plugin.postcssPlugin;
	          let pluginVer = plugin.postcssVersion;
	          let runtimeVer = this.result.processor.version;
	          let a = pluginVer.split('.');
	          let b = runtimeVer.split('.');

	          if (a[0] !== b[0] || parseInt(a[1]) > parseInt(b[1])) {
	            // eslint-disable-next-line no-console
	            console.error(
	              'Unknown error from PostCSS plugin. Your current PostCSS ' +
	                'version is ' +
	                runtimeVer +
	                ', but ' +
	                pluginName +
	                ' uses ' +
	                pluginVer +
	                '. Perhaps this is the source of the error below.'
	            );
	          }
	        }
	      }
	    } catch (err) {
	      /* c8 ignore next 3 */
	      // eslint-disable-next-line no-console
	      if (console && console.error) console.error(err);
	    }
	    return error
	  }

	  prepareVisitors() {
	    this.listeners = {};
	    let add = (plugin, type, cb) => {
	      if (!this.listeners[type]) this.listeners[type] = [];
	      this.listeners[type].push([plugin, cb]);
	    };
	    for (let plugin of this.plugins) {
	      if (typeof plugin === 'object') {
	        for (let event in plugin) {
	          if (!PLUGIN_PROPS[event] && /^[A-Z]/.test(event)) {
	            throw new Error(
	              `Unknown event ${event} in ${plugin.postcssPlugin}. ` +
	                `Try to update PostCSS (${this.processor.version} now).`
	            )
	          }
	          if (!NOT_VISITORS[event]) {
	            if (typeof plugin[event] === 'object') {
	              for (let filter in plugin[event]) {
	                if (filter === '*') {
	                  add(plugin, event, plugin[event][filter]);
	                } else {
	                  add(
	                    plugin,
	                    event + '-' + filter.toLowerCase(),
	                    plugin[event][filter]
	                  );
	                }
	              }
	            } else if (typeof plugin[event] === 'function') {
	              add(plugin, event, plugin[event]);
	            }
	          }
	        }
	      }
	    }
	    this.hasListener = Object.keys(this.listeners).length > 0;
	  }

	  async runAsync() {
	    this.plugin = 0;
	    for (let i = 0; i < this.plugins.length; i++) {
	      let plugin = this.plugins[i];
	      let promise = this.runOnRoot(plugin);
	      if (isPromise(promise)) {
	        try {
	          await promise;
	        } catch (error) {
	          throw this.handleError(error)
	        }
	      }
	    }

	    this.prepareVisitors();
	    if (this.hasListener) {
	      let root = this.result.root;
	      while (!root[isClean]) {
	        root[isClean] = true;
	        let stack = [toStack(root)];
	        while (stack.length > 0) {
	          let promise = this.visitTick(stack);
	          if (isPromise(promise)) {
	            try {
	              await promise;
	            } catch (e) {
	              let node = stack[stack.length - 1].node;
	              throw this.handleError(e, node)
	            }
	          }
	        }
	      }

	      if (this.listeners.OnceExit) {
	        for (let [plugin, visitor] of this.listeners.OnceExit) {
	          this.result.lastPlugin = plugin;
	          try {
	            if (root.type === 'document') {
	              let roots = root.nodes.map(subRoot =>
	                visitor(subRoot, this.helpers)
	              );

	              await Promise.all(roots);
	            } else {
	              await visitor(root, this.helpers);
	            }
	          } catch (e) {
	            throw this.handleError(e)
	          }
	        }
	      }
	    }

	    this.processed = true;
	    return this.stringify()
	  }

	  runOnRoot(plugin) {
	    this.result.lastPlugin = plugin;
	    try {
	      if (typeof plugin === 'object' && plugin.Once) {
	        if (this.result.root.type === 'document') {
	          let roots = this.result.root.nodes.map(root =>
	            plugin.Once(root, this.helpers)
	          );

	          if (isPromise(roots[0])) {
	            return Promise.all(roots)
	          }

	          return roots
	        }

	        return plugin.Once(this.result.root, this.helpers)
	      } else if (typeof plugin === 'function') {
	        return plugin(this.result.root, this.result)
	      }
	    } catch (error) {
	      throw this.handleError(error)
	    }
	  }

	  stringify() {
	    if (this.error) throw this.error
	    if (this.stringified) return this.result
	    this.stringified = true;

	    this.sync();

	    let opts = this.result.opts;
	    let str = stringify;
	    if (opts.syntax) str = opts.syntax.stringify;
	    if (opts.stringifier) str = opts.stringifier;
	    if (str.stringify) str = str.stringify;

	    let map = new MapGenerator(str, this.result.root, this.result.opts);
	    let data = map.generate();
	    this.result.css = data[0];
	    this.result.map = data[1];

	    return this.result
	  }

	  sync() {
	    if (this.error) throw this.error
	    if (this.processed) return this.result
	    this.processed = true;

	    if (this.processing) {
	      throw this.getAsyncError()
	    }

	    for (let plugin of this.plugins) {
	      let promise = this.runOnRoot(plugin);
	      if (isPromise(promise)) {
	        throw this.getAsyncError()
	      }
	    }

	    this.prepareVisitors();
	    if (this.hasListener) {
	      let root = this.result.root;
	      while (!root[isClean]) {
	        root[isClean] = true;
	        this.walkSync(root);
	      }
	      if (this.listeners.OnceExit) {
	        if (root.type === 'document') {
	          for (let subRoot of root.nodes) {
	            this.visitSync(this.listeners.OnceExit, subRoot);
	          }
	        } else {
	          this.visitSync(this.listeners.OnceExit, root);
	        }
	      }
	    }

	    return this.result
	  }

	  then(onFulfilled, onRejected) {
	    if (process.env.NODE_ENV !== 'production') {
	      if (!('from' in this.opts)) {
	        warnOnce(
	          'Without `from` option PostCSS could generate wrong source map ' +
	            'and will not find Browserslist config. Set it to CSS file path ' +
	            'or to `undefined` to prevent this warning.'
	        );
	      }
	    }
	    return this.async().then(onFulfilled, onRejected)
	  }

	  toString() {
	    return this.css
	  }

	  visitSync(visitors, node) {
	    for (let [plugin, visitor] of visitors) {
	      this.result.lastPlugin = plugin;
	      let promise;
	      try {
	        promise = visitor(node, this.helpers);
	      } catch (e) {
	        throw this.handleError(e, node.proxyOf)
	      }
	      if (node.type !== 'root' && node.type !== 'document' && !node.parent) {
	        return true
	      }
	      if (isPromise(promise)) {
	        throw this.getAsyncError()
	      }
	    }
	  }

	  visitTick(stack) {
	    let visit = stack[stack.length - 1];
	    let { node, visitors } = visit;

	    if (node.type !== 'root' && node.type !== 'document' && !node.parent) {
	      stack.pop();
	      return
	    }

	    if (visitors.length > 0 && visit.visitorIndex < visitors.length) {
	      let [plugin, visitor] = visitors[visit.visitorIndex];
	      visit.visitorIndex += 1;
	      if (visit.visitorIndex === visitors.length) {
	        visit.visitors = [];
	        visit.visitorIndex = 0;
	      }
	      this.result.lastPlugin = plugin;
	      try {
	        return visitor(node.toProxy(), this.helpers)
	      } catch (e) {
	        throw this.handleError(e, node)
	      }
	    }

	    if (visit.iterator !== 0) {
	      let iterator = visit.iterator;
	      let child;
	      while ((child = node.nodes[node.indexes[iterator]])) {
	        node.indexes[iterator] += 1;
	        if (!child[isClean]) {
	          child[isClean] = true;
	          stack.push(toStack(child));
	          return
	        }
	      }
	      visit.iterator = 0;
	      delete node.indexes[iterator];
	    }

	    let events = visit.events;
	    while (visit.eventIndex < events.length) {
	      let event = events[visit.eventIndex];
	      visit.eventIndex += 1;
	      if (event === CHILDREN) {
	        if (node.nodes && node.nodes.length) {
	          node[isClean] = true;
	          visit.iterator = node.getIterator();
	        }
	        return
	      } else if (this.listeners[event]) {
	        visit.visitors = this.listeners[event];
	        return
	      }
	    }
	    stack.pop();
	  }

	  walkSync(node) {
	    node[isClean] = true;
	    let events = getEvents(node);
	    for (let event of events) {
	      if (event === CHILDREN) {
	        if (node.nodes) {
	          node.each(child => {
	            if (!child[isClean]) this.walkSync(child);
	          });
	        }
	      } else {
	        let visitors = this.listeners[event];
	        if (visitors) {
	          if (this.visitSync(visitors, node.toProxy())) return
	        }
	      }
	    }
	  }

	  warnings() {
	    return this.sync().warnings()
	  }

	  get content() {
	    return this.stringify().content
	  }

	  get css() {
	    return this.stringify().css
	  }

	  get map() {
	    return this.stringify().map
	  }

	  get messages() {
	    return this.sync().messages
	  }

	  get opts() {
	    return this.result.opts
	  }

	  get processor() {
	    return this.result.processor
	  }

	  get root() {
	    return this.sync().root
	  }

	  get [Symbol.toStringTag]() {
	    return 'LazyResult'
	  }
	}

	LazyResult.registerPostcss = dependant => {
	  postcss = dependant;
	};

	lazyResult = LazyResult;
	LazyResult.default = LazyResult;

	Root.registerLazyResult(LazyResult);
	Document.registerLazyResult(LazyResult);
	return lazyResult;
}

var noWorkResult;
var hasRequiredNoWorkResult;

function requireNoWorkResult () {
	if (hasRequiredNoWorkResult) return noWorkResult;
	hasRequiredNoWorkResult = 1;

	let MapGenerator = requireMapGenerator();
	let stringify = requireStringify();
	let warnOnce = requireWarnOnce();
	let parse = requireParse();
	const Result = requireResult();

	class NoWorkResult {
	  constructor(processor, css, opts) {
	    css = css.toString();
	    this.stringified = false;

	    this._processor = processor;
	    this._css = css;
	    this._opts = opts;
	    this._map = undefined;
	    let root;

	    let str = stringify;
	    this.result = new Result(this._processor, root, this._opts);
	    this.result.css = css;

	    let self = this;
	    Object.defineProperty(this.result, 'root', {
	      get() {
	        return self.root
	      }
	    });

	    let map = new MapGenerator(str, root, this._opts, css);
	    if (map.isMap()) {
	      let [generatedCSS, generatedMap] = map.generate();
	      if (generatedCSS) {
	        this.result.css = generatedCSS;
	      }
	      if (generatedMap) {
	        this.result.map = generatedMap;
	      }
	    } else {
	      map.clearAnnotation();
	      this.result.css = map.css;
	    }
	  }

	  async() {
	    if (this.error) return Promise.reject(this.error)
	    return Promise.resolve(this.result)
	  }

	  catch(onRejected) {
	    return this.async().catch(onRejected)
	  }

	  finally(onFinally) {
	    return this.async().then(onFinally, onFinally)
	  }

	  sync() {
	    if (this.error) throw this.error
	    return this.result
	  }

	  then(onFulfilled, onRejected) {
	    if (process.env.NODE_ENV !== 'production') {
	      if (!('from' in this._opts)) {
	        warnOnce(
	          'Without `from` option PostCSS could generate wrong source map ' +
	            'and will not find Browserslist config. Set it to CSS file path ' +
	            'or to `undefined` to prevent this warning.'
	        );
	      }
	    }

	    return this.async().then(onFulfilled, onRejected)
	  }

	  toString() {
	    return this._css
	  }

	  warnings() {
	    return []
	  }

	  get content() {
	    return this.result.css
	  }

	  get css() {
	    return this.result.css
	  }

	  get map() {
	    return this.result.map
	  }

	  get messages() {
	    return []
	  }

	  get opts() {
	    return this.result.opts
	  }

	  get processor() {
	    return this.result.processor
	  }

	  get root() {
	    if (this._root) {
	      return this._root
	    }

	    let root;
	    let parser = parse;

	    try {
	      root = parser(this._css, this._opts);
	    } catch (error) {
	      this.error = error;
	    }

	    if (this.error) {
	      throw this.error
	    } else {
	      this._root = root;
	      return root
	    }
	  }

	  get [Symbol.toStringTag]() {
	    return 'NoWorkResult'
	  }
	}

	noWorkResult = NoWorkResult;
	NoWorkResult.default = NoWorkResult;
	return noWorkResult;
}

var processor;
var hasRequiredProcessor;

function requireProcessor () {
	if (hasRequiredProcessor) return processor;
	hasRequiredProcessor = 1;

	let NoWorkResult = requireNoWorkResult();
	let LazyResult = requireLazyResult();
	let Document = requireDocument();
	let Root = requireRoot();

	class Processor {
	  constructor(plugins = []) {
	    this.version = '8.4.38';
	    this.plugins = this.normalize(plugins);
	  }

	  normalize(plugins) {
	    let normalized = [];
	    for (let i of plugins) {
	      if (i.postcss === true) {
	        i = i();
	      } else if (i.postcss) {
	        i = i.postcss;
	      }

	      if (typeof i === 'object' && Array.isArray(i.plugins)) {
	        normalized = normalized.concat(i.plugins);
	      } else if (typeof i === 'object' && i.postcssPlugin) {
	        normalized.push(i);
	      } else if (typeof i === 'function') {
	        normalized.push(i);
	      } else if (typeof i === 'object' && (i.parse || i.stringify)) {
	        if (process.env.NODE_ENV !== 'production') {
	          throw new Error(
	            'PostCSS syntaxes cannot be used as plugins. Instead, please use ' +
	              'one of the syntax/parser/stringifier options as outlined ' +
	              'in your PostCSS runner documentation.'
	          )
	        }
	      } else {
	        throw new Error(i + ' is not a PostCSS plugin')
	      }
	    }
	    return normalized
	  }

	  process(css, opts = {}) {
	    if (
	      !this.plugins.length &&
	      !opts.parser &&
	      !opts.stringifier &&
	      !opts.syntax
	    ) {
	      return new NoWorkResult(this, css, opts)
	    } else {
	      return new LazyResult(this, css, opts)
	    }
	  }

	  use(plugin) {
	    this.plugins = this.plugins.concat(this.normalize([plugin]));
	    return this
	  }
	}

	processor = Processor;
	Processor.default = Processor;

	Root.registerProcessor(Processor);
	Document.registerProcessor(Processor);
	return processor;
}

var fromJSON_1;
var hasRequiredFromJSON;

function requireFromJSON () {
	if (hasRequiredFromJSON) return fromJSON_1;
	hasRequiredFromJSON = 1;

	let Declaration = requireDeclaration();
	let PreviousMap = requirePreviousMap();
	let Comment = requireComment();
	let AtRule = requireAtRule();
	let Input = requireInput();
	let Root = requireRoot();
	let Rule = requireRule();

	function fromJSON(json, inputs) {
	  if (Array.isArray(json)) return json.map(n => fromJSON(n))

	  let { inputs: ownInputs, ...defaults } = json;
	  if (ownInputs) {
	    inputs = [];
	    for (let input of ownInputs) {
	      let inputHydrated = { ...input, __proto__: Input.prototype };
	      if (inputHydrated.map) {
	        inputHydrated.map = {
	          ...inputHydrated.map,
	          __proto__: PreviousMap.prototype
	        };
	      }
	      inputs.push(inputHydrated);
	    }
	  }
	  if (defaults.nodes) {
	    defaults.nodes = json.nodes.map(n => fromJSON(n, inputs));
	  }
	  if (defaults.source) {
	    let { inputId, ...source } = defaults.source;
	    defaults.source = source;
	    if (inputId != null) {
	      defaults.source.input = inputs[inputId];
	    }
	  }
	  if (defaults.type === 'root') {
	    return new Root(defaults)
	  } else if (defaults.type === 'decl') {
	    return new Declaration(defaults)
	  } else if (defaults.type === 'rule') {
	    return new Rule(defaults)
	  } else if (defaults.type === 'comment') {
	    return new Comment(defaults)
	  } else if (defaults.type === 'atrule') {
	    return new AtRule(defaults)
	  } else {
	    throw new Error('Unknown node type: ' + json.type)
	  }
	}

	fromJSON_1 = fromJSON;
	fromJSON.default = fromJSON;
	return fromJSON_1;
}

var postcss_1;
var hasRequiredPostcss;

function requirePostcss () {
	if (hasRequiredPostcss) return postcss_1;
	hasRequiredPostcss = 1;

	let CssSyntaxError = requireCssSyntaxError();
	let Declaration = requireDeclaration();
	let LazyResult = requireLazyResult();
	let Container = requireContainer();
	let Processor = requireProcessor();
	let stringify = requireStringify();
	let fromJSON = requireFromJSON();
	let Document = requireDocument();
	let Warning = requireWarning();
	let Comment = requireComment();
	let AtRule = requireAtRule();
	let Result = requireResult();
	let Input = requireInput();
	let parse = requireParse();
	let list = requireList();
	let Rule = requireRule();
	let Root = requireRoot();
	let Node = requireNode();

	function postcss(...plugins) {
	  if (plugins.length === 1 && Array.isArray(plugins[0])) {
	    plugins = plugins[0];
	  }
	  return new Processor(plugins)
	}

	postcss.plugin = function plugin(name, initializer) {
	  let warningPrinted = false;
	  function creator(...args) {
	    // eslint-disable-next-line no-console
	    if (console && console.warn && !warningPrinted) {
	      warningPrinted = true;
	      // eslint-disable-next-line no-console
	      console.warn(
	        name +
	          ': postcss.plugin was deprecated. Migration guide:\n' +
	          'https://evilmartians.com/chronicles/postcss-8-plugin-migration'
	      );
	      if (process.env.LANG && process.env.LANG.startsWith('cn')) {
	        /* c8 ignore next 7 */
	        // eslint-disable-next-line no-console
	        console.warn(
	          name +
	            ': 里面 postcss.plugin 被弃用. 迁移指南:\n' +
	            'https://www.w3ctech.com/topic/2226'
	        );
	      }
	    }
	    let transformer = initializer(...args);
	    transformer.postcssPlugin = name;
	    transformer.postcssVersion = new Processor().version;
	    return transformer
	  }

	  let cache;
	  Object.defineProperty(creator, 'postcss', {
	    get() {
	      if (!cache) cache = creator();
	      return cache
	    }
	  });

	  creator.process = function (css, processOpts, pluginOpts) {
	    return postcss([creator(pluginOpts)]).process(css, processOpts)
	  };

	  return creator
	};

	postcss.stringify = stringify;
	postcss.parse = parse;
	postcss.fromJSON = fromJSON;
	postcss.list = list;

	postcss.comment = defaults => new Comment(defaults);
	postcss.atRule = defaults => new AtRule(defaults);
	postcss.decl = defaults => new Declaration(defaults);
	postcss.rule = defaults => new Rule(defaults);
	postcss.root = defaults => new Root(defaults);
	postcss.document = defaults => new Document(defaults);

	postcss.CssSyntaxError = CssSyntaxError;
	postcss.Declaration = Declaration;
	postcss.Container = Container;
	postcss.Processor = Processor;
	postcss.Document = Document;
	postcss.Comment = Comment;
	postcss.Warning = Warning;
	postcss.AtRule = AtRule;
	postcss.Result = Result;
	postcss.Input = Input;
	postcss.Rule = Rule;
	postcss.Root = Root;
	postcss.Node = Node;

	LazyResult.registerPostcss(postcss);

	postcss_1 = postcss;
	postcss.default = postcss;
	return postcss_1;
}

var postcssExports = requirePostcss();
var postcss = /*@__PURE__*/getDefaultExportFromCjs(postcssExports);

postcss.stringify;
postcss.fromJSON;
postcss.plugin;
postcss.parse;
postcss.list;

postcss.document;
postcss.comment;
postcss.atRule;
postcss.rule;
postcss.decl;
postcss.root;

postcss.CssSyntaxError;
postcss.Declaration;
postcss.Container;
postcss.Processor;
postcss.Document;
postcss.Comment;
postcss.Warning;
postcss.AtRule;
postcss.Result;
postcss.Input;
postcss.Rule;
postcss.Root;
postcss.Node;

function iu(){return {async:!1,breaks:!1,extensions:null,gfm:!0,hooks:null,pedantic:!1,renderer:null,silent:!1,tokenizer:null,walkTokens:null}}let be$1=iu();function Xu(t){be$1=t;}const Wu=/[&<>"']/,Vt$1=new RegExp(Wu.source,"g"),Qu=/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,Zt$1=new RegExp(Qu.source,"g"),Xt={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},vu=t=>Xt[t];function Q$1(t,e){if(e){if(Wu.test(t))return t.replace(Vt$1,vu)}else if(Qu.test(t))return t.replace(Zt$1,vu);return t}const Wt$1=/&(#(?:\d+)|(?:#x[0-9A-Fa-f]+)|(?:\w+));?/ig;function Qt(t){return t.replace(Wt$1,(e,u)=>(u=u.toLowerCase(),u==="colon"?":":u.charAt(0)==="#"?u.charAt(1)==="x"?String.fromCharCode(parseInt(u.substring(2),16)):String.fromCharCode(+u.substring(1)):""))}const Kt$1=/(^|[^\[])\^/g;function P$1(t,e){let u=typeof t=="string"?t:t.source;e=e||"";const n={replace:(r,a)=>{let i=typeof a=="string"?a:a.source;return i=i.replace(Kt$1,"$1"),u=u.replace(r,i),n},getRegex:()=>new RegExp(u,e)};return n}function wu(t){try{t=encodeURI(t).replace(/%25/g,"%");}catch{return null}return t}const Ee$1={exec:()=>null};function Tu(t,e){const u=t.replace(/\|/g,(a,i,l)=>{let c=!1,d=i;for(;--d>=0&&l[d]==="\\";)c=!c;return c?"|":" |"}),n=u.split(/ \|/);let r=0;if(n[0].trim()||n.shift(),n.length>0&&!n[n.length-1].trim()&&n.pop(),e)if(n.length>e)n.splice(e);else for(;n.length<e;)n.push("");for(;r<n.length;r++)n[r]=n[r].trim().replace(/\\\|/g,"|");return n}function Ie$1(t,e,u){const n=t.length;if(n===0)return "";let r=0;for(;r<n;){const a=t.charAt(n-r-1);if(a===e&&!u)r++;else if(a!==e&&u)r++;else break}return t.slice(0,n-r)}function Yt$1(t,e){if(t.indexOf(e[1])===-1)return -1;let u=0;for(let n=0;n<t.length;n++)if(t[n]==="\\")n++;else if(t[n]===e[0])u++;else if(t[n]===e[1]&&(u--,u<0))return n;return -1}function Cu(t,e,u,n){const r=e.href,a=e.title?Q$1(e.title):null,i=t[1].replace(/\\([\[\]])/g,"$1");if(t[0].charAt(0)!=="!"){n.state.inLink=!0;const l={type:"link",raw:u,href:r,title:a,text:i,tokens:n.inlineTokens(i)};return n.state.inLink=!1,l}return {type:"image",raw:u,href:r,title:a,text:Q$1(i)}}function Jt$1(t,e){const u=t.match(/^(\s+)(?:```)/);if(u===null)return e;const n=u[1];return e.split(`
`).map(r=>{const a=r.match(/^\s+/);if(a===null)return r;const[i]=a;return i.length>=n.length?r.slice(n.length):r}).join(`
`)}let Me$1 = class Me{options;rules;lexer;constructor(e){this.options=e||be$1;}space(e){const u=this.rules.block.newline.exec(e);if(u&&u[0].length>0)return {type:"space",raw:u[0]}}code(e){const u=this.rules.block.code.exec(e);if(u){const n=u[0].replace(/^ {1,4}/gm,"");return {type:"code",raw:u[0],codeBlockStyle:"indented",text:this.options.pedantic?n:Ie$1(n,`
`)}}}fences(e){const u=this.rules.block.fences.exec(e);if(u){const n=u[0],r=Jt$1(n,u[3]||"");return {type:"code",raw:n,lang:u[2]?u[2].trim().replace(this.rules.inline.anyPunctuation,"$1"):u[2],text:r}}}heading(e){const u=this.rules.block.heading.exec(e);if(u){let n=u[2].trim();if(/#$/.test(n)){const r=Ie$1(n,"#");(this.options.pedantic||!r||/ $/.test(r))&&(n=r.trim());}return {type:"heading",raw:u[0],depth:u[1].length,text:n,tokens:this.lexer.inline(n)}}}hr(e){const u=this.rules.block.hr.exec(e);if(u)return {type:"hr",raw:u[0]}}blockquote(e){const u=this.rules.block.blockquote.exec(e);if(u){const n=Ie$1(u[0].replace(/^ *>[ \t]?/gm,""),`
`),r=this.lexer.state.top;this.lexer.state.top=!0;const a=this.lexer.blockTokens(n);return this.lexer.state.top=r,{type:"blockquote",raw:u[0],tokens:a,text:n}}}list(e){let u=this.rules.block.list.exec(e);if(u){let n=u[1].trim();const r=n.length>1,a={type:"list",raw:"",ordered:r,start:r?+n.slice(0,-1):"",loose:!1,items:[]};n=r?`\\d{1,9}\\${n.slice(-1)}`:`\\${n}`,this.options.pedantic&&(n=r?n:"[*+-]");const i=new RegExp(`^( {0,3}${n})((?:[	 ][^\\n]*)?(?:\\n|$))`);let l="",c="",d=!1;for(;e;){let f=!1;if(!(u=i.exec(e))||this.rules.block.hr.test(e))break;l=u[0],e=e.substring(l.length);let h=u[2].split(`
`,1)[0].replace(/^\t+/,v=>" ".repeat(3*v.length)),s=e.split(`
`,1)[0],o=0;this.options.pedantic?(o=2,c=h.trimStart()):(o=u[2].search(/[^ ]/),o=o>4?1:o,c=h.slice(o),o+=u[1].length);let D=!1;if(!h&&/^ *$/.test(s)&&(l+=s+`
`,e=e.substring(s.length+1),f=!0),!f){const v=new RegExp(`^ {0,${Math.min(3,o-1)}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`),w=new RegExp(`^ {0,${Math.min(3,o-1)}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`),C=new RegExp(`^ {0,${Math.min(3,o-1)}}(?:\`\`\`|~~~)`),S=new RegExp(`^ {0,${Math.min(3,o-1)}}#`);for(;e;){const _=e.split(`
`,1)[0];if(s=_,this.options.pedantic&&(s=s.replace(/^ {1,4}(?=( {4})*[^ ])/g,"  ")),C.test(s)||S.test(s)||v.test(s)||w.test(e))break;if(s.search(/[^ ]/)>=o||!s.trim())c+=`
`+s.slice(o);else {if(D||h.search(/[^ ]/)>=4||C.test(h)||S.test(h)||w.test(h))break;c+=`
`+s;}!D&&!s.trim()&&(D=!0),l+=_+`
`,e=e.substring(_.length+1),h=s.slice(o);}}a.loose||(d?a.loose=!0:/\n *\n *$/.test(l)&&(d=!0));let E=null,y;this.options.gfm&&(E=/^\[[ xX]\] /.exec(c),E&&(y=E[0]!=="[ ] ",c=c.replace(/^\[[ xX]\] +/,""))),a.items.push({type:"list_item",raw:l,task:!!E,checked:y,loose:!1,text:c,tokens:[]}),a.raw+=l;}a.items[a.items.length-1].raw=l.trimEnd(),a.items[a.items.length-1].text=c.trimEnd(),a.raw=a.raw.trimEnd();for(let f=0;f<a.items.length;f++)if(this.lexer.state.top=!1,a.items[f].tokens=this.lexer.blockTokens(a.items[f].text,[]),!a.loose){const h=a.items[f].tokens.filter(o=>o.type==="space"),s=h.length>0&&h.some(o=>/\n.*\n/.test(o.raw));a.loose=s;}if(a.loose)for(let f=0;f<a.items.length;f++)a.items[f].loose=!0;return a}}html(e){const u=this.rules.block.html.exec(e);if(u)return {type:"html",block:!0,raw:u[0],pre:u[1]==="pre"||u[1]==="script"||u[1]==="style",text:u[0]}}def(e){const u=this.rules.block.def.exec(e);if(u){const n=u[1].toLowerCase().replace(/\s+/g," "),r=u[2]?u[2].replace(/^<(.*)>$/,"$1").replace(this.rules.inline.anyPunctuation,"$1"):"",a=u[3]?u[3].substring(1,u[3].length-1).replace(this.rules.inline.anyPunctuation,"$1"):u[3];return {type:"def",tag:n,raw:u[0],href:r,title:a}}}table(e){const u=this.rules.block.table.exec(e);if(!u||!/[:|]/.test(u[2]))return;const n=Tu(u[1]),r=u[2].replace(/^\||\| *$/g,"").split("|"),a=u[3]&&u[3].trim()?u[3].replace(/\n[ \t]*$/,"").split(`
`):[],i={type:"table",raw:u[0],header:[],align:[],rows:[]};if(n.length===r.length){for(const l of r)/^ *-+: *$/.test(l)?i.align.push("right"):/^ *:-+: *$/.test(l)?i.align.push("center"):/^ *:-+ *$/.test(l)?i.align.push("left"):i.align.push(null);for(const l of n)i.header.push({text:l,tokens:this.lexer.inline(l)});for(const l of a)i.rows.push(Tu(l,i.header.length).map(c=>({text:c,tokens:this.lexer.inline(c)})));return i}}lheading(e){const u=this.rules.block.lheading.exec(e);if(u)return {type:"heading",raw:u[0],depth:u[2].charAt(0)==="="?1:2,text:u[1],tokens:this.lexer.inline(u[1])}}paragraph(e){const u=this.rules.block.paragraph.exec(e);if(u){const n=u[1].charAt(u[1].length-1)===`
`?u[1].slice(0,-1):u[1];return {type:"paragraph",raw:u[0],text:n,tokens:this.lexer.inline(n)}}}text(e){const u=this.rules.block.text.exec(e);if(u)return {type:"text",raw:u[0],text:u[0],tokens:this.lexer.inline(u[0])}}escape(e){const u=this.rules.inline.escape.exec(e);if(u)return {type:"escape",raw:u[0],text:Q$1(u[1])}}tag(e){const u=this.rules.inline.tag.exec(e);if(u)return !this.lexer.state.inLink&&/^<a /i.test(u[0])?this.lexer.state.inLink=!0:this.lexer.state.inLink&&/^<\/a>/i.test(u[0])&&(this.lexer.state.inLink=!1),!this.lexer.state.inRawBlock&&/^<(pre|code|kbd|script)(\s|>)/i.test(u[0])?this.lexer.state.inRawBlock=!0:this.lexer.state.inRawBlock&&/^<\/(pre|code|kbd|script)(\s|>)/i.test(u[0])&&(this.lexer.state.inRawBlock=!1),{type:"html",raw:u[0],inLink:this.lexer.state.inLink,inRawBlock:this.lexer.state.inRawBlock,block:!1,text:u[0]}}link(e){const u=this.rules.inline.link.exec(e);if(u){const n=u[2].trim();if(!this.options.pedantic&&/^</.test(n)){if(!/>$/.test(n))return;const i=Ie$1(n.slice(0,-1),"\\");if((n.length-i.length)%2===0)return}else {const i=Yt$1(u[2],"()");if(i>-1){const c=(u[0].indexOf("!")===0?5:4)+u[1].length+i;u[2]=u[2].substring(0,i),u[0]=u[0].substring(0,c).trim(),u[3]="";}}let r=u[2],a="";if(this.options.pedantic){const i=/^([^'"]*[^\s])\s+(['"])(.*)\2/.exec(r);i&&(r=i[1],a=i[3]);}else a=u[3]?u[3].slice(1,-1):"";return r=r.trim(),/^</.test(r)&&(this.options.pedantic&&!/>$/.test(n)?r=r.slice(1):r=r.slice(1,-1)),Cu(u,{href:r&&r.replace(this.rules.inline.anyPunctuation,"$1"),title:a&&a.replace(this.rules.inline.anyPunctuation,"$1")},u[0],this.lexer)}}reflink(e,u){let n;if((n=this.rules.inline.reflink.exec(e))||(n=this.rules.inline.nolink.exec(e))){const r=(n[2]||n[1]).replace(/\s+/g," "),a=u[r.toLowerCase()];if(!a){const i=n[0].charAt(0);return {type:"text",raw:i,text:i}}return Cu(n,a,n[0],this.lexer)}}emStrong(e,u,n=""){let r=this.rules.inline.emStrongLDelim.exec(e);if(!r||r[3]&&n.match(/[\p{L}\p{N}]/u))return;if(!(r[1]||r[2]||"")||!n||this.rules.inline.punctuation.exec(n)){const i=[...r[0]].length-1;let l,c,d=i,f=0;const h=r[0][0]==="*"?this.rules.inline.emStrongRDelimAst:this.rules.inline.emStrongRDelimUnd;for(h.lastIndex=0,u=u.slice(-1*e.length+i);(r=h.exec(u))!=null;){if(l=r[1]||r[2]||r[3]||r[4]||r[5]||r[6],!l)continue;if(c=[...l].length,r[3]||r[4]){d+=c;continue}else if((r[5]||r[6])&&i%3&&!((i+c)%3)){f+=c;continue}if(d-=c,d>0)continue;c=Math.min(c,c+d+f);const s=[...r[0]][0].length,o=e.slice(0,i+r.index+s+c);if(Math.min(i,c)%2){const E=o.slice(1,-1);return {type:"em",raw:o,text:E,tokens:this.lexer.inlineTokens(E)}}const D=o.slice(2,-2);return {type:"strong",raw:o,text:D,tokens:this.lexer.inlineTokens(D)}}}}codespan(e){const u=this.rules.inline.code.exec(e);if(u){let n=u[2].replace(/\n/g," ");const r=/[^ ]/.test(n),a=/^ /.test(n)&&/ $/.test(n);return r&&a&&(n=n.substring(1,n.length-1)),n=Q$1(n,!0),{type:"codespan",raw:u[0],text:n}}}br(e){const u=this.rules.inline.br.exec(e);if(u)return {type:"br",raw:u[0]}}del(e){const u=this.rules.inline.del.exec(e);if(u)return {type:"del",raw:u[0],text:u[2],tokens:this.lexer.inlineTokens(u[2])}}autolink(e){const u=this.rules.inline.autolink.exec(e);if(u){let n,r;return u[2]==="@"?(n=Q$1(u[1]),r="mailto:"+n):(n=Q$1(u[1]),r=n),{type:"link",raw:u[0],text:n,href:r,tokens:[{type:"text",raw:n,text:n}]}}}url(e){let u;if(u=this.rules.inline.url.exec(e)){let n,r;if(u[2]==="@")n=Q$1(u[0]),r="mailto:"+n;else {let a;do a=u[0],u[0]=this.rules.inline._backpedal.exec(u[0])?.[0]??"";while(a!==u[0]);n=Q$1(u[0]),u[1]==="www."?r="http://"+u[0]:r=u[0];}return {type:"link",raw:u[0],text:n,href:r,tokens:[{type:"text",raw:n,text:n}]}}}inlineText(e){const u=this.rules.inline.text.exec(e);if(u){let n;return this.lexer.state.inRawBlock?n=u[0]:n=Q$1(u[0]),{type:"text",raw:u[0],text:n}}}};const en=/^(?: *(?:\n|$))+/,un$1=/^( {4}[^\n]+(?:\n(?: *(?:\n|$))*)?)+/,tn$1=/^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/,Ce$1=/^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/,nn$1=/^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/,Ku=/(?:[*+-]|\d{1,9}[.)])/,Yu=P$1(/^(?!bull )((?:.|\n(?!\s*?\n|bull ))+?)\n {0,3}(=+|-+) *(?:\n+|$)/).replace(/bull/g,Ku).getRegex(),su=/^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/,rn$1=/^[^\n]+/,ou=/(?!\s*\])(?:\\.|[^\[\]\\])+/,an$1=P$1(/^ {0,3}\[(label)\]: *(?:\n *)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n *)?| *\n *)(title))? *(?:\n+|$)/).replace("label",ou).replace("title",/(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex(),sn$1=P$1(/^( {0,3}bull)([ \t][^\n]+?)?(?:\n|$)/).replace(/bull/g,Ku).getRegex(),Ge$1="address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul",cu=/<!--(?:-?>|[\s\S]*?(?:-->|$))/,on$1=P$1("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n *)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n *)+\\n|$))","i").replace("comment",cu).replace("tag",Ge$1).replace("attribute",/ +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(),Ju=P$1(su).replace("hr",Ce$1).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("|lheading","").replace("|table","").replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Ge$1).getRegex(),cn$1=P$1(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph",Ju).getRegex(),lu={blockquote:cn$1,code:un$1,def:an$1,fences:tn$1,heading:nn$1,hr:Ce$1,html:on$1,lheading:Yu,list:sn$1,newline:en,paragraph:Ju,table:Ee$1,text:rn$1},ku=P$1("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr",Ce$1).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("blockquote"," {0,3}>").replace("code"," {4}[^\\n]").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Ge$1).getRegex(),ln$1={...lu,table:ku,paragraph:P$1(su).replace("hr",Ce$1).replace("heading"," {0,3}#{1,6}(?:\\s|$)").replace("|lheading","").replace("table",ku).replace("blockquote"," {0,3}>").replace("fences"," {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list"," {0,3}(?:[*+-]|1[.)]) ").replace("html","</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag",Ge$1).getRegex()},dn$1={...lu,html:P$1(`^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:"[^"]*"|'[^']*'|\\s[^'"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))`).replace("comment",cu).replace(/tag/g,"(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(),def:/^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/,heading:/^(#{1,6})(.*)(?:\n+|$)/,fences:Ee$1,lheading:/^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/,paragraph:P$1(su).replace("hr",Ce$1).replace("heading",` *#{1,6} *[^
]`).replace("lheading",Yu).replace("|table","").replace("blockquote"," {0,3}>").replace("|fences","").replace("|list","").replace("|html","").replace("|tag","").getRegex()},et$1=/^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/,fn$1=/^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/,ut$2=/^( {2,}|\\)\n(?!\s*$)/,pn$1=/^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/,ke="\\p{P}\\p{S}",bn=P$1(/^((?![*_])[\spunctuation])/,"u").replace(/punctuation/g,ke).getRegex(),hn=/\[[^[\]]*?\]\([^\(\)]*?\)|`[^`]*?`|<[^<>]*?>/g,gn=P$1(/^(?:\*+(?:((?!\*)[punct])|[^\s*]))|^_+(?:((?!_)[punct])|([^\s_]))/,"u").replace(/punct/g,ke).getRegex(),mn=P$1("^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)[punct](\\*+)(?=[\\s]|$)|[^punct\\s](\\*+)(?!\\*)(?=[punct\\s]|$)|(?!\\*)[punct\\s](\\*+)(?=[^punct\\s])|[\\s](\\*+)(?!\\*)(?=[punct])|(?!\\*)[punct](\\*+)(?!\\*)(?=[punct])|[^punct\\s](\\*+)(?=[^punct\\s])","gu").replace(/punct/g,ke).getRegex(),Dn=P$1("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)[punct](_+)(?=[\\s]|$)|[^punct\\s](_+)(?!_)(?=[punct\\s]|$)|(?!_)[punct\\s](_+)(?=[^punct\\s])|[\\s](_+)(?!_)(?=[punct])|(?!_)[punct](_+)(?!_)(?=[punct])","gu").replace(/punct/g,ke).getRegex(),xn=P$1(/\\([punct])/,"gu").replace(/punct/g,ke).getRegex(),An$1=P$1(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme",/[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email",/[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex(),En=P$1(cu).replace("(?:-->|$)","-->").getRegex(),yn=P$1("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment",En).replace("attribute",/\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex(),qe=/(?:\[(?:\\.|[^\[\]\\])*\]|\\.|`[^`]*`|[^\[\]\\`])*?/,vn$1=P$1(/^!?\[(label)\]\(\s*(href)(?:\s+(title))?\s*\)/).replace("label",qe).replace("href",/<(?:\\.|[^\n<>\\])+>|[^\s\x00-\x1f]*/).replace("title",/"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex(),tt$1=P$1(/^!?\[(label)\]\[(ref)\]/).replace("label",qe).replace("ref",ou).getRegex(),nt$1=P$1(/^!?\[(ref)\](?:\[\])?/).replace("ref",ou).getRegex(),wn=P$1("reflink|nolink(?!\\()","g").replace("reflink",tt$1).replace("nolink",nt$1).getRegex(),du={_backpedal:Ee$1,anyPunctuation:xn,autolink:An$1,blockSkip:hn,br:ut$2,code:fn$1,del:Ee$1,emStrongLDelim:gn,emStrongRDelimAst:mn,emStrongRDelimUnd:Dn,escape:et$1,link:vn$1,nolink:nt$1,punctuation:bn,reflink:tt$1,reflinkSearch:wn,tag:yn,text:pn$1,url:Ee$1},Tn={...du,link:P$1(/^!?\[(label)\]\((.*?)\)/).replace("label",qe).getRegex(),reflink:P$1(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label",qe).getRegex()},tu={...du,escape:P$1(et$1).replace("])","~|])").getRegex(),url:P$1(/^((?:ftp|https?):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/,"i").replace("email",/[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(),_backpedal:/(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/,del:/^(~~?)(?=[^\s~])([\s\S]*?[^\s~])\1(?=[^~]|$)/,text:/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|https?:\/\/|ftp:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/},Cn={...tu,br:P$1(ut$2).replace("{2,}","*").getRegex(),text:P$1(tu.text).replace("\\b_","\\b_| {2,}\\n").replace(/\{2,\}/g,"*").getRegex()},Ne={normal:lu,gfm:ln$1,pedantic:dn$1},xe$1={normal:du,gfm:tu,breaks:Cn,pedantic:Tn};let ue$1 = class ue{tokens;options;state;tokenizer;inlineQueue;constructor(e){this.tokens=[],this.tokens.links=Object.create(null),this.options=e||be$1,this.options.tokenizer=this.options.tokenizer||new Me$1,this.tokenizer=this.options.tokenizer,this.tokenizer.options=this.options,this.tokenizer.lexer=this,this.inlineQueue=[],this.state={inLink:!1,inRawBlock:!1,top:!0};const u={block:Ne.normal,inline:xe$1.normal};this.options.pedantic?(u.block=Ne.pedantic,u.inline=xe$1.pedantic):this.options.gfm&&(u.block=Ne.gfm,this.options.breaks?u.inline=xe$1.breaks:u.inline=xe$1.gfm),this.tokenizer.rules=u;}static get rules(){return {block:Ne,inline:xe$1}}static lex(e,u){return new ue(u).lex(e)}static lexInline(e,u){return new ue(u).inlineTokens(e)}lex(e){e=e.replace(/\r\n|\r/g,`
`),this.blockTokens(e,this.tokens);for(let u=0;u<this.inlineQueue.length;u++){const n=this.inlineQueue[u];this.inlineTokens(n.src,n.tokens);}return this.inlineQueue=[],this.tokens}blockTokens(e,u=[]){this.options.pedantic?e=e.replace(/\t/g,"    ").replace(/^ +$/gm,""):e=e.replace(/^( *)(\t+)/gm,(l,c,d)=>c+"    ".repeat(d.length));let n,r,a,i;for(;e;)if(!(this.options.extensions&&this.options.extensions.block&&this.options.extensions.block.some(l=>(n=l.call({lexer:this},e,u))?(e=e.substring(n.raw.length),u.push(n),!0):!1))){if(n=this.tokenizer.space(e)){e=e.substring(n.raw.length),n.raw.length===1&&u.length>0?u[u.length-1].raw+=`
`:u.push(n);continue}if(n=this.tokenizer.code(e)){e=e.substring(n.raw.length),r=u[u.length-1],r&&(r.type==="paragraph"||r.type==="text")?(r.raw+=`
`+n.raw,r.text+=`
`+n.text,this.inlineQueue[this.inlineQueue.length-1].src=r.text):u.push(n);continue}if(n=this.tokenizer.fences(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.heading(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.hr(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.blockquote(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.list(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.html(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.def(e)){e=e.substring(n.raw.length),r=u[u.length-1],r&&(r.type==="paragraph"||r.type==="text")?(r.raw+=`
`+n.raw,r.text+=`
`+n.raw,this.inlineQueue[this.inlineQueue.length-1].src=r.text):this.tokens.links[n.tag]||(this.tokens.links[n.tag]={href:n.href,title:n.title});continue}if(n=this.tokenizer.table(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.lheading(e)){e=e.substring(n.raw.length),u.push(n);continue}if(a=e,this.options.extensions&&this.options.extensions.startBlock){let l=1/0;const c=e.slice(1);let d;this.options.extensions.startBlock.forEach(f=>{d=f.call({lexer:this},c),typeof d=="number"&&d>=0&&(l=Math.min(l,d));}),l<1/0&&l>=0&&(a=e.substring(0,l+1));}if(this.state.top&&(n=this.tokenizer.paragraph(a))){r=u[u.length-1],i&&r.type==="paragraph"?(r.raw+=`
`+n.raw,r.text+=`
`+n.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=r.text):u.push(n),i=a.length!==e.length,e=e.substring(n.raw.length);continue}if(n=this.tokenizer.text(e)){e=e.substring(n.raw.length),r=u[u.length-1],r&&r.type==="text"?(r.raw+=`
`+n.raw,r.text+=`
`+n.text,this.inlineQueue.pop(),this.inlineQueue[this.inlineQueue.length-1].src=r.text):u.push(n);continue}if(e){const l="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(l);break}else throw new Error(l)}}return this.state.top=!0,u}inline(e,u=[]){return this.inlineQueue.push({src:e,tokens:u}),u}inlineTokens(e,u=[]){let n,r,a,i=e,l,c,d;if(this.tokens.links){const f=Object.keys(this.tokens.links);if(f.length>0)for(;(l=this.tokenizer.rules.inline.reflinkSearch.exec(i))!=null;)f.includes(l[0].slice(l[0].lastIndexOf("[")+1,-1))&&(i=i.slice(0,l.index)+"["+"a".repeat(l[0].length-2)+"]"+i.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex));}for(;(l=this.tokenizer.rules.inline.blockSkip.exec(i))!=null;)i=i.slice(0,l.index)+"["+"a".repeat(l[0].length-2)+"]"+i.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);for(;(l=this.tokenizer.rules.inline.anyPunctuation.exec(i))!=null;)i=i.slice(0,l.index)+"++"+i.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);for(;e;)if(c||(d=""),c=!1,!(this.options.extensions&&this.options.extensions.inline&&this.options.extensions.inline.some(f=>(n=f.call({lexer:this},e,u))?(e=e.substring(n.raw.length),u.push(n),!0):!1))){if(n=this.tokenizer.escape(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.tag(e)){e=e.substring(n.raw.length),r=u[u.length-1],r&&n.type==="text"&&r.type==="text"?(r.raw+=n.raw,r.text+=n.text):u.push(n);continue}if(n=this.tokenizer.link(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.reflink(e,this.tokens.links)){e=e.substring(n.raw.length),r=u[u.length-1],r&&n.type==="text"&&r.type==="text"?(r.raw+=n.raw,r.text+=n.text):u.push(n);continue}if(n=this.tokenizer.emStrong(e,i,d)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.codespan(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.br(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.del(e)){e=e.substring(n.raw.length),u.push(n);continue}if(n=this.tokenizer.autolink(e)){e=e.substring(n.raw.length),u.push(n);continue}if(!this.state.inLink&&(n=this.tokenizer.url(e))){e=e.substring(n.raw.length),u.push(n);continue}if(a=e,this.options.extensions&&this.options.extensions.startInline){let f=1/0;const h=e.slice(1);let s;this.options.extensions.startInline.forEach(o=>{s=o.call({lexer:this},h),typeof s=="number"&&s>=0&&(f=Math.min(f,s));}),f<1/0&&f>=0&&(a=e.substring(0,f+1));}if(n=this.tokenizer.inlineText(a)){e=e.substring(n.raw.length),n.raw.slice(-1)!=="_"&&(d=n.raw.slice(-1)),c=!0,r=u[u.length-1],r&&r.type==="text"?(r.raw+=n.raw,r.text+=n.text):u.push(n);continue}if(e){const f="Infinite loop on byte: "+e.charCodeAt(0);if(this.options.silent){console.error(f);break}else throw new Error(f)}}return u}};let Ue$1 = class Ue{options;constructor(e){this.options=e||be$1;}code(e,u,n){const r=(u||"").match(/^\S*/)?.[0];return e=e.replace(/\n$/,"")+`
`,r?'<pre><code class="language-'+Q$1(r)+'">'+(n?e:Q$1(e,!0))+`</code></pre>
`:"<pre><code>"+(n?e:Q$1(e,!0))+`</code></pre>
`}blockquote(e){return `<blockquote>
${e}</blockquote>
`}html(e,u){return e}heading(e,u,n){return `<h${u}>${e}</h${u}>
`}hr(){return `<hr>
`}list(e,u,n){const r=u?"ol":"ul",a=u&&n!==1?' start="'+n+'"':"";return "<"+r+a+`>
`+e+"</"+r+`>
`}listitem(e,u,n){return `<li>${e}</li>
`}checkbox(e){return "<input "+(e?'checked="" ':"")+'disabled="" type="checkbox">'}paragraph(e){return `<p>${e}</p>
`}table(e,u){return u&&(u=`<tbody>${u}</tbody>`),`<table>
<thead>
`+e+`</thead>
`+u+`</table>
`}tablerow(e){return `<tr>
${e}</tr>
`}tablecell(e,u){const n=u.header?"th":"td";return (u.align?`<${n} align="${u.align}">`:`<${n}>`)+e+`</${n}>
`}strong(e){return `<strong>${e}</strong>`}em(e){return `<em>${e}</em>`}codespan(e){return `<code>${e}</code>`}br(){return "<br>"}del(e){return `<del>${e}</del>`}link(e,u,n){const r=wu(e);if(r===null)return n;e=r;let a='<a href="'+e+'"';return u&&(a+=' title="'+u+'"'),a+=">"+n+"</a>",a}image(e,u,n){const r=wu(e);if(r===null)return n;e=r;let a=`<img src="${e}" alt="${n}"`;return u&&(a+=` title="${u}"`),a+=">",a}text(e){return e}};class fu{strong(e){return e}em(e){return e}codespan(e){return e}del(e){return e}html(e){return e}text(e){return e}link(e,u,n){return ""+n}image(e,u,n){return ""+n}br(){return ""}}let te$1 = class te{options;renderer;textRenderer;constructor(e){this.options=e||be$1,this.options.renderer=this.options.renderer||new Ue$1,this.renderer=this.options.renderer,this.renderer.options=this.options,this.textRenderer=new fu;}static parse(e,u){return new te(u).parse(e)}static parseInline(e,u){return new te(u).parseInline(e)}parse(e,u=!0){let n="";for(let r=0;r<e.length;r++){const a=e[r];if(this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[a.type]){const i=a,l=this.options.extensions.renderers[i.type].call({parser:this},i);if(l!==!1||!["space","hr","heading","code","table","blockquote","list","html","paragraph","text"].includes(i.type)){n+=l||"";continue}}switch(a.type){case"space":continue;case"hr":{n+=this.renderer.hr();continue}case"heading":{const i=a;n+=this.renderer.heading(this.parseInline(i.tokens),i.depth,Qt(this.parseInline(i.tokens,this.textRenderer)));continue}case"code":{const i=a;n+=this.renderer.code(i.text,i.lang,!!i.escaped);continue}case"table":{const i=a;let l="",c="";for(let f=0;f<i.header.length;f++)c+=this.renderer.tablecell(this.parseInline(i.header[f].tokens),{header:!0,align:i.align[f]});l+=this.renderer.tablerow(c);let d="";for(let f=0;f<i.rows.length;f++){const h=i.rows[f];c="";for(let s=0;s<h.length;s++)c+=this.renderer.tablecell(this.parseInline(h[s].tokens),{header:!1,align:i.align[s]});d+=this.renderer.tablerow(c);}n+=this.renderer.table(l,d);continue}case"blockquote":{const i=a,l=this.parse(i.tokens);n+=this.renderer.blockquote(l);continue}case"list":{const i=a,l=i.ordered,c=i.start,d=i.loose;let f="";for(let h=0;h<i.items.length;h++){const s=i.items[h],o=s.checked,D=s.task;let E="";if(s.task){const y=this.renderer.checkbox(!!o);d?s.tokens.length>0&&s.tokens[0].type==="paragraph"?(s.tokens[0].text=y+" "+s.tokens[0].text,s.tokens[0].tokens&&s.tokens[0].tokens.length>0&&s.tokens[0].tokens[0].type==="text"&&(s.tokens[0].tokens[0].text=y+" "+s.tokens[0].tokens[0].text)):s.tokens.unshift({type:"text",text:y+" "}):E+=y+" ";}E+=this.parse(s.tokens,d),f+=this.renderer.listitem(E,D,!!o);}n+=this.renderer.list(f,l,c);continue}case"html":{const i=a;n+=this.renderer.html(i.text,i.block);continue}case"paragraph":{const i=a;n+=this.renderer.paragraph(this.parseInline(i.tokens));continue}case"text":{let i=a,l=i.tokens?this.parseInline(i.tokens):i.text;for(;r+1<e.length&&e[r+1].type==="text";)i=e[++r],l+=`
`+(i.tokens?this.parseInline(i.tokens):i.text);n+=u?this.renderer.paragraph(l):l;continue}default:{const i='Token with "'+a.type+'" type was not found.';if(this.options.silent)return console.error(i),"";throw new Error(i)}}}return n}parseInline(e,u){u=u||this.renderer;let n="";for(let r=0;r<e.length;r++){const a=e[r];if(this.options.extensions&&this.options.extensions.renderers&&this.options.extensions.renderers[a.type]){const i=this.options.extensions.renderers[a.type].call({parser:this},a);if(i!==!1||!["escape","html","link","image","strong","em","codespan","br","del","text"].includes(a.type)){n+=i||"";continue}}switch(a.type){case"escape":{const i=a;n+=u.text(i.text);break}case"html":{const i=a;n+=u.html(i.text);break}case"link":{const i=a;n+=u.link(i.href,i.title,this.parseInline(i.tokens,u));break}case"image":{const i=a;n+=u.image(i.href,i.title,i.text);break}case"strong":{const i=a;n+=u.strong(this.parseInline(i.tokens,u));break}case"em":{const i=a;n+=u.em(this.parseInline(i.tokens,u));break}case"codespan":{const i=a;n+=u.codespan(i.text);break}case"br":{n+=u.br();break}case"del":{const i=a;n+=u.del(this.parseInline(i.tokens,u));break}case"text":{const i=a;n+=u.text(i.text);break}default:{const i='Token with "'+a.type+'" type was not found.';if(this.options.silent)return console.error(i),"";throw new Error(i)}}}return n}};class Le{options;constructor(e){this.options=e||be$1;}static passThroughHooks=new Set(["preprocess","postprocess","processAllTokens"]);preprocess(e){return e}postprocess(e){return e}processAllTokens(e){return e}}let rt$1 = class rt{defaults=iu();options=this.setOptions;parse=this.#e(ue$1.lex,te$1.parse);parseInline=this.#e(ue$1.lexInline,te$1.parseInline);Parser=te$1;Renderer=Ue$1;TextRenderer=fu;Lexer=ue$1;Tokenizer=Me$1;Hooks=Le;constructor(...e){this.use(...e);}walkTokens(e,u){let n=[];for(const r of e)switch(n=n.concat(u.call(this,r)),r.type){case"table":{const a=r;for(const i of a.header)n=n.concat(this.walkTokens(i.tokens,u));for(const i of a.rows)for(const l of i)n=n.concat(this.walkTokens(l.tokens,u));break}case"list":{const a=r;n=n.concat(this.walkTokens(a.items,u));break}default:{const a=r;this.defaults.extensions?.childTokens?.[a.type]?this.defaults.extensions.childTokens[a.type].forEach(i=>{const l=a[i].flat(1/0);n=n.concat(this.walkTokens(l,u));}):a.tokens&&(n=n.concat(this.walkTokens(a.tokens,u)));}}return n}use(...e){const u=this.defaults.extensions||{renderers:{},childTokens:{}};return e.forEach(n=>{const r={...n};if(r.async=this.defaults.async||r.async||!1,n.extensions&&(n.extensions.forEach(a=>{if(!a.name)throw new Error("extension name required");if("renderer"in a){const i=u.renderers[a.name];i?u.renderers[a.name]=function(...l){let c=a.renderer.apply(this,l);return c===!1&&(c=i.apply(this,l)),c}:u.renderers[a.name]=a.renderer;}if("tokenizer"in a){if(!a.level||a.level!=="block"&&a.level!=="inline")throw new Error("extension level must be 'block' or 'inline'");const i=u[a.level];i?i.unshift(a.tokenizer):u[a.level]=[a.tokenizer],a.start&&(a.level==="block"?u.startBlock?u.startBlock.push(a.start):u.startBlock=[a.start]:a.level==="inline"&&(u.startInline?u.startInline.push(a.start):u.startInline=[a.start]));}"childTokens"in a&&a.childTokens&&(u.childTokens[a.name]=a.childTokens);}),r.extensions=u),n.renderer){const a=this.defaults.renderer||new Ue$1(this.defaults);for(const i in n.renderer){if(!(i in a))throw new Error(`renderer '${i}' does not exist`);if(i==="options")continue;const l=i,c=n.renderer[l],d=a[l];a[l]=(...f)=>{let h=c.apply(a,f);return h===!1&&(h=d.apply(a,f)),h||""};}r.renderer=a;}if(n.tokenizer){const a=this.defaults.tokenizer||new Me$1(this.defaults);for(const i in n.tokenizer){if(!(i in a))throw new Error(`tokenizer '${i}' does not exist`);if(["options","rules","lexer"].includes(i))continue;const l=i,c=n.tokenizer[l],d=a[l];a[l]=(...f)=>{let h=c.apply(a,f);return h===!1&&(h=d.apply(a,f)),h};}r.tokenizer=a;}if(n.hooks){const a=this.defaults.hooks||new Le;for(const i in n.hooks){if(!(i in a))throw new Error(`hook '${i}' does not exist`);if(i==="options")continue;const l=i,c=n.hooks[l],d=a[l];Le.passThroughHooks.has(i)?a[l]=f=>{if(this.defaults.async)return Promise.resolve(c.call(a,f)).then(s=>d.call(a,s));const h=c.call(a,f);return d.call(a,h)}:a[l]=(...f)=>{let h=c.apply(a,f);return h===!1&&(h=d.apply(a,f)),h};}r.hooks=a;}if(n.walkTokens){const a=this.defaults.walkTokens,i=n.walkTokens;r.walkTokens=function(l){let c=[];return c.push(i.call(this,l)),a&&(c=c.concat(a.call(this,l))),c};}this.defaults={...this.defaults,...r};}),this}setOptions(e){return this.defaults={...this.defaults,...e},this}lexer(e,u){return ue$1.lex(e,u??this.defaults)}parser(e,u){return te$1.parse(e,u??this.defaults)}#e(e,u){return (n,r)=>{const a={...r},i={...this.defaults,...a};this.defaults.async===!0&&a.async===!1&&(i.silent||console.warn("marked(): The async option was set to true by an extension. The async: false option sent to parse will be ignored."),i.async=!0);const l=this.#u(!!i.silent,!!i.async);if(typeof n>"u"||n===null)return l(new Error("marked(): input parameter is undefined or null"));if(typeof n!="string")return l(new Error("marked(): input parameter is of type "+Object.prototype.toString.call(n)+", string expected"));if(i.hooks&&(i.hooks.options=i),i.async)return Promise.resolve(i.hooks?i.hooks.preprocess(n):n).then(c=>e(c,i)).then(c=>i.hooks?i.hooks.processAllTokens(c):c).then(c=>i.walkTokens?Promise.all(this.walkTokens(c,i.walkTokens)).then(()=>c):c).then(c=>u(c,i)).then(c=>i.hooks?i.hooks.postprocess(c):c).catch(l);try{i.hooks&&(n=i.hooks.preprocess(n));let c=e(n,i);i.hooks&&(c=i.hooks.processAllTokens(c)),i.walkTokens&&this.walkTokens(c,i.walkTokens);let d=u(c,i);return i.hooks&&(d=i.hooks.postprocess(d)),d}catch(c){return l(c)}}}#u(e,u){return n=>{if(n.message+=`
Please report this to https://github.com/markedjs/marked.`,e){const r="<p>An error occurred:</p><pre>"+Q$1(n.message+"",!0)+"</pre>";return u?Promise.resolve(r):r}if(u)return Promise.reject(n);throw n}}};const fe$1=new rt$1;function R(t,e){return fe$1.parse(t,e)}R.options=R.setOptions=function(t){return fe$1.setOptions(t),R.defaults=fe$1.defaults,Xu(R.defaults),R};R.getDefaults=iu;R.defaults=be$1;R.use=function(...t){return fe$1.use(...t),R.defaults=fe$1.defaults,Xu(R.defaults),R};R.walkTokens=function(t,e){return fe$1.walkTokens(t,e)};R.parseInline=fe$1.parseInline;R.Parser=te$1;R.parser=te$1.parse;R.Renderer=Ue$1;R.TextRenderer=fu;R.Lexer=ue$1;R.lexer=ue$1.lex;R.Tokenizer=Me$1;R.Hooks=Le;R.parse=R;R.options;R.setOptions;R.use;R.walkTokens;R.parseInline;te$1.parse;ue$1.lex;function kn(t){if(typeof t=="function"&&(t={highlight:t}),!t||typeof t.highlight!="function")throw new Error("Must provide highlight function");return typeof t.langPrefix!="string"&&(t.langPrefix="language-"),typeof t.emptyLangClass!="string"&&(t.emptyLangClass=""),{async:!!t.async,walkTokens(e){if(e.type!=="code")return;const u=Fu(e.lang);if(t.async)return Promise.resolve(t.highlight(e.text,u,e.lang||"")).then(Su(e));const n=t.highlight(e.text,u,e.lang||"");if(n instanceof Promise)throw new Error("markedHighlight is not set to async but the highlight function is async. Set the async option to true on markedHighlight to await the async highlight function.");Su(e)(n);},useNewRenderer:!0,renderer:{code(e,u,n){typeof e=="object"&&(n=e.escaped,u=e.lang,e=e.text);const r=Fu(u),a=r?t.langPrefix+Iu(r):t.emptyLangClass,i=a?` class="${a}"`:"";return e=e.replace(/\n$/,""),`<pre><code${i}>${n?e:Iu(e,!0)}
</code></pre>`}}}}function Fu(t){return (t||"").match(/\S*/)[0]}function Su(t){return e=>{typeof e=="string"&&e!==t.text&&(t.escaped=!0,t.text=e);}}const at$4=/[&<>"']/,Fn=new RegExp(at$4.source,"g"),it$2=/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,Sn=new RegExp(it$2.source,"g"),_n$1={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},_u=t=>_n$1[t];function Iu(t,e){if(e){if(at$4.test(t))return t.replace(Fn,_u)}else if(it$2.test(t))return t.replace(Sn,_u);return t}const In=/[\0-\x1F!-,\.\/:-@\[-\^`\{-\xA9\xAB-\xB4\xB6-\xB9\xBB-\xBF\xD7\xF7\u02C2-\u02C5\u02D2-\u02DF\u02E5-\u02EB\u02ED\u02EF-\u02FF\u0375\u0378\u0379\u037E\u0380-\u0385\u0387\u038B\u038D\u03A2\u03F6\u0482\u0530\u0557\u0558\u055A-\u055F\u0589-\u0590\u05BE\u05C0\u05C3\u05C6\u05C8-\u05CF\u05EB-\u05EE\u05F3-\u060F\u061B-\u061F\u066A-\u066D\u06D4\u06DD\u06DE\u06E9\u06FD\u06FE\u0700-\u070F\u074B\u074C\u07B2-\u07BF\u07F6-\u07F9\u07FB\u07FC\u07FE\u07FF\u082E-\u083F\u085C-\u085F\u086B-\u089F\u08B5\u08C8-\u08D2\u08E2\u0964\u0965\u0970\u0984\u098D\u098E\u0991\u0992\u09A9\u09B1\u09B3-\u09B5\u09BA\u09BB\u09C5\u09C6\u09C9\u09CA\u09CF-\u09D6\u09D8-\u09DB\u09DE\u09E4\u09E5\u09F2-\u09FB\u09FD\u09FF\u0A00\u0A04\u0A0B-\u0A0E\u0A11\u0A12\u0A29\u0A31\u0A34\u0A37\u0A3A\u0A3B\u0A3D\u0A43-\u0A46\u0A49\u0A4A\u0A4E-\u0A50\u0A52-\u0A58\u0A5D\u0A5F-\u0A65\u0A76-\u0A80\u0A84\u0A8E\u0A92\u0AA9\u0AB1\u0AB4\u0ABA\u0ABB\u0AC6\u0ACA\u0ACE\u0ACF\u0AD1-\u0ADF\u0AE4\u0AE5\u0AF0-\u0AF8\u0B00\u0B04\u0B0D\u0B0E\u0B11\u0B12\u0B29\u0B31\u0B34\u0B3A\u0B3B\u0B45\u0B46\u0B49\u0B4A\u0B4E-\u0B54\u0B58-\u0B5B\u0B5E\u0B64\u0B65\u0B70\u0B72-\u0B81\u0B84\u0B8B-\u0B8D\u0B91\u0B96-\u0B98\u0B9B\u0B9D\u0BA0-\u0BA2\u0BA5-\u0BA7\u0BAB-\u0BAD\u0BBA-\u0BBD\u0BC3-\u0BC5\u0BC9\u0BCE\u0BCF\u0BD1-\u0BD6\u0BD8-\u0BE5\u0BF0-\u0BFF\u0C0D\u0C11\u0C29\u0C3A-\u0C3C\u0C45\u0C49\u0C4E-\u0C54\u0C57\u0C5B-\u0C5F\u0C64\u0C65\u0C70-\u0C7F\u0C84\u0C8D\u0C91\u0CA9\u0CB4\u0CBA\u0CBB\u0CC5\u0CC9\u0CCE-\u0CD4\u0CD7-\u0CDD\u0CDF\u0CE4\u0CE5\u0CF0\u0CF3-\u0CFF\u0D0D\u0D11\u0D45\u0D49\u0D4F-\u0D53\u0D58-\u0D5E\u0D64\u0D65\u0D70-\u0D79\u0D80\u0D84\u0D97-\u0D99\u0DB2\u0DBC\u0DBE\u0DBF\u0DC7-\u0DC9\u0DCB-\u0DCE\u0DD5\u0DD7\u0DE0-\u0DE5\u0DF0\u0DF1\u0DF4-\u0E00\u0E3B-\u0E3F\u0E4F\u0E5A-\u0E80\u0E83\u0E85\u0E8B\u0EA4\u0EA6\u0EBE\u0EBF\u0EC5\u0EC7\u0ECE\u0ECF\u0EDA\u0EDB\u0EE0-\u0EFF\u0F01-\u0F17\u0F1A-\u0F1F\u0F2A-\u0F34\u0F36\u0F38\u0F3A-\u0F3D\u0F48\u0F6D-\u0F70\u0F85\u0F98\u0FBD-\u0FC5\u0FC7-\u0FFF\u104A-\u104F\u109E\u109F\u10C6\u10C8-\u10CC\u10CE\u10CF\u10FB\u1249\u124E\u124F\u1257\u1259\u125E\u125F\u1289\u128E\u128F\u12B1\u12B6\u12B7\u12BF\u12C1\u12C6\u12C7\u12D7\u1311\u1316\u1317\u135B\u135C\u1360-\u137F\u1390-\u139F\u13F6\u13F7\u13FE-\u1400\u166D\u166E\u1680\u169B-\u169F\u16EB-\u16ED\u16F9-\u16FF\u170D\u1715-\u171F\u1735-\u173F\u1754-\u175F\u176D\u1771\u1774-\u177F\u17D4-\u17D6\u17D8-\u17DB\u17DE\u17DF\u17EA-\u180A\u180E\u180F\u181A-\u181F\u1879-\u187F\u18AB-\u18AF\u18F6-\u18FF\u191F\u192C-\u192F\u193C-\u1945\u196E\u196F\u1975-\u197F\u19AC-\u19AF\u19CA-\u19CF\u19DA-\u19FF\u1A1C-\u1A1F\u1A5F\u1A7D\u1A7E\u1A8A-\u1A8F\u1A9A-\u1AA6\u1AA8-\u1AAF\u1AC1-\u1AFF\u1B4C-\u1B4F\u1B5A-\u1B6A\u1B74-\u1B7F\u1BF4-\u1BFF\u1C38-\u1C3F\u1C4A-\u1C4C\u1C7E\u1C7F\u1C89-\u1C8F\u1CBB\u1CBC\u1CC0-\u1CCF\u1CD3\u1CFB-\u1CFF\u1DFA\u1F16\u1F17\u1F1E\u1F1F\u1F46\u1F47\u1F4E\u1F4F\u1F58\u1F5A\u1F5C\u1F5E\u1F7E\u1F7F\u1FB5\u1FBD\u1FBF-\u1FC1\u1FC5\u1FCD-\u1FCF\u1FD4\u1FD5\u1FDC-\u1FDF\u1FED-\u1FF1\u1FF5\u1FFD-\u203E\u2041-\u2053\u2055-\u2070\u2072-\u207E\u2080-\u208F\u209D-\u20CF\u20F1-\u2101\u2103-\u2106\u2108\u2109\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A\u213B\u2140-\u2144\u214A-\u214D\u214F-\u215F\u2189-\u24B5\u24EA-\u2BFF\u2C2F\u2C5F\u2CE5-\u2CEA\u2CF4-\u2CFF\u2D26\u2D28-\u2D2C\u2D2E\u2D2F\u2D68-\u2D6E\u2D70-\u2D7E\u2D97-\u2D9F\u2DA7\u2DAF\u2DB7\u2DBF\u2DC7\u2DCF\u2DD7\u2DDF\u2E00-\u2E2E\u2E30-\u3004\u3008-\u3020\u3030\u3036\u3037\u303D-\u3040\u3097\u3098\u309B\u309C\u30A0\u30FB\u3100-\u3104\u3130\u318F-\u319F\u31C0-\u31EF\u3200-\u33FF\u4DC0-\u4DFF\u9FFD-\u9FFF\uA48D-\uA4CF\uA4FE\uA4FF\uA60D-\uA60F\uA62C-\uA63F\uA673\uA67E\uA6F2-\uA716\uA720\uA721\uA789\uA78A\uA7C0\uA7C1\uA7CB-\uA7F4\uA828-\uA82B\uA82D-\uA83F\uA874-\uA87F\uA8C6-\uA8CF\uA8DA-\uA8DF\uA8F8-\uA8FA\uA8FC\uA92E\uA92F\uA954-\uA95F\uA97D-\uA97F\uA9C1-\uA9CE\uA9DA-\uA9DF\uA9FF\uAA37-\uAA3F\uAA4E\uAA4F\uAA5A-\uAA5F\uAA77-\uAA79\uAAC3-\uAADA\uAADE\uAADF\uAAF0\uAAF1\uAAF7-\uAB00\uAB07\uAB08\uAB0F\uAB10\uAB17-\uAB1F\uAB27\uAB2F\uAB5B\uAB6A-\uAB6F\uABEB\uABEE\uABEF\uABFA-\uABFF\uD7A4-\uD7AF\uD7C7-\uD7CA\uD7FC-\uD7FF\uE000-\uF8FF\uFA6E\uFA6F\uFADA-\uFAFF\uFB07-\uFB12\uFB18-\uFB1C\uFB29\uFB37\uFB3D\uFB3F\uFB42\uFB45\uFBB2-\uFBD2\uFD3E-\uFD4F\uFD90\uFD91\uFDC8-\uFDEF\uFDFC-\uFDFF\uFE10-\uFE1F\uFE30-\uFE32\uFE35-\uFE4C\uFE50-\uFE6F\uFE75\uFEFD-\uFF0F\uFF1A-\uFF20\uFF3B-\uFF3E\uFF40\uFF5B-\uFF65\uFFBF-\uFFC1\uFFC8\uFFC9\uFFD0\uFFD1\uFFD8\uFFD9\uFFDD-\uFFFF]|\uD800[\uDC0C\uDC27\uDC3B\uDC3E\uDC4E\uDC4F\uDC5E-\uDC7F\uDCFB-\uDD3F\uDD75-\uDDFC\uDDFE-\uDE7F\uDE9D-\uDE9F\uDED1-\uDEDF\uDEE1-\uDEFF\uDF20-\uDF2C\uDF4B-\uDF4F\uDF7B-\uDF7F\uDF9E\uDF9F\uDFC4-\uDFC7\uDFD0\uDFD6-\uDFFF]|\uD801[\uDC9E\uDC9F\uDCAA-\uDCAF\uDCD4-\uDCD7\uDCFC-\uDCFF\uDD28-\uDD2F\uDD64-\uDDFF\uDF37-\uDF3F\uDF56-\uDF5F\uDF68-\uDFFF]|\uD802[\uDC06\uDC07\uDC09\uDC36\uDC39-\uDC3B\uDC3D\uDC3E\uDC56-\uDC5F\uDC77-\uDC7F\uDC9F-\uDCDF\uDCF3\uDCF6-\uDCFF\uDD16-\uDD1F\uDD3A-\uDD7F\uDDB8-\uDDBD\uDDC0-\uDDFF\uDE04\uDE07-\uDE0B\uDE14\uDE18\uDE36\uDE37\uDE3B-\uDE3E\uDE40-\uDE5F\uDE7D-\uDE7F\uDE9D-\uDEBF\uDEC8\uDEE7-\uDEFF\uDF36-\uDF3F\uDF56-\uDF5F\uDF73-\uDF7F\uDF92-\uDFFF]|\uD803[\uDC49-\uDC7F\uDCB3-\uDCBF\uDCF3-\uDCFF\uDD28-\uDD2F\uDD3A-\uDE7F\uDEAA\uDEAD-\uDEAF\uDEB2-\uDEFF\uDF1D-\uDF26\uDF28-\uDF2F\uDF51-\uDFAF\uDFC5-\uDFDF\uDFF7-\uDFFF]|\uD804[\uDC47-\uDC65\uDC70-\uDC7E\uDCBB-\uDCCF\uDCE9-\uDCEF\uDCFA-\uDCFF\uDD35\uDD40-\uDD43\uDD48-\uDD4F\uDD74\uDD75\uDD77-\uDD7F\uDDC5-\uDDC8\uDDCD\uDDDB\uDDDD-\uDDFF\uDE12\uDE38-\uDE3D\uDE3F-\uDE7F\uDE87\uDE89\uDE8E\uDE9E\uDEA9-\uDEAF\uDEEB-\uDEEF\uDEFA-\uDEFF\uDF04\uDF0D\uDF0E\uDF11\uDF12\uDF29\uDF31\uDF34\uDF3A\uDF45\uDF46\uDF49\uDF4A\uDF4E\uDF4F\uDF51-\uDF56\uDF58-\uDF5C\uDF64\uDF65\uDF6D-\uDF6F\uDF75-\uDFFF]|\uD805[\uDC4B-\uDC4F\uDC5A-\uDC5D\uDC62-\uDC7F\uDCC6\uDCC8-\uDCCF\uDCDA-\uDD7F\uDDB6\uDDB7\uDDC1-\uDDD7\uDDDE-\uDDFF\uDE41-\uDE43\uDE45-\uDE4F\uDE5A-\uDE7F\uDEB9-\uDEBF\uDECA-\uDEFF\uDF1B\uDF1C\uDF2C-\uDF2F\uDF3A-\uDFFF]|\uD806[\uDC3B-\uDC9F\uDCEA-\uDCFE\uDD07\uDD08\uDD0A\uDD0B\uDD14\uDD17\uDD36\uDD39\uDD3A\uDD44-\uDD4F\uDD5A-\uDD9F\uDDA8\uDDA9\uDDD8\uDDD9\uDDE2\uDDE5-\uDDFF\uDE3F-\uDE46\uDE48-\uDE4F\uDE9A-\uDE9C\uDE9E-\uDEBF\uDEF9-\uDFFF]|\uD807[\uDC09\uDC37\uDC41-\uDC4F\uDC5A-\uDC71\uDC90\uDC91\uDCA8\uDCB7-\uDCFF\uDD07\uDD0A\uDD37-\uDD39\uDD3B\uDD3E\uDD48-\uDD4F\uDD5A-\uDD5F\uDD66\uDD69\uDD8F\uDD92\uDD99-\uDD9F\uDDAA-\uDEDF\uDEF7-\uDFAF\uDFB1-\uDFFF]|\uD808[\uDF9A-\uDFFF]|\uD809[\uDC6F-\uDC7F\uDD44-\uDFFF]|[\uD80A\uD80B\uD80E-\uD810\uD812-\uD819\uD824-\uD82B\uD82D\uD82E\uD830-\uD833\uD837\uD839\uD83D\uD83F\uD87B-\uD87D\uD87F\uD885-\uDB3F\uDB41-\uDBFF][\uDC00-\uDFFF]|\uD80D[\uDC2F-\uDFFF]|\uD811[\uDE47-\uDFFF]|\uD81A[\uDE39-\uDE3F\uDE5F\uDE6A-\uDECF\uDEEE\uDEEF\uDEF5-\uDEFF\uDF37-\uDF3F\uDF44-\uDF4F\uDF5A-\uDF62\uDF78-\uDF7C\uDF90-\uDFFF]|\uD81B[\uDC00-\uDE3F\uDE80-\uDEFF\uDF4B-\uDF4E\uDF88-\uDF8E\uDFA0-\uDFDF\uDFE2\uDFE5-\uDFEF\uDFF2-\uDFFF]|\uD821[\uDFF8-\uDFFF]|\uD823[\uDCD6-\uDCFF\uDD09-\uDFFF]|\uD82C[\uDD1F-\uDD4F\uDD53-\uDD63\uDD68-\uDD6F\uDEFC-\uDFFF]|\uD82F[\uDC6B-\uDC6F\uDC7D-\uDC7F\uDC89-\uDC8F\uDC9A-\uDC9C\uDC9F-\uDFFF]|\uD834[\uDC00-\uDD64\uDD6A-\uDD6C\uDD73-\uDD7A\uDD83\uDD84\uDD8C-\uDDA9\uDDAE-\uDE41\uDE45-\uDFFF]|\uD835[\uDC55\uDC9D\uDCA0\uDCA1\uDCA3\uDCA4\uDCA7\uDCA8\uDCAD\uDCBA\uDCBC\uDCC4\uDD06\uDD0B\uDD0C\uDD15\uDD1D\uDD3A\uDD3F\uDD45\uDD47-\uDD49\uDD51\uDEA6\uDEA7\uDEC1\uDEDB\uDEFB\uDF15\uDF35\uDF4F\uDF6F\uDF89\uDFA9\uDFC3\uDFCC\uDFCD]|\uD836[\uDC00-\uDDFF\uDE37-\uDE3A\uDE6D-\uDE74\uDE76-\uDE83\uDE85-\uDE9A\uDEA0\uDEB0-\uDFFF]|\uD838[\uDC07\uDC19\uDC1A\uDC22\uDC25\uDC2B-\uDCFF\uDD2D-\uDD2F\uDD3E\uDD3F\uDD4A-\uDD4D\uDD4F-\uDEBF\uDEFA-\uDFFF]|\uD83A[\uDCC5-\uDCCF\uDCD7-\uDCFF\uDD4C-\uDD4F\uDD5A-\uDFFF]|\uD83B[\uDC00-\uDDFF\uDE04\uDE20\uDE23\uDE25\uDE26\uDE28\uDE33\uDE38\uDE3A\uDE3C-\uDE41\uDE43-\uDE46\uDE48\uDE4A\uDE4C\uDE50\uDE53\uDE55\uDE56\uDE58\uDE5A\uDE5C\uDE5E\uDE60\uDE63\uDE65\uDE66\uDE6B\uDE73\uDE78\uDE7D\uDE7F\uDE8A\uDE9C-\uDEA0\uDEA4\uDEAA\uDEBC-\uDFFF]|\uD83C[\uDC00-\uDD2F\uDD4A-\uDD4F\uDD6A-\uDD6F\uDD8A-\uDFFF]|\uD83E[\uDC00-\uDFEF\uDFFA-\uDFFF]|\uD869[\uDEDE-\uDEFF]|\uD86D[\uDF35-\uDF3F]|\uD86E[\uDC1E\uDC1F]|\uD873[\uDEA2-\uDEAF]|\uD87A[\uDFE1-\uDFFF]|\uD87E[\uDE1E-\uDFFF]|\uD884[\uDF4B-\uDFFF]|\uDB40[\uDC00-\uDCFF\uDDF0-\uDFFF]/g,Nn=Object.hasOwnProperty;class pu{constructor(){this.occurrences,this.reset();}slug(e,u){const n=this;let r=Bn$1(e,u===!0);const a=r;for(;Nn.call(n.occurrences,r);)n.occurrences[a]++,r=a+"-"+n.occurrences[a];return n.occurrences[r]=0,r}reset(){this.occurrences=Object.create(null);}}function Bn$1(t,e){return typeof t!="string"?"":(e||(t=t.toLowerCase()),t.replace(In,"").replace(/ /g,"-"))}let st$2=new pu,ot$2=[];function On({prefix:t="",globalSlugs:e=!1}={}){return {headerIds:!1,hooks:{preprocess(u){return e||Ln(),u}},renderer:{heading(u,n,r){r=r.toLowerCase().trim().replace(/<[!\/a-z].*?>/gi,"");const a=`${t}${st$2.slug(r)}`,i={level:n,text:u,id:a};return ot$2.push(i),`<h${n} id="${a}">${u}</h${n}>
`}}}}function Ln(){ot$2=[],st$2=new pu;}(function(t){var e=/\\(?:[^a-z()[\]]|[a-z*]+)/i,u={"equation-command":{pattern:e,alias:"regex"}};t.languages.latex={comment:/%.*/,cdata:{pattern:/(\\begin\{((?:lstlisting|verbatim)\*?)\})[\s\S]*?(?=\\end\{\2\})/,lookbehind:!0},equation:[{pattern:/\$\$(?:\\[\s\S]|[^\\$])+\$\$|\$(?:\\[\s\S]|[^\\$])+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/,inside:u,alias:"string"},{pattern:/(\\begin\{((?:align|eqnarray|equation|gather|math|multline)\*?)\})[\s\S]*?(?=\\end\{\2\})/,lookbehind:!0,inside:u,alias:"string"}],keyword:{pattern:/(\\(?:begin|cite|documentclass|end|label|ref|usepackage)(?:\[[^\]]+\])?\{)[^}]+(?=\})/,lookbehind:!0},url:{pattern:/(\\url\{)[^}]+(?=\})/,lookbehind:!0},headline:{pattern:/(\\(?:chapter|frametitle|paragraph|part|section|subparagraph|subsection|subsubparagraph|subsubsection|subsubsubparagraph)\*?(?:\[[^\]]+\])?\{)[^}]+(?=\})/,lookbehind:!0,alias:"class-name"},function:{pattern:e,alias:"selector"},punctuation:/[[\]{}&]/},t.languages.tex=t.languages.latex,t.languages.context=t.languages.latex;})(Prism);(function(t){var e="\\b(?:BASH|BASHOPTS|BASH_ALIASES|BASH_ARGC|BASH_ARGV|BASH_CMDS|BASH_COMPLETION_COMPAT_DIR|BASH_LINENO|BASH_REMATCH|BASH_SOURCE|BASH_VERSINFO|BASH_VERSION|COLORTERM|COLUMNS|COMP_WORDBREAKS|DBUS_SESSION_BUS_ADDRESS|DEFAULTS_PATH|DESKTOP_SESSION|DIRSTACK|DISPLAY|EUID|GDMSESSION|GDM_LANG|GNOME_KEYRING_CONTROL|GNOME_KEYRING_PID|GPG_AGENT_INFO|GROUPS|HISTCONTROL|HISTFILE|HISTFILESIZE|HISTSIZE|HOME|HOSTNAME|HOSTTYPE|IFS|INSTANCE|JOB|LANG|LANGUAGE|LC_ADDRESS|LC_ALL|LC_IDENTIFICATION|LC_MEASUREMENT|LC_MONETARY|LC_NAME|LC_NUMERIC|LC_PAPER|LC_TELEPHONE|LC_TIME|LESSCLOSE|LESSOPEN|LINES|LOGNAME|LS_COLORS|MACHTYPE|MAILCHECK|MANDATORY_PATH|NO_AT_BRIDGE|OLDPWD|OPTERR|OPTIND|ORBIT_SOCKETDIR|OSTYPE|PAPERSIZE|PATH|PIPESTATUS|PPID|PS1|PS2|PS3|PS4|PWD|RANDOM|REPLY|SECONDS|SELINUX_INIT|SESSION|SESSIONTYPE|SESSION_MANAGER|SHELL|SHELLOPTS|SHLVL|SSH_AUTH_SOCK|TERM|UID|UPSTART_EVENTS|UPSTART_INSTANCE|UPSTART_JOB|UPSTART_SESSION|USER|WINDOWID|XAUTHORITY|XDG_CONFIG_DIRS|XDG_CURRENT_DESKTOP|XDG_DATA_DIRS|XDG_GREETER_DATA_DIR|XDG_MENU_PREFIX|XDG_RUNTIME_DIR|XDG_SEAT|XDG_SEAT_PATH|XDG_SESSION_DESKTOP|XDG_SESSION_ID|XDG_SESSION_PATH|XDG_SESSION_TYPE|XDG_VTNR|XMODIFIERS)\\b",u={pattern:/(^(["']?)\w+\2)[ \t]+\S.*/,lookbehind:!0,alias:"punctuation",inside:null},n={bash:u,environment:{pattern:RegExp("\\$"+e),alias:"constant"},variable:[{pattern:/\$?\(\([\s\S]+?\)\)/,greedy:!0,inside:{variable:[{pattern:/(^\$\(\([\s\S]+)\)\)/,lookbehind:!0},/^\$\(\(/],number:/\b0x[\dA-Fa-f]+\b|(?:\b\d+(?:\.\d*)?|\B\.\d+)(?:[Ee]-?\d+)?/,operator:/--|\+\+|\*\*=?|<<=?|>>=?|&&|\|\||[=!+\-*/%<>^&|]=?|[?~:]/,punctuation:/\(\(?|\)\)?|,|;/}},{pattern:/\$\((?:\([^)]+\)|[^()])+\)|`[^`]+`/,greedy:!0,inside:{variable:/^\$\(|^`|\)$|`$/}},{pattern:/\$\{[^}]+\}/,greedy:!0,inside:{operator:/:[-=?+]?|[!\/]|##?|%%?|\^\^?|,,?/,punctuation:/[\[\]]/,environment:{pattern:RegExp("(\\{)"+e),lookbehind:!0,alias:"constant"}}},/\$(?:\w+|[#?*!@$])/],entity:/\\(?:[abceEfnrtv\\"]|O?[0-7]{1,3}|U[0-9a-fA-F]{8}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{1,2})/};t.languages.bash={shebang:{pattern:/^#!\s*\/.*/,alias:"important"},comment:{pattern:/(^|[^"{\\$])#.*/,lookbehind:!0},"function-name":[{pattern:/(\bfunction\s+)[\w-]+(?=(?:\s*\(?:\s*\))?\s*\{)/,lookbehind:!0,alias:"function"},{pattern:/\b[\w-]+(?=\s*\(\s*\)\s*\{)/,alias:"function"}],"for-or-select":{pattern:/(\b(?:for|select)\s+)\w+(?=\s+in\s)/,alias:"variable",lookbehind:!0},"assign-left":{pattern:/(^|[\s;|&]|[<>]\()\w+(?:\.\w+)*(?=\+?=)/,inside:{environment:{pattern:RegExp("(^|[\\s;|&]|[<>]\\()"+e),lookbehind:!0,alias:"constant"}},alias:"variable",lookbehind:!0},parameter:{pattern:/(^|\s)-{1,2}(?:\w+:[+-]?)?\w+(?:\.\w+)*(?=[=\s]|$)/,alias:"variable",lookbehind:!0},string:[{pattern:/((?:^|[^<])<<-?\s*)(\w+)\s[\s\S]*?(?:\r?\n|\r)\2/,lookbehind:!0,greedy:!0,inside:n},{pattern:/((?:^|[^<])<<-?\s*)(["'])(\w+)\2\s[\s\S]*?(?:\r?\n|\r)\3/,lookbehind:!0,greedy:!0,inside:{bash:u}},{pattern:/(^|[^\\](?:\\\\)*)"(?:\\[\s\S]|\$\([^)]+\)|\$(?!\()|`[^`]+`|[^"\\`$])*"/,lookbehind:!0,greedy:!0,inside:n},{pattern:/(^|[^$\\])'[^']*'/,lookbehind:!0,greedy:!0},{pattern:/\$'(?:[^'\\]|\\[\s\S])*'/,greedy:!0,inside:{entity:n.entity}}],environment:{pattern:RegExp("\\$?"+e),alias:"constant"},variable:n.variable,function:{pattern:/(^|[\s;|&]|[<>]\()(?:add|apropos|apt|apt-cache|apt-get|aptitude|aspell|automysqlbackup|awk|basename|bash|bc|bconsole|bg|bzip2|cal|cargo|cat|cfdisk|chgrp|chkconfig|chmod|chown|chroot|cksum|clear|cmp|column|comm|composer|cp|cron|crontab|csplit|curl|cut|date|dc|dd|ddrescue|debootstrap|df|diff|diff3|dig|dir|dircolors|dirname|dirs|dmesg|docker|docker-compose|du|egrep|eject|env|ethtool|expand|expect|expr|fdformat|fdisk|fg|fgrep|file|find|fmt|fold|format|free|fsck|ftp|fuser|gawk|git|gparted|grep|groupadd|groupdel|groupmod|groups|grub-mkconfig|gzip|halt|head|hg|history|host|hostname|htop|iconv|id|ifconfig|ifdown|ifup|import|install|ip|java|jobs|join|kill|killall|less|link|ln|locate|logname|logrotate|look|lpc|lpr|lprint|lprintd|lprintq|lprm|ls|lsof|lynx|make|man|mc|mdadm|mkconfig|mkdir|mke2fs|mkfifo|mkfs|mkisofs|mknod|mkswap|mmv|more|most|mount|mtools|mtr|mutt|mv|nano|nc|netstat|nice|nl|node|nohup|notify-send|npm|nslookup|op|open|parted|passwd|paste|pathchk|ping|pkill|pnpm|podman|podman-compose|popd|pr|printcap|printenv|ps|pushd|pv|quota|quotacheck|quotactl|ram|rar|rcp|reboot|remsync|rename|renice|rev|rm|rmdir|rpm|rsync|scp|screen|sdiff|sed|sendmail|seq|service|sftp|sh|shellcheck|shuf|shutdown|sleep|slocate|sort|split|ssh|stat|strace|su|sudo|sum|suspend|swapon|sync|sysctl|tac|tail|tar|tee|time|timeout|top|touch|tr|traceroute|tsort|tty|umount|uname|unexpand|uniq|units|unrar|unshar|unzip|update-grub|uptime|useradd|userdel|usermod|users|uudecode|uuencode|v|vcpkg|vdir|vi|vim|virsh|vmstat|wait|watch|wc|wget|whereis|which|who|whoami|write|xargs|xdg-open|yarn|yes|zenity|zip|zsh|zypper)(?=$|[)\s;|&])/,lookbehind:!0},keyword:{pattern:/(^|[\s;|&]|[<>]\()(?:case|do|done|elif|else|esac|fi|for|function|if|in|select|then|until|while)(?=$|[)\s;|&])/,lookbehind:!0},builtin:{pattern:/(^|[\s;|&]|[<>]\()(?:\.|:|alias|bind|break|builtin|caller|cd|command|continue|declare|echo|enable|eval|exec|exit|export|getopts|hash|help|let|local|logout|mapfile|printf|pwd|read|readarray|readonly|return|set|shift|shopt|source|test|times|trap|type|typeset|ulimit|umask|unalias|unset)(?=$|[)\s;|&])/,lookbehind:!0,alias:"class-name"},boolean:{pattern:/(^|[\s;|&]|[<>]\()(?:false|true)(?=$|[)\s;|&])/,lookbehind:!0},"file-descriptor":{pattern:/\B&\d\b/,alias:"important"},operator:{pattern:/\d?<>|>\||\+=|=[=~]?|!=?|<<[<-]?|[&\d]?>>|\d[<>]&?|[<>][&=]?|&[>&]?|\|[&|]?/,inside:{"file-descriptor":{pattern:/^\d/,alias:"important"}}},punctuation:/\$?\(\(?|\)\)?|\.\.|[{}[\];\\]/,number:{pattern:/(^|\s)(?:[1-9]\d*|0)(?:[.,]\d+)?\b/,lookbehind:!0}},u.inside=t.languages.bash;for(var r=["comment","function-name","for-or-select","assign-left","parameter","string","environment","function","keyword","builtin","boolean","file-descriptor","operator","punctuation","number"],a=n.variable[1].inside,i=0;i<r.length;i++)a[r[i]]=t.languages.bash[r[i]];t.languages.sh=t.languages.bash,t.languages.shell=t.languages.bash;})(Prism);Prism.languages.c=Prism.languages.extend("clike",{comment:{pattern:/\/\/(?:[^\r\n\\]|\\(?:\r\n?|\n|(?![\r\n])))*|\/\*[\s\S]*?(?:\*\/|$)/,greedy:!0},string:{pattern:/"(?:\\(?:\r\n|[\s\S])|[^"\\\r\n])*"/,greedy:!0},"class-name":{pattern:/(\b(?:enum|struct)\s+(?:__attribute__\s*\(\([\s\S]*?\)\)\s*)?)\w+|\b[a-z]\w*_t\b/,lookbehind:!0},keyword:/\b(?:_Alignas|_Alignof|_Atomic|_Bool|_Complex|_Generic|_Imaginary|_Noreturn|_Static_assert|_Thread_local|__attribute__|asm|auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|inline|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|typeof|union|unsigned|void|volatile|while)\b/,function:/\b[a-z_]\w*(?=\s*\()/i,number:/(?:\b0x(?:[\da-f]+(?:\.[\da-f]*)?|\.[\da-f]+)(?:p[+-]?\d+)?|(?:\b\d+(?:\.\d*)?|\B\.\d+)(?:e[+-]?\d+)?)[ful]{0,4}/i,operator:/>>=?|<<=?|->|([-+&|:])\1|[?:~]|[-+*/%&|^!=<>]=?/});Prism.languages.insertBefore("c","string",{char:{pattern:/'(?:\\(?:\r\n|[\s\S])|[^'\\\r\n]){0,32}'/,greedy:!0}});Prism.languages.insertBefore("c","string",{macro:{pattern:/(^[\t ]*)#\s*[a-z](?:[^\r\n\\/]|\/(?!\*)|\/\*(?:[^*]|\*(?!\/))*\*\/|\\(?:\r\n|[\s\S]))*/im,lookbehind:!0,greedy:!0,alias:"property",inside:{string:[{pattern:/^(#\s*include\s*)<[^>]+>/,lookbehind:!0},Prism.languages.c.string],char:Prism.languages.c.char,comment:Prism.languages.c.comment,"macro-name":[{pattern:/(^#\s*define\s+)\w+\b(?!\()/i,lookbehind:!0},{pattern:/(^#\s*define\s+)\w+\b(?=\()/i,lookbehind:!0,alias:"function"}],directive:{pattern:/^(#\s*)[a-z]+/,lookbehind:!0,alias:"keyword"},"directive-hash":/^#/,punctuation:/##|\\(?=[\r\n])/,expression:{pattern:/\S[\s\S]*/,inside:Prism.languages.c}}}});Prism.languages.insertBefore("c","function",{constant:/\b(?:EOF|NULL|SEEK_CUR|SEEK_END|SEEK_SET|__DATE__|__FILE__|__LINE__|__TIMESTAMP__|__TIME__|__func__|stderr|stdin|stdout)\b/});delete Prism.languages.c.boolean;(function(t){var e=/\b(?:alignas|alignof|asm|auto|bool|break|case|catch|char|char16_t|char32_t|char8_t|class|co_await|co_return|co_yield|compl|concept|const|const_cast|consteval|constexpr|constinit|continue|decltype|default|delete|do|double|dynamic_cast|else|enum|explicit|export|extern|final|float|for|friend|goto|if|import|inline|int|int16_t|int32_t|int64_t|int8_t|long|module|mutable|namespace|new|noexcept|nullptr|operator|override|private|protected|public|register|reinterpret_cast|requires|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|thread_local|throw|try|typedef|typeid|typename|uint16_t|uint32_t|uint64_t|uint8_t|union|unsigned|using|virtual|void|volatile|wchar_t|while)\b/,u=/\b(?!<keyword>)\w+(?:\s*\.\s*\w+)*\b/.source.replace(/<keyword>/g,function(){return e.source});t.languages.cpp=t.languages.extend("c",{"class-name":[{pattern:RegExp(/(\b(?:class|concept|enum|struct|typename)\s+)(?!<keyword>)\w+/.source.replace(/<keyword>/g,function(){return e.source})),lookbehind:!0},/\b[A-Z]\w*(?=\s*::\s*\w+\s*\()/,/\b[A-Z_]\w*(?=\s*::\s*~\w+\s*\()/i,/\b\w+(?=\s*<(?:[^<>]|<(?:[^<>]|<[^<>]*>)*>)*>\s*::\s*\w+\s*\()/],keyword:e,number:{pattern:/(?:\b0b[01']+|\b0x(?:[\da-f']+(?:\.[\da-f']*)?|\.[\da-f']+)(?:p[+-]?[\d']+)?|(?:\b[\d']+(?:\.[\d']*)?|\B\.[\d']+)(?:e[+-]?[\d']+)?)[ful]{0,4}/i,greedy:!0},operator:/>>=?|<<=?|->|--|\+\+|&&|\|\||[?:~]|<=>|[-+*/%&|^!=<>]=?|\b(?:and|and_eq|bitand|bitor|not|not_eq|or|or_eq|xor|xor_eq)\b/,boolean:/\b(?:false|true)\b/}),t.languages.insertBefore("cpp","string",{module:{pattern:RegExp(/(\b(?:import|module)\s+)/.source+"(?:"+/"(?:\\(?:\r\n|[\s\S])|[^"\\\r\n])*"|<[^<>\r\n]*>/.source+"|"+/<mod-name>(?:\s*:\s*<mod-name>)?|:\s*<mod-name>/.source.replace(/<mod-name>/g,function(){return u})+")"),lookbehind:!0,greedy:!0,inside:{string:/^[<"][\s\S]+/,operator:/:/,punctuation:/\./}},"raw-string":{pattern:/R"([^()\\ ]{0,16})\([\s\S]*?\)\1"/,alias:"string",greedy:!0}}),t.languages.insertBefore("cpp","keyword",{"generic-function":{pattern:/\b(?!operator\b)[a-z_]\w*\s*<(?:[^<>]|<[^<>]*>)*>(?=\s*\()/i,inside:{function:/^\w+/,generic:{pattern:/<[\s\S]+/,alias:"class-name",inside:t.languages.cpp}}}}),t.languages.insertBefore("cpp","operator",{"double-colon":{pattern:/::/,alias:"punctuation"}}),t.languages.insertBefore("cpp","class-name",{"base-clause":{pattern:/(\b(?:class|struct)\s+\w+\s*:\s*)[^;{}"'\s]+(?:\s+[^;{}"'\s]+)*(?=\s*[;{])/,lookbehind:!0,greedy:!0,inside:t.languages.extend("cpp",{})}}),t.languages.insertBefore("inside","double-colon",{"class-name":/\b[a-z_]\w*\b(?!\s*::)/i},t.languages.cpp["base-clause"]);})(Prism);Prism.languages.json={property:{pattern:/(^|[^\\])"(?:\\.|[^\\"\r\n])*"(?=\s*:)/,lookbehind:!0,greedy:!0},string:{pattern:/(^|[^\\])"(?:\\.|[^\\"\r\n])*"(?!\s*:)/,lookbehind:!0,greedy:!0},comment:{pattern:/\/\/.*|\/\*[\s\S]*?(?:\*\/|$)/,greedy:!0},number:/-?\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b/i,punctuation:/[{}[\],]/,operator:/:/,boolean:/\b(?:false|true)\b/,null:{pattern:/\bnull\b/,alias:"keyword"}};Prism.languages.webmanifest=Prism.languages.json;Prism.languages.sql={comment:{pattern:/(^|[^\\])(?:\/\*[\s\S]*?\*\/|(?:--|\/\/|#).*)/,lookbehind:!0},variable:[{pattern:/@(["'`])(?:\\[\s\S]|(?!\1)[^\\])+\1/,greedy:!0},/@[\w.$]+/],string:{pattern:/(^|[^@\\])("|')(?:\\[\s\S]|(?!\2)[^\\]|\2\2)*\2/,greedy:!0,lookbehind:!0},identifier:{pattern:/(^|[^@\\])`(?:\\[\s\S]|[^`\\]|``)*`/,greedy:!0,lookbehind:!0,inside:{punctuation:/^`|`$/}},function:/\b(?:AVG|COUNT|FIRST|FORMAT|LAST|LCASE|LEN|MAX|MID|MIN|MOD|NOW|ROUND|SUM|UCASE)(?=\s*\()/i,keyword:/\b(?:ACTION|ADD|AFTER|ALGORITHM|ALL|ALTER|ANALYZE|ANY|APPLY|AS|ASC|AUTHORIZATION|AUTO_INCREMENT|BACKUP|BDB|BEGIN|BERKELEYDB|BIGINT|BINARY|BIT|BLOB|BOOL|BOOLEAN|BREAK|BROWSE|BTREE|BULK|BY|CALL|CASCADED?|CASE|CHAIN|CHAR(?:ACTER|SET)?|CHECK(?:POINT)?|CLOSE|CLUSTERED|COALESCE|COLLATE|COLUMNS?|COMMENT|COMMIT(?:TED)?|COMPUTE|CONNECT|CONSISTENT|CONSTRAINT|CONTAINS(?:TABLE)?|CONTINUE|CONVERT|CREATE|CROSS|CURRENT(?:_DATE|_TIME|_TIMESTAMP|_USER)?|CURSOR|CYCLE|DATA(?:BASES?)?|DATE(?:TIME)?|DAY|DBCC|DEALLOCATE|DEC|DECIMAL|DECLARE|DEFAULT|DEFINER|DELAYED|DELETE|DELIMITERS?|DENY|DESC|DESCRIBE|DETERMINISTIC|DISABLE|DISCARD|DISK|DISTINCT|DISTINCTROW|DISTRIBUTED|DO|DOUBLE|DROP|DUMMY|DUMP(?:FILE)?|DUPLICATE|ELSE(?:IF)?|ENABLE|ENCLOSED|END|ENGINE|ENUM|ERRLVL|ERRORS|ESCAPED?|EXCEPT|EXEC(?:UTE)?|EXISTS|EXIT|EXPLAIN|EXTENDED|FETCH|FIELDS|FILE|FILLFACTOR|FIRST|FIXED|FLOAT|FOLLOWING|FOR(?: EACH ROW)?|FORCE|FOREIGN|FREETEXT(?:TABLE)?|FROM|FULL|FUNCTION|GEOMETRY(?:COLLECTION)?|GLOBAL|GOTO|GRANT|GROUP|HANDLER|HASH|HAVING|HOLDLOCK|HOUR|IDENTITY(?:COL|_INSERT)?|IF|IGNORE|IMPORT|INDEX|INFILE|INNER|INNODB|INOUT|INSERT|INT|INTEGER|INTERSECT|INTERVAL|INTO|INVOKER|ISOLATION|ITERATE|JOIN|KEYS?|KILL|LANGUAGE|LAST|LEAVE|LEFT|LEVEL|LIMIT|LINENO|LINES|LINESTRING|LOAD|LOCAL|LOCK|LONG(?:BLOB|TEXT)|LOOP|MATCH(?:ED)?|MEDIUM(?:BLOB|INT|TEXT)|MERGE|MIDDLEINT|MINUTE|MODE|MODIFIES|MODIFY|MONTH|MULTI(?:LINESTRING|POINT|POLYGON)|NATIONAL|NATURAL|NCHAR|NEXT|NO|NONCLUSTERED|NULLIF|NUMERIC|OFF?|OFFSETS?|ON|OPEN(?:DATASOURCE|QUERY|ROWSET)?|OPTIMIZE|OPTION(?:ALLY)?|ORDER|OUT(?:ER|FILE)?|OVER|PARTIAL|PARTITION|PERCENT|PIVOT|PLAN|POINT|POLYGON|PRECEDING|PRECISION|PREPARE|PREV|PRIMARY|PRINT|PRIVILEGES|PROC(?:EDURE)?|PUBLIC|PURGE|QUICK|RAISERROR|READS?|REAL|RECONFIGURE|REFERENCES|RELEASE|RENAME|REPEAT(?:ABLE)?|REPLACE|REPLICATION|REQUIRE|RESIGNAL|RESTORE|RESTRICT|RETURN(?:ING|S)?|REVOKE|RIGHT|ROLLBACK|ROUTINE|ROW(?:COUNT|GUIDCOL|S)?|RTREE|RULE|SAVE(?:POINT)?|SCHEMA|SECOND|SELECT|SERIAL(?:IZABLE)?|SESSION(?:_USER)?|SET(?:USER)?|SHARE|SHOW|SHUTDOWN|SIMPLE|SMALLINT|SNAPSHOT|SOME|SONAME|SQL|START(?:ING)?|STATISTICS|STATUS|STRIPED|SYSTEM_USER|TABLES?|TABLESPACE|TEMP(?:ORARY|TABLE)?|TERMINATED|TEXT(?:SIZE)?|THEN|TIME(?:STAMP)?|TINY(?:BLOB|INT|TEXT)|TOP?|TRAN(?:SACTIONS?)?|TRIGGER|TRUNCATE|TSEQUAL|TYPES?|UNBOUNDED|UNCOMMITTED|UNDEFINED|UNION|UNIQUE|UNLOCK|UNPIVOT|UNSIGNED|UPDATE(?:TEXT)?|USAGE|USE|USER|USING|VALUES?|VAR(?:BINARY|CHAR|CHARACTER|YING)|VIEW|WAITFOR|WARNINGS|WHEN|WHERE|WHILE|WITH(?: ROLLUP|IN)?|WORK|WRITE(?:TEXT)?|YEAR)\b/i,boolean:/\b(?:FALSE|NULL|TRUE)\b/i,number:/\b0x[\da-f]+\b|\b\d+(?:\.\d*)?|\B\.\d+\b/i,operator:/[-+*\/=%^~]|&&?|\|\|?|!=?|<(?:=>?|<|>)?|>[>=]?|\b(?:AND|BETWEEN|DIV|ILIKE|IN|IS|LIKE|NOT|OR|REGEXP|RLIKE|SOUNDS LIKE|XOR)\b/i,punctuation:/[;[\]()`,.]/};(function(t){var e=/\b(?:abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|exports|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|module|native|new|non-sealed|null|open|opens|package|permits|private|protected|provides|public|record(?!\s*[(){}[\]<>=%~.:,;?+\-*/&|^])|requires|return|sealed|short|static|strictfp|super|switch|synchronized|this|throw|throws|to|transient|transitive|try|uses|var|void|volatile|while|with|yield)\b/,u=/(?:[a-z]\w*\s*\.\s*)*(?:[A-Z]\w*\s*\.\s*)*/.source,n={pattern:RegExp(/(^|[^\w.])/.source+u+/[A-Z](?:[\d_A-Z]*[a-z]\w*)?\b/.source),lookbehind:!0,inside:{namespace:{pattern:/^[a-z]\w*(?:\s*\.\s*[a-z]\w*)*(?:\s*\.)?/,inside:{punctuation:/\./}},punctuation:/\./}};t.languages.java=t.languages.extend("clike",{string:{pattern:/(^|[^\\])"(?:\\.|[^"\\\r\n])*"/,lookbehind:!0,greedy:!0},"class-name":[n,{pattern:RegExp(/(^|[^\w.])/.source+u+/[A-Z]\w*(?=\s+\w+\s*[;,=()]|\s*(?:\[[\s,]*\]\s*)?::\s*new\b)/.source),lookbehind:!0,inside:n.inside},{pattern:RegExp(/(\b(?:class|enum|extends|implements|instanceof|interface|new|record|throws)\s+)/.source+u+/[A-Z]\w*\b/.source),lookbehind:!0,inside:n.inside}],keyword:e,function:[t.languages.clike.function,{pattern:/(::\s*)[a-z_]\w*/,lookbehind:!0}],number:/\b0b[01][01_]*L?\b|\b0x(?:\.[\da-f_p+-]+|[\da-f_]+(?:\.[\da-f_p+-]+)?)\b|(?:\b\d[\d_]*(?:\.[\d_]*)?|\B\.\d[\d_]*)(?:e[+-]?\d[\d_]*)?[dfl]?/i,operator:{pattern:/(^|[^.])(?:<<=?|>>>?=?|->|--|\+\+|&&|\|\||::|[?:~]|[-+*/%&|^!=<>]=?)/m,lookbehind:!0},constant:/\b[A-Z][A-Z_\d]+\b/}),t.languages.insertBefore("java","string",{"triple-quoted-string":{pattern:/"""[ \t]*[\r\n](?:(?:"|"")?(?:\\.|[^"\\]))*"""/,greedy:!0,alias:"string"},char:{pattern:/'(?:\\.|[^'\\\r\n]){1,6}'/,greedy:!0}}),t.languages.insertBefore("java","class-name",{annotation:{pattern:/(^|[^.])@\w+(?:\s*\.\s*\w+)*/,lookbehind:!0,alias:"punctuation"},generics:{pattern:/<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&)|<(?:[\w\s,.?]|&(?!&))*>)*>)*>)*>/,inside:{"class-name":n,keyword:e,punctuation:/[<>(),.:]/,operator:/[?&|]/}},import:[{pattern:RegExp(/(\bimport\s+)/.source+u+/(?:[A-Z]\w*|\*)(?=\s*;)/.source),lookbehind:!0,inside:{namespace:n.inside.namespace,punctuation:/\./,operator:/\*/,"class-name":/\w+/}},{pattern:RegExp(/(\bimport\s+static\s+)/.source+u+/(?:\w+|\*)(?=\s*;)/.source),lookbehind:!0,alias:"static",inside:{namespace:n.inside.namespace,static:/\b\w+$/,punctuation:/\./,operator:/\*/,"class-name":/\w+/}}],namespace:{pattern:RegExp(/(\b(?:exports|import(?:\s+static)?|module|open|opens|package|provides|requires|to|transitive|uses|with)\s+)(?!<keyword>)[a-z]\w*(?:\.[a-z]\w*)*\.?/.source.replace(/<keyword>/g,function(){return e.source})),lookbehind:!0,inside:{punctuation:/\./}}});})(Prism);Prism.languages.go=Prism.languages.extend("clike",{string:{pattern:/(^|[^\\])"(?:\\.|[^"\\\r\n])*"|`[^`]*`/,lookbehind:!0,greedy:!0},keyword:/\b(?:break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go(?:to)?|if|import|interface|map|package|range|return|select|struct|switch|type|var)\b/,boolean:/\b(?:_|false|iota|nil|true)\b/,number:[/\b0(?:b[01_]+|o[0-7_]+)i?\b/i,/\b0x(?:[a-f\d_]+(?:\.[a-f\d_]*)?|\.[a-f\d_]+)(?:p[+-]?\d+(?:_\d+)*)?i?(?!\w)/i,/(?:\b\d[\d_]*(?:\.[\d_]*)?|\B\.\d[\d_]*)(?:e[+-]?[\d_]+)?i?(?!\w)/i],operator:/[*\/%^!=]=?|\+[=+]?|-[=-]?|\|[=|]?|&(?:=|&|\^=?)?|>(?:>=?|=)?|<(?:<=?|=|-)?|:=|\.\.\./,builtin:/\b(?:append|bool|byte|cap|close|complex|complex(?:64|128)|copy|delete|error|float(?:32|64)|u?int(?:8|16|32|64)?|imag|len|make|new|panic|print(?:ln)?|real|recover|rune|string|uintptr)\b/});Prism.languages.insertBefore("go","string",{char:{pattern:/'(?:\\.|[^'\\\r\n]){0,10}'/,greedy:!0}});delete Prism.languages.go["class-name"];(function(t){for(var e=/\/\*(?:[^*/]|\*(?!\/)|\/(?!\*)|<self>)*\*\//.source,u=0;u<2;u++)e=e.replace(/<self>/g,function(){return e});e=e.replace(/<self>/g,function(){return /[^\s\S]/.source}),t.languages.rust={comment:[{pattern:RegExp(/(^|[^\\])/.source+e),lookbehind:!0,greedy:!0},{pattern:/(^|[^\\:])\/\/.*/,lookbehind:!0,greedy:!0}],string:{pattern:/b?"(?:\\[\s\S]|[^\\"])*"|b?r(#*)"(?:[^"]|"(?!\1))*"\1/,greedy:!0},char:{pattern:/b?'(?:\\(?:x[0-7][\da-fA-F]|u\{(?:[\da-fA-F]_*){1,6}\}|.)|[^\\\r\n\t'])'/,greedy:!0},attribute:{pattern:/#!?\[(?:[^\[\]"]|"(?:\\[\s\S]|[^\\"])*")*\]/,greedy:!0,alias:"attr-name",inside:{string:null}},"closure-params":{pattern:/([=(,:]\s*|\bmove\s*)\|[^|]*\||\|[^|]*\|(?=\s*(?:\{|->))/,lookbehind:!0,greedy:!0,inside:{"closure-punctuation":{pattern:/^\||\|$/,alias:"punctuation"},rest:null}},"lifetime-annotation":{pattern:/'\w+/,alias:"symbol"},"fragment-specifier":{pattern:/(\$\w+:)[a-z]+/,lookbehind:!0,alias:"punctuation"},variable:/\$\w+/,"function-definition":{pattern:/(\bfn\s+)\w+/,lookbehind:!0,alias:"function"},"type-definition":{pattern:/(\b(?:enum|struct|trait|type|union)\s+)\w+/,lookbehind:!0,alias:"class-name"},"module-declaration":[{pattern:/(\b(?:crate|mod)\s+)[a-z][a-z_\d]*/,lookbehind:!0,alias:"namespace"},{pattern:/(\b(?:crate|self|super)\s*)::\s*[a-z][a-z_\d]*\b(?:\s*::(?:\s*[a-z][a-z_\d]*\s*::)*)?/,lookbehind:!0,alias:"namespace",inside:{punctuation:/::/}}],keyword:[/\b(?:Self|abstract|as|async|await|become|box|break|const|continue|crate|do|dyn|else|enum|extern|final|fn|for|if|impl|in|let|loop|macro|match|mod|move|mut|override|priv|pub|ref|return|self|static|struct|super|trait|try|type|typeof|union|unsafe|unsized|use|virtual|where|while|yield)\b/,/\b(?:bool|char|f(?:32|64)|[ui](?:8|16|32|64|128|size)|str)\b/],function:/\b[a-z_]\w*(?=\s*(?:::\s*<|\())/,macro:{pattern:/\b\w+!/,alias:"property"},constant:/\b[A-Z_][A-Z_\d]+\b/,"class-name":/\b[A-Z]\w*\b/,namespace:{pattern:/(?:\b[a-z][a-z_\d]*\s*::\s*)*\b[a-z][a-z_\d]*\s*::(?!\s*<)/,inside:{punctuation:/::/}},number:/\b(?:0x[\dA-Fa-f](?:_?[\dA-Fa-f])*|0o[0-7](?:_?[0-7])*|0b[01](?:_?[01])*|(?:(?:\d(?:_?\d)*)?\.)?\d(?:_?\d)*(?:[Ee][+-]?\d+)?)(?:_?(?:f32|f64|[iu](?:8|16|32|64|size)?))?\b/,boolean:/\b(?:false|true)\b/,punctuation:/->|\.\.=|\.{1,3}|::|[{}[\];(),:]/,operator:/[-+*\/%!^]=?|=[=>]?|&[&=]?|\|[|=]?|<<?=?|>>?=?|[@?]/},t.languages.rust["closure-params"].inside.rest=t.languages.rust,t.languages.rust.attribute.inside.string=t.languages.rust.string;})(Prism);(function(t){var e=/\/\*[\s\S]*?\*\/|\/\/.*|#(?!\[).*/,u=[{pattern:/\b(?:false|true)\b/i,alias:"boolean"},{pattern:/(::\s*)\b[a-z_]\w*\b(?!\s*\()/i,greedy:!0,lookbehind:!0},{pattern:/(\b(?:case|const)\s+)\b[a-z_]\w*(?=\s*[;=])/i,greedy:!0,lookbehind:!0},/\b(?:null)\b/i,/\b[A-Z_][A-Z0-9_]*\b(?!\s*\()/],n=/\b0b[01]+(?:_[01]+)*\b|\b0o[0-7]+(?:_[0-7]+)*\b|\b0x[\da-f]+(?:_[\da-f]+)*\b|(?:\b\d+(?:_\d+)*\.?(?:\d+(?:_\d+)*)?|\B\.\d+)(?:e[+-]?\d+)?/i,r=/<?=>|\?\?=?|\.{3}|\??->|[!=]=?=?|::|\*\*=?|--|\+\+|&&|\|\||<<|>>|[?~]|[/^|%*&<>.+-]=?/,a=/[{}\[\](),:;]/;t.languages.php={delimiter:{pattern:/\?>$|^<\?(?:php(?=\s)|=)?/i,alias:"important"},comment:e,variable:/\$+(?:\w+\b|(?=\{))/,package:{pattern:/(namespace\s+|use\s+(?:function\s+)?)(?:\\?\b[a-z_]\w*)+\b(?!\\)/i,lookbehind:!0,inside:{punctuation:/\\/}},"class-name-definition":{pattern:/(\b(?:class|enum|interface|trait)\s+)\b[a-z_]\w*(?!\\)\b/i,lookbehind:!0,alias:"class-name"},"function-definition":{pattern:/(\bfunction\s+)[a-z_]\w*(?=\s*\()/i,lookbehind:!0,alias:"function"},keyword:[{pattern:/(\(\s*)\b(?:array|bool|boolean|float|int|integer|object|string)\b(?=\s*\))/i,alias:"type-casting",greedy:!0,lookbehind:!0},{pattern:/([(,?]\s*)\b(?:array(?!\s*\()|bool|callable|(?:false|null)(?=\s*\|)|float|int|iterable|mixed|object|self|static|string)\b(?=\s*\$)/i,alias:"type-hint",greedy:!0,lookbehind:!0},{pattern:/(\)\s*:\s*(?:\?\s*)?)\b(?:array(?!\s*\()|bool|callable|(?:false|null)(?=\s*\|)|float|int|iterable|mixed|never|object|self|static|string|void)\b/i,alias:"return-type",greedy:!0,lookbehind:!0},{pattern:/\b(?:array(?!\s*\()|bool|float|int|iterable|mixed|object|string|void)\b/i,alias:"type-declaration",greedy:!0},{pattern:/(\|\s*)(?:false|null)\b|\b(?:false|null)(?=\s*\|)/i,alias:"type-declaration",greedy:!0,lookbehind:!0},{pattern:/\b(?:parent|self|static)(?=\s*::)/i,alias:"static-context",greedy:!0},{pattern:/(\byield\s+)from\b/i,lookbehind:!0},/\bclass\b/i,{pattern:/((?:^|[^\s>:]|(?:^|[^-])>|(?:^|[^:]):)\s*)\b(?:abstract|and|array|as|break|callable|case|catch|clone|const|continue|declare|default|die|do|echo|else|elseif|empty|enddeclare|endfor|endforeach|endif|endswitch|endwhile|enum|eval|exit|extends|final|finally|fn|for|foreach|function|global|goto|if|implements|include|include_once|instanceof|insteadof|interface|isset|list|match|namespace|never|new|or|parent|print|private|protected|public|readonly|require|require_once|return|self|static|switch|throw|trait|try|unset|use|var|while|xor|yield|__halt_compiler)\b/i,lookbehind:!0}],"argument-name":{pattern:/([(,]\s*)\b[a-z_]\w*(?=\s*:(?!:))/i,lookbehind:!0},"class-name":[{pattern:/(\b(?:extends|implements|instanceof|new(?!\s+self|\s+static))\s+|\bcatch\s*\()\b[a-z_]\w*(?!\\)\b/i,greedy:!0,lookbehind:!0},{pattern:/(\|\s*)\b[a-z_]\w*(?!\\)\b/i,greedy:!0,lookbehind:!0},{pattern:/\b[a-z_]\w*(?!\\)\b(?=\s*\|)/i,greedy:!0},{pattern:/(\|\s*)(?:\\?\b[a-z_]\w*)+\b/i,alias:"class-name-fully-qualified",greedy:!0,lookbehind:!0,inside:{punctuation:/\\/}},{pattern:/(?:\\?\b[a-z_]\w*)+\b(?=\s*\|)/i,alias:"class-name-fully-qualified",greedy:!0,inside:{punctuation:/\\/}},{pattern:/(\b(?:extends|implements|instanceof|new(?!\s+self\b|\s+static\b))\s+|\bcatch\s*\()(?:\\?\b[a-z_]\w*)+\b(?!\\)/i,alias:"class-name-fully-qualified",greedy:!0,lookbehind:!0,inside:{punctuation:/\\/}},{pattern:/\b[a-z_]\w*(?=\s*\$)/i,alias:"type-declaration",greedy:!0},{pattern:/(?:\\?\b[a-z_]\w*)+(?=\s*\$)/i,alias:["class-name-fully-qualified","type-declaration"],greedy:!0,inside:{punctuation:/\\/}},{pattern:/\b[a-z_]\w*(?=\s*::)/i,alias:"static-context",greedy:!0},{pattern:/(?:\\?\b[a-z_]\w*)+(?=\s*::)/i,alias:["class-name-fully-qualified","static-context"],greedy:!0,inside:{punctuation:/\\/}},{pattern:/([(,?]\s*)[a-z_]\w*(?=\s*\$)/i,alias:"type-hint",greedy:!0,lookbehind:!0},{pattern:/([(,?]\s*)(?:\\?\b[a-z_]\w*)+(?=\s*\$)/i,alias:["class-name-fully-qualified","type-hint"],greedy:!0,lookbehind:!0,inside:{punctuation:/\\/}},{pattern:/(\)\s*:\s*(?:\?\s*)?)\b[a-z_]\w*(?!\\)\b/i,alias:"return-type",greedy:!0,lookbehind:!0},{pattern:/(\)\s*:\s*(?:\?\s*)?)(?:\\?\b[a-z_]\w*)+\b(?!\\)/i,alias:["class-name-fully-qualified","return-type"],greedy:!0,lookbehind:!0,inside:{punctuation:/\\/}}],constant:u,function:{pattern:/(^|[^\\\w])\\?[a-z_](?:[\w\\]*\w)?(?=\s*\()/i,lookbehind:!0,inside:{punctuation:/\\/}},property:{pattern:/(->\s*)\w+/,lookbehind:!0},number:n,operator:r,punctuation:a};var i={pattern:/\{\$(?:\{(?:\{[^{}]+\}|[^{}]+)\}|[^{}])+\}|(^|[^\\{])\$+(?:\w+(?:\[[^\r\n\[\]]+\]|->\w+)?)/,lookbehind:!0,inside:t.languages.php},l=[{pattern:/<<<'([^']+)'[\r\n](?:.*[\r\n])*?\1;/,alias:"nowdoc-string",greedy:!0,inside:{delimiter:{pattern:/^<<<'[^']+'|[a-z_]\w*;$/i,alias:"symbol",inside:{punctuation:/^<<<'?|[';]$/}}}},{pattern:/<<<(?:"([^"]+)"[\r\n](?:.*[\r\n])*?\1;|([a-z_]\w*)[\r\n](?:.*[\r\n])*?\2;)/i,alias:"heredoc-string",greedy:!0,inside:{delimiter:{pattern:/^<<<(?:"[^"]+"|[a-z_]\w*)|[a-z_]\w*;$/i,alias:"symbol",inside:{punctuation:/^<<<"?|[";]$/}},interpolation:i}},{pattern:/`(?:\\[\s\S]|[^\\`])*`/,alias:"backtick-quoted-string",greedy:!0},{pattern:/'(?:\\[\s\S]|[^\\'])*'/,alias:"single-quoted-string",greedy:!0},{pattern:/"(?:\\[\s\S]|[^\\"])*"/,alias:"double-quoted-string",greedy:!0,inside:{interpolation:i}}];t.languages.insertBefore("php","variable",{string:l,attribute:{pattern:/#\[(?:[^"'\/#]|\/(?![*/])|\/\/.*$|#(?!\[).*$|\/\*(?:[^*]|\*(?!\/))*\*\/|"(?:\\[\s\S]|[^\\"])*"|'(?:\\[\s\S]|[^\\'])*')+\](?=\s*[a-z$#])/im,greedy:!0,inside:{"attribute-content":{pattern:/^(#\[)[\s\S]+(?=\]$)/,lookbehind:!0,inside:{comment:e,string:l,"attribute-class-name":[{pattern:/([^:]|^)\b[a-z_]\w*(?!\\)\b/i,alias:"class-name",greedy:!0,lookbehind:!0},{pattern:/([^:]|^)(?:\\?\b[a-z_]\w*)+/i,alias:["class-name","class-name-fully-qualified"],greedy:!0,lookbehind:!0,inside:{punctuation:/\\/}}],constant:u,number:n,operator:r,punctuation:a}},delimiter:{pattern:/^#\[|\]$/,alias:"punctuation"}}}}),t.hooks.add("before-tokenize",function(c){if(/<\?/.test(c.code)){var d=/<\?(?:[^"'/#]|\/(?![*/])|("|')(?:\\[\s\S]|(?!\1)[^\\])*\1|(?:\/\/|#(?!\[))(?:[^?\n\r]|\?(?!>))*(?=$|\?>|[\r\n])|#\[|\/\*(?:[^*]|\*(?!\/))*(?:\*\/|$))*?(?:\?>|$)/g;t.languages["markup-templating"].buildPlaceholders(c,"php",d);}}),t.hooks.add("after-tokenize",function(c){t.languages["markup-templating"].tokenizePlaceholders(c,"php");});})(Prism);(function(t){var e=/[*&][^\s[\]{},]+/,u=/!(?:<[\w\-%#;/?:@&=+$,.!~*'()[\]]+>|(?:[a-zA-Z\d-]*!)?[\w\-%#;/?:@&=+$.~*'()]+)?/,n="(?:"+u.source+"(?:[ 	]+"+e.source+")?|"+e.source+"(?:[ 	]+"+u.source+")?)",r=/(?:[^\s\x00-\x08\x0e-\x1f!"#%&'*,\-:>?@[\]`{|}\x7f-\x84\x86-\x9f\ud800-\udfff\ufffe\uffff]|[?:-]<PLAIN>)(?:[ \t]*(?:(?![#:])<PLAIN>|:<PLAIN>))*/.source.replace(/<PLAIN>/g,function(){return /[^\s\x00-\x08\x0e-\x1f,[\]{}\x7f-\x84\x86-\x9f\ud800-\udfff\ufffe\uffff]/.source}),a=/"(?:[^"\\\r\n]|\\.)*"|'(?:[^'\\\r\n]|\\.)*'/.source;function i(l,c){c=(c||"").replace(/m/g,"")+"m";var d=/([:\-,[{]\s*(?:\s<<prop>>[ \t]+)?)(?:<<value>>)(?=[ \t]*(?:$|,|\]|\}|(?:[\r\n]\s*)?#))/.source.replace(/<<prop>>/g,function(){return n}).replace(/<<value>>/g,function(){return l});return RegExp(d,c)}t.languages.yaml={scalar:{pattern:RegExp(/([\-:]\s*(?:\s<<prop>>[ \t]+)?[|>])[ \t]*(?:((?:\r?\n|\r)[ \t]+)\S[^\r\n]*(?:\2[^\r\n]+)*)/.source.replace(/<<prop>>/g,function(){return n})),lookbehind:!0,alias:"string"},comment:/#.*/,key:{pattern:RegExp(/((?:^|[:\-,[{\r\n?])[ \t]*(?:<<prop>>[ \t]+)?)<<key>>(?=\s*:\s)/.source.replace(/<<prop>>/g,function(){return n}).replace(/<<key>>/g,function(){return "(?:"+r+"|"+a+")"})),lookbehind:!0,greedy:!0,alias:"atrule"},directive:{pattern:/(^[ \t]*)%.+/m,lookbehind:!0,alias:"important"},datetime:{pattern:i(/\d{4}-\d\d?-\d\d?(?:[tT]|[ \t]+)\d\d?:\d{2}:\d{2}(?:\.\d*)?(?:[ \t]*(?:Z|[-+]\d\d?(?::\d{2})?))?|\d{4}-\d{2}-\d{2}|\d\d?:\d{2}(?::\d{2}(?:\.\d*)?)?/.source),lookbehind:!0,alias:"number"},boolean:{pattern:i(/false|true/.source,"i"),lookbehind:!0,alias:"important"},null:{pattern:i(/null|~/.source,"i"),lookbehind:!0,alias:"important"},string:{pattern:i(a),lookbehind:!0,greedy:!0},number:{pattern:i(/[+-]?(?:0x[\da-f]+|0o[0-7]+|(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|\.inf|\.nan)/.source,"i"),lookbehind:!0},tag:u,important:e,punctuation:/---|[:[\]{}\-,|>?]|\.\.\./},t.languages.yml=t.languages.yaml;})(Prism);(function(t){function e(u,n){return "___"+u.toUpperCase()+n+"___"}Object.defineProperties(t.languages["markup-templating"]={},{buildPlaceholders:{value:function(u,n,r,a){if(u.language===n){var i=u.tokenStack=[];u.code=u.code.replace(r,function(l){if(typeof a=="function"&&!a(l))return l;for(var c=i.length,d;u.code.indexOf(d=e(n,c))!==-1;)++c;return i[c]=l,d}),u.grammar=t.languages.markup;}}},tokenizePlaceholders:{value:function(u,n){if(u.language!==n||!u.tokenStack)return;u.grammar=t.languages[n];var r=0,a=Object.keys(u.tokenStack);function i(l){for(var c=0;c<l.length&&!(r>=a.length);c++){var d=l[c];if(typeof d=="string"||d.content&&typeof d.content=="string"){var f=a[r],h=u.tokenStack[f],s=typeof d=="string"?d:d.content,o=e(n,f),D=s.indexOf(o);if(D>-1){++r;var E=s.substring(0,D),y=new t.Token(n,t.tokenize(h,u.grammar),"language-"+n,h),v=s.substring(D+o.length),w=[];E&&w.push.apply(w,i([E])),w.push(y),v&&w.push.apply(w,i([v])),typeof d=="string"?l.splice.apply(l,[c,1].concat(w)):d.content=w;}}else d.content&&i(d.content);}return l}i(u.tokens);}}});})(Prism);const Rn='<svg class="md-link-icon" viewBox="0 0 16 16" version="1.1" width="16" height="16" aria-hidden="true" fill="currentColor"><path d="m7.775 3.275 1.25-1.25a3.5 3.5 0 1 1 4.95 4.95l-2.5 2.5a3.5 3.5 0 0 1-4.95 0 .751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018 1.998 1.998 0 0 0 2.83 0l2.5-2.5a2.002 2.002 0 0 0-2.83-2.83l-1.25 1.25a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042Zm-4.69 9.64a1.998 1.998 0 0 0 2.83 0l1.25-1.25a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042l-1.25 1.25a3.5 3.5 0 1 1-4.95-4.95l2.5-2.5a3.5 3.5 0 0 1 4.95 0 .751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018 1.998 1.998 0 0 0-2.83 0l-2.5 2.5a1.998 1.998 0 0 0 0 2.83Z"></path></svg>',Pn=`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15 15" color="currentColor" aria-hidden="true" aria-label="Copy" stroke-width="1.3" width="15" height="15">
  <path fill="currentColor" d="M12.728 4.545v8.182H4.545V4.545zm0 -0.909H4.545a0.909 0.909 0 0 0 -0.909 0.909v8.182a0.909 0.909 0 0 0 0.909 0.909h8.182a0.909 0.909 0 0 0 0.909 -0.909V4.545a0.909 0.909 0 0 0 -0.909 -0.909"/>
  <path fill="currentColor" d="M1.818 8.182H0.909V1.818a0.909 0.909 0 0 1 0.909 -0.909h6.364v0.909H1.818Z"/>
</svg>

`,Mn=`<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 17 17" aria-hidden="true" aria-label="Copied" fill="none" stroke="currentColor" stroke-width="1.3">
  <path d="m13.813 4.781 -7.438 7.438 -3.188 -3.188"/>
</svg>
`,Nu=`<button title="copy" class="copy_code_button">
  <span class="copy-text">${Pn}</span>
  <span class="check">${Mn}</span>
</button>`,ct$3=/[&<>"']/,qn=new RegExp(ct$3.source,"g"),lt$2=/[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,Un=new RegExp(lt$2.source,"g"),Hn={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"},Bu=t=>Hn[t]||"";function eu(t,e){if(e){if(ct$3.test(t))return t.replace(qn,Bu)}else if(lt$2.test(t))return t.replace(Un,Bu);return t}function zn(t){const e=t.map(u=>({start:new RegExp(u.left.replace(/[-\/\\^$*+?.()|[\]{}]/g,"\\$&")),end:new RegExp(u.right.replace(/[-\/\\^$*+?.()|[\]{}]/g,"\\$&"))}));return {name:"latex",level:"block",start(u){for(const n of e){const r=u.match(n.start);if(r)return r.index}return -1},tokenizer(u,n){for(const r of e){const a=new RegExp(`${r.start.source}([\\s\\S]+?)${r.end.source}`).exec(u);if(a)return {type:"latex",raw:a[0],text:a[1].trim()}}},renderer(u){return `<div class="latex-block">${u.text}</div>`}}}function jn(){return {name:"mermaid",level:"block",start(t){return t.match(/^```mermaid\s*\n/)?.index},tokenizer(t){const e=/^```mermaid\s*\n([\s\S]*?)```\s*(?:\n|$)/.exec(t);if(e)return {type:"mermaid",raw:e[0],text:e[1].trim()}},renderer(t){return `<div class="mermaid">${t.text}</div>
`}}}const $n={code(t,e,u){const n=(e??"").match(/\S*/)?.[0]??"";return t=t.replace(/\n$/,"")+`
`,!n||n==="mermaid"?'<div class="code_wrap">'+Nu+"<pre><code>"+(u?t:eu(t,!0))+`</code></pre></div>
`:'<div class="code_wrap">'+Nu+'<pre><code class="language-'+eu(n)+'">'+(u?t:eu(t,!0))+`</code></pre></div>
`}},Gn=new pu;function Vn({header_links:t,line_breaks:e,latex_delimiters:u}){const n=new rt$1;n.use({gfm:!0,pedantic:!1,breaks:e},kn({highlight:(i,l)=>V$1.languages?.[l]?V$1.highlight(i,V$1.languages[l],l):i}),{renderer:$n}),t&&(n.use(On()),n.use({extensions:[{name:"heading",level:"block",renderer(i){const l=i.raw.toLowerCase().trim().replace(/<[!\/a-z].*?>/gi,""),c="h"+Gn.slug(l),d=i.depth,f=this.parser.parseInline(i.tokens);return `<h${d} id="${c}"><a class="md-header-anchor" href="#${c}">${Rn}</a>${f}</h${d}>
`}}]}));const r=jn(),a=zn(u);return n.use({extensions:[r,a]}),n}var dt$2={},ve={},bu={},we$1={},hu={};Object.defineProperty(hu,"__esModule",{value:!0});hu.default=new Uint16Array('ᵁ<Õıʊҝջאٵ۞ޢߖࠏ੊ઑඡ๭༉༦჊ረዡᐕᒝᓃᓟᔥ\0\0\0\0\0\0ᕫᛍᦍᰒᷝ὾⁠↰⊍⏀⏻⑂⠤⤒ⴈ⹈⿎〖㊺㘹㞬㣾㨨㩱㫠㬮ࠀEMabcfglmnoprstu\\bfms¦³¹ÈÏlig耻Æ䃆P耻&䀦cute耻Á䃁reve;䄂Āiyx}rc耻Â䃂;䐐r;쀀𝔄rave耻À䃀pha;䎑acr;䄀d;橓Āgp¡on;䄄f;쀀𝔸plyFunction;恡ing耻Å䃅Ācs¾Ãr;쀀𝒜ign;扔ilde耻Ã䃃ml耻Ä䃄ЀaceforsuåûþėĜĢħĪĀcrêòkslash;或Ŷöø;櫧ed;挆y;䐑ƀcrtąċĔause;戵noullis;愬a;䎒r;쀀𝔅pf;쀀𝔹eve;䋘còēmpeq;扎܀HOacdefhilorsuōőŖƀƞƢƵƷƺǜȕɳɸɾcy;䐧PY耻©䂩ƀcpyŝŢźute;䄆Ā;iŧŨ拒talDifferentialD;慅leys;愭ȀaeioƉƎƔƘron;䄌dil耻Ç䃇rc;䄈nint;戰ot;䄊ĀdnƧƭilla;䂸terDot;䂷òſi;䎧rcleȀDMPTǇǋǑǖot;抙inus;抖lus;投imes;抗oĀcsǢǸkwiseContourIntegral;戲eCurlyĀDQȃȏoubleQuote;思uote;怙ȀlnpuȞȨɇɕonĀ;eȥȦ户;橴ƀgitȯȶȺruent;扡nt;戯ourIntegral;戮ĀfrɌɎ;愂oduct;成nterClockwiseContourIntegral;戳oss;樯cr;쀀𝒞pĀ;Cʄʅ拓ap;才րDJSZacefiosʠʬʰʴʸˋ˗ˡ˦̳ҍĀ;oŹʥtrahd;椑cy;䐂cy;䐅cy;䐏ƀgrsʿ˄ˇger;怡r;憡hv;櫤Āayː˕ron;䄎;䐔lĀ;t˝˞戇a;䎔r;쀀𝔇Āaf˫̧Ācm˰̢riticalȀADGT̖̜̀̆cute;䂴oŴ̋̍;䋙bleAcute;䋝rave;䁠ilde;䋜ond;拄ferentialD;慆Ѱ̽\0\0\0͔͂\0Ѕf;쀀𝔻ƀ;DE͈͉͍䂨ot;惜qual;扐blèCDLRUVͣͲ΂ϏϢϸontourIntegraìȹoɴ͹\0\0ͻ»͉nArrow;懓Āeo·ΤftƀARTΐΖΡrrow;懐ightArrow;懔eåˊngĀLRΫτeftĀARγιrrow;柸ightArrow;柺ightArrow;柹ightĀATϘϞrrow;懒ee;抨pɁϩ\0\0ϯrrow;懑ownArrow;懕erticalBar;戥ǹABLRTaВЪаўѿͼrrowƀ;BUНОТ憓ar;椓pArrow;懵reve;䌑eft˒к\0ц\0ѐightVector;楐eeVector;楞ectorĀ;Bљњ憽ar;楖ightǔѧ\0ѱeeVector;楟ectorĀ;BѺѻ懁ar;楗eeĀ;A҆҇护rrow;憧ĀctҒҗr;쀀𝒟rok;䄐ࠀNTacdfglmopqstuxҽӀӄӋӞӢӧӮӵԡԯԶՒ՝ՠեG;䅊H耻Ð䃐cute耻É䃉ƀaiyӒӗӜron;䄚rc耻Ê䃊;䐭ot;䄖r;쀀𝔈rave耻È䃈ement;戈ĀapӺӾcr;䄒tyɓԆ\0\0ԒmallSquare;旻erySmallSquare;斫ĀgpԦԪon;䄘f;쀀𝔼silon;䎕uĀaiԼՉlĀ;TՂՃ橵ilde;扂librium;懌Āci՗՚r;愰m;橳a;䎗ml耻Ë䃋Āipժկsts;戃onentialE;慇ʀcfiosօֈ֍ֲ׌y;䐤r;쀀𝔉lledɓ֗\0\0֣mallSquare;旼erySmallSquare;斪Ͱֺ\0ֿ\0\0ׄf;쀀𝔽All;戀riertrf;愱cò׋؀JTabcdfgorstר׬ׯ׺؀ؒؖ؛؝أ٬ٲcy;䐃耻>䀾mmaĀ;d׷׸䎓;䏜reve;䄞ƀeiy؇،ؐdil;䄢rc;䄜;䐓ot;䄠r;쀀𝔊;拙pf;쀀𝔾eater̀EFGLSTصلَٖٛ٦qualĀ;Lؾؿ扥ess;招ullEqual;执reater;檢ess;扷lantEqual;橾ilde;扳cr;쀀𝒢;扫ЀAacfiosuڅڋږڛڞڪھۊRDcy;䐪Āctڐڔek;䋇;䁞irc;䄤r;愌lbertSpace;愋ǰگ\0ڲf;愍izontalLine;攀Āctۃۅòکrok;䄦mpńېۘownHumðįqual;扏܀EJOacdfgmnostuۺ۾܃܇܎ܚܞܡܨ݄ݸދޏޕcy;䐕lig;䄲cy;䐁cute耻Í䃍Āiyܓܘrc耻Î䃎;䐘ot;䄰r;愑rave耻Ì䃌ƀ;apܠܯܿĀcgܴܷr;䄪inaryI;慈lieóϝǴ݉\0ݢĀ;eݍݎ戬Āgrݓݘral;戫section;拂isibleĀCTݬݲomma;恣imes;恢ƀgptݿރވon;䄮f;쀀𝕀a;䎙cr;愐ilde;䄨ǫޚ\0ޞcy;䐆l耻Ï䃏ʀcfosuެ޷޼߂ߐĀiyޱ޵rc;䄴;䐙r;쀀𝔍pf;쀀𝕁ǣ߇\0ߌr;쀀𝒥rcy;䐈kcy;䐄΀HJacfosߤߨ߽߬߱ࠂࠈcy;䐥cy;䐌ppa;䎚Āey߶߻dil;䄶;䐚r;쀀𝔎pf;쀀𝕂cr;쀀𝒦րJTaceflmostࠥࠩࠬࡐࡣ঳সে্਷ੇcy;䐉耻<䀼ʀcmnpr࠷࠼ࡁࡄࡍute;䄹bda;䎛g;柪lacetrf;愒r;憞ƀaeyࡗ࡜ࡡron;䄽dil;䄻;䐛Āfsࡨ॰tԀACDFRTUVarࡾࢩࢱࣦ࣠ࣼयज़ΐ४Ānrࢃ࢏gleBracket;柨rowƀ;BR࢙࢚࢞憐ar;懤ightArrow;懆eiling;挈oǵࢷ\0ࣃbleBracket;柦nǔࣈ\0࣒eeVector;楡ectorĀ;Bࣛࣜ懃ar;楙loor;挊ightĀAV࣯ࣵrrow;憔ector;楎Āerँगeƀ;AVउऊऐ抣rrow;憤ector;楚iangleƀ;BEतथऩ抲ar;槏qual;抴pƀDTVषूौownVector;楑eeVector;楠ectorĀ;Bॖॗ憿ar;楘ectorĀ;B॥०憼ar;楒ightáΜs̀EFGLSTॾঋকঝঢভqualGreater;拚ullEqual;扦reater;扶ess;檡lantEqual;橽ilde;扲r;쀀𝔏Ā;eঽা拘ftarrow;懚idot;䄿ƀnpw৔ਖਛgȀLRlr৞৷ਂਐeftĀAR০৬rrow;柵ightArrow;柷ightArrow;柶eftĀarγਊightáοightáϊf;쀀𝕃erĀLRਢਬeftArrow;憙ightArrow;憘ƀchtਾੀੂòࡌ;憰rok;䅁;扪Ѐacefiosuਗ਼੝੠੷੼અઋ઎p;椅y;䐜Ādl੥੯iumSpace;恟lintrf;愳r;쀀𝔐nusPlus;戓pf;쀀𝕄cò੶;䎜ҀJacefostuણધભીଔଙඑ඗ඞcy;䐊cute;䅃ƀaey઴હાron;䅇dil;䅅;䐝ƀgswે૰଎ativeƀMTV૓૟૨ediumSpace;怋hiĀcn૦૘ë૙eryThiî૙tedĀGL૸ଆreaterGreateòٳessLesóੈLine;䀊r;쀀𝔑ȀBnptଢନଷ଺reak;恠BreakingSpace;䂠f;愕ڀ;CDEGHLNPRSTV୕ୖ୪୼஡௫ఄ౞಄ದ೘ൡඅ櫬Āou୛୤ngruent;扢pCap;扭oubleVerticalBar;戦ƀlqxஃஊ஛ement;戉ualĀ;Tஒஓ扠ilde;쀀≂̸ists;戄reater΀;EFGLSTஶஷ஽௉௓௘௥扯qual;扱ullEqual;쀀≧̸reater;쀀≫̸ess;批lantEqual;쀀⩾̸ilde;扵umpń௲௽ownHump;쀀≎̸qual;쀀≏̸eĀfsఊధtTriangleƀ;BEచఛడ拪ar;쀀⧏̸qual;括s̀;EGLSTవశ఼ౄోౘ扮qual;扰reater;扸ess;쀀≪̸lantEqual;쀀⩽̸ilde;扴estedĀGL౨౹reaterGreater;쀀⪢̸essLess;쀀⪡̸recedesƀ;ESಒಓಛ技qual;쀀⪯̸lantEqual;拠ĀeiಫಹverseElement;戌ghtTriangleƀ;BEೋೌ೒拫ar;쀀⧐̸qual;拭ĀquೝഌuareSuĀbp೨೹setĀ;E೰ೳ쀀⊏̸qual;拢ersetĀ;Eഃആ쀀⊐̸qual;拣ƀbcpഓതൎsetĀ;Eഛഞ쀀⊂⃒qual;抈ceedsȀ;ESTലള഻െ抁qual;쀀⪰̸lantEqual;拡ilde;쀀≿̸ersetĀ;E൘൛쀀⊃⃒qual;抉ildeȀ;EFT൮൯൵ൿ扁qual;扄ullEqual;扇ilde;扉erticalBar;戤cr;쀀𝒩ilde耻Ñ䃑;䎝܀Eacdfgmoprstuvලෂ෉෕ෛ෠෧෼ขภยา฿ไlig;䅒cute耻Ó䃓Āiy෎ීrc耻Ô䃔;䐞blac;䅐r;쀀𝔒rave耻Ò䃒ƀaei෮ෲ෶cr;䅌ga;䎩cron;䎟pf;쀀𝕆enCurlyĀDQฎบoubleQuote;怜uote;怘;橔Āclวฬr;쀀𝒪ash耻Ø䃘iŬื฼de耻Õ䃕es;樷ml耻Ö䃖erĀBP๋๠Āar๐๓r;怾acĀek๚๜;揞et;掴arenthesis;揜Ҁacfhilors๿ງຊຏຒດຝະ໼rtialD;戂y;䐟r;쀀𝔓i;䎦;䎠usMinus;䂱Āipຢອncareplanåڝf;愙Ȁ;eio຺ູ໠໤檻cedesȀ;EST່້໏໚扺qual;檯lantEqual;扼ilde;找me;怳Ādp໩໮uct;戏ortionĀ;aȥ໹l;戝Āci༁༆r;쀀𝒫;䎨ȀUfos༑༖༛༟OT耻"䀢r;쀀𝔔pf;愚cr;쀀𝒬؀BEacefhiorsu༾གྷཇའཱིྦྷྪྭ႖ႩႴႾarr;椐G耻®䂮ƀcnrཎནབute;䅔g;柫rĀ;tཛྷཝ憠l;椖ƀaeyཧཬཱron;䅘dil;䅖;䐠Ā;vླྀཹ愜erseĀEUྂྙĀlq྇ྎement;戋uilibrium;懋pEquilibrium;楯r»ཹo;䎡ghtЀACDFTUVa࿁࿫࿳ဢဨၛႇϘĀnr࿆࿒gleBracket;柩rowƀ;BL࿜࿝࿡憒ar;懥eftArrow;懄eiling;按oǵ࿹\0စbleBracket;柧nǔည\0နeeVector;楝ectorĀ;Bဝသ懂ar;楕loor;挋Āerိ၃eƀ;AVဵံြ抢rrow;憦ector;楛iangleƀ;BEၐၑၕ抳ar;槐qual;抵pƀDTVၣၮၸownVector;楏eeVector;楜ectorĀ;Bႂႃ憾ar;楔ectorĀ;B႑႒懀ar;楓Āpuႛ႞f;愝ndImplies;楰ightarrow;懛ĀchႹႼr;愛;憱leDelayed;槴ڀHOacfhimoqstuფჱჷჽᄙᄞᅑᅖᅡᅧᆵᆻᆿĀCcჩხHcy;䐩y;䐨FTcy;䐬cute;䅚ʀ;aeiyᄈᄉᄎᄓᄗ檼ron;䅠dil;䅞rc;䅜;䐡r;쀀𝔖ortȀDLRUᄪᄴᄾᅉownArrow»ОeftArrow»࢚ightArrow»࿝pArrow;憑gma;䎣allCircle;战pf;쀀𝕊ɲᅭ\0\0ᅰt;戚areȀ;ISUᅻᅼᆉᆯ斡ntersection;抓uĀbpᆏᆞsetĀ;Eᆗᆘ抏qual;抑ersetĀ;Eᆨᆩ抐qual;抒nion;抔cr;쀀𝒮ar;拆ȀbcmpᇈᇛሉላĀ;sᇍᇎ拐etĀ;Eᇍᇕqual;抆ĀchᇠህeedsȀ;ESTᇭᇮᇴᇿ扻qual;檰lantEqual;扽ilde;承Tháྌ;我ƀ;esሒሓሣ拑rsetĀ;Eሜም抃qual;抇et»ሓրHRSacfhiorsሾቄ቉ቕ቞ቱቶኟዂወዑORN耻Þ䃞ADE;愢ĀHc቎ቒcy;䐋y;䐦Ābuቚቜ;䀉;䎤ƀaeyብቪቯron;䅤dil;䅢;䐢r;쀀𝔗Āeiቻ኉ǲኀ\0ኇefore;戴a;䎘Ācn኎ኘkSpace;쀀  Space;怉ldeȀ;EFTካኬኲኼ戼qual;扃ullEqual;扅ilde;扈pf;쀀𝕋ipleDot;惛Āctዖዛr;쀀𝒯rok;䅦ૡዷጎጚጦ\0ጬጱ\0\0\0\0\0ጸጽ፷ᎅ\0᏿ᐄᐊᐐĀcrዻጁute耻Ú䃚rĀ;oጇገ憟cir;楉rǣጓ\0጖y;䐎ve;䅬Āiyጞጣrc耻Û䃛;䐣blac;䅰r;쀀𝔘rave耻Ù䃙acr;䅪Ādiፁ፩erĀBPፈ፝Āarፍፐr;䁟acĀekፗፙ;揟et;掵arenthesis;揝onĀ;P፰፱拃lus;抎Āgp፻፿on;䅲f;쀀𝕌ЀADETadps᎕ᎮᎸᏄϨᏒᏗᏳrrowƀ;BDᅐᎠᎤar;椒ownArrow;懅ownArrow;憕quilibrium;楮eeĀ;AᏋᏌ报rrow;憥ownáϳerĀLRᏞᏨeftArrow;憖ightArrow;憗iĀ;lᏹᏺ䏒on;䎥ing;䅮cr;쀀𝒰ilde;䅨ml耻Ü䃜ҀDbcdefosvᐧᐬᐰᐳᐾᒅᒊᒐᒖash;披ar;櫫y;䐒ashĀ;lᐻᐼ抩;櫦Āerᑃᑅ;拁ƀbtyᑌᑐᑺar;怖Ā;iᑏᑕcalȀBLSTᑡᑥᑪᑴar;戣ine;䁼eparator;杘ilde;所ThinSpace;怊r;쀀𝔙pf;쀀𝕍cr;쀀𝒱dash;抪ʀcefosᒧᒬᒱᒶᒼirc;䅴dge;拀r;쀀𝔚pf;쀀𝕎cr;쀀𝒲Ȁfiosᓋᓐᓒᓘr;쀀𝔛;䎞pf;쀀𝕏cr;쀀𝒳ҀAIUacfosuᓱᓵᓹᓽᔄᔏᔔᔚᔠcy;䐯cy;䐇cy;䐮cute耻Ý䃝Āiyᔉᔍrc;䅶;䐫r;쀀𝔜pf;쀀𝕐cr;쀀𝒴ml;䅸ЀHacdefosᔵᔹᔿᕋᕏᕝᕠᕤcy;䐖cute;䅹Āayᕄᕉron;䅽;䐗ot;䅻ǲᕔ\0ᕛoWidtè૙a;䎖r;愨pf;愤cr;쀀𝒵௡ᖃᖊᖐ\0ᖰᖶᖿ\0\0\0\0ᗆᗛᗫᙟ᙭\0ᚕ᚛ᚲᚹ\0ᚾcute耻á䃡reve;䄃̀;Ediuyᖜᖝᖡᖣᖨᖭ戾;쀀∾̳;房rc耻â䃢te肻´̆;䐰lig耻æ䃦Ā;r²ᖺ;쀀𝔞rave耻à䃠ĀepᗊᗖĀfpᗏᗔsym;愵èᗓha;䎱ĀapᗟcĀclᗤᗧr;䄁g;樿ɤᗰ\0\0ᘊʀ;adsvᗺᗻᗿᘁᘇ戧nd;橕;橜lope;橘;橚΀;elmrszᘘᘙᘛᘞᘿᙏᙙ戠;榤e»ᘙsdĀ;aᘥᘦ戡ѡᘰᘲᘴᘶᘸᘺᘼᘾ;榨;榩;榪;榫;榬;榭;榮;榯tĀ;vᙅᙆ戟bĀ;dᙌᙍ抾;榝Āptᙔᙗh;戢»¹arr;捼Āgpᙣᙧon;䄅f;쀀𝕒΀;Eaeiop዁ᙻᙽᚂᚄᚇᚊ;橰cir;橯;扊d;手s;䀧roxĀ;e዁ᚒñᚃing耻å䃥ƀctyᚡᚦᚨr;쀀𝒶;䀪mpĀ;e዁ᚯñʈilde耻ã䃣ml耻ä䃤Āciᛂᛈoninôɲnt;樑ࠀNabcdefiklnoprsu᛭ᛱᜰ᜼ᝃᝈ᝸᝽០៦ᠹᡐᜍ᤽᥈ᥰot;櫭Ācrᛶ᜞kȀcepsᜀᜅᜍᜓong;扌psilon;䏶rime;怵imĀ;e᜚᜛戽q;拍Ŷᜢᜦee;抽edĀ;gᜬᜭ挅e»ᜭrkĀ;t፜᜷brk;掶Āoyᜁᝁ;䐱quo;怞ʀcmprtᝓ᝛ᝡᝤᝨausĀ;eĊĉptyv;榰séᜌnoõēƀahwᝯ᝱ᝳ;䎲;愶een;扬r;쀀𝔟g΀costuvwឍឝឳេ៕៛៞ƀaiuបពរðݠrc;旯p»፱ƀdptឤឨឭot;樀lus;樁imes;樂ɱឹ\0\0ើcup;樆ar;昅riangleĀdu៍្own;施p;斳plus;樄eåᑄåᒭarow;植ƀako៭ᠦᠵĀcn៲ᠣkƀlst៺֫᠂ozenge;槫riangleȀ;dlr᠒᠓᠘᠝斴own;斾eft;旂ight;斸k;搣Ʊᠫ\0ᠳƲᠯ\0ᠱ;斒;斑4;斓ck;斈ĀeoᠾᡍĀ;qᡃᡆ쀀=⃥uiv;쀀≡⃥t;挐Ȁptwxᡙᡞᡧᡬf;쀀𝕓Ā;tᏋᡣom»Ꮜtie;拈؀DHUVbdhmptuvᢅᢖᢪᢻᣗᣛᣬ᣿ᤅᤊᤐᤡȀLRlrᢎᢐᢒᢔ;敗;敔;敖;敓ʀ;DUduᢡᢢᢤᢦᢨ敐;敦;敩;敤;敧ȀLRlrᢳᢵᢷᢹ;敝;敚;敜;教΀;HLRhlrᣊᣋᣍᣏᣑᣓᣕ救;敬;散;敠;敫;敢;敟ox;槉ȀLRlrᣤᣦᣨᣪ;敕;敒;攐;攌ʀ;DUduڽ᣷᣹᣻᣽;敥;敨;攬;攴inus;抟lus;択imes;抠ȀLRlrᤙᤛᤝ᤟;敛;敘;攘;攔΀;HLRhlrᤰᤱᤳᤵᤷ᤻᤹攂;敪;敡;敞;攼;攤;攜Āevģ᥂bar耻¦䂦Ȁceioᥑᥖᥚᥠr;쀀𝒷mi;恏mĀ;e᜚᜜lƀ;bhᥨᥩᥫ䁜;槅sub;柈Ŭᥴ᥾lĀ;e᥹᥺怢t»᥺pƀ;Eeįᦅᦇ;檮Ā;qۜۛೡᦧ\0᧨ᨑᨕᨲ\0ᨷᩐ\0\0᪴\0\0᫁\0\0ᬡᬮ᭍᭒\0᯽\0ᰌƀcpr᦭ᦲ᧝ute;䄇̀;abcdsᦿᧀᧄ᧊᧕᧙戩nd;橄rcup;橉Āau᧏᧒p;橋p;橇ot;橀;쀀∩︀Āeo᧢᧥t;恁îړȀaeiu᧰᧻ᨁᨅǰ᧵\0᧸s;橍on;䄍dil耻ç䃧rc;䄉psĀ;sᨌᨍ橌m;橐ot;䄋ƀdmnᨛᨠᨦil肻¸ƭptyv;榲t脀¢;eᨭᨮ䂢räƲr;쀀𝔠ƀceiᨽᩀᩍy;䑇ckĀ;mᩇᩈ朓ark»ᩈ;䏇r΀;Ecefms᩟᩠ᩢᩫ᪤᪪᪮旋;槃ƀ;elᩩᩪᩭ䋆q;扗eɡᩴ\0\0᪈rrowĀlr᩼᪁eft;憺ight;憻ʀRSacd᪒᪔᪖᪚᪟»ཇ;擈st;抛irc;抚ash;抝nint;樐id;櫯cir;槂ubsĀ;u᪻᪼晣it»᪼ˬ᫇᫔᫺\0ᬊonĀ;eᫍᫎ䀺Ā;qÇÆɭ᫙\0\0᫢aĀ;t᫞᫟䀬;䁀ƀ;fl᫨᫩᫫戁îᅠeĀmx᫱᫶ent»᫩eóɍǧ᫾\0ᬇĀ;dኻᬂot;橭nôɆƀfryᬐᬔᬗ;쀀𝕔oäɔ脀©;sŕᬝr;愗Āaoᬥᬩrr;憵ss;朗Ācuᬲᬷr;쀀𝒸Ābpᬼ᭄Ā;eᭁᭂ櫏;櫑Ā;eᭉᭊ櫐;櫒dot;拯΀delprvw᭠᭬᭷ᮂᮬᯔ᯹arrĀlr᭨᭪;椸;椵ɰ᭲\0\0᭵r;拞c;拟arrĀ;p᭿ᮀ憶;椽̀;bcdosᮏᮐᮖᮡᮥᮨ截rcap;橈Āauᮛᮞp;橆p;橊ot;抍r;橅;쀀∪︀Ȁalrv᮵ᮿᯞᯣrrĀ;mᮼᮽ憷;椼yƀevwᯇᯔᯘqɰᯎ\0\0ᯒreã᭳uã᭵ee;拎edge;拏en耻¤䂤earrowĀlrᯮ᯳eft»ᮀight»ᮽeäᯝĀciᰁᰇoninôǷnt;戱lcty;挭ঀAHabcdefhijlorstuwz᰸᰻᰿ᱝᱩᱵᲊᲞᲬᲷ᳻᳿ᴍᵻᶑᶫᶻ᷆᷍rò΁ar;楥Ȁglrs᱈ᱍ᱒᱔ger;怠eth;愸òᄳhĀ;vᱚᱛ怐»ऊūᱡᱧarow;椏aã̕Āayᱮᱳron;䄏;䐴ƀ;ao̲ᱼᲄĀgrʿᲁr;懊tseq;橷ƀglmᲑᲔᲘ耻°䂰ta;䎴ptyv;榱ĀirᲣᲨsht;楿;쀀𝔡arĀlrᲳᲵ»ࣜ»သʀaegsv᳂͸᳖᳜᳠mƀ;oș᳊᳔ndĀ;ș᳑uit;晦amma;䏝in;拲ƀ;io᳧᳨᳸䃷de脀÷;o᳧ᳰntimes;拇nø᳷cy;䑒cɯᴆ\0\0ᴊrn;挞op;挍ʀlptuwᴘᴝᴢᵉᵕlar;䀤f;쀀𝕕ʀ;emps̋ᴭᴷᴽᵂqĀ;d͒ᴳot;扑inus;戸lus;戔quare;抡blebarwedgåúnƀadhᄮᵝᵧownarrowóᲃarpoonĀlrᵲᵶefôᲴighôᲶŢᵿᶅkaro÷གɯᶊ\0\0ᶎrn;挟op;挌ƀcotᶘᶣᶦĀryᶝᶡ;쀀𝒹;䑕l;槶rok;䄑Ādrᶰᶴot;拱iĀ;fᶺ᠖斿Āah᷀᷃ròЩaòྦangle;榦Āci᷒ᷕy;䑟grarr;柿ऀDacdefglmnopqrstuxḁḉḙḸոḼṉṡṾấắẽỡἪἷὄ὎὚ĀDoḆᴴoôᲉĀcsḎḔute耻é䃩ter;橮ȀaioyḢḧḱḶron;䄛rĀ;cḭḮ扖耻ê䃪lon;払;䑍ot;䄗ĀDrṁṅot;扒;쀀𝔢ƀ;rsṐṑṗ檚ave耻è䃨Ā;dṜṝ檖ot;檘Ȁ;ilsṪṫṲṴ檙nters;揧;愓Ā;dṹṺ檕ot;檗ƀapsẅẉẗcr;䄓tyƀ;svẒẓẕ戅et»ẓpĀ1;ẝẤĳạả;怄;怅怃ĀgsẪẬ;䅋p;怂ĀgpẴẸon;䄙f;쀀𝕖ƀalsỄỎỒrĀ;sỊị拕l;槣us;橱iƀ;lvỚớở䎵on»ớ;䏵ȀcsuvỪỳἋἣĀioữḱrc»Ḯɩỹ\0\0ỻíՈantĀglἂἆtr»ṝess»Ṻƀaeiἒ἖Ἒls;䀽st;扟vĀ;DȵἠD;橸parsl;槥ĀDaἯἳot;打rr;楱ƀcdiἾὁỸr;愯oô͒ĀahὉὋ;䎷耻ð䃰Āmrὓὗl耻ë䃫o;悬ƀcipὡὤὧl;䀡sôծĀeoὬὴctatioîՙnentialåչৡᾒ\0ᾞ\0ᾡᾧ\0\0ῆῌ\0ΐ\0ῦῪ \0 ⁚llingdotseñṄy;䑄male;晀ƀilrᾭᾳ῁lig;耀ﬃɩᾹ\0\0᾽g;耀ﬀig;耀ﬄ;쀀𝔣lig;耀ﬁlig;쀀fjƀaltῙ῜ῡt;晭ig;耀ﬂns;斱of;䆒ǰ΅\0ῳf;쀀𝕗ĀakֿῷĀ;vῼ´拔;櫙artint;樍Āao‌⁕Ācs‑⁒α‚‰‸⁅⁈\0⁐β•‥‧‪‬\0‮耻½䂽;慓耻¼䂼;慕;慙;慛Ƴ‴\0‶;慔;慖ʴ‾⁁\0\0⁃耻¾䂾;慗;慜5;慘ƶ⁌\0⁎;慚;慝8;慞l;恄wn;挢cr;쀀𝒻ࢀEabcdefgijlnorstv₂₉₟₥₰₴⃰⃵⃺⃿℃ℒℸ̗ℾ⅒↞Ā;lٍ₇;檌ƀcmpₐₕ₝ute;䇵maĀ;dₜ᳚䎳;檆reve;䄟Āiy₪₮rc;䄝;䐳ot;䄡Ȁ;lqsؾق₽⃉ƀ;qsؾٌ⃄lanô٥Ȁ;cdl٥⃒⃥⃕c;檩otĀ;o⃜⃝檀Ā;l⃢⃣檂;檄Ā;e⃪⃭쀀⋛︀s;檔r;쀀𝔤Ā;gٳ؛mel;愷cy;䑓Ȁ;Eajٚℌℎℐ;檒;檥;檤ȀEaesℛℝ℩ℴ;扩pĀ;p℣ℤ檊rox»ℤĀ;q℮ℯ檈Ā;q℮ℛim;拧pf;쀀𝕘Āci⅃ⅆr;愊mƀ;el٫ⅎ⅐;檎;檐茀>;cdlqr׮ⅠⅪⅮⅳⅹĀciⅥⅧ;檧r;橺ot;拗Par;榕uest;橼ʀadelsↄⅪ←ٖ↛ǰ↉\0↎proø₞r;楸qĀlqؿ↖lesó₈ií٫Āen↣↭rtneqq;쀀≩︀Å↪ԀAabcefkosy⇄⇇⇱⇵⇺∘∝∯≨≽ròΠȀilmr⇐⇔⇗⇛rsðᒄf»․ilôکĀdr⇠⇤cy;䑊ƀ;cwࣴ⇫⇯ir;楈;憭ar;意irc;䄥ƀalr∁∎∓rtsĀ;u∉∊晥it»∊lip;怦con;抹r;쀀𝔥sĀew∣∩arow;椥arow;椦ʀamopr∺∾≃≞≣rr;懿tht;戻kĀlr≉≓eftarrow;憩ightarrow;憪f;쀀𝕙bar;怕ƀclt≯≴≸r;쀀𝒽asè⇴rok;䄧Ābp⊂⊇ull;恃hen»ᱛૡ⊣\0⊪\0⊸⋅⋎\0⋕⋳\0\0⋸⌢⍧⍢⍿\0⎆⎪⎴cute耻í䃭ƀ;iyݱ⊰⊵rc耻î䃮;䐸Ācx⊼⊿y;䐵cl耻¡䂡ĀfrΟ⋉;쀀𝔦rave耻ì䃬Ȁ;inoܾ⋝⋩⋮Āin⋢⋦nt;樌t;戭fin;槜ta;愩lig;䄳ƀaop⋾⌚⌝ƀcgt⌅⌈⌗r;䄫ƀelpܟ⌏⌓inåގarôܠh;䄱f;抷ed;䆵ʀ;cfotӴ⌬⌱⌽⍁are;愅inĀ;t⌸⌹戞ie;槝doô⌙ʀ;celpݗ⍌⍐⍛⍡al;抺Āgr⍕⍙eróᕣã⍍arhk;樗rod;樼Ȁcgpt⍯⍲⍶⍻y;䑑on;䄯f;쀀𝕚a;䎹uest耻¿䂿Āci⎊⎏r;쀀𝒾nʀ;EdsvӴ⎛⎝⎡ӳ;拹ot;拵Ā;v⎦⎧拴;拳Ā;iݷ⎮lde;䄩ǫ⎸\0⎼cy;䑖l耻ï䃯̀cfmosu⏌⏗⏜⏡⏧⏵Āiy⏑⏕rc;䄵;䐹r;쀀𝔧ath;䈷pf;쀀𝕛ǣ⏬\0⏱r;쀀𝒿rcy;䑘kcy;䑔Ѐacfghjos␋␖␢␧␭␱␵␻ppaĀ;v␓␔䎺;䏰Āey␛␠dil;䄷;䐺r;쀀𝔨reen;䄸cy;䑅cy;䑜pf;쀀𝕜cr;쀀𝓀஀ABEHabcdefghjlmnoprstuv⑰⒁⒆⒍⒑┎┽╚▀♎♞♥♹♽⚚⚲⛘❝❨➋⟀⠁⠒ƀart⑷⑺⑼rò৆òΕail;椛arr;椎Ā;gঔ⒋;檋ar;楢ॣ⒥\0⒪\0⒱\0\0\0\0\0⒵Ⓔ\0ⓆⓈⓍ\0⓹ute;䄺mptyv;榴raîࡌbda;䎻gƀ;dlࢎⓁⓃ;榑åࢎ;檅uo耻«䂫rЀ;bfhlpst࢙ⓞⓦⓩ⓫⓮⓱⓵Ā;f࢝ⓣs;椟s;椝ë≒p;憫l;椹im;楳l;憢ƀ;ae⓿─┄檫il;椙Ā;s┉┊檭;쀀⪭︀ƀabr┕┙┝rr;椌rk;杲Āak┢┬cĀek┨┪;䁻;䁛Āes┱┳;榋lĀdu┹┻;榏;榍Ȁaeuy╆╋╖╘ron;䄾Ādi═╔il;䄼ìࢰâ┩;䐻Ȁcqrs╣╦╭╽a;椶uoĀ;rนᝆĀdu╲╷har;楧shar;楋h;憲ʀ;fgqs▋▌উ◳◿扤tʀahlrt▘▤▷◂◨rrowĀ;t࢙□aé⓶arpoonĀdu▯▴own»њp»०eftarrows;懇ightƀahs◍◖◞rrowĀ;sࣴࢧarpoonó྘quigarro÷⇰hreetimes;拋ƀ;qs▋ও◺lanôবʀ;cdgsব☊☍☝☨c;檨otĀ;o☔☕橿Ā;r☚☛檁;檃Ā;e☢☥쀀⋚︀s;檓ʀadegs☳☹☽♉♋pproøⓆot;拖qĀgq♃♅ôউgtò⒌ôছiíলƀilr♕࣡♚sht;楼;쀀𝔩Ā;Eজ♣;檑š♩♶rĀdu▲♮Ā;l॥♳;楪lk;斄cy;䑙ʀ;achtੈ⚈⚋⚑⚖rò◁orneòᴈard;楫ri;旺Āio⚟⚤dot;䅀ustĀ;a⚬⚭掰che»⚭ȀEaes⚻⚽⛉⛔;扨pĀ;p⛃⛄檉rox»⛄Ā;q⛎⛏檇Ā;q⛎⚻im;拦Ѐabnoptwz⛩⛴⛷✚✯❁❇❐Ānr⛮⛱g;柬r;懽rëࣁgƀlmr⛿✍✔eftĀar০✇ightá৲apsto;柼ightá৽parrowĀlr✥✩efô⓭ight;憬ƀafl✶✹✽r;榅;쀀𝕝us;樭imes;樴š❋❏st;戗áፎƀ;ef❗❘᠀旊nge»❘arĀ;l❤❥䀨t;榓ʀachmt❳❶❼➅➇ròࢨorneòᶌarĀ;d྘➃;業;怎ri;抿̀achiqt➘➝ੀ➢➮➻quo;怹r;쀀𝓁mƀ;egল➪➬;檍;檏Ābu┪➳oĀ;rฟ➹;怚rok;䅂萀<;cdhilqrࠫ⟒☹⟜⟠⟥⟪⟰Āci⟗⟙;檦r;橹reå◲mes;拉arr;楶uest;橻ĀPi⟵⟹ar;榖ƀ;ef⠀भ᠛旃rĀdu⠇⠍shar;楊har;楦Āen⠗⠡rtneqq;쀀≨︀Å⠞܀Dacdefhilnopsu⡀⡅⢂⢎⢓⢠⢥⢨⣚⣢⣤ઃ⣳⤂Dot;戺Ȁclpr⡎⡒⡣⡽r耻¯䂯Āet⡗⡙;時Ā;e⡞⡟朠se»⡟Ā;sျ⡨toȀ;dluျ⡳⡷⡻owîҌefôएðᏑker;斮Āoy⢇⢌mma;権;䐼ash;怔asuredangle»ᘦr;쀀𝔪o;愧ƀcdn⢯⢴⣉ro耻µ䂵Ȁ;acdᑤ⢽⣀⣄sôᚧir;櫰ot肻·Ƶusƀ;bd⣒ᤃ⣓戒Ā;uᴼ⣘;横ţ⣞⣡p;櫛ò−ðઁĀdp⣩⣮els;抧f;쀀𝕞Āct⣸⣽r;쀀𝓂pos»ᖝƀ;lm⤉⤊⤍䎼timap;抸ఀGLRVabcdefghijlmoprstuvw⥂⥓⥾⦉⦘⧚⧩⨕⨚⩘⩝⪃⪕⪤⪨⬄⬇⭄⭿⮮ⰴⱧⱼ⳩Āgt⥇⥋;쀀⋙̸Ā;v⥐௏쀀≫⃒ƀelt⥚⥲⥶ftĀar⥡⥧rrow;懍ightarrow;懎;쀀⋘̸Ā;v⥻ే쀀≪⃒ightarrow;懏ĀDd⦎⦓ash;抯ash;抮ʀbcnpt⦣⦧⦬⦱⧌la»˞ute;䅄g;쀀∠⃒ʀ;Eiop඄⦼⧀⧅⧈;쀀⩰̸d;쀀≋̸s;䅉roø඄urĀ;a⧓⧔普lĀ;s⧓ସǳ⧟\0⧣p肻 ଷmpĀ;e௹ఀʀaeouy⧴⧾⨃⨐⨓ǰ⧹\0⧻;橃on;䅈dil;䅆ngĀ;dൾ⨊ot;쀀⩭̸p;橂;䐽ash;怓΀;Aadqsxஒ⨩⨭⨻⩁⩅⩐rr;懗rĀhr⨳⨶k;椤Ā;oᏲᏰot;쀀≐̸uiöୣĀei⩊⩎ar;椨í஘istĀ;s஠டr;쀀𝔫ȀEest௅⩦⩹⩼ƀ;qs஼⩭௡ƀ;qs஼௅⩴lanô௢ií௪Ā;rஶ⪁»ஷƀAap⪊⪍⪑rò⥱rr;憮ar;櫲ƀ;svྍ⪜ྌĀ;d⪡⪢拼;拺cy;䑚΀AEadest⪷⪺⪾⫂⫅⫶⫹rò⥦;쀀≦̸rr;憚r;急Ȁ;fqs఻⫎⫣⫯tĀar⫔⫙rro÷⫁ightarro÷⪐ƀ;qs఻⪺⫪lanôౕĀ;sౕ⫴»శiíౝĀ;rవ⫾iĀ;eచథiäඐĀpt⬌⬑f;쀀𝕟膀¬;in⬙⬚⬶䂬nȀ;Edvஉ⬤⬨⬮;쀀⋹̸ot;쀀⋵̸ǡஉ⬳⬵;拷;拶iĀ;vಸ⬼ǡಸ⭁⭃;拾;拽ƀaor⭋⭣⭩rȀ;ast୻⭕⭚⭟lleì୻l;쀀⫽⃥;쀀∂̸lint;樔ƀ;ceಒ⭰⭳uåಥĀ;cಘ⭸Ā;eಒ⭽ñಘȀAait⮈⮋⮝⮧rò⦈rrƀ;cw⮔⮕⮙憛;쀀⤳̸;쀀↝̸ghtarrow»⮕riĀ;eೋೖ΀chimpqu⮽⯍⯙⬄୸⯤⯯Ȁ;cerല⯆ഷ⯉uå൅;쀀𝓃ortɭ⬅\0\0⯖ará⭖mĀ;e൮⯟Ā;q൴൳suĀbp⯫⯭å೸åഋƀbcp⯶ⰑⰙȀ;Ees⯿ⰀഢⰄ抄;쀀⫅̸etĀ;eഛⰋqĀ;qണⰀcĀ;eലⰗñസȀ;EesⰢⰣൟⰧ抅;쀀⫆̸etĀ;e൘ⰮqĀ;qൠⰣȀgilrⰽⰿⱅⱇìௗlde耻ñ䃱çృiangleĀlrⱒⱜeftĀ;eచⱚñదightĀ;eೋⱥñ೗Ā;mⱬⱭ䎽ƀ;esⱴⱵⱹ䀣ro;愖p;怇ҀDHadgilrsⲏⲔⲙⲞⲣⲰⲶⳓⳣash;抭arr;椄p;쀀≍⃒ash;抬ĀetⲨⲬ;쀀≥⃒;쀀>⃒nfin;槞ƀAetⲽⳁⳅrr;椂;쀀≤⃒Ā;rⳊⳍ쀀<⃒ie;쀀⊴⃒ĀAtⳘⳜrr;椃rie;쀀⊵⃒im;쀀∼⃒ƀAan⳰⳴ⴂrr;懖rĀhr⳺⳽k;椣Ā;oᏧᏥear;椧ቓ᪕\0\0\0\0\0\0\0\0\0\0\0\0\0ⴭ\0ⴸⵈⵠⵥ⵲ⶄᬇ\0\0ⶍⶫ\0ⷈⷎ\0ⷜ⸙⸫⸾⹃Ācsⴱ᪗ute耻ó䃳ĀiyⴼⵅrĀ;c᪞ⵂ耻ô䃴;䐾ʀabios᪠ⵒⵗǈⵚlac;䅑v;樸old;榼lig;䅓Ācr⵩⵭ir;榿;쀀𝔬ͯ⵹\0\0⵼\0ⶂn;䋛ave耻ò䃲;槁Ābmⶈ෴ar;榵Ȁacitⶕ⶘ⶥⶨrò᪀Āir⶝ⶠr;榾oss;榻nå๒;槀ƀaeiⶱⶵⶹcr;䅍ga;䏉ƀcdnⷀⷅǍron;䎿;榶pf;쀀𝕠ƀaelⷔ⷗ǒr;榷rp;榹΀;adiosvⷪⷫⷮ⸈⸍⸐⸖戨rò᪆Ȁ;efmⷷⷸ⸂⸅橝rĀ;oⷾⷿ愴f»ⷿ耻ª䂪耻º䂺gof;抶r;橖lope;橗;橛ƀclo⸟⸡⸧ò⸁ash耻ø䃸l;折iŬⸯ⸴de耻õ䃵esĀ;aǛ⸺s;樶ml耻ö䃶bar;挽ૡ⹞\0⹽\0⺀⺝\0⺢⺹\0\0⻋ຜ\0⼓\0\0⼫⾼\0⿈rȀ;astЃ⹧⹲຅脀¶;l⹭⹮䂶leìЃɩ⹸\0\0⹻m;櫳;櫽y;䐿rʀcimpt⺋⺏⺓ᡥ⺗nt;䀥od;䀮il;怰enk;怱r;쀀𝔭ƀimo⺨⺰⺴Ā;v⺭⺮䏆;䏕maô੶ne;明ƀ;tv⺿⻀⻈䏀chfork»´;䏖Āau⻏⻟nĀck⻕⻝kĀ;h⇴⻛;愎ö⇴sҀ;abcdemst⻳⻴ᤈ⻹⻽⼄⼆⼊⼎䀫cir;樣ir;樢Āouᵀ⼂;樥;橲n肻±ຝim;樦wo;樧ƀipu⼙⼠⼥ntint;樕f;쀀𝕡nd耻£䂣Ԁ;Eaceinosu່⼿⽁⽄⽇⾁⾉⾒⽾⾶;檳p;檷uå໙Ā;c໎⽌̀;acens່⽙⽟⽦⽨⽾pproø⽃urlyeñ໙ñ໎ƀaes⽯⽶⽺pprox;檹qq;檵im;拨iíໟmeĀ;s⾈ຮ怲ƀEas⽸⾐⽺ð⽵ƀdfp໬⾙⾯ƀals⾠⾥⾪lar;挮ine;挒urf;挓Ā;t໻⾴ï໻rel;抰Āci⿀⿅r;쀀𝓅;䏈ncsp;怈̀fiopsu⿚⋢⿟⿥⿫⿱r;쀀𝔮pf;쀀𝕢rime;恗cr;쀀𝓆ƀaeo⿸〉〓tĀei⿾々rnionóڰnt;樖stĀ;e【】䀿ñἙô༔઀ABHabcdefhilmnoprstux぀けさすムㄎㄫㅇㅢㅲㆎ㈆㈕㈤㈩㉘㉮㉲㊐㊰㊷ƀartぇおがròႳòϝail;検aròᱥar;楤΀cdenqrtとふへみわゔヌĀeuねぱ;쀀∽̱te;䅕iãᅮmptyv;榳gȀ;del࿑らるろ;榒;榥å࿑uo耻»䂻rր;abcfhlpstw࿜ガクシスゼゾダッデナp;極Ā;f࿠ゴs;椠;椳s;椞ë≝ð✮l;楅im;楴l;憣;憝Āaiパフil;椚oĀ;nホボ戶aló༞ƀabrョリヮrò៥rk;杳ĀakンヽcĀekヹ・;䁽;䁝Āes㄂㄄;榌lĀduㄊㄌ;榎;榐Ȁaeuyㄗㄜㄧㄩron;䅙Ādiㄡㄥil;䅗ì࿲âヺ;䑀Ȁclqsㄴㄷㄽㅄa;椷dhar;楩uoĀ;rȎȍh;憳ƀacgㅎㅟངlȀ;ipsླྀㅘㅛႜnåႻarôྩt;断ƀilrㅩဣㅮsht;楽;쀀𝔯ĀaoㅷㆆrĀduㅽㅿ»ѻĀ;l႑ㆄ;楬Ā;vㆋㆌ䏁;䏱ƀgns㆕ㇹㇼht̀ahlrstㆤㆰ㇂㇘㇤㇮rrowĀ;t࿜ㆭaéトarpoonĀduㆻㆿowîㅾp»႒eftĀah㇊㇐rrowó࿪arpoonóՑightarrows;應quigarro÷ニhreetimes;拌g;䋚ingdotseñἲƀahm㈍㈐㈓rò࿪aòՑ;怏oustĀ;a㈞㈟掱che»㈟mid;櫮Ȁabpt㈲㈽㉀㉒Ānr㈷㈺g;柭r;懾rëဃƀafl㉇㉊㉎r;榆;쀀𝕣us;樮imes;樵Āap㉝㉧rĀ;g㉣㉤䀩t;榔olint;樒arò㇣Ȁachq㉻㊀Ⴜ㊅quo;怺r;쀀𝓇Ābu・㊊oĀ;rȔȓƀhir㊗㊛㊠reåㇸmes;拊iȀ;efl㊪ၙᠡ㊫方tri;槎luhar;楨;愞ൡ㋕㋛㋟㌬㌸㍱\0㍺㎤\0\0㏬㏰\0㐨㑈㑚㒭㒱㓊㓱\0㘖\0\0㘳cute;䅛quï➺Ԁ;Eaceinpsyᇭ㋳㋵㋿㌂㌋㌏㌟㌦㌩;檴ǰ㋺\0㋼;檸on;䅡uåᇾĀ;dᇳ㌇il;䅟rc;䅝ƀEas㌖㌘㌛;檶p;檺im;择olint;樓iíሄ;䑁otƀ;be㌴ᵇ㌵担;橦΀Aacmstx㍆㍊㍗㍛㍞㍣㍭rr;懘rĀhr㍐㍒ë∨Ā;oਸ਼਴t耻§䂧i;䀻war;椩mĀin㍩ðnuóñt;朶rĀ;o㍶⁕쀀𝔰Ȁacoy㎂㎆㎑㎠rp;景Āhy㎋㎏cy;䑉;䑈rtɭ㎙\0\0㎜iäᑤaraì⹯耻­䂭Āgm㎨㎴maƀ;fv㎱㎲㎲䏃;䏂Ѐ;deglnprካ㏅㏉㏎㏖㏞㏡㏦ot;橪Ā;q኱ኰĀ;E㏓㏔檞;檠Ā;E㏛㏜檝;檟e;扆lus;樤arr;楲aròᄽȀaeit㏸㐈㐏㐗Āls㏽㐄lsetmé㍪hp;樳parsl;槤Ādlᑣ㐔e;挣Ā;e㐜㐝檪Ā;s㐢㐣檬;쀀⪬︀ƀflp㐮㐳㑂tcy;䑌Ā;b㐸㐹䀯Ā;a㐾㐿槄r;挿f;쀀𝕤aĀdr㑍ЂesĀ;u㑔㑕晠it»㑕ƀcsu㑠㑹㒟Āau㑥㑯pĀ;sᆈ㑫;쀀⊓︀pĀ;sᆴ㑵;쀀⊔︀uĀbp㑿㒏ƀ;esᆗᆜ㒆etĀ;eᆗ㒍ñᆝƀ;esᆨᆭ㒖etĀ;eᆨ㒝ñᆮƀ;afᅻ㒦ְrť㒫ֱ»ᅼaròᅈȀcemt㒹㒾㓂㓅r;쀀𝓈tmîñiì㐕aræᆾĀar㓎㓕rĀ;f㓔ឿ昆Āan㓚㓭ightĀep㓣㓪psiloîỠhé⺯s»⡒ʀbcmnp㓻㕞ሉ㖋㖎Ҁ;Edemnprs㔎㔏㔑㔕㔞㔣㔬㔱㔶抂;櫅ot;檽Ā;dᇚ㔚ot;櫃ult;櫁ĀEe㔨㔪;櫋;把lus;檿arr;楹ƀeiu㔽㕒㕕tƀ;en㔎㕅㕋qĀ;qᇚ㔏eqĀ;q㔫㔨m;櫇Ābp㕚㕜;櫕;櫓c̀;acensᇭ㕬㕲㕹㕻㌦pproø㋺urlyeñᇾñᇳƀaes㖂㖈㌛pproø㌚qñ㌗g;晪ڀ123;Edehlmnps㖩㖬㖯ሜ㖲㖴㗀㗉㗕㗚㗟㗨㗭耻¹䂹耻²䂲耻³䂳;櫆Āos㖹㖼t;檾ub;櫘Ā;dሢ㗅ot;櫄sĀou㗏㗒l;柉b;櫗arr;楻ult;櫂ĀEe㗤㗦;櫌;抋lus;櫀ƀeiu㗴㘉㘌tƀ;enሜ㗼㘂qĀ;qሢ㖲eqĀ;q㗧㗤m;櫈Ābp㘑㘓;櫔;櫖ƀAan㘜㘠㘭rr;懙rĀhr㘦㘨ë∮Ā;oਫ਩war;椪lig耻ß䃟௡㙑㙝㙠ዎ㙳㙹\0㙾㛂\0\0\0\0\0㛛㜃\0㜉㝬\0\0\0㞇ɲ㙖\0\0㙛get;挖;䏄rë๟ƀaey㙦㙫㙰ron;䅥dil;䅣;䑂lrec;挕r;쀀𝔱Ȁeiko㚆㚝㚵㚼ǲ㚋\0㚑eĀ4fኄኁaƀ;sv㚘㚙㚛䎸ym;䏑Ācn㚢㚲kĀas㚨㚮pproø዁im»ኬsðኞĀas㚺㚮ð዁rn耻þ䃾Ǭ̟㛆⋧es膀×;bd㛏㛐㛘䃗Ā;aᤏ㛕r;樱;樰ƀeps㛡㛣㜀á⩍Ȁ;bcf҆㛬㛰㛴ot;挶ir;櫱Ā;o㛹㛼쀀𝕥rk;櫚á㍢rime;怴ƀaip㜏㜒㝤dåቈ΀adempst㜡㝍㝀㝑㝗㝜㝟ngleʀ;dlqr㜰㜱㜶㝀㝂斵own»ᶻeftĀ;e⠀㜾ñम;扜ightĀ;e㊪㝋ñၚot;旬inus;樺lus;樹b;槍ime;樻ezium;揢ƀcht㝲㝽㞁Āry㝷㝻;쀀𝓉;䑆cy;䑛rok;䅧Āio㞋㞎xô᝷headĀlr㞗㞠eftarro÷ࡏightarrow»ཝऀAHabcdfghlmoprstuw㟐㟓㟗㟤㟰㟼㠎㠜㠣㠴㡑㡝㡫㢩㣌㣒㣪㣶ròϭar;楣Ācr㟜㟢ute耻ú䃺òᅐrǣ㟪\0㟭y;䑞ve;䅭Āiy㟵㟺rc耻û䃻;䑃ƀabh㠃㠆㠋ròᎭlac;䅱aòᏃĀir㠓㠘sht;楾;쀀𝔲rave耻ù䃹š㠧㠱rĀlr㠬㠮»ॗ»ႃlk;斀Āct㠹㡍ɯ㠿\0\0㡊rnĀ;e㡅㡆挜r»㡆op;挏ri;旸Āal㡖㡚cr;䅫肻¨͉Āgp㡢㡦on;䅳f;쀀𝕦̀adhlsuᅋ㡸㡽፲㢑㢠ownáᎳarpoonĀlr㢈㢌efô㠭ighô㠯iƀ;hl㢙㢚㢜䏅»ᏺon»㢚parrows;懈ƀcit㢰㣄㣈ɯ㢶\0\0㣁rnĀ;e㢼㢽挝r»㢽op;挎ng;䅯ri;旹cr;쀀𝓊ƀdir㣙㣝㣢ot;拰lde;䅩iĀ;f㜰㣨»᠓Āam㣯㣲rò㢨l耻ü䃼angle;榧ހABDacdeflnoprsz㤜㤟㤩㤭㦵㦸㦽㧟㧤㧨㧳㧹㧽㨁㨠ròϷarĀ;v㤦㤧櫨;櫩asèϡĀnr㤲㤷grt;榜΀eknprst㓣㥆㥋㥒㥝㥤㦖appá␕othinçẖƀhir㓫⻈㥙opô⾵Ā;hᎷ㥢ïㆍĀiu㥩㥭gmá㎳Ābp㥲㦄setneqĀ;q㥽㦀쀀⊊︀;쀀⫋︀setneqĀ;q㦏㦒쀀⊋︀;쀀⫌︀Āhr㦛㦟etá㚜iangleĀlr㦪㦯eft»थight»ၑy;䐲ash»ံƀelr㧄㧒㧗ƀ;beⷪ㧋㧏ar;抻q;扚lip;拮Ābt㧜ᑨaòᑩr;쀀𝔳tré㦮suĀbp㧯㧱»ജ»൙pf;쀀𝕧roð໻tré㦴Ācu㨆㨋r;쀀𝓋Ābp㨐㨘nĀEe㦀㨖»㥾nĀEe㦒㨞»㦐igzag;榚΀cefoprs㨶㨻㩖㩛㩔㩡㩪irc;䅵Ādi㩀㩑Ābg㩅㩉ar;機eĀ;qᗺ㩏;扙erp;愘r;쀀𝔴pf;쀀𝕨Ā;eᑹ㩦atèᑹcr;쀀𝓌ૣណ㪇\0㪋\0㪐㪛\0\0㪝㪨㪫㪯\0\0㫃㫎\0㫘ៜ៟tré៑r;쀀𝔵ĀAa㪔㪗ròσrò৶;䎾ĀAa㪡㪤ròθrò৫að✓is;拻ƀdptឤ㪵㪾Āfl㪺ឩ;쀀𝕩imåឲĀAa㫇㫊ròώròਁĀcq㫒ីr;쀀𝓍Āpt៖㫜ré។Ѐacefiosu㫰㫽㬈㬌㬑㬕㬛㬡cĀuy㫶㫻te耻ý䃽;䑏Āiy㬂㬆rc;䅷;䑋n耻¥䂥r;쀀𝔶cy;䑗pf;쀀𝕪cr;쀀𝓎Ācm㬦㬩y;䑎l耻ÿ䃿Ԁacdefhiosw㭂㭈㭔㭘㭤㭩㭭㭴㭺㮀cute;䅺Āay㭍㭒ron;䅾;䐷ot;䅼Āet㭝㭡træᕟa;䎶r;쀀𝔷cy;䐶grarr;懝pf;쀀𝕫cr;쀀𝓏Ājn㮅㮇;怍j;怌'.split("").map(function(t){return t.charCodeAt(0)}));var gu={};Object.defineProperty(gu,"__esModule",{value:!0});gu.default=new Uint16Array("Ȁaglq	\x1Bɭ\0\0p;䀦os;䀧t;䀾t;䀼uot;䀢".split("").map(function(t){return t.charCodeAt(0)}));var nu={};(function(t){var e;Object.defineProperty(t,"__esModule",{value:!0}),t.replaceCodePoint=t.fromCodePoint=void 0;var u=new Map([[0,65533],[128,8364],[130,8218],[131,402],[132,8222],[133,8230],[134,8224],[135,8225],[136,710],[137,8240],[138,352],[139,8249],[140,338],[142,381],[145,8216],[146,8217],[147,8220],[148,8221],[149,8226],[150,8211],[151,8212],[152,732],[153,8482],[154,353],[155,8250],[156,339],[158,382],[159,376]]);t.fromCodePoint=(e=String.fromCodePoint)!==null&&e!==void 0?e:function(a){var i="";return a>65535&&(a-=65536,i+=String.fromCharCode(a>>>10&1023|55296),a=56320|a&1023),i+=String.fromCharCode(a),i};function n(a){var i;return a>=55296&&a<=57343||a>1114111?65533:(i=u.get(a))!==null&&i!==void 0?i:a}t.replaceCodePoint=n;function r(a){return (0, t.fromCodePoint)(n(a))}t.default=r;})(nu);(function(t){var e=Xs&&Xs.__createBinding||(Object.create?function(b,x,A,k){k===void 0&&(k=A);var p=Object.getOwnPropertyDescriptor(x,A);(!p||("get"in p?!x.__esModule:p.writable||p.configurable))&&(p={enumerable:!0,get:function(){return x[A]}}),Object.defineProperty(b,k,p);}:function(b,x,A,k){k===void 0&&(k=A),b[k]=x[A];}),u=Xs&&Xs.__setModuleDefault||(Object.create?function(b,x){Object.defineProperty(b,"default",{enumerable:!0,value:x});}:function(b,x){b.default=x;}),n=Xs&&Xs.__importStar||function(b){if(b&&b.__esModule)return b;var x={};if(b!=null)for(var A in b)A!=="default"&&Object.prototype.hasOwnProperty.call(b,A)&&e(x,b,A);return u(x,b),x},r=Xs&&Xs.__importDefault||function(b){return b&&b.__esModule?b:{default:b}};Object.defineProperty(t,"__esModule",{value:!0}),t.decodeXML=t.decodeHTMLStrict=t.decodeHTMLAttribute=t.decodeHTML=t.determineBranch=t.EntityDecoder=t.DecodingMode=t.BinTrieFlags=t.fromCodePoint=t.replaceCodePoint=t.decodeCodePoint=t.xmlDecodeTree=t.htmlDecodeTree=void 0;var a=r(hu);t.htmlDecodeTree=a.default;var i=r(gu);t.xmlDecodeTree=i.default;var l=n(nu);t.decodeCodePoint=l.default;var c=nu;Object.defineProperty(t,"replaceCodePoint",{enumerable:!0,get:function(){return c.replaceCodePoint}}),Object.defineProperty(t,"fromCodePoint",{enumerable:!0,get:function(){return c.fromCodePoint}});var d;(function(b){b[b.NUM=35]="NUM",b[b.SEMI=59]="SEMI",b[b.EQUALS=61]="EQUALS",b[b.ZERO=48]="ZERO",b[b.NINE=57]="NINE",b[b.LOWER_A=97]="LOWER_A",b[b.LOWER_F=102]="LOWER_F",b[b.LOWER_X=120]="LOWER_X",b[b.LOWER_Z=122]="LOWER_Z",b[b.UPPER_A=65]="UPPER_A",b[b.UPPER_F=70]="UPPER_F",b[b.UPPER_Z=90]="UPPER_Z";})(d||(d={}));var f=32,h;(function(b){b[b.VALUE_LENGTH=49152]="VALUE_LENGTH",b[b.BRANCH_LENGTH=16256]="BRANCH_LENGTH",b[b.JUMP_TABLE=127]="JUMP_TABLE";})(h=t.BinTrieFlags||(t.BinTrieFlags={}));function s(b){return b>=d.ZERO&&b<=d.NINE}function o(b){return b>=d.UPPER_A&&b<=d.UPPER_F||b>=d.LOWER_A&&b<=d.LOWER_F}function D(b){return b>=d.UPPER_A&&b<=d.UPPER_Z||b>=d.LOWER_A&&b<=d.LOWER_Z||s(b)}function E(b){return b===d.EQUALS||D(b)}var y;(function(b){b[b.EntityStart=0]="EntityStart",b[b.NumericStart=1]="NumericStart",b[b.NumericDecimal=2]="NumericDecimal",b[b.NumericHex=3]="NumericHex",b[b.NamedEntity=4]="NamedEntity";})(y||(y={}));var v;(function(b){b[b.Legacy=0]="Legacy",b[b.Strict=1]="Strict",b[b.Attribute=2]="Attribute";})(v=t.DecodingMode||(t.DecodingMode={}));var w=function(){function b(x,A,k){this.decodeTree=x,this.emitCodePoint=A,this.errors=k,this.state=y.EntityStart,this.consumed=1,this.result=0,this.treeIndex=0,this.excess=1,this.decodeMode=v.Strict;}return b.prototype.startEntity=function(x){this.decodeMode=x,this.state=y.EntityStart,this.result=0,this.treeIndex=0,this.excess=1,this.consumed=1;},b.prototype.write=function(x,A){switch(this.state){case y.EntityStart:return x.charCodeAt(A)===d.NUM?(this.state=y.NumericStart,this.consumed+=1,this.stateNumericStart(x,A+1)):(this.state=y.NamedEntity,this.stateNamedEntity(x,A));case y.NumericStart:return this.stateNumericStart(x,A);case y.NumericDecimal:return this.stateNumericDecimal(x,A);case y.NumericHex:return this.stateNumericHex(x,A);case y.NamedEntity:return this.stateNamedEntity(x,A)}},b.prototype.stateNumericStart=function(x,A){return A>=x.length?-1:(x.charCodeAt(A)|f)===d.LOWER_X?(this.state=y.NumericHex,this.consumed+=1,this.stateNumericHex(x,A+1)):(this.state=y.NumericDecimal,this.stateNumericDecimal(x,A))},b.prototype.addToNumericResult=function(x,A,k,p){if(A!==k){var m=k-A;this.result=this.result*Math.pow(p,m)+parseInt(x.substr(A,m),p),this.consumed+=m;}},b.prototype.stateNumericHex=function(x,A){for(var k=A;A<x.length;){var p=x.charCodeAt(A);if(s(p)||o(p))A+=1;else return this.addToNumericResult(x,k,A,16),this.emitNumericEntity(p,3)}return this.addToNumericResult(x,k,A,16),-1},b.prototype.stateNumericDecimal=function(x,A){for(var k=A;A<x.length;){var p=x.charCodeAt(A);if(s(p))A+=1;else return this.addToNumericResult(x,k,A,10),this.emitNumericEntity(p,2)}return this.addToNumericResult(x,k,A,10),-1},b.prototype.emitNumericEntity=function(x,A){var k;if(this.consumed<=A)return (k=this.errors)===null||k===void 0||k.absenceOfDigitsInNumericCharacterReference(this.consumed),0;if(x===d.SEMI)this.consumed+=1;else if(this.decodeMode===v.Strict)return 0;return this.emitCodePoint((0, l.replaceCodePoint)(this.result),this.consumed),this.errors&&(x!==d.SEMI&&this.errors.missingSemicolonAfterCharacterReference(),this.errors.validateNumericCharacterReference(this.result)),this.consumed},b.prototype.stateNamedEntity=function(x,A){for(var k=this.decodeTree,p=k[this.treeIndex],m=(p&h.VALUE_LENGTH)>>14;A<x.length;A++,this.excess++){var g=x.charCodeAt(A);if(this.treeIndex=S(k,p,this.treeIndex+Math.max(1,m),g),this.treeIndex<0)return this.result===0||this.decodeMode===v.Attribute&&(m===0||E(g))?0:this.emitNotTerminatedNamedEntity();if(p=k[this.treeIndex],m=(p&h.VALUE_LENGTH)>>14,m!==0){if(g===d.SEMI)return this.emitNamedEntityData(this.treeIndex,m,this.consumed+this.excess);this.decodeMode!==v.Strict&&(this.result=this.treeIndex,this.consumed+=this.excess,this.excess=0);}}return -1},b.prototype.emitNotTerminatedNamedEntity=function(){var x,A=this,k=A.result,p=A.decodeTree,m=(p[k]&h.VALUE_LENGTH)>>14;return this.emitNamedEntityData(k,m,this.consumed),(x=this.errors)===null||x===void 0||x.missingSemicolonAfterCharacterReference(),this.consumed},b.prototype.emitNamedEntityData=function(x,A,k){var p=this.decodeTree;return this.emitCodePoint(A===1?p[x]&~h.VALUE_LENGTH:p[x+1],k),A===3&&this.emitCodePoint(p[x+2],k),k},b.prototype.end=function(){var x;switch(this.state){case y.NamedEntity:return this.result!==0&&(this.decodeMode!==v.Attribute||this.result===this.treeIndex)?this.emitNotTerminatedNamedEntity():0;case y.NumericDecimal:return this.emitNumericEntity(0,2);case y.NumericHex:return this.emitNumericEntity(0,3);case y.NumericStart:return (x=this.errors)===null||x===void 0||x.absenceOfDigitsInNumericCharacterReference(this.consumed),0;case y.EntityStart:return 0}},b}();t.EntityDecoder=w;function C(b){var x="",A=new w(b,function(k){return x+=(0, l.fromCodePoint)(k)});return function(p,m){for(var g=0,T=0;(T=p.indexOf("&",T))>=0;){x+=p.slice(g,T),A.startEntity(m);var H=A.write(p,T+1);if(H<0){g=T+A.end();break}g=T+H,T=H===0?g+1:g;}var U=x+p.slice(g);return x="",U}}function S(b,x,A,k){var p=(x&h.BRANCH_LENGTH)>>7,m=x&h.JUMP_TABLE;if(p===0)return m!==0&&k===m?A:-1;if(m){var g=k-m;return g<0||g>=p?-1:b[A+g]-1}for(var T=A,H=T+p-1;T<=H;){var U=T+H>>>1,M=b[U];if(M<k)T=U+1;else if(M>k)H=U-1;else return b[U+p]}return -1}t.determineBranch=S;var _=C(a.default),q=C(i.default);function j(b,x){return x===void 0&&(x=v.Legacy),_(b,x)}t.decodeHTML=j;function G(b){return _(b,v.Attribute)}t.decodeHTMLAttribute=G;function J(b){return _(b,v.Strict)}t.decodeHTMLStrict=J;function W(b){return q(b,v.Strict)}t.decodeXML=W;})(we$1);(function(t){Object.defineProperty(t,"__esModule",{value:!0}),t.QuoteType=void 0;var e=we$1,u;(function(s){s[s.Tab=9]="Tab",s[s.NewLine=10]="NewLine",s[s.FormFeed=12]="FormFeed",s[s.CarriageReturn=13]="CarriageReturn",s[s.Space=32]="Space",s[s.ExclamationMark=33]="ExclamationMark",s[s.Number=35]="Number",s[s.Amp=38]="Amp",s[s.SingleQuote=39]="SingleQuote",s[s.DoubleQuote=34]="DoubleQuote",s[s.Dash=45]="Dash",s[s.Slash=47]="Slash",s[s.Zero=48]="Zero",s[s.Nine=57]="Nine",s[s.Semi=59]="Semi",s[s.Lt=60]="Lt",s[s.Eq=61]="Eq",s[s.Gt=62]="Gt",s[s.Questionmark=63]="Questionmark",s[s.UpperA=65]="UpperA",s[s.LowerA=97]="LowerA",s[s.UpperF=70]="UpperF",s[s.LowerF=102]="LowerF",s[s.UpperZ=90]="UpperZ",s[s.LowerZ=122]="LowerZ",s[s.LowerX=120]="LowerX",s[s.OpeningSquareBracket=91]="OpeningSquareBracket";})(u||(u={}));var n;(function(s){s[s.Text=1]="Text",s[s.BeforeTagName=2]="BeforeTagName",s[s.InTagName=3]="InTagName",s[s.InSelfClosingTag=4]="InSelfClosingTag",s[s.BeforeClosingTagName=5]="BeforeClosingTagName",s[s.InClosingTagName=6]="InClosingTagName",s[s.AfterClosingTagName=7]="AfterClosingTagName",s[s.BeforeAttributeName=8]="BeforeAttributeName",s[s.InAttributeName=9]="InAttributeName",s[s.AfterAttributeName=10]="AfterAttributeName",s[s.BeforeAttributeValue=11]="BeforeAttributeValue",s[s.InAttributeValueDq=12]="InAttributeValueDq",s[s.InAttributeValueSq=13]="InAttributeValueSq",s[s.InAttributeValueNq=14]="InAttributeValueNq",s[s.BeforeDeclaration=15]="BeforeDeclaration",s[s.InDeclaration=16]="InDeclaration",s[s.InProcessingInstruction=17]="InProcessingInstruction",s[s.BeforeComment=18]="BeforeComment",s[s.CDATASequence=19]="CDATASequence",s[s.InSpecialComment=20]="InSpecialComment",s[s.InCommentLike=21]="InCommentLike",s[s.BeforeSpecialS=22]="BeforeSpecialS",s[s.SpecialStartSequence=23]="SpecialStartSequence",s[s.InSpecialTag=24]="InSpecialTag",s[s.BeforeEntity=25]="BeforeEntity",s[s.BeforeNumericEntity=26]="BeforeNumericEntity",s[s.InNamedEntity=27]="InNamedEntity",s[s.InNumericEntity=28]="InNumericEntity",s[s.InHexEntity=29]="InHexEntity";})(n||(n={}));function r(s){return s===u.Space||s===u.NewLine||s===u.Tab||s===u.FormFeed||s===u.CarriageReturn}function a(s){return s===u.Slash||s===u.Gt||r(s)}function i(s){return s>=u.Zero&&s<=u.Nine}function l(s){return s>=u.LowerA&&s<=u.LowerZ||s>=u.UpperA&&s<=u.UpperZ}function c(s){return s>=u.UpperA&&s<=u.UpperF||s>=u.LowerA&&s<=u.LowerF}var d;(function(s){s[s.NoValue=0]="NoValue",s[s.Unquoted=1]="Unquoted",s[s.Single=2]="Single",s[s.Double=3]="Double";})(d=t.QuoteType||(t.QuoteType={}));var f={Cdata:new Uint8Array([67,68,65,84,65,91]),CdataEnd:new Uint8Array([93,93,62]),CommentEnd:new Uint8Array([45,45,62]),ScriptEnd:new Uint8Array([60,47,115,99,114,105,112,116]),StyleEnd:new Uint8Array([60,47,115,116,121,108,101]),TitleEnd:new Uint8Array([60,47,116,105,116,108,101])},h=function(){function s(o,D){var E=o.xmlMode,y=E===void 0?!1:E,v=o.decodeEntities,w=v===void 0?!0:v;this.cbs=D,this.state=n.Text,this.buffer="",this.sectionStart=0,this.index=0,this.baseState=n.Text,this.isSpecial=!1,this.running=!0,this.offset=0,this.currentSequence=void 0,this.sequenceIndex=0,this.trieIndex=0,this.trieCurrent=0,this.entityResult=0,this.entityExcess=0,this.xmlMode=y,this.decodeEntities=w,this.entityTrie=y?e.xmlDecodeTree:e.htmlDecodeTree;}return s.prototype.reset=function(){this.state=n.Text,this.buffer="",this.sectionStart=0,this.index=0,this.baseState=n.Text,this.currentSequence=void 0,this.running=!0,this.offset=0;},s.prototype.write=function(o){this.offset+=this.buffer.length,this.buffer=o,this.parse();},s.prototype.end=function(){this.running&&this.finish();},s.prototype.pause=function(){this.running=!1;},s.prototype.resume=function(){this.running=!0,this.index<this.buffer.length+this.offset&&this.parse();},s.prototype.getIndex=function(){return this.index},s.prototype.getSectionStart=function(){return this.sectionStart},s.prototype.stateText=function(o){o===u.Lt||!this.decodeEntities&&this.fastForwardTo(u.Lt)?(this.index>this.sectionStart&&this.cbs.ontext(this.sectionStart,this.index),this.state=n.BeforeTagName,this.sectionStart=this.index):this.decodeEntities&&o===u.Amp&&(this.state=n.BeforeEntity);},s.prototype.stateSpecialStartSequence=function(o){var D=this.sequenceIndex===this.currentSequence.length,E=D?a(o):(o|32)===this.currentSequence[this.sequenceIndex];if(!E)this.isSpecial=!1;else if(!D){this.sequenceIndex++;return}this.sequenceIndex=0,this.state=n.InTagName,this.stateInTagName(o);},s.prototype.stateInSpecialTag=function(o){if(this.sequenceIndex===this.currentSequence.length){if(o===u.Gt||r(o)){var D=this.index-this.currentSequence.length;if(this.sectionStart<D){var E=this.index;this.index=D,this.cbs.ontext(this.sectionStart,D),this.index=E;}this.isSpecial=!1,this.sectionStart=D+2,this.stateInClosingTagName(o);return}this.sequenceIndex=0;}(o|32)===this.currentSequence[this.sequenceIndex]?this.sequenceIndex+=1:this.sequenceIndex===0?this.currentSequence===f.TitleEnd?this.decodeEntities&&o===u.Amp&&(this.state=n.BeforeEntity):this.fastForwardTo(u.Lt)&&(this.sequenceIndex=1):this.sequenceIndex=+(o===u.Lt);},s.prototype.stateCDATASequence=function(o){o===f.Cdata[this.sequenceIndex]?++this.sequenceIndex===f.Cdata.length&&(this.state=n.InCommentLike,this.currentSequence=f.CdataEnd,this.sequenceIndex=0,this.sectionStart=this.index+1):(this.sequenceIndex=0,this.state=n.InDeclaration,this.stateInDeclaration(o));},s.prototype.fastForwardTo=function(o){for(;++this.index<this.buffer.length+this.offset;)if(this.buffer.charCodeAt(this.index-this.offset)===o)return !0;return this.index=this.buffer.length+this.offset-1,!1},s.prototype.stateInCommentLike=function(o){o===this.currentSequence[this.sequenceIndex]?++this.sequenceIndex===this.currentSequence.length&&(this.currentSequence===f.CdataEnd?this.cbs.oncdata(this.sectionStart,this.index,2):this.cbs.oncomment(this.sectionStart,this.index,2),this.sequenceIndex=0,this.sectionStart=this.index+1,this.state=n.Text):this.sequenceIndex===0?this.fastForwardTo(this.currentSequence[0])&&(this.sequenceIndex=1):o!==this.currentSequence[this.sequenceIndex-1]&&(this.sequenceIndex=0);},s.prototype.isTagStartChar=function(o){return this.xmlMode?!a(o):l(o)},s.prototype.startSpecial=function(o,D){this.isSpecial=!0,this.currentSequence=o,this.sequenceIndex=D,this.state=n.SpecialStartSequence;},s.prototype.stateBeforeTagName=function(o){if(o===u.ExclamationMark)this.state=n.BeforeDeclaration,this.sectionStart=this.index+1;else if(o===u.Questionmark)this.state=n.InProcessingInstruction,this.sectionStart=this.index+1;else if(this.isTagStartChar(o)){var D=o|32;this.sectionStart=this.index,!this.xmlMode&&D===f.TitleEnd[2]?this.startSpecial(f.TitleEnd,3):this.state=!this.xmlMode&&D===f.ScriptEnd[2]?n.BeforeSpecialS:n.InTagName;}else o===u.Slash?this.state=n.BeforeClosingTagName:(this.state=n.Text,this.stateText(o));},s.prototype.stateInTagName=function(o){a(o)&&(this.cbs.onopentagname(this.sectionStart,this.index),this.sectionStart=-1,this.state=n.BeforeAttributeName,this.stateBeforeAttributeName(o));},s.prototype.stateBeforeClosingTagName=function(o){r(o)||(o===u.Gt?this.state=n.Text:(this.state=this.isTagStartChar(o)?n.InClosingTagName:n.InSpecialComment,this.sectionStart=this.index));},s.prototype.stateInClosingTagName=function(o){(o===u.Gt||r(o))&&(this.cbs.onclosetag(this.sectionStart,this.index),this.sectionStart=-1,this.state=n.AfterClosingTagName,this.stateAfterClosingTagName(o));},s.prototype.stateAfterClosingTagName=function(o){(o===u.Gt||this.fastForwardTo(u.Gt))&&(this.state=n.Text,this.baseState=n.Text,this.sectionStart=this.index+1);},s.prototype.stateBeforeAttributeName=function(o){o===u.Gt?(this.cbs.onopentagend(this.index),this.isSpecial?(this.state=n.InSpecialTag,this.sequenceIndex=0):this.state=n.Text,this.baseState=this.state,this.sectionStart=this.index+1):o===u.Slash?this.state=n.InSelfClosingTag:r(o)||(this.state=n.InAttributeName,this.sectionStart=this.index);},s.prototype.stateInSelfClosingTag=function(o){o===u.Gt?(this.cbs.onselfclosingtag(this.index),this.state=n.Text,this.baseState=n.Text,this.sectionStart=this.index+1,this.isSpecial=!1):r(o)||(this.state=n.BeforeAttributeName,this.stateBeforeAttributeName(o));},s.prototype.stateInAttributeName=function(o){(o===u.Eq||a(o))&&(this.cbs.onattribname(this.sectionStart,this.index),this.sectionStart=-1,this.state=n.AfterAttributeName,this.stateAfterAttributeName(o));},s.prototype.stateAfterAttributeName=function(o){o===u.Eq?this.state=n.BeforeAttributeValue:o===u.Slash||o===u.Gt?(this.cbs.onattribend(d.NoValue,this.index),this.state=n.BeforeAttributeName,this.stateBeforeAttributeName(o)):r(o)||(this.cbs.onattribend(d.NoValue,this.index),this.state=n.InAttributeName,this.sectionStart=this.index);},s.prototype.stateBeforeAttributeValue=function(o){o===u.DoubleQuote?(this.state=n.InAttributeValueDq,this.sectionStart=this.index+1):o===u.SingleQuote?(this.state=n.InAttributeValueSq,this.sectionStart=this.index+1):r(o)||(this.sectionStart=this.index,this.state=n.InAttributeValueNq,this.stateInAttributeValueNoQuotes(o));},s.prototype.handleInAttributeValue=function(o,D){o===D||!this.decodeEntities&&this.fastForwardTo(D)?(this.cbs.onattribdata(this.sectionStart,this.index),this.sectionStart=-1,this.cbs.onattribend(D===u.DoubleQuote?d.Double:d.Single,this.index),this.state=n.BeforeAttributeName):this.decodeEntities&&o===u.Amp&&(this.baseState=this.state,this.state=n.BeforeEntity);},s.prototype.stateInAttributeValueDoubleQuotes=function(o){this.handleInAttributeValue(o,u.DoubleQuote);},s.prototype.stateInAttributeValueSingleQuotes=function(o){this.handleInAttributeValue(o,u.SingleQuote);},s.prototype.stateInAttributeValueNoQuotes=function(o){r(o)||o===u.Gt?(this.cbs.onattribdata(this.sectionStart,this.index),this.sectionStart=-1,this.cbs.onattribend(d.Unquoted,this.index),this.state=n.BeforeAttributeName,this.stateBeforeAttributeName(o)):this.decodeEntities&&o===u.Amp&&(this.baseState=this.state,this.state=n.BeforeEntity);},s.prototype.stateBeforeDeclaration=function(o){o===u.OpeningSquareBracket?(this.state=n.CDATASequence,this.sequenceIndex=0):this.state=o===u.Dash?n.BeforeComment:n.InDeclaration;},s.prototype.stateInDeclaration=function(o){(o===u.Gt||this.fastForwardTo(u.Gt))&&(this.cbs.ondeclaration(this.sectionStart,this.index),this.state=n.Text,this.sectionStart=this.index+1);},s.prototype.stateInProcessingInstruction=function(o){(o===u.Gt||this.fastForwardTo(u.Gt))&&(this.cbs.onprocessinginstruction(this.sectionStart,this.index),this.state=n.Text,this.sectionStart=this.index+1);},s.prototype.stateBeforeComment=function(o){o===u.Dash?(this.state=n.InCommentLike,this.currentSequence=f.CommentEnd,this.sequenceIndex=2,this.sectionStart=this.index+1):this.state=n.InDeclaration;},s.prototype.stateInSpecialComment=function(o){(o===u.Gt||this.fastForwardTo(u.Gt))&&(this.cbs.oncomment(this.sectionStart,this.index,0),this.state=n.Text,this.sectionStart=this.index+1);},s.prototype.stateBeforeSpecialS=function(o){var D=o|32;D===f.ScriptEnd[3]?this.startSpecial(f.ScriptEnd,4):D===f.StyleEnd[3]?this.startSpecial(f.StyleEnd,4):(this.state=n.InTagName,this.stateInTagName(o));},s.prototype.stateBeforeEntity=function(o){this.entityExcess=1,this.entityResult=0,o===u.Number?this.state=n.BeforeNumericEntity:o===u.Amp||(this.trieIndex=0,this.trieCurrent=this.entityTrie[0],this.state=n.InNamedEntity,this.stateInNamedEntity(o));},s.prototype.stateInNamedEntity=function(o){if(this.entityExcess+=1,this.trieIndex=(0, e.determineBranch)(this.entityTrie,this.trieCurrent,this.trieIndex+1,o),this.trieIndex<0){this.emitNamedEntity(),this.index--;return}this.trieCurrent=this.entityTrie[this.trieIndex];var D=this.trieCurrent&e.BinTrieFlags.VALUE_LENGTH;if(D){var E=(D>>14)-1;if(!this.allowLegacyEntity()&&o!==u.Semi)this.trieIndex+=E;else {var y=this.index-this.entityExcess+1;y>this.sectionStart&&this.emitPartial(this.sectionStart,y),this.entityResult=this.trieIndex,this.trieIndex+=E,this.entityExcess=0,this.sectionStart=this.index+1,E===0&&this.emitNamedEntity();}}},s.prototype.emitNamedEntity=function(){if(this.state=this.baseState,this.entityResult!==0){var o=(this.entityTrie[this.entityResult]&e.BinTrieFlags.VALUE_LENGTH)>>14;switch(o){case 1:{this.emitCodePoint(this.entityTrie[this.entityResult]&~e.BinTrieFlags.VALUE_LENGTH);break}case 2:{this.emitCodePoint(this.entityTrie[this.entityResult+1]);break}case 3:this.emitCodePoint(this.entityTrie[this.entityResult+1]),this.emitCodePoint(this.entityTrie[this.entityResult+2]);}}},s.prototype.stateBeforeNumericEntity=function(o){(o|32)===u.LowerX?(this.entityExcess++,this.state=n.InHexEntity):(this.state=n.InNumericEntity,this.stateInNumericEntity(o));},s.prototype.emitNumericEntity=function(o){var D=this.index-this.entityExcess-1,E=D+2+ +(this.state===n.InHexEntity);E!==this.index&&(D>this.sectionStart&&this.emitPartial(this.sectionStart,D),this.sectionStart=this.index+Number(o),this.emitCodePoint((0, e.replaceCodePoint)(this.entityResult))),this.state=this.baseState;},s.prototype.stateInNumericEntity=function(o){o===u.Semi?this.emitNumericEntity(!0):i(o)?(this.entityResult=this.entityResult*10+(o-u.Zero),this.entityExcess++):(this.allowLegacyEntity()?this.emitNumericEntity(!1):this.state=this.baseState,this.index--);},s.prototype.stateInHexEntity=function(o){o===u.Semi?this.emitNumericEntity(!0):i(o)?(this.entityResult=this.entityResult*16+(o-u.Zero),this.entityExcess++):c(o)?(this.entityResult=this.entityResult*16+((o|32)-u.LowerA+10),this.entityExcess++):(this.allowLegacyEntity()?this.emitNumericEntity(!1):this.state=this.baseState,this.index--);},s.prototype.allowLegacyEntity=function(){return !this.xmlMode&&(this.baseState===n.Text||this.baseState===n.InSpecialTag)},s.prototype.cleanup=function(){this.running&&this.sectionStart!==this.index&&(this.state===n.Text||this.state===n.InSpecialTag&&this.sequenceIndex===0?(this.cbs.ontext(this.sectionStart,this.index),this.sectionStart=this.index):(this.state===n.InAttributeValueDq||this.state===n.InAttributeValueSq||this.state===n.InAttributeValueNq)&&(this.cbs.onattribdata(this.sectionStart,this.index),this.sectionStart=this.index));},s.prototype.shouldContinue=function(){return this.index<this.buffer.length+this.offset&&this.running},s.prototype.parse=function(){for(;this.shouldContinue();){var o=this.buffer.charCodeAt(this.index-this.offset);switch(this.state){case n.Text:{this.stateText(o);break}case n.SpecialStartSequence:{this.stateSpecialStartSequence(o);break}case n.InSpecialTag:{this.stateInSpecialTag(o);break}case n.CDATASequence:{this.stateCDATASequence(o);break}case n.InAttributeValueDq:{this.stateInAttributeValueDoubleQuotes(o);break}case n.InAttributeName:{this.stateInAttributeName(o);break}case n.InCommentLike:{this.stateInCommentLike(o);break}case n.InSpecialComment:{this.stateInSpecialComment(o);break}case n.BeforeAttributeName:{this.stateBeforeAttributeName(o);break}case n.InTagName:{this.stateInTagName(o);break}case n.InClosingTagName:{this.stateInClosingTagName(o);break}case n.BeforeTagName:{this.stateBeforeTagName(o);break}case n.AfterAttributeName:{this.stateAfterAttributeName(o);break}case n.InAttributeValueSq:{this.stateInAttributeValueSingleQuotes(o);break}case n.BeforeAttributeValue:{this.stateBeforeAttributeValue(o);break}case n.BeforeClosingTagName:{this.stateBeforeClosingTagName(o);break}case n.AfterClosingTagName:{this.stateAfterClosingTagName(o);break}case n.BeforeSpecialS:{this.stateBeforeSpecialS(o);break}case n.InAttributeValueNq:{this.stateInAttributeValueNoQuotes(o);break}case n.InSelfClosingTag:{this.stateInSelfClosingTag(o);break}case n.InDeclaration:{this.stateInDeclaration(o);break}case n.BeforeDeclaration:{this.stateBeforeDeclaration(o);break}case n.BeforeComment:{this.stateBeforeComment(o);break}case n.InProcessingInstruction:{this.stateInProcessingInstruction(o);break}case n.InNamedEntity:{this.stateInNamedEntity(o);break}case n.BeforeEntity:{this.stateBeforeEntity(o);break}case n.InHexEntity:{this.stateInHexEntity(o);break}case n.InNumericEntity:{this.stateInNumericEntity(o);break}default:this.stateBeforeNumericEntity(o);}this.index++;}this.cleanup();},s.prototype.finish=function(){this.state===n.InNamedEntity&&this.emitNamedEntity(),this.sectionStart<this.index&&this.handleTrailingData(),this.cbs.onend();},s.prototype.handleTrailingData=function(){var o=this.buffer.length+this.offset;this.state===n.InCommentLike?this.currentSequence===f.CdataEnd?this.cbs.oncdata(this.sectionStart,o,0):this.cbs.oncomment(this.sectionStart,o,0):this.state===n.InNumericEntity&&this.allowLegacyEntity()?this.emitNumericEntity(!1):this.state===n.InHexEntity&&this.allowLegacyEntity()?this.emitNumericEntity(!1):this.state===n.InTagName||this.state===n.BeforeAttributeName||this.state===n.BeforeAttributeValue||this.state===n.AfterAttributeName||this.state===n.InAttributeName||this.state===n.InAttributeValueSq||this.state===n.InAttributeValueDq||this.state===n.InAttributeValueNq||this.state===n.InClosingTagName||this.cbs.ontext(this.sectionStart,o);},s.prototype.emitPartial=function(o,D){this.baseState!==n.Text&&this.baseState!==n.InSpecialTag?this.cbs.onattribdata(o,D):this.cbs.ontext(o,D);},s.prototype.emitCodePoint=function(o){this.baseState!==n.Text&&this.baseState!==n.InSpecialTag?this.cbs.onattribentity(o):this.cbs.ontextentity(o);},s}();t.default=h;})(bu);var Zn=Xs&&Xs.__createBinding||(Object.create?function(t,e,u,n){n===void 0&&(n=u);var r=Object.getOwnPropertyDescriptor(e,u);(!r||("get"in r?!e.__esModule:r.writable||r.configurable))&&(r={enumerable:!0,get:function(){return e[u]}}),Object.defineProperty(t,n,r);}:function(t,e,u,n){n===void 0&&(n=u),t[n]=e[u];}),Xn=Xs&&Xs.__setModuleDefault||(Object.create?function(t,e){Object.defineProperty(t,"default",{enumerable:!0,value:e});}:function(t,e){t.default=e;}),Wn=Xs&&Xs.__importStar||function(t){if(t&&t.__esModule)return t;var e={};if(t!=null)for(var u in t)u!=="default"&&Object.prototype.hasOwnProperty.call(t,u)&&Zn(e,t,u);return Xn(e,t),e};Object.defineProperty(ve,"__esModule",{value:!0});ve.Parser=void 0;var Be=Wn(bu),Ou=we$1,he$1=new Set(["input","option","optgroup","select","button","datalist","textarea"]),L=new Set(["p"]),Lu=new Set(["thead","tbody"]),Ru=new Set(["dd","dt"]),Pu=new Set(["rt","rp"]),Qn=new Map([["tr",new Set(["tr","th","td"])],["th",new Set(["th"])],["td",new Set(["thead","th","td"])],["body",new Set(["head","link","script"])],["li",new Set(["li"])],["p",L],["h1",L],["h2",L],["h3",L],["h4",L],["h5",L],["h6",L],["select",he$1],["input",he$1],["output",he$1],["button",he$1],["datalist",he$1],["textarea",he$1],["option",new Set(["option"])],["optgroup",new Set(["optgroup","option"])],["dd",Ru],["dt",Ru],["address",L],["article",L],["aside",L],["blockquote",L],["details",L],["div",L],["dl",L],["fieldset",L],["figcaption",L],["figure",L],["footer",L],["form",L],["header",L],["hr",L],["main",L],["nav",L],["ol",L],["pre",L],["section",L],["table",L],["ul",L],["rt",Pu],["rp",Pu],["tbody",Lu],["tfoot",Lu]]),Kn=new Set(["area","base","basefont","br","col","command","embed","frame","hr","img","input","isindex","keygen","link","meta","param","source","track","wbr"]),Mu=new Set(["math","svg"]),qu=new Set(["mi","mo","mn","ms","mtext","annotation-xml","foreignobject","desc","title"]),Yn=/\s|\//,Jn=function(){function t(e,u){u===void 0&&(u={});var n,r,a,i,l;this.options=u,this.startIndex=0,this.endIndex=0,this.openTagStart=0,this.tagname="",this.attribname="",this.attribvalue="",this.attribs=null,this.stack=[],this.foreignContext=[],this.buffers=[],this.bufferOffset=0,this.writeIndex=0,this.ended=!1,this.cbs=e??{},this.lowerCaseTagNames=(n=u.lowerCaseTags)!==null&&n!==void 0?n:!u.xmlMode,this.lowerCaseAttributeNames=(r=u.lowerCaseAttributeNames)!==null&&r!==void 0?r:!u.xmlMode,this.tokenizer=new((a=u.Tokenizer)!==null&&a!==void 0?a:Be.default)(this.options,this),(l=(i=this.cbs).onparserinit)===null||l===void 0||l.call(i,this);}return t.prototype.ontext=function(e,u){var n,r,a=this.getSlice(e,u);this.endIndex=u-1,(r=(n=this.cbs).ontext)===null||r===void 0||r.call(n,a),this.startIndex=u;},t.prototype.ontextentity=function(e){var u,n,r=this.tokenizer.getSectionStart();this.endIndex=r-1,(n=(u=this.cbs).ontext)===null||n===void 0||n.call(u,(0, Ou.fromCodePoint)(e)),this.startIndex=r;},t.prototype.isVoidElement=function(e){return !this.options.xmlMode&&Kn.has(e)},t.prototype.onopentagname=function(e,u){this.endIndex=u;var n=this.getSlice(e,u);this.lowerCaseTagNames&&(n=n.toLowerCase()),this.emitOpenTag(n);},t.prototype.emitOpenTag=function(e){var u,n,r,a;this.openTagStart=this.startIndex,this.tagname=e;var i=!this.options.xmlMode&&Qn.get(e);if(i)for(;this.stack.length>0&&i.has(this.stack[this.stack.length-1]);){var l=this.stack.pop();(n=(u=this.cbs).onclosetag)===null||n===void 0||n.call(u,l,!0);}this.isVoidElement(e)||(this.stack.push(e),Mu.has(e)?this.foreignContext.push(!0):qu.has(e)&&this.foreignContext.push(!1)),(a=(r=this.cbs).onopentagname)===null||a===void 0||a.call(r,e),this.cbs.onopentag&&(this.attribs={});},t.prototype.endOpenTag=function(e){var u,n;this.startIndex=this.openTagStart,this.attribs&&((n=(u=this.cbs).onopentag)===null||n===void 0||n.call(u,this.tagname,this.attribs,e),this.attribs=null),this.cbs.onclosetag&&this.isVoidElement(this.tagname)&&this.cbs.onclosetag(this.tagname,!0),this.tagname="";},t.prototype.onopentagend=function(e){this.endIndex=e,this.endOpenTag(!1),this.startIndex=e+1;},t.prototype.onclosetag=function(e,u){var n,r,a,i,l,c;this.endIndex=u;var d=this.getSlice(e,u);if(this.lowerCaseTagNames&&(d=d.toLowerCase()),(Mu.has(d)||qu.has(d))&&this.foreignContext.pop(),this.isVoidElement(d))!this.options.xmlMode&&d==="br"&&((r=(n=this.cbs).onopentagname)===null||r===void 0||r.call(n,"br"),(i=(a=this.cbs).onopentag)===null||i===void 0||i.call(a,"br",{},!0),(c=(l=this.cbs).onclosetag)===null||c===void 0||c.call(l,"br",!1));else {var f=this.stack.lastIndexOf(d);if(f!==-1)if(this.cbs.onclosetag)for(var h=this.stack.length-f;h--;)this.cbs.onclosetag(this.stack.pop(),h!==0);else this.stack.length=f;else !this.options.xmlMode&&d==="p"&&(this.emitOpenTag("p"),this.closeCurrentTag(!0));}this.startIndex=u+1;},t.prototype.onselfclosingtag=function(e){this.endIndex=e,this.options.xmlMode||this.options.recognizeSelfClosing||this.foreignContext[this.foreignContext.length-1]?(this.closeCurrentTag(!1),this.startIndex=e+1):this.onopentagend(e);},t.prototype.closeCurrentTag=function(e){var u,n,r=this.tagname;this.endOpenTag(e),this.stack[this.stack.length-1]===r&&((n=(u=this.cbs).onclosetag)===null||n===void 0||n.call(u,r,!e),this.stack.pop());},t.prototype.onattribname=function(e,u){this.startIndex=e;var n=this.getSlice(e,u);this.attribname=this.lowerCaseAttributeNames?n.toLowerCase():n;},t.prototype.onattribdata=function(e,u){this.attribvalue+=this.getSlice(e,u);},t.prototype.onattribentity=function(e){this.attribvalue+=(0, Ou.fromCodePoint)(e);},t.prototype.onattribend=function(e,u){var n,r;this.endIndex=u,(r=(n=this.cbs).onattribute)===null||r===void 0||r.call(n,this.attribname,this.attribvalue,e===Be.QuoteType.Double?'"':e===Be.QuoteType.Single?"'":e===Be.QuoteType.NoValue?void 0:null),this.attribs&&!Object.prototype.hasOwnProperty.call(this.attribs,this.attribname)&&(this.attribs[this.attribname]=this.attribvalue),this.attribvalue="";},t.prototype.getInstructionName=function(e){var u=e.search(Yn),n=u<0?e:e.substr(0,u);return this.lowerCaseTagNames&&(n=n.toLowerCase()),n},t.prototype.ondeclaration=function(e,u){this.endIndex=u;var n=this.getSlice(e,u);if(this.cbs.onprocessinginstruction){var r=this.getInstructionName(n);this.cbs.onprocessinginstruction("!".concat(r),"!".concat(n));}this.startIndex=u+1;},t.prototype.onprocessinginstruction=function(e,u){this.endIndex=u;var n=this.getSlice(e,u);if(this.cbs.onprocessinginstruction){var r=this.getInstructionName(n);this.cbs.onprocessinginstruction("?".concat(r),"?".concat(n));}this.startIndex=u+1;},t.prototype.oncomment=function(e,u,n){var r,a,i,l;this.endIndex=u,(a=(r=this.cbs).oncomment)===null||a===void 0||a.call(r,this.getSlice(e,u-n)),(l=(i=this.cbs).oncommentend)===null||l===void 0||l.call(i),this.startIndex=u+1;},t.prototype.oncdata=function(e,u,n){var r,a,i,l,c,d,f,h,s,o;this.endIndex=u;var D=this.getSlice(e,u-n);this.options.xmlMode||this.options.recognizeCDATA?((a=(r=this.cbs).oncdatastart)===null||a===void 0||a.call(r),(l=(i=this.cbs).ontext)===null||l===void 0||l.call(i,D),(d=(c=this.cbs).oncdataend)===null||d===void 0||d.call(c)):((h=(f=this.cbs).oncomment)===null||h===void 0||h.call(f,"[CDATA[".concat(D,"]]")),(o=(s=this.cbs).oncommentend)===null||o===void 0||o.call(s)),this.startIndex=u+1;},t.prototype.onend=function(){var e,u;if(this.cbs.onclosetag){this.endIndex=this.startIndex;for(var n=this.stack.length;n>0;this.cbs.onclosetag(this.stack[--n],!0));}(u=(e=this.cbs).onend)===null||u===void 0||u.call(e);},t.prototype.reset=function(){var e,u,n,r;(u=(e=this.cbs).onreset)===null||u===void 0||u.call(e),this.tokenizer.reset(),this.tagname="",this.attribname="",this.attribs=null,this.stack.length=0,this.startIndex=0,this.endIndex=0,(r=(n=this.cbs).onparserinit)===null||r===void 0||r.call(n,this),this.buffers.length=0,this.bufferOffset=0,this.writeIndex=0,this.ended=!1;},t.prototype.parseComplete=function(e){this.reset(),this.end(e);},t.prototype.getSlice=function(e,u){for(;e-this.bufferOffset>=this.buffers[0].length;)this.shiftBuffer();for(var n=this.buffers[0].slice(e-this.bufferOffset,u-this.bufferOffset);u-this.bufferOffset>this.buffers[0].length;)this.shiftBuffer(),n+=this.buffers[0].slice(0,u-this.bufferOffset);return n},t.prototype.shiftBuffer=function(){this.bufferOffset+=this.buffers[0].length,this.writeIndex--,this.buffers.shift();},t.prototype.write=function(e){var u,n;if(this.ended){(n=(u=this.cbs).onerror)===null||n===void 0||n.call(u,new Error(".write() after done!"));return}this.buffers.push(e),this.tokenizer.running&&(this.tokenizer.write(e),this.writeIndex++);},t.prototype.end=function(e){var u,n;if(this.ended){(n=(u=this.cbs).onerror)===null||n===void 0||n.call(u,new Error(".end() after done!"));return}e&&this.write(e),this.ended=!0,this.tokenizer.end();},t.prototype.pause=function(){this.tokenizer.pause();},t.prototype.resume=function(){for(this.tokenizer.resume();this.tokenizer.running&&this.writeIndex<this.buffers.length;)this.tokenizer.write(this.buffers[this.writeIndex++]);this.ended&&this.tokenizer.end();},t.prototype.parseChunk=function(e){this.write(e);},t.prototype.done=function(e){this.end(e);},t}();ve.Parser=Jn;var se={},De={};(function(t){Object.defineProperty(t,"__esModule",{value:!0}),t.Doctype=t.CDATA=t.Tag=t.Style=t.Script=t.Comment=t.Directive=t.Text=t.Root=t.isTag=t.ElementType=void 0;var e;(function(n){n.Root="root",n.Text="text",n.Directive="directive",n.Comment="comment",n.Script="script",n.Style="style",n.Tag="tag",n.CDATA="cdata",n.Doctype="doctype";})(e=t.ElementType||(t.ElementType={}));function u(n){return n.type===e.Tag||n.type===e.Script||n.type===e.Style}t.isTag=u,t.Root=e.Root,t.Text=e.Text,t.Directive=e.Directive,t.Comment=e.Comment,t.Script=e.Script,t.Style=e.Style,t.Tag=e.Tag,t.CDATA=e.CDATA,t.Doctype=e.Doctype;})(De);var I={},ce$1=Xs&&Xs.__extends||function(){var t=function(e,u){return t=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(n,r){n.__proto__=r;}||function(n,r){for(var a in r)Object.prototype.hasOwnProperty.call(r,a)&&(n[a]=r[a]);},t(e,u)};return function(e,u){if(typeof u!="function"&&u!==null)throw new TypeError("Class extends value "+String(u)+" is not a constructor or null");t(e,u);function n(){this.constructor=e;}e.prototype=u===null?Object.create(u):(n.prototype=u.prototype,new n);}}(),ye$1=Xs&&Xs.__assign||function(){return ye$1=Object.assign||function(t){for(var e,u=1,n=arguments.length;u<n;u++){e=arguments[u];for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&(t[r]=e[r]);}return t},ye$1.apply(this,arguments)};Object.defineProperty(I,"__esModule",{value:!0});I.cloneNode=I.hasChildren=I.isDocument=I.isDirective=I.isComment=I.isText=I.isCDATA=I.isTag=I.Element=I.Document=I.CDATA=I.NodeWithChildren=I.ProcessingInstruction=I.Comment=I.Text=I.DataNode=I.Node=void 0;var X=De,mu=function(){function t(){this.parent=null,this.prev=null,this.next=null,this.startIndex=null,this.endIndex=null;}return Object.defineProperty(t.prototype,"parentNode",{get:function(){return this.parent},set:function(e){this.parent=e;},enumerable:!1,configurable:!0}),Object.defineProperty(t.prototype,"previousSibling",{get:function(){return this.prev},set:function(e){this.prev=e;},enumerable:!1,configurable:!0}),Object.defineProperty(t.prototype,"nextSibling",{get:function(){return this.next},set:function(e){this.next=e;},enumerable:!1,configurable:!0}),t.prototype.cloneNode=function(e){return e===void 0&&(e=!1),Du(this,e)},t}();I.Node=mu;var Ve$1=function(t){ce$1(e,t);function e(u){var n=t.call(this)||this;return n.data=u,n}return Object.defineProperty(e.prototype,"nodeValue",{get:function(){return this.data},set:function(u){this.data=u;},enumerable:!1,configurable:!0}),e}(mu);I.DataNode=Ve$1;var ft$1=function(t){ce$1(e,t);function e(){var u=t!==null&&t.apply(this,arguments)||this;return u.type=X.ElementType.Text,u}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 3},enumerable:!1,configurable:!0}),e}(Ve$1);I.Text=ft$1;var pt$1=function(t){ce$1(e,t);function e(){var u=t!==null&&t.apply(this,arguments)||this;return u.type=X.ElementType.Comment,u}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 8},enumerable:!1,configurable:!0}),e}(Ve$1);I.Comment=pt$1;var bt=function(t){ce$1(e,t);function e(u,n){var r=t.call(this,n)||this;return r.name=u,r.type=X.ElementType.Directive,r}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 1},enumerable:!1,configurable:!0}),e}(Ve$1);I.ProcessingInstruction=bt;var Ze$1=function(t){ce$1(e,t);function e(u){var n=t.call(this)||this;return n.children=u,n}return Object.defineProperty(e.prototype,"firstChild",{get:function(){var u;return (u=this.children[0])!==null&&u!==void 0?u:null},enumerable:!1,configurable:!0}),Object.defineProperty(e.prototype,"lastChild",{get:function(){return this.children.length>0?this.children[this.children.length-1]:null},enumerable:!1,configurable:!0}),Object.defineProperty(e.prototype,"childNodes",{get:function(){return this.children},set:function(u){this.children=u;},enumerable:!1,configurable:!0}),e}(mu);I.NodeWithChildren=Ze$1;var ht$1=function(t){ce$1(e,t);function e(){var u=t!==null&&t.apply(this,arguments)||this;return u.type=X.ElementType.CDATA,u}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 4},enumerable:!1,configurable:!0}),e}(Ze$1);I.CDATA=ht$1;var gt$1=function(t){ce$1(e,t);function e(){var u=t!==null&&t.apply(this,arguments)||this;return u.type=X.ElementType.Root,u}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 9},enumerable:!1,configurable:!0}),e}(Ze$1);I.Document=gt$1;var mt$1=function(t){ce$1(e,t);function e(u,n,r,a){r===void 0&&(r=[]),a===void 0&&(a=u==="script"?X.ElementType.Script:u==="style"?X.ElementType.Style:X.ElementType.Tag);var i=t.call(this,r)||this;return i.name=u,i.attribs=n,i.type=a,i}return Object.defineProperty(e.prototype,"nodeType",{get:function(){return 1},enumerable:!1,configurable:!0}),Object.defineProperty(e.prototype,"tagName",{get:function(){return this.name},set:function(u){this.name=u;},enumerable:!1,configurable:!0}),Object.defineProperty(e.prototype,"attributes",{get:function(){var u=this;return Object.keys(this.attribs).map(function(n){var r,a;return {name:n,value:u.attribs[n],namespace:(r=u["x-attribsNamespace"])===null||r===void 0?void 0:r[n],prefix:(a=u["x-attribsPrefix"])===null||a===void 0?void 0:a[n]}})},enumerable:!1,configurable:!0}),e}(Ze$1);I.Element=mt$1;function Dt$1(t){return (0, X.isTag)(t)}I.isTag=Dt$1;function xt$1(t){return t.type===X.ElementType.CDATA}I.isCDATA=xt$1;function At$1(t){return t.type===X.ElementType.Text}I.isText=At$1;function Et$2(t){return t.type===X.ElementType.Comment}I.isComment=Et$2;function yt$2(t){return t.type===X.ElementType.Directive}I.isDirective=yt$2;function vt$2(t){return t.type===X.ElementType.Root}I.isDocument=vt$2;function er(t){return Object.prototype.hasOwnProperty.call(t,"children")}I.hasChildren=er;function Du(t,e){e===void 0&&(e=!1);var u;if(At$1(t))u=new ft$1(t.data);else if(Et$2(t))u=new pt$1(t.data);else if(Dt$1(t)){var n=e?uu(t.children):[],r=new mt$1(t.name,ye$1({},t.attribs),n);n.forEach(function(c){return c.parent=r}),t.namespace!=null&&(r.namespace=t.namespace),t["x-attribsNamespace"]&&(r["x-attribsNamespace"]=ye$1({},t["x-attribsNamespace"])),t["x-attribsPrefix"]&&(r["x-attribsPrefix"]=ye$1({},t["x-attribsPrefix"])),u=r;}else if(xt$1(t)){var n=e?uu(t.children):[],a=new ht$1(n);n.forEach(function(d){return d.parent=a}),u=a;}else if(vt$2(t)){var n=e?uu(t.children):[],i=new gt$1(n);n.forEach(function(d){return d.parent=i}),t["x-mode"]&&(i["x-mode"]=t["x-mode"]),u=i;}else if(yt$2(t)){var l=new bt(t.name,t.data);t["x-name"]!=null&&(l["x-name"]=t["x-name"],l["x-publicId"]=t["x-publicId"],l["x-systemId"]=t["x-systemId"]),u=l;}else throw new Error("Not implemented yet: ".concat(t.type));return u.startIndex=t.startIndex,u.endIndex=t.endIndex,t.sourceCodeLocation!=null&&(u.sourceCodeLocation=t.sourceCodeLocation),u}I.cloneNode=Du;function uu(t){for(var e=t.map(function(n){return Du(n,!0)}),u=1;u<e.length;u++)e[u].prev=e[u-1],e[u-1].next=e[u];return e}(function(t){var e=Xs&&Xs.__createBinding||(Object.create?function(l,c,d,f){f===void 0&&(f=d);var h=Object.getOwnPropertyDescriptor(c,d);(!h||("get"in h?!c.__esModule:h.writable||h.configurable))&&(h={enumerable:!0,get:function(){return c[d]}}),Object.defineProperty(l,f,h);}:function(l,c,d,f){f===void 0&&(f=d),l[f]=c[d];}),u=Xs&&Xs.__exportStar||function(l,c){for(var d in l)d!=="default"&&!Object.prototype.hasOwnProperty.call(c,d)&&e(c,l,d);};Object.defineProperty(t,"__esModule",{value:!0}),t.DomHandler=void 0;var n=De,r=I;u(I,t);var a={withStartIndices:!1,withEndIndices:!1,xmlMode:!1},i=function(){function l(c,d,f){this.dom=[],this.root=new r.Document(this.dom),this.done=!1,this.tagStack=[this.root],this.lastNode=null,this.parser=null,typeof d=="function"&&(f=d,d=a),typeof c=="object"&&(d=c,c=void 0),this.callback=c??null,this.options=d??a,this.elementCB=f??null;}return l.prototype.onparserinit=function(c){this.parser=c;},l.prototype.onreset=function(){this.dom=[],this.root=new r.Document(this.dom),this.done=!1,this.tagStack=[this.root],this.lastNode=null,this.parser=null;},l.prototype.onend=function(){this.done||(this.done=!0,this.parser=null,this.handleCallback(null));},l.prototype.onerror=function(c){this.handleCallback(c);},l.prototype.onclosetag=function(){this.lastNode=null;var c=this.tagStack.pop();this.options.withEndIndices&&(c.endIndex=this.parser.endIndex),this.elementCB&&this.elementCB(c);},l.prototype.onopentag=function(c,d){var f=this.options.xmlMode?n.ElementType.Tag:void 0,h=new r.Element(c,d,void 0,f);this.addNode(h),this.tagStack.push(h);},l.prototype.ontext=function(c){var d=this.lastNode;if(d&&d.type===n.ElementType.Text)d.data+=c,this.options.withEndIndices&&(d.endIndex=this.parser.endIndex);else {var f=new r.Text(c);this.addNode(f),this.lastNode=f;}},l.prototype.oncomment=function(c){if(this.lastNode&&this.lastNode.type===n.ElementType.Comment){this.lastNode.data+=c;return}var d=new r.Comment(c);this.addNode(d),this.lastNode=d;},l.prototype.oncommentend=function(){this.lastNode=null;},l.prototype.oncdatastart=function(){var c=new r.Text(""),d=new r.CDATA([c]);this.addNode(d),c.parent=d,this.lastNode=c;},l.prototype.oncdataend=function(){this.lastNode=null;},l.prototype.onprocessinginstruction=function(c,d){var f=new r.ProcessingInstruction(c,d);this.addNode(f);},l.prototype.handleCallback=function(c){if(typeof this.callback=="function")this.callback(c,this.dom);else if(c)throw c},l.prototype.addNode=function(c){var d=this.tagStack[this.tagStack.length-1],f=d.children[d.children.length-1];this.options.withStartIndices&&(c.startIndex=this.parser.startIndex),this.options.withEndIndices&&(c.endIndex=this.parser.endIndex),d.children.push(c),f&&(c.prev=f,f.next=c),c.parent=d,this.lastNode=null;},l}();t.DomHandler=i,t.default=i;})(se);var Re={},K={},Fe={},wt={},pe$1={},xu={};Object.defineProperty(xu,"__esModule",{value:!0});function Oe(t){for(var e=1;e<t.length;e++)t[e][0]+=t[e-1][0]+1;return t}xu.default=new Map(Oe([[9,"&Tab;"],[0,"&NewLine;"],[22,"&excl;"],[0,"&quot;"],[0,"&num;"],[0,"&dollar;"],[0,"&percnt;"],[0,"&amp;"],[0,"&apos;"],[0,"&lpar;"],[0,"&rpar;"],[0,"&ast;"],[0,"&plus;"],[0,"&comma;"],[1,"&period;"],[0,"&sol;"],[10,"&colon;"],[0,"&semi;"],[0,{v:"&lt;",n:8402,o:"&nvlt;"}],[0,{v:"&equals;",n:8421,o:"&bne;"}],[0,{v:"&gt;",n:8402,o:"&nvgt;"}],[0,"&quest;"],[0,"&commat;"],[26,"&lbrack;"],[0,"&bsol;"],[0,"&rbrack;"],[0,"&Hat;"],[0,"&lowbar;"],[0,"&DiacriticalGrave;"],[5,{n:106,o:"&fjlig;"}],[20,"&lbrace;"],[0,"&verbar;"],[0,"&rbrace;"],[34,"&nbsp;"],[0,"&iexcl;"],[0,"&cent;"],[0,"&pound;"],[0,"&curren;"],[0,"&yen;"],[0,"&brvbar;"],[0,"&sect;"],[0,"&die;"],[0,"&copy;"],[0,"&ordf;"],[0,"&laquo;"],[0,"&not;"],[0,"&shy;"],[0,"&circledR;"],[0,"&macr;"],[0,"&deg;"],[0,"&PlusMinus;"],[0,"&sup2;"],[0,"&sup3;"],[0,"&acute;"],[0,"&micro;"],[0,"&para;"],[0,"&centerdot;"],[0,"&cedil;"],[0,"&sup1;"],[0,"&ordm;"],[0,"&raquo;"],[0,"&frac14;"],[0,"&frac12;"],[0,"&frac34;"],[0,"&iquest;"],[0,"&Agrave;"],[0,"&Aacute;"],[0,"&Acirc;"],[0,"&Atilde;"],[0,"&Auml;"],[0,"&angst;"],[0,"&AElig;"],[0,"&Ccedil;"],[0,"&Egrave;"],[0,"&Eacute;"],[0,"&Ecirc;"],[0,"&Euml;"],[0,"&Igrave;"],[0,"&Iacute;"],[0,"&Icirc;"],[0,"&Iuml;"],[0,"&ETH;"],[0,"&Ntilde;"],[0,"&Ograve;"],[0,"&Oacute;"],[0,"&Ocirc;"],[0,"&Otilde;"],[0,"&Ouml;"],[0,"&times;"],[0,"&Oslash;"],[0,"&Ugrave;"],[0,"&Uacute;"],[0,"&Ucirc;"],[0,"&Uuml;"],[0,"&Yacute;"],[0,"&THORN;"],[0,"&szlig;"],[0,"&agrave;"],[0,"&aacute;"],[0,"&acirc;"],[0,"&atilde;"],[0,"&auml;"],[0,"&aring;"],[0,"&aelig;"],[0,"&ccedil;"],[0,"&egrave;"],[0,"&eacute;"],[0,"&ecirc;"],[0,"&euml;"],[0,"&igrave;"],[0,"&iacute;"],[0,"&icirc;"],[0,"&iuml;"],[0,"&eth;"],[0,"&ntilde;"],[0,"&ograve;"],[0,"&oacute;"],[0,"&ocirc;"],[0,"&otilde;"],[0,"&ouml;"],[0,"&div;"],[0,"&oslash;"],[0,"&ugrave;"],[0,"&uacute;"],[0,"&ucirc;"],[0,"&uuml;"],[0,"&yacute;"],[0,"&thorn;"],[0,"&yuml;"],[0,"&Amacr;"],[0,"&amacr;"],[0,"&Abreve;"],[0,"&abreve;"],[0,"&Aogon;"],[0,"&aogon;"],[0,"&Cacute;"],[0,"&cacute;"],[0,"&Ccirc;"],[0,"&ccirc;"],[0,"&Cdot;"],[0,"&cdot;"],[0,"&Ccaron;"],[0,"&ccaron;"],[0,"&Dcaron;"],[0,"&dcaron;"],[0,"&Dstrok;"],[0,"&dstrok;"],[0,"&Emacr;"],[0,"&emacr;"],[2,"&Edot;"],[0,"&edot;"],[0,"&Eogon;"],[0,"&eogon;"],[0,"&Ecaron;"],[0,"&ecaron;"],[0,"&Gcirc;"],[0,"&gcirc;"],[0,"&Gbreve;"],[0,"&gbreve;"],[0,"&Gdot;"],[0,"&gdot;"],[0,"&Gcedil;"],[1,"&Hcirc;"],[0,"&hcirc;"],[0,"&Hstrok;"],[0,"&hstrok;"],[0,"&Itilde;"],[0,"&itilde;"],[0,"&Imacr;"],[0,"&imacr;"],[2,"&Iogon;"],[0,"&iogon;"],[0,"&Idot;"],[0,"&imath;"],[0,"&IJlig;"],[0,"&ijlig;"],[0,"&Jcirc;"],[0,"&jcirc;"],[0,"&Kcedil;"],[0,"&kcedil;"],[0,"&kgreen;"],[0,"&Lacute;"],[0,"&lacute;"],[0,"&Lcedil;"],[0,"&lcedil;"],[0,"&Lcaron;"],[0,"&lcaron;"],[0,"&Lmidot;"],[0,"&lmidot;"],[0,"&Lstrok;"],[0,"&lstrok;"],[0,"&Nacute;"],[0,"&nacute;"],[0,"&Ncedil;"],[0,"&ncedil;"],[0,"&Ncaron;"],[0,"&ncaron;"],[0,"&napos;"],[0,"&ENG;"],[0,"&eng;"],[0,"&Omacr;"],[0,"&omacr;"],[2,"&Odblac;"],[0,"&odblac;"],[0,"&OElig;"],[0,"&oelig;"],[0,"&Racute;"],[0,"&racute;"],[0,"&Rcedil;"],[0,"&rcedil;"],[0,"&Rcaron;"],[0,"&rcaron;"],[0,"&Sacute;"],[0,"&sacute;"],[0,"&Scirc;"],[0,"&scirc;"],[0,"&Scedil;"],[0,"&scedil;"],[0,"&Scaron;"],[0,"&scaron;"],[0,"&Tcedil;"],[0,"&tcedil;"],[0,"&Tcaron;"],[0,"&tcaron;"],[0,"&Tstrok;"],[0,"&tstrok;"],[0,"&Utilde;"],[0,"&utilde;"],[0,"&Umacr;"],[0,"&umacr;"],[0,"&Ubreve;"],[0,"&ubreve;"],[0,"&Uring;"],[0,"&uring;"],[0,"&Udblac;"],[0,"&udblac;"],[0,"&Uogon;"],[0,"&uogon;"],[0,"&Wcirc;"],[0,"&wcirc;"],[0,"&Ycirc;"],[0,"&ycirc;"],[0,"&Yuml;"],[0,"&Zacute;"],[0,"&zacute;"],[0,"&Zdot;"],[0,"&zdot;"],[0,"&Zcaron;"],[0,"&zcaron;"],[19,"&fnof;"],[34,"&imped;"],[63,"&gacute;"],[65,"&jmath;"],[142,"&circ;"],[0,"&caron;"],[16,"&breve;"],[0,"&DiacriticalDot;"],[0,"&ring;"],[0,"&ogon;"],[0,"&DiacriticalTilde;"],[0,"&dblac;"],[51,"&DownBreve;"],[127,"&Alpha;"],[0,"&Beta;"],[0,"&Gamma;"],[0,"&Delta;"],[0,"&Epsilon;"],[0,"&Zeta;"],[0,"&Eta;"],[0,"&Theta;"],[0,"&Iota;"],[0,"&Kappa;"],[0,"&Lambda;"],[0,"&Mu;"],[0,"&Nu;"],[0,"&Xi;"],[0,"&Omicron;"],[0,"&Pi;"],[0,"&Rho;"],[1,"&Sigma;"],[0,"&Tau;"],[0,"&Upsilon;"],[0,"&Phi;"],[0,"&Chi;"],[0,"&Psi;"],[0,"&ohm;"],[7,"&alpha;"],[0,"&beta;"],[0,"&gamma;"],[0,"&delta;"],[0,"&epsi;"],[0,"&zeta;"],[0,"&eta;"],[0,"&theta;"],[0,"&iota;"],[0,"&kappa;"],[0,"&lambda;"],[0,"&mu;"],[0,"&nu;"],[0,"&xi;"],[0,"&omicron;"],[0,"&pi;"],[0,"&rho;"],[0,"&sigmaf;"],[0,"&sigma;"],[0,"&tau;"],[0,"&upsi;"],[0,"&phi;"],[0,"&chi;"],[0,"&psi;"],[0,"&omega;"],[7,"&thetasym;"],[0,"&Upsi;"],[2,"&phiv;"],[0,"&piv;"],[5,"&Gammad;"],[0,"&digamma;"],[18,"&kappav;"],[0,"&rhov;"],[3,"&epsiv;"],[0,"&backepsilon;"],[10,"&IOcy;"],[0,"&DJcy;"],[0,"&GJcy;"],[0,"&Jukcy;"],[0,"&DScy;"],[0,"&Iukcy;"],[0,"&YIcy;"],[0,"&Jsercy;"],[0,"&LJcy;"],[0,"&NJcy;"],[0,"&TSHcy;"],[0,"&KJcy;"],[1,"&Ubrcy;"],[0,"&DZcy;"],[0,"&Acy;"],[0,"&Bcy;"],[0,"&Vcy;"],[0,"&Gcy;"],[0,"&Dcy;"],[0,"&IEcy;"],[0,"&ZHcy;"],[0,"&Zcy;"],[0,"&Icy;"],[0,"&Jcy;"],[0,"&Kcy;"],[0,"&Lcy;"],[0,"&Mcy;"],[0,"&Ncy;"],[0,"&Ocy;"],[0,"&Pcy;"],[0,"&Rcy;"],[0,"&Scy;"],[0,"&Tcy;"],[0,"&Ucy;"],[0,"&Fcy;"],[0,"&KHcy;"],[0,"&TScy;"],[0,"&CHcy;"],[0,"&SHcy;"],[0,"&SHCHcy;"],[0,"&HARDcy;"],[0,"&Ycy;"],[0,"&SOFTcy;"],[0,"&Ecy;"],[0,"&YUcy;"],[0,"&YAcy;"],[0,"&acy;"],[0,"&bcy;"],[0,"&vcy;"],[0,"&gcy;"],[0,"&dcy;"],[0,"&iecy;"],[0,"&zhcy;"],[0,"&zcy;"],[0,"&icy;"],[0,"&jcy;"],[0,"&kcy;"],[0,"&lcy;"],[0,"&mcy;"],[0,"&ncy;"],[0,"&ocy;"],[0,"&pcy;"],[0,"&rcy;"],[0,"&scy;"],[0,"&tcy;"],[0,"&ucy;"],[0,"&fcy;"],[0,"&khcy;"],[0,"&tscy;"],[0,"&chcy;"],[0,"&shcy;"],[0,"&shchcy;"],[0,"&hardcy;"],[0,"&ycy;"],[0,"&softcy;"],[0,"&ecy;"],[0,"&yucy;"],[0,"&yacy;"],[1,"&iocy;"],[0,"&djcy;"],[0,"&gjcy;"],[0,"&jukcy;"],[0,"&dscy;"],[0,"&iukcy;"],[0,"&yicy;"],[0,"&jsercy;"],[0,"&ljcy;"],[0,"&njcy;"],[0,"&tshcy;"],[0,"&kjcy;"],[1,"&ubrcy;"],[0,"&dzcy;"],[7074,"&ensp;"],[0,"&emsp;"],[0,"&emsp13;"],[0,"&emsp14;"],[1,"&numsp;"],[0,"&puncsp;"],[0,"&ThinSpace;"],[0,"&hairsp;"],[0,"&NegativeMediumSpace;"],[0,"&zwnj;"],[0,"&zwj;"],[0,"&lrm;"],[0,"&rlm;"],[0,"&dash;"],[2,"&ndash;"],[0,"&mdash;"],[0,"&horbar;"],[0,"&Verbar;"],[1,"&lsquo;"],[0,"&CloseCurlyQuote;"],[0,"&lsquor;"],[1,"&ldquo;"],[0,"&CloseCurlyDoubleQuote;"],[0,"&bdquo;"],[1,"&dagger;"],[0,"&Dagger;"],[0,"&bull;"],[2,"&nldr;"],[0,"&hellip;"],[9,"&permil;"],[0,"&pertenk;"],[0,"&prime;"],[0,"&Prime;"],[0,"&tprime;"],[0,"&backprime;"],[3,"&lsaquo;"],[0,"&rsaquo;"],[3,"&oline;"],[2,"&caret;"],[1,"&hybull;"],[0,"&frasl;"],[10,"&bsemi;"],[7,"&qprime;"],[7,{v:"&MediumSpace;",n:8202,o:"&ThickSpace;"}],[0,"&NoBreak;"],[0,"&af;"],[0,"&InvisibleTimes;"],[0,"&ic;"],[72,"&euro;"],[46,"&tdot;"],[0,"&DotDot;"],[37,"&complexes;"],[2,"&incare;"],[4,"&gscr;"],[0,"&hamilt;"],[0,"&Hfr;"],[0,"&Hopf;"],[0,"&planckh;"],[0,"&hbar;"],[0,"&imagline;"],[0,"&Ifr;"],[0,"&lagran;"],[0,"&ell;"],[1,"&naturals;"],[0,"&numero;"],[0,"&copysr;"],[0,"&weierp;"],[0,"&Popf;"],[0,"&Qopf;"],[0,"&realine;"],[0,"&real;"],[0,"&reals;"],[0,"&rx;"],[3,"&trade;"],[1,"&integers;"],[2,"&mho;"],[0,"&zeetrf;"],[0,"&iiota;"],[2,"&bernou;"],[0,"&Cayleys;"],[1,"&escr;"],[0,"&Escr;"],[0,"&Fouriertrf;"],[1,"&Mellintrf;"],[0,"&order;"],[0,"&alefsym;"],[0,"&beth;"],[0,"&gimel;"],[0,"&daleth;"],[12,"&CapitalDifferentialD;"],[0,"&dd;"],[0,"&ee;"],[0,"&ii;"],[10,"&frac13;"],[0,"&frac23;"],[0,"&frac15;"],[0,"&frac25;"],[0,"&frac35;"],[0,"&frac45;"],[0,"&frac16;"],[0,"&frac56;"],[0,"&frac18;"],[0,"&frac38;"],[0,"&frac58;"],[0,"&frac78;"],[49,"&larr;"],[0,"&ShortUpArrow;"],[0,"&rarr;"],[0,"&darr;"],[0,"&harr;"],[0,"&updownarrow;"],[0,"&nwarr;"],[0,"&nearr;"],[0,"&LowerRightArrow;"],[0,"&LowerLeftArrow;"],[0,"&nlarr;"],[0,"&nrarr;"],[1,{v:"&rarrw;",n:824,o:"&nrarrw;"}],[0,"&Larr;"],[0,"&Uarr;"],[0,"&Rarr;"],[0,"&Darr;"],[0,"&larrtl;"],[0,"&rarrtl;"],[0,"&LeftTeeArrow;"],[0,"&mapstoup;"],[0,"&map;"],[0,"&DownTeeArrow;"],[1,"&hookleftarrow;"],[0,"&hookrightarrow;"],[0,"&larrlp;"],[0,"&looparrowright;"],[0,"&harrw;"],[0,"&nharr;"],[1,"&lsh;"],[0,"&rsh;"],[0,"&ldsh;"],[0,"&rdsh;"],[1,"&crarr;"],[0,"&cularr;"],[0,"&curarr;"],[2,"&circlearrowleft;"],[0,"&circlearrowright;"],[0,"&leftharpoonup;"],[0,"&DownLeftVector;"],[0,"&RightUpVector;"],[0,"&LeftUpVector;"],[0,"&rharu;"],[0,"&DownRightVector;"],[0,"&dharr;"],[0,"&dharl;"],[0,"&RightArrowLeftArrow;"],[0,"&udarr;"],[0,"&LeftArrowRightArrow;"],[0,"&leftleftarrows;"],[0,"&upuparrows;"],[0,"&rightrightarrows;"],[0,"&ddarr;"],[0,"&leftrightharpoons;"],[0,"&Equilibrium;"],[0,"&nlArr;"],[0,"&nhArr;"],[0,"&nrArr;"],[0,"&DoubleLeftArrow;"],[0,"&DoubleUpArrow;"],[0,"&DoubleRightArrow;"],[0,"&dArr;"],[0,"&DoubleLeftRightArrow;"],[0,"&DoubleUpDownArrow;"],[0,"&nwArr;"],[0,"&neArr;"],[0,"&seArr;"],[0,"&swArr;"],[0,"&lAarr;"],[0,"&rAarr;"],[1,"&zigrarr;"],[6,"&larrb;"],[0,"&rarrb;"],[15,"&DownArrowUpArrow;"],[7,"&loarr;"],[0,"&roarr;"],[0,"&hoarr;"],[0,"&forall;"],[0,"&comp;"],[0,{v:"&part;",n:824,o:"&npart;"}],[0,"&exist;"],[0,"&nexist;"],[0,"&empty;"],[1,"&Del;"],[0,"&Element;"],[0,"&NotElement;"],[1,"&ni;"],[0,"&notni;"],[2,"&prod;"],[0,"&coprod;"],[0,"&sum;"],[0,"&minus;"],[0,"&MinusPlus;"],[0,"&dotplus;"],[1,"&Backslash;"],[0,"&lowast;"],[0,"&compfn;"],[1,"&radic;"],[2,"&prop;"],[0,"&infin;"],[0,"&angrt;"],[0,{v:"&ang;",n:8402,o:"&nang;"}],[0,"&angmsd;"],[0,"&angsph;"],[0,"&mid;"],[0,"&nmid;"],[0,"&DoubleVerticalBar;"],[0,"&NotDoubleVerticalBar;"],[0,"&and;"],[0,"&or;"],[0,{v:"&cap;",n:65024,o:"&caps;"}],[0,{v:"&cup;",n:65024,o:"&cups;"}],[0,"&int;"],[0,"&Int;"],[0,"&iiint;"],[0,"&conint;"],[0,"&Conint;"],[0,"&Cconint;"],[0,"&cwint;"],[0,"&ClockwiseContourIntegral;"],[0,"&awconint;"],[0,"&there4;"],[0,"&becaus;"],[0,"&ratio;"],[0,"&Colon;"],[0,"&dotminus;"],[1,"&mDDot;"],[0,"&homtht;"],[0,{v:"&sim;",n:8402,o:"&nvsim;"}],[0,{v:"&backsim;",n:817,o:"&race;"}],[0,{v:"&ac;",n:819,o:"&acE;"}],[0,"&acd;"],[0,"&VerticalTilde;"],[0,"&NotTilde;"],[0,{v:"&eqsim;",n:824,o:"&nesim;"}],[0,"&sime;"],[0,"&NotTildeEqual;"],[0,"&cong;"],[0,"&simne;"],[0,"&ncong;"],[0,"&ap;"],[0,"&nap;"],[0,"&ape;"],[0,{v:"&apid;",n:824,o:"&napid;"}],[0,"&backcong;"],[0,{v:"&asympeq;",n:8402,o:"&nvap;"}],[0,{v:"&bump;",n:824,o:"&nbump;"}],[0,{v:"&bumpe;",n:824,o:"&nbumpe;"}],[0,{v:"&doteq;",n:824,o:"&nedot;"}],[0,"&doteqdot;"],[0,"&efDot;"],[0,"&erDot;"],[0,"&Assign;"],[0,"&ecolon;"],[0,"&ecir;"],[0,"&circeq;"],[1,"&wedgeq;"],[0,"&veeeq;"],[1,"&triangleq;"],[2,"&equest;"],[0,"&ne;"],[0,{v:"&Congruent;",n:8421,o:"&bnequiv;"}],[0,"&nequiv;"],[1,{v:"&le;",n:8402,o:"&nvle;"}],[0,{v:"&ge;",n:8402,o:"&nvge;"}],[0,{v:"&lE;",n:824,o:"&nlE;"}],[0,{v:"&gE;",n:824,o:"&ngE;"}],[0,{v:"&lnE;",n:65024,o:"&lvertneqq;"}],[0,{v:"&gnE;",n:65024,o:"&gvertneqq;"}],[0,{v:"&ll;",n:new Map(Oe([[824,"&nLtv;"],[7577,"&nLt;"]]))}],[0,{v:"&gg;",n:new Map(Oe([[824,"&nGtv;"],[7577,"&nGt;"]]))}],[0,"&between;"],[0,"&NotCupCap;"],[0,"&nless;"],[0,"&ngt;"],[0,"&nle;"],[0,"&nge;"],[0,"&lesssim;"],[0,"&GreaterTilde;"],[0,"&nlsim;"],[0,"&ngsim;"],[0,"&LessGreater;"],[0,"&gl;"],[0,"&NotLessGreater;"],[0,"&NotGreaterLess;"],[0,"&pr;"],[0,"&sc;"],[0,"&prcue;"],[0,"&sccue;"],[0,"&PrecedesTilde;"],[0,{v:"&scsim;",n:824,o:"&NotSucceedsTilde;"}],[0,"&NotPrecedes;"],[0,"&NotSucceeds;"],[0,{v:"&sub;",n:8402,o:"&NotSubset;"}],[0,{v:"&sup;",n:8402,o:"&NotSuperset;"}],[0,"&nsub;"],[0,"&nsup;"],[0,"&sube;"],[0,"&supe;"],[0,"&NotSubsetEqual;"],[0,"&NotSupersetEqual;"],[0,{v:"&subne;",n:65024,o:"&varsubsetneq;"}],[0,{v:"&supne;",n:65024,o:"&varsupsetneq;"}],[1,"&cupdot;"],[0,"&UnionPlus;"],[0,{v:"&sqsub;",n:824,o:"&NotSquareSubset;"}],[0,{v:"&sqsup;",n:824,o:"&NotSquareSuperset;"}],[0,"&sqsube;"],[0,"&sqsupe;"],[0,{v:"&sqcap;",n:65024,o:"&sqcaps;"}],[0,{v:"&sqcup;",n:65024,o:"&sqcups;"}],[0,"&CirclePlus;"],[0,"&CircleMinus;"],[0,"&CircleTimes;"],[0,"&osol;"],[0,"&CircleDot;"],[0,"&circledcirc;"],[0,"&circledast;"],[1,"&circleddash;"],[0,"&boxplus;"],[0,"&boxminus;"],[0,"&boxtimes;"],[0,"&dotsquare;"],[0,"&RightTee;"],[0,"&dashv;"],[0,"&DownTee;"],[0,"&bot;"],[1,"&models;"],[0,"&DoubleRightTee;"],[0,"&Vdash;"],[0,"&Vvdash;"],[0,"&VDash;"],[0,"&nvdash;"],[0,"&nvDash;"],[0,"&nVdash;"],[0,"&nVDash;"],[0,"&prurel;"],[1,"&LeftTriangle;"],[0,"&RightTriangle;"],[0,{v:"&LeftTriangleEqual;",n:8402,o:"&nvltrie;"}],[0,{v:"&RightTriangleEqual;",n:8402,o:"&nvrtrie;"}],[0,"&origof;"],[0,"&imof;"],[0,"&multimap;"],[0,"&hercon;"],[0,"&intcal;"],[0,"&veebar;"],[1,"&barvee;"],[0,"&angrtvb;"],[0,"&lrtri;"],[0,"&bigwedge;"],[0,"&bigvee;"],[0,"&bigcap;"],[0,"&bigcup;"],[0,"&diam;"],[0,"&sdot;"],[0,"&sstarf;"],[0,"&divideontimes;"],[0,"&bowtie;"],[0,"&ltimes;"],[0,"&rtimes;"],[0,"&leftthreetimes;"],[0,"&rightthreetimes;"],[0,"&backsimeq;"],[0,"&curlyvee;"],[0,"&curlywedge;"],[0,"&Sub;"],[0,"&Sup;"],[0,"&Cap;"],[0,"&Cup;"],[0,"&fork;"],[0,"&epar;"],[0,"&lessdot;"],[0,"&gtdot;"],[0,{v:"&Ll;",n:824,o:"&nLl;"}],[0,{v:"&Gg;",n:824,o:"&nGg;"}],[0,{v:"&leg;",n:65024,o:"&lesg;"}],[0,{v:"&gel;",n:65024,o:"&gesl;"}],[2,"&cuepr;"],[0,"&cuesc;"],[0,"&NotPrecedesSlantEqual;"],[0,"&NotSucceedsSlantEqual;"],[0,"&NotSquareSubsetEqual;"],[0,"&NotSquareSupersetEqual;"],[2,"&lnsim;"],[0,"&gnsim;"],[0,"&precnsim;"],[0,"&scnsim;"],[0,"&nltri;"],[0,"&NotRightTriangle;"],[0,"&nltrie;"],[0,"&NotRightTriangleEqual;"],[0,"&vellip;"],[0,"&ctdot;"],[0,"&utdot;"],[0,"&dtdot;"],[0,"&disin;"],[0,"&isinsv;"],[0,"&isins;"],[0,{v:"&isindot;",n:824,o:"&notindot;"}],[0,"&notinvc;"],[0,"&notinvb;"],[1,{v:"&isinE;",n:824,o:"&notinE;"}],[0,"&nisd;"],[0,"&xnis;"],[0,"&nis;"],[0,"&notnivc;"],[0,"&notnivb;"],[6,"&barwed;"],[0,"&Barwed;"],[1,"&lceil;"],[0,"&rceil;"],[0,"&LeftFloor;"],[0,"&rfloor;"],[0,"&drcrop;"],[0,"&dlcrop;"],[0,"&urcrop;"],[0,"&ulcrop;"],[0,"&bnot;"],[1,"&profline;"],[0,"&profsurf;"],[1,"&telrec;"],[0,"&target;"],[5,"&ulcorn;"],[0,"&urcorn;"],[0,"&dlcorn;"],[0,"&drcorn;"],[2,"&frown;"],[0,"&smile;"],[9,"&cylcty;"],[0,"&profalar;"],[7,"&topbot;"],[6,"&ovbar;"],[1,"&solbar;"],[60,"&angzarr;"],[51,"&lmoustache;"],[0,"&rmoustache;"],[2,"&OverBracket;"],[0,"&bbrk;"],[0,"&bbrktbrk;"],[37,"&OverParenthesis;"],[0,"&UnderParenthesis;"],[0,"&OverBrace;"],[0,"&UnderBrace;"],[2,"&trpezium;"],[4,"&elinters;"],[59,"&blank;"],[164,"&circledS;"],[55,"&boxh;"],[1,"&boxv;"],[9,"&boxdr;"],[3,"&boxdl;"],[3,"&boxur;"],[3,"&boxul;"],[3,"&boxvr;"],[7,"&boxvl;"],[7,"&boxhd;"],[7,"&boxhu;"],[7,"&boxvh;"],[19,"&boxH;"],[0,"&boxV;"],[0,"&boxdR;"],[0,"&boxDr;"],[0,"&boxDR;"],[0,"&boxdL;"],[0,"&boxDl;"],[0,"&boxDL;"],[0,"&boxuR;"],[0,"&boxUr;"],[0,"&boxUR;"],[0,"&boxuL;"],[0,"&boxUl;"],[0,"&boxUL;"],[0,"&boxvR;"],[0,"&boxVr;"],[0,"&boxVR;"],[0,"&boxvL;"],[0,"&boxVl;"],[0,"&boxVL;"],[0,"&boxHd;"],[0,"&boxhD;"],[0,"&boxHD;"],[0,"&boxHu;"],[0,"&boxhU;"],[0,"&boxHU;"],[0,"&boxvH;"],[0,"&boxVh;"],[0,"&boxVH;"],[19,"&uhblk;"],[3,"&lhblk;"],[3,"&block;"],[8,"&blk14;"],[0,"&blk12;"],[0,"&blk34;"],[13,"&square;"],[8,"&blacksquare;"],[0,"&EmptyVerySmallSquare;"],[1,"&rect;"],[0,"&marker;"],[2,"&fltns;"],[1,"&bigtriangleup;"],[0,"&blacktriangle;"],[0,"&triangle;"],[2,"&blacktriangleright;"],[0,"&rtri;"],[3,"&bigtriangledown;"],[0,"&blacktriangledown;"],[0,"&dtri;"],[2,"&blacktriangleleft;"],[0,"&ltri;"],[6,"&loz;"],[0,"&cir;"],[32,"&tridot;"],[2,"&bigcirc;"],[8,"&ultri;"],[0,"&urtri;"],[0,"&lltri;"],[0,"&EmptySmallSquare;"],[0,"&FilledSmallSquare;"],[8,"&bigstar;"],[0,"&star;"],[7,"&phone;"],[49,"&female;"],[1,"&male;"],[29,"&spades;"],[2,"&clubs;"],[1,"&hearts;"],[0,"&diamondsuit;"],[3,"&sung;"],[2,"&flat;"],[0,"&natural;"],[0,"&sharp;"],[163,"&check;"],[3,"&cross;"],[8,"&malt;"],[21,"&sext;"],[33,"&VerticalSeparator;"],[25,"&lbbrk;"],[0,"&rbbrk;"],[84,"&bsolhsub;"],[0,"&suphsol;"],[28,"&LeftDoubleBracket;"],[0,"&RightDoubleBracket;"],[0,"&lang;"],[0,"&rang;"],[0,"&Lang;"],[0,"&Rang;"],[0,"&loang;"],[0,"&roang;"],[7,"&longleftarrow;"],[0,"&longrightarrow;"],[0,"&longleftrightarrow;"],[0,"&DoubleLongLeftArrow;"],[0,"&DoubleLongRightArrow;"],[0,"&DoubleLongLeftRightArrow;"],[1,"&longmapsto;"],[2,"&dzigrarr;"],[258,"&nvlArr;"],[0,"&nvrArr;"],[0,"&nvHarr;"],[0,"&Map;"],[6,"&lbarr;"],[0,"&bkarow;"],[0,"&lBarr;"],[0,"&dbkarow;"],[0,"&drbkarow;"],[0,"&DDotrahd;"],[0,"&UpArrowBar;"],[0,"&DownArrowBar;"],[2,"&Rarrtl;"],[2,"&latail;"],[0,"&ratail;"],[0,"&lAtail;"],[0,"&rAtail;"],[0,"&larrfs;"],[0,"&rarrfs;"],[0,"&larrbfs;"],[0,"&rarrbfs;"],[2,"&nwarhk;"],[0,"&nearhk;"],[0,"&hksearow;"],[0,"&hkswarow;"],[0,"&nwnear;"],[0,"&nesear;"],[0,"&seswar;"],[0,"&swnwar;"],[8,{v:"&rarrc;",n:824,o:"&nrarrc;"}],[1,"&cudarrr;"],[0,"&ldca;"],[0,"&rdca;"],[0,"&cudarrl;"],[0,"&larrpl;"],[2,"&curarrm;"],[0,"&cularrp;"],[7,"&rarrpl;"],[2,"&harrcir;"],[0,"&Uarrocir;"],[0,"&lurdshar;"],[0,"&ldrushar;"],[2,"&LeftRightVector;"],[0,"&RightUpDownVector;"],[0,"&DownLeftRightVector;"],[0,"&LeftUpDownVector;"],[0,"&LeftVectorBar;"],[0,"&RightVectorBar;"],[0,"&RightUpVectorBar;"],[0,"&RightDownVectorBar;"],[0,"&DownLeftVectorBar;"],[0,"&DownRightVectorBar;"],[0,"&LeftUpVectorBar;"],[0,"&LeftDownVectorBar;"],[0,"&LeftTeeVector;"],[0,"&RightTeeVector;"],[0,"&RightUpTeeVector;"],[0,"&RightDownTeeVector;"],[0,"&DownLeftTeeVector;"],[0,"&DownRightTeeVector;"],[0,"&LeftUpTeeVector;"],[0,"&LeftDownTeeVector;"],[0,"&lHar;"],[0,"&uHar;"],[0,"&rHar;"],[0,"&dHar;"],[0,"&luruhar;"],[0,"&ldrdhar;"],[0,"&ruluhar;"],[0,"&rdldhar;"],[0,"&lharul;"],[0,"&llhard;"],[0,"&rharul;"],[0,"&lrhard;"],[0,"&udhar;"],[0,"&duhar;"],[0,"&RoundImplies;"],[0,"&erarr;"],[0,"&simrarr;"],[0,"&larrsim;"],[0,"&rarrsim;"],[0,"&rarrap;"],[0,"&ltlarr;"],[1,"&gtrarr;"],[0,"&subrarr;"],[1,"&suplarr;"],[0,"&lfisht;"],[0,"&rfisht;"],[0,"&ufisht;"],[0,"&dfisht;"],[5,"&lopar;"],[0,"&ropar;"],[4,"&lbrke;"],[0,"&rbrke;"],[0,"&lbrkslu;"],[0,"&rbrksld;"],[0,"&lbrksld;"],[0,"&rbrkslu;"],[0,"&langd;"],[0,"&rangd;"],[0,"&lparlt;"],[0,"&rpargt;"],[0,"&gtlPar;"],[0,"&ltrPar;"],[3,"&vzigzag;"],[1,"&vangrt;"],[0,"&angrtvbd;"],[6,"&ange;"],[0,"&range;"],[0,"&dwangle;"],[0,"&uwangle;"],[0,"&angmsdaa;"],[0,"&angmsdab;"],[0,"&angmsdac;"],[0,"&angmsdad;"],[0,"&angmsdae;"],[0,"&angmsdaf;"],[0,"&angmsdag;"],[0,"&angmsdah;"],[0,"&bemptyv;"],[0,"&demptyv;"],[0,"&cemptyv;"],[0,"&raemptyv;"],[0,"&laemptyv;"],[0,"&ohbar;"],[0,"&omid;"],[0,"&opar;"],[1,"&operp;"],[1,"&olcross;"],[0,"&odsold;"],[1,"&olcir;"],[0,"&ofcir;"],[0,"&olt;"],[0,"&ogt;"],[0,"&cirscir;"],[0,"&cirE;"],[0,"&solb;"],[0,"&bsolb;"],[3,"&boxbox;"],[3,"&trisb;"],[0,"&rtriltri;"],[0,{v:"&LeftTriangleBar;",n:824,o:"&NotLeftTriangleBar;"}],[0,{v:"&RightTriangleBar;",n:824,o:"&NotRightTriangleBar;"}],[11,"&iinfin;"],[0,"&infintie;"],[0,"&nvinfin;"],[4,"&eparsl;"],[0,"&smeparsl;"],[0,"&eqvparsl;"],[5,"&blacklozenge;"],[8,"&RuleDelayed;"],[1,"&dsol;"],[9,"&bigodot;"],[0,"&bigoplus;"],[0,"&bigotimes;"],[1,"&biguplus;"],[1,"&bigsqcup;"],[5,"&iiiint;"],[0,"&fpartint;"],[2,"&cirfnint;"],[0,"&awint;"],[0,"&rppolint;"],[0,"&scpolint;"],[0,"&npolint;"],[0,"&pointint;"],[0,"&quatint;"],[0,"&intlarhk;"],[10,"&pluscir;"],[0,"&plusacir;"],[0,"&simplus;"],[0,"&plusdu;"],[0,"&plussim;"],[0,"&plustwo;"],[1,"&mcomma;"],[0,"&minusdu;"],[2,"&loplus;"],[0,"&roplus;"],[0,"&Cross;"],[0,"&timesd;"],[0,"&timesbar;"],[1,"&smashp;"],[0,"&lotimes;"],[0,"&rotimes;"],[0,"&otimesas;"],[0,"&Otimes;"],[0,"&odiv;"],[0,"&triplus;"],[0,"&triminus;"],[0,"&tritime;"],[0,"&intprod;"],[2,"&amalg;"],[0,"&capdot;"],[1,"&ncup;"],[0,"&ncap;"],[0,"&capand;"],[0,"&cupor;"],[0,"&cupcap;"],[0,"&capcup;"],[0,"&cupbrcap;"],[0,"&capbrcup;"],[0,"&cupcup;"],[0,"&capcap;"],[0,"&ccups;"],[0,"&ccaps;"],[2,"&ccupssm;"],[2,"&And;"],[0,"&Or;"],[0,"&andand;"],[0,"&oror;"],[0,"&orslope;"],[0,"&andslope;"],[1,"&andv;"],[0,"&orv;"],[0,"&andd;"],[0,"&ord;"],[1,"&wedbar;"],[6,"&sdote;"],[3,"&simdot;"],[2,{v:"&congdot;",n:824,o:"&ncongdot;"}],[0,"&easter;"],[0,"&apacir;"],[0,{v:"&apE;",n:824,o:"&napE;"}],[0,"&eplus;"],[0,"&pluse;"],[0,"&Esim;"],[0,"&Colone;"],[0,"&Equal;"],[1,"&ddotseq;"],[0,"&equivDD;"],[0,"&ltcir;"],[0,"&gtcir;"],[0,"&ltquest;"],[0,"&gtquest;"],[0,{v:"&leqslant;",n:824,o:"&nleqslant;"}],[0,{v:"&geqslant;",n:824,o:"&ngeqslant;"}],[0,"&lesdot;"],[0,"&gesdot;"],[0,"&lesdoto;"],[0,"&gesdoto;"],[0,"&lesdotor;"],[0,"&gesdotol;"],[0,"&lap;"],[0,"&gap;"],[0,"&lne;"],[0,"&gne;"],[0,"&lnap;"],[0,"&gnap;"],[0,"&lEg;"],[0,"&gEl;"],[0,"&lsime;"],[0,"&gsime;"],[0,"&lsimg;"],[0,"&gsiml;"],[0,"&lgE;"],[0,"&glE;"],[0,"&lesges;"],[0,"&gesles;"],[0,"&els;"],[0,"&egs;"],[0,"&elsdot;"],[0,"&egsdot;"],[0,"&el;"],[0,"&eg;"],[2,"&siml;"],[0,"&simg;"],[0,"&simlE;"],[0,"&simgE;"],[0,{v:"&LessLess;",n:824,o:"&NotNestedLessLess;"}],[0,{v:"&GreaterGreater;",n:824,o:"&NotNestedGreaterGreater;"}],[1,"&glj;"],[0,"&gla;"],[0,"&ltcc;"],[0,"&gtcc;"],[0,"&lescc;"],[0,"&gescc;"],[0,"&smt;"],[0,"&lat;"],[0,{v:"&smte;",n:65024,o:"&smtes;"}],[0,{v:"&late;",n:65024,o:"&lates;"}],[0,"&bumpE;"],[0,{v:"&PrecedesEqual;",n:824,o:"&NotPrecedesEqual;"}],[0,{v:"&sce;",n:824,o:"&NotSucceedsEqual;"}],[2,"&prE;"],[0,"&scE;"],[0,"&precneqq;"],[0,"&scnE;"],[0,"&prap;"],[0,"&scap;"],[0,"&precnapprox;"],[0,"&scnap;"],[0,"&Pr;"],[0,"&Sc;"],[0,"&subdot;"],[0,"&supdot;"],[0,"&subplus;"],[0,"&supplus;"],[0,"&submult;"],[0,"&supmult;"],[0,"&subedot;"],[0,"&supedot;"],[0,{v:"&subE;",n:824,o:"&nsubE;"}],[0,{v:"&supE;",n:824,o:"&nsupE;"}],[0,"&subsim;"],[0,"&supsim;"],[2,{v:"&subnE;",n:65024,o:"&varsubsetneqq;"}],[0,{v:"&supnE;",n:65024,o:"&varsupsetneqq;"}],[2,"&csub;"],[0,"&csup;"],[0,"&csube;"],[0,"&csupe;"],[0,"&subsup;"],[0,"&supsub;"],[0,"&subsub;"],[0,"&supsup;"],[0,"&suphsub;"],[0,"&supdsub;"],[0,"&forkv;"],[0,"&topfork;"],[0,"&mlcp;"],[8,"&Dashv;"],[1,"&Vdashl;"],[0,"&Barv;"],[0,"&vBar;"],[0,"&vBarv;"],[1,"&Vbar;"],[0,"&Not;"],[0,"&bNot;"],[0,"&rnmid;"],[0,"&cirmid;"],[0,"&midcir;"],[0,"&topcir;"],[0,"&nhpar;"],[0,"&parsim;"],[9,{v:"&parsl;",n:8421,o:"&nparsl;"}],[44343,{n:new Map(Oe([[56476,"&Ascr;"],[1,"&Cscr;"],[0,"&Dscr;"],[2,"&Gscr;"],[2,"&Jscr;"],[0,"&Kscr;"],[2,"&Nscr;"],[0,"&Oscr;"],[0,"&Pscr;"],[0,"&Qscr;"],[1,"&Sscr;"],[0,"&Tscr;"],[0,"&Uscr;"],[0,"&Vscr;"],[0,"&Wscr;"],[0,"&Xscr;"],[0,"&Yscr;"],[0,"&Zscr;"],[0,"&ascr;"],[0,"&bscr;"],[0,"&cscr;"],[0,"&dscr;"],[1,"&fscr;"],[1,"&hscr;"],[0,"&iscr;"],[0,"&jscr;"],[0,"&kscr;"],[0,"&lscr;"],[0,"&mscr;"],[0,"&nscr;"],[1,"&pscr;"],[0,"&qscr;"],[0,"&rscr;"],[0,"&sscr;"],[0,"&tscr;"],[0,"&uscr;"],[0,"&vscr;"],[0,"&wscr;"],[0,"&xscr;"],[0,"&yscr;"],[0,"&zscr;"],[52,"&Afr;"],[0,"&Bfr;"],[1,"&Dfr;"],[0,"&Efr;"],[0,"&Ffr;"],[0,"&Gfr;"],[2,"&Jfr;"],[0,"&Kfr;"],[0,"&Lfr;"],[0,"&Mfr;"],[0,"&Nfr;"],[0,"&Ofr;"],[0,"&Pfr;"],[0,"&Qfr;"],[1,"&Sfr;"],[0,"&Tfr;"],[0,"&Ufr;"],[0,"&Vfr;"],[0,"&Wfr;"],[0,"&Xfr;"],[0,"&Yfr;"],[1,"&afr;"],[0,"&bfr;"],[0,"&cfr;"],[0,"&dfr;"],[0,"&efr;"],[0,"&ffr;"],[0,"&gfr;"],[0,"&hfr;"],[0,"&ifr;"],[0,"&jfr;"],[0,"&kfr;"],[0,"&lfr;"],[0,"&mfr;"],[0,"&nfr;"],[0,"&ofr;"],[0,"&pfr;"],[0,"&qfr;"],[0,"&rfr;"],[0,"&sfr;"],[0,"&tfr;"],[0,"&ufr;"],[0,"&vfr;"],[0,"&wfr;"],[0,"&xfr;"],[0,"&yfr;"],[0,"&zfr;"],[0,"&Aopf;"],[0,"&Bopf;"],[1,"&Dopf;"],[0,"&Eopf;"],[0,"&Fopf;"],[0,"&Gopf;"],[1,"&Iopf;"],[0,"&Jopf;"],[0,"&Kopf;"],[0,"&Lopf;"],[0,"&Mopf;"],[1,"&Oopf;"],[3,"&Sopf;"],[0,"&Topf;"],[0,"&Uopf;"],[0,"&Vopf;"],[0,"&Wopf;"],[0,"&Xopf;"],[0,"&Yopf;"],[1,"&aopf;"],[0,"&bopf;"],[0,"&copf;"],[0,"&dopf;"],[0,"&eopf;"],[0,"&fopf;"],[0,"&gopf;"],[0,"&hopf;"],[0,"&iopf;"],[0,"&jopf;"],[0,"&kopf;"],[0,"&lopf;"],[0,"&mopf;"],[0,"&nopf;"],[0,"&oopf;"],[0,"&popf;"],[0,"&qopf;"],[0,"&ropf;"],[0,"&sopf;"],[0,"&topf;"],[0,"&uopf;"],[0,"&vopf;"],[0,"&wopf;"],[0,"&xopf;"],[0,"&yopf;"],[0,"&zopf;"]]))}],[8906,"&fflig;"],[0,"&filig;"],[0,"&fllig;"],[0,"&ffilig;"],[0,"&ffllig;"]]));var He={};(function(t){Object.defineProperty(t,"__esModule",{value:!0}),t.escapeText=t.escapeAttribute=t.escapeUTF8=t.escape=t.encodeXML=t.getCodePoint=t.xmlReplacer=void 0,t.xmlReplacer=/["&'<>$\x80-\uFFFF]/g;var e=new Map([[34,"&quot;"],[38,"&amp;"],[39,"&apos;"],[60,"&lt;"],[62,"&gt;"]]);t.getCodePoint=String.prototype.codePointAt!=null?function(r,a){return r.codePointAt(a)}:function(r,a){return (r.charCodeAt(a)&64512)===55296?(r.charCodeAt(a)-55296)*1024+r.charCodeAt(a+1)-56320+65536:r.charCodeAt(a)};function u(r){for(var a="",i=0,l;(l=t.xmlReplacer.exec(r))!==null;){var c=l.index,d=r.charCodeAt(c),f=e.get(d);f!==void 0?(a+=r.substring(i,c)+f,i=c+1):(a+="".concat(r.substring(i,c),"&#x").concat((0, t.getCodePoint)(r,c).toString(16),";"),i=t.xmlReplacer.lastIndex+=+((d&64512)===55296));}return a+r.substr(i)}t.encodeXML=u,t.escape=u;function n(r,a){return function(l){for(var c,d=0,f="";c=r.exec(l);)d!==c.index&&(f+=l.substring(d,c.index)),f+=a.get(c[0].charCodeAt(0)),d=c.index+1;return f+l.substring(d)}}t.escapeUTF8=n(/[&<>'"]/g,e),t.escapeAttribute=n(/["&\u00A0]/g,new Map([[34,"&quot;"],[38,"&amp;"],[160,"&nbsp;"]])),t.escapeText=n(/[&<>\u00A0]/g,new Map([[38,"&amp;"],[60,"&lt;"],[62,"&gt;"],[160,"&nbsp;"]]));})(He);var ur=Xs&&Xs.__importDefault||function(t){return t&&t.__esModule?t:{default:t}};Object.defineProperty(pe$1,"__esModule",{value:!0});pe$1.encodeNonAsciiHTML=pe$1.encodeHTML=void 0;var tr=ur(xu),Tt$1=He,nr=/[\t\n!-,./:-@[-`\f{-}$\x80-\uFFFF]/g;function rr(t){return Ct$2(nr,t)}pe$1.encodeHTML=rr;function ar(t){return Ct$2(Tt$1.xmlReplacer,t)}pe$1.encodeNonAsciiHTML=ar;function Ct$2(t,e){for(var u="",n=0,r;(r=t.exec(e))!==null;){var a=r.index;u+=e.substring(n,a);var i=e.charCodeAt(a),l=tr.default.get(i);if(typeof l=="object"){if(a+1<e.length){var c=e.charCodeAt(a+1),d=typeof l.n=="number"?l.n===c?l.o:void 0:l.n.get(c);if(d!==void 0){u+=d,n=t.lastIndex+=1;continue}}l=l.v;}if(l!==void 0)u+=l,n=a+1;else {var f=(0, Tt$1.getCodePoint)(e,a);u+="&#x".concat(f.toString(16),";"),n=t.lastIndex+=+(f!==i);}}return u+e.substr(n)}(function(t){Object.defineProperty(t,"__esModule",{value:!0}),t.decodeXMLStrict=t.decodeHTML5Strict=t.decodeHTML4Strict=t.decodeHTML5=t.decodeHTML4=t.decodeHTMLAttribute=t.decodeHTMLStrict=t.decodeHTML=t.decodeXML=t.DecodingMode=t.EntityDecoder=t.encodeHTML5=t.encodeHTML4=t.encodeNonAsciiHTML=t.encodeHTML=t.escapeText=t.escapeAttribute=t.escapeUTF8=t.escape=t.encodeXML=t.encode=t.decodeStrict=t.decode=t.EncodingMode=t.EntityLevel=void 0;var e=we$1,u=pe$1,n=He,r;(function(s){s[s.XML=0]="XML",s[s.HTML=1]="HTML";})(r=t.EntityLevel||(t.EntityLevel={}));var a;(function(s){s[s.UTF8=0]="UTF8",s[s.ASCII=1]="ASCII",s[s.Extensive=2]="Extensive",s[s.Attribute=3]="Attribute",s[s.Text=4]="Text";})(a=t.EncodingMode||(t.EncodingMode={}));function i(s,o){o===void 0&&(o=r.XML);var D=typeof o=="number"?o:o.level;if(D===r.HTML){var E=typeof o=="object"?o.mode:void 0;return (0, e.decodeHTML)(s,E)}return (0, e.decodeXML)(s)}t.decode=i;function l(s,o){var D;o===void 0&&(o=r.XML);var E=typeof o=="number"?{level:o}:o;return (D=E.mode)!==null&&D!==void 0||(E.mode=e.DecodingMode.Strict),i(s,E)}t.decodeStrict=l;function c(s,o){o===void 0&&(o=r.XML);var D=typeof o=="number"?{level:o}:o;return D.mode===a.UTF8?(0, n.escapeUTF8)(s):D.mode===a.Attribute?(0, n.escapeAttribute)(s):D.mode===a.Text?(0, n.escapeText)(s):D.level===r.HTML?D.mode===a.ASCII?(0, u.encodeNonAsciiHTML)(s):(0, u.encodeHTML)(s):(0, n.encodeXML)(s)}t.encode=c;var d=He;Object.defineProperty(t,"encodeXML",{enumerable:!0,get:function(){return d.encodeXML}}),Object.defineProperty(t,"escape",{enumerable:!0,get:function(){return d.escape}}),Object.defineProperty(t,"escapeUTF8",{enumerable:!0,get:function(){return d.escapeUTF8}}),Object.defineProperty(t,"escapeAttribute",{enumerable:!0,get:function(){return d.escapeAttribute}}),Object.defineProperty(t,"escapeText",{enumerable:!0,get:function(){return d.escapeText}});var f=pe$1;Object.defineProperty(t,"encodeHTML",{enumerable:!0,get:function(){return f.encodeHTML}}),Object.defineProperty(t,"encodeNonAsciiHTML",{enumerable:!0,get:function(){return f.encodeNonAsciiHTML}}),Object.defineProperty(t,"encodeHTML4",{enumerable:!0,get:function(){return f.encodeHTML}}),Object.defineProperty(t,"encodeHTML5",{enumerable:!0,get:function(){return f.encodeHTML}});var h=we$1;Object.defineProperty(t,"EntityDecoder",{enumerable:!0,get:function(){return h.EntityDecoder}}),Object.defineProperty(t,"DecodingMode",{enumerable:!0,get:function(){return h.DecodingMode}}),Object.defineProperty(t,"decodeXML",{enumerable:!0,get:function(){return h.decodeXML}}),Object.defineProperty(t,"decodeHTML",{enumerable:!0,get:function(){return h.decodeHTML}}),Object.defineProperty(t,"decodeHTMLStrict",{enumerable:!0,get:function(){return h.decodeHTMLStrict}}),Object.defineProperty(t,"decodeHTMLAttribute",{enumerable:!0,get:function(){return h.decodeHTMLAttribute}}),Object.defineProperty(t,"decodeHTML4",{enumerable:!0,get:function(){return h.decodeHTML}}),Object.defineProperty(t,"decodeHTML5",{enumerable:!0,get:function(){return h.decodeHTML}}),Object.defineProperty(t,"decodeHTML4Strict",{enumerable:!0,get:function(){return h.decodeHTMLStrict}}),Object.defineProperty(t,"decodeHTML5Strict",{enumerable:!0,get:function(){return h.decodeHTMLStrict}}),Object.defineProperty(t,"decodeXMLStrict",{enumerable:!0,get:function(){return h.decodeXML}});})(wt);var me$1={};Object.defineProperty(me$1,"__esModule",{value:!0});me$1.attributeNames=me$1.elementNames=void 0;me$1.elementNames=new Map(["altGlyph","altGlyphDef","altGlyphItem","animateColor","animateMotion","animateTransform","clipPath","feBlend","feColorMatrix","feComponentTransfer","feComposite","feConvolveMatrix","feDiffuseLighting","feDisplacementMap","feDistantLight","feDropShadow","feFlood","feFuncA","feFuncB","feFuncG","feFuncR","feGaussianBlur","feImage","feMerge","feMergeNode","feMorphology","feOffset","fePointLight","feSpecularLighting","feSpotLight","feTile","feTurbulence","foreignObject","glyphRef","linearGradient","radialGradient","textPath"].map(function(t){return [t.toLowerCase(),t]}));me$1.attributeNames=new Map(["definitionURL","attributeName","attributeType","baseFrequency","baseProfile","calcMode","clipPathUnits","diffuseConstant","edgeMode","filterUnits","glyphRef","gradientTransform","gradientUnits","kernelMatrix","kernelUnitLength","keyPoints","keySplines","keyTimes","lengthAdjust","limitingConeAngle","markerHeight","markerUnits","markerWidth","maskContentUnits","maskUnits","numOctaves","pathLength","patternContentUnits","patternTransform","patternUnits","pointsAtX","pointsAtY","pointsAtZ","preserveAlpha","preserveAspectRatio","primitiveUnits","refX","refY","repeatCount","repeatDur","requiredExtensions","requiredFeatures","specularConstant","specularExponent","spreadMethod","startOffset","stdDeviation","stitchTiles","surfaceScale","systemLanguage","tableValues","targetX","targetY","textLength","viewBox","viewTarget","xChannelSelector","yChannelSelector","zoomAndPan"].map(function(t){return [t.toLowerCase(),t]}));var ge$1=Xs&&Xs.__assign||function(){return ge$1=Object.assign||function(t){for(var e,u=1,n=arguments.length;u<n;u++){e=arguments[u];for(var r in e)Object.prototype.hasOwnProperty.call(e,r)&&(t[r]=e[r]);}return t},ge$1.apply(this,arguments)},ir=Xs&&Xs.__createBinding||(Object.create?function(t,e,u,n){n===void 0&&(n=u);var r=Object.getOwnPropertyDescriptor(e,u);(!r||("get"in r?!e.__esModule:r.writable||r.configurable))&&(r={enumerable:!0,get:function(){return e[u]}}),Object.defineProperty(t,n,r);}:function(t,e,u,n){n===void 0&&(n=u),t[n]=e[u];}),sr=Xs&&Xs.__setModuleDefault||(Object.create?function(t,e){Object.defineProperty(t,"default",{enumerable:!0,value:e});}:function(t,e){t.default=e;}),or=Xs&&Xs.__importStar||function(t){if(t&&t.__esModule)return t;var e={};if(t!=null)for(var u in t)u!=="default"&&Object.prototype.hasOwnProperty.call(t,u)&&ir(e,t,u);return sr(e,t),e};Object.defineProperty(Fe,"__esModule",{value:!0});Fe.render=void 0;var ae$1=or(De),ze=wt,kt=me$1,cr=new Set(["style","script","xmp","iframe","noembed","noframes","plaintext","noscript"]);function lr(t){return t.replace(/"/g,"&quot;")}function dr(t,e){var u;if(t){var n=((u=e.encodeEntities)!==null&&u!==void 0?u:e.decodeEntities)===!1?lr:e.xmlMode||e.encodeEntities!=="utf8"?ze.encodeXML:ze.escapeAttribute;return Object.keys(t).map(function(r){var a,i,l=(a=t[r])!==null&&a!==void 0?a:"";return e.xmlMode==="foreign"&&(r=(i=kt.attributeNames.get(r))!==null&&i!==void 0?i:r),!e.emptyAttrs&&!e.xmlMode&&l===""?r:"".concat(r,'="').concat(n(l),'"')}).join(" ")}}var Uu=new Set(["area","base","basefont","br","col","command","embed","frame","hr","img","input","isindex","keygen","link","meta","param","source","track","wbr"]);function Xe(t,e){e===void 0&&(e={});for(var u=("length"in t)?t:[t],n="",r=0;r<u.length;r++)n+=fr(u[r],e);return n}Fe.render=Xe;Fe.default=Xe;function fr(t,e){switch(t.type){case ae$1.Root:return Xe(t.children,e);case ae$1.Doctype:case ae$1.Directive:return gr(t);case ae$1.Comment:return xr(t);case ae$1.CDATA:return Dr(t);case ae$1.Script:case ae$1.Style:case ae$1.Tag:return hr(t,e);case ae$1.Text:return mr(t,e)}}var pr=new Set(["mi","mo","mn","ms","mtext","annotation-xml","foreignObject","desc","title"]),br=new Set(["svg","math"]);function hr(t,e){var u;e.xmlMode==="foreign"&&(t.name=(u=kt.elementNames.get(t.name))!==null&&u!==void 0?u:t.name,t.parent&&pr.has(t.parent.name)&&(e=ge$1(ge$1({},e),{xmlMode:!1}))),!e.xmlMode&&br.has(t.name)&&(e=ge$1(ge$1({},e),{xmlMode:"foreign"}));var n="<".concat(t.name),r=dr(t.attribs,e);return r&&(n+=" ".concat(r)),t.children.length===0&&(e.xmlMode?e.selfClosingTags!==!1:e.selfClosingTags&&Uu.has(t.name))?(e.xmlMode||(n+=" "),n+="/>"):(n+=">",t.children.length>0&&(n+=Xe(t.children,e)),(e.xmlMode||!Uu.has(t.name))&&(n+="</".concat(t.name,">"))),n}function gr(t){return "<".concat(t.data,">")}function mr(t,e){var u,n=t.data||"";return ((u=e.encodeEntities)!==null&&u!==void 0?u:e.decodeEntities)!==!1&&!(!e.xmlMode&&t.parent&&cr.has(t.parent.name))&&(n=e.xmlMode||e.encodeEntities!=="utf8"?(0, ze.encodeXML)(n):(0, ze.escapeText)(n)),n}function Dr(t){return "<![CDATA[".concat(t.children[0].data,"]]>")}function xr(t){return "<!--".concat(t.data,"-->")}var Ar=Xs&&Xs.__importDefault||function(t){return t&&t.__esModule?t:{default:t}};Object.defineProperty(K,"__esModule",{value:!0});K.innerText=K.textContent=K.getText=K.getInnerHTML=K.getOuterHTML=void 0;var ne$1=se,Er=Ar(Fe),yr=De;function Ft(t,e){return (0, Er.default)(t,e)}K.getOuterHTML=Ft;function vr(t,e){return (0, ne$1.hasChildren)(t)?t.children.map(function(u){return Ft(u,e)}).join(""):""}K.getInnerHTML=vr;function Pe(t){return Array.isArray(t)?t.map(Pe).join(""):(0, ne$1.isTag)(t)?t.name==="br"?`
`:Pe(t.children):(0, ne$1.isCDATA)(t)?Pe(t.children):(0, ne$1.isText)(t)?t.data:""}K.getText=Pe;function ru(t){return Array.isArray(t)?t.map(ru).join(""):(0, ne$1.hasChildren)(t)&&!(0, ne$1.isComment)(t)?ru(t.children):(0, ne$1.isText)(t)?t.data:""}K.textContent=ru;function au(t){return Array.isArray(t)?t.map(au).join(""):(0, ne$1.hasChildren)(t)&&(t.type===yr.ElementType.Tag||(0, ne$1.isCDATA)(t))?au(t.children):(0, ne$1.isText)(t)?t.data:""}K.innerText=au;var z={};Object.defineProperty(z,"__esModule",{value:!0});z.prevElementSibling=z.nextElementSibling=z.getName=z.hasAttrib=z.getAttributeValue=z.getSiblings=z.getParent=z.getChildren=void 0;var Au=se;function St$1(t){return (0, Au.hasChildren)(t)?t.children:[]}z.getChildren=St$1;function _t$1(t){return t.parent||null}z.getParent=_t$1;function wr(t){var e,u,n=_t$1(t);if(n!=null)return St$1(n);for(var r=[t],a=t.prev,i=t.next;a!=null;)r.unshift(a),e=a,a=e.prev;for(;i!=null;)r.push(i),u=i,i=u.next;return r}z.getSiblings=wr;function Tr(t,e){var u;return (u=t.attribs)===null||u===void 0?void 0:u[e]}z.getAttributeValue=Tr;function Cr(t,e){return t.attribs!=null&&Object.prototype.hasOwnProperty.call(t.attribs,e)&&t.attribs[e]!=null}z.hasAttrib=Cr;function kr(t){return t.name}z.getName=kr;function Fr(t){for(var e,u=t.next;u!==null&&!(0, Au.isTag)(u);)e=u,u=e.next;return u}z.nextElementSibling=Fr;function Sr(t){for(var e,u=t.prev;u!==null&&!(0, Au.isTag)(u);)e=u,u=e.prev;return u}z.prevElementSibling=Sr;var Z={};Object.defineProperty(Z,"__esModule",{value:!0});Z.prepend=Z.prependChild=Z.append=Z.appendChild=Z.replaceElement=Z.removeElement=void 0;function Se(t){if(t.prev&&(t.prev.next=t.next),t.next&&(t.next.prev=t.prev),t.parent){var e=t.parent.children,u=e.lastIndexOf(t);u>=0&&e.splice(u,1);}t.next=null,t.prev=null,t.parent=null;}Z.removeElement=Se;function _r(t,e){var u=e.prev=t.prev;u&&(u.next=e);var n=e.next=t.next;n&&(n.prev=e);var r=e.parent=t.parent;if(r){var a=r.children;a[a.lastIndexOf(t)]=e,t.parent=null;}}Z.replaceElement=_r;function Ir(t,e){if(Se(e),e.next=null,e.parent=t,t.children.push(e)>1){var u=t.children[t.children.length-2];u.next=e,e.prev=u;}else e.prev=null;}Z.appendChild=Ir;function Nr(t,e){Se(e);var u=t.parent,n=t.next;if(e.next=n,e.prev=t,t.next=e,e.parent=u,n){if(n.prev=e,u){var r=u.children;r.splice(r.lastIndexOf(n),0,e);}}else u&&u.children.push(e);}Z.append=Nr;function Br(t,e){if(Se(e),e.parent=t,e.prev=null,t.children.unshift(e)!==1){var u=t.children[1];u.prev=e,e.next=u;}else e.next=null;}Z.prependChild=Br;function Or(t,e){Se(e);var u=t.parent;if(u){var n=u.children;n.splice(n.indexOf(t),0,e);}t.prev&&(t.prev.next=e),e.parent=u,e.prev=t.prev,e.next=t,t.prev=e;}Z.prepend=Or;var $={};Object.defineProperty($,"__esModule",{value:!0});$.findAll=$.existsOne=$.findOne=$.findOneChild=$.find=$.filter=void 0;var We$1=se;function Lr(t,e,u,n){return u===void 0&&(u=!0),n===void 0&&(n=1/0),It$1(t,Array.isArray(e)?e:[e],u,n)}$.filter=Lr;function It$1(t,e,u,n){for(var r=[],a=[e],i=[0];;){if(i[0]>=a[0].length){if(i.length===1)return r;a.shift(),i.shift();continue}var l=a[0][i[0]++];if(t(l)&&(r.push(l),--n<=0))return r;u&&(0, We$1.hasChildren)(l)&&l.children.length>0&&(i.unshift(0),a.unshift(l.children));}}$.find=It$1;function Rr(t,e){return e.find(t)}$.findOneChild=Rr;function Nt$1(t,e,u){u===void 0&&(u=!0);for(var n=null,r=0;r<e.length&&!n;r++){var a=e[r];if((0, We$1.isTag)(a))t(a)?n=a:u&&a.children.length>0&&(n=Nt$1(t,a.children,!0));else continue}return n}$.findOne=Nt$1;function Bt(t,e){return e.some(function(u){return (0, We$1.isTag)(u)&&(t(u)||Bt(t,u.children))})}$.existsOne=Bt;function Pr(t,e){for(var u=[],n=[e],r=[0];;){if(r[0]>=n[0].length){if(n.length===1)return u;n.shift(),r.shift();continue}var a=n[0][r[0]++];(0, We$1.isTag)(a)&&(t(a)&&u.push(a),a.children.length>0&&(r.unshift(0),n.unshift(a.children)));}}$.findAll=Pr;var Y$1={};Object.defineProperty(Y$1,"__esModule",{value:!0});Y$1.getElementsByTagType=Y$1.getElementsByTagName=Y$1.getElementById=Y$1.getElements=Y$1.testElement=void 0;var de$1=se,Qe=$,je$1={tag_name:function(t){return typeof t=="function"?function(e){return (0, de$1.isTag)(e)&&t(e.name)}:t==="*"?de$1.isTag:function(e){return (0, de$1.isTag)(e)&&e.name===t}},tag_type:function(t){return typeof t=="function"?function(e){return t(e.type)}:function(e){return e.type===t}},tag_contains:function(t){return typeof t=="function"?function(e){return (0, de$1.isText)(e)&&t(e.data)}:function(e){return (0, de$1.isText)(e)&&e.data===t}}};function Ot$1(t,e){return typeof e=="function"?function(u){return (0, de$1.isTag)(u)&&e(u.attribs[t])}:function(u){return (0, de$1.isTag)(u)&&u.attribs[t]===e}}function Mr(t,e){return function(u){return t(u)||e(u)}}function Lt(t){var e=Object.keys(t).map(function(u){var n=t[u];return Object.prototype.hasOwnProperty.call(je$1,u)?je$1[u](n):Ot$1(u,n)});return e.length===0?null:e.reduce(Mr)}function qr(t,e){var u=Lt(t);return u?u(e):!0}Y$1.testElement=qr;function Ur(t,e,u,n){n===void 0&&(n=1/0);var r=Lt(t);return r?(0, Qe.filter)(r,e,u,n):[]}Y$1.getElements=Ur;function Hr(t,e,u){return u===void 0&&(u=!0),Array.isArray(e)||(e=[e]),(0, Qe.findOne)(Ot$1("id",t),e,u)}Y$1.getElementById=Hr;function zr(t,e,u,n){return u===void 0&&(u=!0),n===void 0&&(n=1/0),(0, Qe.filter)(je$1.tag_name(t),e,u,n)}Y$1.getElementsByTagName=zr;function jr(t,e,u,n){return u===void 0&&(u=!0),n===void 0&&(n=1/0),(0, Qe.filter)(je$1.tag_type(t),e,u,n)}Y$1.getElementsByTagType=jr;var Rt$1={};(function(t){Object.defineProperty(t,"__esModule",{value:!0}),t.uniqueSort=t.compareDocumentPosition=t.DocumentPosition=t.removeSubsets=void 0;var e=se;function u(i){for(var l=i.length;--l>=0;){var c=i[l];if(l>0&&i.lastIndexOf(c,l-1)>=0){i.splice(l,1);continue}for(var d=c.parent;d;d=d.parent)if(i.includes(d)){i.splice(l,1);break}}return i}t.removeSubsets=u;var n;(function(i){i[i.DISCONNECTED=1]="DISCONNECTED",i[i.PRECEDING=2]="PRECEDING",i[i.FOLLOWING=4]="FOLLOWING",i[i.CONTAINS=8]="CONTAINS",i[i.CONTAINED_BY=16]="CONTAINED_BY";})(n=t.DocumentPosition||(t.DocumentPosition={}));function r(i,l){var c=[],d=[];if(i===l)return 0;for(var f=(0, e.hasChildren)(i)?i:i.parent;f;)c.unshift(f),f=f.parent;for(f=(0, e.hasChildren)(l)?l:l.parent;f;)d.unshift(f),f=f.parent;for(var h=Math.min(c.length,d.length),s=0;s<h&&c[s]===d[s];)s++;if(s===0)return n.DISCONNECTED;var o=c[s-1],D=o.children,E=c[s],y=d[s];return D.indexOf(E)>D.indexOf(y)?o===l?n.FOLLOWING|n.CONTAINED_BY:n.FOLLOWING:o===i?n.PRECEDING|n.CONTAINS:n.PRECEDING}t.compareDocumentPosition=r;function a(i){return i=i.filter(function(l,c,d){return !d.includes(l,c+1)}),i.sort(function(l,c){var d=r(l,c);return d&n.PRECEDING?-1:d&n.FOLLOWING?1:0}),i}t.uniqueSort=a;})(Rt$1);var Ke={};Object.defineProperty(Ke,"__esModule",{value:!0});Ke.getFeed=void 0;var $r=K,_e$1=Y$1;function Gr(t){var e=$e(Qr,t);return e?e.name==="feed"?Vr(e):Zr(e):null}Ke.getFeed=Gr;function Vr(t){var e,u=t.children,n={type:"atom",items:(0, _e$1.getElementsByTagName)("entry",u).map(function(i){var l,c=i.children,d={media:Pt$1(c)};V(d,"id","id",c),V(d,"title","title",c);var f=(l=$e("link",c))===null||l===void 0?void 0:l.attribs.href;f&&(d.link=f);var h=oe$1("summary",c)||oe$1("content",c);h&&(d.description=h);var s=oe$1("updated",c);return s&&(d.pubDate=new Date(s)),d})};V(n,"id","id",u),V(n,"title","title",u);var r=(e=$e("link",u))===null||e===void 0?void 0:e.attribs.href;r&&(n.link=r),V(n,"description","subtitle",u);var a=oe$1("updated",u);return a&&(n.updated=new Date(a)),V(n,"author","email",u,!0),n}function Zr(t){var e,u,n=(u=(e=$e("channel",t.children))===null||e===void 0?void 0:e.children)!==null&&u!==void 0?u:[],r={type:t.name.substr(0,3),id:"",items:(0, _e$1.getElementsByTagName)("item",t.children).map(function(i){var l=i.children,c={media:Pt$1(l)};V(c,"id","guid",l),V(c,"title","title",l),V(c,"link","link",l),V(c,"description","description",l);var d=oe$1("pubDate",l)||oe$1("dc:date",l);return d&&(c.pubDate=new Date(d)),c})};V(r,"title","title",n),V(r,"link","link",n),V(r,"description","description",n);var a=oe$1("lastBuildDate",n);return a&&(r.updated=new Date(a)),V(r,"author","managingEditor",n,!0),r}var Xr=["url","type","lang"],Wr=["fileSize","bitrate","framerate","samplingrate","channels","duration","height","width"];function Pt$1(t){return (0, _e$1.getElementsByTagName)("media:content",t).map(function(e){for(var u=e.attribs,n={medium:u.medium,isDefault:!!u.isDefault},r=0,a=Xr;r<a.length;r++){var i=a[r];u[i]&&(n[i]=u[i]);}for(var l=0,c=Wr;l<c.length;l++){var i=c[l];u[i]&&(n[i]=parseInt(u[i],10));}return u.expression&&(n.expression=u.expression),n})}function $e(t,e){return (0, _e$1.getElementsByTagName)(t,e,!0,1)[0]}function oe$1(t,e,u){return u===void 0&&(u=!1),(0, $r.textContent)((0, _e$1.getElementsByTagName)(t,e,u,1)).trim()}function V(t,e,u,n,r){r===void 0&&(r=!1);var a=oe$1(u,n,r);a&&(t[e]=a);}function Qr(t){return t==="rss"||t==="feed"||t==="rdf:RDF"}(function(t){var e=Xs&&Xs.__createBinding||(Object.create?function(r,a,i,l){l===void 0&&(l=i);var c=Object.getOwnPropertyDescriptor(a,i);(!c||("get"in c?!a.__esModule:c.writable||c.configurable))&&(c={enumerable:!0,get:function(){return a[i]}}),Object.defineProperty(r,l,c);}:function(r,a,i,l){l===void 0&&(l=i),r[l]=a[i];}),u=Xs&&Xs.__exportStar||function(r,a){for(var i in r)i!=="default"&&!Object.prototype.hasOwnProperty.call(a,i)&&e(a,r,i);};Object.defineProperty(t,"__esModule",{value:!0}),t.hasChildren=t.isDocument=t.isComment=t.isText=t.isCDATA=t.isTag=void 0,u(K,t),u(z,t),u(Z,t),u($,t),u(Y$1,t),u(Rt$1,t),u(Ke,t);var n=se;Object.defineProperty(t,"isTag",{enumerable:!0,get:function(){return n.isTag}}),Object.defineProperty(t,"isCDATA",{enumerable:!0,get:function(){return n.isCDATA}}),Object.defineProperty(t,"isText",{enumerable:!0,get:function(){return n.isText}}),Object.defineProperty(t,"isComment",{enumerable:!0,get:function(){return n.isComment}}),Object.defineProperty(t,"isDocument",{enumerable:!0,get:function(){return n.isDocument}}),Object.defineProperty(t,"hasChildren",{enumerable:!0,get:function(){return n.hasChildren}});})(Re);(function(t){var e=Xs&&Xs.__createBinding||(Object.create?function(v,w,C,S){S===void 0&&(S=C);var _=Object.getOwnPropertyDescriptor(w,C);(!_||("get"in _?!w.__esModule:_.writable||_.configurable))&&(_={enumerable:!0,get:function(){return w[C]}}),Object.defineProperty(v,S,_);}:function(v,w,C,S){S===void 0&&(S=C),v[S]=w[C];}),u=Xs&&Xs.__setModuleDefault||(Object.create?function(v,w){Object.defineProperty(v,"default",{enumerable:!0,value:w});}:function(v,w){v.default=w;}),n=Xs&&Xs.__importStar||function(v){if(v&&v.__esModule)return v;var w={};if(v!=null)for(var C in v)C!=="default"&&Object.prototype.hasOwnProperty.call(v,C)&&e(w,v,C);return u(w,v),w},r=Xs&&Xs.__importDefault||function(v){return v&&v.__esModule?v:{default:v}};Object.defineProperty(t,"__esModule",{value:!0}),t.DomUtils=t.parseFeed=t.getFeed=t.ElementType=t.Tokenizer=t.createDomStream=t.parseDOM=t.parseDocument=t.DefaultHandler=t.DomHandler=t.Parser=void 0;var a=ve,i=ve;Object.defineProperty(t,"Parser",{enumerable:!0,get:function(){return i.Parser}});var l=se,c=se;Object.defineProperty(t,"DomHandler",{enumerable:!0,get:function(){return c.DomHandler}}),Object.defineProperty(t,"DefaultHandler",{enumerable:!0,get:function(){return c.DomHandler}});function d(v,w){var C=new l.DomHandler(void 0,w);return new a.Parser(C,w).end(v),C.root}t.parseDocument=d;function f(v,w){return d(v,w).children}t.parseDOM=f;function h(v,w,C){var S=new l.DomHandler(v,w,C);return new a.Parser(S,w)}t.createDomStream=h;var s=bu;Object.defineProperty(t,"Tokenizer",{enumerable:!0,get:function(){return r(s).default}}),t.ElementType=n(De);var o=Re,D=Re;Object.defineProperty(t,"getFeed",{enumerable:!0,get:function(){return D.getFeed}});var E={xmlMode:!0};function y(v,w){return w===void 0&&(w=E),(0, o.getFeed)(f(v,w))}t.parseFeed=y,t.DomUtils=n(Re);})(dt$2);var Kr=t=>{if(typeof t!="string")throw new TypeError("Expected a string");return t.replace(/[|\\{}()[\]^$+*?.]/g,"\\$&").replace(/-/g,"\\x2d")},Eu={};Object.defineProperty(Eu,"__esModule",{value:!0});/*!
 * is-plain-object <https://github.com/jonschlinkert/is-plain-object>
 *
 * Copyright (c) 2014-2017, Jon Schlinkert.
 * Released under the MIT License.
 */function Hu(t){return Object.prototype.toString.call(t)==="[object Object]"}function Yr(t){var e,u;return Hu(t)===!1?!1:(e=t.constructor,e===void 0?!0:(u=e.prototype,!(Hu(u)===!1||u.hasOwnProperty("isPrototypeOf")===!1)))}Eu.isPlainObject=Yr;var Mt$1={exports:{}};(function(t){(function(e,u){t.exports?t.exports=u():e.parseSrcset=u();})(Xs,function(){return function(e){function u(S){return S===" "||S==="	"||S===`
`||S==="\f"||S==="\r"}function n(S){var _,q=S.exec(e.substring(y));if(q)return _=q[0],y+=_.length,_}for(var r=e.length,a=/^[ \t\n\r\u000c]+/,i=/^[, \t\n\r\u000c]+/,l=/^[^ \t\n\r\u000c]+/,c=/[,]+$/,d=/^\d+$/,f=/^-?(?:[0-9]+|[0-9]*\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/,h,s,o,D,E,y=0,v=[];;){if(n(i),y>=r)return v;h=n(l),s=[],h.slice(-1)===","?(h=h.replace(c,""),C()):w();}function w(){for(n(a),o="",D="in descriptor";;){if(E=e.charAt(y),D==="in descriptor")if(u(E))o&&(s.push(o),o="",D="after descriptor");else if(E===","){y+=1,o&&s.push(o),C();return}else if(E==="(")o=o+E,D="in parens";else if(E===""){o&&s.push(o),C();return}else o=o+E;else if(D==="in parens")if(E===")")o=o+E,D="in descriptor";else if(E===""){s.push(o),C();return}else o=o+E;else if(D==="after descriptor"&&!u(E))if(E===""){C();return}else D="in descriptor",y-=1;y+=1;}}function C(){var S=!1,_,q,j,G,J={},W,b,x,A,k;for(G=0;G<s.length;G++)W=s[G],b=W[W.length-1],x=W.substring(0,W.length-1),A=parseInt(x,10),k=parseFloat(x),d.test(x)&&b==="w"?((_||q)&&(S=!0),A===0?S=!0:_=A):f.test(x)&&b==="x"?((_||q||j)&&(S=!0),k<0?S=!0:q=k):d.test(x)&&b==="h"?((j||q)&&(S=!0),A===0?S=!0:j=A):S=!0;S?console&&console.log&&console.log("Invalid srcset descriptor found in '"+e+"' at '"+W+"'."):(J.url=h,_&&(J.w=_),q&&(J.d=q),j&&(J.h=j),v.push(J));}}});})(Mt$1);var Jr=Mt$1.exports;const ea=dt$2,zu=Kr,{isPlainObject:ua}=Eu,ju=Vr$1,ta=Jr,{parse:na}=postcss,ra=["img","audio","video","picture","svg","object","map","iframe","embed"],aa=["script","style"];function Ae$1(t,e){t&&Object.keys(t).forEach(function(u){e(t[u],u);});}function ie$1(t,e){return {}.hasOwnProperty.call(t,e)}function $u(t,e){const u=[];return Ae$1(t,function(n){e(n)&&u.push(n);}),u}function ia(t){for(const e in t)if(ie$1(t,e))return !1;return !0}function sa(t){return t.map(function(e){if(!e.url)throw new Error("URL missing");return e.url+(e.w?` ${e.w}w`:"")+(e.h?` ${e.h}h`:"")+(e.d?` ${e.d}x`:"")}).join(", ")}var oa=Te$1;const ca=/^[^\0\t\n\f\r /<=>]+$/;function Te$1(t,e,u){if(t==null)return "";typeof t=="number"&&(t=t.toString());let n="",r="";function a(p,m){const g=this;this.tag=p,this.attribs=m||{},this.tagPosition=n.length,this.text="",this.mediaChildren=[],this.updateParentNodeText=function(){if(y.length){const T=y[y.length-1];T.text+=g.text;}},this.updateParentNodeMediaChildren=function(){y.length&&ra.includes(this.tag)&&y[y.length-1].mediaChildren.push(this.tag);};}e=Object.assign({},Te$1.defaults,e),e.parser=Object.assign({},la,e.parser);const i=function(p){return e.allowedTags===!1||(e.allowedTags||[]).indexOf(p)>-1};aa.forEach(function(p){i(p)&&!e.allowVulnerableTags&&console.warn(`

⚠️ Your \`allowedTags\` option includes, \`${p}\`, which is inherently
vulnerable to XSS attacks. Please remove it from \`allowedTags\`.
Or, to disable this warning, add the \`allowVulnerableTags\` option
and ensure you are accounting for this risk.

`);});const l=e.nonTextTags||["script","style","textarea","option"];let c,d;e.allowedAttributes&&(c={},d={},Ae$1(e.allowedAttributes,function(p,m){c[m]=[];const g=[];p.forEach(function(T){typeof T=="string"&&T.indexOf("*")>=0?g.push(zu(T).replace(/\\\*/g,".*")):c[m].push(T);}),g.length&&(d[m]=new RegExp("^("+g.join("|")+")$"));}));const f={},h={},s={};Ae$1(e.allowedClasses,function(p,m){if(c&&(ie$1(c,m)||(c[m]=[]),c[m].push("class")),f[m]=p,Array.isArray(p)){const g=[];f[m]=[],s[m]=[],p.forEach(function(T){typeof T=="string"&&T.indexOf("*")>=0?g.push(zu(T).replace(/\\\*/g,".*")):T instanceof RegExp?s[m].push(T):f[m].push(T);}),g.length&&(h[m]=new RegExp("^("+g.join("|")+")$"));}});const o={};let D;Ae$1(e.transformTags,function(p,m){let g;typeof p=="function"?g=p:typeof p=="string"&&(g=Te$1.simpleTransform(p)),m==="*"?D=g:o[m]=g;});let E,y,v,w,C,S,_=!1;j();const q=new ea.Parser({onopentag:function(p,m){if(e.enforceHtmlBoundary&&p==="html"&&j(),C){S++;return}const g=new a(p,m);y.push(g);let T=!1;const H=!!g.text;let U;if(ie$1(o,p)&&(U=o[p](p,m),g.attribs=m=U.attribs,U.text!==void 0&&(g.innerText=U.text),p!==U.tagName&&(g.name=p=U.tagName,w[E]=U.tagName)),D&&(U=D(p,m),g.attribs=m=U.attribs,p!==U.tagName&&(g.name=p=U.tagName,w[E]=U.tagName)),(!i(p)||e.disallowedTagsMode==="recursiveEscape"&&!ia(v)||e.nestingLimit!=null&&E>=e.nestingLimit)&&(T=!0,v[E]=!0,(e.disallowedTagsMode==="discard"||e.disallowedTagsMode==="completelyDiscard")&&l.indexOf(p)!==-1&&(C=!0,S=1),v[E]=!0),E++,T){if(e.disallowedTagsMode==="discard"||e.disallowedTagsMode==="completelyDiscard")return;r=n,n="";}n+="<"+p,p==="script"&&(e.allowedScriptHostnames||e.allowedScriptDomains)&&(g.innerText=""),(!c||ie$1(c,p)||c["*"])&&Ae$1(m,function(M,O){if(!ca.test(O)){delete g.attribs[O];return}if(M===""&&!e.allowedEmptyAttributes.includes(O)&&(e.nonBooleanAttributes.includes(O)||e.nonBooleanAttributes.includes("*"))){delete g.attribs[O];return}let Ye=!1;if(!c||ie$1(c,p)&&c[p].indexOf(O)!==-1||c["*"]&&c["*"].indexOf(O)!==-1||ie$1(d,p)&&d[p].test(O)||d["*"]&&d["*"].test(O))Ye=!0;else if(c&&c[p]){for(const N of c[p])if(ua(N)&&N.name&&N.name===O){Ye=!0;let B="";if(N.multiple===!0){const le=M.split(" ");for(const re of le)N.values.indexOf(re)!==-1&&(B===""?B=re:B+=" "+re);}else N.values.indexOf(M)>=0&&(B=M);M=B;}}if(Ye){if(e.allowedSchemesAppliedToAttributes.indexOf(O)!==-1&&J(p,M)){delete g.attribs[O];return}if(p==="script"&&O==="src"){let N=!0;try{const B=W(M);if(e.allowedScriptHostnames||e.allowedScriptDomains){const le=(e.allowedScriptHostnames||[]).find(function(ee){return ee===B.url.hostname}),re=(e.allowedScriptDomains||[]).find(function(ee){return B.url.hostname===ee||B.url.hostname.endsWith(`.${ee}`)});N=le||re;}}catch{N=!1;}if(!N){delete g.attribs[O];return}}if(p==="iframe"&&O==="src"){let N=!0;try{const B=W(M);if(B.isRelativeUrl)N=ie$1(e,"allowIframeRelativeUrls")?e.allowIframeRelativeUrls:!e.allowedIframeHostnames&&!e.allowedIframeDomains;else if(e.allowedIframeHostnames||e.allowedIframeDomains){const le=(e.allowedIframeHostnames||[]).find(function(ee){return ee===B.url.hostname}),re=(e.allowedIframeDomains||[]).find(function(ee){return B.url.hostname===ee||B.url.hostname.endsWith(`.${ee}`)});N=le||re;}}catch{N=!1;}if(!N){delete g.attribs[O];return}}if(O==="srcset")try{let N=ta(M);if(N.forEach(function(B){J("srcset",B.url)&&(B.evil=!0);}),N=$u(N,function(B){return !B.evil}),N.length)M=sa($u(N,function(B){return !B.evil})),g.attribs[O]=M;else {delete g.attribs[O];return}}catch{delete g.attribs[O];return}if(O==="class"){const N=f[p],B=f["*"],le=h[p],re=s[p],ee=h["*"],yu=[le,ee].concat(re).filter(function(qt){return qt});if(N&&B?M=k(M,ju(N,B),yu):M=k(M,N||B,yu),!M.length){delete g.attribs[O];return}}if(O==="style"){if(e.parseStyleAttributes)try{const N=na(p+" {"+M+"}",{map:!1}),B=b(N,e.allowedStyles);if(M=x(B),M.length===0){delete g.attribs[O];return}}catch{typeof window<"u"&&console.warn('Failed to parse "'+p+" {"+M+`}", If you're running this in a browser, we recommend to disable style parsing: options.parseStyleAttributes: false, since this only works in a node environment due to a postcss dependency, More info: https://github.com/apostrophecms/sanitize-html/issues/547`),delete g.attribs[O];return}else if(e.allowedStyles)throw new Error("allowedStyles option cannot be used together with parseStyleAttributes: false.")}n+=" "+O,M&&M.length?n+='="'+G(M,!0)+'"':e.allowedEmptyAttributes.includes(O)&&(n+='=""');}else delete g.attribs[O];}),e.selfClosing.indexOf(p)!==-1?n+=" />":(n+=">",g.innerText&&!H&&!e.textFilter&&(n+=G(g.innerText),_=!0)),T&&(n=r+G(n),r="");},ontext:function(p){if(C)return;const m=y[y.length-1];let g;if(m&&(g=m.tag,p=m.innerText!==void 0?m.innerText:p),e.disallowedTagsMode==="completelyDiscard"&&!i(g))p="";else if((e.disallowedTagsMode==="discard"||e.disallowedTagsMode==="completelyDiscard")&&(g==="script"||g==="style"))n+=p;else {const T=G(p,!1);e.textFilter&&!_?n+=e.textFilter(T,g):_||(n+=T);}if(y.length){const T=y[y.length-1];T.text+=p;}},onclosetag:function(p,m){if(C)if(S--,!S)C=!1;else return;const g=y.pop();if(!g)return;if(g.tag!==p){y.push(g);return}C=e.enforceHtmlBoundary?p==="html":!1,E--;const T=v[E];if(T){if(delete v[E],e.disallowedTagsMode==="discard"||e.disallowedTagsMode==="completelyDiscard"){g.updateParentNodeText();return}r=n,n="";}if(w[E]&&(p=w[E],delete w[E]),e.exclusiveFilter&&e.exclusiveFilter(g)){n=n.substr(0,g.tagPosition);return}if(g.updateParentNodeMediaChildren(),g.updateParentNodeText(),e.selfClosing.indexOf(p)!==-1||m&&!i(p)&&["escape","recursiveEscape"].indexOf(e.disallowedTagsMode)>=0){T&&(n=r,r="");return}n+="</"+p+">",T&&(n=r+G(n),r=""),_=!1;}},e.parser);return q.write(t),q.end(),n;function j(){n="",E=0,y=[],v={},w={},C=!1,S=0;}function G(p,m){return typeof p!="string"&&(p=p+""),e.parser.decodeEntities&&(p=p.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),m&&(p=p.replace(/"/g,"&quot;"))),p=p.replace(/&(?![a-zA-Z0-9#]{1,20};)/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),m&&(p=p.replace(/"/g,"&quot;")),p}function J(p,m){for(m=m.replace(/[\x00-\x20]+/g,"");;){const H=m.indexOf("<!--");if(H===-1)break;const U=m.indexOf("-->",H+4);if(U===-1)break;m=m.substring(0,H)+m.substring(U+3);}const g=m.match(/^([a-zA-Z][a-zA-Z0-9.\-+]*):/);if(!g)return m.match(/^[/\\]{2}/)?!e.allowProtocolRelative:!1;const T=g[1].toLowerCase();return ie$1(e.allowedSchemesByTag,p)?e.allowedSchemesByTag[p].indexOf(T)===-1:!e.allowedSchemes||e.allowedSchemes.indexOf(T)===-1}function W(p){if(p=p.replace(/^(\w+:)?\s*[\\/]\s*[\\/]/,"$1//"),p.startsWith("relative:"))throw new Error("relative: exploit attempt");let m="relative://relative-site";for(let H=0;H<100;H++)m+=`/${H}`;const g=new URL(p,m);return {isRelativeUrl:g&&g.hostname==="relative-site"&&g.protocol==="relative:",url:g}}function b(p,m){if(!m)return p;const g=p.nodes[0];let T;return m[g.selector]&&m["*"]?T=ju(m[g.selector],m["*"]):T=m[g.selector]||m["*"],T&&(p.nodes[0].nodes=g.nodes.reduce(A(T),[])),p}function x(p){return p.nodes[0].nodes.reduce(function(m,g){return m.push(`${g.prop}:${g.value}${g.important?" !important":""}`),m},[]).join(";")}function A(p){return function(m,g){return ie$1(p,g.prop)&&p[g.prop].some(function(H){return H.test(g.value)})&&m.push(g),m}}function k(p,m,g){return m?(p=p.split(/\s+/),p.filter(function(T){return m.indexOf(T)!==-1||g.some(function(H){return H.test(T)})}).join(" ")):p}}const la={decodeEntities:!0};Te$1.defaults={allowedTags:["address","article","aside","footer","header","h1","h2","h3","h4","h5","h6","hgroup","main","nav","section","blockquote","dd","div","dl","dt","figcaption","figure","hr","li","main","ol","p","pre","ul","a","abbr","b","bdi","bdo","br","cite","code","data","dfn","em","i","kbd","mark","q","rb","rp","rt","rtc","ruby","s","samp","small","span","strong","sub","sup","time","u","var","wbr","caption","col","colgroup","table","tbody","td","tfoot","th","thead","tr"],nonBooleanAttributes:["abbr","accept","accept-charset","accesskey","action","allow","alt","as","autocapitalize","autocomplete","blocking","charset","cite","class","color","cols","colspan","content","contenteditable","coords","crossorigin","data","datetime","decoding","dir","dirname","download","draggable","enctype","enterkeyhint","fetchpriority","for","form","formaction","formenctype","formmethod","formtarget","headers","height","hidden","high","href","hreflang","http-equiv","id","imagesizes","imagesrcset","inputmode","integrity","is","itemid","itemprop","itemref","itemtype","kind","label","lang","list","loading","low","max","maxlength","media","method","min","minlength","name","nonce","optimum","pattern","ping","placeholder","popover","popovertarget","popovertargetaction","poster","preload","referrerpolicy","rel","rows","rowspan","sandbox","scope","shape","size","sizes","slot","span","spellcheck","src","srcdoc","srclang","srcset","start","step","style","tabindex","target","title","translate","type","usemap","value","width","wrap","onauxclick","onafterprint","onbeforematch","onbeforeprint","onbeforeunload","onbeforetoggle","onblur","oncancel","oncanplay","oncanplaythrough","onchange","onclick","onclose","oncontextlost","oncontextmenu","oncontextrestored","oncopy","oncuechange","oncut","ondblclick","ondrag","ondragend","ondragenter","ondragleave","ondragover","ondragstart","ondrop","ondurationchange","onemptied","onended","onerror","onfocus","onformdata","onhashchange","oninput","oninvalid","onkeydown","onkeypress","onkeyup","onlanguagechange","onload","onloadeddata","onloadedmetadata","onloadstart","onmessage","onmessageerror","onmousedown","onmouseenter","onmouseleave","onmousemove","onmouseout","onmouseover","onmouseup","onoffline","ononline","onpagehide","onpageshow","onpaste","onpause","onplay","onplaying","onpopstate","onprogress","onratechange","onreset","onresize","onrejectionhandled","onscroll","onscrollend","onsecuritypolicyviolation","onseeked","onseeking","onselect","onslotchange","onstalled","onstorage","onsubmit","onsuspend","ontimeupdate","ontoggle","onunhandledrejection","onunload","onvolumechange","onwaiting","onwheel"],disallowedTagsMode:"discard",allowedAttributes:{a:["href","name","target"],img:["src","srcset","alt","title","width","height","loading"]},allowedEmptyAttributes:["alt"],selfClosing:["img","br","hr","area","base","basefont","input","link","meta"],allowedSchemes:["http","https","ftp","mailto","tel"],allowedSchemesByTag:{},allowedSchemesAppliedToAttributes:["href","src","cite"],allowProtocolRelative:!0,enforceHtmlBoundary:!1,parseStyleAttributes:!0};Te$1.simpleTransform=function(t,e,u){return u=u===void 0?!0:u,e=e||{},function(n,r){let a;if(u)for(a in e)r[a]=e[a];else r=e;return {tagName:t,attribs:r}}};const da=Hr$1(oa);function Gu(t){return da(t)}const Vu=["!--","!doctype","a","abbr","acronym","address","applet","area","article","aside","audio","b","base","basefont","bdi","bdo","big","blockquote","body","br","button","canvas","caption","center","cite","code","col","colgroup","data","datalist","dd","del","details","dfn","dialog","dir","div","dl","dt","em","embed","fieldset","figcaption","figure","font","footer","form","frame","frameset","h1","h2","h3","h4","h5","h6","head","header","hgroup","hr","html","i","iframe","img","input","ins","kbd","label","legend","li","link","main","map","mark","menu","meta","meter","nav","noframes","noscript","object","ol","optgroup","option","output","p","param","picture","pre","progress","q","rp","rt","ruby","s","samp","script","search","section","select","small","source","span","strike","strong","style","sub","summary","sup","svg","table","tbody","td","template","textarea","tfoot","th","thead","time","title","tr","track","tt","u","ul","var","video","wbr"],fa=["g","defs","use","symbol","rect","circle","ellipse","line","polyline","polygon","path","image","text","tspan","textPath","linearGradient","radialGradient","stop","pattern","clipPath","mask","filter","feBlend","feColorMatrix","feComponentTransfer","feComposite","feConvolveMatrix","feDiffuseLighting","feDisplacementMap","feGaussianBlur","feMerge","feMorphology","feOffset","feSpecularLighting","feTurbulence","feMergeNode","feFuncR","feFuncG","feFuncB","feFuncA","feDistantLight","fePointLight","feSpotLight","feFlood","feTile","animate","animateTransform","animateMotion","mpath","set","view","cursor","foreignObject","desc","title","metadata","switch"],pa=[...Vu,...fa.filter(t=>!Vu.includes(t))],ba={code:'span.svelte-7ddecg div[class*="code_wrap"]{position:relative}span.svelte-7ddecg span.katex{font-size:var(--text-lg);direction:ltr}span.svelte-7ddecg div[class*="code_wrap"] > button{z-index:1;cursor:pointer;border-bottom-left-radius:var(--radius-sm);padding:var(--spacing-md);width:25px;height:25px;position:absolute;right:0}span.svelte-7ddecg .check{opacity:0;z-index:var(--layer-top);transition:opacity 0.2s;background:var(--code-background-fill);color:var(--body-text-color);position:absolute;top:var(--size-1-5);left:var(--size-1-5)}span.svelte-7ddecg p:not(:first-child){margin-top:var(--spacing-xxl)}span.svelte-7ddecg .md-header-anchor{margin-left:-25px;padding-right:8px;line-height:1;color:var(--body-text-color-subdued);opacity:0}span.svelte-7ddecg h1:hover .md-header-anchor,span.svelte-7ddecg h2:hover .md-header-anchor,span.svelte-7ddecg h3:hover .md-header-anchor,span.svelte-7ddecg h4:hover .md-header-anchor,span.svelte-7ddecg h5:hover .md-header-anchor,span.svelte-7ddecg h6:hover .md-header-anchor{opacity:1}span.md.svelte-7ddecg .md-header-anchor > svg{color:var(--body-text-color-subdued)}span.svelte-7ddecg table{word-break:break-word}',map:'{"version":3,"file":"MarkdownCode.svelte","sources":["MarkdownCode.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { afterUpdate, tick, onMount } from \\"svelte\\";\\nimport { create_marked } from \\"./utils\\";\\nimport { sanitize } from \\"@gradio/sanitize\\";\\nimport \\"./prism.css\\";\\nimport { standardHtmlAndSvgTags } from \\"./html-tags\\";\\nexport let chatbot = true;\\nexport let message;\\nexport let sanitize_html = true;\\nexport let latex_delimiters = [];\\nexport let render_markdown = true;\\nexport let line_breaks = true;\\nexport let header_links = false;\\nexport let allow_tags = false;\\nexport let theme_mode = \\"system\\";\\nlet el;\\nlet html;\\nlet katex_loaded = false;\\nconst marked = create_marked({\\n    header_links,\\n    line_breaks,\\n    latex_delimiters: latex_delimiters || []\\n});\\nfunction has_math_syntax(text) {\\n    if (!latex_delimiters || latex_delimiters.length === 0) {\\n        return false;\\n    }\\n    return latex_delimiters.some((delimiter) => text.includes(delimiter.left) && text.includes(delimiter.right));\\n}\\nfunction escapeRegExp(string) {\\n    return string.replace(/[.*+?^${}()|[\\\\]\\\\\\\\]/g, \\"\\\\\\\\$&\\");\\n}\\nfunction escapeTags(content, tagsToEscape) {\\n    if (tagsToEscape === true) {\\n        const tagRegex = /<\\\\/?([a-zA-Z][a-zA-Z0-9-]*)([\\\\s>])/g;\\n        return content.replace(tagRegex, (match, tagName, endChar) => {\\n            if (!standardHtmlAndSvgTags.includes(tagName.toLowerCase())) {\\n                return match.replace(/</g, \\"&lt;\\").replace(/>/g, \\"&gt;\\");\\n            }\\n            return match;\\n        });\\n    }\\n    if (Array.isArray(tagsToEscape)) {\\n        const tagPattern = tagsToEscape.map((tag) => ({\\n            open: new RegExp(`<(${tag})(\\\\\\\\s+[^>]*)?>`, \\"gi\\"),\\n            close: new RegExp(`</(${tag})>`, \\"gi\\")\\n        }));\\n        let result = content;\\n        tagPattern.forEach((pattern) => {\\n            result = result.replace(pattern.open, (match) => match.replace(/</g, \\"&lt;\\").replace(/>/g, \\"&gt;\\"));\\n            result = result.replace(pattern.close, (match) => match.replace(/</g, \\"&lt;\\").replace(/>/g, \\"&gt;\\"));\\n        });\\n        return result;\\n    }\\n    return content;\\n}\\nfunction process_message(value) {\\n    let parsedValue = value;\\n    if (render_markdown) {\\n        const latexBlocks = [];\\n        latex_delimiters.forEach((delimiter, index) => {\\n            const leftDelimiter = escapeRegExp(delimiter.left);\\n            const rightDelimiter = escapeRegExp(delimiter.right);\\n            const regex = new RegExp(`${leftDelimiter}([\\\\\\\\s\\\\\\\\S]+?)${rightDelimiter}`, \\"g\\");\\n            parsedValue = parsedValue.replace(regex, (match, p1) => {\\n                latexBlocks.push(match);\\n                return `%%%LATEX_BLOCK_${latexBlocks.length - 1}%%%`;\\n            });\\n        });\\n        parsedValue = marked.parse(parsedValue);\\n        parsedValue = parsedValue.replace(/%%%LATEX_BLOCK_(\\\\d+)%%%/g, (match, p1) => latexBlocks[parseInt(p1, 10)]);\\n    }\\n    if (allow_tags) {\\n        parsedValue = escapeTags(parsedValue, allow_tags);\\n    }\\n    if (sanitize_html && sanitize) {\\n        parsedValue = sanitize(parsedValue);\\n    }\\n    return parsedValue;\\n}\\n$: if (message && message.trim()) {\\n    html = process_message(message);\\n}\\nelse {\\n    html = \\"\\";\\n}\\nasync function render_html(value) {\\n    if (latex_delimiters.length > 0 && value && has_math_syntax(value)) {\\n        if (!katex_loaded) {\\n            await Promise.all([\\n                import(\\"katex/dist/katex.min.css\\"),\\n                import(\\"katex/contrib/auto-render\\")\\n            ]).then(([, { default: render_math_in_element }]) => {\\n                katex_loaded = true;\\n                render_math_in_element(el, {\\n                    delimiters: latex_delimiters,\\n                    throwOnError: false\\n                });\\n            });\\n        }\\n        else {\\n            const { default: render_math_in_element } = await import(\\"katex/contrib/auto-render\\");\\n            render_math_in_element(el, {\\n                delimiters: latex_delimiters,\\n                throwOnError: false\\n            });\\n        }\\n    }\\n    if (el) {\\n        const mermaidDivs = el.querySelectorAll(\\".mermaid\\");\\n        if (mermaidDivs.length > 0) {\\n            await tick();\\n            const { default: mermaid } = await import(\\"mermaid\\");\\n            mermaid.initialize({\\n                startOnLoad: false,\\n                theme: theme_mode === \\"dark\\" ? \\"dark\\" : \\"default\\",\\n                securityLevel: \\"antiscript\\"\\n            });\\n            await mermaid.run({\\n                nodes: Array.from(mermaidDivs).map((node) => node)\\n            });\\n        }\\n    }\\n}\\nafterUpdate(async () => {\\n    if (el && document.body.contains(el)) {\\n        await render_html(message);\\n    }\\n    else {\\n        console.error(\\"Element is not in the DOM\\");\\n    }\\n});\\n<\/script>\\n\\n<span class:chatbot bind:this={el} class=\\"md\\" class:prose={render_markdown}>\\n\\t{@html html}\\n</span>\\n\\n<style>\\n\\tspan :global(div[class*=\\"code_wrap\\"]) {\\n\\t\\tposition: relative;\\n\\t}\\n\\n\\t/* KaTeX */\\n\\tspan :global(span.katex) {\\n\\t\\tfont-size: var(--text-lg);\\n\\t\\tdirection: ltr;\\n\\t}\\n\\n\\tspan :global(div[class*=\\"code_wrap\\"] > button) {\\n\\t\\tz-index: 1;\\n\\t\\tcursor: pointer;\\n\\t\\tborder-bottom-left-radius: var(--radius-sm);\\n\\t\\tpadding: var(--spacing-md);\\n\\t\\twidth: 25px;\\n\\t\\theight: 25px;\\n\\t\\tposition: absolute;\\n\\t\\tright: 0;\\n\\t}\\n\\n\\tspan :global(.check) {\\n\\t\\topacity: 0;\\n\\t\\tz-index: var(--layer-top);\\n\\t\\ttransition: opacity 0.2s;\\n\\t\\tbackground: var(--code-background-fill);\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\tposition: absolute;\\n\\t\\ttop: var(--size-1-5);\\n\\t\\tleft: var(--size-1-5);\\n\\t}\\n\\n\\tspan :global(p:not(:first-child)) {\\n\\t\\tmargin-top: var(--spacing-xxl);\\n\\t}\\n\\n\\tspan :global(.md-header-anchor) {\\n\\t\\t/* position: absolute; */\\n\\t\\tmargin-left: -25px;\\n\\t\\tpadding-right: 8px;\\n\\t\\tline-height: 1;\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t\\topacity: 0;\\n\\t}\\n\\n\\tspan :global(h1:hover .md-header-anchor),\\n\\tspan :global(h2:hover .md-header-anchor),\\n\\tspan :global(h3:hover .md-header-anchor),\\n\\tspan :global(h4:hover .md-header-anchor),\\n\\tspan :global(h5:hover .md-header-anchor),\\n\\tspan :global(h6:hover .md-header-anchor) {\\n\\t\\topacity: 1;\\n\\t}\\n\\n\\tspan.md :global(.md-header-anchor > svg) {\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t}\\n\\n\\tspan :global(table) {\\n\\t\\tword-break: break-word;\\n\\t}</style>\\n"],"names":[],"mappings":"AA0IC,kBAAI,CAAS,uBAAyB,CACrC,QAAQ,CAAE,QACX,CAGA,kBAAI,CAAS,UAAY,CACxB,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,SAAS,CAAE,GACZ,CAEA,kBAAI,CAAS,gCAAkC,CAC9C,OAAO,CAAE,CAAC,CACV,MAAM,CAAE,OAAO,CACf,yBAAyB,CAAE,IAAI,WAAW,CAAC,CAC3C,OAAO,CAAE,IAAI,YAAY,CAAC,CAC1B,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IAAI,CACZ,QAAQ,CAAE,QAAQ,CAClB,KAAK,CAAE,CACR,CAEA,kBAAI,CAAS,MAAQ,CACpB,OAAO,CAAE,CAAC,CACV,OAAO,CAAE,IAAI,WAAW,CAAC,CACzB,UAAU,CAAE,OAAO,CAAC,IAAI,CACxB,UAAU,CAAE,IAAI,sBAAsB,CAAC,CACvC,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,QAAQ,CAAE,QAAQ,CAClB,GAAG,CAAE,IAAI,UAAU,CAAC,CACpB,IAAI,CAAE,IAAI,UAAU,CACrB,CAEA,kBAAI,CAAS,mBAAqB,CACjC,UAAU,CAAE,IAAI,aAAa,CAC9B,CAEA,kBAAI,CAAS,iBAAmB,CAE/B,WAAW,CAAE,KAAK,CAClB,aAAa,CAAE,GAAG,CAClB,WAAW,CAAE,CAAC,CACd,KAAK,CAAE,IAAI,yBAAyB,CAAC,CACrC,OAAO,CAAE,CACV,CAEA,kBAAI,CAAS,0BAA2B,CACxC,kBAAI,CAAS,0BAA2B,CACxC,kBAAI,CAAS,0BAA2B,CACxC,kBAAI,CAAS,0BAA2B,CACxC,kBAAI,CAAS,0BAA2B,CACxC,kBAAI,CAAS,0BAA4B,CACxC,OAAO,CAAE,CACV,CAEA,IAAI,iBAAG,CAAS,uBAAyB,CACxC,KAAK,CAAE,IAAI,yBAAyB,CACrC,CAEA,kBAAI,CAAS,KAAO,CACnB,UAAU,CAAE,UACb"}'};function Zu(t){return t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}const Aa=create_ssr_component((t,e,u,n)=>{let{chatbot:r=!0}=e,{message:a}=e,{sanitize_html:i=!0}=e,{latex_delimiters:l=[]}=e,{render_markdown:c=!0}=e,{line_breaks:d=!0}=e,{header_links:f=!1}=e,{allow_tags:h=!1}=e,{theme_mode:s="system"}=e,o,D;const E=Vn({header_links:f,line_breaks:d,latex_delimiters:l||[]});function y(w,C){if(C===!0){const S=/<\/?([a-zA-Z][a-zA-Z0-9-]*)([\s>])/g;return w.replace(S,(_,q,j)=>pa.includes(q.toLowerCase())?_:_.replace(/</g,"&lt;").replace(/>/g,"&gt;"))}if(Array.isArray(C)){const S=C.map(q=>({open:new RegExp(`<(${q})(\\s+[^>]*)?>`,"gi"),close:new RegExp(`</(${q})>`,"gi")}));let _=w;return S.forEach(q=>{_=_.replace(q.open,j=>j.replace(/</g,"&lt;").replace(/>/g,"&gt;")),_=_.replace(q.close,j=>j.replace(/</g,"&lt;").replace(/>/g,"&gt;"));}),_}return w}function v(w){let C=w;if(c){const S=[];l.forEach((_,q)=>{const j=Zu(_.left),G=Zu(_.right),J=new RegExp(`${j}([\\s\\S]+?)${G}`,"g");C=C.replace(J,(W,b)=>(S.push(W),`%%%LATEX_BLOCK_${S.length-1}%%%`));}),C=E.parse(C),C=C.replace(/%%%LATEX_BLOCK_(\d+)%%%/g,(_,q)=>S[parseInt(q,10)]);}return h&&(C=y(C,h)),i&&Gu&&(C=Gu(C)),C}return e.chatbot===void 0&&u.chatbot&&r!==void 0&&u.chatbot(r),e.message===void 0&&u.message&&a!==void 0&&u.message(a),e.sanitize_html===void 0&&u.sanitize_html&&i!==void 0&&u.sanitize_html(i),e.latex_delimiters===void 0&&u.latex_delimiters&&l!==void 0&&u.latex_delimiters(l),e.render_markdown===void 0&&u.render_markdown&&c!==void 0&&u.render_markdown(c),e.line_breaks===void 0&&u.line_breaks&&d!==void 0&&u.line_breaks(d),e.header_links===void 0&&u.header_links&&f!==void 0&&u.header_links(f),e.allow_tags===void 0&&u.allow_tags&&h!==void 0&&u.allow_tags(h),e.theme_mode===void 0&&u.theme_mode&&s!==void 0&&u.theme_mode(s),t.css.add(ba),a&&a.trim()?D=v(a):D="",`<span class="${["md svelte-7ddecg",(r?"chatbot":"")+" "+(c?"prose":"")].join(" ").trim()}"${add_attribute("this",o,0)}><!-- HTML_TAG_START -->${D}<!-- HTML_TAG_END --> </span>`});

const F={code:".block.svelte-1svsvh2{position:relative;margin:0;box-shadow:var(--block-shadow);border-width:var(--block-border-width);border-color:var(--block-border-color);border-radius:var(--block-radius);background:var(--block-background-fill);width:100%;line-height:var(--line-sm)}.block.fullscreen.svelte-1svsvh2{border-radius:0}.auto-margin.svelte-1svsvh2{margin-left:auto;margin-right:auto}.block.border_focus.svelte-1svsvh2{border-color:var(--color-accent)}.block.border_contrast.svelte-1svsvh2{border-color:var(--body-text-color)}.padded.svelte-1svsvh2{padding:var(--block-padding)}.hidden.svelte-1svsvh2{display:none}.flex.svelte-1svsvh2{display:flex;flex-direction:column}.hide-container.svelte-1svsvh2:not(.fullscreen){margin:0;box-shadow:none;--block-border-width:0;background:transparent;padding:0;overflow:visible}.resize-handle.svelte-1svsvh2{position:absolute;bottom:0;right:0;width:10px;height:10px;fill:var(--block-border-color);cursor:nwse-resize}.fullscreen.svelte-1svsvh2{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:1000;overflow:auto}.animating.svelte-1svsvh2{animation:svelte-1svsvh2-pop-out 0.1s ease-out forwards}@keyframes svelte-1svsvh2-pop-out{0%{position:fixed;top:var(--start-top);left:var(--start-left);width:var(--start-width);height:var(--start-height);z-index:100}100%{position:fixed;top:0vh;left:0vw;width:100vw;height:100vh;z-index:1000}}.placeholder.svelte-1svsvh2{border-radius:var(--block-radius);border-width:var(--block-border-width);border-color:var(--block-border-color);border-style:dashed}",map:'{"version":3,"file":"Block.svelte","sources":["Block.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let height = void 0;\\nexport let min_height = void 0;\\nexport let max_height = void 0;\\nexport let width = void 0;\\nexport let elem_id = \\"\\";\\nexport let elem_classes = [];\\nexport let variant = \\"solid\\";\\nexport let border_mode = \\"base\\";\\nexport let padding = true;\\nexport let type = \\"normal\\";\\nexport let test_id = void 0;\\nexport let explicit_call = false;\\nexport let container = true;\\nexport let visible = true;\\nexport let allow_overflow = true;\\nexport let overflow_behavior = \\"auto\\";\\nexport let scale = null;\\nexport let min_width = 0;\\nexport let flex = false;\\nexport let resizable = false;\\nexport let rtl = false;\\nexport let fullscreen = false;\\nlet old_fullscreen = fullscreen;\\nlet element;\\nlet tag = type === \\"fieldset\\" ? \\"fieldset\\" : \\"div\\";\\nlet placeholder_height = 0;\\nlet placeholder_width = 0;\\nlet preexpansionBoundingRect = null;\\nfunction handleKeydown(event) {\\n    if (fullscreen && event.key === \\"Escape\\") {\\n        fullscreen = false;\\n    }\\n}\\n$: if (fullscreen !== old_fullscreen) {\\n    old_fullscreen = fullscreen;\\n    if (fullscreen) {\\n        preexpansionBoundingRect = element.getBoundingClientRect();\\n        placeholder_height = element.offsetHeight;\\n        placeholder_width = element.offsetWidth;\\n        window.addEventListener(\\"keydown\\", handleKeydown);\\n    }\\n    else {\\n        preexpansionBoundingRect = null;\\n        window.removeEventListener(\\"keydown\\", handleKeydown);\\n    }\\n}\\nconst get_dimension = (dimension_value) => {\\n    if (dimension_value === void 0) {\\n        return void 0;\\n    }\\n    if (typeof dimension_value === \\"number\\") {\\n        return dimension_value + \\"px\\";\\n    }\\n    else if (typeof dimension_value === \\"string\\") {\\n        return dimension_value;\\n    }\\n};\\n$: if (!visible) {\\n    flex = false;\\n}\\nconst resize = (e) => {\\n    let prevY = e.clientY;\\n    const onMouseMove = (e2) => {\\n        const dy = e2.clientY - prevY;\\n        prevY = e2.clientY;\\n        element.style.height = `${element.offsetHeight + dy}px`;\\n    };\\n    const onMouseUp = () => {\\n        window.removeEventListener(\\"mousemove\\", onMouseMove);\\n        window.removeEventListener(\\"mouseup\\", onMouseUp);\\n    };\\n    window.addEventListener(\\"mousemove\\", onMouseMove);\\n    window.addEventListener(\\"mouseup\\", onMouseUp);\\n};\\n<\/script>\\n\\n<svelte:element\\n\\tthis={tag}\\n\\tbind:this={element}\\n\\tdata-testid={test_id}\\n\\tid={elem_id}\\n\\tclass:hidden={visible === false || visible === \\"hidden\\"}\\n\\tclass=\\"block {elem_classes?.join(\' \') || \'\'}\\"\\n\\tclass:padded={padding}\\n\\tclass:flex\\n\\tclass:border_focus={border_mode === \\"focus\\"}\\n\\tclass:border_contrast={border_mode === \\"contrast\\"}\\n\\tclass:hide-container={!explicit_call && !container}\\n\\tstyle:height={fullscreen ? undefined : get_dimension(height)}\\n\\tstyle:min-height={fullscreen ? undefined : get_dimension(min_height)}\\n\\tstyle:max-height={fullscreen ? undefined : get_dimension(max_height)}\\n\\tclass:fullscreen\\n\\tclass:animating={fullscreen && preexpansionBoundingRect !== null}\\n\\tstyle:--start-top={preexpansionBoundingRect\\n\\t\\t? `${preexpansionBoundingRect.top}px`\\n\\t\\t: \\"0px\\"}\\n\\tstyle:--start-left={preexpansionBoundingRect\\n\\t\\t? `${preexpansionBoundingRect.left}px`\\n\\t\\t: \\"0px\\"}\\n\\tstyle:--start-width={preexpansionBoundingRect\\n\\t\\t? `${preexpansionBoundingRect.width}px`\\n\\t\\t: \\"0px\\"}\\n\\tstyle:--start-height={preexpansionBoundingRect\\n\\t\\t? `${preexpansionBoundingRect.height}px`\\n\\t\\t: \\"0px\\"}\\n\\tstyle:width={fullscreen\\n\\t\\t? undefined\\n\\t\\t: typeof width === \\"number\\"\\n\\t\\t\\t? `calc(min(${width}px, 100%))`\\n\\t\\t\\t: get_dimension(width)}\\n\\tstyle:border-style={variant}\\n\\tstyle:overflow={allow_overflow ? overflow_behavior : \\"hidden\\"}\\n\\tstyle:flex-grow={scale}\\n\\tstyle:min-width={`calc(min(${min_width}px, 100%))`}\\n\\tstyle:border-width=\\"var(--block-border-width)\\"\\n\\tclass:auto-margin={scale === null}\\n\\tdir={rtl ? \\"rtl\\" : \\"ltr\\"}\\n>\\n\\t<slot />\\n\\t{#if resizable}\\n\\t\\t<!-- svelte-ignore a11y-no-static-element-interactions -->\\n\\t\\t<svg\\n\\t\\t\\tclass=\\"resize-handle\\"\\n\\t\\t\\txmlns=\\"http://www.w3.org/2000/svg\\"\\n\\t\\t\\tviewBox=\\"0 0 10 10\\"\\n\\t\\t\\ton:mousedown={resize}\\n\\t\\t>\\n\\t\\t\\t<line x1=\\"1\\" y1=\\"9\\" x2=\\"9\\" y2=\\"1\\" stroke=\\"gray\\" stroke-width=\\"0.5\\" />\\n\\t\\t\\t<line x1=\\"5\\" y1=\\"9\\" x2=\\"9\\" y2=\\"5\\" stroke=\\"gray\\" stroke-width=\\"0.5\\" />\\n\\t\\t</svg>\\n\\t{/if}\\n</svelte:element>\\n{#if fullscreen}\\n\\t<div\\n\\t\\tclass=\\"placeholder\\"\\n\\t\\tstyle:height={placeholder_height + \\"px\\"}\\n\\t\\tstyle:width={placeholder_width + \\"px\\"}\\n\\t></div>\\n{/if}\\n\\n<style>\\n\\t.block {\\n\\t\\tposition: relative;\\n\\t\\tmargin: 0;\\n\\t\\tbox-shadow: var(--block-shadow);\\n\\t\\tborder-width: var(--block-border-width);\\n\\t\\tborder-color: var(--block-border-color);\\n\\t\\tborder-radius: var(--block-radius);\\n\\t\\tbackground: var(--block-background-fill);\\n\\t\\twidth: 100%;\\n\\t\\tline-height: var(--line-sm);\\n\\t}\\n\\t.block.fullscreen {\\n\\t\\tborder-radius: 0;\\n\\t}\\n\\n\\t.auto-margin {\\n\\t\\tmargin-left: auto;\\n\\t\\tmargin-right: auto;\\n\\t}\\n\\n\\t.block.border_focus {\\n\\t\\tborder-color: var(--color-accent);\\n\\t}\\n\\n\\t.block.border_contrast {\\n\\t\\tborder-color: var(--body-text-color);\\n\\t}\\n\\n\\t.padded {\\n\\t\\tpadding: var(--block-padding);\\n\\t}\\n\\n\\t.hidden {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\t.flex {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t}\\n\\t.hide-container:not(.fullscreen) {\\n\\t\\tmargin: 0;\\n\\t\\tbox-shadow: none;\\n\\t\\t--block-border-width: 0;\\n\\t\\tbackground: transparent;\\n\\t\\tpadding: 0;\\n\\t\\toverflow: visible;\\n\\t}\\n\\t.resize-handle {\\n\\t\\tposition: absolute;\\n\\t\\tbottom: 0;\\n\\t\\tright: 0;\\n\\t\\twidth: 10px;\\n\\t\\theight: 10px;\\n\\t\\tfill: var(--block-border-color);\\n\\t\\tcursor: nwse-resize;\\n\\t}\\n\\t.fullscreen {\\n\\t\\tposition: fixed;\\n\\t\\ttop: 0;\\n\\t\\tleft: 0;\\n\\t\\twidth: 100vw;\\n\\t\\theight: 100vh;\\n\\t\\tz-index: 1000;\\n\\t\\toverflow: auto;\\n\\t}\\n\\n\\t.animating {\\n\\t\\tanimation: pop-out 0.1s ease-out forwards;\\n\\t}\\n\\n\\t@keyframes pop-out {\\n\\t\\t0% {\\n\\t\\t\\tposition: fixed;\\n\\t\\t\\ttop: var(--start-top);\\n\\t\\t\\tleft: var(--start-left);\\n\\t\\t\\twidth: var(--start-width);\\n\\t\\t\\theight: var(--start-height);\\n\\t\\t\\tz-index: 100;\\n\\t\\t}\\n\\t\\t100% {\\n\\t\\t\\tposition: fixed;\\n\\t\\t\\ttop: 0vh;\\n\\t\\t\\tleft: 0vw;\\n\\t\\t\\twidth: 100vw;\\n\\t\\t\\theight: 100vh;\\n\\t\\t\\tz-index: 1000;\\n\\t\\t}\\n\\t}\\n\\n\\t.placeholder {\\n\\t\\tborder-radius: var(--block-radius);\\n\\t\\tborder-width: var(--block-border-width);\\n\\t\\tborder-color: var(--block-border-color);\\n\\t\\tborder-style: dashed;\\n\\t}</style>\\n"],"names":[],"mappings":"AA6IC,qBAAO,CACN,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,UAAU,CAAE,IAAI,cAAc,CAAC,CAC/B,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,aAAa,CAAE,IAAI,cAAc,CAAC,CAClC,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,KAAK,CAAE,IAAI,CACX,WAAW,CAAE,IAAI,SAAS,CAC3B,CACA,MAAM,0BAAY,CACjB,aAAa,CAAE,CAChB,CAEA,2BAAa,CACZ,WAAW,CAAE,IAAI,CACjB,YAAY,CAAE,IACf,CAEA,MAAM,4BAAc,CACnB,YAAY,CAAE,IAAI,cAAc,CACjC,CAEA,MAAM,+BAAiB,CACtB,YAAY,CAAE,IAAI,iBAAiB,CACpC,CAEA,sBAAQ,CACP,OAAO,CAAE,IAAI,eAAe,CAC7B,CAEA,sBAAQ,CACP,OAAO,CAAE,IACV,CAEA,oBAAM,CACL,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MACjB,CACA,8BAAe,KAAK,WAAW,CAAE,CAChC,MAAM,CAAE,CAAC,CACT,UAAU,CAAE,IAAI,CAChB,oBAAoB,CAAE,CAAC,CACvB,UAAU,CAAE,WAAW,CACvB,OAAO,CAAE,CAAC,CACV,QAAQ,CAAE,OACX,CACA,6BAAe,CACd,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,KAAK,CAAE,CAAC,CACR,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IAAI,CACZ,IAAI,CAAE,IAAI,oBAAoB,CAAC,CAC/B,MAAM,CAAE,WACT,CACA,0BAAY,CACX,QAAQ,CAAE,KAAK,CACf,GAAG,CAAE,CAAC,CACN,IAAI,CAAE,CAAC,CACP,KAAK,CAAE,KAAK,CACZ,MAAM,CAAE,KAAK,CACb,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,IACX,CAEA,yBAAW,CACV,SAAS,CAAE,sBAAO,CAAC,IAAI,CAAC,QAAQ,CAAC,QAClC,CAEA,WAAW,sBAAQ,CAClB,EAAG,CACF,QAAQ,CAAE,KAAK,CACf,GAAG,CAAE,IAAI,WAAW,CAAC,CACrB,IAAI,CAAE,IAAI,YAAY,CAAC,CACvB,KAAK,CAAE,IAAI,aAAa,CAAC,CACzB,MAAM,CAAE,IAAI,cAAc,CAAC,CAC3B,OAAO,CAAE,GACV,CACA,IAAK,CACJ,QAAQ,CAAE,KAAK,CACf,GAAG,CAAE,GAAG,CACR,IAAI,CAAE,GAAG,CACT,KAAK,CAAE,KAAK,CACZ,MAAM,CAAE,KAAK,CACb,OAAO,CAAE,IACV,CACD,CAEA,2BAAa,CACZ,aAAa,CAAE,IAAI,cAAc,CAAC,CAClC,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,YAAY,CAAE,IAAI,oBAAoB,CAAC,CACvC,YAAY,CAAE,MACf"}'},It=create_ssr_component((o,t,e,n)=>{let{height:l=void 0}=t,{min_height:A=void 0}=t,{max_height:i=void 0}=t,{width:s=void 0}=t,{elem_id:a=""}=t,{elem_classes:d=[]}=t,{variant:g="solid"}=t,{border_mode:h="base"}=t,{padding:p=!0}=t,{type:x="normal"}=t,{test_id:b=void 0}=t,{explicit_call:k=!1}=t,{container:B=!0}=t,{visible:f=!0}=t,{allow_overflow:_=!0}=t,{overflow_behavior:z="auto"}=t,{scale:I=null}=t,{min_width:j=0}=t,{flex:y=!1}=t,{resizable:K=!1}=t,{rtl:L=!1}=t,{fullscreen:C=!1}=t,Z=C,E,V=x==="fieldset"?"fieldset":"div",U=0,T=0,w=null;function S(u){C&&u.key==="Escape"&&(C=!1);}const M=u=>{if(u!==void 0){if(typeof u=="number")return u+"px";if(typeof u=="string")return u}};return t.height===void 0&&e.height&&l!==void 0&&e.height(l),t.min_height===void 0&&e.min_height&&A!==void 0&&e.min_height(A),t.max_height===void 0&&e.max_height&&i!==void 0&&e.max_height(i),t.width===void 0&&e.width&&s!==void 0&&e.width(s),t.elem_id===void 0&&e.elem_id&&a!==void 0&&e.elem_id(a),t.elem_classes===void 0&&e.elem_classes&&d!==void 0&&e.elem_classes(d),t.variant===void 0&&e.variant&&g!==void 0&&e.variant(g),t.border_mode===void 0&&e.border_mode&&h!==void 0&&e.border_mode(h),t.padding===void 0&&e.padding&&p!==void 0&&e.padding(p),t.type===void 0&&e.type&&x!==void 0&&e.type(x),t.test_id===void 0&&e.test_id&&b!==void 0&&e.test_id(b),t.explicit_call===void 0&&e.explicit_call&&k!==void 0&&e.explicit_call(k),t.container===void 0&&e.container&&B!==void 0&&e.container(B),t.visible===void 0&&e.visible&&f!==void 0&&e.visible(f),t.allow_overflow===void 0&&e.allow_overflow&&_!==void 0&&e.allow_overflow(_),t.overflow_behavior===void 0&&e.overflow_behavior&&z!==void 0&&e.overflow_behavior(z),t.scale===void 0&&e.scale&&I!==void 0&&e.scale(I),t.min_width===void 0&&e.min_width&&j!==void 0&&e.min_width(j),t.flex===void 0&&e.flex&&y!==void 0&&e.flex(y),t.resizable===void 0&&e.resizable&&K!==void 0&&e.resizable(K),t.rtl===void 0&&e.rtl&&L!==void 0&&e.rtl(L),t.fullscreen===void 0&&e.fullscreen&&C!==void 0&&e.fullscreen(C),o.css.add(F),C!==Z&&(Z=C,C?(w=E.getBoundingClientRect(),U=E.offsetHeight,T=E.offsetWidth,window.addEventListener("keydown",S)):(w=null,window.removeEventListener("keydown",S))),f||(y=!1),`${(u=>u?`<${V}${add_attribute("data-testid",b,0)}${add_attribute("id",a,0)} class="${["block "+escape(d?.join(" ")||"",!0)+" svelte-1svsvh2",(f===!1||f==="hidden"?"hidden":"")+" "+(p?"padded":"")+" "+(y?"flex":"")+" "+(h==="focus"?"border_focus":"")+" "+(h==="contrast"?"border_contrast":"")+" "+(!k&&!B?"hide-container":"")+" "+(C?"fullscreen":"")+" "+(C&&w!==null?"animating":"")+" "+(I===null?"auto-margin":"")].join(" ").trim()}"${add_attribute("dir",L?"rtl":"ltr",0)}${add_styles({height:C?void 0:M(l),"min-height":C?void 0:M(A),"max-height":C?void 0:M(i),"--start-top":w?`${w.top}px`:"0px","--start-left":w?`${w.left}px`:"0px","--start-width":w?`${w.width}px`:"0px","--start-height":w?`${w.height}px`:"0px",width:C?void 0:typeof s=="number"?`calc(min(${s}px, 100%))`:M(s),"border-style":g,overflow:_?z:"hidden","flex-grow":I,"min-width":`calc(min(${j}px, 100%))`,"border-width":"var(--block-border-width)"})}${add_attribute("this",E,0)}>${is_void(u)?"":`${n.default?n.default({}):""} ${K?' <svg class="resize-handle svelte-1svsvh2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><line x1="1" y1="9" x2="9" y2="1" stroke="gray" stroke-width="0.5"></line><line x1="5" y1="9" x2="9" y2="5" stroke="gray" stroke-width="0.5"></line></svg>':""}`}${is_void(u)?"":`</${u}>`}`:"")(V)} ${C?`<div class="placeholder svelte-1svsvh2"${add_styles({height:U+"px",width:T+"px"})}></div>`:""}`}),J={code:"div.svelte-j9uq24>.md.prose{font-weight:var(--block-info-text-weight);font-size:var(--block-info-text-size);line-height:var(--line-sm)}div.svelte-j9uq24>.md.prose *{color:var(--block-info-text-color)}div.svelte-j9uq24{margin-bottom:var(--spacing-md)}",map:'{"version":3,"file":"Info.svelte","sources":["Info.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { MarkdownCode as Markdown } from \\"@gradio/markdown-code\\";\\nexport let info;\\n<\/script>\\n\\n<div>\\n\\t<Markdown message={info} sanitize_html={true} />\\n</div>\\n\\n<style>\\n\\tdiv > :global(.md.prose) {\\n\\t\\tfont-weight: var(--block-info-text-weight);\\n\\t\\tfont-size: var(--block-info-text-size);\\n\\t\\tline-height: var(--line-sm);\\n\\t}\\n\\tdiv > :global(.md.prose *) {\\n\\t\\tcolor: var(--block-info-text-color);\\n\\t}\\n\\tdiv {\\n\\t\\tmargin-bottom: var(--spacing-md);\\n\\t}</style>\\n"],"names":[],"mappings":"AASC,iBAAG,CAAW,SAAW,CACxB,WAAW,CAAE,IAAI,wBAAwB,CAAC,CAC1C,SAAS,CAAE,IAAI,sBAAsB,CAAC,CACtC,WAAW,CAAE,IAAI,SAAS,CAC3B,CACA,iBAAG,CAAW,WAAa,CAC1B,KAAK,CAAE,IAAI,uBAAuB,CACnC,CACA,iBAAI,CACH,aAAa,CAAE,IAAI,YAAY,CAChC"}'},tt=create_ssr_component((o,t,e,n)=>{let{info:l}=t;return t.info===void 0&&e.info&&l!==void 0&&e.info(l),o.css.add(J),`<div class="svelte-j9uq24">${validate_component(Aa,"Markdown").$$render(o,{message:l,sanitize_html:!0},{},{})} </div>`}),et={code:`span.has-info.svelte-g2oxp3{margin-bottom:var(--spacing-xs)}span.svelte-g2oxp3:not(.has-info){margin-bottom:var(--spacing-lg)}span.svelte-g2oxp3{display:inline-block;position:relative;z-index:var(--layer-4);border:solid var(--block-title-border-width)
			var(--block-title-border-color);border-radius:var(--block-title-radius);background:var(--block-title-background-fill);padding:var(--block-title-padding);color:var(--block-title-text-color);font-weight:var(--block-title-text-weight);font-size:var(--block-title-text-size);line-height:var(--line-sm)}span[dir="rtl"].svelte-g2oxp3{display:block}.hide.svelte-g2oxp3{margin:0;height:0}`,map:'{"version":3,"file":"BlockTitle.svelte","sources":["BlockTitle.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { default as Info } from \\"./Info.svelte\\";\\nexport let show_label = true;\\nexport let info = void 0;\\nexport let rtl = false;\\n<\/script>\\n\\n<span\\n\\tclass:sr-only={!show_label}\\n\\tclass:hide={!show_label}\\n\\tclass:has-info={info != null}\\n\\tdata-testid=\\"block-info\\"\\n\\tdir={rtl ? \\"rtl\\" : \\"ltr\\"}\\n>\\n\\t<slot />\\n</span>\\n{#if info}\\n\\t<Info {info} />\\n{/if}\\n\\n<style>\\n\\tspan.has-info {\\n\\t\\tmargin-bottom: var(--spacing-xs);\\n\\t}\\n\\tspan:not(.has-info) {\\n\\t\\tmargin-bottom: var(--spacing-lg);\\n\\t}\\n\\tspan {\\n\\t\\tdisplay: inline-block;\\n\\t\\tposition: relative;\\n\\t\\tz-index: var(--layer-4);\\n\\t\\tborder: solid var(--block-title-border-width)\\n\\t\\t\\tvar(--block-title-border-color);\\n\\t\\tborder-radius: var(--block-title-radius);\\n\\t\\tbackground: var(--block-title-background-fill);\\n\\t\\tpadding: var(--block-title-padding);\\n\\t\\tcolor: var(--block-title-text-color);\\n\\t\\tfont-weight: var(--block-title-text-weight);\\n\\t\\tfont-size: var(--block-title-text-size);\\n\\t\\tline-height: var(--line-sm);\\n\\t}\\n\\n\\tspan[dir=\\"rtl\\"] {\\n\\t\\tdisplay: block;\\n\\t}\\n\\n\\t.hide {\\n\\t\\tmargin: 0;\\n\\t\\theight: 0;\\n\\t}</style>\\n"],"names":[],"mappings":"AAoBC,IAAI,uBAAU,CACb,aAAa,CAAE,IAAI,YAAY,CAChC,CACA,kBAAI,KAAK,SAAS,CAAE,CACnB,aAAa,CAAE,IAAI,YAAY,CAChC,CACA,kBAAK,CACJ,OAAO,CAAE,YAAY,CACrB,QAAQ,CAAE,QAAQ,CAClB,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,MAAM,CAAE,KAAK,CAAC,IAAI,0BAA0B;AAC9C,GAAG,IAAI,0BAA0B,CAAC,CAChC,aAAa,CAAE,IAAI,oBAAoB,CAAC,CACxC,UAAU,CAAE,IAAI,6BAA6B,CAAC,CAC9C,OAAO,CAAE,IAAI,qBAAqB,CAAC,CACnC,KAAK,CAAE,IAAI,wBAAwB,CAAC,CACpC,WAAW,CAAE,IAAI,yBAAyB,CAAC,CAC3C,SAAS,CAAE,IAAI,uBAAuB,CAAC,CACvC,WAAW,CAAE,IAAI,SAAS,CAC3B,CAEA,IAAI,CAAC,GAAG,CAAC,KAAK,eAAE,CACf,OAAO,CAAE,KACV,CAEA,mBAAM,CACL,MAAM,CAAE,CAAC,CACT,MAAM,CAAE,CACT"}'},yt$1=create_ssr_component((o,t,e,n)=>{let{show_label:l=!0}=t,{info:A=void 0}=t,{rtl:i=!1}=t;return t.show_label===void 0&&e.show_label&&l!==void 0&&e.show_label(l),t.info===void 0&&e.info&&A!==void 0&&e.info(A),t.rtl===void 0&&e.rtl&&i!==void 0&&e.rtl(i),o.css.add(et),`<span data-testid="block-info"${add_attribute("dir",i?"rtl":"ltr",0)} class="${["svelte-g2oxp3",(l?"":"sr-only")+" "+(l?"":"hide")+" "+(A!=null?"has-info":"")].join(" ").trim()}">${n.default?n.default({}):""}</span> ${A?`${validate_component(tt,"Info").$$render(o,{info:A},{},{})}`:""}`}),ot$1={code:`label.svelte-j0zqjt.svelte-j0zqjt{display:inline-flex;align-items:center;z-index:var(--layer-2);box-shadow:var(--block-label-shadow);border:var(--block-label-border-width) solid
			var(--block-label-border-color);border-top:none;border-left:none;border-radius:var(--block-label-radius);background:var(--block-label-background-fill);padding:var(--block-label-padding);pointer-events:none;color:var(--block-label-text-color);font-weight:var(--block-label-text-weight);font-size:var(--block-label-text-size);line-height:var(--line-sm)}.gr-group label.svelte-j0zqjt.svelte-j0zqjt{border-top-left-radius:0}label.float.svelte-j0zqjt.svelte-j0zqjt{position:absolute;top:var(--block-label-margin);left:var(--block-label-margin)}label.svelte-j0zqjt.svelte-j0zqjt:not(.float){position:static;margin-top:var(--block-label-margin);margin-left:var(--block-label-margin)}.hide.svelte-j0zqjt.svelte-j0zqjt{display:none}span.svelte-j0zqjt.svelte-j0zqjt{opacity:0.8;margin-right:var(--size-2);width:calc(var(--block-label-text-size) - 1px);height:calc(var(--block-label-text-size) - 1px)}.hide-label.svelte-j0zqjt.svelte-j0zqjt{box-shadow:none;border-width:0;background:transparent;overflow:visible}label[dir="rtl"].svelte-j0zqjt.svelte-j0zqjt{border:var(--block-label-border-width) solid
			var(--block-label-border-color);border-top:none;border-right:none;border-bottom-left-radius:var(--block-radius);border-bottom-right-radius:var(--block-label-radius);border-top-left-radius:var(--block-label-radius)}label[dir="rtl"].svelte-j0zqjt span.svelte-j0zqjt{margin-left:var(--size-2);margin-right:0}`,map:'{"version":3,"file":"BlockLabel.svelte","sources":["BlockLabel.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let label = null;\\nexport let Icon;\\nexport let show_label = true;\\nexport let disable = false;\\nexport let float = true;\\nexport let rtl = false;\\n<\/script>\\n\\n<label\\n\\tfor=\\"\\"\\n\\tclass:hide={!show_label}\\n\\tclass:sr-only={!show_label}\\n\\tclass:float\\n\\tclass:hide-label={disable}\\n\\tdata-testid=\\"block-label\\"\\n\\tdir={rtl ? \\"rtl\\" : \\"ltr\\"}\\n>\\n\\t<span>\\n\\t\\t<Icon />\\n\\t</span>\\n\\t{label}\\n</label>\\n\\n<style>\\n\\tlabel {\\n\\t\\tdisplay: inline-flex;\\n\\t\\talign-items: center;\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tbox-shadow: var(--block-label-shadow);\\n\\t\\tborder: var(--block-label-border-width) solid\\n\\t\\t\\tvar(--block-label-border-color);\\n\\t\\tborder-top: none;\\n\\t\\tborder-left: none;\\n\\t\\tborder-radius: var(--block-label-radius);\\n\\t\\tbackground: var(--block-label-background-fill);\\n\\t\\tpadding: var(--block-label-padding);\\n\\t\\tpointer-events: none;\\n\\t\\tcolor: var(--block-label-text-color);\\n\\t\\tfont-weight: var(--block-label-text-weight);\\n\\t\\tfont-size: var(--block-label-text-size);\\n\\t\\tline-height: var(--line-sm);\\n\\t}\\n\\t:global(.gr-group) label {\\n\\t\\tborder-top-left-radius: 0;\\n\\t}\\n\\n\\tlabel.float {\\n\\t\\tposition: absolute;\\n\\t\\ttop: var(--block-label-margin);\\n\\t\\tleft: var(--block-label-margin);\\n\\t}\\n\\tlabel:not(.float) {\\n\\t\\tposition: static;\\n\\t\\tmargin-top: var(--block-label-margin);\\n\\t\\tmargin-left: var(--block-label-margin);\\n\\t}\\n\\n\\t.hide {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\tspan {\\n\\t\\topacity: 0.8;\\n\\t\\tmargin-right: var(--size-2);\\n\\t\\twidth: calc(var(--block-label-text-size) - 1px);\\n\\t\\theight: calc(var(--block-label-text-size) - 1px);\\n\\t}\\n\\t.hide-label {\\n\\t\\tbox-shadow: none;\\n\\t\\tborder-width: 0;\\n\\t\\tbackground: transparent;\\n\\t\\toverflow: visible;\\n\\t}\\n\\n\\tlabel[dir=\\"rtl\\"] {\\n\\t\\tborder: var(--block-label-border-width) solid\\n\\t\\t\\tvar(--block-label-border-color);\\n\\t\\tborder-top: none;\\n\\t\\tborder-right: none;\\n\\t\\tborder-bottom-left-radius: var(--block-radius);\\n\\t\\tborder-bottom-right-radius: var(--block-label-radius);\\n\\t\\tborder-top-left-radius: var(--block-label-radius);\\n\\t}\\n\\n\\tlabel[dir=\\"rtl\\"] span {\\n\\t\\tmargin-left: var(--size-2);\\n\\t\\tmargin-right: 0;\\n\\t}</style>\\n"],"names":[],"mappings":"AAwBC,iCAAM,CACL,OAAO,CAAE,WAAW,CACpB,WAAW,CAAE,MAAM,CACnB,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,UAAU,CAAE,IAAI,oBAAoB,CAAC,CACrC,MAAM,CAAE,IAAI,0BAA0B,CAAC,CAAC;AAC1C,GAAG,IAAI,0BAA0B,CAAC,CAChC,UAAU,CAAE,IAAI,CAChB,WAAW,CAAE,IAAI,CACjB,aAAa,CAAE,IAAI,oBAAoB,CAAC,CACxC,UAAU,CAAE,IAAI,6BAA6B,CAAC,CAC9C,OAAO,CAAE,IAAI,qBAAqB,CAAC,CACnC,cAAc,CAAE,IAAI,CACpB,KAAK,CAAE,IAAI,wBAAwB,CAAC,CACpC,WAAW,CAAE,IAAI,yBAAyB,CAAC,CAC3C,SAAS,CAAE,IAAI,uBAAuB,CAAC,CACvC,WAAW,CAAE,IAAI,SAAS,CAC3B,CACQ,SAAU,CAAC,iCAAM,CACxB,sBAAsB,CAAE,CACzB,CAEA,KAAK,kCAAO,CACX,QAAQ,CAAE,QAAQ,CAClB,GAAG,CAAE,IAAI,oBAAoB,CAAC,CAC9B,IAAI,CAAE,IAAI,oBAAoB,CAC/B,CACA,iCAAK,KAAK,MAAM,CAAE,CACjB,QAAQ,CAAE,MAAM,CAChB,UAAU,CAAE,IAAI,oBAAoB,CAAC,CACrC,WAAW,CAAE,IAAI,oBAAoB,CACtC,CAEA,iCAAM,CACL,OAAO,CAAE,IACV,CAEA,gCAAK,CACJ,OAAO,CAAE,GAAG,CACZ,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,KAAK,CAAE,KAAK,IAAI,uBAAuB,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CAC/C,MAAM,CAAE,KAAK,IAAI,uBAAuB,CAAC,CAAC,CAAC,CAAC,GAAG,CAChD,CACA,uCAAY,CACX,UAAU,CAAE,IAAI,CAChB,YAAY,CAAE,CAAC,CACf,UAAU,CAAE,WAAW,CACvB,QAAQ,CAAE,OACX,CAEA,KAAK,CAAC,GAAG,CAAC,KAAK,6BAAE,CAChB,MAAM,CAAE,IAAI,0BAA0B,CAAC,CAAC;AAC1C,GAAG,IAAI,0BAA0B,CAAC,CAChC,UAAU,CAAE,IAAI,CAChB,YAAY,CAAE,IAAI,CAClB,yBAAyB,CAAE,IAAI,cAAc,CAAC,CAC9C,0BAA0B,CAAE,IAAI,oBAAoB,CAAC,CACrD,sBAAsB,CAAE,IAAI,oBAAoB,CACjD,CAEA,KAAK,CAAC,GAAG,CAAC,KAAK,eAAC,CAAC,kBAAK,CACrB,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,YAAY,CAAE,CACf"}'},Et$1=create_ssr_component((o,t,e,n)=>{let{label:l=null}=t,{Icon:A}=t,{show_label:i=!0}=t,{disable:s=!1}=t,{float:a=!0}=t,{rtl:d=!1}=t;return t.label===void 0&&e.label&&l!==void 0&&e.label(l),t.Icon===void 0&&e.Icon&&A!==void 0&&e.Icon(A),t.show_label===void 0&&e.show_label&&i!==void 0&&e.show_label(i),t.disable===void 0&&e.disable&&s!==void 0&&e.disable(s),t.float===void 0&&e.float&&a!==void 0&&e.float(a),t.rtl===void 0&&e.rtl&&d!==void 0&&e.rtl(d),o.css.add(ot$1),`<label for="" data-testid="block-label"${add_attribute("dir",d?"rtl":"ltr",0)} class="${["svelte-j0zqjt",(i?"":"hide")+" "+(i?"":"sr-only")+" "+(a?"float":"")+" "+(s?"hide-label":"")].join(" ").trim()}"><span class="svelte-j0zqjt">${validate_component(A,"Icon").$$render(o,{},{},{})}</span> ${escape(l)} </label>`}),nt={code:".unstyled-link.svelte-1s8vnbx{all:unset;cursor:pointer}",map:'{"version":3,"file":"DownloadLink.svelte","sources":["DownloadLink.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { createEventDispatcher } from \\"svelte\\";\\nexport let href = void 0;\\nexport let download;\\nconst dispatch = createEventDispatcher();\\n<\/script>\\n\\n<a\\n\\tstyle:position=\\"relative\\"\\n\\tclass=\\"download-link\\"\\n\\t{href}\\n\\ttarget={typeof window !== \\"undefined\\" && window.__is_colab__\\n\\t\\t? \\"_blank\\"\\n\\t\\t: null}\\n\\trel=\\"noopener noreferrer\\"\\n\\t{download}\\n\\t{...$$restProps}\\n\\ton:click={dispatch.bind(null, \\"click\\")}\\n>\\n\\t<slot />\\n</a>\\n\\n<style>\\n\\t.unstyled-link {\\n\\t\\tall: unset;\\n\\t\\tcursor: pointer;\\n\\t}</style>\\n"],"names":[],"mappings":"AAsBC,6BAAe,CACd,GAAG,CAAE,KAAK,CACV,MAAM,CAAE,OACT"}'},Mt=create_ssr_component((o,t,e,n)=>{let l=compute_rest_props(t,["href","download"]),{href:A=void 0}=t,{download:i}=t;return createEventDispatcher(),t.href===void 0&&e.href&&A!==void 0&&e.href(A),t.download===void 0&&e.download&&i!==void 0&&e.download(i),o.css.add(nt),`<a${spread([{class:"download-link"},{href:escape_attribute_value(A)},{target:escape_attribute_value(typeof window<"u"&&window.__is_colab__?"_blank":null)},{rel:"noopener noreferrer"},{download:escape_attribute_value(i)},escape_object(l)],{classes:"svelte-1s8vnbx",styles:{position:"relative"}})}>${n.default?n.default({}):""} </a>`}),rt={code:"button.svelte-fuq25k{display:flex;justify-content:center;align-items:center;gap:1px;z-index:var(--layer-2);border-radius:var(--radius-xs);color:var(--block-label-text-color);border:1px solid var(--border-color);padding:var(--spacing-xxs)}button.svelte-fuq25k:hover{background-color:var(--background-fill-secondary)}button[disabled].svelte-fuq25k{opacity:0.5;box-shadow:none}button[disabled].svelte-fuq25k:hover{cursor:not-allowed}.padded.svelte-fuq25k{background:var(--bg-color)}button.svelte-fuq25k:hover,button.highlight.svelte-fuq25k{cursor:pointer;color:var(--color-accent)}.padded.svelte-fuq25k:hover{color:var(--block-label-text-color)}span.svelte-fuq25k{padding:0px 1px;font-size:10px}div.svelte-fuq25k{display:flex;align-items:center;justify-content:center;transition:filter 0.2s ease-in-out}.x-small.svelte-fuq25k{width:10px;height:10px}.small.svelte-fuq25k{width:14px;height:14px}.medium.svelte-fuq25k{width:20px;height:20px}.large.svelte-fuq25k{width:22px;height:22px}.pending.svelte-fuq25k{animation:svelte-fuq25k-flash 0.5s infinite}@keyframes svelte-fuq25k-flash{0%{opacity:0.5}50%{opacity:1}100%{opacity:0.5}}.transparent.svelte-fuq25k{background:transparent;border:none;box-shadow:none}",map:'{"version":3,"file":"IconButton.svelte","sources":["IconButton.svelte"],"sourcesContent":["<script lang=\\"ts\\">import {} from \\"svelte\\";\\nexport let Icon;\\nexport let label = \\"\\";\\nexport let show_label = false;\\nexport let pending = false;\\nexport let size = \\"small\\";\\nexport let padded = true;\\nexport let highlight = false;\\nexport let disabled = false;\\nexport let hasPopup = false;\\nexport let color = \\"var(--block-label-text-color)\\";\\nexport let transparent = false;\\nexport let background = \\"var(--block-background-fill)\\";\\nexport let border = \\"transparent\\";\\n$: _color = highlight ? \\"var(--color-accent)\\" : color;\\n<\/script>\\n\\n<button\\n\\tclass=\\"icon-button\\"\\n\\t{disabled}\\n\\ton:click\\n\\taria-label={label}\\n\\taria-haspopup={hasPopup}\\n\\ttitle={label}\\n\\tclass:pending\\n\\tclass:padded\\n\\tclass:highlight\\n\\tclass:transparent\\n\\tstyle:--border-color={border}\\n\\tstyle:color={!disabled && _color ? _color : \\"var(--block-label-text-color)\\"}\\n\\tstyle:--bg-color={!disabled ? background : \\"auto\\"}\\n>\\n\\t{#if show_label}<span>{label}</span>{/if}\\n\\t<div\\n\\t\\tclass:x-small={size === \\"x-small\\"}\\n\\t\\tclass:small={size === \\"small\\"}\\n\\t\\tclass:large={size === \\"large\\"}\\n\\t\\tclass:medium={size === \\"medium\\"}\\n\\t>\\n\\t\\t<svelte:component this={Icon} />\\n\\t\\t<slot />\\n\\t</div>\\n</button>\\n\\n<style>\\n\\tbutton {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tgap: 1px;\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tborder-radius: var(--radius-xs);\\n\\t\\tcolor: var(--block-label-text-color);\\n\\t\\tborder: 1px solid var(--border-color);\\n\\t\\tpadding: var(--spacing-xxs);\\n\\t}\\n\\n\\tbutton:hover {\\n\\t\\tbackground-color: var(--background-fill-secondary);\\n\\t}\\n\\n\\tbutton[disabled] {\\n\\t\\topacity: 0.5;\\n\\t\\tbox-shadow: none;\\n\\t}\\n\\n\\tbutton[disabled]:hover {\\n\\t\\tcursor: not-allowed;\\n\\t}\\n\\n\\t.padded {\\n\\t\\tbackground: var(--bg-color);\\n\\t}\\n\\n\\tbutton:hover,\\n\\tbutton.highlight {\\n\\t\\tcursor: pointer;\\n\\t\\tcolor: var(--color-accent);\\n\\t}\\n\\n\\t.padded:hover {\\n\\t\\tcolor: var(--block-label-text-color);\\n\\t}\\n\\n\\tspan {\\n\\t\\tpadding: 0px 1px;\\n\\t\\tfont-size: 10px;\\n\\t}\\n\\n\\tdiv {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\ttransition: filter 0.2s ease-in-out;\\n\\t}\\n\\n\\t.x-small {\\n\\t\\twidth: 10px;\\n\\t\\theight: 10px;\\n\\t}\\n\\n\\t.small {\\n\\t\\twidth: 14px;\\n\\t\\theight: 14px;\\n\\t}\\n\\n\\t.medium {\\n\\t\\twidth: 20px;\\n\\t\\theight: 20px;\\n\\t}\\n\\n\\t.large {\\n\\t\\twidth: 22px;\\n\\t\\theight: 22px;\\n\\t}\\n\\n\\t.pending {\\n\\t\\tanimation: flash 0.5s infinite;\\n\\t}\\n\\n\\t@keyframes flash {\\n\\t\\t0% {\\n\\t\\t\\topacity: 0.5;\\n\\t\\t}\\n\\t\\t50% {\\n\\t\\t\\topacity: 1;\\n\\t\\t}\\n\\t\\t100% {\\n\\t\\t\\topacity: 0.5;\\n\\t\\t}\\n\\t}\\n\\n\\t.transparent {\\n\\t\\tbackground: transparent;\\n\\t\\tborder: none;\\n\\t\\tbox-shadow: none;\\n\\t}</style>\\n"],"names":[],"mappings":"AA6CC,oBAAO,CACN,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,GAAG,CAAE,GAAG,CACR,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,aAAa,CAAE,IAAI,WAAW,CAAC,CAC/B,KAAK,CAAE,IAAI,wBAAwB,CAAC,CACpC,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,cAAc,CAAC,CACrC,OAAO,CAAE,IAAI,aAAa,CAC3B,CAEA,oBAAM,MAAO,CACZ,gBAAgB,CAAE,IAAI,2BAA2B,CAClD,CAEA,MAAM,CAAC,QAAQ,eAAE,CAChB,OAAO,CAAE,GAAG,CACZ,UAAU,CAAE,IACb,CAEA,MAAM,CAAC,QAAQ,eAAC,MAAO,CACtB,MAAM,CAAE,WACT,CAEA,qBAAQ,CACP,UAAU,CAAE,IAAI,UAAU,CAC3B,CAEA,oBAAM,MAAM,CACZ,MAAM,wBAAW,CAChB,MAAM,CAAE,OAAO,CACf,KAAK,CAAE,IAAI,cAAc,CAC1B,CAEA,qBAAO,MAAO,CACb,KAAK,CAAE,IAAI,wBAAwB,CACpC,CAEA,kBAAK,CACJ,OAAO,CAAE,GAAG,CAAC,GAAG,CAChB,SAAS,CAAE,IACZ,CAEA,iBAAI,CACH,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MAAM,CACnB,eAAe,CAAE,MAAM,CACvB,UAAU,CAAE,MAAM,CAAC,IAAI,CAAC,WACzB,CAEA,sBAAS,CACR,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,oBAAO,CACN,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,qBAAQ,CACP,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,oBAAO,CACN,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,sBAAS,CACR,SAAS,CAAE,mBAAK,CAAC,IAAI,CAAC,QACvB,CAEA,WAAW,mBAAM,CAChB,EAAG,CACF,OAAO,CAAE,GACV,CACA,GAAI,CACH,OAAO,CAAE,CACV,CACA,IAAK,CACJ,OAAO,CAAE,GACV,CACD,CAEA,0BAAa,CACZ,UAAU,CAAE,WAAW,CACvB,MAAM,CAAE,IAAI,CACZ,UAAU,CAAE,IACb"}'},O$1=create_ssr_component((o,t,e,n)=>{let l,{Icon:A}=t,{label:i=""}=t,{show_label:s=!1}=t,{pending:a=!1}=t,{size:d="small"}=t,{padded:g=!0}=t,{highlight:h=!1}=t,{disabled:p=!1}=t,{hasPopup:x=!1}=t,{color:b="var(--block-label-text-color)"}=t,{transparent:k=!1}=t,{background:B="var(--block-background-fill)"}=t,{border:f="transparent"}=t;return t.Icon===void 0&&e.Icon&&A!==void 0&&e.Icon(A),t.label===void 0&&e.label&&i!==void 0&&e.label(i),t.show_label===void 0&&e.show_label&&s!==void 0&&e.show_label(s),t.pending===void 0&&e.pending&&a!==void 0&&e.pending(a),t.size===void 0&&e.size&&d!==void 0&&e.size(d),t.padded===void 0&&e.padded&&g!==void 0&&e.padded(g),t.highlight===void 0&&e.highlight&&h!==void 0&&e.highlight(h),t.disabled===void 0&&e.disabled&&p!==void 0&&e.disabled(p),t.hasPopup===void 0&&e.hasPopup&&x!==void 0&&e.hasPopup(x),t.color===void 0&&e.color&&b!==void 0&&e.color(b),t.transparent===void 0&&e.transparent&&k!==void 0&&e.transparent(k),t.background===void 0&&e.background&&B!==void 0&&e.background(B),t.border===void 0&&e.border&&f!==void 0&&e.border(f),o.css.add(rt),l=h?"var(--color-accent)":b,`<button class="${["icon-button svelte-fuq25k",(a?"pending":"")+" "+(g?"padded":"")+" "+(h?"highlight":"")+" "+(k?"transparent":"")].join(" ").trim()}" ${p?"disabled":""}${add_attribute("aria-label",i,0)}${add_attribute("aria-haspopup",x,0)}${add_attribute("title",i,0)}${add_styles({"--border-color":f,color:!p&&l?l:"var(--block-label-text-color)","--bg-color":p?"auto":B})}>${s?`<span class="svelte-fuq25k">${escape(i)}</span>`:""} <div class="${["svelte-fuq25k",(d==="x-small"?"x-small":"")+" "+(d==="small"?"small":"")+" "+(d==="large"?"large":"")+" "+(d==="medium"?"medium":"")].join(" ").trim()}">${validate_component(A||missing_component,"svelte:component").$$render(o,{},{},{})} ${n.default?n.default({}):""}</div> </button>`}),lt$1={code:".empty.svelte-1oiin9d{display:flex;justify-content:center;align-items:center;margin-top:calc(0px - var(--size-6));height:var(--size-full)}.icon.svelte-1oiin9d{opacity:0.5;height:var(--size-5);color:var(--body-text-color)}.small.svelte-1oiin9d{min-height:calc(var(--size-32) - 20px)}.large.svelte-1oiin9d{min-height:calc(var(--size-64) - 20px)}.unpadded_box.svelte-1oiin9d{margin-top:0}.small_parent.svelte-1oiin9d{min-height:100% !important}",map:'{"version":3,"file":"Empty.svelte","sources":["Empty.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let size = \\"small\\";\\nexport let unpadded_box = false;\\nlet el;\\n$: parent_height = compare_el_to_parent(el);\\nfunction compare_el_to_parent(el2) {\\n    if (!el2)\\n        return false;\\n    const { height: el_height } = el2.getBoundingClientRect();\\n    const { height: parent_height2 } = el2.parentElement?.getBoundingClientRect() || { height: el_height };\\n    return el_height > parent_height2 + 2;\\n}\\n<\/script>\\n\\n<div\\n\\tclass=\\"empty\\"\\n\\tclass:small={size === \\"small\\"}\\n\\tclass:large={size === \\"large\\"}\\n\\tclass:unpadded_box\\n\\tbind:this={el}\\n\\tclass:small_parent={parent_height}\\n\\taria-label=\\"Empty value\\"\\n>\\n\\t<div class=\\"icon\\">\\n\\t\\t<slot />\\n\\t</div>\\n</div>\\n\\n<style>\\n\\t.empty {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tmargin-top: calc(0px - var(--size-6));\\n\\t\\theight: var(--size-full);\\n\\t}\\n\\n\\t.icon {\\n\\t\\topacity: 0.5;\\n\\t\\theight: var(--size-5);\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.small {\\n\\t\\tmin-height: calc(var(--size-32) - 20px);\\n\\t}\\n\\n\\t.large {\\n\\t\\tmin-height: calc(var(--size-64) - 20px);\\n\\t}\\n\\n\\t.unpadded_box {\\n\\t\\tmargin-top: 0;\\n\\t}\\n\\n\\t.small_parent {\\n\\t\\tmin-height: 100% !important;\\n\\t}</style>\\n"],"names":[],"mappings":"AA4BC,qBAAO,CACN,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,UAAU,CAAE,KAAK,GAAG,CAAC,CAAC,CAAC,IAAI,QAAQ,CAAC,CAAC,CACrC,MAAM,CAAE,IAAI,WAAW,CACxB,CAEA,oBAAM,CACL,OAAO,CAAE,GAAG,CACZ,MAAM,CAAE,IAAI,QAAQ,CAAC,CACrB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,qBAAO,CACN,UAAU,CAAE,KAAK,IAAI,SAAS,CAAC,CAAC,CAAC,CAAC,IAAI,CACvC,CAEA,qBAAO,CACN,UAAU,CAAE,KAAK,IAAI,SAAS,CAAC,CAAC,CAAC,CAAC,IAAI,CACvC,CAEA,4BAAc,CACb,UAAU,CAAE,CACb,CAEA,4BAAc,CACb,UAAU,CAAE,IAAI,CAAC,UAClB"}'};function At(o){return !1}const _t=create_ssr_component((o,t,e,n)=>{let l,{size:A="small"}=t,{unpadded_box:i=!1}=t,s;return t.size===void 0&&e.size&&A!==void 0&&e.size(A),t.unpadded_box===void 0&&e.unpadded_box&&i!==void 0&&e.unpadded_box(i),o.css.add(lt$1),l=At(),`<div class="${["empty svelte-1oiin9d",(A==="small"?"small":"")+" "+(A==="large"?"large":"")+" "+(i?"unpadded_box":"")+" "+(l?"small_parent":"")].join(" ").trim()}" aria-label="Empty value"${add_attribute("this",s,0)}><div class="icon svelte-1oiin9d">${n.default?n.default({}):""}</div> </div>`});const Kt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" stroke-width="1.5" viewBox="0 0 24 24" color="currentColor"><path stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" d="M21.044 5.704a.6.6 0 0 1 .956.483v11.626a.6.6 0 0 1-.956.483l-7.889-5.813a.6.6 0 0 1 0-.966l7.89-5.813ZM10.044 5.704a.6.6 0 0 1 .956.483v11.626a.6.6 0 0 1-.956.483l-7.888-5.813a.6.6 0 0 1 0-.966l7.888-5.813Z"></path></svg>'),Wt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></rect><line x1="2" y1="9" x2="22" y2="9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></line><line x1="7" y1="2" x2="7" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></line><line x1="17" y1="2" x2="17" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"></line></svg>'),Ot=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-camera"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>');const Gt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--carbon" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" viewBox="0 0 32 32"><path fill="currentColor" d="M17.74 30L16 29l4-7h6a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h9v2H6a4 4 0 0 1-4-4V8a4 4 0 0 1 4-4h20a4 4 0 0 1 4 4v12a4 4 0 0 1-4 4h-4.84Z"></path><path fill="currentColor" d="M8 10h16v2H8zm0 6h10v2H8z"></path></svg>'),Zt=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor"><path d="M5 13L9 17L19 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>'),Vt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-circle"><circle cx="12" cy="12" r="10"></circle></svg>'),Ut=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 24 24" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" stroke="currentColor" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linecap:round;stroke-linejoin:round;"><g transform="matrix(1.14096,-0.140958,-0.140958,1.14096,-0.0559523,0.0559523)"><path d="M18,6L6.087,17.913" style="fill:none;fill-rule:nonzero;stroke-width:2px;"></path></g><path d="M4.364,4.364L19.636,19.636" style="fill:none;fill-rule:nonzero;stroke-width:2px;"></path></svg>'),Tt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="feather feather-closed-caption"><rect x="2" y="6" width="20" height="12" rx="2" ry="2"></rect><text x="12" y="15" font-family="sans-serif" font-size="8" font-weight="bold" fill="currentColor" stroke="none" text-anchor="middle">CC</text></svg>'),St=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 32 32"><path fill="currentColor" d="m31 16l-7 7l-1.41-1.41L28.17 16l-5.58-5.59L24 9l7 7zM1 16l7-7l1.41 1.41L3.83 16l5.58 5.59L8 23l-7-7zm11.42 9.484L17.64 6l1.932.517L14.352 26z"></path></svg>');const it$1=create_ssr_component((o,t,e,n)=>'<svg id="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="100%" height="100%"><path d="M23,20a5,5,0,0,0-3.89,1.89L11.8,17.32a4.46,4.46,0,0,0,0-2.64l7.31-4.57A5,5,0,1,0,18,7a4.79,4.79,0,0,0,.2,1.32l-7.31,4.57a5,5,0,1,0,0,6.22l7.31,4.57A4.79,4.79,0,0,0,18,25a5,5,0,1,0,5-5ZM23,4a3,3,0,1,1-3,3A3,3,0,0,1,23,4ZM7,19a3,3,0,1,1,3-3A3,3,0,0,1,7,19Zm16,9a3,3,0,1,1,3-3A3,3,0,0,1,23,28Z" fill="currentColor"></path></svg>'),Yt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 33 33" color="currentColor" aria-hidden="true" width="100%" height="100%"><path fill="currentColor" d="M28 10v18H10V10h18m0-2H10a2 2 0 0 0-2 2v18a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2Z"></path><path fill="currentColor" d="M4 18H2V4a2 2 0 0 1 2-2h14v2H4Z"></path></svg>'),$t=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 32 32"><path fill="currentColor" d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4zm0-10l-1.41-1.41L17 20.17V2h-2v18.17l-7.59-7.58L6 14l10 10l10-10z"></path></svg>'),st$1={code:".dropdown-arrow.svelte-xjn76a{fill:currentColor}",map:'{"version":3,"file":"DropdownArrow.svelte","sources":["DropdownArrow.svelte"],"sourcesContent":["<svg\\n\\tclass=\\"dropdown-arrow\\"\\n\\txmlns=\\"http://www.w3.org/2000/svg\\"\\n\\twidth=\\"100%\\"\\n\\theight=\\"100%\\"\\n\\tviewBox=\\"0 0 18 18\\"\\n>\\n\\t<path d=\\"M5 8l4 4 4-4z\\" />\\n</svg>\\n\\n<style>\\n\\t.dropdown-arrow {\\n\\t\\tfill: currentColor;\\n\\t\\t/* margin-right: var(--size-2); */\\n\\t\\t/* width: var(--size-5); */\\n\\t}</style>\\n"],"names":[],"mappings":"AAWC,6BAAgB,CACf,IAAI,CAAE,YAGP"}'},Rt=create_ssr_component((o,t,e,n)=>(o.css.add(st$1),'<svg class="dropdown-arrow svelte-xjn76a" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 18 18"><path d="M5 8l4 4 4-4z"></path></svg>')),at$3={code:".dropdown-arrow.svelte-1m886t3{fill:currentColor}.circle.svelte-1m886t3{fill:currentColor;opacity:0.1}",map:'{"version":3,"file":"DropdownCircularArrow.svelte","sources":["DropdownCircularArrow.svelte"],"sourcesContent":["<svg\\n\\tclass=\\"dropdown-arrow\\"\\n\\txmlns=\\"http://www.w3.org/2000/svg\\"\\n\\twidth=\\"100%\\"\\n\\theight=\\"100%\\"\\n\\tviewBox=\\"0 0 18 18\\"\\n>\\n\\t<circle cx=\\"9\\" cy=\\"9\\" r=\\"8\\" class=\\"circle\\" />\\n\\t<path d=\\"M5 8l4 4 4-4z\\" />\\n</svg>\\n\\n<style>\\n\\t.dropdown-arrow {\\n\\t\\tfill: currentColor;\\n\\t}\\n\\n\\t.circle {\\n\\t\\tfill: currentColor;\\n\\t\\topacity: 0.1;\\n\\t}</style>\\n"],"names":[],"mappings":"AAYC,8BAAgB,CACf,IAAI,CAAE,YACP,CAEA,sBAAQ,CACP,IAAI,CAAE,YAAY,CAClB,OAAO,CAAE,GACV"}'},Pt=create_ssr_component((o,t,e,n)=>(o.css.add(at$3),'<svg class="dropdown-arrow svelte-1m886t3" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 18 18"><circle cx="9" cy="9" r="8" class="circle svelte-1m886t3"></circle><path d="M5 8l4 4 4-4z"></path></svg>')),Dt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-edit-2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>'),Nt=create_ssr_component((o,t,e,n)=>'<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"></path></svg>'),Jt=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" fill="currentColor" stroke-width="1.5" viewBox="0 0 24 24" color="currentColor"><path stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" d="M2.956 5.704A.6.6 0 0 0 2 6.187v11.626a.6.6 0 0 0 .956.483l7.889-5.813a.6.6 0 0 0 0-.966l-7.89-5.813ZM13.956 5.704a.6.6 0 0 0-.956.483v11.626a.6.6 0 0 0 .956.483l7.889-5.813a.6.6 0 0 0 0-.966l-7.89-5.813Z"></path></svg>'),te=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-file"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>'),ee=create_ssr_component((o,t,e,n)=>'<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"></path></svg>'),oe=create_ssr_component((o,t,e,n)=>'<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'),ne=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-image"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>'),Y=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 256 256"><path fill="currentColor" d="M200 32h-36.26a47.92 47.92 0 0 0-71.48 0H56a16 16 0 0 0-16 16v168a16 16 0 0 0 16 16h144a16 16 0 0 0 16-16V48a16 16 0 0 0-16-16m-72 0a32 32 0 0 1 32 32H96a32 32 0 0 1 32-32m72 184H56V48h26.75A47.9 47.9 0 0 0 80 64v8a8 8 0 0 0 8 8h80a8 8 0 0 0 8-8v-8a47.9 47.9 0 0 0-2.75-16H200Z"></path></svg>'),re=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--mdi" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" viewBox="0 0 24 24"><path fill="currentColor" d="M5 3h2v2H5v5a2 2 0 0 1-2 2a2 2 0 0 1 2 2v5h2v2H5c-1.07-.27-2-.9-2-2v-4a2 2 0 0 0-2-2H0v-2h1a2 2 0 0 0 2-2V5a2 2 0 0 1 2-2m14 0a2 2 0 0 1 2 2v4a2 2 0 0 0 2 2h1v2h-1a2 2 0 0 0-2 2v4a2 2 0 0 1-2 2h-2v-2h2v-5a2 2 0 0 1 2-2a2 2 0 0 1-2-2V5h-2V3h2m-7 12a1 1 0 0 1 1 1a1 1 0 0 1-1 1a1 1 0 0 1-1-1a1 1 0 0 1 1-1m-4 0a1 1 0 0 1 1 1a1 1 0 0 1-1 1a1 1 0 0 1-1-1a1 1 0 0 1 1-1m8 0a1 1 0 0 1 1 1a1 1 0 0 1-1 1a1 1 0 0 1-1-1a1 1 0 0 1 1-1Z"></path></svg>'),Ae=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--carbon" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" viewBox="0 0 32 32"><path fill="currentColor" d="M4 2H2v26a2 2 0 0 0 2 2h26v-2H4v-3h22v-8H4v-4h14V5H4Zm20 17v4H4v-4ZM16 7v4H4V7Z"></path></svg>'),dt$1=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-maximize" width="100%" height="100%"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>'),ct$2=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-mic"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>'),Ct$1=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-minimize" width="100%" height="100%"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>'),ie=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-music"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>');const ae=create_ssr_component((o,t,e,n)=>'<svg fill="currentColor" width="100%" height="100%" viewBox="0 0 1920 1920" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M1752.768 221.109C1532.646.986 1174.283.986 954.161 221.109l-838.588 838.588c-154.052 154.165-154.052 404.894 0 558.946 149.534 149.421 409.976 149.308 559.059 0l758.738-758.626c87.982-88.094 87.982-231.417 0-319.51-88.32-88.208-231.642-87.982-319.51 0l-638.796 638.908 79.85 79.849 638.795-638.908c43.934-43.821 115.539-43.934 159.812 0 43.934 44.047 43.934 115.877 0 159.812l-758.739 758.625c-110.23 110.118-289.355 110.005-399.36 0-110.118-110.117-110.005-289.242 0-399.247l838.588-838.588c175.963-175.962 462.382-176.188 638.909 0 176.075 176.188 176.075 462.833 0 638.908l-798.607 798.72 79.849 79.85 798.607-798.72c220.01-220.123 220.01-578.485 0-798.607" fill-rule="evenodd"></path></g></svg>'),de=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>'),ce=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>'),Ce=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--carbon" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" viewBox="0 0 32 32"><circle cx="20" cy="4" r="2" fill="currentColor"></circle><circle cx="8" cy="16" r="2" fill="currentColor"></circle><circle cx="28" cy="12" r="2" fill="currentColor"></circle><circle cx="11" cy="7" r="2" fill="currentColor"></circle><circle cx="16" cy="24" r="2" fill="currentColor"></circle><path fill="currentColor" d="M30 3.413L28.586 2L4 26.585V2H2v26a2 2 0 0 0 2 2h26v-2H5.413Z"></path></svg>'),he=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6 12H12M18 12H12M12 12V6M12 12V18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>'),pe=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path></svg>');const ue=create_ssr_component((o,t,e,n)=>'<svg viewBox="0 0 22 24" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M19.1168 12.1484C19.474 12.3581 19.9336 12.2384 20.1432 11.8811C20.3528 11.5238 20.2331 11.0643 19.8758 10.8547L19.1168 12.1484ZM6.94331 4.13656L6.55624 4.77902L6.56378 4.78344L6.94331 4.13656ZM5.92408 4.1598L5.50816 3.5357L5.50816 3.5357L5.92408 4.1598ZM5.51031 5.09156L4.76841 5.20151C4.77575 5.25101 4.78802 5.29965 4.80505 5.34671L5.51031 5.09156ZM7.12405 11.7567C7.26496 12.1462 7.69495 12.3477 8.08446 12.2068C8.47397 12.0659 8.67549 11.6359 8.53458 11.2464L7.12405 11.7567ZM19.8758 12.1484C20.2331 11.9388 20.3528 11.4793 20.1432 11.122C19.9336 10.7648 19.474 10.6451 19.1168 10.8547L19.8758 12.1484ZM6.94331 18.8666L6.56375 18.2196L6.55627 18.2241L6.94331 18.8666ZM5.92408 18.8433L5.50815 19.4674H5.50815L5.92408 18.8433ZM5.51031 17.9116L4.80505 17.6564C4.78802 17.7035 4.77575 17.7521 4.76841 17.8016L5.51031 17.9116ZM8.53458 11.7567C8.67549 11.3672 8.47397 10.9372 8.08446 10.7963C7.69495 10.6554 7.26496 10.8569 7.12405 11.2464L8.53458 11.7567ZM19.4963 12.2516C19.9105 12.2516 20.2463 11.9158 20.2463 11.5016C20.2463 11.0873 19.9105 10.7516 19.4963 10.7516V12.2516ZM7.82931 10.7516C7.4151 10.7516 7.07931 11.0873 7.07931 11.5016C7.07931 11.9158 7.4151 12.2516 7.82931 12.2516V10.7516ZM19.8758 10.8547L7.32284 3.48968L6.56378 4.78344L19.1168 12.1484L19.8758 10.8547ZM7.33035 3.49414C6.76609 3.15419 6.05633 3.17038 5.50816 3.5357L6.34 4.78391C6.40506 4.74055 6.4893 4.73863 6.55627 4.77898L7.33035 3.49414ZM5.50816 3.5357C4.95998 3.90102 4.67184 4.54987 4.76841 5.20151L6.25221 4.98161C6.24075 4.90427 6.27494 4.82727 6.34 4.78391L5.50816 3.5357ZM4.80505 5.34671L7.12405 11.7567L8.53458 11.2464L6.21558 4.83641L4.80505 5.34671ZM19.1168 10.8547L6.56378 18.2197L7.32284 19.5134L19.8758 12.1484L19.1168 10.8547ZM6.55627 18.2241C6.4893 18.2645 6.40506 18.2626 6.34 18.2192L5.50815 19.4674C6.05633 19.8327 6.76609 19.8489 7.33035 19.509L6.55627 18.2241ZM6.34 18.2192C6.27494 18.1759 6.24075 18.0988 6.25221 18.0215L4.76841 17.8016C4.67184 18.4532 4.95998 19.1021 5.50815 19.4674L6.34 18.2192ZM6.21558 18.1667L8.53458 11.7567L7.12405 11.2464L4.80505 17.6564L6.21558 18.1667ZM19.4963 10.7516H7.82931V12.2516H19.4963V10.7516Z" fill="currentColor"></path></g></svg>');const ge=create_ssr_component((o,t,e,n)=>{let{fill:l="currentColor"}=t,{stroke_width:A=1.5}=t;return t.fill===void 0&&e.fill&&l!==void 0&&e.fill(l),t.stroke_width===void 0&&e.stroke_width&&A!==void 0&&e.stroke_width(A),`<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"${add_attribute("fill",l,0)} stroke="currentColor"${add_attribute("stroke-width",`${A}`,0)} stroke-linecap="round" stroke-linejoin="round" class="feather feather-square"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>`});const we=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--carbon" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" viewBox="0 0 32 32"><path fill="currentColor" d="M12 15H5a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h5V5a1 1 0 0 0-1-1H3V2h6a3 3 0 0 1 3 3zM5 9a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1h5V9zm15 14v2a1 1 0 0 0 1 1h5v-4h-5a1 1 0 0 0-1 1z"></path><path fill="currentColor" d="M2 30h28V2Zm26-2h-7a3 3 0 0 1-3-3v-2a3 3 0 0 1 3-3h5v-2a1 1 0 0 0-1-1h-6v-2h6a3 3 0 0 1 3 3Z"></path></svg>'),fe=create_ssr_component((o,t,e,n)=>`<svg id="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="currentColor" width="100%" height="100%"><defs><style>.cls-1 {
				fill: none;
			}</style></defs><rect x="12" y="12" width="2" height="12"></rect><rect x="18" y="12" width="2" height="12"></rect><path d="M4,6V8H6V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V8h2V6ZM8,28V8H24V28Z"></path><rect x="12" y="2" width="8" height="2"></rect><rect id="_Transparent_Rectangle_" data-name="<Transparent Rectangle>" class="cls-1" width="32" height="32"></rect></svg>`);const me=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-scissors"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>'),xe=create_ssr_component((o,t,e,n)=>'<svg aria-label="undo" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-rotate-ccw"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>'),Q=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="90%" height="90%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-upload"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>'),be=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-video"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>'),Ie=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 24 24" stroke-width="1.5" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" color="currentColor"><title>Low volume</title><path d="M19.5 7.5C19.5 7.5 21 9 21 11.5C21 14 19.5 15.5 19.5 15.5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M2 13.8571V10.1429C2 9.03829 2.89543 8.14286 4 8.14286H6.9C7.09569 8.14286 7.28708 8.08544 7.45046 7.97772L13.4495 4.02228C14.1144 3.5839 15 4.06075 15 4.85714V19.1429C15 19.9392 14.1144 20.4161 13.4495 19.9777L7.45046 16.0223C7.28708 15.9146 7.09569 15.8571 6.9 15.8571H4C2.89543 15.8571 2 14.9617 2 13.8571Z" stroke-width="1.5"></path></svg>'),ye=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 24 24" stroke-width="1.5" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg" color="currentColor"><title>High volume</title><path d="M1 13.8571V10.1429C1 9.03829 1.89543 8.14286 3 8.14286H5.9C6.09569 8.14286 6.28708 8.08544 6.45046 7.97772L12.4495 4.02228C13.1144 3.5839 14 4.06075 14 4.85714V19.1429C14 19.9392 13.1144 20.4161 12.4495 19.9777L6.45046 16.0223C6.28708 15.9146 6.09569 15.8571 5.9 15.8571H3C1.89543 15.8571 1 14.9617 1 13.8571Z" stroke-width="1.5"></path><path d="M17.5 7.5C17.5 7.5 19 9 19 11.5C19 14 17.5 15.5 17.5 15.5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M20.5 4.5C20.5 4.5 23 7 23 11.5C23 16 20.5 18.5 20.5 18.5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>'),Ee=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" viewBox="0 0 24 24" stroke-width="1.5" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="currentColor" color="currentColor"><title>Muted volume</title><g clip-path="url(#clip0_3173_16686)"><path d="M18 14L20.0005 12M22 10L20.0005 12M20.0005 12L18 10M20.0005 12L22 14" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M2 13.8571V10.1429C2 9.03829 2.89543 8.14286 4 8.14286H6.9C7.09569 8.14286 7.28708 8.08544 7.45046 7.97772L13.4495 4.02228C14.1144 3.5839 15 4.06075 15 4.85714V19.1429C15 19.9392 14.1144 20.4161 13.4495 19.9777L7.45046 16.0223C7.28708 15.9146 7.09569 15.8571 6.9 15.8571H4C2.89543 15.8571 2 14.9617 2 13.8571Z" stroke-width="1.5"></path></g><defs><clipPath id="clip0_3173_16686"><rect width="24" height="24" fill="white"></rect></clipPath></defs></svg>'),Me=create_ssr_component((o,t,e,n)=>'<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" stroke-linecap="round" stroke-linejoin="round"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"></path></svg>'),ht=create_ssr_component((o,t,e,n)=>'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2c-4.963 0-9 4.038-9 9c0 3.328 1.82 6.232 4.513 7.79l-2.067 1.378A1 1 0 0 0 6 22h12a1 1 0 0 0 .555-1.832l-2.067-1.378C19.18 17.232 21 14.328 21 11c0-4.962-4.037-9-9-9zm0 16c-3.859 0-7-3.141-7-7c0-3.86 3.141-7 7-7s7 3.14 7 7c0 3.859-3.141 7-7 7z"></path><path fill="currentColor" d="M12 6c-2.757 0-5 2.243-5 5s2.243 5 5 5s5-2.243 5-5s-2.243-5-5-5zm0 8c-1.654 0-3-1.346-3-3s1.346-3 3-3s3 1.346 3 3s-1.346 3-3 3z"></path></svg>'),vt$1={code:"svg.svelte-184ngxt{animation:svelte-184ngxt-spin 1.5s linear infinite}@keyframes svelte-184ngxt-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}",map:'{"version":3,"file":"Spinner.svelte","sources":["Spinner.svelte"],"sourcesContent":["<svg\\n\\txmlns=\\"http://www.w3.org/2000/svg\\"\\n\\twidth=\\"100%\\"\\n\\theight=\\"100%\\"\\n\\tviewBox=\\"0 0 50 50\\"\\n>\\n\\t<circle\\n\\t\\tcx=\\"25\\"\\n\\t\\tcy=\\"25\\"\\n\\t\\tr=\\"20\\"\\n\\t\\tfill=\\"none\\"\\n\\t\\tstroke-width=\\"3.0\\"\\n\\t\\tstroke-linecap=\\"round\\"\\n\\t\\tstroke-dasharray=\\"94.2477796076938 94.2477796076938\\"\\n\\t\\tstroke-dashoffset=\\"0\\"\\n\\t>\\n\\t\\t<animateTransform\\n\\t\\t\\tattributeName=\\"transform\\"\\n\\t\\t\\ttype=\\"rotate\\"\\n\\t\\t\\tfrom=\\"0 25 25\\"\\n\\t\\t\\tto=\\"360 25 25\\"\\n\\t\\t\\trepeatCount=\\"indefinite\\"\\n\\t\\t/>\\n\\t</circle>\\n</svg>\\n\\n<style>\\n\\tsvg {\\n\\t\\tanimation: spin 1.5s linear infinite;\\n\\t}\\n\\n\\t@keyframes spin {\\n\\t\\t0% {\\n\\t\\t\\ttransform: rotate(0deg);\\n\\t\\t}\\n\\t\\t100% {\\n\\t\\t\\ttransform: rotate(360deg);\\n\\t\\t}\\n\\t}</style>\\n"],"names":[],"mappings":"AA2BC,kBAAI,CACH,SAAS,CAAE,mBAAI,CAAC,IAAI,CAAC,MAAM,CAAC,QAC7B,CAEA,WAAW,mBAAK,CACf,EAAG,CACF,SAAS,CAAE,OAAO,IAAI,CACvB,CACA,IAAK,CACJ,SAAS,CAAE,OAAO,MAAM,CACzB,CACD"}'},_e=create_ssr_component((o,t,e,n)=>(o.css.add(vt$1),'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 50 50" class="svelte-184ngxt"><circle cx="25" cy="25" r="20" fill="none" stroke-width="3.0" stroke-linecap="round" stroke-dasharray="94.2477796076938 94.2477796076938" stroke-dashoffset="0"><animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" repeatCount="indefinite"></animateTransform></circle></svg>')),je=create_ssr_component((o,t,e,n)=>'<svg width="100%" height="100%" stroke-width="1.5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" color="currentColor"><path d="M19.1679 9C18.0247 6.46819 15.3006 4.5 11.9999 4.5C8.31459 4.5 5.05104 7.44668 4.54932 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M16 9H19.4C19.7314 9 20 8.73137 20 8.4V5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M4.88146 15C5.92458 17.5318 8.64874 19.5 12.0494 19.5C15.7347 19.5 18.9983 16.5533 19.5 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M8.04932 15H4.64932C4.31795 15 4.04932 15.2686 4.04932 15.6V19" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>');const Ge=create_ssr_component((o,t,e,n)=>{createEventDispatcher();let{formatter:l}=t,{value:A}=t,{i18n:i}=t,s=!1;return t.formatter===void 0&&e.formatter&&l!==void 0&&e.formatter(l),t.value===void 0&&e.value&&A!==void 0&&e.value(A),t.i18n===void 0&&e.i18n&&i!==void 0&&e.i18n(i),`${validate_component(O$1,"IconButton").$$render(o,{Icon:it$1,label:i("common.share"),pending:s},{},{})}`}),pt=/^(#\s*)(.+)$/m;function ut$1(o){const t=o.trim(),e=t.match(pt);if(!e)return [!1,t||!1];const[n,,l]=e,A=l.trim();if(t===n)return [A,!1];const i=e.index!==void 0?e.index+n.length:0,a=t.substring(i).trim()||!1;return [A,a]}const gt={code:"h2.svelte-12ioyct{font-size:var(--text-xl) !important}p.svelte-12ioyct,h2.svelte-12ioyct{white-space:pre-line}.wrap.svelte-12ioyct{display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:var(--size-60);color:var(--block-label-text-color);line-height:var(--line-md);height:100%;padding-top:var(--size-3);text-align:center;margin:auto var(--spacing-lg)}.or.svelte-12ioyct{color:var(--body-text-color-subdued);display:flex}.icon-wrap.svelte-12ioyct{width:30px;margin-bottom:var(--spacing-lg)}@media(min-width: 768px){.wrap.svelte-12ioyct{font-size:var(--text-lg)}}.hovered.svelte-12ioyct{color:var(--color-accent)}",map:'{"version":3,"file":"UploadText.svelte","sources":["UploadText.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { Upload as UploadIcon, ImagePaste } from \\"@gradio/icons\\";\\nimport { inject } from \\"./utils/parse_placeholder\\";\\nexport let type = \\"file\\";\\nexport let i18n;\\nexport let message = void 0;\\nexport let mode = \\"full\\";\\nexport let hovered = false;\\nexport let placeholder = void 0;\\nconst defs = {\\n    image: \\"upload_text.drop_image\\",\\n    video: \\"upload_text.drop_video\\",\\n    audio: \\"upload_text.drop_audio\\",\\n    file: \\"upload_text.drop_file\\",\\n    csv: \\"upload_text.drop_csv\\",\\n    gallery: \\"upload_text.drop_gallery\\",\\n    clipboard: \\"upload_text.paste_clipboard\\"\\n};\\n$: [heading, paragraph] = placeholder ? inject(placeholder) : [false, false];\\n<\/script>\\n\\n<div class=\\"wrap\\">\\n\\t<span class=\\"icon-wrap\\" class:hovered>\\n\\t\\t{#if type === \\"clipboard\\"}\\n\\t\\t\\t<ImagePaste />\\n\\t\\t{:else}\\n\\t\\t\\t<UploadIcon />\\n\\t\\t{/if}\\n\\t</span>\\n\\n\\t{#if heading || paragraph}\\n\\t\\t{#if heading}\\n\\t\\t\\t<h2>{heading}</h2>\\n\\t\\t{/if}\\n\\t\\t{#if paragraph}\\n\\t\\t\\t<p>{paragraph}</p>\\n\\t\\t{/if}\\n\\t{:else}\\n\\t\\t{i18n(defs[type] || defs.file)}\\n\\n\\t\\t{#if mode !== \\"short\\"}\\n\\t\\t\\t<span class=\\"or\\">- {i18n(\\"common.or\\")} -</span>\\n\\t\\t\\t{message || i18n(\\"upload_text.click_to_upload\\")}\\n\\t\\t{/if}\\n\\t{/if}\\n</div>\\n\\n<style>\\n\\th2 {\\n\\t\\tfont-size: var(--text-xl) !important;\\n\\t}\\n\\n\\tp,\\n\\th2 {\\n\\t\\twhite-space: pre-line;\\n\\t}\\n\\n\\t.wrap {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tmin-height: var(--size-60);\\n\\t\\tcolor: var(--block-label-text-color);\\n\\t\\tline-height: var(--line-md);\\n\\t\\theight: 100%;\\n\\t\\tpadding-top: var(--size-3);\\n\\t\\ttext-align: center;\\n\\t\\tmargin: auto var(--spacing-lg);\\n\\t}\\n\\n\\t.or {\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t\\tdisplay: flex;\\n\\t}\\n\\n\\t.icon-wrap {\\n\\t\\twidth: 30px;\\n\\t\\tmargin-bottom: var(--spacing-lg);\\n\\t}\\n\\n\\t@media (min-width: 768px) {\\n\\t\\t.wrap {\\n\\t\\t\\tfont-size: var(--text-lg);\\n\\t\\t}\\n\\t}\\n\\n\\t.hovered {\\n\\t\\tcolor: var(--color-accent);\\n\\t}</style>\\n"],"names":[],"mappings":"AA+CC,iBAAG,CACF,SAAS,CAAE,IAAI,SAAS,CAAC,CAAC,UAC3B,CAEA,gBAAC,CACD,iBAAG,CACF,WAAW,CAAE,QACd,CAEA,oBAAM,CACL,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MAAM,CACtB,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,UAAU,CAAE,IAAI,SAAS,CAAC,CAC1B,KAAK,CAAE,IAAI,wBAAwB,CAAC,CACpC,WAAW,CAAE,IAAI,SAAS,CAAC,CAC3B,MAAM,CAAE,IAAI,CACZ,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,UAAU,CAAE,MAAM,CAClB,MAAM,CAAE,IAAI,CAAC,IAAI,YAAY,CAC9B,CAEA,kBAAI,CACH,KAAK,CAAE,IAAI,yBAAyB,CAAC,CACrC,OAAO,CAAE,IACV,CAEA,yBAAW,CACV,KAAK,CAAE,IAAI,CACX,aAAa,CAAE,IAAI,YAAY,CAChC,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,oBAAM,CACL,SAAS,CAAE,IAAI,SAAS,CACzB,CACD,CAEA,uBAAS,CACR,KAAK,CAAE,IAAI,cAAc,CAC1B"}'},Ze=create_ssr_component((o,t,e,n)=>{let l,A,{type:i="file"}=t,{i18n:s}=t,{message:a=void 0}=t,{mode:d="full"}=t,{hovered:g=!1}=t,{placeholder:h=void 0}=t;const p={image:"upload_text.drop_image",video:"upload_text.drop_video",audio:"upload_text.drop_audio",file:"upload_text.drop_file",csv:"upload_text.drop_csv",gallery:"upload_text.drop_gallery",clipboard:"upload_text.paste_clipboard"};return t.type===void 0&&e.type&&i!==void 0&&e.type(i),t.i18n===void 0&&e.i18n&&s!==void 0&&e.i18n(s),t.message===void 0&&e.message&&a!==void 0&&e.message(a),t.mode===void 0&&e.mode&&d!==void 0&&e.mode(d),t.hovered===void 0&&e.hovered&&g!==void 0&&e.hovered(g),t.placeholder===void 0&&e.placeholder&&h!==void 0&&e.placeholder(h),o.css.add(gt),[l,A]=h?ut$1(h):[!1,!1],`<div class="wrap svelte-12ioyct"><span class="${["icon-wrap svelte-12ioyct",g?"hovered":""].join(" ").trim()}">${i==="clipboard"?`${validate_component(Y,"ImagePaste").$$render(o,{},{},{})}`:`${validate_component(Q,"UploadIcon").$$render(o,{},{},{})}`}</span> ${l||A?`${l?`<h2 class="svelte-12ioyct">${escape(l)}</h2>`:""} ${A?`<p class="svelte-12ioyct">${escape(A)}</p>`:""}`:`${escape(s(p[i]||p.file))} ${d!=="short"?`<span class="or svelte-12ioyct">- ${escape(s("common.or"))} -</span> ${escape(a||s("upload_text.click_to_upload"))}`:""}`} </div>`});const ft={code:".source-selection.svelte-snayfm{display:flex;align-items:center;justify-content:center;border-top:1px solid var(--border-color-primary);width:100%;margin-left:auto;margin-right:auto;height:var(--size-10)}.icon.svelte-snayfm{width:22px;height:22px;margin:var(--spacing-lg) var(--spacing-xs);padding:var(--spacing-xs);color:var(--neutral-400);border-radius:var(--radius-md)}.selected.svelte-snayfm{color:var(--color-accent)}.icon.svelte-snayfm:hover,.icon.svelte-snayfm:focus{color:var(--color-accent)}",map:'{"version":3,"file":"SelectSource.svelte","sources":["SelectSource.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { Microphone, Upload, Webcam, ImagePaste } from \\"@gradio/icons\\";\\nexport let sources;\\nexport let active_source;\\nexport let handle_clear = () => {\\n};\\nexport let handle_select = () => {\\n};\\n$: unique_sources = [...new Set(sources)];\\nasync function handle_select_source(source) {\\n    handle_clear();\\n    active_source = source;\\n    handle_select(source);\\n}\\n<\/script>\\n\\n{#if unique_sources.length > 1}\\n\\t<span class=\\"source-selection\\" data-testid=\\"source-select\\">\\n\\t\\t{#if sources.includes(\\"upload\\")}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"icon\\"\\n\\t\\t\\t\\tclass:selected={active_source === \\"upload\\" || !active_source}\\n\\t\\t\\t\\taria-label=\\"Upload file\\"\\n\\t\\t\\t\\ton:click={() => handle_select_source(\\"upload\\")}><Upload /></button\\n\\t\\t\\t>\\n\\t\\t{/if}\\n\\n\\t\\t{#if sources.includes(\\"microphone\\")}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"icon\\"\\n\\t\\t\\t\\tclass:selected={active_source === \\"microphone\\"}\\n\\t\\t\\t\\taria-label=\\"Record audio\\"\\n\\t\\t\\t\\ton:click={() => handle_select_source(\\"microphone\\")}\\n\\t\\t\\t\\t><Microphone /></button\\n\\t\\t\\t>\\n\\t\\t{/if}\\n\\n\\t\\t{#if sources.includes(\\"webcam\\")}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"icon\\"\\n\\t\\t\\t\\tclass:selected={active_source === \\"webcam\\"}\\n\\t\\t\\t\\taria-label=\\"Capture from camera\\"\\n\\t\\t\\t\\ton:click={() => handle_select_source(\\"webcam\\")}><Webcam /></button\\n\\t\\t\\t>\\n\\t\\t{/if}\\n\\t\\t{#if sources.includes(\\"clipboard\\")}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"icon\\"\\n\\t\\t\\t\\tclass:selected={active_source === \\"clipboard\\"}\\n\\t\\t\\t\\taria-label=\\"Paste from clipboard\\"\\n\\t\\t\\t\\ton:click={() => handle_select_source(\\"clipboard\\")}\\n\\t\\t\\t\\t><ImagePaste /></button\\n\\t\\t\\t>\\n\\t\\t{/if}\\n\\t</span>\\n{/if}\\n\\n<style>\\n\\t.source-selection {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\tborder-top: 1px solid var(--border-color-primary);\\n\\t\\twidth: 100%;\\n\\t\\tmargin-left: auto;\\n\\t\\tmargin-right: auto;\\n\\t\\theight: var(--size-10);\\n\\t}\\n\\n\\t.icon {\\n\\t\\twidth: 22px;\\n\\t\\theight: 22px;\\n\\t\\tmargin: var(--spacing-lg) var(--spacing-xs);\\n\\t\\tpadding: var(--spacing-xs);\\n\\t\\tcolor: var(--neutral-400);\\n\\t\\tborder-radius: var(--radius-md);\\n\\t}\\n\\n\\t.selected {\\n\\t\\tcolor: var(--color-accent);\\n\\t}\\n\\n\\t.icon:hover,\\n\\t.icon:focus {\\n\\t\\tcolor: var(--color-accent);\\n\\t}</style>\\n"],"names":[],"mappings":"AAyDC,+BAAkB,CACjB,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MAAM,CACnB,eAAe,CAAE,MAAM,CACvB,UAAU,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,sBAAsB,CAAC,CACjD,KAAK,CAAE,IAAI,CACX,WAAW,CAAE,IAAI,CACjB,YAAY,CAAE,IAAI,CAClB,MAAM,CAAE,IAAI,SAAS,CACtB,CAEA,mBAAM,CACL,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IAAI,CACZ,MAAM,CAAE,IAAI,YAAY,CAAC,CAAC,IAAI,YAAY,CAAC,CAC3C,OAAO,CAAE,IAAI,YAAY,CAAC,CAC1B,KAAK,CAAE,IAAI,aAAa,CAAC,CACzB,aAAa,CAAE,IAAI,WAAW,CAC/B,CAEA,uBAAU,CACT,KAAK,CAAE,IAAI,cAAc,CAC1B,CAEA,mBAAK,MAAM,CACX,mBAAK,MAAO,CACX,KAAK,CAAE,IAAI,cAAc,CAC1B"}'},Ve=create_ssr_component((o,t,e,n)=>{let l,{sources:A}=t,{active_source:i}=t,{handle_clear:s=()=>{}}=t,{handle_select:a=()=>{}}=t;return t.sources===void 0&&e.sources&&A!==void 0&&e.sources(A),t.active_source===void 0&&e.active_source&&i!==void 0&&e.active_source(i),t.handle_clear===void 0&&e.handle_clear&&s!==void 0&&e.handle_clear(s),t.handle_select===void 0&&e.handle_select&&a!==void 0&&e.handle_select(a),o.css.add(ft),l=[...new Set(A)],`${l.length>1?`<span class="source-selection svelte-snayfm" data-testid="source-select">${A.includes("upload")?`<button class="${["icon svelte-snayfm",i==="upload"||!i?"selected":""].join(" ").trim()}" aria-label="Upload file">${validate_component(Q,"Upload").$$render(o,{},{},{})}</button>`:""} ${A.includes("microphone")?`<button class="${["icon svelte-snayfm",i==="microphone"?"selected":""].join(" ").trim()}" aria-label="Record audio">${validate_component(ct$2,"Microphone").$$render(o,{},{},{})}</button>`:""} ${A.includes("webcam")?`<button class="${["icon svelte-snayfm",i==="webcam"?"selected":""].join(" ").trim()}" aria-label="Capture from camera">${validate_component(ht,"Webcam").$$render(o,{},{},{})}</button>`:""} ${A.includes("clipboard")?`<button class="${["icon svelte-snayfm",i==="clipboard"?"selected":""].join(" ").trim()}" aria-label="Paste from clipboard">${validate_component(Y,"ImagePaste").$$render(o,{},{},{})}</button>`:""}</span>`:""}`}),mt={code:'.icon-button-wrapper.svelte-ud4hud{display:flex;flex-direction:row;align-items:center;justify-content:center;z-index:var(--layer-2);gap:var(--spacing-sm);box-shadow:var(--shadow-drop);border:1px solid var(--border-color-primary);background:var(--block-background-fill);padding:var(--spacing-xxs)}.icon-button-wrapper.hide-top-corner.svelte-ud4hud{border-top:none;border-right:none;border-radius:var(--block-label-right-radius)}.icon-button-wrapper.display-top-corner.svelte-ud4hud{border-radius:var(--radius-sm) 0 0 var(--radius-sm);top:var(--spacing-sm);right:-1px}.icon-button-wrapper.svelte-ud4hud:not(.top-panel){border:1px solid var(--border-color-primary);border-radius:var(--radius-sm)}.top-panel.svelte-ud4hud{position:absolute;top:var(--block-label-margin);right:var(--block-label-margin);margin:0}.icon-button-wrapper.svelte-ud4hud button{margin:var(--spacing-xxs);border-radius:var(--radius-xs);position:relative}.icon-button-wrapper.svelte-ud4hud a.download-link:not(:last-child),.icon-button-wrapper.svelte-ud4hud button:not(:last-child){margin-right:var(--spacing-xxs)}.icon-button-wrapper.svelte-ud4hud a.download-link:not(:last-child):not(.no-border *)::after,.icon-button-wrapper.svelte-ud4hud button:not(:last-child):not(.no-border *)::after{content:"";position:absolute;right:-4.5px;top:15%;height:70%;width:1px;background-color:var(--border-color-primary)}.icon-button-wrapper.svelte-ud4hud > *{height:100%}',map:'{"version":3,"file":"IconButtonWrapper.svelte","sources":["IconButtonWrapper.svelte"],"sourcesContent":["<script>\\n\\texport let top_panel = true;\\n\\texport let display_top_corner = false;\\n<\/script>\\n\\n<div\\n\\tclass={`icon-button-wrapper ${top_panel ? \\"top-panel\\" : \\"\\"} ${display_top_corner ? \\"display-top-corner\\" : \\"hide-top-corner\\"}`}\\n>\\n\\t<slot></slot>\\n</div>\\n\\n<style>\\n\\t.icon-button-wrapper {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: row;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tgap: var(--spacing-sm);\\n\\t\\tbox-shadow: var(--shadow-drop);\\n\\t\\tborder: 1px solid var(--border-color-primary);\\n\\t\\tbackground: var(--block-background-fill);\\n\\t\\tpadding: var(--spacing-xxs);\\n\\t}\\n\\n\\t.icon-button-wrapper.hide-top-corner {\\n\\t\\tborder-top: none;\\n\\t\\tborder-right: none;\\n\\t\\tborder-radius: var(--block-label-right-radius);\\n\\t}\\n\\n\\t.icon-button-wrapper.display-top-corner {\\n\\t\\tborder-radius: var(--radius-sm) 0 0 var(--radius-sm);\\n\\t\\ttop: var(--spacing-sm);\\n\\t\\tright: -1px;\\n\\t}\\n\\n\\t.icon-button-wrapper:not(.top-panel) {\\n\\t\\tborder: 1px solid var(--border-color-primary);\\n\\t\\tborder-radius: var(--radius-sm);\\n\\t}\\n\\n\\t.top-panel {\\n\\t\\tposition: absolute;\\n\\t\\ttop: var(--block-label-margin);\\n\\t\\tright: var(--block-label-margin);\\n\\t\\tmargin: 0;\\n\\t}\\n\\n\\t.icon-button-wrapper :global(button) {\\n\\t\\tmargin: var(--spacing-xxs);\\n\\t\\tborder-radius: var(--radius-xs);\\n\\t\\tposition: relative;\\n\\t}\\n\\n\\t.icon-button-wrapper :global(a.download-link:not(:last-child)),\\n\\t.icon-button-wrapper :global(button:not(:last-child)) {\\n\\t\\tmargin-right: var(--spacing-xxs);\\n\\t}\\n\\n\\t.icon-button-wrapper\\n\\t\\t:global(a.download-link:not(:last-child):not(.no-border *)::after),\\n\\t.icon-button-wrapper\\n\\t\\t:global(button:not(:last-child):not(.no-border *)::after) {\\n\\t\\tcontent: \\"\\";\\n\\t\\tposition: absolute;\\n\\t\\tright: -4.5px;\\n\\t\\ttop: 15%;\\n\\t\\theight: 70%;\\n\\t\\twidth: 1px;\\n\\t\\tbackground-color: var(--border-color-primary);\\n\\t}\\n\\n\\t.icon-button-wrapper :global(> *) {\\n\\t\\theight: 100%;\\n\\t}</style>\\n"],"names":[],"mappings":"AAYC,kCAAqB,CACpB,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,GAAG,CACnB,WAAW,CAAE,MAAM,CACnB,eAAe,CAAE,MAAM,CACvB,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,GAAG,CAAE,IAAI,YAAY,CAAC,CACtB,UAAU,CAAE,IAAI,aAAa,CAAC,CAC9B,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,sBAAsB,CAAC,CAC7C,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,OAAO,CAAE,IAAI,aAAa,CAC3B,CAEA,oBAAoB,8BAAiB,CACpC,UAAU,CAAE,IAAI,CAChB,YAAY,CAAE,IAAI,CAClB,aAAa,CAAE,IAAI,0BAA0B,CAC9C,CAEA,oBAAoB,iCAAoB,CACvC,aAAa,CAAE,IAAI,WAAW,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,IAAI,WAAW,CAAC,CACpD,GAAG,CAAE,IAAI,YAAY,CAAC,CACtB,KAAK,CAAE,IACR,CAEA,kCAAoB,KAAK,UAAU,CAAE,CACpC,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,sBAAsB,CAAC,CAC7C,aAAa,CAAE,IAAI,WAAW,CAC/B,CAEA,wBAAW,CACV,QAAQ,CAAE,QAAQ,CAClB,GAAG,CAAE,IAAI,oBAAoB,CAAC,CAC9B,KAAK,CAAE,IAAI,oBAAoB,CAAC,CAChC,MAAM,CAAE,CACT,CAEA,kCAAoB,CAAS,MAAQ,CACpC,MAAM,CAAE,IAAI,aAAa,CAAC,CAC1B,aAAa,CAAE,IAAI,WAAW,CAAC,CAC/B,QAAQ,CAAE,QACX,CAEA,kCAAoB,CAAS,gCAAiC,CAC9D,kCAAoB,CAAS,uBAAyB,CACrD,YAAY,CAAE,IAAI,aAAa,CAChC,CAEA,kCAAoB,CACX,yDAA0D,CACnE,kCAAoB,CACX,gDAAkD,CAC1D,OAAO,CAAE,EAAE,CACX,QAAQ,CAAE,QAAQ,CAClB,KAAK,CAAE,MAAM,CACb,GAAG,CAAE,GAAG,CACR,MAAM,CAAE,GAAG,CACX,KAAK,CAAE,GAAG,CACV,gBAAgB,CAAE,IAAI,sBAAsB,CAC7C,CAEA,kCAAoB,CAAS,GAAK,CACjC,MAAM,CAAE,IACT"}'},Ue=create_ssr_component((o,t,e,n)=>{let{top_panel:l=!0}=t,{display_top_corner:A=!1}=t;return t.top_panel===void 0&&e.top_panel&&l!==void 0&&e.top_panel(l),t.display_top_corner===void 0&&e.display_top_corner&&A!==void 0&&e.display_top_corner(A),o.css.add(mt),`<div class="${escape(null_to_empty(`icon-button-wrapper ${l?"top-panel":""} ${A?"display-top-corner":"hide-top-corner"}`),!0)+" svelte-ud4hud"}">${n.default?n.default({}):""} </div>`}),Te=create_ssr_component((o,t,e,n)=>{createEventDispatcher();let{fullscreen:l}=t;return t.fullscreen===void 0&&e.fullscreen&&l!==void 0&&e.fullscreen(l),`${l?`${validate_component(O$1,"IconButton").$$render(o,{Icon:Ct$1,label:"Exit fullscreen mode"},{},{})}`:`${validate_component(O$1,"IconButton").$$render(o,{Icon:dt$1,label:"Fullscreen"},{},{})}`}`});

function O(r){let A=["","k","M","G","T","P","E","Z"],t=0;for(;r>1e3&&t<A.length-1;)r/=1e3,t++;let p=A[t];return (Number.isInteger(r)?r:r.toFixed(1))+p}const ot={code:"svg.svelte-zyxd38.svelte-zyxd38{width:var(--size-20);height:var(--size-20)}svg.svelte-zyxd38 path.svelte-zyxd38{fill:var(--loader-color)}div.svelte-zyxd38.svelte-zyxd38{z-index:var(--layer-2)}.margin.svelte-zyxd38.svelte-zyxd38{margin:var(--size-4)}",map:'{"version":3,"file":"Loader.svelte","sources":["Loader.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { onMount } from \\"svelte\\";\\nimport { spring } from \\"svelte/motion\\";\\nexport let margin = true;\\nconst top = spring([0, 0]);\\nconst bottom = spring([0, 0]);\\nlet dismounted;\\nasync function animate() {\\n    await Promise.all([top.set([125, 140]), bottom.set([-125, -140])]);\\n    await Promise.all([top.set([-125, 140]), bottom.set([125, -140])]);\\n    await Promise.all([top.set([-125, 0]), bottom.set([125, -0])]);\\n    await Promise.all([top.set([125, 0]), bottom.set([-125, 0])]);\\n}\\nasync function run() {\\n    await animate();\\n    if (!dismounted)\\n        run();\\n}\\nasync function loading() {\\n    await Promise.all([top.set([125, 0]), bottom.set([-125, 0])]);\\n    run();\\n}\\nonMount(() => {\\n    loading();\\n    return () => dismounted = true;\\n});\\n<\/script>\\n\\n<div class:margin>\\n\\t<svg\\n\\t\\tviewBox=\\"-1200 -1200 3000 3000\\"\\n\\t\\tfill=\\"none\\"\\n\\t\\txmlns=\\"http://www.w3.org/2000/svg\\"\\n\\t>\\n\\t\\t<g style=\\"transform: translate({$top[0]}px, {$top[1]}px);\\">\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M255.926 0.754768L509.702 139.936V221.027L255.926 81.8465V0.754768Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t\\tfill-opacity=\\"0.4\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M509.69 139.936L254.981 279.641V361.255L509.69 221.55V139.936Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M0.250138 139.937L254.981 279.641V361.255L0.250138 221.55V139.937Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t\\tfill-opacity=\\"0.4\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M255.923 0.232622L0.236328 139.936V221.55L255.923 81.8469V0.232622Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t/>\\n\\t\\t</g>\\n\\t\\t<g style=\\"transform: translate({$bottom[0]}px, {$bottom[1]}px);\\">\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M255.926 141.5L509.702 280.681V361.773L255.926 222.592V141.5Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t\\tfill-opacity=\\"0.4\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M509.69 280.679L254.981 420.384V501.998L509.69 362.293V280.679Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M0.250138 280.681L254.981 420.386V502L0.250138 362.295V280.681Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t\\tfill-opacity=\\"0.4\\"\\n\\t\\t\\t/>\\n\\t\\t\\t<path\\n\\t\\t\\t\\td=\\"M255.923 140.977L0.236328 280.68V362.294L255.923 222.591V140.977Z\\"\\n\\t\\t\\t\\tfill=\\"#FF7C00\\"\\n\\t\\t\\t/>\\n\\t\\t</g>\\n\\t</svg>\\n</div>\\n\\n<style>\\n\\tsvg {\\n\\t\\twidth: var(--size-20);\\n\\t\\theight: var(--size-20);\\n\\t}\\n\\n\\tsvg path {\\n\\t\\tfill: var(--loader-color);\\n\\t}\\n\\n\\tdiv {\\n\\t\\tz-index: var(--layer-2);\\n\\t}\\n\\n\\t.margin {\\n\\t\\tmargin: var(--size-4);\\n\\t}</style>\\n"],"names":[],"mappings":"AA6EC,+BAAI,CACH,KAAK,CAAE,IAAI,SAAS,CAAC,CACrB,MAAM,CAAE,IAAI,SAAS,CACtB,CAEA,iBAAG,CAAC,kBAAK,CACR,IAAI,CAAE,IAAI,cAAc,CACzB,CAEA,+BAAI,CACH,OAAO,CAAE,IAAI,SAAS,CACvB,CAEA,mCAAQ,CACP,MAAM,CAAE,IAAI,QAAQ,CACrB"}'},at$2=create_ssr_component((r,A,t,p)=>{let i,c,o,C,{margin:a=!0}=A;const n=spring([0,0]);c=subscribe(n,f=>i=f);const l=spring([0,0]);C=subscribe(l,f=>o=f);return A.margin===void 0&&t.margin&&a!==void 0&&t.margin(a),r.css.add(ot),c(),C(),`<div class="${["svelte-zyxd38",a?"margin":""].join(" ").trim()}"><svg viewBox="-1200 -1200 3000 3000" fill="none" xmlns="http://www.w3.org/2000/svg" class="svelte-zyxd38"><g style="${"transform: translate("+escape(i[0],!0)+"px, "+escape(i[1],!0)+"px);"}"><path d="M255.926 0.754768L509.702 139.936V221.027L255.926 81.8465V0.754768Z" fill="#FF7C00" fill-opacity="0.4" class="svelte-zyxd38"></path><path d="M509.69 139.936L254.981 279.641V361.255L509.69 221.55V139.936Z" fill="#FF7C00" class="svelte-zyxd38"></path><path d="M0.250138 139.937L254.981 279.641V361.255L0.250138 221.55V139.937Z" fill="#FF7C00" fill-opacity="0.4" class="svelte-zyxd38"></path><path d="M255.923 0.232622L0.236328 139.936V221.55L255.923 81.8469V0.232622Z" fill="#FF7C00" class="svelte-zyxd38"></path></g><g style="${"transform: translate("+escape(o[0],!0)+"px, "+escape(o[1],!0)+"px);"}"><path d="M255.926 141.5L509.702 280.681V361.773L255.926 222.592V141.5Z" fill="#FF7C00" fill-opacity="0.4" class="svelte-zyxd38"></path><path d="M509.69 280.679L254.981 420.384V501.998L509.69 362.293V280.679Z" fill="#FF7C00" class="svelte-zyxd38"></path><path d="M0.250138 280.681L254.981 420.386V502L0.250138 362.295V280.681Z" fill="#FF7C00" fill-opacity="0.4" class="svelte-zyxd38"></path><path d="M255.923 140.977L0.236328 280.68V362.294L255.923 222.591V140.977Z" fill="#FF7C00" class="svelte-zyxd38"></path></g></svg> </div>`}),lt={code:`.wrap.svelte-btia7y.svelte-btia7y{display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:var(--layer-3);transition:opacity 0.1s ease-in-out;border-radius:var(--block-radius);background:var(--block-background-fill);padding:0 var(--size-6);overflow:hidden;pointer-events:none}.wrap.center.svelte-btia7y.svelte-btia7y{top:0;right:0px;left:0px}.wrap.default.svelte-btia7y.svelte-btia7y{top:0px;right:0px;bottom:0px;left:0px}.hide.svelte-btia7y.svelte-btia7y{opacity:0;pointer-events:none}.generating.svelte-btia7y.svelte-btia7y{animation:svelte-btia7y-pulseStart 1s cubic-bezier(0.4, 0, 0.6, 1),
			svelte-btia7y-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) 1s infinite;border:2px solid var(--color-accent);background:transparent;z-index:var(--layer-1);pointer-events:none}.translucent.svelte-btia7y.svelte-btia7y{background:none}@keyframes svelte-btia7y-pulseStart{0%{opacity:0}100%{opacity:1}}@keyframes svelte-btia7y-pulse{0%,100%{opacity:1}50%{opacity:0.5}}.loading.svelte-btia7y.svelte-btia7y{z-index:var(--layer-2);color:var(--body-text-color)}.eta-bar.svelte-btia7y.svelte-btia7y{position:absolute;top:0;right:0;bottom:0;left:0;transform-origin:left;opacity:0.8;z-index:var(--layer-1);transition:10ms;background:var(--background-fill-secondary)}.progress-bar-wrap.svelte-btia7y.svelte-btia7y{border:1px solid var(--border-color-primary);background:var(--background-fill-primary);width:55.5%;height:var(--size-4)}.progress-bar.svelte-btia7y.svelte-btia7y{transform-origin:left;background-color:var(--loader-color);width:var(--size-full);height:var(--size-full)}.progress-level.svelte-btia7y.svelte-btia7y{display:flex;flex-direction:column;align-items:center;gap:1;z-index:var(--layer-2);width:var(--size-full)}.progress-level-inner.svelte-btia7y.svelte-btia7y{margin:var(--size-2) auto;color:var(--body-text-color);font-size:var(--text-sm);font-family:var(--font-mono)}.meta-text.svelte-btia7y.svelte-btia7y{position:absolute;bottom:0;right:0;z-index:var(--layer-2);padding:var(--size-1) var(--size-2);font-size:var(--text-sm);font-family:var(--font-mono)}.meta-text-center.svelte-btia7y.svelte-btia7y{display:flex;position:absolute;top:0;right:0;justify-content:center;align-items:center;transform:translateY(var(--size-6));z-index:var(--layer-2);padding:var(--size-1) var(--size-2);font-size:var(--text-sm);font-family:var(--font-mono);text-align:center}.error.svelte-btia7y.svelte-btia7y{box-shadow:var(--shadow-drop);border:solid 1px var(--error-border-color);border-radius:var(--radius-full);background:var(--error-background-fill);padding-right:var(--size-4);padding-left:var(--size-4);color:var(--error-text-color);font-weight:var(--weight-semibold);font-size:var(--text-lg);line-height:var(--line-lg);font-family:var(--font)}.validation-error.svelte-btia7y.svelte-btia7y{pointer-events:auto;color:var(--error-text-color);font-weight:var(--weight-semibold);font-size:var(--text-lg);line-height:var(--line-lg);font-family:var(--font);position:absolute;background:var(--error-background-fill);top:0;right:0;z-index:var(--layer-3);padding:var(--size-1) var(--size-2);font-size:var(--text-md);text-align:center;border-bottom-left-radius:var(--radius-sm);border-bottom:1px solid var(--error-border-color);border-left:1px solid var(--error-border-color);display:flex;justify-content:space-between;align-items:center;gap:var(--spacing-xl)}.minimal.svelte-btia7y.svelte-btia7y{pointer-events:none}.minimal.svelte-btia7y .progress-text.svelte-btia7y{background:var(--block-background-fill)}.border.svelte-btia7y.svelte-btia7y{border:1px solid var(--border-color-primary)}.clear-status.svelte-btia7y.svelte-btia7y{position:absolute;display:flex;top:var(--size-2);right:var(--size-2);justify-content:flex-end;gap:var(--spacing-sm);z-index:var(--layer-1)}`,map:'{"version":3,"file":"index.svelte","sources":["index.svelte"],"sourcesContent":["<script context=\\"module\\" lang=\\"ts\\">import { tick } from \\"svelte\\";\\nimport { pretty_si } from \\"./utils\\";\\nlet items = [];\\nlet called = false;\\nconst is_browser = typeof window !== \\"undefined\\";\\nconst raf = is_browser ? window.requestAnimationFrame : (cb) => {\\n};\\nasync function scroll_into_view(el, enable = true) {\\n    if (window.__gradio_mode__ === \\"website\\" || window.__gradio_mode__ !== \\"app\\" && enable !== true) {\\n        return;\\n    }\\n    items.push(el);\\n    if (!called)\\n        called = true;\\n    else\\n        return;\\n    await tick();\\n    raf(() => {\\n        let min = [0, 0];\\n        for (let i = 0; i < items.length; i++) {\\n            const element = items[i];\\n            const box = element.getBoundingClientRect();\\n            if (i === 0 || box.top + window.scrollY <= min[0]) {\\n                min[0] = box.top + window.scrollY;\\n                min[1] = i;\\n            }\\n        }\\n        window.scrollTo({ top: min[0] - 20, behavior: \\"smooth\\" });\\n        called = false;\\n        items = [];\\n    });\\n}\\n<\/script>\\n\\n<script lang=\\"ts\\">import { onDestroy } from \\"svelte\\";\\nimport Loader from \\"./Loader.svelte\\";\\nimport { createEventDispatcher } from \\"svelte\\";\\nimport { IconButton } from \\"@gradio/atoms\\";\\nimport { Clear } from \\"@gradio/icons\\";\\nconst dispatch = createEventDispatcher();\\nexport let i18n;\\nexport let eta = null;\\nexport let queue_position;\\nexport let queue_size;\\nexport let status;\\nexport let scroll_to_output = false;\\nexport let timer = true;\\nexport let show_progress = \\"full\\";\\nexport let message = null;\\nexport let progress = null;\\nexport let variant = \\"default\\";\\nexport let loading_text = \\"Loading...\\";\\nexport let absolute = true;\\nexport let translucent = false;\\nexport let border = false;\\nexport let autoscroll;\\nexport let validation_error = null;\\nexport let show_validation_error = true;\\nlet el;\\nlet _timer = false;\\nlet timer_start = 0;\\nlet timer_diff = 0;\\nlet old_eta = null;\\nlet eta_from_start = null;\\nlet message_visible = false;\\nlet eta_level = 0;\\nlet progress_level = null;\\nlet last_progress_level = void 0;\\nlet progress_bar = null;\\nlet show_eta_bar = true;\\n$: eta_level = eta_from_start === null || eta_from_start <= 0 || !timer_diff ? null : Math.min(timer_diff / eta_from_start, 1);\\n$: if (progress != null) {\\n    show_eta_bar = false;\\n}\\n$: {\\n    if (progress != null) {\\n        progress_level = progress.map((p) => {\\n            if (p.index != null && p.length != null) {\\n                return p.index / p.length;\\n            }\\n            else if (p.progress != null) {\\n                return p.progress;\\n            }\\n            return void 0;\\n        });\\n    }\\n    else {\\n        progress_level = null;\\n    }\\n    if (progress_level) {\\n        last_progress_level = progress_level[progress_level.length - 1];\\n        if (progress_bar) {\\n            if (last_progress_level === 0) {\\n                progress_bar.style.transition = \\"0\\";\\n            }\\n            else {\\n                progress_bar.style.transition = \\"150ms\\";\\n            }\\n        }\\n    }\\n    else {\\n        last_progress_level = void 0;\\n    }\\n}\\nconst start_timer = () => {\\n    eta = old_eta = formatted_eta = null;\\n    timer_start = performance.now();\\n    timer_diff = 0;\\n    _timer = true;\\n    run();\\n};\\nfunction run() {\\n    raf(() => {\\n        timer_diff = (performance.now() - timer_start) / 1e3;\\n        if (_timer)\\n            run();\\n    });\\n}\\nfunction stop_timer() {\\n    timer_diff = 0;\\n    eta = old_eta = formatted_eta = null;\\n    if (!_timer)\\n        return;\\n    _timer = false;\\n}\\nonDestroy(() => {\\n    if (_timer)\\n        stop_timer();\\n});\\n$: {\\n    if (status === \\"pending\\") {\\n        start_timer();\\n    }\\n    else {\\n        stop_timer();\\n    }\\n}\\n$: el && scroll_to_output && (status === \\"pending\\" || status === \\"complete\\") && scroll_into_view(el, autoscroll);\\nlet formatted_eta = null;\\n$: {\\n    if (eta === null) {\\n        eta = old_eta;\\n    }\\n    if (eta != null && old_eta !== eta) {\\n        eta_from_start = (performance.now() - timer_start) / 1e3 + eta;\\n        formatted_eta = eta_from_start.toFixed(1);\\n        old_eta = eta;\\n    }\\n}\\nlet show_message_timeout = null;\\nfunction close_message() {\\n    message_visible = false;\\n    if (show_message_timeout !== null) {\\n        clearTimeout(show_message_timeout);\\n    }\\n}\\n$: {\\n    close_message();\\n    if (status === \\"error\\" && message) {\\n        message_visible = true;\\n    }\\n}\\n$: formatted_timer = timer_diff.toFixed(1);\\n<\/script>\\n\\n<div\\n\\tclass=\\"wrap {variant} {show_progress}\\"\\n\\tclass:hide={(!status ||\\n\\t\\tstatus === \\"complete\\" ||\\n\\t\\tshow_progress === \\"hidden\\" ||\\n\\t\\tstatus == \\"streaming\\") &&\\n\\t\\t!validation_error}\\n\\tclass:translucent={(variant === \\"center\\" &&\\n\\t\\t(status === \\"pending\\" || status === \\"error\\")) ||\\n\\t\\ttranslucent ||\\n\\t\\tshow_progress === \\"minimal\\" ||\\n\\t\\tvalidation_error}\\n\\tclass:generating={status === \\"generating\\" && show_progress === \\"full\\"}\\n\\tclass:border\\n\\tstyle:position={absolute ? \\"absolute\\" : \\"static\\"}\\n\\tstyle:padding={absolute ? \\"0\\" : \\"var(--size-8) 0\\"}\\n\\tbind:this={el}\\n>\\n\\t{#if validation_error && show_validation_error}\\n\\t\\t<div class=\\"validation-error\\">\\n\\t\\t\\t{validation_error}\\n\\t\\t\\t<button\\n\\t\\t\\t\\t><IconButton\\n\\t\\t\\t\\t\\tIcon={Clear}\\n\\t\\t\\t\\t\\tlabel={i18n(\\"common.clear\\")}\\n\\t\\t\\t\\t\\tdisabled={false}\\n\\t\\t\\t\\t\\tsize=\\"x-small\\"\\n\\t\\t\\t\\t\\tbackground=\\"var(--background-fill-primary)\\"\\n\\t\\t\\t\\t\\tcolor=\\"var(--error-background-text)\\"\\n\\t\\t\\t\\t\\tborder=\\"var(--border-color-primary)\\"\\n\\t\\t\\t\\t\\ton:click={() => (validation_error = null)}\\n\\t\\t\\t\\t/></button\\n\\t\\t\\t>\\n\\t\\t</div>\\n\\t{/if}\\n\\t{#if status === \\"pending\\"}\\n\\t\\t{#if variant === \\"default\\" && show_eta_bar && show_progress === \\"full\\"}\\n\\t\\t\\t<div\\n\\t\\t\\t\\tclass=\\"eta-bar\\"\\n\\t\\t\\t\\tstyle:transform=\\"translateX({(eta_level || 0) * 100 - 100}%)\\"\\n\\t\\t\\t/>\\n\\t\\t{/if}\\n\\t\\t<div\\n\\t\\t\\tclass:meta-text-center={variant === \\"center\\"}\\n\\t\\t\\tclass:meta-text={variant === \\"default\\"}\\n\\t\\t\\tclass=\\"progress-text\\"\\n\\t\\t>\\n\\t\\t\\t{#if progress}\\n\\t\\t\\t\\t{#each progress as p}\\n\\t\\t\\t\\t\\t{#if p.index != null}\\n\\t\\t\\t\\t\\t\\t{#if p.length != null}\\n\\t\\t\\t\\t\\t\\t\\t{pretty_si(p.index || 0)}/{pretty_si(p.length)}\\n\\t\\t\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t\\t\\t{pretty_si(p.index || 0)}\\n\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t{p.unit} | {\\" \\"}\\n\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t{/each}\\n\\t\\t\\t{:else if queue_position !== null && queue_size !== undefined && queue_position >= 0}\\n\\t\\t\\t\\tqueue: {queue_position + 1}/{queue_size} |\\n\\t\\t\\t{:else if queue_position === 0}\\n\\t\\t\\t\\tprocessing |\\n\\t\\t\\t{/if}\\n\\n\\t\\t\\t{#if timer}\\n\\t\\t\\t\\t{formatted_timer}{eta ? `/${formatted_eta}` : \\"\\"}s\\n\\t\\t\\t{/if}\\n\\t\\t</div>\\n\\n\\t\\t{#if last_progress_level != null}\\n\\t\\t\\t<div class=\\"progress-level\\">\\n\\t\\t\\t\\t<div class=\\"progress-level-inner\\">\\n\\t\\t\\t\\t\\t{#if progress != null}\\n\\t\\t\\t\\t\\t\\t{#each progress as p, i}\\n\\t\\t\\t\\t\\t\\t\\t{#if p.desc != null || (progress_level && progress_level[i] != null)}\\n\\t\\t\\t\\t\\t\\t\\t\\t{#if i !== 0}\\n\\t\\t\\t\\t\\t\\t\\t\\t\\t&nbsp;/\\n\\t\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t\\t\\t{#if p.desc != null}\\n\\t\\t\\t\\t\\t\\t\\t\\t\\t{p.desc}\\n\\t\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t\\t\\t{#if p.desc != null && progress_level && progress_level[i] != null}\\n\\t\\t\\t\\t\\t\\t\\t\\t\\t-\\n\\t\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t\\t\\t{#if progress_level != null}\\n\\t\\t\\t\\t\\t\\t\\t\\t\\t{(100 * (progress_level[i] || 0)).toFixed(1)}%\\n\\t\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t{/each}\\n\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t</div>\\n\\n\\t\\t\\t\\t<div class=\\"progress-bar-wrap\\">\\n\\t\\t\\t\\t\\t<div\\n\\t\\t\\t\\t\\t\\tbind:this={progress_bar}\\n\\t\\t\\t\\t\\t\\tclass=\\"progress-bar\\"\\n\\t\\t\\t\\t\\t\\tstyle:width=\\"{last_progress_level * 100}%\\"\\n\\t\\t\\t\\t\\t/>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t</div>\\n\\t\\t{:else if show_progress === \\"full\\"}\\n\\t\\t\\t<Loader margin={variant === \\"default\\"} />\\n\\t\\t{/if}\\n\\n\\t\\t{#if !timer}\\n\\t\\t\\t<p class=\\"loading\\">{loading_text}</p>\\n\\t\\t\\t<slot name=\\"additional-loading-text\\" />\\n\\t\\t{/if}\\n\\t{:else if status === \\"error\\"}\\n\\t\\t<div class=\\"clear-status\\">\\n\\t\\t\\t<IconButton\\n\\t\\t\\t\\tIcon={Clear}\\n\\t\\t\\t\\tlabel={i18n(\\"common.clear\\")}\\n\\t\\t\\t\\tdisabled={false}\\n\\t\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\t\\tdispatch(\\"clear_status\\");\\n\\t\\t\\t\\t}}\\n\\t\\t\\t/>\\n\\t\\t</div>\\n\\t\\t<span class=\\"error\\">{i18n(\\"common.error\\")}</span>\\n\\t\\t<slot name=\\"error\\" />\\n\\t{/if}\\n</div>\\n\\n<style>\\n\\t.wrap {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tz-index: var(--layer-3);\\n\\t\\ttransition: opacity 0.1s ease-in-out;\\n\\t\\tborder-radius: var(--block-radius);\\n\\t\\tbackground: var(--block-background-fill);\\n\\t\\tpadding: 0 var(--size-6);\\n\\t\\toverflow: hidden;\\n\\t\\tpointer-events: none;\\n\\t}\\n\\n\\t.wrap.center {\\n\\t\\ttop: 0;\\n\\t\\tright: 0px;\\n\\t\\tleft: 0px;\\n\\t}\\n\\n\\t.wrap.default {\\n\\t\\ttop: 0px;\\n\\t\\tright: 0px;\\n\\t\\tbottom: 0px;\\n\\t\\tleft: 0px;\\n\\t}\\n\\n\\t.hide {\\n\\t\\topacity: 0;\\n\\t\\tpointer-events: none;\\n\\t}\\n\\n\\t.generating {\\n\\t\\tanimation:\\n\\t\\t\\tpulseStart 1s cubic-bezier(0.4, 0, 0.6, 1),\\n\\t\\t\\tpulse 2s cubic-bezier(0.4, 0, 0.6, 1) 1s infinite;\\n\\t\\tborder: 2px solid var(--color-accent);\\n\\t\\tbackground: transparent;\\n\\t\\tz-index: var(--layer-1);\\n\\t\\tpointer-events: none;\\n\\t}\\n\\n\\t.translucent {\\n\\t\\tbackground: none;\\n\\t}\\n\\n\\t@keyframes pulseStart {\\n\\t\\t0% {\\n\\t\\t\\topacity: 0;\\n\\t\\t}\\n\\t\\t100% {\\n\\t\\t\\topacity: 1;\\n\\t\\t}\\n\\t}\\n\\n\\t@keyframes pulse {\\n\\t\\t0%,\\n\\t\\t100% {\\n\\t\\t\\topacity: 1;\\n\\t\\t}\\n\\t\\t50% {\\n\\t\\t\\topacity: 0.5;\\n\\t\\t}\\n\\t}\\n\\n\\t.loading {\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\t.eta-bar {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 0;\\n\\t\\tright: 0;\\n\\t\\tbottom: 0;\\n\\t\\tleft: 0;\\n\\t\\ttransform-origin: left;\\n\\t\\topacity: 0.8;\\n\\t\\tz-index: var(--layer-1);\\n\\t\\ttransition: 10ms;\\n\\t\\tbackground: var(--background-fill-secondary);\\n\\t}\\n\\t.progress-bar-wrap {\\n\\t\\tborder: 1px solid var(--border-color-primary);\\n\\t\\tbackground: var(--background-fill-primary);\\n\\t\\twidth: 55.5%;\\n\\t\\theight: var(--size-4);\\n\\t}\\n\\t.progress-bar {\\n\\t\\ttransform-origin: left;\\n\\t\\tbackground-color: var(--loader-color);\\n\\t\\twidth: var(--size-full);\\n\\t\\theight: var(--size-full);\\n\\t}\\n\\n\\t.progress-level {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\talign-items: center;\\n\\t\\tgap: 1;\\n\\t\\tz-index: var(--layer-2);\\n\\t\\twidth: var(--size-full);\\n\\t}\\n\\n\\t.progress-level-inner {\\n\\t\\tmargin: var(--size-2) auto;\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\tfont-size: var(--text-sm);\\n\\t\\tfont-family: var(--font-mono);\\n\\t}\\n\\n\\t.meta-text {\\n\\t\\tposition: absolute;\\n\\t\\tbottom: 0;\\n\\t\\tright: 0;\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t\\tfont-size: var(--text-sm);\\n\\t\\tfont-family: var(--font-mono);\\n\\t}\\n\\n\\t.meta-text-center {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: absolute;\\n\\t\\ttop: 0;\\n\\t\\tright: 0;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\ttransform: translateY(var(--size-6));\\n\\t\\tz-index: var(--layer-2);\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t\\tfont-size: var(--text-sm);\\n\\t\\tfont-family: var(--font-mono);\\n\\t\\ttext-align: center;\\n\\t}\\n\\n\\t.error {\\n\\t\\tbox-shadow: var(--shadow-drop);\\n\\t\\tborder: solid 1px var(--error-border-color);\\n\\t\\tborder-radius: var(--radius-full);\\n\\t\\tbackground: var(--error-background-fill);\\n\\t\\tpadding-right: var(--size-4);\\n\\t\\tpadding-left: var(--size-4);\\n\\t\\tcolor: var(--error-text-color);\\n\\t\\tfont-weight: var(--weight-semibold);\\n\\t\\tfont-size: var(--text-lg);\\n\\t\\tline-height: var(--line-lg);\\n\\t\\tfont-family: var(--font);\\n\\t}\\n\\n\\t.validation-error {\\n\\t\\tpointer-events: auto;\\n\\t\\tcolor: var(--error-text-color);\\n\\t\\tfont-weight: var(--weight-semibold);\\n\\t\\tfont-size: var(--text-lg);\\n\\t\\tline-height: var(--line-lg);\\n\\t\\tfont-family: var(--font);\\n\\t\\tposition: absolute;\\n\\t\\tbackground: var(--error-background-fill);\\n\\t\\ttop: 0;\\n\\t\\tright: 0;\\n\\t\\tz-index: var(--layer-3);\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t\\tfont-size: var(--text-md);\\n\\t\\ttext-align: center;\\n\\t\\tborder-bottom-left-radius: var(--radius-sm);\\n\\t\\tborder-bottom: 1px solid var(--error-border-color);\\n\\t\\tborder-left: 1px solid var(--error-border-color);\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: space-between;\\n\\t\\talign-items: center;\\n\\t\\tgap: var(--spacing-xl);\\n\\t}\\n\\n\\t.minimal {\\n\\t\\tpointer-events: none;\\n\\t}\\n\\n\\t.minimal .progress-text {\\n\\t\\tbackground: var(--block-background-fill);\\n\\t}\\n\\n\\t.border {\\n\\t\\tborder: 1px solid var(--border-color-primary);\\n\\t}\\n\\n\\t.clear-status {\\n\\t\\tposition: absolute;\\n\\t\\tdisplay: flex;\\n\\t\\ttop: var(--size-2);\\n\\t\\tright: var(--size-2);\\n\\t\\tjustify-content: flex-end;\\n\\t\\tgap: var(--spacing-sm);\\n\\t\\tz-index: var(--layer-1);\\n\\t}</style>\\n"],"names":[],"mappings":"AAkSC,iCAAM,CACL,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MAAM,CACtB,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,UAAU,CAAE,OAAO,CAAC,IAAI,CAAC,WAAW,CACpC,aAAa,CAAE,IAAI,cAAc,CAAC,CAClC,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,OAAO,CAAE,CAAC,CAAC,IAAI,QAAQ,CAAC,CACxB,QAAQ,CAAE,MAAM,CAChB,cAAc,CAAE,IACjB,CAEA,KAAK,mCAAQ,CACZ,GAAG,CAAE,CAAC,CACN,KAAK,CAAE,GAAG,CACV,IAAI,CAAE,GACP,CAEA,KAAK,oCAAS,CACb,GAAG,CAAE,GAAG,CACR,KAAK,CAAE,GAAG,CACV,MAAM,CAAE,GAAG,CACX,IAAI,CAAE,GACP,CAEA,iCAAM,CACL,OAAO,CAAE,CAAC,CACV,cAAc,CAAE,IACjB,CAEA,uCAAY,CACX,SAAS,CACR,wBAAU,CAAC,EAAE,CAAC,aAAa,GAAG,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CAAC,CAAC,CAAC;AAC7C,GAAG,mBAAK,CAAC,EAAE,CAAC,aAAa,GAAG,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CAAC,CAAC,CAAC,CAAC,EAAE,CAAC,QAAQ,CAClD,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,cAAc,CAAC,CACrC,UAAU,CAAE,WAAW,CACvB,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,cAAc,CAAE,IACjB,CAEA,wCAAa,CACZ,UAAU,CAAE,IACb,CAEA,WAAW,wBAAW,CACrB,EAAG,CACF,OAAO,CAAE,CACV,CACA,IAAK,CACJ,OAAO,CAAE,CACV,CACD,CAEA,WAAW,mBAAM,CAChB,EAAE,CACF,IAAK,CACJ,OAAO,CAAE,CACV,CACA,GAAI,CACH,OAAO,CAAE,GACV,CACD,CAEA,oCAAS,CACR,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CACA,oCAAS,CACR,QAAQ,CAAE,QAAQ,CAClB,GAAG,CAAE,CAAC,CACN,KAAK,CAAE,CAAC,CACR,MAAM,CAAE,CAAC,CACT,IAAI,CAAE,CAAC,CACP,gBAAgB,CAAE,IAAI,CACtB,OAAO,CAAE,GAAG,CACZ,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,UAAU,CAAE,IAAI,CAChB,UAAU,CAAE,IAAI,2BAA2B,CAC5C,CACA,8CAAmB,CAClB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,sBAAsB,CAAC,CAC7C,UAAU,CAAE,IAAI,yBAAyB,CAAC,CAC1C,KAAK,CAAE,KAAK,CACZ,MAAM,CAAE,IAAI,QAAQ,CACrB,CACA,yCAAc,CACb,gBAAgB,CAAE,IAAI,CACtB,gBAAgB,CAAE,IAAI,cAAc,CAAC,CACrC,KAAK,CAAE,IAAI,WAAW,CAAC,CACvB,MAAM,CAAE,IAAI,WAAW,CACxB,CAEA,2CAAgB,CACf,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MAAM,CACtB,WAAW,CAAE,MAAM,CACnB,GAAG,CAAE,CAAC,CACN,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,KAAK,CAAE,IAAI,WAAW,CACvB,CAEA,iDAAsB,CACrB,MAAM,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,CAC1B,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,WAAW,CAC7B,CAEA,sCAAW,CACV,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,KAAK,CAAE,CAAC,CACR,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,WAAW,CAC7B,CAEA,6CAAkB,CACjB,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,GAAG,CAAE,CAAC,CACN,KAAK,CAAE,CAAC,CACR,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,SAAS,CAAE,WAAW,IAAI,QAAQ,CAAC,CAAC,CACpC,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,WAAW,CAAC,CAC7B,UAAU,CAAE,MACb,CAEA,kCAAO,CACN,UAAU,CAAE,IAAI,aAAa,CAAC,CAC9B,MAAM,CAAE,KAAK,CAAC,GAAG,CAAC,IAAI,oBAAoB,CAAC,CAC3C,aAAa,CAAE,IAAI,aAAa,CAAC,CACjC,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,aAAa,CAAE,IAAI,QAAQ,CAAC,CAC5B,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,KAAK,CAAE,IAAI,kBAAkB,CAAC,CAC9B,WAAW,CAAE,IAAI,iBAAiB,CAAC,CACnC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,SAAS,CAAC,CAC3B,WAAW,CAAE,IAAI,MAAM,CACxB,CAEA,6CAAkB,CACjB,cAAc,CAAE,IAAI,CACpB,KAAK,CAAE,IAAI,kBAAkB,CAAC,CAC9B,WAAW,CAAE,IAAI,iBAAiB,CAAC,CACnC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,SAAS,CAAC,CAC3B,WAAW,CAAE,IAAI,MAAM,CAAC,CACxB,QAAQ,CAAE,QAAQ,CAClB,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,GAAG,CAAE,CAAC,CACN,KAAK,CAAE,CAAC,CACR,OAAO,CAAE,IAAI,SAAS,CAAC,CACvB,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACpC,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,UAAU,CAAE,MAAM,CAClB,yBAAyB,CAAE,IAAI,WAAW,CAAC,CAC3C,aAAa,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,oBAAoB,CAAC,CAClD,WAAW,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,oBAAoB,CAAC,CAChD,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,aAAa,CAC9B,WAAW,CAAE,MAAM,CACnB,GAAG,CAAE,IAAI,YAAY,CACtB,CAEA,oCAAS,CACR,cAAc,CAAE,IACjB,CAEA,sBAAQ,CAAC,4BAAe,CACvB,UAAU,CAAE,IAAI,uBAAuB,CACxC,CAEA,mCAAQ,CACP,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,sBAAsB,CAC7C,CAEA,yCAAc,CACb,QAAQ,CAAE,QAAQ,CAClB,OAAO,CAAE,IAAI,CACb,GAAG,CAAE,IAAI,QAAQ,CAAC,CAClB,KAAK,CAAE,IAAI,QAAQ,CAAC,CACpB,eAAe,CAAE,QAAQ,CACzB,GAAG,CAAE,IAAI,YAAY,CAAC,CACtB,OAAO,CAAE,IAAI,SAAS,CACvB"}'},Ct=typeof window<"u",st=Ct?window.requestAnimationFrame:r=>{},Et=create_ssr_component((r,A,t,p)=>{let i;createEventDispatcher();let{i18n:c}=A,{eta:o=null}=A,{queue_position:C}=A,{queue_size:a}=A,{status:n}=A,{scroll_to_output:l=!1}=A,{timer:v=!0}=A,{show_progress:d="full"}=A,{message:m=null}=A,{progress:u=null}=A,{variant:f="default"}=A,{loading_text:M="Loading..."}=A,{absolute:h=!0}=A,{translucent:Q=!1}=A,{border:W=!1}=A,{autoscroll:V}=A,{validation_error:I=null}=A,{show_validation_error:S=!0}=A,N,E=!1,G=0,b=0,y=null,x=null,j=0,g=null,K,H=null,T=!0;const J=()=>{o=y=z=null,G=performance.now(),b=0,E=!0,q();};function q(){st(()=>{b=(performance.now()-G)/1e3,E&&q();});}function Z(){b=0,o=y=z=null,E&&(E=!1);}onDestroy(()=>{E&&Z();});let z=null;return A.i18n===void 0&&t.i18n&&c!==void 0&&t.i18n(c),A.eta===void 0&&t.eta&&o!==void 0&&t.eta(o),A.queue_position===void 0&&t.queue_position&&C!==void 0&&t.queue_position(C),A.queue_size===void 0&&t.queue_size&&a!==void 0&&t.queue_size(a),A.status===void 0&&t.status&&n!==void 0&&t.status(n),A.scroll_to_output===void 0&&t.scroll_to_output&&l!==void 0&&t.scroll_to_output(l),A.timer===void 0&&t.timer&&v!==void 0&&t.timer(v),A.show_progress===void 0&&t.show_progress&&d!==void 0&&t.show_progress(d),A.message===void 0&&t.message&&m!==void 0&&t.message(m),A.progress===void 0&&t.progress&&u!==void 0&&t.progress(u),A.variant===void 0&&t.variant&&f!==void 0&&t.variant(f),A.loading_text===void 0&&t.loading_text&&M!==void 0&&t.loading_text(M),A.absolute===void 0&&t.absolute&&h!==void 0&&t.absolute(h),A.translucent===void 0&&t.translucent&&Q!==void 0&&t.translucent(Q),A.border===void 0&&t.border&&W!==void 0&&t.border(W),A.autoscroll===void 0&&t.autoscroll&&V!==void 0&&t.autoscroll(V),A.validation_error===void 0&&t.validation_error&&I!==void 0&&t.validation_error(I),A.show_validation_error===void 0&&t.show_validation_error&&S!==void 0&&t.show_validation_error(S),r.css.add(lt),o===null&&(o=y),o!=null&&y!==o&&(x=(performance.now()-G)/1e3+o,z=x.toFixed(1),y=o),j=x===null||x<=0||!b?null:Math.min(b/x,1),u!=null&&(T=!1),u!=null?g=u.map(s=>{if(s.index!=null&&s.length!=null)return s.index/s.length;if(s.progress!=null)return s.progress}):g=null,g?K=g[g.length-1]:K=void 0,n==="pending"?J():Z(),i=b.toFixed(1),`<div class="${["wrap "+escape(f,!0)+" "+escape(d,!0)+" svelte-btia7y",((!n||n==="complete"||d==="hidden"||n=="streaming")&&!I?"hide":"")+" "+(f==="center"&&(n==="pending"||n==="error")||Q||d==="minimal"||I?"translucent":"")+" "+(n==="generating"&&d==="full"?"generating":"")+" "+(W?"border":"")].join(" ").trim()}"${add_styles({position:h?"absolute":"static",padding:h?"0":"var(--size-8) 0"})}${add_attribute("this",N,0)}>${I&&S?`<div class="validation-error svelte-btia7y">${escape(I)} <button>${validate_component(O$1,"IconButton").$$render(r,{Icon:Ut,label:c("common.clear"),disabled:!1,size:"x-small",background:"var(--background-fill-primary)",color:"var(--error-background-text)",border:"var(--border-color-primary)"},{},{})}</button></div>`:""} ${n==="pending"?`${f==="default"&&T&&d==="full"?`<div class="eta-bar svelte-btia7y"${add_styles({transform:`translateX(${(j||0)*100-100}%)`})}></div>`:""} <div class="${["progress-text svelte-btia7y",(f==="center"?"meta-text-center":"")+" "+(f==="default"?"meta-text":"")].join(" ").trim()}">${u?`${each(u,s=>`${s.index!=null?`${s.length!=null?`${escape(O(s.index||0))}/${escape(O(s.length))}`:`${escape(O(s.index||0))}`} ${escape(s.unit)} | ${escape(" ")}`:""}`)}`:`${C!==null&&a!==void 0&&C>=0?`queue: ${escape(C+1)}/${escape(a)} |`:`${C===0?"processing |":""}`}`} ${v?`${escape(i)}${escape(o?`/${z}`:"")}s`:""}</div> ${K!=null?`<div class="progress-level svelte-btia7y"><div class="progress-level-inner svelte-btia7y">${u!=null?`${each(u,(s,k)=>`${s.desc!=null||g&&g[k]!=null?`${k!==0?" /":""} ${s.desc!=null?`${escape(s.desc)}`:""} ${s.desc!=null&&g&&g[k]!=null?"-":""} ${g!=null?`${escape((100*(g[k]||0)).toFixed(1))}%`:""}`:""}`)}`:""}</div> <div class="progress-bar-wrap svelte-btia7y"><div class="progress-bar svelte-btia7y"${add_styles({width:`${K*100}%`})}${add_attribute("this",H,0)}></div></div></div>`:`${d==="full"?`${validate_component(at$2,"Loader").$$render(r,{margin:f==="default"},{},{})}`:""}`} ${v?"":`<p class="loading svelte-btia7y">${escape(M)}</p> ${p["additional-loading-text"]?p["additional-loading-text"]({}):""}`}`:`${n==="error"?`<div class="clear-status svelte-btia7y">${validate_component(O$1,"IconButton").$$render(r,{Icon:Ut,label:c("common.clear"),disabled:!1},{},{})}</div> <span class="error svelte-btia7y">${escape(c("common.error"))}</span> ${p.error?p.error({}):""}`:""}`} </div>`});function it(r){return da(r)}const ct$1={code:".toast-body.svelte-fee5uc{display:flex;position:relative;right:0;left:0;align-items:center;margin:var(--size-6) var(--size-4);margin:auto;border-radius:var(--container-radius);overflow:hidden;pointer-events:auto}.toast-body.error.svelte-fee5uc{border:1px solid var(--color-red-700);background:var(--color-red-50)}.dark .toast-body.error.svelte-fee5uc{border:1px solid var(--color-red-500);background-color:var(--color-grey-950)}.toast-body.warning.svelte-fee5uc{border:1px solid var(--color-yellow-700);background:var(--color-yellow-50)}.dark .toast-body.warning.svelte-fee5uc{border:1px solid var(--color-yellow-500);background-color:var(--color-grey-950)}.toast-body.info.svelte-fee5uc{border:1px solid var(--color-grey-700);background:var(--color-grey-50)}.dark .toast-body.info.svelte-fee5uc{border:1px solid var(--color-grey-500);background-color:var(--color-grey-950)}.toast-body.success.svelte-fee5uc{border:1px solid var(--color-green-700);background:var(--color-green-50)}.dark .toast-body.success.svelte-fee5uc{border:1px solid var(--color-green-500);background-color:var(--color-grey-950)}.toast-title.svelte-fee5uc{display:flex;align-items:center;font-weight:var(--weight-bold);font-size:var(--text-lg);line-height:var(--line-sm)}.toast-title.error.svelte-fee5uc{color:var(--color-red-700)}.dark .toast-title.error.svelte-fee5uc{color:var(--color-red-50)}.toast-title.warning.svelte-fee5uc{color:var(--color-yellow-700)}.dark .toast-title.warning.svelte-fee5uc{color:var(--color-yellow-50)}.toast-title.info.svelte-fee5uc{color:var(--color-grey-700)}.dark .toast-title.info.svelte-fee5uc{color:var(--color-grey-50)}.toast-title.success.svelte-fee5uc{color:var(--color-green-700)}.dark .toast-title.success.svelte-fee5uc{color:var(--color-green-50)}.toast-close.svelte-fee5uc{margin:0 var(--size-3);border-radius:var(--size-3);padding:0px var(--size-1-5);font-size:var(--size-5);line-height:var(--size-5)}.toast-close.error.svelte-fee5uc{color:var(--color-red-700)}.dark .toast-close.error.svelte-fee5uc{color:var(--color-red-500)}.toast-close.warning.svelte-fee5uc{color:var(--color-yellow-700)}.dark .toast-close.warning.svelte-fee5uc{color:var(--color-yellow-500)}.toast-close.info.svelte-fee5uc{color:var(--color-grey-700)}.dark .toast-close.info.svelte-fee5uc{color:var(--color-grey-500)}.toast-close.success.svelte-fee5uc{color:var(--color-green-700)}.dark .toast-close.success.svelte-fee5uc{color:var(--color-green-500)}.toast-text.svelte-fee5uc{font-size:var(--text-lg);word-wrap:break-word;overflow-wrap:break-word;word-break:break-word}.toast-text.error.svelte-fee5uc{color:var(--color-red-700)}.dark .toast-text.error.svelte-fee5uc{color:var(--color-red-50)}.toast-text.warning.svelte-fee5uc{color:var(--color-yellow-700)}.dark .toast-text.warning.svelte-fee5uc{color:var(--color-yellow-50)}.toast-text.info.svelte-fee5uc{color:var(--color-grey-700)}.dark .toast-text.info.svelte-fee5uc{color:var(--color-grey-50)}.toast-text.success.svelte-fee5uc{color:var(--color-green-700)}.dark .toast-text.success.svelte-fee5uc{color:var(--color-green-50)}.toast-details.svelte-fee5uc{margin:var(--size-3) var(--size-3) var(--size-3) 0;width:100%}.toast-icon.svelte-fee5uc{display:flex;position:absolute;position:relative;flex-shrink:0;justify-content:center;align-items:center;margin:var(--size-2);border-radius:var(--radius-full);padding:var(--size-1);padding-left:calc(var(--size-1) - 1px);width:35px;height:35px}.toast-icon.error.svelte-fee5uc{color:var(--color-red-700)}.dark .toast-icon.error.svelte-fee5uc{color:var(--color-red-500)}.toast-icon.warning.svelte-fee5uc{color:var(--color-yellow-700)}.dark .toast-icon.warning.svelte-fee5uc{color:var(--color-yellow-500)}.toast-icon.info.svelte-fee5uc{color:var(--color-grey-700)}.dark .toast-icon.info.svelte-fee5uc{color:var(--color-grey-500)}.toast-icon.success.svelte-fee5uc{color:var(--color-green-700)}.dark .toast-icon.success.svelte-fee5uc{color:var(--color-green-500)}@keyframes svelte-fee5uc-countdown{from{transform:scaleX(1)}to{transform:scaleX(0)}}.timer.svelte-fee5uc{position:absolute;bottom:0;left:0;transform-origin:0 0;animation:svelte-fee5uc-countdown 10s linear forwards;width:100%;height:var(--size-1)}.timer.error.svelte-fee5uc{background:var(--color-red-700)}.dark .timer.error.svelte-fee5uc{background:var(--color-red-500)}.timer.warning.svelte-fee5uc{background:var(--color-yellow-700)}.dark .timer.warning.svelte-fee5uc{background:var(--color-yellow-500)}.timer.info.svelte-fee5uc{background:var(--color-grey-700)}.dark .timer.info.svelte-fee5uc{background:var(--color-grey-500)}.timer.success.svelte-fee5uc{background:var(--color-green-700)}.dark .timer.success.svelte-fee5uc{background:var(--color-green-500)}.hidden.svelte-fee5uc{display:none}.toast-text.svelte-fee5uc a{text-decoration:underline}",map:'{"version":3,"file":"ToastContent.svelte","sources":["ToastContent.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { Error, Info, Warning, Success } from \\"@gradio/icons\\";\\nimport { sanitize } from \\"@gradio/sanitize\\";\\nimport { createEventDispatcher, onMount } from \\"svelte\\";\\nimport { fade } from \\"svelte/transition\\";\\nexport let title = \\"\\";\\nexport let message = \\"\\";\\nexport let type;\\nexport let id;\\nexport let duration = 10;\\nexport let visible = true;\\n$: message = sanitize(message);\\n$: display = visible;\\n$: duration = duration || null;\\nconst dispatch = createEventDispatcher();\\nfunction close_message() {\\n    dispatch(\\"close\\", id);\\n}\\nonMount(() => {\\n    if (duration !== null) {\\n        setTimeout(() => {\\n            close_message();\\n        }, duration * 1e3);\\n    }\\n});\\n$: timer_animation_duration = `${duration || 0}s`;\\n<\/script>\\n\\n<!-- TODO: fix-->\\n<!-- svelte-ignore a11y-no-noninteractive-element-interactions-->\\n<div\\n\\tclass=\\"toast-body {type}\\"\\n\\trole=\\"alert\\"\\n\\tdata-testid=\\"toast-body\\"\\n\\tclass:hidden={!display}\\n\\ton:click|stopPropagation\\n\\ton:keydown|stopPropagation\\n\\tin:fade={{ duration: 200, delay: 100 }}\\n\\tout:fade={{ duration: 200 }}\\n>\\n\\t<div class=\\"toast-icon {type}\\">\\n\\t\\t{#if type === \\"warning\\"}\\n\\t\\t\\t<Warning />\\n\\t\\t{:else if type === \\"info\\"}\\n\\t\\t\\t<Info />\\n\\t\\t{:else if type === \\"success\\"}\\n\\t\\t\\t<Success />\\n\\t\\t{:else if type === \\"error\\"}\\n\\t\\t\\t<Error />\\n\\t\\t{/if}\\n\\t</div>\\n\\n\\t<div class=\\"toast-details {type}\\">\\n\\t\\t<div class=\\"toast-title {type}\\">{title}</div>\\n\\t\\t<div class=\\"toast-text {type}\\">\\n\\t\\t\\t{@html message}\\n\\t\\t</div>\\n\\t</div>\\n\\n\\t<button\\n\\t\\ton:click={close_message}\\n\\t\\tclass=\\"toast-close {type}\\"\\n\\t\\ttype=\\"button\\"\\n\\t\\taria-label=\\"Close\\"\\n\\t\\tdata-testid=\\"toast-close\\"\\n\\t>\\n\\t\\t<span aria-hidden=\\"true\\">&#215;</span>\\n\\t</button>\\n\\n\\t<div\\n\\t\\tclass=\\"timer {type}\\"\\n\\t\\tstyle={`animation-duration: ${timer_animation_duration};`}\\n\\t/>\\n</div>\\n\\n<style>\\n\\t.toast-body {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: relative;\\n\\t\\tright: 0;\\n\\t\\tleft: 0;\\n\\t\\talign-items: center;\\n\\t\\tmargin: var(--size-6) var(--size-4);\\n\\t\\tmargin: auto;\\n\\t\\tborder-radius: var(--container-radius);\\n\\t\\toverflow: hidden;\\n\\t\\tpointer-events: auto;\\n\\t}\\n\\n\\t.toast-body.error {\\n\\t\\tborder: 1px solid var(--color-red-700);\\n\\t\\tbackground: var(--color-red-50);\\n\\t}\\n\\n\\t:global(.dark) .toast-body.error {\\n\\t\\tborder: 1px solid var(--color-red-500);\\n\\t\\tbackground-color: var(--color-grey-950);\\n\\t}\\n\\n\\t.toast-body.warning {\\n\\t\\tborder: 1px solid var(--color-yellow-700);\\n\\t\\tbackground: var(--color-yellow-50);\\n\\t}\\n\\t:global(.dark) .toast-body.warning {\\n\\t\\tborder: 1px solid var(--color-yellow-500);\\n\\t\\tbackground-color: var(--color-grey-950);\\n\\t}\\n\\n\\t.toast-body.info {\\n\\t\\tborder: 1px solid var(--color-grey-700);\\n\\t\\tbackground: var(--color-grey-50);\\n\\t}\\n\\t:global(.dark) .toast-body.info {\\n\\t\\tborder: 1px solid var(--color-grey-500);\\n\\t\\tbackground-color: var(--color-grey-950);\\n\\t}\\n\\n\\t.toast-body.success {\\n\\t\\tborder: 1px solid var(--color-green-700);\\n\\t\\tbackground: var(--color-green-50);\\n\\t}\\n\\t:global(.dark) .toast-body.success {\\n\\t\\tborder: 1px solid var(--color-green-500);\\n\\t\\tbackground-color: var(--color-grey-950);\\n\\t}\\n\\n\\t.toast-title {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tfont-weight: var(--weight-bold);\\n\\t\\tfont-size: var(--text-lg);\\n\\t\\tline-height: var(--line-sm);\\n\\t}\\n\\n\\t.toast-title.error {\\n\\t\\tcolor: var(--color-red-700);\\n\\t}\\n\\t:global(.dark) .toast-title.error {\\n\\t\\tcolor: var(--color-red-50);\\n\\t}\\n\\n\\t.toast-title.warning {\\n\\t\\tcolor: var(--color-yellow-700);\\n\\t}\\n\\t:global(.dark) .toast-title.warning {\\n\\t\\tcolor: var(--color-yellow-50);\\n\\t}\\n\\n\\t.toast-title.info {\\n\\t\\tcolor: var(--color-grey-700);\\n\\t}\\n\\t:global(.dark) .toast-title.info {\\n\\t\\tcolor: var(--color-grey-50);\\n\\t}\\n\\n\\t.toast-title.success {\\n\\t\\tcolor: var(--color-green-700);\\n\\t}\\n\\t:global(.dark) .toast-title.success {\\n\\t\\tcolor: var(--color-green-50);\\n\\t}\\n\\n\\t.toast-close {\\n\\t\\tmargin: 0 var(--size-3);\\n\\t\\tborder-radius: var(--size-3);\\n\\t\\tpadding: 0px var(--size-1-5);\\n\\t\\tfont-size: var(--size-5);\\n\\t\\tline-height: var(--size-5);\\n\\t}\\n\\n\\t.toast-close.error {\\n\\t\\tcolor: var(--color-red-700);\\n\\t}\\n\\t:global(.dark) .toast-close.error {\\n\\t\\tcolor: var(--color-red-500);\\n\\t}\\n\\n\\t.toast-close.warning {\\n\\t\\tcolor: var(--color-yellow-700);\\n\\t}\\n\\t:global(.dark) .toast-close.warning {\\n\\t\\tcolor: var(--color-yellow-500);\\n\\t}\\n\\n\\t.toast-close.info {\\n\\t\\tcolor: var(--color-grey-700);\\n\\t}\\n\\t:global(.dark) .toast-close.info {\\n\\t\\tcolor: var(--color-grey-500);\\n\\t}\\n\\n\\t.toast-close.success {\\n\\t\\tcolor: var(--color-green-700);\\n\\t}\\n\\t:global(.dark) .toast-close.success {\\n\\t\\tcolor: var(--color-green-500);\\n\\t}\\n\\n\\t.toast-text {\\n\\t\\tfont-size: var(--text-lg);\\n\\t\\tword-wrap: break-word;\\n\\t\\toverflow-wrap: break-word;\\n\\t\\tword-break: break-word;\\n\\t}\\n\\n\\t.toast-text.error {\\n\\t\\tcolor: var(--color-red-700);\\n\\t}\\n\\t:global(.dark) .toast-text.error {\\n\\t\\tcolor: var(--color-red-50);\\n\\t}\\n\\n\\t.toast-text.warning {\\n\\t\\tcolor: var(--color-yellow-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-text.warning {\\n\\t\\tcolor: var(--color-yellow-50);\\n\\t}\\n\\n\\t.toast-text.info {\\n\\t\\tcolor: var(--color-grey-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-text.info {\\n\\t\\tcolor: var(--color-grey-50);\\n\\t}\\n\\n\\t.toast-text.success {\\n\\t\\tcolor: var(--color-green-700);\\n\\t}\\n\\t:global(.dark) .toast-text.success {\\n\\t\\tcolor: var(--color-green-50);\\n\\t}\\n\\n\\t.toast-details {\\n\\t\\tmargin: var(--size-3) var(--size-3) var(--size-3) 0;\\n\\t\\twidth: 100%;\\n\\t}\\n\\n\\t.toast-icon {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: absolute;\\n\\t\\tposition: relative;\\n\\t\\tflex-shrink: 0;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tmargin: var(--size-2);\\n\\t\\tborder-radius: var(--radius-full);\\n\\t\\tpadding: var(--size-1);\\n\\t\\tpadding-left: calc(var(--size-1) - 1px);\\n\\t\\twidth: 35px;\\n\\t\\theight: 35px;\\n\\t}\\n\\n\\t.toast-icon.error {\\n\\t\\tcolor: var(--color-red-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-icon.error {\\n\\t\\tcolor: var(--color-red-500);\\n\\t}\\n\\n\\t.toast-icon.warning {\\n\\t\\tcolor: var(--color-yellow-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-icon.warning {\\n\\t\\tcolor: var(--color-yellow-500);\\n\\t}\\n\\n\\t.toast-icon.info {\\n\\t\\tcolor: var(--color-grey-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-icon.info {\\n\\t\\tcolor: var(--color-grey-500);\\n\\t}\\n\\n\\t.toast-icon.success {\\n\\t\\tcolor: var(--color-green-700);\\n\\t}\\n\\n\\t:global(.dark) .toast-icon.success {\\n\\t\\tcolor: var(--color-green-500);\\n\\t}\\n\\n\\t@keyframes countdown {\\n\\t\\tfrom {\\n\\t\\t\\ttransform: scaleX(1);\\n\\t\\t}\\n\\t\\tto {\\n\\t\\t\\ttransform: scaleX(0);\\n\\t\\t}\\n\\t}\\n\\n\\t.timer {\\n\\t\\tposition: absolute;\\n\\t\\tbottom: 0;\\n\\t\\tleft: 0;\\n\\t\\ttransform-origin: 0 0;\\n\\t\\tanimation: countdown 10s linear forwards;\\n\\t\\twidth: 100%;\\n\\t\\theight: var(--size-1);\\n\\t}\\n\\n\\t.timer.error {\\n\\t\\tbackground: var(--color-red-700);\\n\\t}\\n\\n\\t:global(.dark) .timer.error {\\n\\t\\tbackground: var(--color-red-500);\\n\\t}\\n\\n\\t.timer.warning {\\n\\t\\tbackground: var(--color-yellow-700);\\n\\t}\\n\\n\\t:global(.dark) .timer.warning {\\n\\t\\tbackground: var(--color-yellow-500);\\n\\t}\\n\\n\\t.timer.info {\\n\\t\\tbackground: var(--color-grey-700);\\n\\t}\\n\\n\\t:global(.dark) .timer.info {\\n\\t\\tbackground: var(--color-grey-500);\\n\\t}\\n\\n\\t.timer.success {\\n\\t\\tbackground: var(--color-green-700);\\n\\t}\\n\\n\\t:global(.dark) .timer.success {\\n\\t\\tbackground: var(--color-green-500);\\n\\t}\\n\\n\\t.hidden {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\t.toast-text :global(a) {\\n\\t\\ttext-decoration: underline;\\n\\t}</style>\\n"],"names":[],"mappings":"AA2EC,yBAAY,CACX,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,KAAK,CAAE,CAAC,CACR,IAAI,CAAE,CAAC,CACP,WAAW,CAAE,MAAM,CACnB,MAAM,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CACnC,MAAM,CAAE,IAAI,CACZ,aAAa,CAAE,IAAI,kBAAkB,CAAC,CACtC,QAAQ,CAAE,MAAM,CAChB,cAAc,CAAE,IACjB,CAEA,WAAW,oBAAO,CACjB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,eAAe,CAAC,CACtC,UAAU,CAAE,IAAI,cAAc,CAC/B,CAEQ,KAAM,CAAC,WAAW,oBAAO,CAChC,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,eAAe,CAAC,CACtC,gBAAgB,CAAE,IAAI,gBAAgB,CACvC,CAEA,WAAW,sBAAS,CACnB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,kBAAkB,CAAC,CACzC,UAAU,CAAE,IAAI,iBAAiB,CAClC,CACQ,KAAM,CAAC,WAAW,sBAAS,CAClC,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,kBAAkB,CAAC,CACzC,gBAAgB,CAAE,IAAI,gBAAgB,CACvC,CAEA,WAAW,mBAAM,CAChB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,gBAAgB,CAAC,CACvC,UAAU,CAAE,IAAI,eAAe,CAChC,CACQ,KAAM,CAAC,WAAW,mBAAM,CAC/B,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,gBAAgB,CAAC,CACvC,gBAAgB,CAAE,IAAI,gBAAgB,CACvC,CAEA,WAAW,sBAAS,CACnB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,iBAAiB,CAAC,CACxC,UAAU,CAAE,IAAI,gBAAgB,CACjC,CACQ,KAAM,CAAC,WAAW,sBAAS,CAClC,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAI,iBAAiB,CAAC,CACxC,gBAAgB,CAAE,IAAI,gBAAgB,CACvC,CAEA,0BAAa,CACZ,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MAAM,CACnB,WAAW,CAAE,IAAI,aAAa,CAAC,CAC/B,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,WAAW,CAAE,IAAI,SAAS,CAC3B,CAEA,YAAY,oBAAO,CAClB,KAAK,CAAE,IAAI,eAAe,CAC3B,CACQ,KAAM,CAAC,YAAY,oBAAO,CACjC,KAAK,CAAE,IAAI,cAAc,CAC1B,CAEA,YAAY,sBAAS,CACpB,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CACQ,KAAM,CAAC,YAAY,sBAAS,CACnC,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,YAAY,mBAAM,CACjB,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CACQ,KAAM,CAAC,YAAY,mBAAM,CAChC,KAAK,CAAE,IAAI,eAAe,CAC3B,CAEA,YAAY,sBAAS,CACpB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CACQ,KAAM,CAAC,YAAY,sBAAS,CACnC,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEA,0BAAa,CACZ,MAAM,CAAE,CAAC,CAAC,IAAI,QAAQ,CAAC,CACvB,aAAa,CAAE,IAAI,QAAQ,CAAC,CAC5B,OAAO,CAAE,GAAG,CAAC,IAAI,UAAU,CAAC,CAC5B,SAAS,CAAE,IAAI,QAAQ,CAAC,CACxB,WAAW,CAAE,IAAI,QAAQ,CAC1B,CAEA,YAAY,oBAAO,CAClB,KAAK,CAAE,IAAI,eAAe,CAC3B,CACQ,KAAM,CAAC,YAAY,oBAAO,CACjC,KAAK,CAAE,IAAI,eAAe,CAC3B,CAEA,YAAY,sBAAS,CACpB,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CACQ,KAAM,CAAC,YAAY,sBAAS,CACnC,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CAEA,YAAY,mBAAM,CACjB,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CACQ,KAAM,CAAC,YAAY,mBAAM,CAChC,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEA,YAAY,sBAAS,CACpB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CACQ,KAAM,CAAC,YAAY,sBAAS,CACnC,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,yBAAY,CACX,SAAS,CAAE,IAAI,SAAS,CAAC,CACzB,SAAS,CAAE,UAAU,CACrB,aAAa,CAAE,UAAU,CACzB,UAAU,CAAE,UACb,CAEA,WAAW,oBAAO,CACjB,KAAK,CAAE,IAAI,eAAe,CAC3B,CACQ,KAAM,CAAC,WAAW,oBAAO,CAChC,KAAK,CAAE,IAAI,cAAc,CAC1B,CAEA,WAAW,sBAAS,CACnB,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CAEQ,KAAM,CAAC,WAAW,sBAAS,CAClC,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,WAAW,mBAAM,CAChB,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEQ,KAAM,CAAC,WAAW,mBAAM,CAC/B,KAAK,CAAE,IAAI,eAAe,CAC3B,CAEA,WAAW,sBAAS,CACnB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CACQ,KAAM,CAAC,WAAW,sBAAS,CAClC,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEA,4BAAe,CACd,MAAM,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CAAC,CAAC,CAAC,CACnD,KAAK,CAAE,IACR,CAEA,yBAAY,CACX,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,QAAQ,CAAE,QAAQ,CAClB,WAAW,CAAE,CAAC,CACd,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,MAAM,CAAE,IAAI,QAAQ,CAAC,CACrB,aAAa,CAAE,IAAI,aAAa,CAAC,CACjC,OAAO,CAAE,IAAI,QAAQ,CAAC,CACtB,YAAY,CAAE,KAAK,IAAI,QAAQ,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CACvC,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IACT,CAEA,WAAW,oBAAO,CACjB,KAAK,CAAE,IAAI,eAAe,CAC3B,CAEQ,KAAM,CAAC,WAAW,oBAAO,CAChC,KAAK,CAAE,IAAI,eAAe,CAC3B,CAEA,WAAW,sBAAS,CACnB,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CAEQ,KAAM,CAAC,WAAW,sBAAS,CAClC,KAAK,CAAE,IAAI,kBAAkB,CAC9B,CAEA,WAAW,mBAAM,CAChB,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEQ,KAAM,CAAC,WAAW,mBAAM,CAC/B,KAAK,CAAE,IAAI,gBAAgB,CAC5B,CAEA,WAAW,sBAAS,CACnB,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEQ,KAAM,CAAC,WAAW,sBAAS,CAClC,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,WAAW,uBAAU,CACpB,IAAK,CACJ,SAAS,CAAE,OAAO,CAAC,CACpB,CACA,EAAG,CACF,SAAS,CAAE,OAAO,CAAC,CACpB,CACD,CAEA,oBAAO,CACN,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,IAAI,CAAE,CAAC,CACP,gBAAgB,CAAE,CAAC,CAAC,CAAC,CACrB,SAAS,CAAE,uBAAS,CAAC,GAAG,CAAC,MAAM,CAAC,QAAQ,CACxC,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IAAI,QAAQ,CACrB,CAEA,MAAM,oBAAO,CACZ,UAAU,CAAE,IAAI,eAAe,CAChC,CAEQ,KAAM,CAAC,MAAM,oBAAO,CAC3B,UAAU,CAAE,IAAI,eAAe,CAChC,CAEA,MAAM,sBAAS,CACd,UAAU,CAAE,IAAI,kBAAkB,CACnC,CAEQ,KAAM,CAAC,MAAM,sBAAS,CAC7B,UAAU,CAAE,IAAI,kBAAkB,CACnC,CAEA,MAAM,mBAAM,CACX,UAAU,CAAE,IAAI,gBAAgB,CACjC,CAEQ,KAAM,CAAC,MAAM,mBAAM,CAC1B,UAAU,CAAE,IAAI,gBAAgB,CACjC,CAEA,MAAM,sBAAS,CACd,UAAU,CAAE,IAAI,iBAAiB,CAClC,CAEQ,KAAM,CAAC,MAAM,sBAAS,CAC7B,UAAU,CAAE,IAAI,iBAAiB,CAClC,CAEA,qBAAQ,CACP,OAAO,CAAE,IACV,CAEA,yBAAW,CAAS,CAAG,CACtB,eAAe,CAAE,SAClB"}'},dt=create_ssr_component((r,A,t,p)=>{let i,c,{title:o=""}=A,{message:C=""}=A,{type:a}=A,{id:n}=A,{duration:l=10}=A,{visible:v=!0}=A;createEventDispatcher();return A.title===void 0&&t.title&&o!==void 0&&t.title(o),A.message===void 0&&t.message&&C!==void 0&&t.message(C),A.type===void 0&&t.type&&a!==void 0&&t.type(a),A.id===void 0&&t.id&&n!==void 0&&t.id(n),A.duration===void 0&&t.duration&&l!==void 0&&t.duration(l),A.visible===void 0&&t.visible&&v!==void 0&&t.visible(v),r.css.add(ct$1),C=it(C),i=v,l=l||null,c=`${l||0}s`,`  <div class="${["toast-body "+escape(a,!0)+" svelte-fee5uc",i?"":"hidden"].join(" ").trim()}" role="alert" data-testid="toast-body"><div class="${"toast-icon "+escape(a,!0)+" svelte-fee5uc"}">${a==="warning"?`${validate_component(Me,"Warning").$$render(r,{},{},{})}`:`${a==="info"?`${validate_component(ee,"Info").$$render(r,{},{},{})}`:`${a==="success"?`${validate_component(oe,"Success").$$render(r,{},{},{})}`:`${a==="error"?`${validate_component(Nt,"Error").$$render(r,{},{},{})}`:""}`}`}`}</div> <div class="${"toast-details "+escape(a,!0)+" svelte-fee5uc"}"><div class="${"toast-title "+escape(a,!0)+" svelte-fee5uc"}">${escape(o)}</div> <div class="${"toast-text "+escape(a,!0)+" svelte-fee5uc"}"><!-- HTML_TAG_START -->${C}<!-- HTML_TAG_END --></div></div> <button class="${"toast-close "+escape(a,!0)+" svelte-fee5uc"}" type="button" aria-label="Close" data-testid="toast-close"><span aria-hidden="true" data-svelte-h="svelte-zpkfw7">×</span></button> <div class="${"timer "+escape(a,!0)+" svelte-fee5uc"}"${add_attribute("style",`animation-duration: ${c};`,0)}></div> </div>`}),vt={code:".toast-wrap.svelte-1jktj9z{--toast-top:var(--size-4);display:flex;position:fixed;top:calc(var(--toast-top) + var(--size-4));right:var(--size-4);flex-direction:column;align-items:end;gap:var(--size-2);z-index:var(--layer-top);width:calc(100% - var(--size-8))}@media(min-width: 640px){.toast-wrap.svelte-1jktj9z{width:calc(var(--size-96) + var(--size-10))}}",map:'{"version":3,"file":"Toast.svelte","sources":["Toast.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { flip } from \\"svelte/animate\\";\\nimport ToastContent from \\"./ToastContent.svelte\\";\\nimport { spring } from \\"svelte/motion\\";\\nexport let messages = [];\\nconst top = spring(0, { stiffness: 0.4, damping: 0.5 });\\n$: scroll_to_top(messages);\\nfunction scroll_to_top(_messages) {\\n    if (_messages.length > 0) {\\n        if (\\"parentIFrame\\" in window) {\\n            window.parentIFrame?.getPageInfo((page_info) => {\\n                if (page_info.scrollTop < page_info.offsetTop) {\\n                    top.set(0);\\n                }\\n                else {\\n                    top.set(page_info.scrollTop - page_info.offsetTop);\\n                }\\n            });\\n        }\\n    }\\n}\\n<\/script>\\n\\n<div class=\\"toast-wrap\\" style=\\"--toast-top: {$top}px;\\">\\n\\t{#each messages as { type, title, message, id, duration, visible } (id)}\\n\\t\\t<div animate:flip={{ duration: 300 }} style:width=\\"100%\\">\\n\\t\\t\\t<ToastContent\\n\\t\\t\\t\\t{type}\\n\\t\\t\\t\\t{title}\\n\\t\\t\\t\\t{message}\\n\\t\\t\\t\\t{duration}\\n\\t\\t\\t\\t{visible}\\n\\t\\t\\t\\ton:close\\n\\t\\t\\t\\t{id}\\n\\t\\t\\t/>\\n\\t\\t</div>\\n\\t{/each}\\n</div>\\n\\n<style>\\n\\t.toast-wrap {\\n\\t\\t--toast-top: var(--size-4);\\n\\t\\tdisplay: flex;\\n\\t\\tposition: fixed;\\n\\t\\ttop: calc(var(--toast-top) + var(--size-4));\\n\\t\\tright: var(--size-4);\\n\\n\\t\\tflex-direction: column;\\n\\t\\talign-items: end;\\n\\t\\tgap: var(--size-2);\\n\\t\\tz-index: var(--layer-top);\\n\\t\\twidth: calc(100% - var(--size-8));\\n\\t}\\n\\n\\t@media (min-width: 640px) {\\n\\t\\t.toast-wrap {\\n\\t\\t\\twidth: calc(var(--size-96) + var(--size-10));\\n\\t\\t}\\n\\t}</style>\\n"],"names":[],"mappings":"AAuCC,0BAAY,CACX,WAAW,CAAE,aAAa,CAC1B,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,KAAK,CACf,GAAG,CAAE,KAAK,IAAI,WAAW,CAAC,CAAC,CAAC,CAAC,IAAI,QAAQ,CAAC,CAAC,CAC3C,KAAK,CAAE,IAAI,QAAQ,CAAC,CAEpB,cAAc,CAAE,MAAM,CACtB,WAAW,CAAE,GAAG,CAChB,GAAG,CAAE,IAAI,QAAQ,CAAC,CAClB,OAAO,CAAE,IAAI,WAAW,CAAC,CACzB,KAAK,CAAE,KAAK,IAAI,CAAC,CAAC,CAAC,IAAI,QAAQ,CAAC,CACjC,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,0BAAY,CACX,KAAK,CAAE,KAAK,IAAI,SAAS,CAAC,CAAC,CAAC,CAAC,IAAI,SAAS,CAAC,CAC5C,CACD"}'},yt=create_ssr_component((r,A,t,p)=>{let i,c,{messages:o=[]}=A;const C=spring(0,{stiffness:.4,damping:.5});c=subscribe(C,n=>i=n);function a(n){n.length>0&&"parentIFrame"in window&&window.parentIFrame?.getPageInfo(l=>{l.scrollTop<l.offsetTop?C.set(0):C.set(l.scrollTop-l.offsetTop);});}return A.messages===void 0&&t.messages&&o!==void 0&&t.messages(o),r.css.add(vt),a(o),c(),`<div class="toast-wrap svelte-1jktj9z" style="${"--toast-top: "+escape(i,!0)+"px;"}">${each(o,({type:n,title:l,message:v,id:d,duration:m,visible:u})=>`<div${add_styles({width:"100%"})}>${validate_component(dt,"ToastContent").$$render(r,{type:n,title:l,message:v,duration:m,visible:u,id:d},{},{})} </div>`)} </div>`}),ut={code:".streaming-bar.svelte-roz8lq{position:absolute;bottom:0;left:0;right:0;height:4px;background-color:var(--primary-600);animation:svelte-roz8lq-countdown linear forwards;z-index:1}@keyframes svelte-roz8lq-countdown{from{transform:translateX(0%)}to{transform:translateX(-100%)}}",map:'{"version":3,"file":"StreamingBar.svelte","sources":["StreamingBar.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let time_limit;\\n<\/script>\\n\\n{#if time_limit}\\n\\t<div class=\\"streaming-bar\\" style:animation-duration=\\"{time_limit}s\\"></div>\\n{/if}\\n\\n<style>\\n\\t.streaming-bar {\\n\\t\\tposition: absolute;\\n\\t\\tbottom: 0;\\n\\t\\tleft: 0;\\n\\t\\tright: 0;\\n\\t\\theight: 4px;\\n\\t\\tbackground-color: var(--primary-600);\\n\\t\\tanimation: countdown linear forwards;\\n\\t\\tz-index: 1;\\n\\t}\\n\\n\\t@keyframes countdown {\\n\\t\\tfrom {\\n\\t\\t\\ttransform: translateX(0%);\\n\\t\\t}\\n\\t\\tto {\\n\\t\\t\\ttransform: translateX(-100%);\\n\\t\\t}\\n\\t}</style>\\n"],"names":[],"mappings":"AAQC,4BAAe,CACd,QAAQ,CAAE,QAAQ,CAClB,MAAM,CAAE,CAAC,CACT,IAAI,CAAE,CAAC,CACP,KAAK,CAAE,CAAC,CACR,MAAM,CAAE,GAAG,CACX,gBAAgB,CAAE,IAAI,aAAa,CAAC,CACpC,SAAS,CAAE,uBAAS,CAAC,MAAM,CAAC,QAAQ,CACpC,OAAO,CAAE,CACV,CAEA,WAAW,uBAAU,CACpB,IAAK,CACJ,SAAS,CAAE,WAAW,EAAE,CACzB,CACA,EAAG,CACF,SAAS,CAAE,WAAW,KAAK,CAC5B,CACD"}'},xt=create_ssr_component((r,A,t,p)=>{let{time_limit:i}=A;return A.time_limit===void 0&&t.time_limit&&i!==void 0&&t.time_limit(i),r.css.add(ut),`${i?`<div class="streaming-bar svelte-roz8lq"${add_styles({"animation-duration":`${i}s`})}></div>`:""}`});

let l$1 = class l extends Error{constructor(e){super(e),this.name="ShareError";}};async function _(t,e){if(window.__gradio_space__==null)throw new l$1("Must be on Spaces to share.");let o,n,i;{let r;if(typeof t=="object"&&t.url)r=t.url;else if(typeof t=="string")r=t;else throw new Error("Invalid data format for URL type");const c=await fetch(r);o=await c.blob(),n=c.headers.get("content-type")||"",i=c.headers.get("content-disposition")||"";}const s=new File([o],i,{type:n}),a=await fetch("https://huggingface.co/uploads",{method:"POST",body:s,headers:{"Content-Type":s.type,"X-Requested-With":"XMLHttpRequest"}});if(!a.ok){if(a.headers.get("content-type")?.includes("application/json")){const r=await a.json();throw new l$1(`Upload failed: ${r.error}`)}throw new l$1("Upload failed.")}return await a.text()}const w$1=t=>{const e=Math.floor(t/3600),o=Math.floor(t%3600/60),n=Math.round(t)%60,i=`${o<10?"0":""}${o}`,s=`${n<10?"0":""}${n}`;return e>0?`${e}:${i}:${s}`:`${o}:${s}`},u$1=typeof window<"u";let m$1 = class m{#e;theme;version;i18n;#t;root;autoscroll;max_file_size;client;_load_component;load_component=f.bind(this);constructor(e,o,n,i,s,a,h,r=d=>d,c,p){this.#e=e,this.theme=n,this.version=i,this.#t=o,this.max_file_size=h,this.i18n=r,this.root=s,this.autoscroll=a,this.client=c,this._load_component=p;}dispatch(e,o){if(!u$1||!this.#t)return;const n=new CustomEvent("gradio",{bubbles:!0,detail:{data:o,id:this.#e,event:e}});this.#t.dispatchEvent(n);}};function f(t,e="component"){return this._load_component({name:t,api_url:this.client.config?.root,variant:e})}const y$1=t=>typeof t=="number"?t+"px":t;

const l={code:"div.svelte-1vd8eap{display:flex;flex-direction:inherit;flex-wrap:wrap;gap:var(--form-gap-width);box-shadow:var(--block-shadow);border:var(--block-border-width) solid var(--block-border-color);border-radius:var(--block-radius);background:var(--border-color-primary);overflow-y:hidden}div.svelte-1vd8eap .block{box-shadow:none !important;border-width:0px !important;border-radius:0px !important}.hidden.svelte-1vd8eap{display:none}.hidden-css.svelte-1vd8eap{display:none !important}",map:'{"version":3,"file":"Index.svelte","sources":["Index.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let visible = true;\\nexport let scale = null;\\nexport let min_width = 0;\\n<\/script>\\n\\n<div\\n\\tclass=\\"form\\"\\n\\tclass:hidden={visible === false}\\n\\tclass:hidden-css={visible === \\"hidden\\"}\\n\\tstyle:flex-grow={scale}\\n\\tstyle:min-width={`calc(min(${min_width}px, 100%))`}\\n>\\n\\t<slot />\\n</div>\\n\\n<style>\\n\\tdiv {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: inherit;\\n\\t\\tflex-wrap: wrap;\\n\\t\\tgap: var(--form-gap-width);\\n\\t\\tbox-shadow: var(--block-shadow);\\n\\t\\tborder: var(--block-border-width) solid var(--block-border-color);\\n\\t\\tborder-radius: var(--block-radius);\\n\\t\\tbackground: var(--border-color-primary);\\n\\t\\toverflow-y: hidden;\\n\\t}\\n\\n\\tdiv :global(.block) {\\n\\t\\tbox-shadow: none !important;\\n\\t\\tborder-width: 0px !important;\\n\\t\\tborder-radius: 0px !important;\\n\\t}\\n\\n\\t.hidden {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\t.hidden-css {\\n\\t\\tdisplay: none !important;\\n\\t}</style>\\n"],"names":[],"mappings":"AAgBC,kBAAI,CACH,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,OAAO,CACvB,SAAS,CAAE,IAAI,CACf,GAAG,CAAE,IAAI,gBAAgB,CAAC,CAC1B,UAAU,CAAE,IAAI,cAAc,CAAC,CAC/B,MAAM,CAAE,IAAI,oBAAoB,CAAC,CAAC,KAAK,CAAC,IAAI,oBAAoB,CAAC,CACjE,aAAa,CAAE,IAAI,cAAc,CAAC,CAClC,UAAU,CAAE,IAAI,sBAAsB,CAAC,CACvC,UAAU,CAAE,MACb,CAEA,kBAAG,CAAS,MAAQ,CACnB,UAAU,CAAE,IAAI,CAAC,UAAU,CAC3B,YAAY,CAAE,GAAG,CAAC,UAAU,CAC5B,aAAa,CAAE,GAAG,CAAC,UACpB,CAEA,sBAAQ,CACP,OAAO,CAAE,IACV,CAEA,0BAAY,CACX,OAAO,CAAE,IAAI,CAAC,UACf"}'},s=create_ssr_component((o,A,t,n)=>{let{visible:e=!0}=A,{scale:d=null}=A,{min_width:i=0}=A;return A.visible===void 0&&t.visible&&e!==void 0&&t.visible(e),A.scale===void 0&&t.scale&&d!==void 0&&t.scale(d),A.min_width===void 0&&t.min_width&&i!==void 0&&t.min_width(i),o.css.add(l),`<div class="${["form svelte-1vd8eap",(e===!1?"hidden":"")+" "+(e==="hidden"?"hidden-css":"")].join(" ").trim()}"${add_styles({"flex-grow":d,"min-width":`calc(min(${i}px, 100%))`})}>${n.default?n.default({}):""} </div>`});

var Index19 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	default: s
});

const A={code:".gallery.svelte-1oitfqa{padding:var(--size-1) var(--size-2)}div.svelte-1oitfqa{overflow:hidden;white-space:nowrap}",map:'{"version":3,"file":"Example.svelte","sources":["Example.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { onMount } from \\"svelte\\";\\nexport let value;\\nexport let type;\\nexport let selected = false;\\nlet size;\\nlet el;\\nfunction set_styles(element, el_width) {\\n    element.style.setProperty(\\"--local-text-width\\", `${el_width && el_width < 150 ? el_width : 200}px`);\\n    element.style.whiteSpace = \\"unset\\";\\n}\\nfunction truncate_text(text, max_length = 60) {\\n    if (!text)\\n        return \\"\\";\\n    const str = String(text);\\n    if (str.length <= max_length)\\n        return str;\\n    return str.slice(0, max_length) + \\"...\\";\\n}\\nonMount(() => {\\n    set_styles(el, size);\\n});\\n<\/script>\\n\\n<div\\n\\tbind:clientWidth={size}\\n\\tbind:this={el}\\n\\tclass:table={type === \\"table\\"}\\n\\tclass:gallery={type === \\"gallery\\"}\\n\\tclass:selected\\n>\\n\\t{truncate_text(value)}\\n</div>\\n\\n<style>\\n\\t.gallery {\\n\\t\\tpadding: var(--size-1) var(--size-2);\\n\\t}\\n\\n\\tdiv {\\n\\t\\toverflow: hidden;\\n\\t\\twhite-space: nowrap;\\n\\t}</style>\\n"],"names":[],"mappings":"AAkCC,uBAAS,CACR,OAAO,CAAE,IAAI,QAAQ,CAAC,CAAC,IAAI,QAAQ,CACpC,CAEA,kBAAI,CACH,QAAQ,CAAE,MAAM,CAChB,WAAW,CAAE,MACd"}'};function u(l,e=60){if(!l)return "";const t=String(l);return t.length<=e?t:t.slice(0,e)+"..."}const h$1=create_ssr_component((l,e,t,p)=>{let{value:s}=e,{type:n}=e,{selected:i=!1}=e,a;return e.value===void 0&&t.value&&s!==void 0&&t.value(s),e.type===void 0&&t.type&&n!==void 0&&t.type(n),e.selected===void 0&&t.selected&&i!==void 0&&t.selected(i),l.css.add(A),`<div class="${["svelte-1oitfqa",(n==="table"?"table":"")+" "+(n==="gallery"?"gallery":"")+" "+(i?"selected":"")].join(" ").trim()}"${add_attribute("this",a,0)}>${escape(u(s))} </div>`});

var Example5 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	default: h$1
});

const N={code:`label.svelte-1ae7ssi.svelte-1ae7ssi{display:block;width:100%}input.svelte-1ae7ssi.svelte-1ae7ssi,textarea.svelte-1ae7ssi.svelte-1ae7ssi{flex-grow:1;outline:none !important;margin-top:0px;margin-bottom:0px;resize:none;z-index:1;display:block;position:relative;outline:none !important;background:var(--input-background-fill);padding:var(--input-padding);width:100%;color:var(--body-text-color);font-weight:var(--input-text-weight);font-size:var(--input-text-size);line-height:var(--line-sm);border:none}textarea.no-label.svelte-1ae7ssi.svelte-1ae7ssi{padding-top:5px;padding-bottom:5px}label.show_textbox_border.svelte-1ae7ssi input.svelte-1ae7ssi,label.show_textbox_border.svelte-1ae7ssi textarea.svelte-1ae7ssi{box-shadow:var(--input-shadow)}label.svelte-1ae7ssi.svelte-1ae7ssi:not(.container),label.svelte-1ae7ssi:not(.container) input.svelte-1ae7ssi,label.svelte-1ae7ssi:not(.container) textarea.svelte-1ae7ssi{height:100%}label.container.show_textbox_border.svelte-1ae7ssi input.svelte-1ae7ssi,label.container.show_textbox_border.svelte-1ae7ssi textarea.svelte-1ae7ssi{border:var(--input-border-width) solid var(--input-border-color);border-radius:var(--input-radius)}input.svelte-1ae7ssi.svelte-1ae7ssi:disabled,textarea.svelte-1ae7ssi.svelte-1ae7ssi:disabled{-webkit-opacity:1;opacity:1}label.container.show_textbox_border.svelte-1ae7ssi input.svelte-1ae7ssi:focus,label.container.show_textbox_border.svelte-1ae7ssi textarea.svelte-1ae7ssi:focus{box-shadow:var(--input-shadow-focus);border-color:var(--input-border-color-focus);background:var(--input-background-fill-focus)}input.svelte-1ae7ssi.svelte-1ae7ssi::placeholder,textarea.svelte-1ae7ssi.svelte-1ae7ssi::placeholder{color:var(--input-placeholder-color)}.input-container.svelte-1ae7ssi.svelte-1ae7ssi{display:flex;position:relative;align-items:flex-end}.submit-button.svelte-1ae7ssi.svelte-1ae7ssi,.stop-button.svelte-1ae7ssi.svelte-1ae7ssi{border:none;text-align:center;text-decoration:none;font-size:14px;cursor:pointer;border-radius:15px;min-width:30px;height:30px;flex-shrink:0;display:flex;justify-content:center;align-items:center;z-index:var(--layer-1)}.stop-button.svelte-1ae7ssi.svelte-1ae7ssi,.submit-button.svelte-1ae7ssi.svelte-1ae7ssi{background:var(--button-secondary-background-fill);color:var(--button-secondary-text-color)}.stop-button.svelte-1ae7ssi.svelte-1ae7ssi:hover,.submit-button.svelte-1ae7ssi.svelte-1ae7ssi:hover{background:var(--button-secondary-background-fill-hover)}.stop-button.svelte-1ae7ssi.svelte-1ae7ssi:disabled,.submit-button.svelte-1ae7ssi.svelte-1ae7ssi:disabled{background:var(--button-secondary-background-fill);cursor:pointer}.stop-button.svelte-1ae7ssi.svelte-1ae7ssi:active,.submit-button.svelte-1ae7ssi.svelte-1ae7ssi:active{box-shadow:var(--button-shadow-active)}.submit-button.svelte-1ae7ssi svg{height:22px;width:22px}.stop-button.svelte-1ae7ssi svg{height:16px;width:16px}.padded-button.svelte-1ae7ssi.svelte-1ae7ssi{padding:0 10px}div.validation-error.svelte-1ae7ssi.svelte-1ae7ssi{color:var(--error-icon-color);font-size:var(--font-sans);margin-top:var(--spacing-sm);font-weight:var(--weight-semibold)}label.container.svelte-1ae7ssi input.validation-error.svelte-1ae7ssi,label.container.svelte-1ae7ssi textarea.validation-error.svelte-1ae7ssi{border-color:transparent !important;box-shadow:0 0 3px 1px var(--error-icon-color),
			var(--shadow-inset) !important}`,map:'{"version":3,"file":"Textbox.svelte","sources":["Textbox.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { beforeUpdate, afterUpdate, createEventDispatcher, tick } from \\"svelte\\";\\nimport { BlockTitle, IconButton, IconButtonWrapper } from \\"@gradio/atoms\\";\\nimport { Copy, Check, Send, Square } from \\"@gradio/icons\\";\\nimport { fade } from \\"svelte/transition\\";\\nexport let value = \\"\\";\\nexport let value_is_output = false;\\nexport let lines = 1;\\nexport let placeholder = \\"Type here...\\";\\nexport let label;\\nexport let info = void 0;\\nexport let disabled = false;\\nexport let show_label = true;\\nexport let container = true;\\nexport let max_lines = void 0;\\nexport let type = \\"text\\";\\nexport let show_copy_button = false;\\nexport let submit_btn = null;\\nexport let stop_btn = null;\\nexport let rtl = false;\\nexport let autofocus = false;\\nexport let text_align = void 0;\\nexport let autoscroll = true;\\nexport let max_length = void 0;\\nexport let html_attributes = null;\\nexport let validation_error = void 0;\\nlet el;\\nlet copied = false;\\nlet timer;\\nlet can_scroll;\\nlet previous_scroll_top = 0;\\nlet user_has_scrolled_up = false;\\nlet _max_lines;\\nlet ghost_element = null;\\nconst show_textbox_border = !submit_btn;\\n$: if (max_lines === void 0 || max_lines === null) {\\n    if (type === \\"text\\") {\\n        _max_lines = Math.max(lines, 20);\\n    }\\n    else {\\n        _max_lines = 1;\\n    }\\n}\\nelse {\\n    _max_lines = Math.max(max_lines, lines);\\n}\\n$: value, validation_error, el && lines !== _max_lines && lines > 1 && resize({ target: el });\\n$: if (value === null)\\n    value = \\"\\";\\nconst dispatch = createEventDispatcher();\\nbeforeUpdate(() => {\\n    if (!user_has_scrolled_up && el && el.offsetHeight + el.scrollTop > el.scrollHeight - 100) {\\n        can_scroll = true;\\n    }\\n});\\nconst scroll = () => {\\n    if (can_scroll && autoscroll && !user_has_scrolled_up) {\\n        el.scrollTo(0, el.scrollHeight);\\n    }\\n};\\nfunction handle_change() {\\n    dispatch(\\"change\\", value);\\n    if (!value_is_output) {\\n        dispatch(\\"input\\");\\n    }\\n}\\nafterUpdate(() => {\\n    if (autofocus) {\\n        el.focus();\\n    }\\n    if (can_scroll && autoscroll) {\\n        scroll();\\n    }\\n    value_is_output = false;\\n});\\n$: value, handle_change();\\nasync function handle_copy() {\\n    if (\\"clipboard\\" in navigator) {\\n        await navigator.clipboard.writeText(value);\\n        dispatch(\\"copy\\", { value });\\n        copy_feedback();\\n    }\\n}\\nfunction copy_feedback() {\\n    copied = true;\\n    if (timer)\\n        clearTimeout(timer);\\n    timer = setTimeout(() => {\\n        copied = false;\\n    }, 1e3);\\n}\\nfunction handle_select(event) {\\n    const target = event.target;\\n    const text = target.value;\\n    const index = [\\n        target.selectionStart,\\n        target.selectionEnd\\n    ];\\n    dispatch(\\"select\\", { value: text.substring(...index), index });\\n}\\nasync function handle_keypress(e) {\\n    await tick();\\n    if (e.key === \\"Enter\\" && e.shiftKey && lines > 1) {\\n        e.preventDefault();\\n        dispatch(\\"submit\\");\\n    }\\n    else if (e.key === \\"Enter\\" && !e.shiftKey && lines === 1 && _max_lines >= 1) {\\n        e.preventDefault();\\n        dispatch(\\"submit\\");\\n    }\\n}\\nfunction handle_scroll(event) {\\n    const target = event.target;\\n    const current_scroll_top = target.scrollTop;\\n    if (current_scroll_top < previous_scroll_top) {\\n        user_has_scrolled_up = true;\\n    }\\n    previous_scroll_top = current_scroll_top;\\n    const max_scroll_top = target.scrollHeight - target.clientHeight;\\n    const user_has_scrolled_to_bottom = current_scroll_top >= max_scroll_top;\\n    if (user_has_scrolled_to_bottom) {\\n        user_has_scrolled_up = false;\\n    }\\n}\\nfunction handle_stop() {\\n    dispatch(\\"stop\\");\\n}\\nfunction handle_submit() {\\n    dispatch(\\"submit\\");\\n}\\nasync function resize(event) {\\n    await tick();\\n    if (lines === _max_lines)\\n        return;\\n    const target = event.target;\\n    const computed_styles = window.getComputedStyle(target);\\n    const padding_top = parseFloat(computed_styles.paddingTop);\\n    const padding_bottom = parseFloat(computed_styles.paddingBottom);\\n    const line_height = parseFloat(computed_styles.lineHeight);\\n    let max = _max_lines === void 0 ? false : padding_top + padding_bottom + line_height * _max_lines;\\n    let min = padding_top + padding_bottom + lines * line_height;\\n    target.style.height = \\"1px\\";\\n    let scroll_height;\\n    if (max && target.scrollHeight > max) {\\n        scroll_height = max;\\n    }\\n    else if (target.scrollHeight < min) {\\n        scroll_height = min;\\n    }\\n    else {\\n        scroll_height = target.scrollHeight;\\n    }\\n    target.style.height = `${scroll_height}px`;\\n    update_scrollbar_visibility(target);\\n}\\nfunction update_scrollbar_visibility(textarea) {\\n    const content_height = textarea.scrollHeight;\\n    const visible_height = textarea.clientHeight;\\n    const line_height = parseFloat(window.getComputedStyle(textarea).lineHeight);\\n    if (content_height > visible_height + line_height) {\\n        textarea.style.overflowY = \\"scroll\\";\\n    }\\n    else {\\n        textarea.style.overflowY = \\"hidden\\";\\n    }\\n}\\nfunction text_area_resize(_el, _value) {\\n    if (lines === _max_lines || lines === 1 && _max_lines === 1)\\n        return;\\n    _el.style.overflowY = \\"scroll\\";\\n    _el.addEventListener(\\"input\\", resize);\\n    if (!_value.trim())\\n        return;\\n    resize({ target: _el });\\n    return {\\n        destroy: () => _el.removeEventListener(\\"input\\", resize)\\n    };\\n}\\n<\/script>\\n\\n<!-- svelte-ignore a11y-autofocus -->\\n<label class:container class:show_textbox_border>\\n\\t{#if show_label && show_copy_button}\\n\\t\\t<IconButtonWrapper>\\n\\t\\t\\t<IconButton\\n\\t\\t\\t\\tIcon={copied ? Check : Copy}\\n\\t\\t\\t\\ton:click={handle_copy}\\n\\t\\t\\t\\tlabel={copied ? \\"Copied\\" : \\"Copy\\"}\\n\\t\\t\\t/>\\n\\t\\t</IconButtonWrapper>\\n\\t{/if}\\n\\t<BlockTitle show_label={validation_error ? true : show_label} {info}\\n\\t\\t>{label}\\n\\t\\t{#if validation_error}\\n\\t\\t\\t<div class=\\"validation-error\\">{validation_error}</div>\\n\\t\\t{/if}\\n\\t</BlockTitle>\\n\\n\\t<div class=\\"input-container\\">\\n\\t\\t{#if lines === 1 && _max_lines === 1}\\n\\t\\t\\t{#if type === \\"text\\"}\\n\\t\\t\\t\\t<input\\n\\t\\t\\t\\t\\tdata-testid=\\"textbox\\"\\n\\t\\t\\t\\t\\ttype=\\"text\\"\\n\\t\\t\\t\\t\\tclass=\\"scroll-hide\\"\\n\\t\\t\\t\\t\\tdir={rtl ? \\"rtl\\" : \\"ltr\\"}\\n\\t\\t\\t\\t\\tbind:value\\n\\t\\t\\t\\t\\tbind:this={el}\\n\\t\\t\\t\\t\\t{placeholder}\\n\\t\\t\\t\\t\\t{disabled}\\n\\t\\t\\t\\t\\t{autofocus}\\n\\t\\t\\t\\t\\tmaxlength={max_length}\\n\\t\\t\\t\\t\\ton:keypress={handle_keypress}\\n\\t\\t\\t\\t\\ton:blur\\n\\t\\t\\t\\t\\ton:select={handle_select}\\n\\t\\t\\t\\t\\ton:focus\\n\\t\\t\\t\\t\\tclass:validation-error={validation_error}\\n\\t\\t\\t\\t\\tstyle={text_align ? \\"text-align: \\" + text_align : \\"\\"}\\n\\t\\t\\t\\t\\tautocapitalize={html_attributes?.autocapitalize}\\n\\t\\t\\t\\t\\tautocorrect={html_attributes?.autocorrect}\\n\\t\\t\\t\\t\\tspellcheck={html_attributes?.spellcheck}\\n\\t\\t\\t\\t\\tautocomplete={html_attributes?.autocomplete}\\n\\t\\t\\t\\t\\ttabindex={html_attributes?.tabindex}\\n\\t\\t\\t\\t\\tenterkeyhint={html_attributes?.enterkeyhint}\\n\\t\\t\\t\\t\\tlang={html_attributes?.lang}\\n\\t\\t\\t\\t/>\\n\\t\\t\\t{:else if type === \\"password\\"}\\n\\t\\t\\t\\t<input\\n\\t\\t\\t\\t\\tdata-testid=\\"password\\"\\n\\t\\t\\t\\t\\ttype=\\"password\\"\\n\\t\\t\\t\\t\\tclass=\\"scroll-hide\\"\\n\\t\\t\\t\\t\\tbind:value\\n\\t\\t\\t\\t\\tbind:this={el}\\n\\t\\t\\t\\t\\t{placeholder}\\n\\t\\t\\t\\t\\t{disabled}\\n\\t\\t\\t\\t\\t{autofocus}\\n\\t\\t\\t\\t\\tmaxlength={max_length}\\n\\t\\t\\t\\t\\ton:keypress={handle_keypress}\\n\\t\\t\\t\\t\\ton:blur\\n\\t\\t\\t\\t\\ton:select={handle_select}\\n\\t\\t\\t\\t\\ton:focus\\n\\t\\t\\t\\t\\tclass:validation-error={validation_error}\\n\\t\\t\\t\\t\\tautocomplete=\\"\\"\\n\\t\\t\\t\\t\\tautocapitalize={html_attributes?.autocapitalize}\\n\\t\\t\\t\\t\\tautocorrect={html_attributes?.autocorrect}\\n\\t\\t\\t\\t\\tspellcheck={html_attributes?.spellcheck}\\n\\t\\t\\t\\t\\ttabindex={html_attributes?.tabindex}\\n\\t\\t\\t\\t\\tenterkeyhint={html_attributes?.enterkeyhint}\\n\\t\\t\\t\\t\\tlang={html_attributes?.lang}\\n\\t\\t\\t\\t/>\\n\\t\\t\\t{:else if type === \\"email\\"}\\n\\t\\t\\t\\t<input\\n\\t\\t\\t\\t\\tdata-testid=\\"textbox\\"\\n\\t\\t\\t\\t\\ttype=\\"email\\"\\n\\t\\t\\t\\t\\tclass=\\"scroll-hide\\"\\n\\t\\t\\t\\t\\tbind:value\\n\\t\\t\\t\\t\\tbind:this={el}\\n\\t\\t\\t\\t\\t{placeholder}\\n\\t\\t\\t\\t\\t{disabled}\\n\\t\\t\\t\\t\\t{autofocus}\\n\\t\\t\\t\\t\\tmaxlength={max_length}\\n\\t\\t\\t\\t\\ton:keypress={handle_keypress}\\n\\t\\t\\t\\t\\ton:blur\\n\\t\\t\\t\\t\\ton:select={handle_select}\\n\\t\\t\\t\\t\\ton:focus\\n\\t\\t\\t\\t\\tclass:validation-error={validation_error}\\n\\t\\t\\t\\t\\tautocomplete=\\"email\\"\\n\\t\\t\\t\\t\\tautocapitalize={html_attributes?.autocapitalize}\\n\\t\\t\\t\\t\\tautocorrect={html_attributes?.autocorrect}\\n\\t\\t\\t\\t\\tspellcheck={html_attributes?.spellcheck}\\n\\t\\t\\t\\t\\ttabindex={html_attributes?.tabindex}\\n\\t\\t\\t\\t\\tenterkeyhint={html_attributes?.enterkeyhint}\\n\\t\\t\\t\\t\\tlang={html_attributes?.lang}\\n\\t\\t\\t\\t/>\\n\\t\\t\\t{/if}\\n\\t\\t{:else}\\n\\t\\t\\t<textarea\\n\\t\\t\\t\\tdata-testid=\\"textbox\\"\\n\\t\\t\\t\\tuse:text_area_resize={value}\\n\\t\\t\\t\\tdir={rtl ? \\"rtl\\" : \\"ltr\\"}\\n\\t\\t\\t\\tclass:no-label={!show_label && (submit_btn || stop_btn)}\\n\\t\\t\\t\\tbind:value\\n\\t\\t\\t\\tbind:this={el}\\n\\t\\t\\t\\t{placeholder}\\n\\t\\t\\t\\trows={lines}\\n\\t\\t\\t\\t{disabled}\\n\\t\\t\\t\\t{autofocus}\\n\\t\\t\\t\\tmaxlength={max_length}\\n\\t\\t\\t\\ton:keypress={handle_keypress}\\n\\t\\t\\t\\ton:blur\\n\\t\\t\\t\\ton:select={handle_select}\\n\\t\\t\\t\\ton:focus\\n\\t\\t\\t\\ton:scroll={handle_scroll}\\n\\t\\t\\t\\tclass:validation-error={validation_error}\\n\\t\\t\\t\\tstyle={text_align ? \\"text-align: \\" + text_align : \\"\\"}\\n\\t\\t\\t\\tautocapitalize={html_attributes?.autocapitalize}\\n\\t\\t\\t\\tautocorrect={html_attributes?.autocorrect}\\n\\t\\t\\t\\tspellcheck={html_attributes?.spellcheck}\\n\\t\\t\\t\\tautocomplete={html_attributes?.autocomplete}\\n\\t\\t\\t\\ttabindex={html_attributes?.tabindex}\\n\\t\\t\\t\\tenterkeyhint={html_attributes?.enterkeyhint}\\n\\t\\t\\t\\tlang={html_attributes?.lang}\\n\\t\\t\\t/>\\n\\t\\t{/if}\\n\\t\\t{#if submit_btn}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"submit-button\\"\\n\\t\\t\\t\\tclass:padded-button={submit_btn !== true}\\n\\t\\t\\t\\ton:click={handle_submit}\\n\\t\\t\\t>\\n\\t\\t\\t\\t{#if submit_btn === true}\\n\\t\\t\\t\\t\\t<Send />\\n\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t{submit_btn}\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t</button>\\n\\t\\t{/if}\\n\\t\\t{#if stop_btn}\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass=\\"stop-button\\"\\n\\t\\t\\t\\tclass:padded-button={stop_btn !== true}\\n\\t\\t\\t\\ton:click={handle_stop}\\n\\t\\t\\t>\\n\\t\\t\\t\\t{#if stop_btn === true}\\n\\t\\t\\t\\t\\t<Square fill=\\"none\\" stroke_width={2.5} />\\n\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t{stop_btn}\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t</button>\\n\\t\\t{/if}\\n\\t</div>\\n</label>\\n\\n<style>\\n\\tlabel {\\n\\t\\tdisplay: block;\\n\\t\\twidth: 100%;\\n\\t}\\n\\n\\tinput,\\n\\ttextarea {\\n\\t\\tflex-grow: 1;\\n\\t\\toutline: none !important;\\n\\t\\tmargin-top: 0px;\\n\\t\\tmargin-bottom: 0px;\\n\\t\\tresize: none;\\n\\t\\tz-index: 1;\\n\\t\\tdisplay: block;\\n\\t\\tposition: relative;\\n\\t\\toutline: none !important;\\n\\t\\tbackground: var(--input-background-fill);\\n\\t\\tpadding: var(--input-padding);\\n\\t\\twidth: 100%;\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\tfont-weight: var(--input-text-weight);\\n\\t\\tfont-size: var(--input-text-size);\\n\\t\\tline-height: var(--line-sm);\\n\\t\\tborder: none;\\n\\t}\\n\\n\\ttextarea.no-label {\\n\\t\\tpadding-top: 5px;\\n\\t\\tpadding-bottom: 5px;\\n\\t}\\n\\tlabel.show_textbox_border input,\\n\\tlabel.show_textbox_border textarea {\\n\\t\\tbox-shadow: var(--input-shadow);\\n\\t}\\n\\tlabel:not(.container),\\n\\tlabel:not(.container) input,\\n\\tlabel:not(.container) textarea {\\n\\t\\theight: 100%;\\n\\t}\\n\\tlabel.container.show_textbox_border input,\\n\\tlabel.container.show_textbox_border textarea {\\n\\t\\tborder: var(--input-border-width) solid var(--input-border-color);\\n\\t\\tborder-radius: var(--input-radius);\\n\\t}\\n\\tinput:disabled,\\n\\ttextarea:disabled {\\n\\t\\t-webkit-opacity: 1;\\n\\t\\topacity: 1;\\n\\t}\\n\\n\\tlabel.container.show_textbox_border input:focus,\\n\\tlabel.container.show_textbox_border textarea:focus {\\n\\t\\tbox-shadow: var(--input-shadow-focus);\\n\\t\\tborder-color: var(--input-border-color-focus);\\n\\t\\tbackground: var(--input-background-fill-focus);\\n\\t}\\n\\n\\tinput::placeholder,\\n\\ttextarea::placeholder {\\n\\t\\tcolor: var(--input-placeholder-color);\\n\\t}\\n\\n\\t/* Same submit button style as MultimodalTextbox for the consistent UI */\\n\\t.input-container {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: relative;\\n\\t\\talign-items: flex-end;\\n\\t}\\n\\t.submit-button,\\n\\t.stop-button {\\n\\t\\tborder: none;\\n\\t\\ttext-align: center;\\n\\t\\ttext-decoration: none;\\n\\t\\tfont-size: 14px;\\n\\t\\tcursor: pointer;\\n\\t\\tborder-radius: 15px;\\n\\t\\tmin-width: 30px;\\n\\t\\theight: 30px;\\n\\t\\tflex-shrink: 0;\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tz-index: var(--layer-1);\\n\\t}\\n\\t.stop-button,\\n\\t.submit-button {\\n\\t\\tbackground: var(--button-secondary-background-fill);\\n\\t\\tcolor: var(--button-secondary-text-color);\\n\\t}\\n\\t.stop-button:hover,\\n\\t.submit-button:hover {\\n\\t\\tbackground: var(--button-secondary-background-fill-hover);\\n\\t}\\n\\t.stop-button:disabled,\\n\\t.submit-button:disabled {\\n\\t\\tbackground: var(--button-secondary-background-fill);\\n\\t\\tcursor: pointer;\\n\\t}\\n\\t.stop-button:active,\\n\\t.submit-button:active {\\n\\t\\tbox-shadow: var(--button-shadow-active);\\n\\t}\\n\\t.submit-button :global(svg) {\\n\\t\\theight: 22px;\\n\\t\\twidth: 22px;\\n\\t}\\n\\n\\t.stop-button :global(svg) {\\n\\t\\theight: 16px;\\n\\t\\twidth: 16px;\\n\\t}\\n\\t.padded-button {\\n\\t\\tpadding: 0 10px;\\n\\t}\\n\\n\\tdiv.validation-error {\\n\\t\\tcolor: var(--error-icon-color);\\n\\t\\tfont-size: var(--font-sans);\\n\\t\\tmargin-top: var(--spacing-sm);\\n\\t\\tfont-weight: var(--weight-semibold);\\n\\t}\\n\\n\\tlabel.container input.validation-error,\\n\\tlabel.container textarea.validation-error {\\n\\t\\tborder-color: transparent !important;\\n\\t\\tbox-shadow:\\n\\t\\t\\t0 0 3px 1px var(--error-icon-color),\\n\\t\\t\\tvar(--shadow-inset) !important;\\n\\t}</style>\\n"],"names":[],"mappings":"AA6UC,mCAAM,CACL,OAAO,CAAE,KAAK,CACd,KAAK,CAAE,IACR,CAEA,mCAAK,CACL,sCAAS,CACR,SAAS,CAAE,CAAC,CACZ,OAAO,CAAE,IAAI,CAAC,UAAU,CACxB,UAAU,CAAE,GAAG,CACf,aAAa,CAAE,GAAG,CAClB,MAAM,CAAE,IAAI,CACZ,OAAO,CAAE,CAAC,CACV,OAAO,CAAE,KAAK,CACd,QAAQ,CAAE,QAAQ,CAClB,OAAO,CAAE,IAAI,CAAC,UAAU,CACxB,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,OAAO,CAAE,IAAI,eAAe,CAAC,CAC7B,KAAK,CAAE,IAAI,CACX,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,WAAW,CAAE,IAAI,mBAAmB,CAAC,CACrC,SAAS,CAAE,IAAI,iBAAiB,CAAC,CACjC,WAAW,CAAE,IAAI,SAAS,CAAC,CAC3B,MAAM,CAAE,IACT,CAEA,QAAQ,uCAAU,CACjB,WAAW,CAAE,GAAG,CAChB,cAAc,CAAE,GACjB,CACA,KAAK,mCAAoB,CAAC,oBAAK,CAC/B,KAAK,mCAAoB,CAAC,uBAAS,CAClC,UAAU,CAAE,IAAI,cAAc,CAC/B,CACA,mCAAK,KAAK,UAAU,CAAC,CACrB,oBAAK,KAAK,UAAU,CAAC,CAAC,oBAAK,CAC3B,oBAAK,KAAK,UAAU,CAAC,CAAC,uBAAS,CAC9B,MAAM,CAAE,IACT,CACA,KAAK,UAAU,mCAAoB,CAAC,oBAAK,CACzC,KAAK,UAAU,mCAAoB,CAAC,uBAAS,CAC5C,MAAM,CAAE,IAAI,oBAAoB,CAAC,CAAC,KAAK,CAAC,IAAI,oBAAoB,CAAC,CACjE,aAAa,CAAE,IAAI,cAAc,CAClC,CACA,mCAAK,SAAS,CACd,sCAAQ,SAAU,CACjB,eAAe,CAAE,CAAC,CAClB,OAAO,CAAE,CACV,CAEA,KAAK,UAAU,mCAAoB,CAAC,oBAAK,MAAM,CAC/C,KAAK,UAAU,mCAAoB,CAAC,uBAAQ,MAAO,CAClD,UAAU,CAAE,IAAI,oBAAoB,CAAC,CACrC,YAAY,CAAE,IAAI,0BAA0B,CAAC,CAC7C,UAAU,CAAE,IAAI,6BAA6B,CAC9C,CAEA,mCAAK,aAAa,CAClB,sCAAQ,aAAc,CACrB,KAAK,CAAE,IAAI,yBAAyB,CACrC,CAGA,8CAAiB,CAChB,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,WAAW,CAAE,QACd,CACA,4CAAc,CACd,0CAAa,CACZ,MAAM,CAAE,IAAI,CACZ,UAAU,CAAE,MAAM,CAClB,eAAe,CAAE,IAAI,CACrB,SAAS,CAAE,IAAI,CACf,MAAM,CAAE,OAAO,CACf,aAAa,CAAE,IAAI,CACnB,SAAS,CAAE,IAAI,CACf,MAAM,CAAE,IAAI,CACZ,WAAW,CAAE,CAAC,CACd,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,OAAO,CAAE,IAAI,SAAS,CACvB,CACA,0CAAY,CACZ,4CAAe,CACd,UAAU,CAAE,IAAI,kCAAkC,CAAC,CACnD,KAAK,CAAE,IAAI,6BAA6B,CACzC,CACA,0CAAY,MAAM,CAClB,4CAAc,MAAO,CACpB,UAAU,CAAE,IAAI,wCAAwC,CACzD,CACA,0CAAY,SAAS,CACrB,4CAAc,SAAU,CACvB,UAAU,CAAE,IAAI,kCAAkC,CAAC,CACnD,MAAM,CAAE,OACT,CACA,0CAAY,OAAO,CACnB,4CAAc,OAAQ,CACrB,UAAU,CAAE,IAAI,sBAAsB,CACvC,CACA,6BAAc,CAAS,GAAK,CAC3B,MAAM,CAAE,IAAI,CACZ,KAAK,CAAE,IACR,CAEA,2BAAY,CAAS,GAAK,CACzB,MAAM,CAAE,IAAI,CACZ,KAAK,CAAE,IACR,CACA,4CAAe,CACd,OAAO,CAAE,CAAC,CAAC,IACZ,CAEA,GAAG,+CAAkB,CACpB,KAAK,CAAE,IAAI,kBAAkB,CAAC,CAC9B,SAAS,CAAE,IAAI,WAAW,CAAC,CAC3B,UAAU,CAAE,IAAI,YAAY,CAAC,CAC7B,WAAW,CAAE,IAAI,iBAAiB,CACnC,CAEA,KAAK,yBAAU,CAAC,KAAK,gCAAiB,CACtC,KAAK,yBAAU,CAAC,QAAQ,gCAAkB,CACzC,YAAY,CAAE,WAAW,CAAC,UAAU,CACpC,UAAU,CACT,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,GAAG,CAAC,IAAI,kBAAkB,CAAC;AACtC,GAAG,IAAI,cAAc,CAAC,CAAC,UACtB"}'},P=create_ssr_component((A,t,e,Q)=>{let{value:a=""}=t,{value_is_output:m=!1}=t,{lines:d=1}=t,{placeholder:C="Type here..."}=t,{label:g}=t,{info:B=void 0}=t,{disabled:r=!1}=t,{show_label:h=!0}=t,{container:w=!0}=t,{max_lines:b=void 0}=t,{type:v="text"}=t,{show_copy_button:k=!1}=t,{submit_btn:o=null}=t,{stop_btn:c=null}=t,{rtl:f=!1}=t,{autofocus:u=!1}=t,{text_align:_=void 0}=t,{autoscroll:I=!0}=t,{max_length:s=void 0}=t,{html_attributes:n=null}=t,{validation_error:i=void 0}=t,x,p;const K=!o,E=createEventDispatcher();function U(){E("change",a),m||E("input");}return t.value===void 0&&e.value&&a!==void 0&&e.value(a),t.value_is_output===void 0&&e.value_is_output&&m!==void 0&&e.value_is_output(m),t.lines===void 0&&e.lines&&d!==void 0&&e.lines(d),t.placeholder===void 0&&e.placeholder&&C!==void 0&&e.placeholder(C),t.label===void 0&&e.label&&g!==void 0&&e.label(g),t.info===void 0&&e.info&&B!==void 0&&e.info(B),t.disabled===void 0&&e.disabled&&r!==void 0&&e.disabled(r),t.show_label===void 0&&e.show_label&&h!==void 0&&e.show_label(h),t.container===void 0&&e.container&&w!==void 0&&e.container(w),t.max_lines===void 0&&e.max_lines&&b!==void 0&&e.max_lines(b),t.type===void 0&&e.type&&v!==void 0&&e.type(v),t.show_copy_button===void 0&&e.show_copy_button&&k!==void 0&&e.show_copy_button(k),t.submit_btn===void 0&&e.submit_btn&&o!==void 0&&e.submit_btn(o),t.stop_btn===void 0&&e.stop_btn&&c!==void 0&&e.stop_btn(c),t.rtl===void 0&&e.rtl&&f!==void 0&&e.rtl(f),t.autofocus===void 0&&e.autofocus&&u!==void 0&&e.autofocus(u),t.text_align===void 0&&e.text_align&&_!==void 0&&e.text_align(_),t.autoscroll===void 0&&e.autoscroll&&I!==void 0&&e.autoscroll(I),t.max_length===void 0&&e.max_length&&s!==void 0&&e.max_length(s),t.html_attributes===void 0&&e.html_attributes&&n!==void 0&&e.html_attributes(n),t.validation_error===void 0&&e.validation_error&&i!==void 0&&e.validation_error(i),A.css.add(N),b==null?v==="text"?p=Math.max(d,20):p=1:p=Math.max(b,d),a===null&&(a=""),U(),` <label class="${["svelte-1ae7ssi",(w?"container":"")+" "+(K?"show_textbox_border":"")].join(" ").trim()}">${h&&k?`${validate_component(Ue,"IconButtonWrapper").$$render(A,{},{},{default:()=>`${validate_component(O$1,"IconButton").$$render(A,{Icon:Yt,label:"Copy"},{},{})}`})}`:""} ${validate_component(yt$1,"BlockTitle").$$render(A,{show_label:i?!0:h,info:B},{},{default:()=>`${escape(g)} ${i?`<div class="validation-error svelte-1ae7ssi">${escape(i)}</div>`:""}`})} <div class="input-container svelte-1ae7ssi">${d===1&&p===1?`${v==="text"?`<input data-testid="textbox" type="text" class="${["scroll-hide svelte-1ae7ssi",i?"validation-error":""].join(" ").trim()}"${add_attribute("dir",f?"rtl":"ltr",0)}${add_attribute("placeholder",C,0)} ${r?"disabled":""} ${u?"autofocus":""}${add_attribute("maxlength",s,0)}${add_attribute("style",_?"text-align: "+_:"",0)}${add_attribute("autocapitalize",n?.autocapitalize,0)}${add_attribute("autocorrect",n?.autocorrect,0)}${add_attribute("spellcheck",n?.spellcheck,0)}${add_attribute("autocomplete",n?.autocomplete,0)}${add_attribute("tabindex",n?.tabindex,0)}${add_attribute("enterkeyhint",n?.enterkeyhint,0)}${add_attribute("lang",n?.lang,0)}${add_attribute("value",a,0)}${add_attribute("this",x,0)}>`:`${v==="password"?`<input data-testid="password" type="password" class="${["scroll-hide svelte-1ae7ssi",i?"validation-error":""].join(" ").trim()}"${add_attribute("placeholder",C,0)} ${r?"disabled":""} ${u?"autofocus":""}${add_attribute("maxlength",s,0)} autocomplete=""${add_attribute("autocapitalize",n?.autocapitalize,0)}${add_attribute("autocorrect",n?.autocorrect,0)}${add_attribute("spellcheck",n?.spellcheck,0)}${add_attribute("tabindex",n?.tabindex,0)}${add_attribute("enterkeyhint",n?.enterkeyhint,0)}${add_attribute("lang",n?.lang,0)}${add_attribute("value",a,0)}${add_attribute("this",x,0)}>`:`${v==="email"?`<input data-testid="textbox" type="email" class="${["scroll-hide svelte-1ae7ssi",i?"validation-error":""].join(" ").trim()}"${add_attribute("placeholder",C,0)} ${r?"disabled":""} ${u?"autofocus":""}${add_attribute("maxlength",s,0)} autocomplete="email"${add_attribute("autocapitalize",n?.autocapitalize,0)}${add_attribute("autocorrect",n?.autocorrect,0)}${add_attribute("spellcheck",n?.spellcheck,0)}${add_attribute("tabindex",n?.tabindex,0)}${add_attribute("enterkeyhint",n?.enterkeyhint,0)}${add_attribute("lang",n?.lang,0)}${add_attribute("value",a,0)}${add_attribute("this",x,0)}>`:""}`}`}`:`<textarea data-testid="textbox"${add_attribute("dir",f?"rtl":"ltr",0)}${add_attribute("placeholder",C,0)}${add_attribute("rows",d,0)} ${r?"disabled":""} ${u?"autofocus":""}${add_attribute("maxlength",s,0)}${add_attribute("style",_?"text-align: "+_:"",0)}${add_attribute("autocapitalize",n?.autocapitalize,0)}${add_attribute("autocorrect",n?.autocorrect,0)}${add_attribute("spellcheck",n?.spellcheck,0)}${add_attribute("autocomplete",n?.autocomplete,0)}${add_attribute("tabindex",n?.tabindex,0)}${add_attribute("enterkeyhint",n?.enterkeyhint,0)}${add_attribute("lang",n?.lang,0)} class="${["svelte-1ae7ssi",(!h&&(o||c)?"no-label":"")+" "+(i?"validation-error":"")].join(" ").trim()}"${add_attribute("this",x,0)}>${escape(a||"")}</textarea>`} ${o?`<button class="${["submit-button svelte-1ae7ssi",o!==!0?"padded-button":""].join(" ").trim()}">${o===!0?`${validate_component(ue,"Send").$$render(A,{},{},{})}`:`${escape(o)}`}</button>`:""} ${c?`<button class="${["stop-button svelte-1ae7ssi",c!==!0?"padded-button":""].join(" ").trim()}">${c===!0?`${validate_component(ge,"Square").$$render(A,{fill:"none",stroke_width:2.5},{},{})}`:`${escape(c)}`}</button>`:""}</div> </label>`}),at$1=create_ssr_component((A,t,e,Q)=>{let{gradio:a}=t,{label:m="Textbox"}=t,{info:d=void 0}=t,{elem_id:C=""}=t,{elem_classes:g=[]}=t,{visible:B=!0}=t,{value:r=""}=t,{lines:h}=t,{placeholder:w=""}=t,{show_label:b}=t,{max_lines:v=void 0}=t,{type:k="text"}=t,{container:o=!0}=t,{scale:c=null}=t,{min_width:f=void 0}=t,{submit_btn:u=null}=t,{stop_btn:_=null}=t,{show_copy_button:I=!1}=t,{loading_status:s=void 0}=t,{value_is_output:n=!1}=t,{rtl:i=!1}=t,{text_align:x=void 0}=t,{autofocus:p=!1}=t,{autoscroll:K=!0}=t,{interactive:E}=t,{max_length:U=void 0}=t,{html_attributes:M=null}=t,{validation_error:O=null}=t;t.gradio===void 0&&e.gradio&&a!==void 0&&e.gradio(a),t.label===void 0&&e.label&&m!==void 0&&e.label(m),t.info===void 0&&e.info&&d!==void 0&&e.info(d),t.elem_id===void 0&&e.elem_id&&C!==void 0&&e.elem_id(C),t.elem_classes===void 0&&e.elem_classes&&g!==void 0&&e.elem_classes(g),t.visible===void 0&&e.visible&&B!==void 0&&e.visible(B),t.value===void 0&&e.value&&r!==void 0&&e.value(r),t.lines===void 0&&e.lines&&h!==void 0&&e.lines(h),t.placeholder===void 0&&e.placeholder&&w!==void 0&&e.placeholder(w),t.show_label===void 0&&e.show_label&&b!==void 0&&e.show_label(b),t.max_lines===void 0&&e.max_lines&&v!==void 0&&e.max_lines(v),t.type===void 0&&e.type&&k!==void 0&&e.type(k),t.container===void 0&&e.container&&o!==void 0&&e.container(o),t.scale===void 0&&e.scale&&c!==void 0&&e.scale(c),t.min_width===void 0&&e.min_width&&f!==void 0&&e.min_width(f),t.submit_btn===void 0&&e.submit_btn&&u!==void 0&&e.submit_btn(u),t.stop_btn===void 0&&e.stop_btn&&_!==void 0&&e.stop_btn(_),t.show_copy_button===void 0&&e.show_copy_button&&I!==void 0&&e.show_copy_button(I),t.loading_status===void 0&&e.loading_status&&s!==void 0&&e.loading_status(s),t.value_is_output===void 0&&e.value_is_output&&n!==void 0&&e.value_is_output(n),t.rtl===void 0&&e.rtl&&i!==void 0&&e.rtl(i),t.text_align===void 0&&e.text_align&&x!==void 0&&e.text_align(x),t.autofocus===void 0&&e.autofocus&&p!==void 0&&e.autofocus(p),t.autoscroll===void 0&&e.autoscroll&&K!==void 0&&e.autoscroll(K),t.interactive===void 0&&e.interactive&&E!==void 0&&e.interactive(E),t.max_length===void 0&&e.max_length&&U!==void 0&&e.max_length(U),t.html_attributes===void 0&&e.html_attributes&&M!==void 0&&e.html_attributes(M),t.validation_error===void 0&&e.validation_error&&O!==void 0&&e.validation_error(O);let S,W,j=A.head;do S=!0,A.head=j,W=`   ${validate_component(It,"Block").$$render(A,{visible:B,elem_id:C,elem_classes:g,scale:c,min_width:f,allow_overflow:!1,padding:o},{},{default:()=>`${s?`${validate_component(Et,"StatusTracker").$$render(A,Object.assign({},{autoscroll:a.autoscroll},{i18n:a.i18n},s,{show_validation_error:!1}),{},{})}`:""} ${validate_component(P,"TextBox").$$render(A,{label:m,info:d,show_label:b,lines:h,type:k,rtl:i,text_align:x,max_lines:v,placeholder:w,submit_btn:u,stop_btn:_,show_copy_button:I,autofocus:p,container:o,autoscroll:K,max_length:U,html_attributes:M,validation_error:s?.validation_error||O,disabled:!E,value:r,value_is_output:n},{value:T=>{r=T,S=!1;},value_is_output:T=>{n=T,S=!1;}},{})}`})}`;while(!S);return W});

var Index25 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	BaseExample: h$1,
	BaseTextbox: P,
	default: at$1
});

const m={code:"img.svelte-1pijsyv{object-fit:cover}",map:'{"version":3,"file":"Image.svelte","sources":["Image.svelte"],"sourcesContent":["<script lang=\\"ts\\">export let src = void 0;\\n<\/script>\\n\\n<!-- svelte-ignore a11y-missing-attribute -->\\n<img {src} {...$$restProps} on:load />\\n\\n<style>\\n\\timg {\\n\\t\\tobject-fit: cover;\\n\\t}</style>\\n"],"names":[],"mappings":"AAOC,kBAAI,CACH,UAAU,CAAE,KACb"}'},g$1=create_ssr_component((r,e,t,p)=>{let c=compute_rest_props(e,["src"]),{src:s=void 0}=e;return e.src===void 0&&t.src&&s!==void 0&&t.src(s),r.css.add(m),` <img${spread([{src:escape_attribute_value(s)},escape_object(c)],{classes:"svelte-1pijsyv"})}>`});

const w={code:`button.svelte-o34uqh,a.svelte-o34uqh{display:inline-flex;justify-content:center;align-items:center;transition:var(--button-transition);padding:var(--size-0-5) var(--size-2);text-align:center}button.svelte-o34uqh:hover{transform:var(--button-transform-hover)}button.svelte-o34uqh:active,a.svelte-o34uqh:active{transform:var(--button-transform-active)}button[disabled].svelte-o34uqh,a.disabled.svelte-o34uqh{opacity:0.5;filter:grayscale(30%);cursor:not-allowed;transform:none}.hidden.svelte-o34uqh{display:none}.primary.svelte-o34uqh{border:var(--button-border-width) solid var(--button-primary-border-color);background:var(--button-primary-background-fill);color:var(--button-primary-text-color);box-shadow:var(--button-primary-shadow)}.primary.svelte-o34uqh:hover,.primary[disabled].svelte-o34uqh{background:var(--button-primary-background-fill-hover);color:var(--button-primary-text-color-hover)}.primary.svelte-o34uqh:hover{border-color:var(--button-primary-border-color-hover);box-shadow:var(--button-primary-shadow-hover)}.primary.svelte-o34uqh:active{box-shadow:var(--button-primary-shadow-active)}.primary[disabled].svelte-o34uqh{border-color:var(--button-primary-border-color)}.secondary.svelte-o34uqh{border:var(--button-border-width) solid
			var(--button-secondary-border-color);background:var(--button-secondary-background-fill);color:var(--button-secondary-text-color);box-shadow:var(--button-secondary-shadow)}.secondary.svelte-o34uqh:hover,.secondary[disabled].svelte-o34uqh{background:var(--button-secondary-background-fill-hover);color:var(--button-secondary-text-color-hover)}.secondary.svelte-o34uqh:hover{border-color:var(--button-secondary-border-color-hover);box-shadow:var(--button-secondary-shadow-hover)}.secondary.svelte-o34uqh:active{box-shadow:var(--button-secondary-shadow-active)}.secondary[disabled].svelte-o34uqh{border-color:var(--button-secondary-border-color)}.stop.svelte-o34uqh{background:var(--button-cancel-background-fill);color:var(--button-cancel-text-color);border:var(--button-border-width) solid var(--button-cancel-border-color);box-shadow:var(--button-cancel-shadow)}.stop.svelte-o34uqh:hover,.stop[disabled].svelte-o34uqh{background:var(--button-cancel-background-fill-hover)}.stop.svelte-o34uqh:hover{border-color:var(--button-cancel-border-color-hover);box-shadow:var(--button-cancel-shadow-hover)}.stop.svelte-o34uqh:active{box-shadow:var(--button-cancel-shadow-active)}.stop[disabled].svelte-o34uqh{border-color:var(--button-cancel-border-color)}.sm.svelte-o34uqh{border-radius:var(--button-small-radius);padding:var(--button-small-padding);font-weight:var(--button-small-text-weight);font-size:var(--button-small-text-size)}.md.svelte-o34uqh{border-radius:var(--button-medium-radius);padding:var(--button-medium-padding);font-weight:var(--button-medium-text-weight);font-size:var(--button-medium-text-size)}.lg.svelte-o34uqh{border-radius:var(--button-large-radius);padding:var(--button-large-padding);font-weight:var(--button-large-text-weight);font-size:var(--button-large-text-size)}.button-icon{width:var(--text-xl);height:var(--text-xl)}.button-icon.right-padded{margin-right:var(--spacing-md)}.huggingface.svelte-o34uqh{background:rgb(20, 28, 46);color:white}.huggingface.svelte-o34uqh:hover{background:rgb(40, 48, 66);color:white}`,map:'{"version":3,"file":"Button.svelte","sources":["Button.svelte"],"sourcesContent":["<script lang=\\"ts\\">import {} from \\"@gradio/client\\";\\nimport { Image } from \\"@gradio/image/shared\\";\\nexport let elem_id = \\"\\";\\nexport let elem_classes = [];\\nexport let visible = true;\\nexport let variant = \\"secondary\\";\\nexport let size = \\"lg\\";\\nexport let value = null;\\nexport let link = null;\\nexport let icon = null;\\nexport let disabled = false;\\nexport let scale = null;\\nexport let min_width = void 0;\\n<\/script>\\n\\n{#if link && link.length > 0}\\n\\t<a\\n\\t\\thref={link}\\n\\t\\trel=\\"noopener noreferrer\\"\\n\\t\\tclass:hidden={visible === false || visible === \\"hidden\\"}\\n\\t\\tclass:disabled\\n\\t\\taria-disabled={disabled}\\n\\t\\tclass=\\"{size} {variant} {elem_classes.join(\' \')}\\"\\n\\t\\tstyle:flex-grow={scale}\\n\\t\\tstyle:pointer-events={disabled ? \\"none\\" : null}\\n\\t\\tstyle:width={scale === 0 ? \\"fit-content\\" : null}\\n\\t\\tstyle:min-width={typeof min_width === \\"number\\"\\n\\t\\t\\t? `calc(min(${min_width}px, 100%))`\\n\\t\\t\\t: null}\\n\\t\\tid={elem_id}\\n\\t>\\n\\t\\t{#if icon}\\n\\t\\t\\t<Image class=\\"button-icon\\" src={icon.url} alt={`${value} icon`} />\\n\\t\\t{/if}\\n\\t\\t<slot />\\n\\t</a>\\n{:else}\\n\\t<button\\n\\t\\ton:click\\n\\t\\tclass:hidden={visible === false || visible === \\"hidden\\"}\\n\\t\\tclass=\\"{size} {variant} {elem_classes.join(\' \')}\\"\\n\\t\\tstyle:flex-grow={scale}\\n\\t\\tstyle:width={scale === 0 ? \\"fit-content\\" : null}\\n\\t\\tstyle:min-width={typeof min_width === \\"number\\"\\n\\t\\t\\t? `calc(min(${min_width}px, 100%))`\\n\\t\\t\\t: null}\\n\\t\\tid={elem_id}\\n\\t\\t{disabled}\\n\\t>\\n\\t\\t{#if icon}\\n\\t\\t\\t<Image\\n\\t\\t\\t\\tclass={`button-icon ${value ? \\"right-padded\\" : \\"\\"}`}\\n\\t\\t\\t\\tsrc={icon.url}\\n\\t\\t\\t\\talt={`${value} icon`}\\n\\t\\t\\t/>\\n\\t\\t{/if}\\n\\t\\t<slot />\\n\\t</button>\\n{/if}\\n\\n<style>\\n\\tbutton,\\n\\ta {\\n\\t\\tdisplay: inline-flex;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\ttransition: var(--button-transition);\\n\\t\\tpadding: var(--size-0-5) var(--size-2);\\n\\t\\ttext-align: center;\\n\\t}\\n\\n\\tbutton:hover {\\n\\t\\ttransform: var(--button-transform-hover);\\n\\t}\\n\\n\\tbutton:active,\\n\\ta:active {\\n\\t\\ttransform: var(--button-transform-active);\\n\\t}\\n\\n\\tbutton[disabled],\\n\\ta.disabled {\\n\\t\\topacity: 0.5;\\n\\t\\tfilter: grayscale(30%);\\n\\t\\tcursor: not-allowed;\\n\\t\\ttransform: none;\\n\\t}\\n\\n\\t.hidden {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\t.primary {\\n\\t\\tborder: var(--button-border-width) solid var(--button-primary-border-color);\\n\\t\\tbackground: var(--button-primary-background-fill);\\n\\t\\tcolor: var(--button-primary-text-color);\\n\\t\\tbox-shadow: var(--button-primary-shadow);\\n\\t}\\n\\t.primary:hover,\\n\\t.primary[disabled] {\\n\\t\\tbackground: var(--button-primary-background-fill-hover);\\n\\t\\tcolor: var(--button-primary-text-color-hover);\\n\\t}\\n\\n\\t.primary:hover {\\n\\t\\tborder-color: var(--button-primary-border-color-hover);\\n\\t\\tbox-shadow: var(--button-primary-shadow-hover);\\n\\t}\\n\\t.primary:active {\\n\\t\\tbox-shadow: var(--button-primary-shadow-active);\\n\\t}\\n\\n\\t.primary[disabled] {\\n\\t\\tborder-color: var(--button-primary-border-color);\\n\\t}\\n\\n\\t.secondary {\\n\\t\\tborder: var(--button-border-width) solid\\n\\t\\t\\tvar(--button-secondary-border-color);\\n\\t\\tbackground: var(--button-secondary-background-fill);\\n\\t\\tcolor: var(--button-secondary-text-color);\\n\\t\\tbox-shadow: var(--button-secondary-shadow);\\n\\t}\\n\\n\\t.secondary:hover,\\n\\t.secondary[disabled] {\\n\\t\\tbackground: var(--button-secondary-background-fill-hover);\\n\\t\\tcolor: var(--button-secondary-text-color-hover);\\n\\t}\\n\\n\\t.secondary:hover {\\n\\t\\tborder-color: var(--button-secondary-border-color-hover);\\n\\t\\tbox-shadow: var(--button-secondary-shadow-hover);\\n\\t}\\n\\t.secondary:active {\\n\\t\\tbox-shadow: var(--button-secondary-shadow-active);\\n\\t}\\n\\n\\t.secondary[disabled] {\\n\\t\\tborder-color: var(--button-secondary-border-color);\\n\\t}\\n\\n\\t.stop {\\n\\t\\tbackground: var(--button-cancel-background-fill);\\n\\t\\tcolor: var(--button-cancel-text-color);\\n\\t\\tborder: var(--button-border-width) solid var(--button-cancel-border-color);\\n\\t\\tbox-shadow: var(--button-cancel-shadow);\\n\\t}\\n\\n\\t.stop:hover,\\n\\t.stop[disabled] {\\n\\t\\tbackground: var(--button-cancel-background-fill-hover);\\n\\t}\\n\\n\\t.stop:hover {\\n\\t\\tborder-color: var(--button-cancel-border-color-hover);\\n\\t\\tbox-shadow: var(--button-cancel-shadow-hover);\\n\\t}\\n\\t.stop:active {\\n\\t\\tbox-shadow: var(--button-cancel-shadow-active);\\n\\t}\\n\\n\\t.stop[disabled] {\\n\\t\\tborder-color: var(--button-cancel-border-color);\\n\\t}\\n\\n\\t.sm {\\n\\t\\tborder-radius: var(--button-small-radius);\\n\\t\\tpadding: var(--button-small-padding);\\n\\t\\tfont-weight: var(--button-small-text-weight);\\n\\t\\tfont-size: var(--button-small-text-size);\\n\\t}\\n\\n\\t.md {\\n\\t\\tborder-radius: var(--button-medium-radius);\\n\\t\\tpadding: var(--button-medium-padding);\\n\\t\\tfont-weight: var(--button-medium-text-weight);\\n\\t\\tfont-size: var(--button-medium-text-size);\\n\\t}\\n\\n\\t.lg {\\n\\t\\tborder-radius: var(--button-large-radius);\\n\\t\\tpadding: var(--button-large-padding);\\n\\t\\tfont-weight: var(--button-large-text-weight);\\n\\t\\tfont-size: var(--button-large-text-size);\\n\\t}\\n\\n\\t:global(.button-icon) {\\n\\t\\twidth: var(--text-xl);\\n\\t\\theight: var(--text-xl);\\n\\t}\\n\\t:global(.button-icon.right-padded) {\\n\\t\\tmargin-right: var(--spacing-md);\\n\\t}\\n\\n\\t.huggingface {\\n\\t\\tbackground: rgb(20, 28, 46);\\n\\t\\tcolor: white;\\n\\t}\\n\\n\\t.huggingface:hover {\\n\\t\\tbackground: rgb(40, 48, 66);\\n\\t\\tcolor: white;\\n\\t}</style>\\n"],"names":[],"mappings":"AA6DC,oBAAM,CACN,eAAE,CACD,OAAO,CAAE,WAAW,CACpB,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,UAAU,CAAE,IAAI,mBAAmB,CAAC,CACpC,OAAO,CAAE,IAAI,UAAU,CAAC,CAAC,IAAI,QAAQ,CAAC,CACtC,UAAU,CAAE,MACb,CAEA,oBAAM,MAAO,CACZ,SAAS,CAAE,IAAI,wBAAwB,CACxC,CAEA,oBAAM,OAAO,CACb,eAAC,OAAQ,CACR,SAAS,CAAE,IAAI,yBAAyB,CACzC,CAEA,MAAM,CAAC,QAAQ,eAAC,CAChB,CAAC,uBAAU,CACV,OAAO,CAAE,GAAG,CACZ,MAAM,CAAE,UAAU,GAAG,CAAC,CACtB,MAAM,CAAE,WAAW,CACnB,SAAS,CAAE,IACZ,CAEA,qBAAQ,CACP,OAAO,CAAE,IACV,CAEA,sBAAS,CACR,MAAM,CAAE,IAAI,qBAAqB,CAAC,CAAC,KAAK,CAAC,IAAI,6BAA6B,CAAC,CAC3E,UAAU,CAAE,IAAI,gCAAgC,CAAC,CACjD,KAAK,CAAE,IAAI,2BAA2B,CAAC,CACvC,UAAU,CAAE,IAAI,uBAAuB,CACxC,CACA,sBAAQ,MAAM,CACd,QAAQ,CAAC,QAAQ,eAAE,CAClB,UAAU,CAAE,IAAI,sCAAsC,CAAC,CACvD,KAAK,CAAE,IAAI,iCAAiC,CAC7C,CAEA,sBAAQ,MAAO,CACd,YAAY,CAAE,IAAI,mCAAmC,CAAC,CACtD,UAAU,CAAE,IAAI,6BAA6B,CAC9C,CACA,sBAAQ,OAAQ,CACf,UAAU,CAAE,IAAI,8BAA8B,CAC/C,CAEA,QAAQ,CAAC,QAAQ,eAAE,CAClB,YAAY,CAAE,IAAI,6BAA6B,CAChD,CAEA,wBAAW,CACV,MAAM,CAAE,IAAI,qBAAqB,CAAC,CAAC;AACrC,GAAG,IAAI,+BAA+B,CAAC,CACrC,UAAU,CAAE,IAAI,kCAAkC,CAAC,CACnD,KAAK,CAAE,IAAI,6BAA6B,CAAC,CACzC,UAAU,CAAE,IAAI,yBAAyB,CAC1C,CAEA,wBAAU,MAAM,CAChB,UAAU,CAAC,QAAQ,eAAE,CACpB,UAAU,CAAE,IAAI,wCAAwC,CAAC,CACzD,KAAK,CAAE,IAAI,mCAAmC,CAC/C,CAEA,wBAAU,MAAO,CAChB,YAAY,CAAE,IAAI,qCAAqC,CAAC,CACxD,UAAU,CAAE,IAAI,+BAA+B,CAChD,CACA,wBAAU,OAAQ,CACjB,UAAU,CAAE,IAAI,gCAAgC,CACjD,CAEA,UAAU,CAAC,QAAQ,eAAE,CACpB,YAAY,CAAE,IAAI,+BAA+B,CAClD,CAEA,mBAAM,CACL,UAAU,CAAE,IAAI,+BAA+B,CAAC,CAChD,KAAK,CAAE,IAAI,0BAA0B,CAAC,CACtC,MAAM,CAAE,IAAI,qBAAqB,CAAC,CAAC,KAAK,CAAC,IAAI,4BAA4B,CAAC,CAC1E,UAAU,CAAE,IAAI,sBAAsB,CACvC,CAEA,mBAAK,MAAM,CACX,KAAK,CAAC,QAAQ,eAAE,CACf,UAAU,CAAE,IAAI,qCAAqC,CACtD,CAEA,mBAAK,MAAO,CACX,YAAY,CAAE,IAAI,kCAAkC,CAAC,CACrD,UAAU,CAAE,IAAI,4BAA4B,CAC7C,CACA,mBAAK,OAAQ,CACZ,UAAU,CAAE,IAAI,6BAA6B,CAC9C,CAEA,KAAK,CAAC,QAAQ,eAAE,CACf,YAAY,CAAE,IAAI,4BAA4B,CAC/C,CAEA,iBAAI,CACH,aAAa,CAAE,IAAI,qBAAqB,CAAC,CACzC,OAAO,CAAE,IAAI,sBAAsB,CAAC,CACpC,WAAW,CAAE,IAAI,0BAA0B,CAAC,CAC5C,SAAS,CAAE,IAAI,wBAAwB,CACxC,CAEA,iBAAI,CACH,aAAa,CAAE,IAAI,sBAAsB,CAAC,CAC1C,OAAO,CAAE,IAAI,uBAAuB,CAAC,CACrC,WAAW,CAAE,IAAI,2BAA2B,CAAC,CAC7C,SAAS,CAAE,IAAI,yBAAyB,CACzC,CAEA,iBAAI,CACH,aAAa,CAAE,IAAI,qBAAqB,CAAC,CACzC,OAAO,CAAE,IAAI,sBAAsB,CAAC,CACpC,WAAW,CAAE,IAAI,0BAA0B,CAAC,CAC5C,SAAS,CAAE,IAAI,wBAAwB,CACxC,CAEQ,YAAc,CACrB,KAAK,CAAE,IAAI,SAAS,CAAC,CACrB,MAAM,CAAE,IAAI,SAAS,CACtB,CACQ,yBAA2B,CAClC,YAAY,CAAE,IAAI,YAAY,CAC/B,CAEA,0BAAa,CACZ,UAAU,CAAE,IAAI,EAAE,CAAC,CAAC,EAAE,CAAC,CAAC,EAAE,CAAC,CAC3B,KAAK,CAAE,KACR,CAEA,0BAAY,MAAO,CAClB,UAAU,CAAE,IAAI,EAAE,CAAC,CAAC,EAAE,CAAC,CAAC,EAAE,CAAC,CAC3B,KAAK,CAAE,KACR"}'},y=create_ssr_component((u,t,A,b)=>{let{elem_id:d=""}=t,{elem_classes:v=[]}=t,{visible:e=!0}=t,{variant:l="secondary"}=t,{size:c="lg"}=t,{value:C=null}=t,{link:i=null}=t,{icon:o=null}=t,{disabled:n=!1}=t,{scale:r=null}=t,{min_width:a=void 0}=t;return t.elem_id===void 0&&A.elem_id&&d!==void 0&&A.elem_id(d),t.elem_classes===void 0&&A.elem_classes&&v!==void 0&&A.elem_classes(v),t.visible===void 0&&A.visible&&e!==void 0&&A.visible(e),t.variant===void 0&&A.variant&&l!==void 0&&A.variant(l),t.size===void 0&&A.size&&c!==void 0&&A.size(c),t.value===void 0&&A.value&&C!==void 0&&A.value(C),t.link===void 0&&A.link&&i!==void 0&&A.link(i),t.icon===void 0&&A.icon&&o!==void 0&&A.icon(o),t.disabled===void 0&&A.disabled&&n!==void 0&&A.disabled(n),t.scale===void 0&&A.scale&&r!==void 0&&A.scale(r),t.min_width===void 0&&A.min_width&&a!==void 0&&A.min_width(a),u.css.add(w),`${i&&i.length>0?`<a${add_attribute("href",i,0)} rel="noopener noreferrer"${add_attribute("aria-disabled",n,0)} class="${[escape(c,!0)+" "+escape(l,!0)+" "+escape(v.join(" "),!0)+" svelte-o34uqh",(e===!1||e==="hidden"?"hidden":"")+" "+(n?"disabled":"")].join(" ").trim()}"${add_attribute("id",d,0)}${add_styles({"flex-grow":r,"pointer-events":n?"none":null,width:r===0?"fit-content":null,"min-width":typeof a=="number"?`calc(min(${a}px, 100%))`:null})}>${o?`${validate_component(g$1,"Image").$$render(u,{class:"button-icon",src:o.url,alt:`${C} icon`},{},{})}`:""} ${b.default?b.default({}):""}</a>`:`<button class="${[escape(c,!0)+" "+escape(l,!0)+" "+escape(v.join(" "),!0)+" svelte-o34uqh",e===!1||e==="hidden"?"hidden":""].join(" ").trim()}"${add_attribute("id",d,0)} ${n?"disabled":""}${add_styles({"flex-grow":r,width:r===0?"fit-content":null,"min-width":typeof a=="number"?`calc(min(${a}px, 100%))`:null})}>${o?`${validate_component(g$1,"Image").$$render(u,{class:`button-icon ${C?"right-padded":""}`,src:o.url,alt:`${C} icon`},{},{})}`:""} ${b.default?b.default({}):""}</button>`}`}),k=create_ssr_component((u,t,A,b)=>{let{elem_id:d=""}=t,{elem_classes:v=[]}=t,{visible:e=!0}=t,{value:l}=t,{variant:c="secondary"}=t,{interactive:C}=t,{size:i="lg"}=t,{scale:o=null}=t,{icon:n=null}=t,{link:r=null}=t,{min_width:a=void 0}=t,{gradio:B}=t;return t.elem_id===void 0&&A.elem_id&&d!==void 0&&A.elem_id(d),t.elem_classes===void 0&&A.elem_classes&&v!==void 0&&A.elem_classes(v),t.visible===void 0&&A.visible&&e!==void 0&&A.visible(e),t.value===void 0&&A.value&&l!==void 0&&A.value(l),t.variant===void 0&&A.variant&&c!==void 0&&A.variant(c),t.interactive===void 0&&A.interactive&&C!==void 0&&A.interactive(C),t.size===void 0&&A.size&&i!==void 0&&A.size(i),t.scale===void 0&&A.scale&&o!==void 0&&A.scale(o),t.icon===void 0&&A.icon&&n!==void 0&&A.icon(n),t.link===void 0&&A.link&&r!==void 0&&A.link(r),t.min_width===void 0&&A.min_width&&a!==void 0&&A.min_width(a),t.gradio===void 0&&A.gradio&&B!==void 0&&A.gradio(B),`${validate_component(y,"Button").$$render(u,{value:l,variant:c,elem_id:d,elem_classes:v,size:i,scale:o,link:r,icon:n,min_width:a,visible:e,disabled:!C},{},{default:()=>`${escape(l??"")}`})}`});

var Index36 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	BaseButton: y,
	default: k
});

const x={code:"div.svelte-bnzux8{display:flex;position:relative;flex-direction:column;gap:var(--layout-gap)}div.svelte-bnzux8>*,div.svelte-bnzux8>.form > *{width:var(--size-full)}.hide.svelte-bnzux8{display:none}.compact.svelte-bnzux8>*,.compact.svelte-bnzux8 .box{border-radius:0}.compact.svelte-bnzux8,.panel.svelte-bnzux8{border:solid var(--panel-border-width) var(--panel-border-color);border-radius:var(--container-radius);background:var(--panel-background-fill);padding:var(--spacing-lg)}",map:`{"version":3,"file":"Index.svelte","sources":["Index.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { StatusTracker } from \\"@gradio/statustracker\\";\\nexport let scale = null;\\nexport let min_width = 0;\\nexport let elem_id = \\"\\";\\nexport let elem_classes = [];\\nexport let visible = true;\\nexport let variant = \\"default\\";\\nexport let loading_status = void 0;\\nexport let gradio = void 0;\\nexport let show_progress = false;\\n<\/script>\\n\\n<div\\n\\tid={elem_id}\\n\\tclass=\\"column {elem_classes.join(' ')}\\"\\n\\tclass:compact={variant === \\"compact\\"}\\n\\tclass:panel={variant === \\"panel\\"}\\n\\tclass:hide={!visible}\\n\\tstyle:flex-grow={scale}\\n\\tstyle:min-width=\\"calc(min({min_width}px, 100%))\\"\\n>\\n\\t{#if loading_status && show_progress && gradio}\\n\\t\\t<StatusTracker\\n\\t\\t\\tautoscroll={gradio.autoscroll}\\n\\t\\t\\ti18n={gradio.i18n}\\n\\t\\t\\t{...loading_status}\\n\\t\\t\\tstatus={loading_status\\n\\t\\t\\t\\t? loading_status.status == \\"pending\\"\\n\\t\\t\\t\\t\\t? \\"generating\\"\\n\\t\\t\\t\\t\\t: loading_status.status\\n\\t\\t\\t\\t: null}\\n\\t\\t/>\\n\\t{/if}\\n\\t<slot />\\n</div>\\n\\n<style>\\n\\tdiv {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: relative;\\n\\t\\tflex-direction: column;\\n\\t\\tgap: var(--layout-gap);\\n\\t}\\n\\n\\tdiv > :global(*),\\n\\tdiv > :global(.form > *) {\\n\\t\\twidth: var(--size-full);\\n\\t}\\n\\n\\t.hide {\\n\\t\\tdisplay: none;\\n\\t}\\n\\n\\t.compact > :global(*),\\n\\t.compact :global(.box) {\\n\\t\\tborder-radius: 0;\\n\\t}\\n\\n\\t.compact,\\n\\t.panel {\\n\\t\\tborder: solid var(--panel-border-width) var(--panel-border-color);\\n\\t\\tborder-radius: var(--container-radius);\\n\\t\\tbackground: var(--panel-background-fill);\\n\\t\\tpadding: var(--spacing-lg);\\n\\t}</style>\\n"],"names":[],"mappings":"AAqCC,iBAAI,CACH,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,QAAQ,CAClB,cAAc,CAAE,MAAM,CACtB,GAAG,CAAE,IAAI,YAAY,CACtB,CAEA,iBAAG,CAAW,CAAE,CAChB,iBAAG,CAAW,SAAW,CACxB,KAAK,CAAE,IAAI,WAAW,CACvB,CAEA,mBAAM,CACL,OAAO,CAAE,IACV,CAEA,sBAAQ,CAAW,CAAE,CACrB,sBAAQ,CAAS,IAAM,CACtB,aAAa,CAAE,CAChB,CAEA,sBAAQ,CACR,oBAAO,CACN,MAAM,CAAE,KAAK,CAAC,IAAI,oBAAoB,CAAC,CAAC,IAAI,oBAAoB,CAAC,CACjE,aAAa,CAAE,IAAI,kBAAkB,CAAC,CACtC,UAAU,CAAE,IAAI,uBAAuB,CAAC,CACxC,OAAO,CAAE,IAAI,YAAY,CAC1B"}`},h=create_ssr_component((c,t,e,v)=>{let{scale:i=null}=t,{min_width:n=0}=t,{elem_id:o=""}=t,{elem_classes:s=[]}=t,{visible:r=!0}=t,{variant:A="default"}=t,{loading_status:a=void 0}=t,{gradio:l=void 0}=t,{show_progress:d=!1}=t;return t.scale===void 0&&e.scale&&i!==void 0&&e.scale(i),t.min_width===void 0&&e.min_width&&n!==void 0&&e.min_width(n),t.elem_id===void 0&&e.elem_id&&o!==void 0&&e.elem_id(o),t.elem_classes===void 0&&e.elem_classes&&s!==void 0&&e.elem_classes(s),t.visible===void 0&&e.visible&&r!==void 0&&e.visible(r),t.variant===void 0&&e.variant&&A!==void 0&&e.variant(A),t.loading_status===void 0&&e.loading_status&&a!==void 0&&e.loading_status(a),t.gradio===void 0&&e.gradio&&l!==void 0&&e.gradio(l),t.show_progress===void 0&&e.show_progress&&d!==void 0&&e.show_progress(d),c.css.add(x),`<div${add_attribute("id",o,0)} class="${["column "+escape(s.join(" "),!0)+" svelte-bnzux8",(A==="compact"?"compact":"")+" "+(A==="panel"?"panel":"")+" "+(r?"":"hide")].join(" ").trim()}"${add_styles({"flex-grow":i,"min-width":`calc(min(${n}px, 100%))`})}>${a&&d&&l?`${validate_component(Et,"StatusTracker").$$render(c,Object.assign({},{autoscroll:l.autoscroll},{i18n:l.i18n},a,{status:a?a.status=="pending"?"generating":a.status:null}),{},{})}`:""} ${v.default?v.default({}):""} </div>`});

var Index20 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	default: h
});

const{Object:tn}=globals,nn=create_ssr_component((s,e,t,J)=>{let m=compute_rest_props(e,["root","component","target","theme_mode","instance","value","elem_id","elem_classes","_id","visible"]),{root:_}=e,{component:p}=e,{target:i}=e,{theme_mode:h}=e,{instance:w}=e,{value:v}=e,{elem_id:x}=e,{elem_classes:d}=e,{_id:S}=e,{visible:b}=e;const N=(B,j,$)=>new CustomEvent("prop_change",{detail:{id:B,prop:j,value:$}});function R(B){return new Proxy(B,{construct($,oe){const ee=new $(...oe),y=Object.keys(ee.$$.props);function te(F){return function(me){if(!i)return;const re=N(S,F,me);i.dispatchEvent(re);}}return y.forEach(F=>{binding_callbacks.push(()=>bind(ee,F,te(F)));}),ee}})}let Q=R(p);const H=["description","info","title","placeholder","value","label"];function g(B){for(const j in B)H.includes(j)&&(B[j]=oa$1(B[j]));}e.root===void 0&&t.root&&_!==void 0&&t.root(_),e.component===void 0&&t.component&&p!==void 0&&t.component(p),e.target===void 0&&t.target&&i!==void 0&&t.target(i),e.theme_mode===void 0&&t.theme_mode&&h!==void 0&&t.theme_mode(h),e.instance===void 0&&t.instance&&w!==void 0&&t.instance(w),e.value===void 0&&t.value&&v!==void 0&&t.value(v),e.elem_id===void 0&&t.elem_id&&x!==void 0&&t.elem_id(x),e.elem_classes===void 0&&t.elem_classes&&d!==void 0&&t.elem_classes(d),e._id===void 0&&t._id&&S!==void 0&&t._id(S),e.visible===void 0&&t.visible&&b!==void 0&&t.visible(b);let f,G,X=s.head;do f=!0,s.head=X,g(m),v=oa$1(v),G=`  ${b?`${validate_component(Q||missing_component,"svelte:component").$$render(s,tn.assign({},{elem_id:x},{elem_classes:d},{target:i},{visible:b},m,{theme_mode:h},{root:_},{this:w},{value:v}),{this:B=>{w=B,f=!1;},value:B=>{v=B,f=!1;}},{default:()=>`${J.default?J.default({}):""}`})}`:""}`;while(!f);return G}),ct=create_ssr_component((s,e,t,J)=>{let m,_;_=subscribe(ra$1,f=>m=f);let{root:p}=e,{node:i}=e,{parent:h=null}=e,{target:w}=e,{theme_mode:v}=e,{version:x}=e,{autoscroll:d}=e,{max_file_size:S}=e,{client:b}=e;createEventDispatcher();setContext("BLOCK_KEY",h),e.root===void 0&&t.root&&p!==void 0&&t.root(p),e.node===void 0&&t.node&&i!==void 0&&t.node(i),e.parent===void 0&&t.parent&&h!==void 0&&t.parent(h),e.target===void 0&&t.target&&w!==void 0&&t.target(w),e.theme_mode===void 0&&t.theme_mode&&v!==void 0&&t.theme_mode(v),e.version===void 0&&t.version&&x!==void 0&&t.version(x),e.autoscroll===void 0&&t.autoscroll&&d!==void 0&&t.autoscroll(d),e.max_file_size===void 0&&t.max_file_size&&S!==void 0&&t.max_file_size(S),e.client===void 0&&t.client&&b!==void 0&&t.client(b);let Q,H,g=s.head;do{if(Q=!0,s.head=g,i&&(i.children=i.children&&i.children.filter(f=>{const G=i.type!=="statustracker";return G})),i&&i.type==="form")if(i.children?.every(G=>G.props.visible===!1||G.props.visible==="hidden")){const G=i.children?.some(X=>X.props.visible==="hidden");i.props.visible=G?"hidden":!1;}else i.props.visible=!0;i.props.gradio=new m$1(i.id,w,v,x,p,d,S,m,b,rn$2),H=`${i.component?`${validate_component(nn,"RenderComponent").$$render(s,Object.assign({},{_id:i?.id},{component:i.component},{elem_id:"elem_id"in i.props&&i.props.elem_id||`component-${i.id}`},{elem_classes:"elem_classes"in i.props&&i.props.elem_classes||[]},{target:w},i.props,{theme_mode:v},{root:p},{visible:typeof i.props.visible=="boolean"||i.props.visible==="hidden"?i.props.visible:!0},{instance:i.instance},{value:i.props.value}),{instance:f=>{i.instance=f,Q=!1;},value:f=>{i.props.value=f,Q=!1;}},{default:()=>`${i.children&&i.children.length?`${each(i.children,f=>`${validate_component(ct,"svelte:self").$$render(s,{node:f,component:f.component,target:w,id:f.id,root:p,theme_mode:v,max_file_size:S,client:b},{},{})}`)}`:""}`})}`:""}`;}while(!Q);return _(),H}),on=create_ssr_component((s,e,t,J)=>{let{rootNode:m}=e,{root:_}=e,{target:p}=e,{theme_mode:i}=e,{version:h}=e,{autoscroll:w}=e,{max_file_size:v=null}=e,{client:x}=e;createEventDispatcher();return e.rootNode===void 0&&t.rootNode&&m!==void 0&&t.rootNode(m),e.root===void 0&&t.root&&_!==void 0&&t.root(_),e.target===void 0&&t.target&&p!==void 0&&t.target(p),e.theme_mode===void 0&&t.theme_mode&&i!==void 0&&t.theme_mode(i),e.version===void 0&&t.version&&h!==void 0&&t.version(h),e.autoscroll===void 0&&t.autoscroll&&w!==void 0&&t.autoscroll(w),e.max_file_size===void 0&&t.max_file_size&&v!==void 0&&t.max_file_size(v),e.client===void 0&&t.client&&x!==void 0&&t.client(x),`${m?`${validate_component(ct,"Render").$$render(s,{node:m,root:_,target:p,theme_mode:i,version:h,autoscroll:w,max_file_size:v,client:x},{},{})}`:""}`}),an="data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='576'%20height='576'%20viewBox='0%200%20576%20576'%20fill='none'%3e%3cpath%20d='M287.5%20229L86%20344.5L287.5%20460L489%20344.5L287.5%20229Z'%20stroke='url(%23paint0_linear_102_7)'%20stroke-width='59'%20stroke-linejoin='round'/%3e%3cpath%20d='M287.5%20116L86%20231.5L287.5%20347L489%20231.5L287.5%20116Z'%20stroke='url(%23paint1_linear_102_7)'%20stroke-width='59'%20stroke-linejoin='round'/%3e%3cpath%20d='M86%20344L288%20229'%20stroke='url(%23paint2_linear_102_7)'%20stroke-width='59'%20stroke-linejoin='bevel'/%3e%3cdefs%3e%3clinearGradient%20id='paint0_linear_102_7'%20x1='60'%20y1='341'%20x2='429.5'%20y2='344'%20gradientUnits='userSpaceOnUse'%3e%3cstop%20stop-color='%23F9D100'/%3e%3cstop%20offset='1'%20stop-color='%23F97700'/%3e%3c/linearGradient%3e%3clinearGradient%20id='paint1_linear_102_7'%20x1='513.5'%20y1='231'%20x2='143.5'%20y2='231'%20gradientUnits='userSpaceOnUse'%3e%3cstop%20stop-color='%23F9D100'/%3e%3cstop%20offset='1'%20stop-color='%23F97700'/%3e%3c/linearGradient%3e%3clinearGradient%20id='paint2_linear_102_7'%20x1='60'%20y1='344'%20x2='428.987'%20y2='341.811'%20gradientUnits='userSpaceOnUse'%3e%3cstop%20stop-color='%23F9D100'/%3e%3cstop%20offset='1'%20stop-color='%23F97700'/%3e%3c/linearGradient%3e%3c/defs%3e%3c/svg%3e",sn="data:image/svg+xml,%3csvg%20width='28'%20height='28'%20viewBox='0%200%2028%2028'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M26.9425%202.94265C27.4632%202.42195%2027.4632%201.57773%2026.9425%201.05703C26.4218%200.536329%2025.5776%200.536329%2025.0569%201.05703L22.5713%203.54256C21.1213%202.59333%2019.5367%202.43378%2018.1753%202.64006C16.5495%202.88638%2015.1127%203.66838%2014.3905%204.39053L12.3905%206.39053C12.1405%206.64058%2012%206.97972%2012%207.33334C12%207.68697%2012.1405%208.0261%2012.3905%208.27615L19.7239%2015.6095C20.2446%2016.1302%2021.0888%2016.1302%2021.6095%2015.6095L23.6095%2013.6095C24.3316%2012.8873%2025.1136%2011.4505%2025.36%209.82475C25.5663%208.46312%2025.4066%206.87827%2024.4571%205.42807L26.9425%202.94265Z'%20fill='%233c4555'/%3e%3cpath%20fill-rule='evenodd'%20clip-rule='evenodd'%20d='M12.276%2012.9426C12.7967%2012.4219%2012.7967%2011.5777%2012.276%2011.057C11.7553%2010.5363%2010.9111%2010.5363%2010.3904%2011.057L8.66651%2012.7809L8.27615%2012.3905C8.0261%2012.1405%207.68697%2012%207.33334%2012C6.97972%2012%206.64058%2012.1405%206.39053%2012.3905L4.39053%2014.3905C3.66838%2015.1127%202.88638%2016.5495%202.64006%2018.1753C2.43377%2019.5367%202.59333%2021.1214%203.54262%2022.5714L1.05703%2025.057C0.536329%2025.5777%200.536329%2026.4219%201.05703%2026.9426C1.57773%2027.4633%202.42195%2027.4633%202.94265%2026.9426L5.42817%2024.4571C6.87835%2025.4066%208.46315%2025.5663%209.82475%2025.36C11.4505%2025.1136%2012.8873%2024.3316%2013.6095%2023.6095L15.6095%2021.6095C16.1302%2021.0888%2016.1302%2020.2446%2015.6095%2019.7239L15.2188%2019.3332L16.9426%2017.6093C17.4633%2017.0886%2017.4633%2016.2444%2016.9426%2015.7237C16.4219%2015.203%2015.5777%2015.203%2015.057%2015.7237L13.3332%2017.4475L10.5521%2014.6665L12.276%2012.9426Z'%20fill='%23FF7C00'/%3e%3c/svg%3e",rn="data:image/svg+xml,%3csvg%20width='24'%20height='24'%20viewBox='0%200%2024%2024'%20xmlns='http://www.w3.org/2000/svg'%3e%3c!--%20Outer%20gear%20teeth%20(gray)%20--%3e%3cpath%20d='M19.14%2012.94c.04-.3.06-.61.06-.94%200-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24%200-.43.17-.47.41l-.36%202.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47%200-.59.22L2.74%208.87c-.12.21-.08.47.12.61l2.03%201.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03%201.58c-.18.14-.23.41-.12.61l1.92%203.32c.12.22.37.29.59.22l2.39-.96c.5.38%201.03.7%201.62.94l.36%202.54c.05.24.24.41.48.41h3.84c.24%200%20.44-.17.47-.41l.36-2.54c.59-.24%201.13-.56%201.62-.94l2.39.96c.22.08.47%200%20.59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12%2015.6c-1.98%200-3.6-1.62-3.6-3.6s1.62-3.6%203.6-3.6%203.6%201.62%203.6%203.6-1.62%203.6-3.6%203.6z'%20fill='%23808080'/%3e%3c!--%20Inner%20circle%20(now%20gray)%20--%3e%3ccircle%20cx='12'%20cy='12'%20r='2.5'%20fill='%23808080'/%3e%3c/svg%3e",ln="data:image/svg+xml,%3csvg%20viewBox='0%200%2020%2020'%20version='1.1'%20xmlns='http://www.w3.org/2000/svg'%20xmlns:xlink='http://www.w3.org/1999/xlink'%20fill='%23000000'%3e%3cg%20id='SVGRepo_bgCarrier'%20stroke-width='0'%3e%3c/g%3e%3cg%20id='SVGRepo_tracerCarrier'%20stroke-linecap='round'%20stroke-linejoin='round'%3e%3c/g%3e%3cg%20id='SVGRepo_iconCarrier'%3e%3ctitle%3erecord%20[%23982]%3c/title%3e%3cdesc%3eCreated%20with%20Sketch.%3c/desc%3e%3cdefs%3e%3c/defs%3e%3cg%20id='Page-1'%20stroke='none'%20stroke-width='1'%20fill='none'%20fill-rule='evenodd'%3e%3cg%20id='Dribbble-Light-Preview'%20transform='translate(-380.000000,%20-3839.000000)'%20fill='%23FF0000'%3e%3cg%20id='icons'%20transform='translate(56.000000,%20160.000000)'%3e%3cpath%20d='M338,3689%20C338,3691.209%20336.209,3693%20334,3693%20C331.791,3693%20330,3691.209%20330,3689%20C330,3686.791%20331.791,3685%20334,3685%20C336.209,3685%20338,3686.791%20338,3689%20M334,3697%20C329.589,3697%20326,3693.411%20326,3689%20C326,3684.589%20329.589,3681%20334,3681%20C338.411,3681%20342,3684.589%20342,3689%20C342,3693.411%20338.411,3697%20334,3697%20M334,3679%20C328.477,3679%20324,3683.477%20324,3689%20C324,3694.523%20328.477,3699%20334,3699%20C339.523,3699%20344,3694.523%20344,3689%20C344,3683.477%20339.523,3679%20334,3679'%20id='record-[%23982]'%3e%3c/path%3e%3c/g%3e%3c/g%3e%3c/g%3e%3c/g%3e%3c/svg%3e";const dn={code:".wrap.svelte-czcr5b.svelte-czcr5b{display:flex;flex-grow:1;flex-direction:column;width:var(--size-full);font-weight:var(--body-text-weight);font-size:var(--body-text-size)}.contain.svelte-czcr5b.svelte-czcr5b{display:flex;flex-direction:column}footer.svelte-czcr5b.svelte-czcr5b{display:flex;justify-content:center;margin-top:var(--size-4);color:var(--body-text-color-subdued)}.divider.svelte-czcr5b.svelte-czcr5b{margin-left:var(--size-1);margin-right:var(--size-2)}.show-api.svelte-czcr5b.svelte-czcr5b,.settings.svelte-czcr5b.svelte-czcr5b,.record.svelte-czcr5b.svelte-czcr5b{display:flex;align-items:center}.show-api.svelte-czcr5b.svelte-czcr5b:hover{color:var(--body-text-color)}.show-api.svelte-czcr5b img.svelte-czcr5b{margin-right:var(--size-1);margin-left:var(--size-2);width:var(--size-3)}.settings.svelte-czcr5b img.svelte-czcr5b{margin-right:var(--size-1);margin-left:var(--size-1);width:var(--size-4)}.record.svelte-czcr5b img.svelte-czcr5b{margin-right:var(--size-1);margin-left:var(--size-1);width:var(--size-3)}.built-with.svelte-czcr5b.svelte-czcr5b{display:flex;align-items:center}.built-with.svelte-czcr5b.svelte-czcr5b:hover,.settings.svelte-czcr5b.svelte-czcr5b:hover,.record.svelte-czcr5b.svelte-czcr5b:hover{color:var(--body-text-color)}.built-with.svelte-czcr5b img.svelte-czcr5b{margin-right:var(--size-1);margin-left:var(--size-1);margin-bottom:1px;width:var(--size-4)}.api-docs.svelte-czcr5b.svelte-czcr5b{display:flex;position:fixed;top:0;right:0;z-index:var(--layer-top);background:rgba(0, 0, 0, 0.5);width:var(--size-screen);height:var(--size-screen-h)}.backdrop.svelte-czcr5b.svelte-czcr5b{flex:1 1 0%;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}.api-docs-wrap.svelte-czcr5b.svelte-czcr5b{box-shadow:var(--shadow-drop-lg);background:var(--background-fill-primary);overflow-x:hidden;overflow-y:auto}@media(min-width: 768px){.api-docs-wrap.svelte-czcr5b.svelte-czcr5b{border-top-left-radius:var(--radius-lg);border-bottom-left-radius:var(--radius-lg);width:950px}}@media(min-width: 1536px){.api-docs-wrap.svelte-czcr5b.svelte-czcr5b{width:1150px}}#api-recorder-container.svelte-czcr5b.svelte-czcr5b{position:fixed;left:10px;bottom:10px;z-index:1000}.show-api.svelte-czcr5b.svelte-czcr5b{display:flex;align-items:center}@media(max-width: 640px){.show-api.svelte-czcr5b.svelte-czcr5b,.show-api-divider.svelte-czcr5b.svelte-czcr5b{display:none}}.show-api.svelte-czcr5b.svelte-czcr5b:hover{color:var(--body-text-color)}.hidden.svelte-czcr5b.svelte-czcr5b{display:none}",map:'{"version":3,"file":"Blocks.svelte","sources":["Blocks.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { tick, onMount } from \\"svelte\\";\\nimport { _ } from \\"svelte-i18n\\";\\nimport { Client } from \\"@gradio/client\\";\\nimport { writable } from \\"svelte/store\\";\\nimport { setupi18n } from \\"./i18n\\";\\nimport { Toast } from \\"@gradio/statustracker\\";\\nimport MountComponents from \\"./MountComponents.svelte\\";\\nimport { prefix_css } from \\"./css\\";\\nimport logo from \\"./images/logo.svg\\";\\nimport api_logo from \\"./api_docs/img/api-logo.svg\\";\\nimport settings_logo from \\"./api_docs/img/settings-logo.svg\\";\\nimport record_stop from \\"./api_docs/img/record-stop.svg\\";\\nimport { create_components, AsyncFunction } from \\"./init\\";\\nimport * as screen_recorder from \\"./screen_recorder\\";\\nexport let root;\\nexport let components;\\nexport let layout;\\nexport let dependencies;\\nexport let title = \\"Gradio\\";\\nexport let target;\\nexport let autoscroll;\\nexport let show_api = true;\\nexport let show_footer = true;\\nexport let control_page_title = false;\\nexport let app_mode;\\nexport let theme_mode;\\nexport let app;\\nexport let space_id;\\nexport let version;\\nexport let js;\\nexport let fill_height = false;\\nexport let ready;\\nexport let username;\\nexport let api_prefix = \\"\\";\\nexport let max_file_size = void 0;\\nexport let initial_layout = void 0;\\nexport let css = null;\\nexport let vibe_mode = false;\\nlet broken_connection = false;\\nlet { layout: _layout, targets, update_value, get_data, modify_stream, get_stream_state, set_time_limit, loading_status, scheduled_updates, create_layout, rerender_layout, value_change } = create_components({\\n    initial_layout\\n});\\n$: components, layout, dependencies, root, app, fill_height, target, run();\\n$: {\\n    ready = !!$_layout;\\n}\\nlet old_dependencies = dependencies;\\n$: if (dependencies !== old_dependencies && render_complete && !layout_creating) {\\n    handle_load_triggers();\\n    old_dependencies = dependencies;\\n}\\nlet vibe_editor_width = 350;\\nasync function run() {\\n    await setupi18n(app.config?.i18n_translations || void 0);\\n    layout_creating = true;\\n    await create_layout({\\n        components,\\n        layout,\\n        dependencies,\\n        root: root + api_prefix,\\n        app,\\n        options: {\\n            fill_height\\n        }\\n    });\\n    layout_creating = false;\\n}\\nexport let search_params;\\nlet api_docs_visible = search_params.get(\\"view\\") === \\"api\\" && show_api;\\nlet settings_visible = search_params.get(\\"view\\") === \\"settings\\";\\nlet api_recorder_visible = search_params.get(\\"view\\") === \\"api-recorder\\" && show_api;\\nlet allow_zoom = true;\\nlet allow_video_trim = true;\\nlet ApiDocs = null;\\nlet ApiRecorder = null;\\nlet Settings = null;\\nlet VibeEditor = null;\\nasync function loadApiDocs() {\\n    if (!ApiDocs || !ApiRecorder) {\\n        const api_docs_module = await import(\\"./api_docs/ApiDocs.svelte\\");\\n        const api_recorder_module = await import(\\"./api_docs/ApiRecorder.svelte\\");\\n        if (!ApiDocs)\\n            ApiDocs = api_docs_module.default;\\n        if (!ApiRecorder)\\n            ApiRecorder = api_recorder_module.default;\\n    }\\n}\\nasync function loadApiRecorder() {\\n    if (!ApiRecorder) {\\n        const api_recorder_module = await import(\\"./api_docs/ApiRecorder.svelte\\");\\n        ApiRecorder = api_recorder_module.default;\\n    }\\n}\\nasync function loadSettings() {\\n    if (!Settings) {\\n        const settings_module = await import(\\"./api_docs/Settings.svelte\\");\\n        Settings = settings_module.default;\\n    }\\n}\\nasync function loadVibeEditor() {\\n    if (!VibeEditor) {\\n        const vibe_editor_module = await import(\\"@gradio/vibeeditor\\");\\n        VibeEditor = vibe_editor_module.default;\\n    }\\n}\\nasync function set_api_docs_visible(visible) {\\n    api_recorder_visible = false;\\n    if (visible) {\\n        await loadApiDocs();\\n    }\\n    api_docs_visible = visible;\\n    let params = new URLSearchParams(window.location.search);\\n    if (visible) {\\n        params.set(\\"view\\", \\"api\\");\\n    }\\n    else {\\n        params.delete(\\"view\\");\\n    }\\n    history.replaceState(null, \\"\\", \\"?\\" + params.toString());\\n}\\nasync function set_settings_visible(visible) {\\n    if (visible) {\\n        await loadSettings();\\n    }\\n    let params = new URLSearchParams(window.location.search);\\n    if (visible) {\\n        params.set(\\"view\\", \\"settings\\");\\n    }\\n    else {\\n        params.delete(\\"view\\");\\n    }\\n    history.replaceState(null, \\"\\", \\"?\\" + params.toString());\\n    settings_visible = !settings_visible;\\n}\\nlet api_calls = [];\\nlet layout_creating = false;\\nexport let render_complete = false;\\nasync function handle_update(data, fn_index) {\\n    const dep = dependencies.find((dep2) => dep2.id === fn_index);\\n    const input_type = components.find((comp) => comp.id === dep?.inputs[0])?.type;\\n    if (allow_zoom && dep && input_type !== \\"dataset\\") {\\n        if (dep && dep.inputs && dep.inputs.length > 0 && $is_screen_recording) {\\n            screen_recorder.zoom(true, dep.inputs, 1);\\n        }\\n        if (dep && dep.outputs && dep.outputs.length > 0 && $is_screen_recording) {\\n            screen_recorder.zoom(false, dep.outputs, 2);\\n        }\\n    }\\n    if (!dep) {\\n        return;\\n    }\\n    const outputs = dep.outputs;\\n    const meta_updates = data?.map((value, i) => {\\n        return {\\n            id: outputs[i],\\n            prop: \\"value_is_output\\",\\n            value: true\\n        };\\n    });\\n    update_value(meta_updates);\\n    await tick();\\n    const updates = [];\\n    data?.forEach((value, i) => {\\n        if (typeof value === \\"object\\" && value !== null && value.__type__ === \\"update\\") {\\n            for (const [update_key, update_value2] of Object.entries(value)) {\\n                if (update_key === \\"__type__\\") {\\n                    continue;\\n                }\\n                else {\\n                    updates.push({\\n                        id: outputs[i],\\n                        prop: update_key,\\n                        value: update_value2\\n                    });\\n                }\\n            }\\n        }\\n        else {\\n            updates.push({\\n                id: outputs[i],\\n                prop: \\"value\\",\\n                value\\n            });\\n        }\\n    });\\n    update_value(updates);\\n    updates.forEach((update) => {\\n        const component = components.find((comp) => comp.id === update.id);\\n        if (component && component.type === \\"navbar\\") {\\n            import(\\"./navbar_store\\").then(({ navbar_config }) => {\\n                navbar_config.update((current) => ({\\n                    ...current,\\n                    [update.prop]: update.value\\n                }));\\n            });\\n        }\\n    });\\n    await tick();\\n}\\nlet submit_map = /* @__PURE__ */ new Map();\\nlet messages = [];\\nfunction new_message(title2, message, fn_index, type, duration = 10, visible = true) {\\n    return {\\n        title: title2,\\n        message,\\n        fn_index,\\n        type,\\n        id: ++_error_id,\\n        duration,\\n        visible\\n    };\\n}\\nexport function add_new_message(title2, message, type) {\\n    messages = [new_message(title2, message, -1, type), ...messages];\\n}\\nlet _error_id = -1;\\nconst MESSAGE_QUOTE_RE = /^\'([^]+)\'$/;\\nconst DUPLICATE_MESSAGE = $_(\\"blocks.long_requests_queue\\");\\nconst MOBILE_QUEUE_WARNING = $_(\\"blocks.connection_can_break\\");\\nconst LOST_CONNECTION_MESSAGE = \\"Connection to the server was lost. Attempting reconnection...\\";\\nconst CHANGED_CONNECTION_MESSAGE = \\"Reconnected to server, but the server has changed. You may need to <a href=\'\'>refresh the page</a>.\\";\\nconst RECONNECTION_MESSAGE = \\"Connection re-established.\\";\\nconst SESSION_NOT_FOUND_MESSAGE = \\"Session not found - this is likely because the machine you were connected to has changed. <a href=\'\'>Refresh the page</a> to continue.\\";\\nconst WAITING_FOR_INPUTS_MESSAGE = $_(\\"blocks.waiting_for_inputs\\");\\nconst SHOW_DUPLICATE_MESSAGE_ON_ETA = 15;\\nconst SHOW_MOBILE_QUEUE_WARNING_ON_ETA = 10;\\nlet is_mobile_device = false;\\nlet showed_duplicate_message = false;\\nlet showed_mobile_warning = false;\\nlet inputs_waiting = [];\\nfunction wait_then_trigger_api_call(dep_index, trigger_id = null, event_data = null) {\\n    let _unsub = () => {\\n    };\\n    function unsub() {\\n        _unsub();\\n    }\\n    if ($scheduled_updates) {\\n        _unsub = scheduled_updates.subscribe((updating) => {\\n            if (!updating) {\\n                tick().then(() => {\\n                    trigger_api_call(dep_index, trigger_id, event_data);\\n                    unsub();\\n                });\\n            }\\n        });\\n    }\\n    else {\\n        trigger_api_call(dep_index, trigger_id, event_data);\\n    }\\n}\\nasync function get_component_value_or_event_data(component_id, trigger_id, event_data) {\\n    if (component_id === trigger_id && event_data && event_data.is_value_data === true) {\\n        return event_data.value;\\n    }\\n    return get_data(component_id);\\n}\\nasync function trigger_api_call(dep_index, trigger_id = null, event_data = null) {\\n    const _dep = dependencies.find((dep2) => dep2.id === dep_index);\\n    if (_dep === void 0) {\\n        return;\\n    }\\n    const dep = _dep;\\n    if (inputs_waiting.length > 0) {\\n        for (const input of inputs_waiting) {\\n            if (dep.inputs.includes(input)) {\\n                add_new_message(\\"Warning\\", WAITING_FOR_INPUTS_MESSAGE, \\"warning\\");\\n                return;\\n            }\\n        }\\n    }\\n    const current_status = loading_status.get_status_for_fn(dep_index);\\n    messages = messages.filter(({ fn_index }) => fn_index !== dep_index);\\n    if (current_status === \\"pending\\" || current_status === \\"generating\\") {\\n        dep.pending_request = true;\\n    }\\n    let payload = {\\n        fn_index: dep_index,\\n        data: await Promise.all(dep.inputs.map((id) => get_component_value_or_event_data(id, trigger_id, event_data))),\\n        event_data: dep.collects_event_data ? event_data : null,\\n        trigger_id\\n    };\\n    if (dep.frontend_fn && typeof dep.frontend_fn !== \\"boolean\\") {\\n        dep.frontend_fn(payload.data.concat(await Promise.all(dep.outputs.map((id) => get_data(id))))).then((v) => {\\n            if (dep.backend_fn) {\\n                payload.data = v;\\n                trigger_prediction(dep, payload);\\n            }\\n            else {\\n                handle_update(v, dep_index);\\n            }\\n        });\\n    }\\n    else if (dep.types.cancel && dep.cancels) {\\n        await Promise.all(dep.cancels.map(async (fn_index) => {\\n            const submission = submit_map.get(fn_index);\\n            submission?.cancel();\\n            return submission;\\n        }));\\n    }\\n    else {\\n        if (dep.backend_fn) {\\n            if (dep.js_implementation) {\\n                let js_fn = new AsyncFunction(`let result = await (${dep.js_implementation})(...arguments);\\n\\t\\t\\t\\t\\t\\treturn (!Array.isArray(result)) ? [result] : result;`);\\n                js_fn(...payload.data).then((js_result) => {\\n                    handle_update(js_result, dep_index);\\n                    payload.js_implementation = true;\\n                }).catch((error) => {\\n                    console.error(error);\\n                    payload.js_implementation = false;\\n                });\\n            }\\n            trigger_prediction(dep, payload);\\n        }\\n    }\\n    function trigger_prediction(dep2, payload2) {\\n        if (dep2.trigger_mode === \\"once\\") {\\n            if (!dep2.pending_request)\\n                make_prediction(payload2, dep2.connection == \\"stream\\");\\n        }\\n        else if (dep2.trigger_mode === \\"multiple\\") {\\n            make_prediction(payload2, dep2.connection == \\"stream\\");\\n        }\\n        else if (dep2.trigger_mode === \\"always_last\\") {\\n            if (!dep2.pending_request) {\\n                make_prediction(payload2, dep2.connection == \\"stream\\");\\n            }\\n            else {\\n                dep2.final_event = payload2;\\n            }\\n        }\\n    }\\n    async function reconnect() {\\n        const connection_status = await app.reconnect();\\n        if (connection_status === \\"broken\\") {\\n            setTimeout(reconnect, 1e3);\\n        }\\n        else if (connection_status === \\"changed\\") {\\n            broken_connection = false;\\n            messages = [\\n                new_message(\\"Changed Connection\\", CHANGED_CONNECTION_MESSAGE, -1, \\"info\\", 3, true),\\n                ...messages.map((m) => m.message === LOST_CONNECTION_MESSAGE ? { ...m, visible: false } : m)\\n            ];\\n        }\\n        else if (connection_status === \\"connected\\") {\\n            broken_connection = false;\\n            messages = [\\n                new_message(\\"Reconnected\\", RECONNECTION_MESSAGE, -1, \\"success\\", null, true),\\n                ...messages.map((m) => m.message === LOST_CONNECTION_MESSAGE ? { ...m, visible: false } : m)\\n            ];\\n        }\\n    }\\n    async function make_prediction(payload2, streaming = false) {\\n        if (allow_video_trim) {\\n            screen_recorder.markRemoveSegmentStart();\\n        }\\n        if (api_recorder_visible) {\\n            api_calls = [...api_calls, JSON.parse(JSON.stringify(payload2))];\\n        }\\n        let submission;\\n        app.set_current_payload(payload2);\\n        if (streaming) {\\n            if (!submit_map.has(dep_index)) {\\n                dep.inputs.forEach((id) => modify_stream(id, \\"waiting\\"));\\n            }\\n            else if (submit_map.has(dep_index) && dep.inputs.some((id) => get_stream_state(id) === \\"waiting\\")) {\\n                return;\\n            }\\n            else if (submit_map.has(dep_index) && dep.inputs.some((id) => get_stream_state(id) === \\"open\\")) {\\n                await app.send_ws_message(\\n                // @ts-ignore\\n                `${app.config.root + app.config.api_prefix}/stream/${submit_map.get(dep_index).event_id()}`, { ...payload2, session_hash: app.session_hash });\\n                return;\\n            }\\n        }\\n        try {\\n            submission = app.submit(payload2.fn_index, payload2.data, payload2.event_data, payload2.trigger_id);\\n        }\\n        catch (e) {\\n            const fn_index = 0;\\n            if (app.closed)\\n                return;\\n            messages = [\\n                new_message(\\"Error\\", String(e), fn_index, \\"error\\"),\\n                ...messages\\n            ];\\n            loading_status.update({\\n                status: \\"error\\",\\n                fn_index,\\n                eta: 0,\\n                queue: false,\\n                queue_position: null\\n            });\\n            set_status($loading_status);\\n            return;\\n        }\\n        submit_map.set(dep_index, submission);\\n        for await (const message of submission) {\\n            if (payload2.js_implementation) {\\n                return;\\n            }\\n            if (message.type === \\"data\\") {\\n                handle_data(message);\\n            }\\n            else if (message.type === \\"render\\") {\\n                handle_render(message);\\n            }\\n            else if (message.type === \\"status\\") {\\n                handle_status_update(message);\\n            }\\n            else if (message.type === \\"log\\") {\\n                handle_log(message);\\n            }\\n        }\\n        function handle_data(message) {\\n            const { data, fn_index } = message;\\n            if (dep.pending_request && dep.final_event) {\\n                dep.pending_request = false;\\n                make_prediction(dep.final_event, dep.connection == \\"stream\\");\\n            }\\n            dep.pending_request = false;\\n            handle_update(data, fn_index);\\n            set_status($loading_status);\\n        }\\n        function handle_render(message) {\\n            const { data } = message;\\n            let _components = data.components;\\n            let render_layout = data.layout;\\n            let _dependencies = data.dependencies;\\n            let render_id = data.render_id;\\n            let deps_to_remove = [];\\n            dependencies.forEach((old_dep, i) => {\\n                if (old_dep.rendered_in === dep.render_id) {\\n                    deps_to_remove.push(i);\\n                }\\n            });\\n            deps_to_remove.reverse().forEach((i) => {\\n                dependencies.splice(i, 1);\\n            });\\n            _dependencies.forEach((dep2) => {\\n                dependencies.push(dep2);\\n            });\\n            rerender_layout({\\n                components: _components,\\n                layout: render_layout,\\n                root: root + api_prefix,\\n                dependencies,\\n                render_id\\n            });\\n            _dependencies.forEach((dep2) => {\\n                if (dep2.targets.some((dep3) => dep3[1] === \\"load\\")) {\\n                    wait_then_trigger_api_call(dep2.id);\\n                }\\n            });\\n        }\\n        function handle_log(msg) {\\n            const { title: title2, log, fn_index, level, duration, visible } = msg;\\n            messages = [\\n                new_message(title2, log, fn_index, level, duration, visible),\\n                ...messages\\n            ];\\n        }\\n        function open_stream_events(status, id, dep2) {\\n            if (status.original_msg === \\"process_starts\\" && dep2.connection === \\"stream\\") {\\n                modify_stream(id, \\"open\\");\\n            }\\n        }\\n        function handle_status_update(message) {\\n            if (message.code === \\"validation_error\\") {\\n                const dep2 = dependencies.find((dep3) => dep3.id === message.fn_index);\\n                if (dep2 === void 0 || message.message === void 0 || typeof message.message === \\"string\\") {\\n                    return;\\n                }\\n                const validation_error_data = [];\\n                message.message.forEach((message2, i) => {\\n                    if (message2.is_valid) {\\n                        return;\\n                    }\\n                    validation_error_data.push({\\n                        id: dep2.inputs[i],\\n                        prop: \\"validation_error\\",\\n                        value: message2.message\\n                    });\\n                    validation_error_data.push({\\n                        id: dep2.inputs[i],\\n                        prop: \\"loading_status\\",\\n                        value: { validation_error: message2.message }\\n                    });\\n                });\\n                if (validation_error_data.length > 0) {\\n                    update_value(validation_error_data);\\n                    loading_status.update({\\n                        status: \\"complete\\",\\n                        fn_index: message.fn_index,\\n                        eta: 0,\\n                        queue: false,\\n                        queue_position: null\\n                    });\\n                    set_status($loading_status);\\n                    return;\\n                }\\n            }\\n            if (message.broken && !broken_connection) {\\n                messages = [\\n                    new_message(\\"Broken Connection\\", LOST_CONNECTION_MESSAGE, -1, \\"error\\", null, true),\\n                    ...messages\\n                ];\\n                broken_connection = true;\\n                setTimeout(reconnect, 1e3);\\n            }\\n            if (message.session_not_found) {\\n                messages = [\\n                    new_message(\\"Session Not Found\\", SESSION_NOT_FOUND_MESSAGE, -1, \\"error\\", null, true),\\n                    ...messages\\n                ];\\n            }\\n            const { fn_index, ...status } = message;\\n            if (status.stage === \\"streaming\\" && status.time_limit) {\\n                dep.inputs.forEach((id) => {\\n                    set_time_limit(id, status.time_limit);\\n                });\\n            }\\n            dep.inputs.forEach((id) => {\\n                open_stream_events(message, id, dep);\\n            });\\n            loading_status.update({\\n                ...status,\\n                time_limit: status.time_limit,\\n                status: status.stage,\\n                progress: status.progress_data,\\n                fn_index\\n            });\\n            set_status($loading_status);\\n            if (!showed_duplicate_message && space_id !== null && status.position !== void 0 && status.position >= 2 && status.eta !== void 0 && status.eta > SHOW_DUPLICATE_MESSAGE_ON_ETA) {\\n                showed_duplicate_message = true;\\n                messages = [\\n                    new_message(\\"Warning\\", DUPLICATE_MESSAGE, fn_index, \\"warning\\"),\\n                    ...messages\\n                ];\\n            }\\n            if (!showed_mobile_warning && is_mobile_device && status.eta !== void 0 && status.eta > SHOW_MOBILE_QUEUE_WARNING_ON_ETA) {\\n                showed_mobile_warning = true;\\n                messages = [\\n                    new_message(\\"Warning\\", MOBILE_QUEUE_WARNING, fn_index, \\"warning\\"),\\n                    ...messages\\n                ];\\n            }\\n            if (status.stage === \\"complete\\" || status.stage === \\"generating\\") {\\n                const deps_triggered_by_state = /* @__PURE__ */ new Set();\\n                status.changed_state_ids?.forEach((id) => {\\n                    dependencies.filter((dep2) => dep2.targets.some(([_id, _2]) => _id === id)).forEach((dep2) => {\\n                        deps_triggered_by_state.add(dep2);\\n                    });\\n                });\\n                deps_triggered_by_state.forEach((dep2) => {\\n                    wait_then_trigger_api_call(dep2.id, payload2.trigger_id);\\n                });\\n            }\\n            if (status.stage === \\"complete\\") {\\n                dependencies.forEach(async (dep2) => {\\n                    if (dep2.trigger_after === fn_index && !dep2.trigger_only_on_failure) {\\n                        wait_then_trigger_api_call(dep2.id, payload2.trigger_id);\\n                    }\\n                });\\n                dep.inputs.forEach((id) => {\\n                    modify_stream(id, \\"closed\\");\\n                });\\n                submit_map.delete(dep_index);\\n            }\\n            if (status.stage === \\"error\\" && !broken_connection && !message.session_not_found) {\\n                if (status.message && typeof status.message === \\"string\\") {\\n                    const _message = status.message.replace(MESSAGE_QUOTE_RE, (_2, b) => b);\\n                    const _title = status.title ?? \\"Error\\";\\n                    messages = [\\n                        new_message(_title, _message, fn_index, \\"error\\", status.duration, status.visible),\\n                        ...messages\\n                    ];\\n                }\\n                dependencies.map(async (dep2) => {\\n                    if (dep2.trigger_after === fn_index && (!dep2.trigger_only_on_success || dep2.trigger_only_on_failure)) {\\n                        wait_then_trigger_api_call(dep2.id, payload2.trigger_id);\\n                    }\\n                });\\n            }\\n        }\\n        if (allow_video_trim) {\\n            screen_recorder.markRemoveSegmentEnd();\\n        }\\n    }\\n}\\nfunction trigger_share(title2, description) {\\n    if (space_id === null) {\\n        return;\\n    }\\n    const discussion_url = new URL(`https://huggingface.co/spaces/${space_id}/discussions/new`);\\n    if (title2 !== void 0 && title2.length > 0) {\\n        discussion_url.searchParams.set(\\"title\\", title2);\\n    }\\n    discussion_url.searchParams.set(\\"description\\", description);\\n    window.open(discussion_url.toString(), \\"_blank\\");\\n}\\nfunction handle_error_close(e) {\\n    const _id = e.detail;\\n    messages = messages.filter((m) => m.id !== _id);\\n}\\nconst is_external_url = (link) => !!(link && new URL(link, location.href).origin !== location.origin);\\nasync function handle_mount() {\\n    if (js) {\\n        let blocks_frontend_fn = new AsyncFunction(`let result = await (${js})();\\n\\t\\t\\t\\t\\treturn (!Array.isArray(result)) ? [result] : result;`);\\n        await blocks_frontend_fn();\\n    }\\n    await tick();\\n    var a = target.getElementsByTagName(\\"a\\");\\n    for (var i = 0; i < a.length; i++) {\\n        const _target = a[i].getAttribute(\\"target\\");\\n        const _link = a[i].getAttribute(\\"href\\");\\n        if (is_external_url(_link) && _target !== \\"_blank\\")\\n            a[i].setAttribute(\\"target\\", \\"_blank\\");\\n    }\\n    handle_load_triggers();\\n    if (!target || render_complete)\\n        return;\\n    target.addEventListener(\\"prop_change\\", (e) => {\\n        if (!isCustomEvent(e))\\n            throw new Error(\\"not a custom event\\");\\n        const { id, prop, value } = e.detail;\\n        if (prop === \\"value\\") {\\n            update_value([\\n                {\\n                    id,\\n                    prop: \\"loading_status\\",\\n                    value: { validation_error: void 0 }\\n                }\\n            ]);\\n        }\\n        update_value([{ id, prop, value }]);\\n        if (prop === \\"input_ready\\" && value === false) {\\n            inputs_waiting.push(id);\\n        }\\n        if (prop === \\"input_ready\\" && value === true) {\\n            inputs_waiting = inputs_waiting.filter((item) => item !== id);\\n        }\\n    });\\n    target.addEventListener(\\"gradio\\", (e) => {\\n        if (!isCustomEvent(e))\\n            throw new Error(\\"not a custom event\\");\\n        const { id, event, data } = e.detail;\\n        if (event === \\"share\\") {\\n            const { title: title2, description } = data;\\n            trigger_share(title2, description);\\n        }\\n        else if (event === \\"error\\") {\\n            messages = [new_message(\\"Error\\", data, -1, event), ...messages];\\n        }\\n        else if (event === \\"warning\\") {\\n            messages = [new_message(\\"Warning\\", data, -1, event), ...messages];\\n        }\\n        else if (event === \\"info\\") {\\n            messages = [new_message(\\"Info\\", data, -1, event), ...messages];\\n        }\\n        else if (event == \\"clear_status\\") {\\n            update_status(id, \\"complete\\", data);\\n        }\\n        else if (event == \\"close_stream\\") {\\n            const deps = $targets[id]?.[data];\\n            deps?.forEach((dep_id) => {\\n                if (submit_map.has(dep_id)) {\\n                    const url = `${app.config.root + app.config.api_prefix}/stream/${submit_map.get(dep_id).event_id()}`;\\n                    app.post_data(`${url}/close`, {});\\n                    app.close_ws(url);\\n                }\\n            });\\n        }\\n        else {\\n            const deps = $targets[id]?.[event];\\n            deps?.forEach((dep_id) => {\\n                requestAnimationFrame(() => {\\n                    wait_then_trigger_api_call(dep_id, id, data);\\n                });\\n            });\\n        }\\n    });\\n    render_complete = true;\\n}\\nvalue_change((id, value) => {\\n    const deps = $targets[id]?.[\\"change\\"];\\n    deps?.forEach((dep_id) => {\\n        requestAnimationFrame(() => {\\n            wait_then_trigger_api_call(dep_id, id, value);\\n        });\\n    });\\n});\\nconst handle_load_triggers = () => {\\n    dependencies.forEach((dep) => {\\n        if (dep.targets.some((dep2) => dep2[1] === \\"load\\")) {\\n            wait_then_trigger_api_call(dep.id);\\n        }\\n    });\\n};\\n$: set_status($loading_status);\\nfunction update_status(id, status, data) {\\n    data.status = status;\\n    update_value([\\n        {\\n            id,\\n            prop: \\"loading_status\\",\\n            value: data\\n        }\\n    ]);\\n}\\nfunction set_status(statuses) {\\n    let updates = [];\\n    Object.entries(statuses).forEach(([id, loading_status2]) => {\\n        if (app.closed && loading_status2.status === \\"error\\") {\\n            return;\\n        }\\n        let dependency = dependencies.find((dep) => dep.id == loading_status2.fn_index);\\n        if (dependency === void 0) {\\n            return;\\n        }\\n        loading_status2.scroll_to_output = dependency.scroll_to_output;\\n        loading_status2.show_progress = dependency.show_progress;\\n        updates.push({\\n            id: parseInt(id),\\n            prop: \\"loading_status\\",\\n            value: loading_status2\\n        });\\n    });\\n    const inputs_to_update = loading_status.get_inputs_to_update();\\n    const additional_updates = Array.from(inputs_to_update).map(([id, pending_status]) => {\\n        return {\\n            id,\\n            prop: \\"pending\\",\\n            value: pending_status === \\"pending\\"\\n        };\\n    });\\n    update_value([...updates, ...additional_updates]);\\n}\\nfunction isCustomEvent(event) {\\n    return \\"detail\\" in event;\\n}\\nlet is_screen_recording = writable(false);\\nonMount(() => {\\n    is_mobile_device = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);\\n    screen_recorder.initialize(root, (title2, message, type) => {\\n        add_new_message(title2, message, type);\\n    }, (isRecording) => {\\n        $is_screen_recording = isRecording;\\n    });\\n    const handleVibeEditorResize = (event) => {\\n        vibe_editor_width = event.detail.width;\\n    };\\n    window.addEventListener(\\"vibeEditorResize\\", handleVibeEditorResize);\\n    if (api_docs_visible) {\\n        loadApiDocs();\\n    }\\n    if (api_recorder_visible) {\\n        loadApiRecorder();\\n    }\\n    if (settings_visible) {\\n        loadSettings();\\n    }\\n    if (vibe_mode) {\\n        loadVibeEditor();\\n    }\\n});\\nfunction screen_recording() {\\n    if ($is_screen_recording) {\\n        screen_recorder.stopRecording();\\n    }\\n    else {\\n        screen_recorder.startRecording();\\n    }\\n}\\nlet footer_height = 0;\\nlet root_container;\\nfunction get_root_node(container) {\\n    if (!container)\\n        return null;\\n    return container.children[container.children.length - 1];\\n}\\nfunction handle_resize() {\\n    if (\\"parentIFrame\\" in window) {\\n        const box = root_container.children[0].getBoundingClientRect();\\n        if (!box)\\n            return;\\n        window.parentIFrame?.size(box.bottom + footer_height + 32);\\n    }\\n}\\nonMount(() => {\\n    if (\\"parentIFrame\\" in window) {\\n        window.parentIFrame?.autoResize(false);\\n    }\\n    const mut = new MutationObserver(handle_resize);\\n    const res = new ResizeObserver(handle_resize);\\n    mut.observe(root_container, {\\n        childList: true,\\n        subtree: true,\\n        attributes: true\\n    });\\n    res.observe(root_container);\\n    return () => {\\n        mut.disconnect();\\n        res.disconnect();\\n    };\\n});\\n<\/script>\\n\\n<svelte:head>\\n\\t{#if control_page_title}\\n\\t\\t<title>{title}</title>\\n\\t{/if}\\n\\t{#if css}\\n\\t\\t{@html `\\\\<style\\\\>${prefix_css(css, version)}</style>`}\\n\\t{/if}\\n</svelte:head>\\n\\n<div class=\\"wrap\\" style:min-height={app_mode ? \\"100%\\" : \\"auto\\"}>\\n\\t<div\\n\\t\\tclass=\\"contain\\"\\n\\t\\tstyle:flex-grow={app_mode ? \\"1\\" : \\"auto\\"}\\n\\t\\tbind:this={root_container}\\n\\t\\tstyle:margin-right={vibe_mode ? `${vibe_editor_width}px` : \\"0\\"}\\n\\t>\\n\\t\\t{#if $_layout && app.config}\\n\\t\\t\\t<MountComponents\\n\\t\\t\\t\\trootNode={$_layout}\\n\\t\\t\\t\\t{root}\\n\\t\\t\\t\\t{target}\\n\\t\\t\\t\\t{theme_mode}\\n\\t\\t\\t\\ton:mount={handle_mount}\\n\\t\\t\\t\\t{version}\\n\\t\\t\\t\\t{autoscroll}\\n\\t\\t\\t\\t{max_file_size}\\n\\t\\t\\t\\tclient={app}\\n\\t\\t\\t/>\\n\\t\\t{/if}\\n\\t</div>\\n\\n\\t{#if show_footer}\\n\\t\\t<footer bind:clientHeight={footer_height}>\\n\\t\\t\\t{#if show_api}\\n\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\t\\t\\tset_api_docs_visible(!api_docs_visible);\\n\\t\\t\\t\\t\\t}}\\n\\t\\t\\t\\t\\ton:mouseenter={() => {\\n\\t\\t\\t\\t\\t\\tloadApiDocs();\\n\\t\\t\\t\\t\\t\\tloadApiRecorder();\\n\\t\\t\\t\\t\\t}}\\n\\t\\t\\t\\t\\tclass=\\"show-api\\"\\n\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t{#if app.config?.mcp_server}\\n\\t\\t\\t\\t\\t\\t{$_(\\"errors.use_via_api_or_mcp\\")}\\n\\t\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t\\t{$_(\\"errors.use_via_api\\")}\\n\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t<img src={api_logo} alt={$_(\\"common.logo\\")} />\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t<div class=\\"divider show-api-divider\\">·</div>\\n\\t\\t\\t{/if}\\n\\t\\t\\t<a\\n\\t\\t\\t\\thref=\\"https://gradio.app\\"\\n\\t\\t\\t\\tclass=\\"built-with\\"\\n\\t\\t\\t\\ttarget=\\"_blank\\"\\n\\t\\t\\t\\trel=\\"noreferrer\\"\\n\\t\\t\\t>\\n\\t\\t\\t\\t{$_(\\"common.built_with_gradio\\")}\\n\\t\\t\\t\\t<img src={logo} alt={$_(\\"common.logo\\")} />\\n\\t\\t\\t</a>\\n\\t\\t\\t<div class=\\"divider\\" class:hidden={!$is_screen_recording}>·</div>\\n\\t\\t\\t<button\\n\\t\\t\\t\\tclass:hidden={!$is_screen_recording}\\n\\t\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\t\\tscreen_recording();\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\tclass=\\"record\\"\\n\\t\\t\\t>\\n\\t\\t\\t\\t{$_(\\"common.stop_recording\\")}\\n\\t\\t\\t\\t<img src={record_stop} alt={$_(\\"common.stop_recording\\")} />\\n\\t\\t\\t</button>\\n\\t\\t\\t<div class=\\"divider\\">·</div>\\n\\t\\t\\t<button\\n\\t\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\t\\tset_settings_visible(!settings_visible);\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\ton:mouseenter={() => {\\n\\t\\t\\t\\t\\tloadSettings();\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\tclass=\\"settings\\"\\n\\t\\t\\t>\\n\\t\\t\\t\\t{$_(\\"common.settings\\")}\\n\\t\\t\\t\\t<img src={settings_logo} alt={$_(\\"common.settings\\")} />\\n\\t\\t\\t</button>\\n\\t\\t</footer>\\n\\t{/if}\\n</div>\\n\\n{#if api_recorder_visible && ApiRecorder}\\n\\t<!-- TODO: fix -->\\n\\t<!-- svelte-ignore a11y-click-events-have-key-events-->\\n\\t<!-- svelte-ignore a11y-no-static-element-interactions-->\\n\\t<div\\n\\t\\tid=\\"api-recorder-container\\"\\n\\t\\ton:click={() => {\\n\\t\\t\\tset_api_docs_visible(true);\\n\\t\\t\\tapi_recorder_visible = false;\\n\\t\\t}}\\n\\t>\\n\\t\\t<svelte:component this={ApiRecorder} {api_calls} {dependencies} />\\n\\t</div>\\n{/if}\\n\\n{#if api_docs_visible && $_layout && ApiDocs}\\n\\t<div class=\\"api-docs\\">\\n\\t\\t<!-- TODO: fix -->\\n\\t\\t<!-- svelte-ignore a11y-click-events-have-key-events-->\\n\\t\\t<!-- svelte-ignore a11y-no-static-element-interactions-->\\n\\t\\t<div\\n\\t\\t\\tclass=\\"backdrop\\"\\n\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\tset_api_docs_visible(false);\\n\\t\\t\\t}}\\n\\t\\t/>\\n\\t\\t<div class=\\"api-docs-wrap\\">\\n\\t\\t\\t<svelte:component\\n\\t\\t\\t\\tthis={ApiDocs}\\n\\t\\t\\t\\troot_node={$_layout}\\n\\t\\t\\t\\ton:close={(event) => {\\n\\t\\t\\t\\t\\tset_api_docs_visible(false);\\n\\t\\t\\t\\t\\tapi_calls = [];\\n\\t\\t\\t\\t\\tapi_recorder_visible = api_recorder_visible =\\n\\t\\t\\t\\t\\t\\tevent.detail?.api_recorder_visible;\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\t{dependencies}\\n\\t\\t\\t\\t{root}\\n\\t\\t\\t\\t{app}\\n\\t\\t\\t\\t{space_id}\\n\\t\\t\\t\\t{api_calls}\\n\\t\\t\\t\\t{username}\\n\\t\\t\\t/>\\n\\t\\t</div>\\n\\t</div>\\n{/if}\\n\\n{#if settings_visible && $_layout && app.config && Settings}\\n\\t<div class=\\"api-docs\\">\\n\\t\\t<!-- TODO: fix -->\\n\\t\\t<!-- svelte-ignore a11y-click-events-have-key-events-->\\n\\t\\t<!-- svelte-ignore a11y-no-static-element-interactions-->\\n\\t\\t<div\\n\\t\\t\\tclass=\\"backdrop\\"\\n\\t\\t\\ton:click={() => {\\n\\t\\t\\t\\tset_settings_visible(false);\\n\\t\\t\\t}}\\n\\t\\t/>\\n\\t\\t<div class=\\"api-docs-wrap\\">\\n\\t\\t\\t<svelte:component\\n\\t\\t\\t\\tthis={Settings}\\n\\t\\t\\t\\tbind:allow_zoom\\n\\t\\t\\t\\tbind:allow_video_trim\\n\\t\\t\\t\\ton:close={() => {\\n\\t\\t\\t\\t\\tset_settings_visible(false);\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\ton:start_recording={() => {\\n\\t\\t\\t\\t\\tscreen_recording();\\n\\t\\t\\t\\t}}\\n\\t\\t\\t\\tpwa_enabled={app.config.pwa}\\n\\t\\t\\t\\t{root}\\n\\t\\t\\t\\t{space_id}\\n\\t\\t\\t/>\\n\\t\\t</div>\\n\\t</div>\\n{/if}\\n\\n{#if messages}\\n\\t<Toast {messages} on:close={handle_error_close} />\\n{/if}\\n\\n{#if vibe_mode && VibeEditor}\\n\\t<svelte:component this={VibeEditor} {app} {root} />\\n{/if}\\n\\n<style>\\n\\t.wrap {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-grow: 1;\\n\\t\\tflex-direction: column;\\n\\t\\twidth: var(--size-full);\\n\\t\\tfont-weight: var(--body-text-weight);\\n\\t\\tfont-size: var(--body-text-size);\\n\\t}\\n\\n\\t.contain {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t}\\n\\n\\tfooter {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: center;\\n\\t\\tmargin-top: var(--size-4);\\n\\t\\tcolor: var(--body-text-color-subdued);\\n\\t}\\n\\t.divider {\\n\\t\\tmargin-left: var(--size-1);\\n\\t\\tmargin-right: var(--size-2);\\n\\t}\\n\\n\\t.show-api,\\n\\t.settings,\\n\\t.record {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t}\\n\\t.show-api:hover {\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.show-api img {\\n\\t\\tmargin-right: var(--size-1);\\n\\t\\tmargin-left: var(--size-2);\\n\\t\\twidth: var(--size-3);\\n\\t}\\n\\n\\t.settings img {\\n\\t\\tmargin-right: var(--size-1);\\n\\t\\tmargin-left: var(--size-1);\\n\\t\\twidth: var(--size-4);\\n\\t}\\n\\n\\t.record img {\\n\\t\\tmargin-right: var(--size-1);\\n\\t\\tmargin-left: var(--size-1);\\n\\t\\twidth: var(--size-3);\\n\\t}\\n\\n\\t.built-with {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t}\\n\\n\\t.built-with:hover,\\n\\t.settings:hover,\\n\\t.record:hover {\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.built-with img {\\n\\t\\tmargin-right: var(--size-1);\\n\\t\\tmargin-left: var(--size-1);\\n\\t\\tmargin-bottom: 1px;\\n\\t\\twidth: var(--size-4);\\n\\t}\\n\\n\\t.api-docs {\\n\\t\\tdisplay: flex;\\n\\t\\tposition: fixed;\\n\\t\\ttop: 0;\\n\\t\\tright: 0;\\n\\t\\tz-index: var(--layer-top);\\n\\t\\tbackground: rgba(0, 0, 0, 0.5);\\n\\t\\twidth: var(--size-screen);\\n\\t\\theight: var(--size-screen-h);\\n\\t}\\n\\n\\t.backdrop {\\n\\t\\tflex: 1 1 0%;\\n\\t\\t-webkit-backdrop-filter: blur(4px);\\n\\t\\tbackdrop-filter: blur(4px);\\n\\t}\\n\\n\\t.api-docs-wrap {\\n\\t\\tbox-shadow: var(--shadow-drop-lg);\\n\\t\\tbackground: var(--background-fill-primary);\\n\\t\\toverflow-x: hidden;\\n\\t\\toverflow-y: auto;\\n\\t}\\n\\n\\t@media (min-width: 768px) {\\n\\t\\t.api-docs-wrap {\\n\\t\\t\\tborder-top-left-radius: var(--radius-lg);\\n\\t\\t\\tborder-bottom-left-radius: var(--radius-lg);\\n\\t\\t\\twidth: 950px;\\n\\t\\t}\\n\\t}\\n\\n\\t@media (min-width: 1536px) {\\n\\t\\t.api-docs-wrap {\\n\\t\\t\\twidth: 1150px;\\n\\t\\t}\\n\\t}\\n\\n\\t#api-recorder-container {\\n\\t\\tposition: fixed;\\n\\t\\tleft: 10px;\\n\\t\\tbottom: 10px;\\n\\t\\tz-index: 1000;\\n\\t}\\n\\n\\t.show-api {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t}\\n\\n\\t@media (max-width: 640px) {\\n\\t\\t.show-api,\\n\\t\\t.show-api-divider {\\n\\t\\t\\tdisplay: none;\\n\\t\\t}\\n\\t}\\n\\n\\t.show-api:hover {\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.hidden {\\n\\t\\tdisplay: none;\\n\\t}</style>\\n"],"names":[],"mappings":"AAy9BC,iCAAM,CACL,OAAO,CAAE,IAAI,CACb,SAAS,CAAE,CAAC,CACZ,cAAc,CAAE,MAAM,CACtB,KAAK,CAAE,IAAI,WAAW,CAAC,CACvB,WAAW,CAAE,IAAI,kBAAkB,CAAC,CACpC,SAAS,CAAE,IAAI,gBAAgB,CAChC,CAEA,oCAAS,CACR,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MACjB,CAEA,kCAAO,CACN,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,MAAM,CACvB,UAAU,CAAE,IAAI,QAAQ,CAAC,CACzB,KAAK,CAAE,IAAI,yBAAyB,CACrC,CACA,oCAAS,CACR,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,YAAY,CAAE,IAAI,QAAQ,CAC3B,CAEA,qCAAS,CACT,qCAAS,CACT,mCAAQ,CACP,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MACd,CACA,qCAAS,MAAO,CACf,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,uBAAS,CAAC,iBAAI,CACb,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,KAAK,CAAE,IAAI,QAAQ,CACpB,CAEA,uBAAS,CAAC,iBAAI,CACb,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,KAAK,CAAE,IAAI,QAAQ,CACpB,CAEA,qBAAO,CAAC,iBAAI,CACX,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,KAAK,CAAE,IAAI,QAAQ,CACpB,CAEA,uCAAY,CACX,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MACd,CAEA,uCAAW,MAAM,CACjB,qCAAS,MAAM,CACf,mCAAO,MAAO,CACb,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,yBAAW,CAAC,iBAAI,CACf,YAAY,CAAE,IAAI,QAAQ,CAAC,CAC3B,WAAW,CAAE,IAAI,QAAQ,CAAC,CAC1B,aAAa,CAAE,GAAG,CAClB,KAAK,CAAE,IAAI,QAAQ,CACpB,CAEA,qCAAU,CACT,OAAO,CAAE,IAAI,CACb,QAAQ,CAAE,KAAK,CACf,GAAG,CAAE,CAAC,CACN,KAAK,CAAE,CAAC,CACR,OAAO,CAAE,IAAI,WAAW,CAAC,CACzB,UAAU,CAAE,KAAK,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CAC9B,KAAK,CAAE,IAAI,aAAa,CAAC,CACzB,MAAM,CAAE,IAAI,eAAe,CAC5B,CAEA,qCAAU,CACT,IAAI,CAAE,CAAC,CAAC,CAAC,CAAC,EAAE,CACZ,uBAAuB,CAAE,KAAK,GAAG,CAAC,CAClC,eAAe,CAAE,KAAK,GAAG,CAC1B,CAEA,0CAAe,CACd,UAAU,CAAE,IAAI,gBAAgB,CAAC,CACjC,UAAU,CAAE,IAAI,yBAAyB,CAAC,CAC1C,UAAU,CAAE,MAAM,CAClB,UAAU,CAAE,IACb,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,0CAAe,CACd,sBAAsB,CAAE,IAAI,WAAW,CAAC,CACxC,yBAAyB,CAAE,IAAI,WAAW,CAAC,CAC3C,KAAK,CAAE,KACR,CACD,CAEA,MAAO,YAAY,MAAM,CAAE,CAC1B,0CAAe,CACd,KAAK,CAAE,MACR,CACD,CAEA,mDAAwB,CACvB,QAAQ,CAAE,KAAK,CACf,IAAI,CAAE,IAAI,CACV,MAAM,CAAE,IAAI,CACZ,OAAO,CAAE,IACV,CAEA,qCAAU,CACT,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MACd,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,qCAAS,CACT,6CAAkB,CACjB,OAAO,CAAE,IACV,CACD,CAEA,qCAAS,MAAO,CACf,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,mCAAQ,CACP,OAAO,CAAE,IACV"}'},cn=/^'([^]+)'$/,We="Connection to the server was lost. Attempting reconnection...",_n="Reconnected to server, but the server has changed. You may need to <a href=''>refresh the page</a>.",pn="Connection re-established.",un="Session not found - this is likely because the machine you were connected to has changed. <a href=''>Refresh the page</a> to continue.",An=15,fn=create_ssr_component((s,e,t,J)=>{let m,_,p,i,h,w,v,x,d,S,b,N;S=subscribe(Pt$2,n=>d=n);let{root:R}=e,{components:Q}=e,{layout:H}=e,{dependencies:g}=e,{title:f="Gradio"}=e,{target:G}=e,{autoscroll:X}=e,{show_api:B=!0}=e,{show_footer:j=!0}=e,{control_page_title:$=!1}=e,{app_mode:oe}=e,{theme_mode:ee}=e,{app:y}=e,{space_id:te}=e,{version:F}=e,{js:me}=e,{fill_height:re=!1}=e,{ready:xe}=e,{username:ze}=e,{api_prefix:fe=""}=e,{max_file_size:Ie=void 0}=e,{initial_layout:Se=void 0}=e,{css:ve=null}=e,{vibe_mode:le=!1}=e,de=!1,{layout:_t,targets:pt,update_value:ge,get_data:Qe,modify_stream:Be,get_stream_state:Ke,set_time_limit:ut,loading_status:ae,scheduled_updates:je,create_layout:At,rerender_layout:mt,value_change:ft}=ua$1({initial_layout:Se});N=subscribe(_t,n=>b=n),w=subscribe(pt,n=>h=n),i=subscribe(ae,n=>p=n),x=subscribe(je,n=>v=n);let De=g,qe=350;async function vt(){await aa$1(y.config?.i18n_translations||void 0),Me=!0,await At({components:Q,layout:H,dependencies:g,root:R+fe,app:y,options:{fill_height:re}}),Me=!1;}let{search_params:ce}=e,Fe=ce.get("view")==="api"&&B,Pe=ce.get("view")==="settings",ke=ce.get("view")==="api-recorder"&&B,Oe=!0,Ye=!0,_e=null,ne=null,Ce=null,he=null;let we=[],Me=!1,{render_complete:Ne=!1}=e;async function Te(n,u){const c=g.find(z=>z.id===u),U=Q.find(z=>z.id===c?.inputs[0])?.type;if(Oe&&c&&U!=="dataset"&&(c&&c.inputs&&c.inputs.length>0&&m&&(c.inputs,void 0),c&&c.outputs&&c.outputs.length>0&&m&&(c.outputs,void 0)),!c)return;const a=c.outputs,O=n?.map((z,q)=>({id:a[q],prop:"value_is_output",value:!0}));ge(O),await tick();const M=[];n?.forEach((z,q)=>{if(typeof z=="object"&&z!==null&&z.__type__==="update")for(const[W,o]of Object.entries(z))W!=="__type__"&&M.push({id:a[q],prop:W,value:o});else M.push({id:a[q],prop:"value",value:z});}),ge(M),M.forEach(z=>{const q=Q.find(W=>W.id===z.id);q&&q.type==="navbar"&&Promise.resolve().then(function () { return client; }).then(W=>W.z).then(({navbar_config:W})=>{W.update(o=>({...o,[z.prop]:z.value}));});}),await tick();}let ie=new Map,C=[];function D(n,u,c,U,a=10,O=!0){return {title:n,message:u,fn_index:c,type:U,id:++bt,duration:a,visible:O}}function Re(n,u,c){C=[D(n,u,-1,c),...C];}let bt=-1;const yt$1=d("blocks.long_requests_queue");d("blocks.connection_can_break");const xt=d("blocks.waiting_for_inputs");let He=!1,Je=[];function se(n,u=null,c=null){let U=()=>{};function a(){U();}v?U=je.subscribe(O=>{O||tick().then(()=>{Xe(n,u,c),a();});}):Xe(n,u,c);}async function zt(n,u,c){return n===u&&c&&c.is_value_data===!0?c.value:Qe(n)}async function Xe(n,u=null,c=null){const U=g.find(o=>o.id===n);if(U===void 0)return;const a=U;if(Je.length>0){for(const o of Je)if(a.inputs.includes(o)){Re("Warning",xt,"warning");return}}const O=ae.get_status_for_fn(n);C=C.filter(({fn_index:o})=>o!==n),(O==="pending"||O==="generating")&&(a.pending_request=!0);let M={fn_index:n,data:await Promise.all(a.inputs.map(o=>zt(o,u,c))),event_data:a.collects_event_data?c:null,trigger_id:u};a.frontend_fn&&typeof a.frontend_fn!="boolean"?a.frontend_fn(M.data.concat(await Promise.all(a.outputs.map(o=>Qe(o))))).then(o=>{a.backend_fn?(M.data=o,z(a,M)):Te(o,n);}):a.types.cancel&&a.cancels?await Promise.all(a.cancels.map(async o=>{const E=ie.get(o);return E?.cancel(),E})):a.backend_fn&&(a.js_implementation&&new Do(`let result = await (${a.js_implementation})(...arguments);
						return (!Array.isArray(result)) ? [result] : result;`)(...M.data).then(E=>{Te(E,n),M.js_implementation=!0;}).catch(E=>{console.error(E),M.js_implementation=!1;}),z(a,M));function z(o,E){o.trigger_mode==="once"?o.pending_request||W(E,o.connection=="stream"):o.trigger_mode==="multiple"?W(E,o.connection=="stream"):o.trigger_mode==="always_last"&&(o.pending_request?o.final_event=E:W(E,o.connection=="stream"));}async function q(){const o=await y.reconnect();o==="broken"?setTimeout(q,1e3):o==="changed"?(de=!1,C=[D("Changed Connection",_n,-1,"info",3,!0),...C.map(E=>E.message===We?{...E,visible:!1}:E)]):o==="connected"&&(de=!1,C=[D("Reconnected",pn,-1,"success",null,!0),...C.map(E=>E.message===We?{...E,visible:!1}:E)]);}async function W(o,E=!1){ke&&(we=[...we,JSON.parse(JSON.stringify(o))]);let Ge;if(y.set_current_payload(o),E)if(!ie.has(n))a.inputs.forEach(r=>Be(r,"waiting"));else {if(ie.has(n)&&a.inputs.some(r=>Ke(r)==="waiting"))return;if(ie.has(n)&&a.inputs.some(r=>Ke(r)==="open")){await y.send_ws_message(`${y.config.root+y.config.api_prefix}/stream/${ie.get(n).event_id()}`,{...o,session_hash:y.session_hash});return}}try{Ge=y.submit(o.fn_index,o.data,o.event_data,o.trigger_id);}catch(r){if(y.closed)return;C=[D("Error",String(r),0,"error"),...C],ae.update({status:"error",fn_index:0,eta:0,queue:!1,queue_position:null}),pe(p);return}ie.set(n,Ge);for await(const r of Ge){if(o.js_implementation)return;r.type==="data"?Ot(r):r.type==="render"?Mt(r):r.type==="status"?Rt(r):r.type==="log"&&Nt(r);}function Ot(r){const{data:I,fn_index:l}=r;a.pending_request&&a.final_event&&(a.pending_request=!1,W(a.final_event,a.connection=="stream")),a.pending_request=!1,Te(I,l),pe(p);}function Mt(r){const{data:I}=r;let l=I.components,A=I.layout,T=I.dependencies,L=I.render_id,K=[];g.forEach((P,Le)=>{P.rendered_in===a.render_id&&K.push(Le);}),K.reverse().forEach(P=>{g.splice(P,1);}),T.forEach(P=>{g.push(P);}),mt({components:l,layout:A,root:R+fe,dependencies:g,render_id:L}),T.forEach(P=>{P.targets.some(Le=>Le[1]==="load")&&se(P.id);});}function Nt(r){const{title:I,log:l,fn_index:A,level:T,duration:L,visible:K}=r;C=[D(I,l,A,T,L,K),...C];}function Tt(r,I,l){r.original_msg==="process_starts"&&l.connection==="stream"&&Be(I,"open");}function Rt(r){if(r.code==="validation_error"){const A=g.find(L=>L.id===r.fn_index);if(A===void 0||r.message===void 0||typeof r.message=="string")return;const T=[];if(r.message.forEach((L,K)=>{L.is_valid||(T.push({id:A.inputs[K],prop:"validation_error",value:L.message}),T.push({id:A.inputs[K],prop:"loading_status",value:{validation_error:L.message}}));}),T.length>0){ge(T),ae.update({status:"complete",fn_index:r.fn_index,eta:0,queue:!1,queue_position:null}),pe(p);return}}r.broken&&!de&&(C=[D("Broken Connection",We,-1,"error",null,!0),...C],de=!0,setTimeout(q,1e3)),r.session_not_found&&(C=[D("Session Not Found",un,-1,"error",null,!0),...C]);const{fn_index:I,...l}=r;if(l.stage==="streaming"&&l.time_limit&&a.inputs.forEach(A=>{ut(A,l.time_limit);}),a.inputs.forEach(A=>{Tt(r,A,a);}),ae.update({...l,time_limit:l.time_limit,status:l.stage,progress:l.progress_data,fn_index:I}),pe(p),!He&&te!==null&&l.position!==void 0&&l.position>=2&&l.eta!==void 0&&l.eta>An&&(He=!0,C=[D("Warning",yt$1,I,"warning"),...C]),l.stage==="complete"||l.stage==="generating"){const A=new Set;l.changed_state_ids?.forEach(T=>{g.filter(L=>L.targets.some(([K,P])=>K===T)).forEach(L=>{A.add(L);});}),A.forEach(T=>{se(T.id,o.trigger_id);});}if(l.stage==="complete"&&(g.forEach(async A=>{A.trigger_after===I&&!A.trigger_only_on_failure&&se(A.id,o.trigger_id);}),a.inputs.forEach(A=>{Be(A,"closed");}),ie.delete(n)),l.stage==="error"&&!de&&!r.session_not_found){if(l.message&&typeof l.message=="string"){const A=l.message.replace(cn,(L,K)=>K),T=l.title??"Error";C=[D(T,A,I,"error",l.duration,l.visible),...C];}g.map(async A=>{A.trigger_after===I&&(!A.trigger_only_on_success||A.trigger_only_on_failure)&&se(A.id,o.trigger_id);});}}}}ft((n,u)=>{h[n]?.change?.forEach(U=>{requestAnimationFrame(()=>{se(U,n,u);});});});const It=()=>{g.forEach(n=>{n.targets.some(u=>u[1]==="load")&&se(n.id);});};function pe(n){let u=[];Object.entries(n).forEach(([a,O])=>{if(y.closed&&O.status==="error")return;let M=g.find(z=>z.id==O.fn_index);M!==void 0&&(O.scroll_to_output=M.scroll_to_output,O.show_progress=M.show_progress,u.push({id:parseInt(a),prop:"loading_status",value:O}));});const c=ae.get_inputs_to_update(),U=Array.from(c).map(([a,O])=>({id:a,prop:"pending",value:O==="pending"}));ge([...u,...U]);}let St=writable(!1);_=subscribe(St,n=>m=n);let be;e.root===void 0&&t.root&&R!==void 0&&t.root(R),e.components===void 0&&t.components&&Q!==void 0&&t.components(Q),e.layout===void 0&&t.layout&&H!==void 0&&t.layout(H),e.dependencies===void 0&&t.dependencies&&g!==void 0&&t.dependencies(g),e.title===void 0&&t.title&&f!==void 0&&t.title(f),e.target===void 0&&t.target&&G!==void 0&&t.target(G),e.autoscroll===void 0&&t.autoscroll&&X!==void 0&&t.autoscroll(X),e.show_api===void 0&&t.show_api&&B!==void 0&&t.show_api(B),e.show_footer===void 0&&t.show_footer&&j!==void 0&&t.show_footer(j),e.control_page_title===void 0&&t.control_page_title&&$!==void 0&&t.control_page_title($),e.app_mode===void 0&&t.app_mode&&oe!==void 0&&t.app_mode(oe),e.theme_mode===void 0&&t.theme_mode&&ee!==void 0&&t.theme_mode(ee),e.app===void 0&&t.app&&y!==void 0&&t.app(y),e.space_id===void 0&&t.space_id&&te!==void 0&&t.space_id(te),e.version===void 0&&t.version&&F!==void 0&&t.version(F),e.js===void 0&&t.js&&me!==void 0&&t.js(me),e.fill_height===void 0&&t.fill_height&&re!==void 0&&t.fill_height(re),e.ready===void 0&&t.ready&&xe!==void 0&&t.ready(xe),e.username===void 0&&t.username&&ze!==void 0&&t.username(ze),e.api_prefix===void 0&&t.api_prefix&&fe!==void 0&&t.api_prefix(fe),e.max_file_size===void 0&&t.max_file_size&&Ie!==void 0&&t.max_file_size(Ie),e.initial_layout===void 0&&t.initial_layout&&Se!==void 0&&t.initial_layout(Se),e.css===void 0&&t.css&&ve!==void 0&&t.css(ve),e.vibe_mode===void 0&&t.vibe_mode&&le!==void 0&&t.vibe_mode(le),e.search_params===void 0&&t.search_params&&ce!==void 0&&t.search_params(ce),e.render_complete===void 0&&t.render_complete&&Ne!==void 0&&t.render_complete(Ne),e.add_new_message===void 0&&t.add_new_message&&Re!==void 0&&t.add_new_message(Re),s.css.add(dn);let ye,et,kt=s.head;do ye=!0,s.head=kt,vt(),xe=!!b,g!==De&&Ne&&!Me&&(It(),De=g),pe(p),et=`${s.head+=`<!-- HEAD_svelte-eiigye_START -->${$?`${s.title=`<title>${escape(f)}</title>`,""}`:""}${ve?`<!-- HTML_TAG_START -->${`<style>${ea$1(ve,F)}</style>`}<!-- HTML_TAG_END -->`:""}<!-- HEAD_svelte-eiigye_END -->`,""} <div class="wrap svelte-czcr5b"${add_styles({"min-height":oe?"100%":"auto"})}><div class="contain svelte-czcr5b"${add_styles({"flex-grow":oe?"1":"auto","margin-right":le?`${qe}px`:"0"})}${add_attribute("this",be,0)}>${b&&y.config?`${validate_component(on,"MountComponents").$$render(s,{rootNode:b,root:R,target:G,theme_mode:ee,version:F,autoscroll:X,max_file_size:Ie,client:y},{},{})}`:""}</div> ${j?`<footer class="svelte-czcr5b">${B?`<button class="show-api svelte-czcr5b">${y.config?.mcp_server?`${escape(d("errors.use_via_api_or_mcp"))}`:`${escape(d("errors.use_via_api"))}`} <img${add_attribute("src",sn,0)}${add_attribute("alt",d("common.logo"),0)} class="svelte-czcr5b"></button> <div class="divider show-api-divider svelte-czcr5b" data-svelte-h="svelte-1b2w0qd">·</div>`:""} <a href="https://gradio.app" class="built-with svelte-czcr5b" target="_blank" rel="noreferrer">${escape(d("common.built_with_gradio"))} <img${add_attribute("src",an,0)}${add_attribute("alt",d("common.logo"),0)} class="svelte-czcr5b"></a> <div class="${["divider svelte-czcr5b",m?"":"hidden"].join(" ").trim()}" data-svelte-h="svelte-8g02jg">·</div> <button class="${["record svelte-czcr5b",m?"":"hidden"].join(" ").trim()}">${escape(d("common.stop_recording"))} <img${add_attribute("src",ln,0)}${add_attribute("alt",d("common.stop_recording"),0)} class="svelte-czcr5b"></button> <div class="divider svelte-czcr5b" data-svelte-h="svelte-1r8d4nl">·</div> <button class="settings svelte-czcr5b">${escape(d("common.settings"))} <img${add_attribute("src",rn,0)}${add_attribute("alt",d("common.settings"),0)} class="svelte-czcr5b"></button></footer>`:""}</div> ${ke&&ne?`   <div id="api-recorder-container" class="svelte-czcr5b">${validate_component(missing_component,"svelte:component").$$render(s,{api_calls:we,dependencies:g},{},{})}</div>`:""} ${Fe&&b&&_e?`<div class="api-docs svelte-czcr5b">   <div class="backdrop svelte-czcr5b"></div> <div class="api-docs-wrap svelte-czcr5b">${validate_component(missing_component,"svelte:component").$$render(s,{root_node:b,dependencies:g,root:R,app:y,space_id:te,api_calls:we,username:ze},{},{})}</div></div>`:""} ${Pe&&b&&y.config&&Ce?`<div class="api-docs svelte-czcr5b">   <div class="backdrop svelte-czcr5b"></div> <div class="api-docs-wrap svelte-czcr5b">${validate_component(missing_component,"svelte:component").$$render(s,{pwa_enabled:y.config.pwa,root:R,space_id:te,allow_zoom:Oe,allow_video_trim:Ye},{allow_zoom:n=>{Oe=n,ye=!1;},allow_video_trim:n=>{Ye=n,ye=!1;}},{})}</div></div>`:""} ${C?`${validate_component(yt,"Toast").$$render(s,{messages:C},{},{})}`:""} ${le&&he?`${validate_component(missing_component,"svelte:component").$$render(s,{app:y,root:R},{},{})}`:""}`;while(!ye);return _(),i(),w(),x(),S(),N(),et}),vn={code:".wrap.svelte-1ogxbi0{display:flex;flex-direction:column;justify-content:center;align-items:center;margin-top:var(--size-3);background:var(--background-fill-primary);width:var(--size-full)}h2.svelte-1ogxbi0{margin-bottom:var(--size-3);color:var(--body-text-color);font-weight:var(--section-header-text-weight);font-size:var(--text-xl)}.auth.svelte-1ogxbi0{margin-top:var(--size-1);margin-bottom:var(--size-1);color:var(--body-text-color)}.creds.svelte-1ogxbi0{margin-top:var(--size-4);margin-bottom:var(--size-4);color:var(--error-text-color);font-weight:var(--weight-semibold)}",map:'{"version":3,"file":"Login.svelte","sources":["Login.svelte"],"sourcesContent":["<script lang=\\"ts\\">import Form from \\"@gradio/form\\";\\nimport { BaseTextbox as Textbox } from \\"@gradio/textbox\\";\\nimport { BaseButton } from \\"@gradio/button\\";\\nimport Column from \\"@gradio/column\\";\\nimport { Block } from \\"@gradio/atoms\\";\\nimport { _ } from \\"svelte-i18n\\";\\nexport let root;\\nexport let auth_message;\\nexport let app_mode;\\nexport let space_id;\\nlet username = \\"\\";\\nlet password = \\"\\";\\nlet incorrect_credentials = false;\\nconst submit = async () => {\\n    const formData = new FormData();\\n    formData.append(\\"username\\", username);\\n    formData.append(\\"password\\", password);\\n    let response = await fetch(root + \\"/login\\", {\\n        method: \\"POST\\",\\n        body: formData\\n    });\\n    if (response.status === 400) {\\n        incorrect_credentials = true;\\n        username = \\"\\";\\n        password = \\"\\";\\n    }\\n    else if (response.status == 200) {\\n        location.reload();\\n    }\\n};\\n<\/script>\\n\\n<div class=\\"wrap\\" class:min-h-screen={app_mode}>\\n\\t<Column variant=\\"panel\\" min_width={480}>\\n\\t\\t<h2>{$_(\\"login.login\\")}</h2>\\n\\t\\t{#if auth_message}\\n\\t\\t\\t<p class=\\"auth\\">{@html auth_message}</p>\\n\\t\\t{/if}\\n\\t\\t{#if space_id}\\n\\t\\t\\t<p class=\\"auth\\">\\n\\t\\t\\t\\t{$_(\\"login.enable_cookies\\")}\\n\\t\\t\\t</p>\\n\\t\\t{/if}\\n\\t\\t{#if incorrect_credentials}\\n\\t\\t\\t<p class=\\"creds\\">{$_(\\"login.incorrect_credentials\\")}</p>\\n\\t\\t{/if}\\n\\t\\t<Form>\\n\\t\\t\\t<Block>\\n\\t\\t\\t\\t<Textbox\\n\\t\\t\\t\\t\\tlabel={$_(\\"login.username\\")}\\n\\t\\t\\t\\t\\tlines={1}\\n\\t\\t\\t\\t\\tshow_label={true}\\n\\t\\t\\t\\t\\tmax_lines={1}\\n\\t\\t\\t\\t\\ton:submit={submit}\\n\\t\\t\\t\\t\\tbind:value={username}\\n\\t\\t\\t\\t/>\\n\\t\\t\\t</Block>\\n\\n\\t\\t\\t<Block>\\n\\t\\t\\t\\t<Textbox\\n\\t\\t\\t\\t\\tlabel={$_(\\"login.password\\")}\\n\\t\\t\\t\\t\\tlines={1}\\n\\t\\t\\t\\t\\tshow_label={true}\\n\\t\\t\\t\\t\\tmax_lines={1}\\n\\t\\t\\t\\t\\ttype=\\"password\\"\\n\\t\\t\\t\\t\\ton:submit={submit}\\n\\t\\t\\t\\t\\tbind:value={password}\\n\\t\\t\\t\\t/>\\n\\t\\t\\t</Block>\\n\\t\\t</Form>\\n\\n\\t\\t<BaseButton size=\\"lg\\" variant=\\"primary\\" on:click={submit}\\n\\t\\t\\t>{$_(\\"login.login\\")}</BaseButton\\n\\t\\t>\\n\\t</Column>\\n</div>\\n\\n<style>\\n\\t.wrap {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tjustify-content: center;\\n\\t\\talign-items: center;\\n\\t\\tmargin-top: var(--size-3);\\n\\t\\tbackground: var(--background-fill-primary);\\n\\t\\twidth: var(--size-full);\\n\\t}\\n\\n\\th2 {\\n\\t\\tmargin-bottom: var(--size-3);\\n\\t\\tcolor: var(--body-text-color);\\n\\t\\tfont-weight: var(--section-header-text-weight);\\n\\t\\tfont-size: var(--text-xl);\\n\\t}\\n\\n\\t.auth {\\n\\t\\tmargin-top: var(--size-1);\\n\\t\\tmargin-bottom: var(--size-1);\\n\\t\\tcolor: var(--body-text-color);\\n\\t}\\n\\n\\t.creds {\\n\\t\\tmargin-top: var(--size-4);\\n\\t\\tmargin-bottom: var(--size-4);\\n\\t\\tcolor: var(--error-text-color);\\n\\t\\tfont-weight: var(--weight-semibold);\\n\\t}</style>\\n"],"names":[],"mappings":"AA8EC,oBAAM,CACL,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MAAM,CACtB,eAAe,CAAE,MAAM,CACvB,WAAW,CAAE,MAAM,CACnB,UAAU,CAAE,IAAI,QAAQ,CAAC,CACzB,UAAU,CAAE,IAAI,yBAAyB,CAAC,CAC1C,KAAK,CAAE,IAAI,WAAW,CACvB,CAEA,iBAAG,CACF,aAAa,CAAE,IAAI,QAAQ,CAAC,CAC5B,KAAK,CAAE,IAAI,iBAAiB,CAAC,CAC7B,WAAW,CAAE,IAAI,4BAA4B,CAAC,CAC9C,SAAS,CAAE,IAAI,SAAS,CACzB,CAEA,oBAAM,CACL,UAAU,CAAE,IAAI,QAAQ,CAAC,CACzB,aAAa,CAAE,IAAI,QAAQ,CAAC,CAC5B,KAAK,CAAE,IAAI,iBAAiB,CAC7B,CAEA,qBAAO,CACN,UAAU,CAAE,IAAI,QAAQ,CAAC,CACzB,aAAa,CAAE,IAAI,QAAQ,CAAC,CAC5B,KAAK,CAAE,IAAI,kBAAkB,CAAC,CAC9B,WAAW,CAAE,IAAI,iBAAiB,CACnC"}'},at=create_ssr_component((s$1,e,t,J)=>{let m,_;_=subscribe(Pt$2,N=>m=N);let{root:p}=e,{auth_message:i}=e,{app_mode:h$1}=e,{space_id:w}=e,v="",x="";e.root===void 0&&t.root&&p!==void 0&&t.root(p),e.auth_message===void 0&&t.auth_message&&i!==void 0&&t.auth_message(i),e.app_mode===void 0&&t.app_mode&&h$1!==void 0&&t.app_mode(h$1),e.space_id===void 0&&t.space_id&&w!==void 0&&t.space_id(w),s$1.css.add(vn);let d,S,b=s$1.head;do d=!0,s$1.head=b,S=`<div class="${["wrap svelte-1ogxbi0",h$1?"min-h-screen":""].join(" ").trim()}">${validate_component(h,"Column").$$render(s$1,{variant:"panel",min_width:480},{},{default:()=>`<h2 class="svelte-1ogxbi0">${escape(m("login.login"))}</h2> ${i?`<p class="auth svelte-1ogxbi0"><!-- HTML_TAG_START -->${i}<!-- HTML_TAG_END --></p>`:""} ${w?`<p class="auth svelte-1ogxbi0">${escape(m("login.enable_cookies"))}</p>`:""}  ${validate_component(s,"Form").$$render(s$1,{},{},{default:()=>`${validate_component(It,"Block").$$render(s$1,{},{},{default:()=>`${validate_component(P,"Textbox").$$render(s$1,{label:m("login.username"),lines:1,show_label:!0,max_lines:1,value:v},{value:N=>{v=N,d=!1;}},{})}`})} ${validate_component(It,"Block").$$render(s$1,{},{},{default:()=>`${validate_component(P,"Textbox").$$render(s$1,{label:m("login.password"),lines:1,show_label:!0,max_lines:1,type:"password",value:x},{value:N=>{x=N,d=!1;}},{})}`})}`})} ${validate_component(y,"BaseButton").$$render(s$1,{size:"lg",variant:"primary"},{},{default:()=>`${escape(m("login.login"))}`})}`})} </div>`;while(!d);return _(),S});async function Bn({url:s,data:{server:e,port:t,local_dev_mode:J,accept_language:m}}){let _;const p=e,i=s.searchParams.get("deep_link");try{_=await yn$1.connect(p,{with_null_state:!0,events:["data","log","status","render"],query_params:i?{deep_link:i}:void 0});}catch(d){const S=d.message||"";let b="";return S.includes(os)||(b=S.replace(/^Error:?\s*/,"")),{Render:at,config:{auth_message:b,auth_required:!0,components:[],current_page:"",dependencies:[],layout:{},pages:[],page:{},root:s.origin,space_id:null,analytics_enabled:!1,connect_heartbeat:!1,css:"",js:"",theme_hash:0,head:"",dev_mode:!1,enable_queue:!1,show_error:!1,fill_height:!1,fill_width:!1,mode:"blocks",theme:"default",title:"",version:"",api_prefix:"",is_space:!1,is_colab:!1,show_api:!1,stylesheets:[],protocol:"sse_v3",username:""},api_url:p,layout:{},app:null}}if(!_.config)throw new Error("No config found");let h=_.get_url_config(s.toString());const{create_layout:w,layout:v}=ua$1();await w({app:_,components:h.components,dependencies:h.dependencies,layout:h.layout,root:_.config.root+_.config.api_prefix,options:{fill_height:_.config.fill_height??!1}});const x=get_store_value(v);return await aa$1(_.config?.i18n_translations||void 0,m),{Render:_.config?.auth_required?at:fn,config:h,api_url:p,layout:x,app:_}}

var _page_ts = /*#__PURE__*/Object.freeze({
	__proto__: null,
	load: Bn
});

const a=s$1,t=a$1;

async function g({request:e}){const o=e.headers.get("x-gradio-server")||"http://127.0.0.1:7860",a=e.headers.get("x-gradio-port")||"7860",r=e.headers.get("x-gradio-local-dev-mode")||t?"true":void 0,t$1=e.headers.get("accept-language")||"en";return {server:o,port:a,local_dev_mode:r,accept_language:t$1}}

var _page_server_ts = /*#__PURE__*/Object.freeze({
	__proto__: null,
	load: g
});

const index = 2;
let component_cache;
const component = async () => component_cache ??= (await import('./_page.svelte-rjY2KN1w.js')).default;
const universal_id = "src/routes/[...catchall]/+page.ts";
const server_id = "src/routes/[...catchall]/+page.server.ts";
const imports = ["_app/immutable/nodes/2.44jw4EI1.js","_app/immutable/chunks/2.XmRMbGVn.js","_app/immutable/chunks/preload-helper.D6kgxu3v.js","_app/immutable/chunks/stores.CAUBlXQ3.js","_app/immutable/chunks/client.CZs4mqb7.js"];
const stylesheets = ["_app/immutable/assets/2.DQyR9B4u.css","_app/immutable/assets/Index.C5NYahSl.css","_app/immutable/assets/Index.E3yBBMTH.css","_app/immutable/assets/AudioPlayer.BoZZFzLH.css","_app/immutable/assets/Example.D7K5RtQ2.css","_app/immutable/assets/InteractiveAudio.B76TQFG-.css","_app/immutable/assets/Upload.L7mprsyN.css","_app/immutable/assets/Index.CHmdF0QV.css","_app/immutable/assets/Checkbox.HTxjVTe0.css","_app/immutable/assets/Index.DCIxV6YO.css","_app/immutable/assets/Example.oomIF0ca.css","_app/immutable/assets/Code.DloLYeAi.css","_app/immutable/assets/Example.Bw8Q_3wB.css","_app/immutable/assets/Index.DwWu86Nh.css","_app/immutable/assets/Example.1kVNej19.css","_app/immutable/assets/Index.ucfmx5ZO.css","_app/immutable/assets/ImageUploader.DMdYP1a9.css","_app/immutable/assets/Example.DikqVAPo.css","_app/immutable/assets/Index.D3f6Hf9S.css","_app/immutable/assets/Index.Bk5ZTHOI.css","_app/immutable/assets/Index.Br8OrD4S.css","_app/immutable/assets/Dropdown.CWxB-qJp.css","_app/immutable/assets/Index.tcNSQSor.css","_app/immutable/assets/Index.CIMAvdMc.css","_app/immutable/assets/Example.DpWs9cEC.css","_app/immutable/assets/FileUpload.b2Zdge9M.css","_app/immutable/assets/Example.DfhEULNF.css","_app/immutable/assets/Index.BKaa_GXG.css","_app/immutable/assets/Gallery.Cs9Ilp9M.css","_app/immutable/assets/Video.DJw86Ppo.css","_app/immutable/assets/Example.C6fDlAyr.css","_app/immutable/assets/Index.Cgj6KPvj.css","_app/immutable/assets/Index.KsvjhaTn.css","_app/immutable/assets/Index.Csm0OGa9.css","_app/immutable/assets/Example.CSw4pLi5.css","_app/immutable/assets/Example.6rv12T44.css","_app/immutable/assets/Index.CCAzyDPy.css","_app/immutable/assets/Example.fMB4cHw6.css","_app/immutable/assets/Index.xkmfPIkL.css","_app/immutable/assets/Example.CG7uBGLE.css","_app/immutable/assets/JSON.AVFPpFex.css","_app/immutable/assets/Index.D3BKJl5I.css","_app/immutable/assets/Index.BTXaMQgd.css","_app/immutable/assets/Index.Be3F7oKw.css","_app/immutable/assets/Example.CCTTJ5R1.css","_app/immutable/assets/Index.D6bhueJw.css","_app/immutable/assets/Index.WdTVQ0oj.css","_app/immutable/assets/Index.MxHcWSnO.css","_app/immutable/assets/Index.2z2XN1av.css","_app/immutable/assets/BokehPlot.Cd-I2ErV.css","_app/immutable/assets/AltairPlot.CSe9xcFj.css","_app/immutable/assets/MatplotlibPlot.AF_QcUtc.css","_app/immutable/assets/Index.-UpFQsHg.css","_app/immutable/assets/Index.CfowPFmo.css","_app/immutable/assets/Index.w1Ra_uQ1.css","_app/immutable/assets/Index.Cwr2RydD.css","_app/immutable/assets/Index.C0mowOU5.css","_app/immutable/assets/Index.6AICi3cy.css","_app/immutable/assets/Walkthrough.DTfMPm_f.css","_app/immutable/assets/Index.DYDmCduo.css","_app/immutable/assets/Index.CWsqmWBE.css","_app/immutable/assets/VideoPreview.BeECudjn.css","_app/immutable/assets/Example.B5CSTz0f.css","_app/immutable/assets/index.CFBZQE_H.css","_app/immutable/assets/Index.CgDrEMlk.css","_app/immutable/assets/ApiDocs.CrTYCJN9.css","_app/immutable/assets/ApiRecorder.7UmvbTxs.css","_app/immutable/assets/Settings.D01KD214.css"];
const fonts = [];

var _2 = /*#__PURE__*/Object.freeze({
	__proto__: null,
	component: component,
	fonts: fonts,
	imports: imports,
	index: index,
	server: _page_server_ts,
	server_id: server_id,
	stylesheets: stylesheets,
	universal: _page_ts,
	universal_id: universal_id
});

export { $t as $, Aa as A, Ut as B, je as C, xe as D, Et as E, Dt as F, Ge as G, Hr$1 as H, It as I, Js as J, yt$1 as K, Lo as L, Mt as M, No as N, O$1 as O, Pt as P, tt as Q, h$1 as R, w$1 as S, Te as T, Ue as U, Kt as V, Wt as W, Xs as X, Ys as Y, Ze as Z, _t as _, aa$1 as a, de as a0, ce as a1, Jt as a2, Tt as a3, me as a4, Ee as a5, Ie as a6, ye as a7, Ve as a8, _e as a9, Ce as aA, dt$1 as aB, Ks as aC, now as aD, loop as aE, is_date as aF, _2 as aG, ha as aa, St as ab, ht as ac, ge as ad, Vt as ae, Ot as af, Rt as ag, he as ah, ue as ai, pe as aj, y as ak, Q as al, we as am, globals as an, na$1 as ao, ta$1 as ap, y$1 as aq, et$2 as ar, re as as, Ae as at, Le$1 as au, be as av, ae as aw, ct$2 as ax, yt$3 as ay, te$2 as az, at$2 as b, ca$1 as c, a as d, ea$1 as e, Et$1 as f, ie as g, h, ia$1 as i, _ as j, ko as k, la$1 as l, Gt as m, ne as n, oa$1 as o, it$1 as p, fe as q, g$1 as r, sa$1 as s, te as t, ua$1 as u, Yt as v, wt$1 as w, xt as x, yt as y, Zt as z };
//# sourceMappingURL=2-2QjpS3e7.js.map
