const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {"start":"_app/immutable/entry/start.bFX3RwUH.js","app":"_app/immutable/entry/app.CEv0s9UE.js","imports":["_app/immutable/entry/start.bFX3RwUH.js","_app/immutable/chunks/client.CZs4mqb7.js","_app/immutable/entry/app.CEv0s9UE.js","_app/immutable/chunks/preload-helper.D6kgxu3v.js"],"stylesheets":[],"fonts":[],"uses_env_dynamic_public":false},
		nodes: [
			__memo(() => import('./chunks/0-DijfUwFQ.js')),
			__memo(() => import('./chunks/1-BSUGQSKm.js')),
			__memo(() => import('./chunks/2-2QjpS3e7.js').then(function (n) { return n.aG; }))
		],
		routes: [
			{
				id: "/[...catchall]",
				pattern: /^(?:\/(.*))?\/?$/,
				params: [{"name":"catchall","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();

const prerendered = new Set([]);

const base = "";

export { base, manifest, prerendered };
//# sourceMappingURL=manifest.js.map
