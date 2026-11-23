/**
 * 生活拼贴工作台（弹窗主组件，第二版）
 * ==================================================================
 * 交互流程（按用户要求：点开「生活拼贴」后首先弹出可选择的风格）：
 *   ① 进入即展示 13 套风格网格（每套带 CSS 绘制的预览示例图），可点选
 *   ② 选照片数量布局（2/3/4/5 张，附 AI 布局提示词）
 *   ③ 上传多张照片 / 一键用今天的日记照片
 *   ④ 生成：优先 AI（风格提示词 + 布局提示词一起发送）；
 *      失败或未配置 Key 时自动降级为本地 Canvas 排版
 *   ⑤ 结果预览 + 下载 PNG
 *
 * 只依赖 React + 项目内工具函数，不引入任何第三方 UI / AI 框架。
 */

import { useMemo, useRef, useState } from 'react';
import CollagePreview from './CollagePreview';
import {
  COLLAGE_CATEGORIES, COLLAGE_TEMPLATES, PHOTO_LAYOUTS,
  findTemplate, findLayout, type CollageCategory, type CollageTemplate,
} from './templates';
import { downloadDataURL, fileToDataURL, renderCollage } from './collageEngine';

interface PickedPhoto { id: string; dataURL: string; name: string }

interface Props {
  onClose: () => void;
  /** 后端 API 根地址，形如 http://host:8000/api 或 /api */
  apiBase: string;
}

type GenMode = 'idle' | 'ai' | 'local' | 'error';

export default function CollageStudio({ onClose, apiBase }: Props) {
  // ---- 状态 ----
  const [selectedId, setSelectedId] = useState<string>(COLLAGE_TEMPLATES[0].id);
  const [category, setCategory] = useState<CollageCategory | '全部'>('全部');
  const [layoutCount, setLayoutCount] = useState<number>(4); // 默认 4 张 2×2
  const [photos, setPhotos] = useState<PickedPhoto[]>([]);
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<GenMode>('idle');
  const [result, setResult] = useState<string>('');
  const [notice, setNotice] = useState('');
  const [showResult, setShowResult] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const selected = useMemo<CollageTemplate>(() => findTemplate(selectedId), [selectedId]);
  const layout = useMemo(() => findLayout(layoutCount), [layoutCount]);
  const visibleTemplates = useMemo(
    () => category === '全部' ? COLLAGE_TEMPLATES : COLLAGE_TEMPLATES.filter((t) => t.category === category),
    [category],
  );

  /** 追加照片（最多取布局所需张数，避免多余照片导致人脸融合） */
  const addFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setNotice('');
    try {
      const images = Array.from(files).filter((f) => f.type.startsWith('image/'));
      if (!images.length) { setNotice('请选择图片文件'); return; }
      const picked = await Promise.all(images.slice(0, 12).map(async (file, i) => ({
        id: `${Date.now()}-${i}-${Math.random().toString(36).slice(2)}`,
        dataURL: await fileToDataURL(file),
        name: file.name,
      })));
      setPhotos((prev) => [...prev, ...picked].slice(0, 12));
      if (picked.length > layoutCount) {
        setNotice(`已添加 ${picked.length} 张；当前「${layout.name}」布局只会使用前 ${layoutCount} 张，多余照片不影响排版。`);
      }
    } catch (e) {
      setNotice(e instanceof Error ? e.message : '读取图片失败');
    }
  };

  /** 用今天共同日记里的照片快捷填充 */
  const useDiaryPhotos = (sources: string[] = []) => {
    if (!sources.length) { setNotice('今天还没有可使用的照片记录'); return; }
    setPhotos(sources.slice(0, 12).map((src, i) => ({
      id: `diary-${Date.now()}-${i}`, dataURL: src, name: `共同日记 ${i + 1}`,
    })));
    setNotice(`已填入 ${Math.min(sources.length, 12)} 张今天的照片`);
  };

  const removePhoto = (id: string) => setPhotos((prev) => prev.filter((p) => p.id !== id));

  /** 本地兜底排版 */
  const generateLocal = async (): Promise<string> => {
    const subtitle = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
    return renderCollage(
      photos.slice(0, layoutCount).map((p) => p.dataURL),
      selected,
      { title: title.trim() || selected.name, subtitle: `${selected.subtitle} · ${subtitle}` },
    );
  };

  /** 组装 AI 提示词：风格 + 布局 + 反向 */
  const buildPrompt = () =>
    `${selected.aiPrompt}\n【照片布局要求】${layout.aiPrompt}\n高清，保留真实人脸，9:16 竖版拼贴海报。`;
  const buildNegative = () => `${selected.aiNegative}；${layout.aiNegative}`;

  /** 主生成：先 AI，失败自动降级本地 */
  const generate = async () => {
    if (!photos.length) { setNotice('请先上传至少一张照片'); return; }
    setBusy(true); setNotice(''); setResult('');
    let finalURL = '', usedMode: GenMode = 'local';
    try {
      const form = new FormData();
      form.append('style_id', selected.id);
      form.append('prompt', buildPrompt());
      form.append('negative_prompt', buildNegative());
      if (title.trim()) form.append('title', title.trim());
      const blobs = await Promise.all(
        photos.slice(0, layoutCount).map(async (p, i) => {
          const blob = await fetch(p.dataURL).then((r) => r.blob());
          return new File([blob], `photo-${i + 1}.png`, { type: blob.type || 'image/png' });
        }),
      );
      blobs.forEach((b) => form.append('images', b));

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 120000);
      let response: Response;
      try {
        response = await fetch(`${apiBase}/collage/generate`, { method: 'POST', body: form, signal: controller.signal });
      } finally { clearTimeout(timer); }
      if (!response.ok) {
        const detail = await response.text().catch(() => '');
        throw new Error(`AI 服务不可用（${response.status}）${detail ? '：' + detail.slice(0, 80) : ''}`);
      }
      const data = await response.json();
      finalURL = data.image || (data.image_url
        ? (data.image_url.startsWith('http') ? data.image_url : apiBase.replace(/\/api$/, '') + data.image_url)
        : '');
      if (!finalURL) throw new Error('AI 未返回图片');
      usedMode = 'ai';
    } catch (e) {
      const reason = e instanceof Error ? e.message : String(e);
      try {
        finalURL = await generateLocal();
        usedMode = 'local';
        setNotice(`AI 生成未成功（${reason.slice(0, 50)}），已自动使用本地排版生成。`);
      } catch (localErr) {
        setNotice('生成失败：' + (localErr instanceof Error ? localErr.message : '未知错误'));
        setBusy(false); return;
      }
    }
    setResult(finalURL); setMode(usedMode); setShowResult(true); setBusy(false);
  };

  /** 强制本地排版 */
  const generateLocalOnly = async () => {
    if (!photos.length) { setNotice('请先上传至少一张照片'); return; }
    setBusy(true); setNotice('');
    try {
      setResult(await generateLocal()); setMode('local'); setShowResult(true);
    } catch (e) {
      setNotice('本地生成失败：' + (e instanceof Error ? e.message : '未知错误'));
    } finally { setBusy(false); }
  };

  /** 复制当前「风格 + 布局」完整提示词 */
  const copyPrompt = async () => {
    const text = `【风格正向】\n${selected.aiPrompt}\n\n【布局正向】\n${layout.aiPrompt}\n\n【风格反向】\n${selected.aiNegative}\n\n【布局反向】\n${layout.aiNegative}`;
    try {
      await navigator.clipboard.writeText(text);
      setNotice('已复制「风格 + 布局」完整提示词');
    } catch {
      setNotice('复制失败，可在 docs/拼贴提示词.md 中查看');
    }
  };

  return (
    <div className="sheet open collage-sheet" role="dialog" aria-modal="true" aria-label="生活拼贴">
      <div className="panel collage-panel">
        <div className="head">
          <b>🖼️ 生活拼贴</b>
          <button className="btn small secondary" onClick={onClose} aria-label="关闭">关闭</button>
        </div>

        {/* ① 风格选择（进入即展示，对应需求第 1 点） */}
        <div className="collage-section-title">① 选择风格 <span className="muted">（{COLLAGE_TEMPLATES.length} 套 · 点击卡片预览）</span></div>
        <div className="collage-filters">
          {COLLAGE_CATEGORIES.map((c) => (
            <button key={c} className={`tab ${category === c ? 'active' : ''}`} onClick={() => setCategory(c)}>{c}</button>
          ))}
        </div>
        <div className="collage-grid">
          {visibleTemplates.map((t) => (
            <button
              key={t.id}
              className={`collage-card ${selectedId === t.id ? 'selected' : ''}`}
              style={{ ['--tpl-color' as string]: t.color }}
              onClick={() => setSelectedId(t.id)}
            >
              <div className="collage-card-preview">
                <CollagePreview template={t} />
                {selectedId === t.id && <span className="collage-check">✓ 已选</span>}
              </div>
              <div className="collage-card-info">
                <strong>{t.emoji} {t.name}</strong>
                <span>{t.desc}</span>
              </div>
            </button>
          ))}
        </div>

        {/* ② 照片数量布局 */}
        <div className="collage-section-title">② 照片布局 <span className="muted">（按你上传的照片张数选）</span></div>
        <div className="collage-layouts">
          {PHOTO_LAYOUTS.map((l) => (
            <button
              key={l.count}
              className={`collage-layout ${layoutCount === l.count ? 'active' : ''}`}
              onClick={() => setLayoutCount(l.count)}
            >
              <span className="collage-layout-count">{l.count}</span>
              <span className="collage-layout-text"><b>{l.name}</b><small>{l.desc}</small></span>
            </button>
          ))}
        </div>
        {/* 布局示意：竖屏九宫格缩略示意 */}
        <div className="collage-layout-demo" aria-label="布局示意">
          {Array.from({ length: layoutCount }, (_, i) => <span className={`demo-${layoutCount} demo-photo`} key={i}>{i + 1}</span>)}
        </div>

        {/* ③ 上传照片 */}
        <div className="collage-section-title">③ 上传照片 <span className="muted">（{photos.length} 张 · 当前布局取前 {layoutCount} 张）</span></div>
        <div className="collage-upload">
          <button className="collage-drop" onClick={() => fileRef.current?.click()}>
            <span style={{ fontSize: 26 }}>＋</span>
            <span>点击选择多张照片</span>
          </button>
          <input ref={fileRef} hidden type="file" accept="image/*" multiple
            onChange={(e) => { void addFiles(e.target.files); e.target.value = ''; }} />
          <button className="btn small secondary" onClick={() => useDiaryPhotos()}>用今天的日记照片</button>
        </div>
        {photos.length > 0 && (
          <div className="collage-thumbs">
            {photos.map((p, i) => (
              <div className={`collage-thumb ${i >= layoutCount ? 'overflow' : ''}`} key={p.id}>
                <img src={p.dataURL} alt={p.name} />
                {i < layoutCount && <span className="thumb-index">{i + 1}</span>}
                <button onClick={() => removePhoto(p.id)} aria-label="移除">×</button>
              </div>
            ))}
          </div>
        )}

        {/* ④ 标题与提示词 */}
        <div className="collage-section-title">④ 标题（可选）</div>
        <input className="field" value={title} maxLength={24}
          placeholder={`留空则使用「${selected.name}」作为标题`}
          onChange={(e) => setTitle(e.target.value)} />
        <button className="collage-prompt-link" onClick={copyPrompt}>📋 复制「{selected.name} + {layout.name}」完整提示词</button>

        {notice && <p className="collage-notice">{notice}</p>}

        <div className="collage-actions">
          <button className="btn" onClick={generate} disabled={busy || !photos.length}>
            {busy ? '生成中…' : '✨ AI 生成拼贴'}
          </button>
          <button className="btn secondary" onClick={generateLocalOnly} disabled={busy || !photos.length}>
            本地排版
          </button>
        </div>
      </div>

      {/* 结果预览层 */}
      {showResult && result && (
        <div className="sheet open collage-result" role="dialog" aria-modal="true" aria-label="拼贴预览">
          <div className="panel center">
            <div className="head">
              <b>生成完成 {mode === 'ai' ? '· AI' : '· 本地排版'}</b>
              <button className="btn small secondary" onClick={() => setShowResult(false)}>返回编辑</button>
            </div>
            <img className="collage-result-img" src={result} alt="拼贴结果预览" />
            <div className="collage-actions">
              <button className="btn" onClick={() => downloadDataURL(result, `生活拼贴-${selected.name}-${Date.now()}.png`)}>
                ⬇️ 下载 PNG
              </button>
              <button className="btn secondary" onClick={() => setShowResult(false)}>继续编辑</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
