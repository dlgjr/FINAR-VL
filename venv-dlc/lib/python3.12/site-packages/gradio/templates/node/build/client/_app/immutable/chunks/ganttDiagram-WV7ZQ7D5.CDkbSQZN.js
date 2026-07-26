import{_ as l,at as U,d as ct,s as me,g as ke,n as ye,o as ge,c as pe,b as ve,t as xe,k as Te,l as bt,j as be,e as we,u as _e}from"./mermaid.core.DTNv8IuU.js";import{H as Ft,h as Lt}from"./2.XmRMbGVn.js";import{t as De,m as Se,a as Ce,i as Ee,b as jt,c as Xt,d as qt,e as Ut,f as Zt,s as Qt,g as $t,h as Me,j as Ae,k as Ie,l as Fe,n as Le,o as Ye,p as We}from"./time.Be8aEIgQ.js";import{l as Ve}from"./linear.BQxp-PJv.js";import{s as gt}from"./select.BigU4G0v.js";function Oe(t){return t}var vt=1,St=2,Ct=3,pt=4,Kt=1e-6;function ze(t){return"translate("+t+",0)"}function Pe(t){return"translate(0,"+t+")"}function Re(t){return e=>+t(e)}function Ne(t,e){return e=Math.max(0,t.bandwidth()-e*2)/2,t.round()&&(e=Math.round(e)),i=>+t(i)+e}function Be(){return!this.__axis}function re(t,e){var i=[],a=null,s=null,h=6,u=6,D=3,E=typeof window<"u"&&window.devicePixelRatio>1?0:.5,C=t===vt||t===pt?-1:1,p=t===pt||t===St?"x":"y",F=t===vt||t===Ct?ze:Pe;function S(x){var G=a??(e.ticks?e.ticks.apply(e,i):e.domain()),A=s??(e.tickFormat?e.tickFormat.apply(e,i):Oe),T=Math.max(h,0)+D,M=e.range(),L=+M[0]+E,Y=+M[M.length-1]+E,N=(e.bandwidth?Ne:Re)(e.copy(),E),R=x.selection?x.selection():x,j=R.selectAll(".domain").data([null]),z=R.selectAll(".tick").data(G,e).order(),g=z.exit(),w=z.enter().append("g").attr("class","tick"),b=z.select("line"),v=z.select("text");j=j.merge(j.enter().insert("path",".tick").attr("class","domain").attr("stroke","currentColor")),z=z.merge(w),b=b.merge(w.append("line").attr("stroke","currentColor").attr(p+"2",C*h)),v=v.merge(w.append("text").attr("fill","currentColor").attr(p,C*T).attr("dy",t===vt?"0em":t===Ct?"0.71em":"0.32em")),x!==R&&(j=j.transition(x),z=z.transition(x),b=b.transition(x),v=v.transition(x),g=g.transition(x).attr("opacity",Kt).attr("transform",function(m){return isFinite(m=N(m))?F(m+E):this.getAttribute("transform")}),w.attr("opacity",Kt).attr("transform",function(m){var _=this.parentNode.__axis;return F((_&&isFinite(_=_(m))?_:N(m))+E)})),g.remove(),j.attr("d",t===pt||t===St?u?"M"+C*u+","+L+"H"+E+"V"+Y+"H"+C*u:"M"+E+","+L+"V"+Y:u?"M"+L+","+C*u+"V"+E+"H"+Y+"V"+C*u:"M"+L+","+E+"H"+Y),z.attr("opacity",1).attr("transform",function(m){return F(N(m)+E)}),b.attr(p+"2",C*h),v.attr(p,C*T).text(A),R.filter(Be).attr("fill","none").attr("font-size",10).attr("font-family","sans-serif").attr("text-anchor",t===St?"start":t===pt?"end":"middle"),R.each(function(){this.__axis=N})}return S.scale=function(x){return arguments.length?(e=x,S):e},S.ticks=function(){return i=Array.from(arguments),S},S.tickArguments=function(x){return arguments.length?(i=x==null?[]:Array.from(x),S):i.slice()},S.tickValues=function(x){return arguments.length?(a=x==null?null:Array.from(x),S):a&&a.slice()},S.tickFormat=function(x){return arguments.length?(s=x,S):s},S.tickSize=function(x){return arguments.length?(h=u=+x,S):h},S.tickSizeInner=function(x){return arguments.length?(h=+x,S):h},S.tickSizeOuter=function(x){return arguments.length?(u=+x,S):u},S.tickPadding=function(x){return arguments.length?(D=+x,S):D},S.offset=function(x){return arguments.length?(E=+x,S):E},S}function He(t){return re(vt,t)}function Ge(t){return re(Ct,t)}var ne={exports:{}};(function(t,e){(function(i,a){t.exports=a()})(Ft,function(){var i="day";return function(a,s,h){var u=function(C){return C.add(4-C.isoWeekday(),i)},D=s.prototype;D.isoWeekYear=function(){return u(this).year()},D.isoWeek=function(C){if(!this.$utils().u(C))return this.add(7*(C-this.isoWeek()),i);var p,F,S,x,G=u(this),A=(p=this.isoWeekYear(),F=this.$u,S=(F?h.utc:h)().year(p).startOf("year"),x=4-S.isoWeekday(),S.isoWeekday()>4&&(x+=7),S.add(x,i));return G.diff(A,"week")+1},D.isoWeekday=function(C){return this.$utils().u(C)?this.day()||7:this.day(this.day()%7?C:C-7)};var E=D.startOf;D.startOf=function(C,p){var F=this.$utils(),S=!!F.u(p)||p;return F.p(C)==="isoweek"?S?this.date(this.date()-(this.isoWeekday()-1)).startOf("day"):this.date(this.date()-1-(this.isoWeekday()-1)+7).endOf("day"):E.bind(this)(C,p)}}})})(ne);var je=ne.exports;const Xe=Lt(je);var ie={exports:{}};(function(t,e){(function(i,a){t.exports=a()})(Ft,function(){var i={LTS:"h:mm:ss A",LT:"h:mm A",L:"MM/DD/YYYY",LL:"MMMM D, YYYY",LLL:"MMMM D, YYYY h:mm A",LLLL:"dddd, MMMM D, YYYY h:mm A"},a=/(\[[^[]*\])|([-_:/.,()\s]+)|(A|a|Q|YYYY|YY?|ww?|MM?M?M?|Do|DD?|hh?|HH?|mm?|ss?|S{1,3}|z|ZZ?)/g,s=/\d/,h=/\d\d/,u=/\d\d?/,D=/\d*[^-_:/,()\s\d]+/,E={},C=function(T){return(T=+T)+(T>68?1900:2e3)},p=function(T){return function(M){this[T]=+M}},F=[/[+-]\d\d:?(\d\d)?|Z/,function(T){(this.zone||(this.zone={})).offset=function(M){if(!M||M==="Z")return 0;var L=M.match(/([+-]|\d\d)/g),Y=60*L[1]+(+L[2]||0);return Y===0?0:L[0]==="+"?-Y:Y}(T)}],S=function(T){var M=E[T];return M&&(M.indexOf?M:M.s.concat(M.f))},x=function(T,M){var L,Y=E.meridiem;if(Y){for(var N=1;N<=24;N+=1)if(T.indexOf(Y(N,0,M))>-1){L=N>12;break}}else L=T===(M?"pm":"PM");return L},G={A:[D,function(T){this.afternoon=x(T,!1)}],a:[D,function(T){this.afternoon=x(T,!0)}],Q:[s,function(T){this.month=3*(T-1)+1}],S:[s,function(T){this.milliseconds=100*+T}],SS:[h,function(T){this.milliseconds=10*+T}],SSS:[/\d{3}/,function(T){this.milliseconds=+T}],s:[u,p("seconds")],ss:[u,p("seconds")],m:[u,p("minutes")],mm:[u,p("minutes")],H:[u,p("hours")],h:[u,p("hours")],HH:[u,p("hours")],hh:[u,p("hours")],D:[u,p("day")],DD:[h,p("day")],Do:[D,function(T){var M=E.ordinal,L=T.match(/\d+/);if(this.day=L[0],M)for(var Y=1;Y<=31;Y+=1)M(Y).replace(/\[|\]/g,"")===T&&(this.day=Y)}],w:[u,p("week")],ww:[h,p("week")],M:[u,p("month")],MM:[h,p("month")],MMM:[D,function(T){var M=S("months"),L=(S("monthsShort")||M.map(function(Y){return Y.slice(0,3)})).indexOf(T)+1;if(L<1)throw new Error;this.month=L%12||L}],MMMM:[D,function(T){var M=S("months").indexOf(T)+1;if(M<1)throw new Error;this.month=M%12||M}],Y:[/[+-]?\d+/,p("year")],YY:[h,function(T){this.year=C(T)}],YYYY:[/\d{4}/,p("year")],Z:F,ZZ:F};function A(T){var M,L;M=T,L=E&&E.formats;for(var Y=(T=M.replace(/(\[[^\]]+])|(LTS?|l{1,4}|L{1,4})/g,function(b,v,m){var _=m&&m.toUpperCase();return v||L[m]||i[m]||L[_].replace(/(\[[^\]]+])|(MMMM|MM|DD|dddd)/g,function(c,f,k){return f||k.slice(1)})})).match(a),N=Y.length,R=0;R<N;R+=1){var j=Y[R],z=G[j],g=z&&z[0],w=z&&z[1];Y[R]=w?{regex:g,parser:w}:j.replace(/^\[|\]$/g,"")}return function(b){for(var v={},m=0,_=0;m<N;m+=1){var c=Y[m];if(typeof c=="string")_+=c.length;else{var f=c.regex,k=c.parser,d=b.slice(_),y=f.exec(d)[0];k.call(v,y),b=b.replace(y,"")}}return function(n){var o=n.afternoon;if(o!==void 0){var r=n.hours;o?r<12&&(n.hours+=12):r===12&&(n.hours=0),delete n.afternoon}}(v),v}}return function(T,M,L){L.p.customParseFormat=!0,T&&T.parseTwoDigitYear&&(C=T.parseTwoDigitYear);var Y=M.prototype,N=Y.parse;Y.parse=function(R){var j=R.date,z=R.utc,g=R.args;this.$u=z;var w=g[1];if(typeof w=="string"){var b=g[2]===!0,v=g[3]===!0,m=b||v,_=g[2];v&&(_=g[2]),E=this.$locale(),!b&&_&&(E=L.Ls[_]),this.$d=function(d,y,n,o){try{if(["x","X"].indexOf(y)>-1)return new Date((y==="X"?1e3:1)*d);var r=A(y)(d),W=r.year,I=r.month,V=r.day,X=r.hours,O=r.minutes,P=r.seconds,$=r.milliseconds,st=r.zone,at=r.week,dt=new Date,ft=V||(W||I?1:dt.getDate()),ot=W||dt.getFullYear(),B=0;W&&!I||(B=I>0?I-1:dt.getMonth());var Q,q=X||0,nt=O||0,K=P||0,rt=$||0;return st?new Date(Date.UTC(ot,B,ft,q,nt,K,rt+60*st.offset*1e3)):n?new Date(Date.UTC(ot,B,ft,q,nt,K,rt)):(Q=new Date(ot,B,ft,q,nt,K,rt),at&&(Q=o(Q).week(at).toDate()),Q)}catch{return new Date("")}}(j,w,z,L),this.init(),_&&_!==!0&&(this.$L=this.locale(_).$L),m&&j!=this.format(w)&&(this.$d=new Date("")),E={}}else if(w instanceof Array)for(var c=w.length,f=1;f<=c;f+=1){g[1]=w[f-1];var k=L.apply(this,g);if(k.isValid()){this.$d=k.$d,this.$L=k.$L,this.init();break}f===c&&(this.$d=new Date(""))}else N.call(this,R)}}})})(ie);var qe=ie.exports;const Ue=Lt(qe);var se={exports:{}};(function(t,e){(function(i,a){t.exports=a()})(Ft,function(){return function(i,a){var s=a.prototype,h=s.format;s.format=function(u){var D=this,E=this.$locale();if(!this.isValid())return h.bind(this)(u);var C=this.$utils(),p=(u||"YYYY-MM-DDTHH:mm:ssZ").replace(/\[([^\]]+)]|Q|wo|ww|w|WW|W|zzz|z|gggg|GGGG|Do|X|x|k{1,2}|S/g,function(F){switch(F){case"Q":return Math.ceil((D.$M+1)/3);case"Do":return E.ordinal(D.$D);case"gggg":return D.weekYear();case"GGGG":return D.isoWeekYear();case"wo":return E.ordinal(D.week(),"W");case"w":case"ww":return C.s(D.week(),F==="w"?1:2,"0");case"W":case"WW":return C.s(D.isoWeek(),F==="W"?1:2,"0");case"k":case"kk":return C.s(String(D.$H===0?24:D.$H),F==="k"?1:2,"0");case"X":return Math.floor(D.$d.getTime()/1e3);case"x":return D.$d.getTime();case"z":return"["+D.offsetName()+"]";case"zzz":return"["+D.offsetName("long")+"]";default:return F}});return h.bind(this)(p)}}})})(se);var Ze=se.exports;const Qe=Lt(Ze);var Et=function(){var t=l(function(_,c,f,k){for(f=f||{},k=_.length;k--;f[_[k]]=c);return f},"o"),e=[6,8,10,12,13,14,15,16,17,18,20,21,22,23,24,25,26,27,28,29,30,31,33,35,36,38,40],i=[1,26],a=[1,27],s=[1,28],h=[1,29],u=[1,30],D=[1,31],E=[1,32],C=[1,33],p=[1,34],F=[1,9],S=[1,10],x=[1,11],G=[1,12],A=[1,13],T=[1,14],M=[1,15],L=[1,16],Y=[1,19],N=[1,20],R=[1,21],j=[1,22],z=[1,23],g=[1,25],w=[1,35],b={trace:l(function(){},"trace"),yy:{},symbols_:{error:2,start:3,gantt:4,document:5,EOF:6,line:7,SPACE:8,statement:9,NL:10,weekday:11,weekday_monday:12,weekday_tuesday:13,weekday_wednesday:14,weekday_thursday:15,weekday_friday:16,weekday_saturday:17,weekday_sunday:18,weekend:19,weekend_friday:20,weekend_saturday:21,dateFormat:22,inclusiveEndDates:23,topAxis:24,axisFormat:25,tickInterval:26,excludes:27,includes:28,todayMarker:29,title:30,acc_title:31,acc_title_value:32,acc_descr:33,acc_descr_value:34,acc_descr_multiline_value:35,section:36,clickStatement:37,taskTxt:38,taskData:39,click:40,callbackname:41,callbackargs:42,href:43,clickStatementDebug:44,$accept:0,$end:1},terminals_:{2:"error",4:"gantt",6:"EOF",8:"SPACE",10:"NL",12:"weekday_monday",13:"weekday_tuesday",14:"weekday_wednesday",15:"weekday_thursday",16:"weekday_friday",17:"weekday_saturday",18:"weekday_sunday",20:"weekend_friday",21:"weekend_saturday",22:"dateFormat",23:"inclusiveEndDates",24:"topAxis",25:"axisFormat",26:"tickInterval",27:"excludes",28:"includes",29:"todayMarker",30:"title",31:"acc_title",32:"acc_title_value",33:"acc_descr",34:"acc_descr_value",35:"acc_descr_multiline_value",36:"section",38:"taskTxt",39:"taskData",40:"click",41:"callbackname",42:"callbackargs",43:"href"},productions_:[0,[3,3],[5,0],[5,2],[7,2],[7,1],[7,1],[7,1],[11,1],[11,1],[11,1],[11,1],[11,1],[11,1],[11,1],[19,1],[19,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,2],[9,2],[9,1],[9,1],[9,1],[9,2],[37,2],[37,3],[37,3],[37,4],[37,3],[37,4],[37,2],[44,2],[44,3],[44,3],[44,4],[44,3],[44,4],[44,2]],performAction:l(function(c,f,k,d,y,n,o){var r=n.length-1;switch(y){case 1:return n[r-1];case 2:this.$=[];break;case 3:n[r-1].push(n[r]),this.$=n[r-1];break;case 4:case 5:this.$=n[r];break;case 6:case 7:this.$=[];break;case 8:d.setWeekday("monday");break;case 9:d.setWeekday("tuesday");break;case 10:d.setWeekday("wednesday");break;case 11:d.setWeekday("thursday");break;case 12:d.setWeekday("friday");break;case 13:d.setWeekday("saturday");break;case 14:d.setWeekday("sunday");break;case 15:d.setWeekend("friday");break;case 16:d.setWeekend("saturday");break;case 17:d.setDateFormat(n[r].substr(11)),this.$=n[r].substr(11);break;case 18:d.enableInclusiveEndDates(),this.$=n[r].substr(18);break;case 19:d.TopAxis(),this.$=n[r].substr(8);break;case 20:d.setAxisFormat(n[r].substr(11)),this.$=n[r].substr(11);break;case 21:d.setTickInterval(n[r].substr(13)),this.$=n[r].substr(13);break;case 22:d.setExcludes(n[r].substr(9)),this.$=n[r].substr(9);break;case 23:d.setIncludes(n[r].substr(9)),this.$=n[r].substr(9);break;case 24:d.setTodayMarker(n[r].substr(12)),this.$=n[r].substr(12);break;case 27:d.setDiagramTitle(n[r].substr(6)),this.$=n[r].substr(6);break;case 28:this.$=n[r].trim(),d.setAccTitle(this.$);break;case 29:case 30:this.$=n[r].trim(),d.setAccDescription(this.$);break;case 31:d.addSection(n[r].substr(8)),this.$=n[r].substr(8);break;case 33:d.addTask(n[r-1],n[r]),this.$="task";break;case 34:this.$=n[r-1],d.setClickEvent(n[r-1],n[r],null);break;case 35:this.$=n[r-2],d.setClickEvent(n[r-2],n[r-1],n[r]);break;case 36:this.$=n[r-2],d.setClickEvent(n[r-2],n[r-1],null),d.setLink(n[r-2],n[r]);break;case 37:this.$=n[r-3],d.setClickEvent(n[r-3],n[r-2],n[r-1]),d.setLink(n[r-3],n[r]);break;case 38:this.$=n[r-2],d.setClickEvent(n[r-2],n[r],null),d.setLink(n[r-2],n[r-1]);break;case 39:this.$=n[r-3],d.setClickEvent(n[r-3],n[r-1],n[r]),d.setLink(n[r-3],n[r-2]);break;case 40:this.$=n[r-1],d.setLink(n[r-1],n[r]);break;case 41:case 47:this.$=n[r-1]+" "+n[r];break;case 42:case 43:case 45:this.$=n[r-2]+" "+n[r-1]+" "+n[r];break;case 44:case 46:this.$=n[r-3]+" "+n[r-2]+" "+n[r-1]+" "+n[r];break}},"anonymous"),table:[{3:1,4:[1,2]},{1:[3]},t(e,[2,2],{5:3}),{6:[1,4],7:5,8:[1,6],9:7,10:[1,8],11:17,12:i,13:a,14:s,15:h,16:u,17:D,18:E,19:18,20:C,21:p,22:F,23:S,24:x,25:G,26:A,27:T,28:M,29:L,30:Y,31:N,33:R,35:j,36:z,37:24,38:g,40:w},t(e,[2,7],{1:[2,1]}),t(e,[2,3]),{9:36,11:17,12:i,13:a,14:s,15:h,16:u,17:D,18:E,19:18,20:C,21:p,22:F,23:S,24:x,25:G,26:A,27:T,28:M,29:L,30:Y,31:N,33:R,35:j,36:z,37:24,38:g,40:w},t(e,[2,5]),t(e,[2,6]),t(e,[2,17]),t(e,[2,18]),t(e,[2,19]),t(e,[2,20]),t(e,[2,21]),t(e,[2,22]),t(e,[2,23]),t(e,[2,24]),t(e,[2,25]),t(e,[2,26]),t(e,[2,27]),{32:[1,37]},{34:[1,38]},t(e,[2,30]),t(e,[2,31]),t(e,[2,32]),{39:[1,39]},t(e,[2,8]),t(e,[2,9]),t(e,[2,10]),t(e,[2,11]),t(e,[2,12]),t(e,[2,13]),t(e,[2,14]),t(e,[2,15]),t(e,[2,16]),{41:[1,40],43:[1,41]},t(e,[2,4]),t(e,[2,28]),t(e,[2,29]),t(e,[2,33]),t(e,[2,34],{42:[1,42],43:[1,43]}),t(e,[2,40],{41:[1,44]}),t(e,[2,35],{43:[1,45]}),t(e,[2,36]),t(e,[2,38],{42:[1,46]}),t(e,[2,37]),t(e,[2,39])],defaultActions:{},parseError:l(function(c,f){if(f.recoverable)this.trace(c);else{var k=new Error(c);throw k.hash=f,k}},"parseError"),parse:l(function(c){var f=this,k=[0],d=[],y=[null],n=[],o=this.table,r="",W=0,I=0,V=2,X=1,O=n.slice.call(arguments,1),P=Object.create(this.lexer),$={yy:{}};for(var st in this.yy)Object.prototype.hasOwnProperty.call(this.yy,st)&&($.yy[st]=this.yy[st]);P.setInput(c,$.yy),$.yy.lexer=P,$.yy.parser=this,typeof P.yylloc>"u"&&(P.yylloc={});var at=P.yylloc;n.push(at);var dt=P.options&&P.options.ranges;typeof $.yy.parseError=="function"?this.parseError=$.yy.parseError:this.parseError=Object.getPrototypeOf(this).parseError;function ft(Z){k.length=k.length-2*Z,y.length=y.length-Z,n.length=n.length-Z}l(ft,"popStack");function ot(){var Z;return Z=d.pop()||P.lex()||X,typeof Z!="number"&&(Z instanceof Array&&(d=Z,Z=d.pop()),Z=f.symbols_[Z]||Z),Z}l(ot,"lex");for(var B,Q,q,nt,K={},rt,J,Gt,yt;;){if(Q=k[k.length-1],this.defaultActions[Q]?q=this.defaultActions[Q]:((B===null||typeof B>"u")&&(B=ot()),q=o[Q]&&o[Q][B]),typeof q>"u"||!q.length||!q[0]){var Dt="";yt=[];for(rt in o[Q])this.terminals_[rt]&&rt>V&&yt.push("'"+this.terminals_[rt]+"'");P.showPosition?Dt="Parse error on line "+(W+1)+`:
`+P.showPosition()+`
Expecting `+yt.join(", ")+", got '"+(this.terminals_[B]||B)+"'":Dt="Parse error on line "+(W+1)+": Unexpected "+(B==X?"end of input":"'"+(this.terminals_[B]||B)+"'"),this.parseError(Dt,{text:P.match,token:this.terminals_[B]||B,line:P.yylineno,loc:at,expected:yt})}if(q[0]instanceof Array&&q.length>1)throw new Error("Parse Error: multiple actions possible at state: "+Q+", token: "+B);switch(q[0]){case 1:k.push(B),y.push(P.yytext),n.push(P.yylloc),k.push(q[1]),B=null,I=P.yyleng,r=P.yytext,W=P.yylineno,at=P.yylloc;break;case 2:if(J=this.productions_[q[1]][1],K.$=y[y.length-J],K._$={first_line:n[n.length-(J||1)].first_line,last_line:n[n.length-1].last_line,first_column:n[n.length-(J||1)].first_column,last_column:n[n.length-1].last_column},dt&&(K._$.range=[n[n.length-(J||1)].range[0],n[n.length-1].range[1]]),nt=this.performAction.apply(K,[r,I,W,$.yy,q[1],y,n].concat(O)),typeof nt<"u")return nt;J&&(k=k.slice(0,-1*J*2),y=y.slice(0,-1*J),n=n.slice(0,-1*J)),k.push(this.productions_[q[1]][0]),y.push(K.$),n.push(K._$),Gt=o[k[k.length-2]][k[k.length-1]],k.push(Gt);break;case 3:return!0}}return!0},"parse")},v=function(){var _={EOF:1,parseError:l(function(f,k){if(this.yy.parser)this.yy.parser.parseError(f,k);else throw new Error(f)},"parseError"),setInput:l(function(c,f){return this.yy=f||this.yy||{},this._input=c,this._more=this._backtrack=this.done=!1,this.yylineno=this.yyleng=0,this.yytext=this.matched=this.match="",this.conditionStack=["INITIAL"],this.yylloc={first_line:1,first_column:0,last_line:1,last_column:0},this.options.ranges&&(this.yylloc.range=[0,0]),this.offset=0,this},"setInput"),input:l(function(){var c=this._input[0];this.yytext+=c,this.yyleng++,this.offset++,this.match+=c,this.matched+=c;var f=c.match(/(?:\r\n?|\n).*/g);return f?(this.yylineno++,this.yylloc.last_line++):this.yylloc.last_column++,this.options.ranges&&this.yylloc.range[1]++,this._input=this._input.slice(1),c},"input"),unput:l(function(c){var f=c.length,k=c.split(/(?:\r\n?|\n)/g);this._input=c+this._input,this.yytext=this.yytext.substr(0,this.yytext.length-f),this.offset-=f;var d=this.match.split(/(?:\r\n?|\n)/g);this.match=this.match.substr(0,this.match.length-1),this.matched=this.matched.substr(0,this.matched.length-1),k.length-1&&(this.yylineno-=k.length-1);var y=this.yylloc.range;return this.yylloc={first_line:this.yylloc.first_line,last_line:this.yylineno+1,first_column:this.yylloc.first_column,last_column:k?(k.length===d.length?this.yylloc.first_column:0)+d[d.length-k.length].length-k[0].length:this.yylloc.first_column-f},this.options.ranges&&(this.yylloc.range=[y[0],y[0]+this.yyleng-f]),this.yyleng=this.yytext.length,this},"unput"),more:l(function(){return this._more=!0,this},"more"),reject:l(function(){if(this.options.backtrack_lexer)this._backtrack=!0;else return this.parseError("Lexical error on line "+(this.yylineno+1)+`. You can only invoke reject() in the lexer when the lexer is of the backtracking persuasion (options.backtrack_lexer = true).
`+this.showPosition(),{text:"",token:null,line:this.yylineno});return this},"reject"),less:l(function(c){this.unput(this.match.slice(c))},"less"),pastInput:l(function(){var c=this.matched.substr(0,this.matched.length-this.match.length);return(c.length>20?"...":"")+c.substr(-20).replace(/\n/g,"")},"pastInput"),upcomingInput:l(function(){var c=this.match;return c.length<20&&(c+=this._input.substr(0,20-c.length)),(c.substr(0,20)+(c.length>20?"...":"")).replace(/\n/g,"")},"upcomingInput"),showPosition:l(function(){var c=this.pastInput(),f=new Array(c.length+1).join("-");return c+this.upcomingInput()+`
`+f+"^"},"showPosition"),test_match:l(function(c,f){var k,d,y;if(this.options.backtrack_lexer&&(y={yylineno:this.yylineno,yylloc:{first_line:this.yylloc.first_line,last_line:this.last_line,first_column:this.yylloc.first_column,last_column:this.yylloc.last_column},yytext:this.yytext,match:this.match,matches:this.matches,matched:this.matched,yyleng:this.yyleng,offset:this.offset,_more:this._more,_input:this._input,yy:this.yy,conditionStack:this.conditionStack.slice(0),done:this.done},this.options.ranges&&(y.yylloc.range=this.yylloc.range.slice(0))),d=c[0].match(/(?:\r\n?|\n).*/g),d&&(this.yylineno+=d.length),this.yylloc={first_line:this.yylloc.last_line,last_line:this.yylineno+1,first_column:this.yylloc.last_column,last_column:d?d[d.length-1].length-d[d.length-1].match(/\r?\n?/)[0].length:this.yylloc.last_column+c[0].length},this.yytext+=c[0],this.match+=c[0],this.matches=c,this.yyleng=this.yytext.length,this.options.ranges&&(this.yylloc.range=[this.offset,this.offset+=this.yyleng]),this._more=!1,this._backtrack=!1,this._input=this._input.slice(c[0].length),this.matched+=c[0],k=this.performAction.call(this,this.yy,this,f,this.conditionStack[this.conditionStack.length-1]),this.done&&this._input&&(this.done=!1),k)return k;if(this._backtrack){for(var n in y)this[n]=y[n];return!1}return!1},"test_match"),next:l(function(){if(this.done)return this.EOF;this._input||(this.done=!0);var c,f,k,d;this._more||(this.yytext="",this.match="");for(var y=this._currentRules(),n=0;n<y.length;n++)if(k=this._input.match(this.rules[y[n]]),k&&(!f||k[0].length>f[0].length)){if(f=k,d=n,this.options.backtrack_lexer){if(c=this.test_match(k,y[n]),c!==!1)return c;if(this._backtrack){f=!1;continue}else return!1}else if(!this.options.flex)break}return f?(c=this.test_match(f,y[d]),c!==!1?c:!1):this._input===""?this.EOF:this.parseError("Lexical error on line "+(this.yylineno+1)+`. Unrecognized text.
`+this.showPosition(),{text:"",token:null,line:this.yylineno})},"next"),lex:l(function(){var f=this.next();return f||this.lex()},"lex"),begin:l(function(f){this.conditionStack.push(f)},"begin"),popState:l(function(){var f=this.conditionStack.length-1;return f>0?this.conditionStack.pop():this.conditionStack[0]},"popState"),_currentRules:l(function(){return this.conditionStack.length&&this.conditionStack[this.conditionStack.length-1]?this.conditions[this.conditionStack[this.conditionStack.length-1]].rules:this.conditions.INITIAL.rules},"_currentRules"),topState:l(function(f){return f=this.conditionStack.length-1-Math.abs(f||0),f>=0?this.conditionStack[f]:"INITIAL"},"topState"),pushState:l(function(f){this.begin(f)},"pushState"),stateStackSize:l(function(){return this.conditionStack.length},"stateStackSize"),options:{"case-insensitive":!0},performAction:l(function(f,k,d,y){switch(d){case 0:return this.begin("open_directive"),"open_directive";case 1:return this.begin("acc_title"),31;case 2:return this.popState(),"acc_title_value";case 3:return this.begin("acc_descr"),33;case 4:return this.popState(),"acc_descr_value";case 5:this.begin("acc_descr_multiline");break;case 6:this.popState();break;case 7:return"acc_descr_multiline_value";case 8:break;case 9:break;case 10:break;case 11:return 10;case 12:break;case 13:break;case 14:this.begin("href");break;case 15:this.popState();break;case 16:return 43;case 17:this.begin("callbackname");break;case 18:this.popState();break;case 19:this.popState(),this.begin("callbackargs");break;case 20:return 41;case 21:this.popState();break;case 22:return 42;case 23:this.begin("click");break;case 24:this.popState();break;case 25:return 40;case 26:return 4;case 27:return 22;case 28:return 23;case 29:return 24;case 30:return 25;case 31:return 26;case 32:return 28;case 33:return 27;case 34:return 29;case 35:return 12;case 36:return 13;case 37:return 14;case 38:return 15;case 39:return 16;case 40:return 17;case 41:return 18;case 42:return 20;case 43:return 21;case 44:return"date";case 45:return 30;case 46:return"accDescription";case 47:return 36;case 48:return 38;case 49:return 39;case 50:return":";case 51:return 6;case 52:return"INVALID"}},"anonymous"),rules:[/^(?:%%\{)/i,/^(?:accTitle\s*:\s*)/i,/^(?:(?!\n||)*[^\n]*)/i,/^(?:accDescr\s*:\s*)/i,/^(?:(?!\n||)*[^\n]*)/i,/^(?:accDescr\s*\{\s*)/i,/^(?:[\}])/i,/^(?:[^\}]*)/i,/^(?:%%(?!\{)*[^\n]*)/i,/^(?:[^\}]%%*[^\n]*)/i,/^(?:%%*[^\n]*[\n]*)/i,/^(?:[\n]+)/i,/^(?:\s+)/i,/^(?:%[^\n]*)/i,/^(?:href[\s]+["])/i,/^(?:["])/i,/^(?:[^"]*)/i,/^(?:call[\s]+)/i,/^(?:\([\s]*\))/i,/^(?:\()/i,/^(?:[^(]*)/i,/^(?:\))/i,/^(?:[^)]*)/i,/^(?:click[\s]+)/i,/^(?:[\s\n])/i,/^(?:[^\s\n]*)/i,/^(?:gantt\b)/i,/^(?:dateFormat\s[^#\n;]+)/i,/^(?:inclusiveEndDates\b)/i,/^(?:topAxis\b)/i,/^(?:axisFormat\s[^#\n;]+)/i,/^(?:tickInterval\s[^#\n;]+)/i,/^(?:includes\s[^#\n;]+)/i,/^(?:excludes\s[^#\n;]+)/i,/^(?:todayMarker\s[^\n;]+)/i,/^(?:weekday\s+monday\b)/i,/^(?:weekday\s+tuesday\b)/i,/^(?:weekday\s+wednesday\b)/i,/^(?:weekday\s+thursday\b)/i,/^(?:weekday\s+friday\b)/i,/^(?:weekday\s+saturday\b)/i,/^(?:weekday\s+sunday\b)/i,/^(?:weekend\s+friday\b)/i,/^(?:weekend\s+saturday\b)/i,/^(?:\d\d\d\d-\d\d-\d\d\b)/i,/^(?:title\s[^\n]+)/i,/^(?:accDescription\s[^#\n;]+)/i,/^(?:section\s[^\n]+)/i,/^(?:[^:\n]+)/i,/^(?::[^#\n;]+)/i,/^(?::)/i,/^(?:$)/i,/^(?:.)/i],conditions:{acc_descr_multiline:{rules:[6,7],inclusive:!1},acc_descr:{rules:[4],inclusive:!1},acc_title:{rules:[2],inclusive:!1},callbackargs:{rules:[21,22],inclusive:!1},callbackname:{rules:[18,19,20],inclusive:!1},href:{rules:[15,16],inclusive:!1},click:{rules:[24,25],inclusive:!1},INITIAL:{rules:[0,1,3,5,8,9,10,11,12,13,14,17,23,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52],inclusive:!0}}};return _}();b.lexer=v;function m(){this.yy={}}return l(m,"Parser"),m.prototype=b,b.Parser=m,new m}();Et.parser=Et;var $e=Et;U.extend(Xe);U.extend(Ue);U.extend(Qe);var Jt={friday:5,saturday:6},tt="",Yt="",Wt=void 0,Vt="",ht=[],mt=[],Ot=new Map,zt=[],wt=[],ut="",Pt="",ae=["active","done","crit","milestone","vert"],Rt=[],kt=!1,Nt=!1,Bt="sunday",_t="saturday",Mt=0,Ke=l(function(){zt=[],wt=[],ut="",Rt=[],xt=0,It=void 0,Tt=void 0,H=[],tt="",Yt="",Pt="",Wt=void 0,Vt="",ht=[],mt=[],kt=!1,Nt=!1,Mt=0,Ot=new Map,xe(),Bt="sunday",_t="saturday"},"clear"),Je=l(function(t){Yt=t},"setAxisFormat"),tr=l(function(){return Yt},"getAxisFormat"),er=l(function(t){Wt=t},"setTickInterval"),rr=l(function(){return Wt},"getTickInterval"),nr=l(function(t){Vt=t},"setTodayMarker"),ir=l(function(){return Vt},"getTodayMarker"),sr=l(function(t){tt=t},"setDateFormat"),ar=l(function(){kt=!0},"enableInclusiveEndDates"),or=l(function(){return kt},"endDatesAreInclusive"),cr=l(function(){Nt=!0},"enableTopAxis"),lr=l(function(){return Nt},"topAxisEnabled"),ur=l(function(t){Pt=t},"setDisplayMode"),dr=l(function(){return Pt},"getDisplayMode"),fr=l(function(){return tt},"getDateFormat"),hr=l(function(t){ht=t.toLowerCase().split(/[\s,]+/)},"setIncludes"),mr=l(function(){return ht},"getIncludes"),kr=l(function(t){mt=t.toLowerCase().split(/[\s,]+/)},"setExcludes"),yr=l(function(){return mt},"getExcludes"),gr=l(function(){return Ot},"getLinks"),pr=l(function(t){ut=t,zt.push(t)},"addSection"),vr=l(function(){return zt},"getSections"),xr=l(function(){let t=te();const e=10;let i=0;for(;!t&&i<e;)t=te(),i++;return wt=H,wt},"getTasks"),oe=l(function(t,e,i,a){const s=t.format(e.trim()),h=t.format("YYYY-MM-DD");return a.includes(s)||a.includes(h)?!1:i.includes("weekends")&&(t.isoWeekday()===Jt[_t]||t.isoWeekday()===Jt[_t]+1)||i.includes(t.format("dddd").toLowerCase())?!0:i.includes(s)||i.includes(h)},"isInvalidDate"),Tr=l(function(t){Bt=t},"setWeekday"),br=l(function(){return Bt},"getWeekday"),wr=l(function(t){_t=t},"setWeekend"),ce=l(function(t,e,i,a){if(!i.length||t.manualEndTime)return;let s;t.startTime instanceof Date?s=U(t.startTime):s=U(t.startTime,e,!0),s=s.add(1,"d");let h;t.endTime instanceof Date?h=U(t.endTime):h=U(t.endTime,e,!0);const[u,D]=_r(s,h,e,i,a);t.endTime=u.toDate(),t.renderEndTime=D},"checkTaskDates"),_r=l(function(t,e,i,a,s){let h=!1,u=null;for(;t<=e;)h||(u=e.toDate()),h=oe(t,i,a,s),h&&(e=e.add(1,"d")),t=t.add(1,"d");return[e,u]},"fixTaskDates"),At=l(function(t,e,i){i=i.trim();const s=/^after\s+(?<ids>[\d\w- ]+)/.exec(i);if(s!==null){let u=null;for(const E of s.groups.ids.split(" ")){let C=it(E);C!==void 0&&(!u||C.endTime>u.endTime)&&(u=C)}if(u)return u.endTime;const D=new Date;return D.setHours(0,0,0,0),D}let h=U(i,e.trim(),!0);if(h.isValid())return h.toDate();{bt.debug("Invalid date:"+i),bt.debug("With date format:"+e.trim());const u=new Date(i);if(u===void 0||isNaN(u.getTime())||u.getFullYear()<-1e4||u.getFullYear()>1e4)throw new Error("Invalid date:"+i);return u}},"getStartDate"),le=l(function(t){const e=/^(\d+(?:\.\d+)?)([Mdhmswy]|ms)$/.exec(t.trim());return e!==null?[Number.parseFloat(e[1]),e[2]]:[NaN,"ms"]},"parseDuration"),ue=l(function(t,e,i,a=!1){i=i.trim();const h=/^until\s+(?<ids>[\d\w- ]+)/.exec(i);if(h!==null){let p=null;for(const S of h.groups.ids.split(" ")){let x=it(S);x!==void 0&&(!p||x.startTime<p.startTime)&&(p=x)}if(p)return p.startTime;const F=new Date;return F.setHours(0,0,0,0),F}let u=U(i,e.trim(),!0);if(u.isValid())return a&&(u=u.add(1,"d")),u.toDate();let D=U(t);const[E,C]=le(i);if(!Number.isNaN(E)){const p=D.add(E,C);p.isValid()&&(D=p)}return D.toDate()},"getEndDate"),xt=0,lt=l(function(t){return t===void 0?(xt=xt+1,"task"+xt):t},"parseId"),Dr=l(function(t,e){let i;e.substr(0,1)===":"?i=e.substr(1,e.length):i=e;const a=i.split(","),s={};Ht(a,s,ae);for(let u=0;u<a.length;u++)a[u]=a[u].trim();let h="";switch(a.length){case 1:s.id=lt(),s.startTime=t.endTime,h=a[0];break;case 2:s.id=lt(),s.startTime=At(void 0,tt,a[0]),h=a[1];break;case 3:s.id=lt(a[0]),s.startTime=At(void 0,tt,a[1]),h=a[2];break}return h&&(s.endTime=ue(s.startTime,tt,h,kt),s.manualEndTime=U(h,"YYYY-MM-DD",!0).isValid(),ce(s,tt,mt,ht)),s},"compileData"),Sr=l(function(t,e){let i;e.substr(0,1)===":"?i=e.substr(1,e.length):i=e;const a=i.split(","),s={};Ht(a,s,ae);for(let h=0;h<a.length;h++)a[h]=a[h].trim();switch(a.length){case 1:s.id=lt(),s.startTime={type:"prevTaskEnd",id:t},s.endTime={data:a[0]};break;case 2:s.id=lt(),s.startTime={type:"getStartDate",startData:a[0]},s.endTime={data:a[1]};break;case 3:s.id=lt(a[0]),s.startTime={type:"getStartDate",startData:a[1]},s.endTime={data:a[2]};break}return s},"parseData"),It,Tt,H=[],de={},Cr=l(function(t,e){const i={section:ut,type:ut,processed:!1,manualEndTime:!1,renderEndTime:null,raw:{data:e},task:t,classes:[]},a=Sr(Tt,e);i.raw.startTime=a.startTime,i.raw.endTime=a.endTime,i.id=a.id,i.prevTaskId=Tt,i.active=a.active,i.done=a.done,i.crit=a.crit,i.milestone=a.milestone,i.vert=a.vert,i.order=Mt,Mt++;const s=H.push(i);Tt=i.id,de[i.id]=s-1},"addTask"),it=l(function(t){const e=de[t];return H[e]},"findTaskById"),Er=l(function(t,e){const i={section:ut,type:ut,description:t,task:t,classes:[]},a=Dr(It,e);i.startTime=a.startTime,i.endTime=a.endTime,i.id=a.id,i.active=a.active,i.done=a.done,i.crit=a.crit,i.milestone=a.milestone,i.vert=a.vert,It=i,wt.push(i)},"addTaskOrg"),te=l(function(){const t=l(function(i){const a=H[i];let s="";switch(H[i].raw.startTime.type){case"prevTaskEnd":{const h=it(a.prevTaskId);a.startTime=h.endTime;break}case"getStartDate":s=At(void 0,tt,H[i].raw.startTime.startData),s&&(H[i].startTime=s);break}return H[i].startTime&&(H[i].endTime=ue(H[i].startTime,tt,H[i].raw.endTime.data,kt),H[i].endTime&&(H[i].processed=!0,H[i].manualEndTime=U(H[i].raw.endTime.data,"YYYY-MM-DD",!0).isValid(),ce(H[i],tt,mt,ht))),H[i].processed},"compileTask");let e=!0;for(const[i,a]of H.entries())t(i),e=e&&a.processed;return e},"compileTasks"),Mr=l(function(t,e){let i=e;ct().securityLevel!=="loose"&&(i=Te(e)),t.split(",").forEach(function(a){it(a)!==void 0&&(he(a,()=>{window.open(i,"_self")}),Ot.set(a,i))}),fe(t,"clickable")},"setLink"),fe=l(function(t,e){t.split(",").forEach(function(i){let a=it(i);a!==void 0&&a.classes.push(e)})},"setClass"),Ar=l(function(t,e,i){if(ct().securityLevel!=="loose"||e===void 0)return;let a=[];if(typeof i=="string"){a=i.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);for(let h=0;h<a.length;h++){let u=a[h].trim();u.startsWith('"')&&u.endsWith('"')&&(u=u.substr(1,u.length-2)),a[h]=u}}a.length===0&&a.push(t),it(t)!==void 0&&he(t,()=>{_e.runFunc(e,...a)})},"setClickFun"),he=l(function(t,e){Rt.push(function(){const i=document.querySelector(`[id="${t}"]`);i!==null&&i.addEventListener("click",function(){e()})},function(){const i=document.querySelector(`[id="${t}-text"]`);i!==null&&i.addEventListener("click",function(){e()})})},"pushFun"),Ir=l(function(t,e,i){t.split(",").forEach(function(a){Ar(a,e,i)}),fe(t,"clickable")},"setClickEvent"),Fr=l(function(t){Rt.forEach(function(e){e(t)})},"bindFunctions"),Lr={getConfig:l(()=>ct().gantt,"getConfig"),clear:Ke,setDateFormat:sr,getDateFormat:fr,enableInclusiveEndDates:ar,endDatesAreInclusive:or,enableTopAxis:cr,topAxisEnabled:lr,setAxisFormat:Je,getAxisFormat:tr,setTickInterval:er,getTickInterval:rr,setTodayMarker:nr,getTodayMarker:ir,setAccTitle:me,getAccTitle:ke,setDiagramTitle:ye,getDiagramTitle:ge,setDisplayMode:ur,getDisplayMode:dr,setAccDescription:pe,getAccDescription:ve,addSection:pr,getSections:vr,getTasks:xr,addTask:Cr,findTaskById:it,addTaskOrg:Er,setIncludes:hr,getIncludes:mr,setExcludes:kr,getExcludes:yr,setClickEvent:Ir,setLink:Mr,getLinks:gr,bindFunctions:Fr,parseDuration:le,isInvalidDate:oe,setWeekday:Tr,getWeekday:br,setWeekend:wr};function Ht(t,e,i){let a=!0;for(;a;)a=!1,i.forEach(function(s){const h="^\\s*"+s+"\\s*$",u=new RegExp(h);t[0].match(u)&&(e[s]=!0,t.shift(1),a=!0)})}l(Ht,"getTaskTags");var Yr=l(function(){bt.debug("Something is calling, setConf, remove the call")},"setConf"),ee={monday:Me,tuesday:Ae,wednesday:Ie,thursday:Fe,friday:Le,saturday:Ye,sunday:We},Wr=l((t,e)=>{let i=[...t].map(()=>-1/0),a=[...t].sort((h,u)=>h.startTime-u.startTime||h.order-u.order),s=0;for(const h of a)for(let u=0;u<i.length;u++)if(h.startTime>=i[u]){i[u]=h.endTime,h.order=u+e,u>s&&(s=u);break}return s},"getMaxIntersections"),et,Vr=l(function(t,e,i,a){const s=ct().gantt,h=ct().securityLevel;let u;h==="sandbox"&&(u=gt("#i"+e));const D=h==="sandbox"?gt(u.nodes()[0].contentDocument.body):gt("body"),E=h==="sandbox"?u.nodes()[0].contentDocument:document,C=E.getElementById(e);et=C.parentElement.offsetWidth,et===void 0&&(et=1200),s.useWidth!==void 0&&(et=s.useWidth);const p=a.db.getTasks();let F=[];for(const g of p)F.push(g.type);F=z(F);const S={};let x=2*s.topPadding;if(a.db.getDisplayMode()==="compact"||s.displayMode==="compact"){const g={};for(const b of p)g[b.section]===void 0?g[b.section]=[b]:g[b.section].push(b);let w=0;for(const b of Object.keys(g)){const v=Wr(g[b],w)+1;w+=v,x+=v*(s.barHeight+s.barGap),S[b]=v}}else{x+=p.length*(s.barHeight+s.barGap);for(const g of F)S[g]=p.filter(w=>w.type===g).length}C.setAttribute("viewBox","0 0 "+et+" "+x);const G=D.select(`[id="${e}"]`),A=De().domain([Se(p,function(g){return g.startTime}),Ce(p,function(g){return g.endTime})]).rangeRound([0,et-s.leftPadding-s.rightPadding]);function T(g,w){const b=g.startTime,v=w.startTime;let m=0;return b>v?m=1:b<v&&(m=-1),m}l(T,"taskCompare"),p.sort(T),M(p,et,x),be(G,x,et,s.useMaxWidth),G.append("text").text(a.db.getDiagramTitle()).attr("x",et/2).attr("y",s.titleTopMargin).attr("class","titleText");function M(g,w,b){const v=s.barHeight,m=v+s.barGap,_=s.topPadding,c=s.leftPadding,f=Ve().domain([0,F.length]).range(["#00B9FA","#F95002"]).interpolate(Ee);Y(m,_,c,w,b,g,a.db.getExcludes(),a.db.getIncludes()),N(c,_,w,b),L(g,m,_,c,v,f,w),R(m,_),j(c,_,w,b)}l(M,"makeGantt");function L(g,w,b,v,m,_,c){g.sort((o,r)=>o.vert===r.vert?0:o.vert?1:-1);const k=[...new Set(g.map(o=>o.order))].map(o=>g.find(r=>r.order===o));G.append("g").selectAll("rect").data(k).enter().append("rect").attr("x",0).attr("y",function(o,r){return r=o.order,r*w+b-2}).attr("width",function(){return c-s.rightPadding/2}).attr("height",w).attr("class",function(o){for(const[r,W]of F.entries())if(o.type===W)return"section section"+r%s.numberSectionStyles;return"section section0"}).enter();const d=G.append("g").selectAll("rect").data(g).enter(),y=a.db.getLinks();if(d.append("rect").attr("id",function(o){return o.id}).attr("rx",3).attr("ry",3).attr("x",function(o){return o.milestone?A(o.startTime)+v+.5*(A(o.endTime)-A(o.startTime))-.5*m:A(o.startTime)+v}).attr("y",function(o,r){return r=o.order,o.vert?s.gridLineStartPadding:r*w+b}).attr("width",function(o){return o.milestone?m:o.vert?.08*m:A(o.renderEndTime||o.endTime)-A(o.startTime)}).attr("height",function(o){return o.vert?p.length*(s.barHeight+s.barGap)+s.barHeight*2:m}).attr("transform-origin",function(o,r){return r=o.order,(A(o.startTime)+v+.5*(A(o.endTime)-A(o.startTime))).toString()+"px "+(r*w+b+.5*m).toString()+"px"}).attr("class",function(o){const r="task";let W="";o.classes.length>0&&(W=o.classes.join(" "));let I=0;for(const[X,O]of F.entries())o.type===O&&(I=X%s.numberSectionStyles);let V="";return o.active?o.crit?V+=" activeCrit":V=" active":o.done?o.crit?V=" doneCrit":V=" done":o.crit&&(V+=" crit"),V.length===0&&(V=" task"),o.milestone&&(V=" milestone "+V),o.vert&&(V=" vert "+V),V+=I,V+=" "+W,r+V}),d.append("text").attr("id",function(o){return o.id+"-text"}).text(function(o){return o.task}).attr("font-size",s.fontSize).attr("x",function(o){let r=A(o.startTime),W=A(o.renderEndTime||o.endTime);if(o.milestone&&(r+=.5*(A(o.endTime)-A(o.startTime))-.5*m,W=r+m),o.vert)return A(o.startTime)+v;const I=this.getBBox().width;return I>W-r?W+I+1.5*s.leftPadding>c?r+v-5:W+v+5:(W-r)/2+r+v}).attr("y",function(o,r){return o.vert?s.gridLineStartPadding+p.length*(s.barHeight+s.barGap)+60:(r=o.order,r*w+s.barHeight/2+(s.fontSize/2-2)+b)}).attr("text-height",m).attr("class",function(o){const r=A(o.startTime);let W=A(o.endTime);o.milestone&&(W=r+m);const I=this.getBBox().width;let V="";o.classes.length>0&&(V=o.classes.join(" "));let X=0;for(const[P,$]of F.entries())o.type===$&&(X=P%s.numberSectionStyles);let O="";return o.active&&(o.crit?O="activeCritText"+X:O="activeText"+X),o.done?o.crit?O=O+" doneCritText"+X:O=O+" doneText"+X:o.crit&&(O=O+" critText"+X),o.milestone&&(O+=" milestoneText"),o.vert&&(O+=" vertText"),I>W-r?W+I+1.5*s.leftPadding>c?V+" taskTextOutsideLeft taskTextOutside"+X+" "+O:V+" taskTextOutsideRight taskTextOutside"+X+" "+O+" width-"+I:V+" taskText taskText"+X+" "+O+" width-"+I}),ct().securityLevel==="sandbox"){let o;o=gt("#i"+e);const r=o.nodes()[0].contentDocument;d.filter(function(W){return y.has(W.id)}).each(function(W){var I=r.querySelector("#"+W.id),V=r.querySelector("#"+W.id+"-text");const X=I.parentNode;var O=r.createElement("a");O.setAttribute("xlink:href",y.get(W.id)),O.setAttribute("target","_top"),X.appendChild(O),O.appendChild(I),O.appendChild(V)})}}l(L,"drawRects");function Y(g,w,b,v,m,_,c,f){if(c.length===0&&f.length===0)return;let k,d;for(const{startTime:I,endTime:V}of _)(k===void 0||I<k)&&(k=I),(d===void 0||V>d)&&(d=V);if(!k||!d)return;if(U(d).diff(U(k),"year")>5){bt.warn("The difference between the min and max time is more than 5 years. This will cause performance issues. Skipping drawing exclude days.");return}const y=a.db.getDateFormat(),n=[];let o=null,r=U(k);for(;r.valueOf()<=d;)a.db.isInvalidDate(r,y,c,f)?o?o.end=r:o={start:r,end:r}:o&&(n.push(o),o=null),r=r.add(1,"d");G.append("g").selectAll("rect").data(n).enter().append("rect").attr("id",I=>"exclude-"+I.start.format("YYYY-MM-DD")).attr("x",I=>A(I.start.startOf("day"))+b).attr("y",s.gridLineStartPadding).attr("width",I=>A(I.end.endOf("day"))-A(I.start.startOf("day"))).attr("height",m-w-s.gridLineStartPadding).attr("transform-origin",function(I,V){return(A(I.start)+b+.5*(A(I.end)-A(I.start))).toString()+"px "+(V*g+.5*m).toString()+"px"}).attr("class","exclude-range")}l(Y,"drawExcludeDays");function N(g,w,b,v){const m=a.db.getDateFormat(),_=a.db.getAxisFormat();let c;_?c=_:m==="D"?c="%d":c=s.axisFormat??"%Y-%m-%d";let f=Ge(A).tickSize(-v+w+s.gridLineStartPadding).tickFormat(jt(c));const d=/^([1-9]\d*)(millisecond|second|minute|hour|day|week|month)$/.exec(a.db.getTickInterval()||s.tickInterval);if(d!==null){const y=d[1],n=d[2],o=a.db.getWeekday()||s.weekday;switch(n){case"millisecond":f.ticks($t.every(y));break;case"second":f.ticks(Qt.every(y));break;case"minute":f.ticks(Zt.every(y));break;case"hour":f.ticks(Ut.every(y));break;case"day":f.ticks(qt.every(y));break;case"week":f.ticks(ee[o].every(y));break;case"month":f.ticks(Xt.every(y));break}}if(G.append("g").attr("class","grid").attr("transform","translate("+g+", "+(v-50)+")").call(f).selectAll("text").style("text-anchor","middle").attr("fill","#000").attr("stroke","none").attr("font-size",10).attr("dy","1em"),a.db.topAxisEnabled()||s.topAxis){let y=He(A).tickSize(-v+w+s.gridLineStartPadding).tickFormat(jt(c));if(d!==null){const n=d[1],o=d[2],r=a.db.getWeekday()||s.weekday;switch(o){case"millisecond":y.ticks($t.every(n));break;case"second":y.ticks(Qt.every(n));break;case"minute":y.ticks(Zt.every(n));break;case"hour":y.ticks(Ut.every(n));break;case"day":y.ticks(qt.every(n));break;case"week":y.ticks(ee[r].every(n));break;case"month":y.ticks(Xt.every(n));break}}G.append("g").attr("class","grid").attr("transform","translate("+g+", "+w+")").call(y).selectAll("text").style("text-anchor","middle").attr("fill","#000").attr("stroke","none").attr("font-size",10)}}l(N,"makeGrid");function R(g,w){let b=0;const v=Object.keys(S).map(m=>[m,S[m]]);G.append("g").selectAll("text").data(v).enter().append(function(m){const _=m[0].split(we.lineBreakRegex),c=-(_.length-1)/2,f=E.createElementNS("http://www.w3.org/2000/svg","text");f.setAttribute("dy",c+"em");for(const[k,d]of _.entries()){const y=E.createElementNS("http://www.w3.org/2000/svg","tspan");y.setAttribute("alignment-baseline","central"),y.setAttribute("x","10"),k>0&&y.setAttribute("dy","1em"),y.textContent=d,f.appendChild(y)}return f}).attr("x",10).attr("y",function(m,_){if(_>0)for(let c=0;c<_;c++)return b+=v[_-1][1],m[1]*g/2+b*g+w;else return m[1]*g/2+w}).attr("font-size",s.sectionFontSize).attr("class",function(m){for(const[_,c]of F.entries())if(m[0]===c)return"sectionTitle sectionTitle"+_%s.numberSectionStyles;return"sectionTitle"})}l(R,"vertLabels");function j(g,w,b,v){const m=a.db.getTodayMarker();if(m==="off")return;const _=G.append("g").attr("class","today"),c=new Date,f=_.append("line");f.attr("x1",A(c)+g).attr("x2",A(c)+g).attr("y1",s.titleTopMargin).attr("y2",v-s.titleTopMargin).attr("class","today"),m!==""&&f.attr("style",m.replace(/,/g,";"))}l(j,"drawToday");function z(g){const w={},b=[];for(let v=0,m=g.length;v<m;++v)Object.prototype.hasOwnProperty.call(w,g[v])||(w[g[v]]=!0,b.push(g[v]));return b}l(z,"checkUnique")},"draw"),Or={setConf:Yr,draw:Vr},zr=l(t=>`
  .mermaid-main-font {
        font-family: ${t.fontFamily};
  }

  .exclude-range {
    fill: ${t.excludeBkgColor};
  }

  .section {
    stroke: none;
    opacity: 0.2;
  }

  .section0 {
    fill: ${t.sectionBkgColor};
  }

  .section2 {
    fill: ${t.sectionBkgColor2};
  }

  .section1,
  .section3 {
    fill: ${t.altSectionBkgColor};
    opacity: 0.2;
  }

  .sectionTitle0 {
    fill: ${t.titleColor};
  }

  .sectionTitle1 {
    fill: ${t.titleColor};
  }

  .sectionTitle2 {
    fill: ${t.titleColor};
  }

  .sectionTitle3 {
    fill: ${t.titleColor};
  }

  .sectionTitle {
    text-anchor: start;
    font-family: ${t.fontFamily};
  }


  /* Grid and axis */

  .grid .tick {
    stroke: ${t.gridColor};
    opacity: 0.8;
    shape-rendering: crispEdges;
  }

  .grid .tick text {
    font-family: ${t.fontFamily};
    fill: ${t.textColor};
  }

  .grid path {
    stroke-width: 0;
  }


  /* Today line */

  .today {
    fill: none;
    stroke: ${t.todayLineColor};
    stroke-width: 2px;
  }


  /* Task styling */

  /* Default task */

  .task {
    stroke-width: 2;
  }

  .taskText {
    text-anchor: middle;
    font-family: ${t.fontFamily};
  }

  .taskTextOutsideRight {
    fill: ${t.taskTextDarkColor};
    text-anchor: start;
    font-family: ${t.fontFamily};
  }

  .taskTextOutsideLeft {
    fill: ${t.taskTextDarkColor};
    text-anchor: end;
  }


  /* Special case clickable */

  .task.clickable {
    cursor: pointer;
  }

  .taskText.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }

  .taskTextOutsideLeft.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }

  .taskTextOutsideRight.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }


  /* Specific task settings for the sections*/

  .taskText0,
  .taskText1,
  .taskText2,
  .taskText3 {
    fill: ${t.taskTextColor};
  }

  .task0,
  .task1,
  .task2,
  .task3 {
    fill: ${t.taskBkgColor};
    stroke: ${t.taskBorderColor};
  }

  .taskTextOutside0,
  .taskTextOutside2
  {
    fill: ${t.taskTextOutsideColor};
  }

  .taskTextOutside1,
  .taskTextOutside3 {
    fill: ${t.taskTextOutsideColor};
  }


  /* Active task */

  .active0,
  .active1,
  .active2,
  .active3 {
    fill: ${t.activeTaskBkgColor};
    stroke: ${t.activeTaskBorderColor};
  }

  .activeText0,
  .activeText1,
  .activeText2,
  .activeText3 {
    fill: ${t.taskTextDarkColor} !important;
  }


  /* Completed task */

  .done0,
  .done1,
  .done2,
  .done3 {
    stroke: ${t.doneTaskBorderColor};
    fill: ${t.doneTaskBkgColor};
    stroke-width: 2;
  }

  .doneText0,
  .doneText1,
  .doneText2,
  .doneText3 {
    fill: ${t.taskTextDarkColor} !important;
  }


  /* Tasks on the critical line */

  .crit0,
  .crit1,
  .crit2,
  .crit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.critBkgColor};
    stroke-width: 2;
  }

  .activeCrit0,
  .activeCrit1,
  .activeCrit2,
  .activeCrit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.activeTaskBkgColor};
    stroke-width: 2;
  }

  .doneCrit0,
  .doneCrit1,
  .doneCrit2,
  .doneCrit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.doneTaskBkgColor};
    stroke-width: 2;
    cursor: pointer;
    shape-rendering: crispEdges;
  }

  .milestone {
    transform: rotate(45deg) scale(0.8,0.8);
  }

  .milestoneText {
    font-style: italic;
  }
  .doneCritText0,
  .doneCritText1,
  .doneCritText2,
  .doneCritText3 {
    fill: ${t.taskTextDarkColor} !important;
  }

  .vert {
    stroke: ${t.vertLineColor};
  }

  .vertText {
    font-size: 15px;
    text-anchor: middle;
    fill: ${t.vertLineColor} !important;
  }

  .activeCritText0,
  .activeCritText1,
  .activeCritText2,
  .activeCritText3 {
    fill: ${t.taskTextDarkColor} !important;
  }

  .titleText {
    text-anchor: middle;
    font-size: 18px;
    fill: ${t.titleColor||t.textColor};
    font-family: ${t.fontFamily};
  }
`,"getStyles"),Pr=zr,jr={parser:$e,db:Lr,renderer:Or,styles:Pr};export{jr as diagram};
//# sourceMappingURL=ganttDiagram-WV7ZQ7D5.CDkbSQZN.js.map
