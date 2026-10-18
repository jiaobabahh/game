/* Python runs in a dedicated worker so verification cannot freeze the page. */
let runtime;
const checkedFetch = async path => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`文件加载失败：${path} (${response.status})`);
  return response;
};
async function initialize() {
  postMessage({type: 'status', text: '正在加载核验引擎，首次访问约需下载 18 MB…'});
  importScripts('./vendor/pyodide.js');
  const py = await loadPyodide({indexURL: new URL('./vendor/', self.location.href).href});
  postMessage({type: 'status', text: '正在准备符号计算与图论模块…'});
  const packages = await (await checkedFetch('./vendor/packages.json')).json();
  py.FS.mkdirTree('/packages');
  for (const name of packages) {
    const bytes = await (await checkedFetch('./vendor/' + name)).arrayBuffer();
    py.unpackArchive(bytes, 'zip', {extractDir: '/packages'});
  }
  py.FS.mkdirTree('/app/dmverify');
  const names = ['__init__', 'prop', 'sets_engine', 'rels', 'graphs', 'autodissect', 'cases', 'runner'];
  await Promise.all(names.map(async name => {
    py.FS.writeFile('/app/dmverify/' + name + '.py', await (await checkedFetch('./engine/' + name + '.py')).text());
  }));
  py.FS.writeFile('/app/bridge.py', await (await checkedFetch('./bridge.py')).text());
  py.runPython("import sys; sys.path[:0] = ['/app', '/packages']\nfrom bridge import handle\nfrom dmverify.autodissect import PRESETS");
  postMessage({type: 'ready', presets: JSON.parse(py.runPython('import json; json.dumps(PRESETS, ensure_ascii=False)'))});
  return py;
}
onmessage = async ({data}) => {
  try {
    runtime ??= initialize();
    const py = await runtime;
    if (data.type === 'init') return;
    py.globals.set('browser_input', JSON.stringify(data.payload));
    const result = JSON.parse(py.runPython('handle(browser_input)'));
    py.globals.delete('browser_input');
    if (result._error) throw new Error(result._error);
    postMessage({type: 'result', id: data.id, result});
  } catch (error) {
    postMessage({type: 'error', id: data.id, text: String(error.message || error)});
  }
};
