import unittest
from unittest.mock import Mock, patch
from quote import AttachedTerminal, annotate, composer_end_row, composer_has_text, quote_text, reply_bytes


class QuoteTests(unittest.TestCase):
    def test_multiline_quote_leaves_reply_line(self):
        self.assertEqual(quote_text('一行目\r\n\r\n二行目'), '> 一行目\n> \n> 二行目\n\n')

    def test_empty_selection_and_escape_sequences_are_rejected(self):
        for text in ('  \n', '\x1b[201~danger', '\x00'):
            with self.subTest(text=repr(text)), self.assertRaises(ValueError):
                quote_text(text)

    def test_reply_lines_use_newline_keys_without_submit(self):
        data = reply_bytes(quote_text('a\nb'), True)
        self.assertEqual(data, b'\n\x1b[200~> a\x1b[201~\n\x1b[200~> b\x1b[201~\n\n')
        self.assertNotIn(b'\r', data)

    def test_empty_and_existing_composers(self):
        self.assertFalse(composer_has_text('─' * 12 + '\n❯ \n' + '─' * 12, 'claude-code'))
        self.assertTrue(composer_has_text('❯ first\n  second\n────────', 'claude-code'))
        self.assertTrue(composer_has_text('❯ \n\n  third\n────────', 'claude-code'))
        self.assertFalse(composer_has_text('› \n\n GPT-6 · Context 0% used', 'codex'))
        self.assertFalse(composer_has_text('› Ask Codex to do anything\n\n GPT-6 · Context 0% used', 'codex'))
        self.assertTrue(composer_has_text('› Ask Codex to do anything\n\n GPT-6 · Context 0% used', 'codex', (1, 27)))
        self.assertTrue(composer_has_text('› \n\n\n GPT-6 · Context 0% used', 'codex', (2, 3)))
        self.assertTrue(composer_has_text('› first\n  second\n\n GPT-6', 'codex'))

    def test_missing_composer_does_not_guess(self):
        with self.assertRaises(RuntimeError):
            composer_has_text('Permission required', 'codex')

    def test_end_row_does_not_include_footer_or_border(self):
        self.assertEqual(composer_end_row('────────\n❯ first\n  second\n────────', 'claude-code'), 3)
        self.assertEqual(composer_end_row('› first\n  second\n\n GPT-6 · Context 0% used', 'codex'), 2)
        self.assertEqual(composer_end_row('› Context example\n  Context in a quote\n\n GPT-6 · Context 0% used', 'codex'), 2)
        self.assertEqual(composer_end_row('────────\n❯ first\n  ────────\n  last\n────────', 'claude-code'), 4)

    def test_partial_terminal_write_keeps_remaining_bytes(self):
        terminal = AttachedTerminal.__new__(AttachedTerminal)
        terminal.master = 99
        with patch('quote.os.write', side_effect=[1, 2]) as write:
            terminal.write(b'abc')
        self.assertEqual([bytes(call.args[1]) for call in write.call_args_list], [b'abc', b'bc'])

    def test_attach_display_query_is_answered_before_first_paint(self):
        terminal = AttachedTerminal.__new__(AttachedTerminal)
        terminal.master = 99
        terminal.cursor = None
        terminal.process = Mock()
        terminal.process.poll.return_value = None
        with patch('quote.select.select', side_effect=[([99], [], [])] * 3 + [([], [], [])]), \
             patch('quote.os.read', side_effect=[b'\x1b[', b'c', b'\x1b[24;3H']), \
             patch.object(terminal, 'write') as write:
            self.assertEqual(terminal.drain(), (24, 3))
        write.assert_called_once_with(b'\x1b[?1;2c')

    def test_streaming_agent_can_receive_an_unsent_quote(self):
        terminal = '{"status":{"app":"codex","state":"working"},"cols":80,"rows":24}'
        before = 'response before\n› \n\n GPT-6 · Context 0% used'
        after = 'response streaming\n› \n\n GPT-6 · Context 0% used'
        with patch('quote.cli', side_effect=[terminal, before, after]), patch('quote.AttachedTerminal') as attach:
            attach.return_value.cursor = (2, 3)
            annotate('target', 'selected text')
        self.assertEqual([c.args[0] for c in attach.return_value.write.call_args_list],
                         [b'\x05', reply_bytes(quote_text('selected text'), False)])


if __name__ == '__main__':
    unittest.main()
