/**
 * 生活拼贴模板定义
 * ------------------------------------------------------------------
 * 每一套模板都包含三部分信息：
 *  1. 展示信息（名称 / 副标题 / 分类 / 强调色）——供弹窗卡片与预览图使用
 *  2. aiPrompt / aiNegative——调用 AI 图像模型时使用的风格提示词（可直接复制）
 *  3. theme——纯前端 Canvas 兜底排版时使用的配色与纹理参数
 *
 * 设计原则：不依赖任何外部资源。预览图由 CollagePreview 组件用 CSS 现场绘制，
 * 兜底成图由 collageEngine 用 Canvas 现场合成，因此离线也能完整使用。
 */

export type CollageCategory = '手账' | '极简' | '胶片' | '复古' | '潮流' | '文艺';

/** 本地 Canvas 兜底排版时使用的视觉主题参数 */
export interface CollageTheme {
  /** 画布底色（CSS 颜色，可为渐变字符串） */
  background: string;
  /** 卡片/照片底衬色 */
  paper: string;
  /** 标题与正文文字色 */
  ink: string;
  /** 点缀色（胶带、贴纸、描边、光晕等） */
  accent: string;
  /** 照片圆角像素 */
  radius: number;
  /** 照片白边宽度像素 */
  border: number;
  /** 照片倾斜角度范围（度），0 表示规整排列 */
  tilt: number;
  /** 纹理类型，决定 Canvas 绘制的背景纹理 */
  texture: 'none' | 'paper' | 'grain' | 'dot' | 'grid' | 'glass' | 'newspaper' | 'calendar' | 'graffiti';
  /** 是否绘制装饰元素（胶带 / 贴纸 / 涂鸦线） */
  deco: boolean;
}

/** 一套拼贴模板的完整定义 */
export interface CollageTemplate {
  /** 唯一标识（同时作为 AI 提示词中的风格代号） */
  id: string;
  /** 中文名称 */
  name: string;
  /** 英文副标题（展示用） */
  subtitle: string;
  /** 风格分类 */
  category: CollageCategory;
  /** 一句话简介 */
  desc: string;
  /** 弹窗卡片右上角分类 Emoji */
  emoji: string;
  /** 主题强调色（用于卡片描边、选中态） */
  color: string;
  /** AI 生成正面提示词（英文优先，兼容主流图像模型） */
  aiPrompt: string;
  /** AI 生成负面提示词 */
  aiNegative: string;
  /** 本地 Canvas 兜底排版主题 */
  theme: CollageTheme;
}

/**
 * 11 套生活拼贴模板。
 * 提示词在用户提供的风格描述基础上做了结构化整理，保留「保留真实人脸 / 高清」等共同约束。
 */
export const COLLAGE_TEMPLATES: CollageTemplate[] = [
  {
    id: 'travel-journal',
    name: '复古旅行手账',
    subtitle: 'Vintage Travel Journal',
    category: '手账',
    desc: '牛皮纸、撕纸毛边、宝丽来边框与干花胶带，暖复古松弛感',
    emoji: '🧳',
    color: '#b07b43',
    aiPrompt:
      'Vintage travel journal collage poster, kraft paper background, multiple real travel photos arranged in a scattered overlapping layout, torn paper rough edges, polaroid frames, dried flower stickers, washi tape, hand-drawn doodles, warm retro color tone, relaxed and nostalgic mood, preserve real human faces, high definition, clean composition, premium editorial look',
    aiNegative: 'distorted facial features, blurry, dark gloomy tone, garbled text, extra limbs, low resolution',
    theme: {
      background: '#c8a375',
      paper: '#e6cfab',
      ink: '#4a3524',
      accent: '#8a5a33',
      radius: 2,
      border: 10,
      tilt: 9,
      texture: 'paper',
      deco: true,
    },
  },
  {
    id: 'fresh-green',
    name: '清新绿调手账',
    subtitle: 'Fresh Green Journal',
    category: '手账',
    desc: '柔和浅绿渐变、手绘雨滴星星小花与便签贴纸，温柔日常',
    emoji: '🌿',
    color: '#6fa87c',
    aiPrompt:
      'Fresh lifestyle journal collage, soft light green gradient background, food and portrait photos, hand-drawn raindrops stars and tiny flowers, sticky note stickers, clean and gentle style, daily fragments record, natural and relaxed, preserve real human faces, high definition, bright clean composition',
    aiNegative: 'harsh colors, face distortion, cluttered mess, blurry, dark tone',
    theme: {
      background: 'linear-gradient(150deg,#eaf5e8,#cfe6d2)',
      paper: '#ffffff',
      ink: '#33513c',
      accent: '#6fa87c',
      radius: 14,
      border: 8,
      tilt: 5,
      texture: 'none',
      deco: true,
    },
  },
  {
    id: 'four-seasons',
    name: '四季时间轴',
    subtitle: 'Four Seasons Timeline',
    category: '手账',
    desc: '长卷时间轴叙事，四季配色、手绘线条与可爱贴纸，温暖治愈',
    emoji: '🌸',
    color: '#c98aa0',
    aiPrompt:
      'Long scroll timeline journal collage, four seasons color palette, multiple groups of life photos connected by a winding timeline, hand-drawn lines and cute stickers, diary narrative feeling, free and casual layout, warm and healing, preserve real human faces, high definition, clean composition',
    aiNegative: 'overly cluttered, face deformation, chaotic layout, blurry, dark tone',
    theme: {
      background: 'linear-gradient(180deg,#fde9d9 0%,#e7f2d8 33%,#d7eef0 66%,#e9dcf0 100%)',
      paper: '#ffffff',
      ink: '#5a4a45',
      accent: '#c98aa0',
      radius: 12,
      border: 7,
      tilt: 4,
      texture: 'grid',
      deco: true,
    },
  },
  {
    id: 'pop-art',
    name: '波普撞色海报',
    subtitle: 'Pop Art Poster',
    category: '潮流',
    desc: '高饱和撞色、粗黑体大字与复古网点，活力张扬的视觉冲击',
    emoji: '💥',
    color: '#e5432f',
    aiPrompt:
      'Pop art poster collage, high saturation contrasting colors, bold heavy black typography, retro halftone dots, torn edge photos, energetic and flamboyant, urban portrait, strong visual impact, preserve real human faces, high definition, clean and sharp, premium graphic design',
    aiNegative: 'distorted face, blurry, dull dark colors, garbled text, low resolution',
    theme: {
      background: '#f7d94b',
      paper: '#ffffff',
      ink: '#111111',
      accent: '#e5432f',
      radius: 0,
      border: 6,
      tilt: 8,
      texture: 'dot',
      deco: true,
    },
  },
  {
    id: 'ins-minimal',
    name: 'INS 极简留白',
    subtitle: 'INS Minimal White',
    category: '极简',
    desc: '超大留白、不对称错落、圆角细白边，哑光低饱和高级 ins 风',
    emoji: '🤍',
    color: '#b9aFA4',
    aiPrompt:
      'INS极简留白高级拼贴风格：超大留白布局，不对称错落排版，照片圆角细白边，哑光低饱和奶白色调，无多余装饰，干净高级ins风，保留真实人脸，高清质感，适合小组日常记录。Large negative space layout, asymmetric staggering, rounded photos with thin white borders, matte low-saturation milky white tone, no extra decoration, clean premium instagram style, preserve real faces, high definition texture',
    aiNegative: 'cluttered decoration, harsh saturated colors, distorted face, blurry, dark gloomy, garbled text',
    theme: {
      background: '#f4f1ec',
      paper: '#ffffff',
      ink: '#6b665f',
      accent: '#c9c2b6',
      radius: 22,
      border: 7,
      tilt: 3,
      texture: 'none',
      deco: false,
    },
  },
  {
    id: 'japanese-film',
    name: '日系盐系胶片',
    subtitle: 'Japanese Salt Film',
    category: '胶片',
    desc: '低饱和清透、胶片颗粒柔光、浅灰朦胧边框，治愈盐系',
    emoji: '🎞️',
    color: '#8fa3a8',
    aiPrompt:
      '日系盐系胶片拼贴风格：日系低饱和清透色调，轻微胶片颗粒柔光，浅灰朦胧边框，疏松半重叠温柔排版，干净治愈盐系风格，保留真实人脸，高清通透，适合校园日常记录。Japanese low-saturation clear tone, subtle film grain and soft light, light gray hazy borders, loose semi-overlapping gentle layout, clean healing style, preserve real faces, high definition and translucent',
    aiNegative: 'over-saturated, face distortion, harsh contrast, blurry, dark tone, heavy filters',
    theme: {
      background: 'linear-gradient(160deg,#eef1f2,#dde4e6)',
      paper: '#f6f7f7',
      ink: '#5b686c',
      accent: '#a9b7bb',
      radius: 10,
      border: 12,
      tilt: 5,
      texture: 'grain',
      deco: false,
    },
  },
  {
    id: 'macaron-cream',
    name: '奶油马卡龙',
    subtitle: 'Cream Macaron',
    category: '极简',
    desc: '奶油磨砂底、马卡龙浅粉浅蓝渐变与小爱心圆点，软糯青春',
    emoji: '🍬',
    color: '#e6a0b4',
    aiPrompt:
      '奶油马卡龙青春拼贴风格：奶油磨砂底色，马卡龙浅粉浅蓝温柔渐变，极简小爱心圆点装饰，柔和错落排版，软糯青春治愈风格，干净清新校园感，保留人脸高清。Cream frosted background, macaron light pink and light blue gentle gradient, minimal tiny heart and dot decorations, soft staggered layout, soft youthful healing style, clean fresh campus feeling, preserve real faces, high definition',
    aiNegative: 'harsh colors, face distortion, cluttered, blurry, dark gloomy, garbled text',
    theme: {
      background: 'linear-gradient(135deg,#fdeef1 0%,#eef3fd 50%,#fef4e6 100%)',
      paper: '#fffafc',
      ink: '#8a6672',
      accent: '#e6a0b4',
      radius: 26,
      border: 8,
      tilt: 4,
      texture: 'dot',
      deco: true,
    },
  },
  {
    id: 'frosted-tech',
    name: '清透 AI 科技磨砂',
    subtitle: 'Frosted Tech AI',
    category: '潮流',
    desc: '磨砂玻璃通透、淡冰蓝微光边框、极简几何排版，未来科技感',
    emoji: '🔷',
    color: '#4f9fd6',
    aiPrompt:
      '清透AI科技磨砂拼贴风格：适配AI创客主题，磨砂玻璃通透质感，淡冰蓝微光边框，极简几何排版，干净未来科技感，清透不刺眼，高清真实照片，保留人脸，AI项目专属高级风格。Frosted glass translucent texture, light ice-blue glowing borders, minimal geometric layout, clean futuristic tech feeling, clear not harsh, high definition real photos, preserve real faces, premium AI-project-exclusive style',
    aiNegative: 'dark heavy, face distortion, cluttered wires, blurry, neon harsh glare, garbled text',
    theme: {
      background: 'linear-gradient(150deg,#eaf4fb,#dceaf5 60%,#e8f1fa)',
      paper: 'rgba(255,255,255,.55)',
      ink: '#2c4b63',
      accent: '#4f9fd6',
      radius: 18,
      border: 5,
      tilt: 0,
      texture: 'glass',
      deco: true,
    },
  },
  {
    id: 'calendar-diary',
    name: '时光日历日记',
    subtitle: 'Calendar Diary',
    category: '文艺',
    desc: '淡日历纹理、便签贴角真实日记质感，有序叙事的每日归档',
    emoji: '📅',
    color: '#c08a5a',
    aiPrompt:
      '时光日历日记拼贴风格：贴合项目每日记录功能，淡日历纹理底色，便签贴角真实日记质感，有序叙事排版，温暖时光记录氛围，适合小组每日照片归档，高清干净、保留人脸。Light calendar texture background, sticky note corner tabs, authentic diary feeling, orderly narrative layout, warm time-recording atmosphere, suitable for daily photo archiving, high definition clean, preserve real faces',
    aiNegative: 'cluttered, face deformation, blurry, dark tone, garbled text, messy overlap',
    theme: {
      background: '#f6f0e4',
      paper: '#fffdf6',
      ink: '#5b4c3a',
      accent: '#c08a5a',
      radius: 8,
      border: 9,
      tilt: 3,
      texture: 'calendar',
      deco: true,
    },
  },
  {
    id: 'street-graffiti',
    name: '街头极简涂鸦',
    subtitle: 'Street Graffiti',
    category: '潮流',
    desc: '潮牌浅灰底、极简黑白涂鸦线条，随性年轻的干净街头感',
    emoji: '✍️',
    color: '#4a4a4a',
    aiPrompt:
      '街头极简潮流涂鸦拼贴风格：潮牌浅灰底色，极简黑白涂鸦线条装饰，自由随性年轻排版，干净街头青春感，不花哨、高级潮流，保留人脸高清。Streetwear light gray background, minimal black and white graffiti line decorations, free and casual youthful layout, clean street青春 feeling, not flashy, premium trendy, preserve real faces, high definition',
    aiNegative: 'colorful messy graffiti, face distortion, blurry, dark gloomy, garbled text, overwhelming',
    theme: {
      background: '#e8e8e6',
      paper: '#ffffff',
      ink: '#1a1a1a',
      accent: '#2b2b2b',
      radius: 4,
      border: 6,
      tilt: 11,
      texture: 'graffiti',
      deco: true,
    },
  },
  {
    id: 'rice-paper',
    name: '文艺宣纸书香',
    subtitle: 'Rice Paper Literary',
    category: '文艺',
    desc: '宣纸纹理、淡雅素色极简排版、柔边照片，安静治愈的文学氛围',
    emoji: '📖',
    color: '#9a8f7a',
    aiPrompt:
      '文艺宣纸书香拼贴风格：宣纸纹理底色，淡雅素色极简排版，柔边照片，文学安静治愈氛围，素雅高级、干净小众，适合校园生活记录，高清保留人脸。Rice paper texture background, elegant muted minimal layout, soft-edge photos, quiet healing literary atmosphere, refined and understated, clean niche style, suitable for campus life records, high definition, preserve real faces',
    aiNegative: 'bright saturated colors, face distortion, blurry, dark gloomy, garbled text, heavy decoration',
    theme: {
      background: '#efe9dc',
      paper: '#faf6ec',
      ink: '#514a3c',
      accent: '#9a8f7a',
      radius: 8,
      border: 10,
      tilt: 2,
      texture: 'paper',
      deco: false,
    },
  },
  {
    id: 'retro-magazine',
    name: '美式复古杂志',
    subtitle: 'Retro Magazine',
    category: '复古',
    desc: '90 年代美式杂志、米黄报纸纹理、粗黑线框与做旧印刷质感',
    emoji: '📰',
    color: '#b8552f',
    aiPrompt:
      '美式复古杂志拼贴风格：90年代美式杂志风，复古米黄报纸纹理底，粗黑线条边框，自由大胆不对称排版，轻微做旧印刷质感，简约复古装饰，高清干净，保留人脸，视觉高级适合比赛展示。90s American retro magazine style, vintage beige newspaper texture background, thick black line frames, bold free asymmetric layout, slight aged print texture, minimal retro decoration, high definition clean, preserve real faces, premium look suitable for competitions',
    aiNegative: 'distorted face, blurry, dark gloomy, garbled text, over-decorated, low resolution',
    theme: {
      background: '#e8dcc0',
      paper: '#f3ead2',
      ink: '#1c1a16',
      accent: '#b8552f',
      radius: 0,
      border: 5,
      tilt: 7,
      texture: 'newspaper',
      deco: true,
    },
  },
];

/** 按 id 查找模板，找不到时回退到第一套 */
export const findTemplate = (id: string): CollageTemplate =>
  COLLAGE_TEMPLATES.find((t) => t.id === id) || COLLAGE_TEMPLATES[0];

/** 分类去重列表（弹窗筛选栏使用） */
export const COLLAGE_CATEGORIES: Array<CollageCategory | '全部'> = [
  '全部',
  '手账',
  '极简',
  '胶片',
  '复古',
  '潮流',
  '文艺',
];
