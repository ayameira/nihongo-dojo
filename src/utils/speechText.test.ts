import { describe, it, expect } from 'vitest';
import { cleanTextForSpeech } from './speechText';

describe('cleanTextForSpeech', () => {
  it('leaves plain text untouched', () => {
    expect(cleanTextForSpeech('こんにちは、元気ですか？')).toBe('こんにちは、元気ですか？');
  });

  it('strips bold markers', () => {
    expect(cleanTextForSpeech('The word **taberu** means to eat')).toBe(
      'The word taberu means to eat'
    );
    expect(cleanTextForSpeech('__strong__ statement')).toBe('strong statement');
  });

  it('strips italic markers', () => {
    expect(cleanTextForSpeech('This is *very* important')).toBe('This is very important');
    expect(cleanTextForSpeech('This is _very_ important')).toBe('This is very important');
  });

  it('strips bold-italic markers', () => {
    expect(cleanTextForSpeech('***wow*** and ___whoa___')).toBe('wow and whoa');
  });

  it('handles bold on Japanese text', () => {
    expect(cleanTextForSpeech('「**食べる**」は "to eat" という意味です')).toBe(
      '「食べる」は "to eat" という意味です'
    );
  });

  it('keeps snake_case words intact', () => {
    expect(cleanTextForSpeech('call update_student_record here')).toBe(
      'call update_student_record here'
    );
  });

  it('strips inline code backticks', () => {
    expect(cleanTextForSpeech('Use `desu` at the end')).toBe('Use desu at the end');
  });

  it('unwraps fenced code blocks', () => {
    expect(cleanTextForSpeech('```text\n食べます\n```')).toBe('食べます');
  });

  it('keeps link labels and drops URLs', () => {
    expect(cleanTextForSpeech('See [this guide](https://example.com/guide)')).toBe(
      'See this guide'
    );
  });

  it('keeps image alt text', () => {
    expect(cleanTextForSpeech('![a cat](https://example.com/cat.png)')).toBe('a cat');
  });

  it('strips strikethrough markers', () => {
    expect(cleanTextForSpeech('~~wrong~~ right')).toBe('wrong right');
  });

  it('strips heading markers', () => {
    expect(cleanTextForSpeech('## Vocabulary\nSome words')).toBe('Vocabulary\nSome words');
  });

  it('strips blockquote markers', () => {
    expect(cleanTextForSpeech('> 猫が好きです')).toBe('猫が好きです');
  });

  it('strips list markers', () => {
    expect(cleanTextForSpeech('- 犬\n- 猫\n1. first\n2. second')).toBe(
      '犬\n猫\nfirst\nsecond'
    );
  });

  it('turns table rows into comma-paused text and drops separators', () => {
    expect(cleanTextForSpeech('| 日本語 | English |\n| --- | --- |\n| 犬 | dog |')).toBe(
      '日本語, English\n犬, dog'
    );
  });

  it('removes horizontal rules', () => {
    expect(cleanTextForSpeech('above\n\n---\n\nbelow')).toBe('above\n\nbelow');
  });

  it('handles nested formatting', () => {
    expect(cleanTextForSpeech('**bold with *italic* inside**')).toBe(
      'bold with italic inside'
    );
  });

  it('does not treat multiplication or lone asterisks as formatting', () => {
    expect(cleanTextForSpeech('2 * 3 = 6')).toBe('2 * 3 = 6');
  });
});
