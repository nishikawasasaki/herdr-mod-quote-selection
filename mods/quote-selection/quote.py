#!/usr/bin/env python3
"""Insert a quoted reply through hc attach, without submitting it."""
import argparse
import fcntl
import json
import os
import pty
import re
import select
import struct
import subprocess
import termios
import time


def quote_text(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if not text.strip():
        raise ValueError('文章を選択してから Quote Selection を実行してください。')
    if any(ord(c) < 32 and c not in '\n\t' or ord(c) == 127 for c in text):
        raise ValueError('選択文に端末の制御文字が含まれています。')
    return '\n'.join('> ' + line for line in text.split('\n')) + '\n\n'


def reply_bytes(quoted, has_draft):
    # Separate lines keep Claude's multiline-paste chip from swallowing the reply cursor.
    lines = [b'\x1b[200~' + line.encode() + b'\x1b[201~' for line in quoted[:-2].split('\n')]
    return (b'\n' if has_draft else b'') + b'\n'.join(lines) + b'\n\n'


def cli(*args):
    result = subprocess.run(['hc', *args], capture_output=True, text=True, timeout=5)
    if result.returncode:
        raise RuntimeError('対象のターミナルを取得できません。')
    return result.stdout


def composer_has_text(screen, app, cursor=None):
    marker = '›' if app == 'codex' else '❯'
    lines = screen.splitlines()
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith(marker)]
    if not starts:
        raise RuntimeError('入力欄が見つかりません。通常の入力画面で実行してください。')
    start = starts[-1]
    if cursor is not None and cursor != (start + 1, 3):
        return True
    first = lines[start].lstrip()[1:].strip()
    if app == 'codex' and first == 'Ask Codex to do anything':
        return False
    if first:
        return True
    return any(line.strip() for line in lines[start + 1:composer_end_row(screen, app)])


def composer_end_row(screen, app):
    lines = screen.splitlines()
    marker = '›' if app == 'codex' else '❯'
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith(marker)]
    if not starts:
        raise RuntimeError('入力欄が見つかりません。')
    for i in range(len(lines) - 1, starts[-1], -1):
        if app == 'codex' and ('Context ' in lines[i] or 'context left' in lines[i]):
            return i - 1
        if app != 'codex' and re.fullmatch(r'[─━]{3,}', lines[i].strip()):
            return i
    raise RuntimeError('入力欄の末尾を取得できませんでした。')


def composer_text(screen, app):
    lines = screen.splitlines()
    marker = '›' if app == 'codex' else '❯'
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith(marker)]
    if not starts:
        raise RuntimeError('入力欄が見つかりません。')
    return '\n'.join(lines[starts[-1]:composer_end_row(screen, app)])


class AttachedTerminal:
    def __init__(self, address, cols, rows):
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        self.process = subprocess.Popen(['hc', 'attach', address], stdin=slave,
                                        stdout=slave, stderr=slave, start_new_session=True,
                                        preexec_fn=lambda: fcntl.ioctl(0, termios.TIOCSCTTY, 0))
        os.close(slave)
        self.cursor = None

    def drain(self):
        deadline = time.monotonic() + (2 if self.cursor is None else 0.5)
        blocks = []
        display_answered = False
        while time.monotonic() < deadline:
            if not select.select([self.master], [], [], 0.06)[0]:
                if blocks and (self.cursor is not None or re.search(rb'\x1b\[\d+;\d+[Hf]', b''.join(blocks))):
                    break
                continue
            try:
                block = os.read(self.master, 65536)
            except OSError:
                break
            if not block:
                break
            blocks.append(block)
            # hc waits 500 ms for the outer terminal's DA1 reply before attaching.
            if self.cursor is None and not display_answered and b'\x1b[c' in b''.join(blocks):
                self.write(b'\x1b[?1;2c')
                display_answered = True
        data = b''.join(blocks)
        positions = re.findall(rb'\x1b\[(\d+);(\d+)[Hf]', data)
        if positions:
            self.cursor = tuple(map(int, positions[-1]))
        if self.process.poll() is not None:
            raise RuntimeError('対象のターミナルへの接続が終了しました。')
        return self.cursor

    def write(self, data):
        remaining = memoryview(data)
        while remaining:
            written = os.write(self.master, remaining)
            if written <= 0:
                raise RuntimeError('入力を送れなかったため、処理を中止しました。')
            remaining = remaining[written:]

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        os.close(self.master)


def annotate(address, text):
    quoted = quote_text(text)
    terminal = json.loads(cli('get', address))
    status = terminal.get('status') or {}
    if not isinstance(status, dict):
        status = {}
    app = status.get('app', '')
    if app not in ('codex', 'claude-code', 'claude'):
        raise RuntimeError('Claude Code または Codex の入力欄で実行してください。')
    if status.get('state') not in ('idle', 'done', 'working'):
        raise RuntimeError('確認ダイアログを閉じ、通常の入力画面で実行してください。')
    attached = AttachedTerminal(address, terminal['cols'], terminal['rows'])
    try:
        attached.drain()
        if attached.cursor is None:
            raise RuntimeError('入力位置を取得できませんでした。')
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            before = (attached.cursor, cli('read', address))
            attached.write(b'\x05')
            attached.drain()
            after = (attached.cursor, cli('read', address))
            # A response can stream above the draft without changing the input.
            if before[0] == after[0] and composer_text(before[1], app) == composer_text(after[1], app):
                if attached.cursor[0] < composer_end_row(after[1], app):
                    attached.write(b'\x1b[B')
                    attached.drain()
                    continue
                break
        else:
            raise RuntimeError('入力末尾へ移動できなかったため、引用は追加していません。')
        attached.write(reply_bytes(quoted, composer_has_text(after[1], app, attached.cursor)))
        attached.drain()
    finally:
        attached.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('terminal')
    parser.add_argument('text')
    args = parser.parse_args()
    try:
        annotate(args.terminal, args.text)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(str(error))
        raise SystemExit(1)
