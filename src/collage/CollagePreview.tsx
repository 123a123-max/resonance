/**
 * 拼贴模板预览示例图（纯 CSS 绘制，第二版）
 * ==================================================================
 * 每套模板用 9:16 竖屏微缩拼贴展示风格，完全由 div + 内联样式构成，
 * 不加载外部图片：离线可用、无版权顾虑、体积为零。
 *
 * 预览遵循照片布局规则：2 张并排 / 3 张错落 / 4 张 2×2 / 5 张左侧三张+右侧叠放。
 * 用彩色渐变块 + 小圆点模拟真实照片与人脸，配合各风格的底色 / 边框 / 装饰。
 */

import type { CollageTemplate } from './templates';

/** 模拟照片的渐变色板 */
const PHOTO_GRADIENTS = [
  'linear-gradient(135deg,#f0a97b,#c96b4a)',
  'linear-gradient(135deg,#8ec5d6,#3f7d94)',
  'linear-gradient(135deg,#a8c98a,#5f8a4e)',
  'linear-gradient(135deg,#e6a0b4,#b25f7c)',
  'linear-gradient(135deg,#cfc3b0,#8c7f6b)',
  'linear-gradient(135deg,#f5d98b,#d1a24a)',
];

interface Props { template: CollageTemplate }

export default function CollagePreview({ template }: Props) {
  const { theme, id } = template;
  // 单张模拟照片的样式构造器
  const photo = (i: number, extra: React.CSSProperties = {}): React.CSSProperties => ({
    position: 'absolute',
    background: PHOTO_GRADIENTS[i % PHOTO_GRADIENTS.length],
    borderRadius: theme.radius,
    border: `${Math.max(1.5, theme.border / 4)}px solid ${theme.paper}`,
    boxShadow: '0 1px 4px rgba(0,0,0,.2)',
    overflow: 'hidden',
    ...extra,
  });
  // 照片里的「人脸」小圆点
  const face = (
    <span style={{
      position: 'absolute', left: '50%', top: '46%', width: '30%', aspectRatio: '1',
      transform: 'translate(-50%,-50%)', borderRadius: '50%', background: 'rgba(255,255,255,.5)',
    }} />
  );

  let body: React.ReactNode;
  // 统一用 4 张 2×2 作为示例布局（最能体现"排版好看"），个别风格做差异化
  if (id === 'ins-minimal' || id === 'macaron-cream') {
    // 留白风格：少量照片错落，大量留白
    body = (
      <>
        <div style={photo(0, { left: '14%', top: '26%', width: '40%', height: '30%' })}>{face}</div>
        <div style={photo(1, { right: '14%', top: '44%', width: '34%', height: '26%' })}>{face}</div>
        {id === 'macaron-cream' && <span style={{ position: 'absolute', left: '20%', bottom: '18%', color: theme.accent, fontSize: 11 }}>♥ ✿</span>}
      </>
    );
  } else if (id === 'four-seasons') {
    // 四季：横向四段色带 + 照片
    body = (
      <>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={photo(i, { left: `${10 + i * 21}%`, top: i % 2 ? '48%' : '30%', width: '19%', height: '34%' })}>{face}</div>
        ))}
      </>
    );
  } else if (id === 'frosted-tech') {
    body = (
      <>
        {[[0, 30, 26, 38, 30], [1, 56, 42, 32, 36], [2, 26, 64, 40, 24], [3, 60, 74, 30, 18]].map(([i, l, t, w, h], k) => (
          <div key={k} style={{
            ...photo(i as number, { left: `${l}%`, top: `${t}%`, width: `${w}%`, height: `${h}%` }),
            background: 'rgba(255,255,255,.55)',
            border: '1.5px solid rgba(90,160,215,.7)',
            boxShadow: '0 0 8px rgba(90,160,215,.35)',
          }}>{face}</div>
        ))}
      </>
    );
  } else if (id === 'street-graffiti' || id === 'pop-art') {
    // 涂鸦/波普：粗黑边 + 倾斜
    body = (
      <>
        {[[0, 12, 28, -7], [1, 54, 30, 6], [2, 14, 60, 5], [3, 56, 62, -6]].map(([i, l, t, r], k) => (
          <div key={k} style={photo(i as number, {
            left: `${l}%`, top: `${t}%`, width: '38%', height: '30%',
            border: '3px solid #111', borderRadius: 0, transform: `rotate(${r}deg)`,
          })}>{face}</div>
        ))}
      </>
    );
  } else {
    // 其余风格（手账/胶片/复古/文艺/青春）：错落 4 张，可适度旋转
    const tilts = id === 'travel-journal' || id === 'retro-montage' ? [-6, 5, -4, 6] : [-3, 3, -2, 2];
    body = (
      <>
        <div style={photo(0, { left: '12%', top: '28%', width: '38%', height: '30%', transform: `rotate(${tilts[0]}deg)` })}>{face}</div>
        <div style={photo(1, { right: '12%', top: '30%', width: '38%', height: '30%', transform: `rotate(${tilts[1]}deg)` })}>{face}</div>
        <div style={photo(2, { left: '14%', bottom: '20%', width: '38%', height: '28%', transform: `rotate(${tilts[2]}deg)` })}>{face}</div>
        <div style={photo(3, { right: '14%', bottom: '22%', width: '38%', height: '28%', transform: `rotate(${tilts[3]}deg)` })}>{face}</div>
        {theme.deco && <span style={{
          position: 'absolute', left: '16%', top: '14%', width: 26, height: 8,
          background: id === 'retro-magazine' ? 'rgba(184,85,47,.6)' : 'rgba(180,140,90,.5)',
          transform: 'rotate(-14deg)',
        }} />}
      </>
    );
  }

  return (
    <div style={{
      background: theme.background, position: 'relative', width: '100%',
      aspectRatio: '9 / 16', borderRadius: 10, overflow: 'hidden',
      border: '1px solid rgba(0,0,0,.06)',
    }} aria-label={`${template.name} 风格预览示例`}>
      {/* 顶部小标题条 */}
      <div style={{
        position: 'absolute', left: 0, right: 0, top: 0, zIndex: 2,
        textAlign: 'center', padding: '5px 2px',
        color: theme.ink, fontWeight: 800, fontSize: 8, letterSpacing: '.3px',
        background: 'rgba(255,255,255,.28)',
      }}>{template.name}</div>
      {body}
    </div>
  );
}
