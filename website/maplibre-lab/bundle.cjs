/* Dev-only bundler. Dependencies live in an isolated directory, never in the app. */
const path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'../..'),vendor=path.resolve(process.env.HEATWATER_MAPLIBRE_VENDOR||(fs.existsSync(path.join(__dirname,'node_modules/maplibre-gl'))?__dirname:path.join(root,'artifacts/maplibre-runtime')));
const esbuild=require(path.join(vendor,'node_modules/esbuild'));
for(const [entry,name,globalName]of [['maplibre-gl.mjs','maplibre.js','maplibregl'],['maplibre-gl-worker.mjs','worker.js',undefined]]){
 esbuild.buildSync({absWorkingDir:root,entryPoints:[path.join(vendor,'node_modules/maplibre-gl/dist',entry)],bundle:true,format:'iife',globalName,platform:'browser',outfile:path.join(vendor,'bundle',name),minify:true});
}
console.log('MapLibre and worker bundles ready');
