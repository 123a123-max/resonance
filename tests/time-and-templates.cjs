const assert = require('node:assert/strict');
const fs = require('node:fs');
async function main() {
const {createServer} = await import('vite');
const server = await createServer({server: {middlewareMode: true, hmr: false}, appType: 'custom'});
try {
const {parseServerTime, diaryDate, uploadTime} = await server.ssrLoadModule('/src/time.ts');
const utc = Date.parse('2026-11-21T04:57:00Z');
assert.equal(parseServerTime('2026-11-21T04:57:00'), utc);
assert.equal(parseServerTime('2026-11-21 04:57:00.000000'), utc);
assert.equal(parseServerTime('2026-11-21T12:57:00+08:00'), utc);
assert.equal(uploadTime(utc), '12:57');
assert.equal(diaryDate(Date.parse('2026-11-20T16:01:00Z')), '2026-11-21');
assert.equal(diaryDate(Date.parse('2026-11-20T15:59:00Z')), '2026-11-20');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const {ScrapbookDiary, isScrapbookTemplate} = await server.ssrLoadModule('/src/ScrapbookDiary.tsx');
const moments = Array.from({length: 7}, (_, i) => ({id: String(i), memberId: '1', kind: i === 6 ? 'video' : 'image', media: '/test.jpg', caption: `记忆 ${i} <script>`, createdAt: utc}));
for (const theme of ['a', 'f', 'g', 'h']) {
  assert.equal(isScrapbookTemplate(theme), true);
  const html = renderToStaticMarkup(React.createElement(ScrapbookDiary, {theme, moments, urls: {}, date: '2026-11-21', onPreview() {}}));
  assert.equal((html.match(/aria-label="手帐第/g) || []).length, 2);
  assert.equal((html.match(/<figure/g) || []).length, 7);
  assert.ok(html.includes('12:57'));
  assert.ok(html.includes('2026 / 11 / 21'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.equal((html.match(/<video/g) || []).length, 1);
  assert.ok(renderToStaticMarkup(React.createElement(ScrapbookDiary, {theme, moments: [], urls: {}, onPreview() {}})).includes('从一张照片开始'));
}
assert.equal(isScrapbookTemplate('custom'), false);
console.log('PASS: legacy/new UTC timestamps, Beijing midnight, 4 templates, pagination, video, empty states and escaped captions');

} finally { await server.close(); }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
