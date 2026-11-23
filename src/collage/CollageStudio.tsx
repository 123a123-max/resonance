/**
 * 生活拼贴工作台（弹窗主组件）
 * ------------------------------------------------------------------
 * 完整交互流程：
 *   1. 选择风格模板（每张卡片带 CSS 绘制的预览示例图）
 *   2. 上传 / 选择多张照片（本地图片，支持一次多选、可移除）
 *   3. 点击「AI 生成」——调用后端 /api/collage/generate；
 *      若后端未配置 AI Key 或调用失败，自动降级到本地 Canvas 排版
 *   4. 生成结果弹层预览 + 一键下载 PNG
 *
 * 只依赖 React + 项目内工具函数，不引入任何第三方 UI / AI 框架。
 */

import { useMemo, useRef, useState } from 'react';
import CollagePreview from './CollagePreview';
import { COLLAGE_CATEGORIES, COLLAGE_TEMPLATES, findTemplate, type CollageCategory, type CollageTemplate } from './templates';
import { downloadDataURL, fileToDataURL, renderCollage } from './collageEngine';

/** 单张已选照片 */
interface PickedPhoto {
  id: string;
  dataURL: string;
  name: string;
}

interface Props {
  /** 关闭弹窗回调 */
  onClose: () => void;
  /** 后端 API 根地址（从 App 传入，形如 http://host:8000/api 或 /api） */
  apiBase: string;
  /** 可选：把共同日记里已有的照片 dataURL 作为快捷素材预填（这里不强制使用） */
  initialPhotos?: string[];
}

type GenMode = 'idle' | 'ai' | 'local' | 'error';

export default function CollageStudio({ onClose, apiBase }: Props) {
  // ---- 状态 ----
  const [selectedId, setSelectedId] = useState<string>(COLLAGE_TEMPLATES[0].id);
  const [category, setCategory] = useState<CollageCategory | '全部'>('全部');
  const [photos, setPhotos] = useState<PickedPhoto[]>([]);
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<GenMode>('idle');
  const [result, setResult] = useState<string>('');
  const [notice, setNotice] = useState('');
  const [showResult, setShowResult] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const selected = useMemo<CollageTemplate>(() => findTemplate(selectedId), [selectedId]);
  const visibleTemplates = useMemo(
    () =>
      category === '全部'
        ? COLLAGE_TEMPLATES
        : COLLAGE_TEMPLATES.filter((t) => t.category === category),
    [category],
  );

  /** 追加用户选择的照片（支持多选，最多 12 张） */
  const addFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setNotice('');
    try {
      const images = Array.from(files).filter((f) => f.type.startsWith('image/'));
      if (!images.length) {
        setNotice('请选择图片文件');
        return;
      }
      const remain = 12 - photos.length;
      if (remain <= 0) {
        setNotice('最多选择 12 张照片');
        return;
      }
      const picked = await Promise.all(
        images.slice(0, remain).map(async (file, i) => ({
          id: `${Date.now()}-${i}-${Math.random().toString(36).slice(2)}`,
          dataURL: await fileToDataURL(file),
          name: file.name,
        })),
      );
      setPhotos((prev) => [...prev, ...picked]);
      if (images.length > remain) setNotice(`超出上限，仅添加了前 ${remain} 张`);
    } catch (e) {
      setNotice(e instanceof Error ? e.message : '读取图片失败');
    }
  };

  /** 使用共同日记今天的照片作为快捷素材 */
  const useDiaryPhotos = (sources: string[] = []) => {
    if (!sources.length) {
      setNotice('今天还没有可使用的照片记录');
      return;
    }
    const picked = sources.slice(0, 12).map((src, i) => ({
      id: `diary-${Date.now()}-${i}`,
      dataURL: src,
      name: `共同日记 ${i + 1}`,
    }));
    setPhotos(picked);
    setNotice(`已填入 ${picked.length} 张今天的照片`);
  };

  const removePhoto = (id: string) => setPhotos((prev) => prev.filter((p) => p.id !== id));

  /** 生成本地兜底拼贴（始终可用） */
  const generateLocal = async (): Promise<string> => {
    const subtitle = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
    return renderCollage(
      photos.map((p) => p.dataURL),
      selected,
      { title: title.trim() || selected.name, subtitle: `${selected.subtitle} · ${subtitle}` },
    );
  };

  /** 主生成流程：先尝试 AI，失败自动降级本地 */
  const generate = async () => {
    if (!photos.length) {
      setNotice('请先上传至少一张照片');
      return;
    }
    setBusy(true);
    setNotice('');
    setResult('');
    let finalURL = '';
    let usedMode: GenMode = 'local';

    try {
      // ---- 第一步：尝试调用后端 AI 生成 ----
      const form = new FormData();
      form.append('style_id', selected.id);
      form.append('prompt', selected.aiPrompt);
      form.append('negative_prompt', selected.aiNegative);
      if (title.trim()) form.append('title', title.trim());
      // 把 dataURL 还原成 Blob 上传，避免后端额外处理 base64
      const blobs = await Promise.all(
        photos.map(async (p, i) => {
          const blob = await fetch(p.dataURL).then((r) => r.blob());
          return new File([blob], `photo-${i + 1}.png`, { type: blob.type || 'image/png' });
        }),
      );
      blobs.forEach((b) => form.append('images', b));

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 120000); // 2 分钟超时
      let response: Response;
      try {
        response = await fetch(`${apiBase}/collage/generate`, {
          method: 'POST',
          body: form,
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timer);
      }

      if (!response.ok) {
        const detail = await response.text().catch(() => '');
        throw new Error(`AI 服务不可用（${response.status}）${detail ? '：' + detail.slice(0, 80) : ''}`);
      }
      const data = await response.json();
      // 兼容后端返回 dataURL 或相对 /uploads 路径
      finalURL = data.image || (data.image_url ? (data.image_url.startsWith('http') ? data.image_url : apiBase.replace(/\/api$/, '') + data.image_url) : '');
      if (!finalURL) throw new Error('AI 未返回图片');
      usedMode = 'ai';
    } catch (e) {
      // ---- 第二步：AI 失败，自动降级到本地 Canvas ----
      const reason = e instanceof Error ? e.message : String(e);
      try {
        finalURL = await generateLocal();
        usedMode = 'local';
        setNotice(`AI 生成未成功（${reason.slice(0, 60)}），已自动使用本地排版生成。`);
      } catch (localErr) {
        setNotice('生成失败：' + (localErr instanceof Error ? localErr.message : '未知错误'));
        setBusy(false);
        return;
      }
    }

    setResult(finalURL);
    setMode(usedMode);
    setShowResult(true);
    setBusy(false);
  };

  /** 手动强制使用本地排版（不请求 AI） */
  const generateLocalOnly = async () => {
    if (!photos.length) {
      setNotice('请先上传至少一张照片');
      return;
    }
    setBusy(true);
    setNotice('');
    try {
      setResult(await generateLocal());
      setMode('local');
      setShowResult(true);
    } catch (e) {
      setNotice('本地生成失败：' + (e instanceof Error ? e.message : '未知错误'));
    } finally {
      setBusy(false);
    }
  };

  /** 复制当前模板的 AI 提示词，方便用户到自己的模型里使用 */
  const copyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(
        `正面提示词：\n${selected.aiPrompt}\n\n负面提示词：\n${selected.aiNegative}`,
      );
      setNotice('该风格的 AI 提示词已复制');
    } catch {
      setNotice('复制失败，可在文档 docs/拼贴提示词.md 中查看');
    }
  };

  return (
    <div className="sheet open collage-sheet" role="dialog" aria-modal="true" aria-label="生活拼贴">
      <div className="panel collage-panel">
        <div className="head">
          <b>🖼️ 生活拼贴</b>
          <button className="btn small secondary" onClick={onClose} aria-label="关闭">关闭</button>
        </div>
        <p className="notice">选择风格 → 上传照片 → 生成拼贴。未配置 AI 时会自动使用本地排版，离线也能用。</p>

        {/* ---------- 1. 风格模板区 ---------- */}
        <div className="collage-section-title">① 选择风格模板 <span className="muted">（{COLLAGE_TEMPLATES.length} 套）</span></div>
        <div className="collage-filters">
          {COLLAGE_CATEGORIES.map((c) => (
            <button
              key={c}
              className={`tab ${category === c ? 'active' : ''}`}
              onClick={() => setCategory(c)}
            >
              {c}
            </button>
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

        {/* ---------- 2. 上传照片区 ---------- */}
        <div className="collage-section-title">② 上传照片 <span className="muted">（{photos.length}/12 张）</span></div>
        <div className="collage-upload">
          <button className="collage-drop" onClick={() => fileRef.current?.click()}>
            <span style={{ fontSize: 26 }}>＋</span>
            <span>点击选择多张照片</span>
          </button>
          <input
            ref={fileRef}
            hidden
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => { void addFiles(e.target.files); e.target.value = ''; }}
          />
          <button className="btn small secondary" onClick={() => useDiaryPhotos()}>用今天的日记照片</button>
        </div>
        {photos.length > 0 && (
          <div className="collage-thumbs">
            {photos.map((p) => (
              <div className="collage-thumb" key={p.id}>
                <img src={p.dataURL} alt={p.name} />
                <button onClick={() => removePhoto(p.id)} aria-label="移除">×</button>
              </div>
            ))}
          </div>
        )}

        {/* ---------- 3. 标题与提示词 ---------- */}
        <div className="collage-section-title">③ 标题（可选）</div>
        <input
          className="field"
          value={title}
          maxLength={24}
          placeholder={`留空则使用「${selected.name}」作为标题`}
          onChange={(e) => setTitle(e.target.value)}
        />
        <button className="collage-prompt-link" onClick={copyPrompt}>📋 复制「{selected.name}」AI 提示词</button>

        {notice && <p className="collage-notice">{notice}</p>}

        {/* ---------- 4. 生成操作区 ---------- */}
        <div className="collage-actions">
          <button className="btn" onClick={generate} disabled={busy || !photos.length}>
            {busy ? '生成中…' : '✨ AI 生成拼贴'}
          </button>
          <button className="btn secondary" onClick={generateLocalOnly} disabled={busy || !photos.length}>
            本地排版
          </button>
        </div>
      </div>

      {/* ---------- 生成结果预览层 ---------- */}
      {showResult && result && (
        <div className="sheet open collage-result" role="dialog" aria-modal="true" aria-label="拼贴预览">
          <div className="panel center">
            <div className="head">
              <b>生成完成 {mode === 'ai' ? '· AI' : '· 本地排版'}</b>
              <button className="btn small secondary" onClick={() => setShowResult(false)}>返回编辑</button>
            </div>
            <img className="collage-result-img" src={result} alt="拼贴结果预览" />
            <div className="collage-actions">
              <button
                className="btn"
                onClick={() => downloadDataURL(result, `生活拼贴-${selected.name}-${Date.now()}.png`)}
              >
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
