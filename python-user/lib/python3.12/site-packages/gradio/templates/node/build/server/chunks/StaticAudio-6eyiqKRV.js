import { c as create_ssr_component, b as createEventDispatcher, v as validate_component } from './ssr-C3HYbsxA.js';
import { f as Et, g as ie, U as Ue, M as Mt, O, $ as $t, G as Ge, j as _, _ as _t } from './2-2QjpS3e7.js';
import { Z as Zt } from './AudioPlayer-BodTRsY3.js';
import './index-ClteBeTX.js';
import './Component-NmRBwSfF.js';
import 'path';
import 'url';
import 'fs';
import './hls-DpKhbIaL.js';

const q=create_ssr_component((a,o,e,P)=>{let{value:t=null}=o,{subtitles:_$1=null}=o,{label:u}=o,{show_label:i=!0}=o,{show_download_button:d=!0}=o,{show_share_button:n=!1}=o,{i18n:r}=o,{waveform_settings:f={}}=o,{waveform_options:v={show_recording_waveform:!0}}=o,{editable:c=!0}=o,{loop:w}=o,{display_icon_button_wrapper_top_corner:m=!1}=o;const y=createEventDispatcher();return o.value===void 0&&e.value&&t!==void 0&&e.value(t),o.subtitles===void 0&&e.subtitles&&_$1!==void 0&&e.subtitles(_$1),o.label===void 0&&e.label&&u!==void 0&&e.label(u),o.show_label===void 0&&e.show_label&&i!==void 0&&e.show_label(i),o.show_download_button===void 0&&e.show_download_button&&d!==void 0&&e.show_download_button(d),o.show_share_button===void 0&&e.show_share_button&&n!==void 0&&e.show_share_button(n),o.i18n===void 0&&e.i18n&&r!==void 0&&e.i18n(r),o.waveform_settings===void 0&&e.waveform_settings&&f!==void 0&&e.waveform_settings(f),o.waveform_options===void 0&&e.waveform_options&&v!==void 0&&e.waveform_options(v),o.editable===void 0&&e.editable&&c!==void 0&&e.editable(c),o.loop===void 0&&e.loop&&w!==void 0&&e.loop(w),o.display_icon_button_wrapper_top_corner===void 0&&e.display_icon_button_wrapper_top_corner&&m!==void 0&&e.display_icon_button_wrapper_top_corner(m),t&&y("change",t),`${validate_component(Et,"BlockLabel").$$render(a,{show_label:i,Icon:ie,float:!1,label:u||r("audio.audio")},{},{})} ${t!==null?`${validate_component(Ue,"IconButtonWrapper").$$render(a,{display_top_corner:m},{},{default:()=>`${d?`${validate_component(Mt,"DownloadLink").$$render(a,{href:t.is_stream?t.url?.replace("playlist.m3u8","playlist-file"):t.url,download:t.orig_name||t.path},{},{default:()=>`${validate_component(O,"IconButton").$$render(a,{Icon:$t,label:r("common.download")},{},{})}`})}`:""} ${n?`${validate_component(Ge,"ShareButton").$$render(a,{i18n:r,formatter:async s=>s?`<audio controls src="${await _(s.url)}"></audio>`:"",value:t},{},{})}`:""}`})} ${validate_component(Zt,"AudioPlayer").$$render(a,{value:t,subtitles:Array.isArray(_$1)?_$1:_$1?.url,label:u,i18n:r,waveform_settings:f,waveform_options:v,editable:c,loop:w},{},{})}`:`${validate_component(_t,"Empty").$$render(a,{size:"small"},{},{default:()=>`${validate_component(ie,"Music").$$render(a,{},{},{})}`})}`}`});

export { q as default };
//# sourceMappingURL=StaticAudio-6eyiqKRV.js.map
