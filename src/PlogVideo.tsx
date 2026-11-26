import { useEffect, useMemo, useRef, useState } from 'react';
import {
  COLORS,
  FONTS,
  SLOT_SECONDS,
  probeDuration,
  startPlogVideo,
  totalSeconds,
  type PlogGroup,
  type PlogItem,
  type PlogResult,
  type PlogTask,
} from './plogRender';

type Props = {
  groups: PlogGroup[];
  date: string;
  onClose: () => void;
};

type Status = 'idle' | 'recording' | 'done' | 'error';

/** 本地智能建议：不联网，根据日期、成员昵称与用户输入的文字组合候选 */
function buildSuggestions(date: string, names: string[], captions: string[]) {
  const [, month, day] = date.split('-');
  const md = `${Number(month)}月${Number(day)}日`;
  const who = names.length > 1 ? `${names.slice(0, 2).join('和')}` : names[0] || '我们';
  const seed = date.split('').reduce((s, c) => s + c.charCodeAt(0), 0);
  const pick = (list: string[], n: number) => {
    const out: string[] = [];
    for (let i = 0; i < n && i < list.length; i += 1) out.push(list[(seed + i) % list.length]);
    return out;
  };

  const titles = pick(
    [
      `${md} · 我们的日常`,
      `今天，也在一起`,
      `${who}的一天`,
      `把今天收进日记里`,
      `${md} 的小确幸`,
      `这一天，值得记住`,
      `我们的第 ${Number(day)} 天`,
      `平凡日子里的光`,
    ],
    6,
  );

  const base = [
    '平凡的日子，也值得认真收藏。',
    '今天的风，刚好吹到我们这里。',
    '日子很长，记得常常笑。',
    '把喜欢的生活，过成日常。',
    '我们的小事，也闪闪发光。',
    '又攒下一天的好心情。',
    '认真生活的样子，最好看。',
    '今天也辛苦啦，明天见。',
  ];
  const fromUser = captions.filter((c) => c && c.trim()).slice(0, 2);
  const lines = [...fromUser, ...pick(base, Math.max(4, 6 - fromUser.length))];
  return { titles, captions: lines.slice(0, 6) };
}

function formatTime(sec: number) {
  return `${sec.toFixed(1)}s`;
}

export function PlogVideo({ groups, date, onClose }: Props) {
  const usable = useMemo(() => groups.filter((g) => g.items.length > 0), [groups]);
  const names = usable.map((g) => g.name);
  const captions = useMemo(
    () => usable.flatMap((g) => g.items.map((i) => i.caption || '')).filter(Boolean),
    [usable],
  );
  const suggestions = useMemo(() => buildSuggestions(date, names, captions), [date, names, captions]);

  const [title, setTitle] = useState(suggestions.titles[0] || '我们的日常');
  const [caption, setCaption] = useState(suggestions.captions[0] || '');
  const [fontKey, setFontKey] = useState<string>(FONTS[0].key);
  const [colorKey, setColorKey] = useState<string>(COLORS[0].key);
  const [trims, setTrims] = useState<Record<string, number>>({});
  const [durations, setDurations] = useState<Record<string, number>>({});
  const [status, setStatus] = useState<Status>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [result, setResult] = useState<PlogResult | null>(null);
  const [resultUrl, setResultUrl] = useState('');
  const taskRef = useRef<PlogTask | null>(null);

  // 补齐视频时长（用于截取滑块）
  const probed = useRef<Set<string>>(new Set());
  useEffect(() => {
    let alive = true;
    usable.forEach((g) => {
      g.items.forEach((item) => {
        if (item.kind !== 'video') return;
        if (durations[item.id] !== undefined) return;
        if (probed.current.has(item.id)) return;
        probed.current.add(item.id);
        if (item.duration) {
          setDurations((d) => ({ ...d, [item.id]: item.duration as number }));
          return;
        }
        probeDuration(item.src)
          .then((sec) => {
            if (alive) setDurations((d) => ({ ...d, [item.id]: sec }));
          })
          .catch(() => {});
      });
    });
    return () => {
      alive = false;
    };
  }, [usable, durations]);

  useEffect(() => () => {
    taskRef.current?.cancel();
  }, []);

  useEffect(() => () => {
    if (resultUrl) URL.revokeObjectURL(resultUrl);
  }, [resultUrl]);

  const total = totalSeconds(usable);
  const fontCss = FONTS.find((f) => f.key === fontKey)?.css || FONTS[0].css;
  const color = COLORS.find((c) => c.key === colorKey)?.value || '#ffffff';

  const maxTrim = (item: PlogItem) => {
    const d = durations[item.id] || item.duration || 0;
    return Math.max(0, d - SLOT_SECONDS);
  };

  const make = async () => {
    if (!usable.length) return;
    if (!title.trim() && !caption.trim()) {
      setError('标题和文案至少填一个');
      return;
    }
    setError('');
    setResult(null);
    if (resultUrl) {
      URL.revokeObjectURL(resultUrl);
      setResultUrl('');
    }
    setProgress(0);
    setStatus('recording');
    const prepared: PlogGroup[] = usable.map((g) => ({
      ...g,
      items: g.items.map((i) => ({ ...i, trimStart: i.kind === 'video' ? trims[i.id] || 0 : 0 })),
    }));
    const task = startPlogVideo(
      { groups: prepared, title: title.trim(), caption: caption.trim(), fontCss, color },
      (ratio) => setProgress(ratio),
    );
    taskRef.current = task;
    try {
      const out = await task.promise;
      setResult(out);
      setResultUrl(URL.createObjectURL(out.blob));
      setProgress(1);
      setStatus('done');
    } catch (e) {
      if (e instanceof Error && e.message === 'cancelled') {
        setStatus('idle');
        return;
      }
      setError(e instanceof Error ? e.message : '生成失败');
      setStatus('error');
    } finally {
      taskRef.current = null;
    }
  };

  const fileName = `resonance-${date}.${result?.ext || 'webm'}`;

  return (
    <div className="sheet open">
      <div className="panel plogv-panel">
        <div className="head">
          <b>制作视频</b>
          <button className="btn small secondary" onClick={onClose}>关闭</button>
        </div>

        <p className="notice">
          黑色背景、竖向画幅（高为长边），每人一个格子；图片每 2 秒切换，视频可截取其中 2 秒。共 {usable.length} 人，
          预计时长 {total} 秒，导出无声。生成时请停留在本页面，不要切到其他窗口或锁屏。
        </p>

        {/* 素材与截取 */}
        <div className="plogv-section">
          <b>素材</b>
          {usable.length === 0 && <div className="empty">今天还没有可用的素材。</div>}
          {usable.map((g) => (
            <div className="plogv-group" key={g.key}>
              <div className="plogv-group-head">
                <span>{g.name}</span>
                <span className="muted">{g.items.length} 个素材</span>
              </div>
              {g.items.map((item) => (
                <div className="plogv-item" key={item.id}>
                  <div className="plogv-thumb">
                    {item.kind === 'video' ? (
                      <video src={item.src} preload="metadata" muted playsInline />
                    ) : (
                      <img src={item.src} alt="" loading="lazy" />
                    )}
                  </div>
                  <div className="plogv-item-meta">
                    <span>{item.kind === 'video' ? '视频' : '图片'}</span>
                    {item.caption && <small className="muted">{item.caption}</small>}
                    {item.kind === 'video' && (
                      <label className="plogv-trim">
                        <span className="muted">
                          截取 {formatTime(trims[item.id] || 0)} – {formatTime((trims[item.id] || 0) + SLOT_SECONDS)}
                        </span>
                        <input
                          type="range"
                          min={0}
                          max={maxTrim(item)}
                          step={0.1}
                          value={Math.min(trims[item.id] || 0, maxTrim(item))}
                          onChange={(e) => setTrims((t) => ({ ...t, [item.id]: Number(e.target.value) }))}
                          disabled={maxTrim(item) <= 0}
                        />
                      </label>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* 标题 */}
        <div className="plogv-section">
          <b>标题（顶部）</b>
          <input
            className="field"
            value={title}
            maxLength={24}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="例如：11月26日 · 我们的日常"
          />
          <div className="plogv-chips">
            {suggestions.titles.map((t) => (
              <button key={t} className={`tab ${title === t ? 'active' : ''}`} onClick={() => setTitle(t)}>
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* 文案 */}
        <div className="plogv-section">
          <b>文案（右下角）</b>
          <input
            className="field"
            value={caption}
            maxLength={30}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="例如：平凡的日子，也值得认真收藏。"
          />
          <div className="plogv-chips">
            {suggestions.captions.map((c) => (
              <button key={c} className={`tab ${caption === c ? 'active' : ''}`} onClick={() => setCaption(c)}>
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* 字体与颜色 */}
        <div className="plogv-section">
          <b>字体</b>
          <div className="count-picker">
            {FONTS.map((f) => (
              <button
                key={f.key}
                className={`tab ${fontKey === f.key ? 'active' : ''}`}
                onClick={() => setFontKey(f.key)}
                style={{ fontFamily: f.css }}
              >
                {f.label}
              </button>
            ))}
          </div>
          <b>文字颜色</b>
          <div className="plogv-colors">
            {COLORS.map((c) => (
              <button
                key={c.key}
                title={c.label}
                aria-label={c.label}
                className={`plogv-color ${colorKey === c.key ? 'active' : ''}`}
                style={{ background: c.value }}
                onClick={() => setColorKey(c.key)}
              />
            ))}
          </div>
        </div>

        {error && <p className="plogv-error">{error}</p>}

        {status === 'recording' && (
          <div className="plogv-progress">
            <div className="plogv-bar" style={{ width: `${Math.round(progress * 100)}%` }} />
            <span className="muted">正在生成… {Math.round(progress * 100)}%（实时录制，请勿切换页面）</span>
          </div>
        )}

        {status !== 'recording' && (
          <button className="btn" style={{ width: '100%', marginTop: 12 }} onClick={make} disabled={!usable.length}>
            {status === 'done' ? '重新生成视频' : '生成视频'}
          </button>
        )}

        {status === 'done' && result && resultUrl && (
          <div className="plogv-result">
            <video src={resultUrl} controls playsInline className="plogv-preview" />
            <div className="muted">
              {result.ext.toUpperCase()} · {result.duration} 秒 · {Math.round(result.blob.size / 1024)} KB
            </div>
            <a className="btn" href={resultUrl} download={fileName}>保存视频</a>
          </div>
        )}
      </div>
    </div>
  );
}
