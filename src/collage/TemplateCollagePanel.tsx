/**
 * 生活拼贴 —— 内联设置条组件。
 *
 * 挂在「共同日记」卡片的 tabs 下方，点击「生活拼贴」标签后展开。
 * 交互严格按约定：
 *   · 不弹选择窗、不在右上角加按钮、不重复上传；
 *   · 左侧选风格，右侧小框实时预览该风格模板；
 *   · 照片直接取「今天的 moments」里的图片，按上传顺序自动使用；
 *   · 点「立即生成」输出一张带照片的拼贴图，可下载、可「再来一张」。
 */
import { useEffect, useState } from 'react';
import { TEMPLATE_STYLES, type TemplateStyle } from './templateStyles';
import { renderStyleCollage, downloadCollage } from './templateRenderer';

interface MomentLike {
  id: string;
  kind: 'image' | 'video';
  assetId?: string;
  media?: string;
}

interface Props {
  /** 今日已上传的照片（由 App 传入，来自 store.moments） */
  moments: MomentLike[];
  /** 已解析好的图片 URL：assetId -> blob URL */
  mediaUrls: Record<string, string>;
}

export default function TemplateCollagePanel({ moments, mediaUrls }: Props) {
  // 默认选中第一套风格
  const [styleId, setStyleId] = useState<string>(TEMPLATE_STYLES[0].id);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState('');
  // 当前成品用的随机种子；「再来一张」会换一个新种子重新排布
  const [seed, setSeed] = useState<number>(0);

  const style: TemplateStyle = TEMPLATE_STYLES.find((s) => s.id === styleId) || TEMPLATE_STYLES[0];

  /** 今日照片：只取图片类型，跳过视频；优先用 IndexedDB 解析出的 blob URL */
  const todayPhotos = moments
    .filter((m) => m.kind === 'image')
    .map((m) => (m.assetId && mediaUrls[m.assetId]) || m.media || '')
    .filter(Boolean);

  // 切换风格时清掉旧结果与错误（模板预览会立刻跟着变）
  useEffect(() => { setResult(''); setError(''); }, [styleId]);

  /** 生成：不传 seed 时每次都用新随机种子，所以同风格连点排布不同 */
  const generate = async (seedOverride?: number) => {
    if (!todayPhotos.length) {
      setError('今天还没有照片，请先点「记录一条」上传照片');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const out = await renderStyleCollage(style, todayPhotos, seedOverride);
      setResult(out.dataURL);
      setSeed(out.seed);
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败，请重试');
    } finally {
      setBusy(false);
    }
  };

  const todayLabel = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' });
  const shown = Math.min(todayPhotos.length, 8);

  return (
    <>
      <div className="collage-settings">
        <div className="collage-settings-main">
          <b>生活拼贴设置</b>

          {/* 风格选择：点一下右侧小框立刻换模板预览 */}
          <div className="collage-style-label muted">选择风格（共 {TEMPLATE_STYLES.length} 种）</div>
          <div className="collage-style-grid">
            {TEMPLATE_STYLES.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`collage-style-btn ${styleId === s.id ? 'active' : ''}`}
                title={s.desc}
                onClick={() => setStyleId(s.id)}
              >
                {s.name}
              </button>
            ))}
          </div>
          <div className="collage-style-desc muted">{style.desc}</div>

          {/* 今日照片：自动读取，不再让用户选，也不重复上传 */}
          <div className="collage-photo-info muted">
            使用今日已上传照片 <b>{todayPhotos.length}</b> 张，本次排入 <b>{shown}</b> 张
            {todayPhotos.length > 8 && <span className="collage-hint">（最多排 8 张，取前 8 张）</span>}
          </div>
          <div className="collage-hint muted">
            排版随照片数量自动变化：1–4 张选空位错落摆放，空位转成手账便签；5–8 张自动拆成双图格。
            每次生成都会换一种排布。
          </div>

          {/* 生成按钮 */}
          <button type="button" className="btn collage-generate" disabled={busy} onClick={() => generate()}>
            {busy ? '生成中…' : '立即生成'}
          </button>
          {error && <div className="collage-error">{error}</div>}
        </div>

        {/* 右侧模板小框预览：跟着选中的风格实时切换 */}
        <div className="collage-preview-box">
          <div className="muted collage-preview-title">模板预览 · {style.name}</div>
          <img src={style.image} alt={`${style.name}模板预览`} />
          <div className="muted collage-preview-foot">9:16 竖版 · 照片位自动适配</div>
        </div>
      </div>

      {/* 生成结果大图预览 */}
      {result && (
        <div className="sheet open" onClick={() => setResult('')}>
          <div className="panel center collage-result-panel" onClick={(e) => e.stopPropagation()}>
            <div className="head">
              <b>拼贴已生成</b>
              <button className="btn small secondary" onClick={() => setResult('')}>关闭</button>
            </div>
            <p className="notice">已使用今日 {shown} 张照片 · {style.name} · 排布编号 {String(seed).slice(-6)}</p>
            <img className="collage-result-img" src={result} alt="生成的拼贴图" />
            <div className="collage-result-actions">
              <button
                className="btn secondary"
                disabled={busy}
                onClick={() => generate((Date.now() ^ Math.floor(Math.random() * 0x7fffffff)) >>> 0)}
              >
                {busy ? '生成中…' : '再来一张'}
              </button>
              <button
                className="btn"
                onClick={() => downloadCollage(result, `resonance-生活拼贴-${style.name}-${todayLabel}.jpg`)}
              >
                下载图片
              </button>
            </div>
            <div className="muted collage-result-foot">「再来一张」会保留同一风格与今日照片，只换排布和点缀。</div>
          </div>
        </div>
      )}
    </>
  );
}
