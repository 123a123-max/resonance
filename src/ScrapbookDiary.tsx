import {useState} from 'react';
import {diaryDate, uploadTime} from './time';
import './scrapbook.css';

export const scrapbookThemes = {
  a: {title: '把日子，慢慢收藏', subtitle: 'LITTLE MOMENTS / 生活手帐', note: '平凡的一天，也有值得留住的光。'},
  f: {title: '拾起一页秋天', subtitle: 'AUTUMN NOTES / 秋日手帐', note: '把暖色的片刻，贴进我们的日记。'},
  g: {title: '沿途都是好时光', subtitle: 'ON THE ROAD / 胶片旅行', note: '下一站，和你一起。'},
  h: {title: '日子自有四季', subtitle: 'SEASON BY SEASON / 四季拼贴', note: '把每个季节，过成喜欢的样子。'},
} as const;
export function isScrapbookTemplate(value: string): value is keyof typeof scrapbookThemes {
  return Object.prototype.hasOwnProperty.call(scrapbookThemes, value);
}
type PhotoMoment = {memberId: string; id: string; kind: 'image'|'video'; media?: string; assetId?: string; caption: string; createdAt: number};
type Props = {theme: keyof typeof scrapbookThemes; moments: PhotoMoment[]; urls: Record<string,string>; date?: string; onPreview: (moment: PhotoMoment) => void};

function DiaryPhoto({src, caption, onPreview}: {src?: string; caption: string; onPreview: () => void}) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) return <div className="scrapbook-missing">照片暂未载入<br/><button onClick={() => {setFailed(false); onPreview();}}>查看原图</button></div>;
  return <button className="scrapbook-photo" onClick={onPreview} aria-label={`放大照片：${caption || '生活记录'}`}><img src={src} alt={caption || '生活记录'} loading="lazy" decoding="async" onError={() => setFailed(true)}/></button>;
}

export function ScrapbookDiary({theme, moments, urls, date = diaryDate(), onPreview}: Props) {
  const design = scrapbookThemes[theme];
  // Short pages keep large collections responsive and avoid a single huge canvas on phones.
  const pages = Array.from({length: Math.ceil(moments.length / 6)}, (_, i) => moments.slice(i * 6, i * 6 + 6));
  return <div className={`scrapbook scrapbook-${theme}`}>
    <header className="scrapbook-heading"><span>{design.subtitle}</span><div className="scrapbook-dateline"><time dateTime={date}>{date.replace(/-/g, ' / ')}</time><span aria-hidden="true">✳</span></div><h2>{design.title}</h2><p>{design.note}</p></header>
    {!moments.length && <div className="scrapbook-empty"><span aria-hidden="true">✉</span><p>今天的故事，从一张照片开始。</p></div>}
    {pages.map((page, pageIndex) => <section className="scrapbook-page" key={page[0].id} aria-label={`手帐第 ${pageIndex + 1} 页`}>
      <div className="scrapbook-paper" aria-hidden="true"/>
      <div className="scrapbook-stamp" aria-hidden="true">{theme === 'f' ? 'AUTUMN\n枫叶来信' : theme === 'g' ? 'BON VOYAGE\n沿途收集' : theme === 'h' ? '春 · 夏\n秋 · 冬' : 'DEAR DAYS\n好好生活'}</div>
      {page.map((moment, i) => <figure className={`scrapbook-frame scrapbook-frame-${i + 1}`} key={moment.id}>
        <span className="scrapbook-tape" aria-hidden="true"/>
        {moment.kind === 'video' ? <video src={moment.assetId ? urls[moment.assetId] || moment.media : moment.media} controls playsInline preload="none" aria-label={moment.caption || '生活视频'}/> : <DiaryPhoto src={moment.assetId ? urls[moment.assetId] || moment.media : moment.media} caption={moment.caption} onPreview={() => onPreview(moment)}/>}
        <figcaption><span className="scrapbook-number">{String(pageIndex * 6 + i + 1).padStart(2, '0')}</span><p>{moment.caption || ['留住这一刻', '今天的小确幸', '日常也闪光'][i % 3]}</p><time title="上传时间（北京时间）">{uploadTime(moment.createdAt)}</time></figcaption>
      </figure>)}
      <div className="scrapbook-page-note"><span aria-hidden="true">✷</span> {['生活的碎片，拼成我们的今天。', '一些小事，一些想念，一起收藏。'][pageIndex % 2]}<span className="scrapbook-page-index">{String(pageIndex + 1).padStart(2, '0')} / {String(pages.length).padStart(2, '0')}</span></div>
    </section>)}
    <footer className="scrapbook-footer"><span>resonance · 共同日记</span><span>{moments.length} 个珍藏片刻</span></footer>
  </div>;
}
