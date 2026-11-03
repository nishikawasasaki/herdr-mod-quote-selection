import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import test from 'node:test';

const source = (await readFile(new URL('./main.js', import.meta.url), 'utf8'))
  .replace(/^import .*;$/gm, '')
  .replace('export default class Annotation', 'globalThis.Annotation = class Annotation');

function setup(terminal, exec) {
  const tasks = [], closed = [], commands = [], notifications = [];
  const context = vm.createContext({
    View: class {}, focused: () => ({ terminal }),
    props: () => ({ overlay: 'annotation' }), appHome: () => '/app', exec,
    closeOverlay: id => closed.push(id), run: (...args) => commands.push(args),
    notify: note => notifications.push(note),
  });
  vm.runInContext(source, context);
  const mod = new context.Annotation();
  const cx = { notify() {}, spawn(f) { tasks.push(f(cx)); } };
  return { mod, cx, tasks, closed, commands, notifications, focus(value) { terminal = value; } };
}

test('shortcut reads UTF-8 and keeps its original terminal across focus changes', async () => {
  const calls = [];
  let finish;
  const selection = new Promise(resolve => { finish = resolve; });
  const s = setup('selected', async (...args) => {
    calls.push(args);
    return calls.length === 1 ? selection : { code: 0 };
  });
  s.mod.init({}, s.cx);
  s.focus('other');
  finish({ code: 0, stdout: '日本語の引用ＡＢ😀' });
  await Promise.all(s.tasks);
  assert.deepEqual(JSON.parse(JSON.stringify(calls)), [
    ['/usr/bin/env', ['LC_ALL=en_US.UTF-8', '/usr/bin/pbpaste']],
    ['python3', ['/app/mods/quote-selection/quote.py', '--', 'selected', '日本語の引用ＡＢ😀']],
  ]);
  assert.deepEqual(s.closed, ['annotation']);
  assert.equal(s.commands[0][1].terminal, 'selected');
  assert.deepEqual(s.notifications, []);
});

test('no focused terminal does not read clipboard or paste', () => {
  const s = setup(null, () => assert.fail('unexpected execution'));
  s.mod.init({}, s.cx);
  assert.match(s.mod.error, /ターミナル/);
  assert.equal(s.tasks.length, 0);
  assert.equal(s.notifications[0].level, 'error');
});

test('clipboard failure does not invoke the insertion helper', async () => {
  let calls = 0;
  const s = setup('selected', async () => { calls++; return { code: 1 }; });
  s.mod.init({}, s.cx);
  await Promise.all(s.tasks);
  assert.equal(calls, 1);
  assert.match(s.mod.error, /読み取れません/);
  assert.deepEqual(s.closed, ['annotation']);
  assert.equal(s.notifications[0].body, s.mod.error);
});
