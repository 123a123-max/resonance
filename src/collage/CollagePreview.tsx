/**
 * 拼贴模板预览示例图（纯 CSS 绘制）
 * ------------------------------------------------------------------
 * 每套模板用一个微缩的「示例拼贴」来展示风格，完全由 div + 内联样式构成，
 * 不加载任何外部图片，因此离线可用、无版权顾虑、体积为零。
 *
 * 使用几张彩色渐变块模拟真实照片，配合每套模板特有的边框 / 纹理 / 装饰，
 * 让用户一眼就能分辨风格差异。
 */

import type { CollageTemplate } from './templates';

/** 模拟照片的渐变色板（暖、冷、绿、粉、中性），让示例更接近真实照片墙 */
const PHOTO_GRADIENTS = [
  'linear-gradient(135deg,#f0a97b,#c96b4a)',
  'linear-gradient(135deg,#8ec5d6,#3f7d94)',
  'linear-gradient(135deg,#a8c98a,#5f8a4e)',
  'linear-gradient(135deg,#e6a0b4,#b25f7c)',
  'linear-gradient(135deg,#cfc3b0,#8c7f6b)',
  'linear-gradient(135deg,#f5d98b,#d1a24a)',
];

interface Props {
  template: CollageTemplate;
}

export default function CollagePreview({ template }: Props) {
  const { theme, id } = template;
  // 预览容器公共样式：底色 / 背景
  const baseStyle: React.CSSProperties = {
    background: theme.background,
    fontFamily: 'system-ui, sans-serif',
  };
  // 一张模拟照片的样式构造器
  const photo = (i: number, extra: React.CSSProperties = {}): React.CSSProperties => ({
    position: 'absolute',
    background: PHOTO_GRADIENTS[i % PHOTO_GRADIENTS.length],
    borderRadius: theme.radius,
    border: `${Math.max(2, theme.border / 3)}px solid ${theme.paper}`,
    boxShadow: '0 2px 6px rgba(0,0,0,.18)',
    overflow: 'hidden',
    ...extra,
  });
  // 照片里的「人像」小圆点，暗示保留人脸
  const face = (
    <span
      style={{
        position: 'absolute',
        left: '50%',
        top: '48%',
        width: '28%',
        aspectRatio: '1',
        transform: 'translate(-50%,-50%)',
        borderRadius: '50%',
        background: 'rgba(255,255,255,.55)',
      }}
    />
  );

  /* ---- 各模板差异化的预览构图 ---- */
  let body: React.ReactNode;

  if (id === 'ins-minimal' || id === 'macaron-cream') {
    // 留白 / 马卡龙：超大留白 + 不对称错落
    body = (
      <>
        <div style={photo(0, { left: '10%', top: '20%', width: '46%', height: '52%' })}>{face}</div>
        <div style={photo(1, { right: '8%', top: '14%', width: '30%', height: '30%' })}>{face}</div>
        <div style={photo(2, { right: '12%', bottom: '12%', width: '34%', height: '32%' })}>{face}</div>
        {id === 'macaron-cream' && (
          <span style={{ position: 'absolute', right: '16%', top: '52%', color: theme.accent, fontSize: 13 }}>♥</span>
        )}
      </>
    );
  } else if (id === 'four-seasons' || id === 'japanese-film') {
    // 时间轴：竖线 + 左右交替
    body = (
      <>
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '8%',
            bottom: '8%',
            borderLeft: `2px dashed ${theme.accent}`,
          }}
        />
        <div style={photo(0, { left: '8%', top: '12%', width: '34%', height: '34%' })}>{face}</div>
        <div style={photo(1, { right: '8%', top: '40%', width: '34%', height: '34%' })}>{face}</div>
        <div style={photo(2, { left: '8%', bottom: '8%', width: '34%', height: '30%' })}>{face}</div>
      </>
    );
  } else if (id === 'pop-art') {
    // 波普：粗黑边 + 撞色 + 网点
    body = (
      <>
        <div style={photo(0, { left: '8%', top: '16%', width: '40%', height: '44%', border: '4px solid #111', borderRadius: 0 })}>{face}</div>
        <div style={photo(1, { right: '8%', top: '16%', width: '40%', height: '44%', border: '4px solid #111', borderRadius: 0 })}>{face}</div>
        <div
          style={{
            position: 'absolute',
            left: '8%',
            bottom: '10%',
            width: '84%',
            height: '12%',
            background: '#111',
            color: '#ffe14d',
            fontWeight: 900,
            fontSize: 13,
            display: 'grid',
            placeItems: 'center',
            letterSpacing: 2,
          }}
        >
          POP! 撞色
        </div>
      </>
    );
  } else if (id === 'calendar-diary') {
    // 日历：网格 + 日期角标
    body = (
      <>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={photo(i, { left: `${7 + i * 23}%`, top: '22%', width: '19%', height: '48%' })}>
            {face}
            <span
              style={{
                position: 'absolute',
                right: 0,
                top: 0,
                background: theme.accent,
                color: '#fff',
                fontSize: 8,
                padding: '1px 3px',
              }}
            >
              {String(i + 1).padStart(2, '0')}
            </span>
          </div>
        ))}
      </>
    );
  } else if (id === 'frosted-tech') {
    // 磨砂科技：半透明玻璃块 + 微光边
    body = (
      <>
        <div
          style={{
            ...photo(0, { left: '10%', top: '18%', width: '44%', height: '50%' }),
            background: 'rgba(255,255,255,.5)',
            border: '2px solid rgba(90,160,215,.7)',
            boxShadow: '0 0 12px rgba(90,160,215,.4)',
          }}
        >
          {face}
        </div>
        <div
          style={{
            ...photo(1, { right: '10%', top: '26%', width: '32%', height: '38%' }),
            border: '2px solid rgba(90,160,215,.7)',
            boxShadow: '0 0 12px rgba(90,160,215,.4)',
          }}
        >
          {face}
        </div>
      </>
    );
  } else {
    // 手账 / 胶片 / 复古 / 涂鸦 / 文艺：错落倾斜 + 装饰
    const tilts = id === 'street-graffiti' ? [-10, 8, -6] : id === 'travel-journal' ? [-7, 6, -4] : [-4, 4, -2];
    body = (
      <>
        <div style={photo(0, { left: '9%', top: '16%', width: '42%', height: '50%', transform: `rotate(${tilts[0]}deg)` })}>{face}</div>
        <div style={photo(1, { right: '9%', top: '24%', width: '38%', height: '46%', transform: `rotate(${tilts[1]}deg)` })}>{face}</div>
        <div style={photo(2, { left: '30%', bottom: '8%', width: '34%', height: '34%', transform: `rotate(${tilts[2]}deg)` })}>{face}</div>
        {theme.deco && (
          <span
            style={{
              position: 'absolute',
              left: '14%',
              top: '8%',
              width: 34,
              height: 12,
              background: id === 'retro-magazine' ? 'rgba(184,85,47,.6)' : 'rgba(180,140,90,.5)',
              transform: 'rotate(-16deg)',
            }}
          />
        )}
      </>
    );
  }

  return (
    <div
      style={{
        ...baseStyle,
        position: 'relative',
        width: '100%',
        aspectRatio: '16 / 11',
        borderRadius: 12,
        overflow: 'hidden',
        border: '1px solid rgba(0,0,0,.06)',
      }}
      aria-label={`${template.name} 风格预览示例`}
    >
      {/* 顶部标题条 */}
      <div
        style={{
          position: 'absolute',
          left: '8%',
          top: '6%',
          color: theme.ink,
          fontWeight: 800,
          fontSize: 11,
          letterSpacing: '.5px',
          zIndex: 2,
        }}
      >
        {template.subtitle}
      </div>
      {body}
    </div>
  );
}
