/**
 * Strip markdown formatting from text before sending it to TTS, so
 * engines don't read out literal syntax ("asterisk asterisk word...").
 * Keeps the human-readable content: bold/italic markers are dropped,
 * link labels are kept, code fences are removed but code text is kept.
 */
export function cleanTextForSpeech(text: string): string {
  let result = text;

  // Fenced code blocks: drop the fences and language tag, keep the code
  result = result.replace(/```[^\n]*\n?([\s\S]*?)```/g, '$1');

  // Inline code
  result = result.replace(/`([^`]+)`/g, '$1');

  // Images: speak the alt text
  result = result.replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1');

  // Links: speak the label, not the URL
  result = result.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1');

  // Bold+italic, bold, then italic (order matters so ** isn't eaten as *)
  result = result.replace(/(\*\*\*|___)(?=\S)([\s\S]*?\S)\1/g, '$2');
  result = result.replace(/(\*\*|__)(?=\S)([\s\S]*?\S)\1/g, '$2');
  result = result.replace(/\*(?=\S)([^*]*\S)\*/g, '$1');
  // Underscore italic only at word edges, so snake_case survives
  result = result.replace(/(?<![\w_])_(?=\S)([^_]*\S)_(?![\w_])/g, '$1');

  // Strikethrough
  result = result.replace(/~~(?=\S)([\s\S]*?\S)~~/g, '$1');

  // Headings
  result = result.replace(/^#{1,6}\s+/gm, '');

  // Blockquote markers
  result = result.replace(/^\s*>\s?/gm, '');

  // Table separator rows (|---|:---:|), then pipes become pauses
  result = result.replace(/^\s*\|?[\s:|-]+\|[\s:|-]*$/gm, '');
  result = result
    .replace(/^\s*\|\s*/gm, '')
    .replace(/\s*\|\s*$/gm, '')
    .replace(/\s*\|\s*/g, ', ');

  // Horizontal rules
  result = result.replace(/^ {0,3}([-*_])( ?\1){2,}\s*$/gm, '');

  // List markers (unordered and ordered)
  result = result.replace(/^(\s*)[-*+]\s+/gm, '$1');
  result = result.replace(/^(\s*)\d+[.)]\s+/gm, '$1');

  // Collapse leftover blank lines and trim
  result = result.replace(/\n{3,}/g, '\n\n');

  return result.trim();
}
