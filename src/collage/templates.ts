/**
 * 生活拼贴模板定义（第二版）
 * ==================================================================
 * 本版按用户提供的 13 套风格提示词 + 5 种照片数量布局规则重写。
 *
 * 每套模板包含：
 *  1. 展示信息：名称 / 副标题 / 分类 / 强调色 / Emoji
 *  2. aiPrompt / aiNegative：用户提供的正向 / 反向提示词（原样保留，可直接复制）
 *  3. theme：纯前端 Canvas 兜底排版使用的配色、纹理、边框参数
 *
 * 另有 PHOTO_LAYOUTS：2/3/4/5 张照片的布局规则与提示词，供 AI 与本地排版共用。
 * 所有内容均为静态数据，无外部依赖，离线可用。
 */

export type CollageCategory = '极简' | '胶片' | '复古' | '青春' | '科技' | '文艺' | '潮流';

/** 本地 Canvas 兜底排版的视觉主题参数 */
export interface CollageTheme {
  /** 画布底色（CSS 颜色，可为渐变字符串） */
  background: string;
  /** 照片底衬/相纸色 */
  paper: string;
  /** 标题与正文色 */
  ink: string;
  /** 点缀色（胶带/贴纸/描边/光晕） */
  accent: string;
  /** 照片圆角像素 */
  radius: number;
  /** 照片白边宽度像素 */
  border: number;
  /** 照片倾斜角度范围（度），0 表示规整 */
  tilt: number;
  /** 背景纹理类型 */
  texture: 'none' | 'paper' | 'grain' | 'dot' | 'grid' | 'glass' | 'newspaper' | 'calendar' | 'graffiti' | 'silk';
  /** 是否绘制装饰元素 */
  deco: boolean;
}

/** 一套拼贴模板 */
export interface CollageTemplate {
  id: string;
  name: string;
  subtitle: string;
  category: CollageCategory;
  desc: string;
  emoji: string;
  color: string;
  /** AI 正向提示词（用户提供，原样保留） */
  aiPrompt: string;
  /** AI 反向提示词（用户提供，原样保留） */
  aiNegative: string;
  theme: CollageTheme;
}

/** 照片数量布局：AI 提示词 + 说明 */
export interface PhotoLayout {
  count: number;
  name: string;
  desc: string;
  /** AI 正向布局提示词（用户提供） */
  aiPrompt: string;
  /** AI 反向布局提示词（用户提供） */
  aiNegative: string;
}

/**
 * 4 种照片数量布局规则（2/3/4/5 张）。
 * 本地 Canvas 引擎按 count 精确排布；AI 生成时把对应提示词拼进风格提示词。
 */
export const PHOTO_LAYOUTS: PhotoLayout[] = [
  {
    count: 2,
    name: '2 张并排',
    desc: '下半部分左右并排，间距均匀',
    aiPrompt: '手机竖屏 9:16，画面下半部分并排摆放两个照片，左右并排，间距均匀；可适度旋转照片',
    aiNegative: '方框错位、大小不一、重叠，人脸融合，文字错乱，杂乱装饰',
  },
  {
    count: 3,
    name: '3 张错落',
    desc: '上左 / 中右 / 底部左，错落留白',
    aiPrompt: '手机竖屏 9:16，一共 3 个照片：第一个在画面上侧靠左，第二个在中间靠右，第三个在底部靠左，错落排布，留有空隙，可适度旋转照片',
    aiNegative: '排成一行/标准网格，方框重叠，人物混在一起，疯狂加装饰',
  },
  {
    count: 4,
    name: '4 张网格',
    desc: '标准 2×2，间距均匀',
    aiPrompt: '手机竖屏 9:16，四个照片，标准 2×2 排布：左上、右上、左下、右下，间距均匀，可适度旋转',
    aiNegative: '大小不一，位置乱飘，方框倾斜，人脸互相融合',
  },
  {
    count: 5,
    name: '5 张叙事',
    desc: '左侧三张纵向 + 右侧上下叠放两张',
    aiPrompt: '手机竖屏 9:16，五个照片，错落排布：左上 1 个，中间左 1 个，底部左 1 个，中间右侧上下叠放 2 个；可适度旋转照片',
    aiNegative: '整齐网格，方框重叠，人物混在一起，大量多余图案',
  },
];

/** 13 套风格模板（提示词为用户提供的最终版本，原样保留） */
export const COLLAGE_TEMPLATES: CollageTemplate[] = [
  {
    id: 'ins-minimal',
    name: 'INS 极简留白',
    subtitle: 'INS Minimal',
    category: '极简',
    desc: '米白浅灰裸棕低饱和，大量留白，松弛精致，少即是多',
    emoji: '🤍',
    color: '#b6aa9c',
    aiPrompt: '竖版 3:4，INS 高级拼贴，大量留白，米白浅灰裸棕低饱和色调，少量实拍照片、干花、器皿、局部人像，纤细无衬线小字，松弛精致，贴纸细白描边，柔和纸张纹理，淡淡的颗粒，构图克制，少即是多，时尚社交海报，高清，细腻质感，层次轻柔，简约高级，不拥挤。',
    aiNegative: '色彩浓烈，杂乱堆砌，粗大字，密集贴纸，畸形文字，夸张涂鸦，厚重阴影。',
    theme: {
      background: '#f2efe9', paper: '#ffffff', ink: '#6f6960', accent: '#c4b9a8',
      radius: 18, border: 9, tilt: 2, texture: 'grain', deco: false,
    },
  },
  {
    id: 'japanese-film',
    name: '日系盐系胶片',
    subtitle: 'Japanese Salt Film',
    category: '胶片',
    desc: '低饱和灰蓝浅草绿，褪色颗粒，和纸胶带，安静温柔',
    emoji: '🎞️',
    color: '#8fa3a8',
    aiPrompt: '日系盐系拼贴，胶片质感，低饱和灰蓝、浅草绿，淡淡的褪色颗粒，随意撕边，细和纸胶带，路边快照、咖啡、植物、旧相机，松散随性排版，小小的手写字，安静温柔，生活碎片，复古胶片，柔和暗角，粗糙纸底，治愈，干净。',
    aiNegative: '高饱和，艳色，夸张图案，厚重涂鸦，密密麻麻，卡通，强对比。',
    theme: {
      background: 'linear-gradient(160deg,#e9eef0,#dbe4de)', paper: '#f7f8f6', ink: '#5b6a68', accent: '#9aab9a',
      radius: 8, border: 14, tilt: 6, texture: 'grain', deco: true,
    },
  },
  {
    id: 'retro-magazine',
    name: '美式复古杂志',
    subtitle: 'Retro Magazine',
    category: '复古',
    desc: '60–70 年代时尚内页，泛黄牛皮纸，焦糖正红宝蓝撞色',
    emoji: '📰',
    color: '#b8542f',
    aiPrompt: '美式复古杂志拼贴海报，复刻 60–70 年代时尚内页，泛黄牛皮纸底色，撕纸毛边，剪贴复古人像、复古广告字母、标语，焦糖、正红、宝蓝撞色，自由奔放排版，旧报纸肌理，网点印刷质感，怀旧时髦，大幅粗体标题，多层剪贴，复古印刷颗粒，都市时尚。',
    aiNegative: '现代荧光色，干净光滑，极简，可爱贴纸，扭曲文字。',
    theme: {
      background: '#e6d5ae', paper: '#f1e3c4', ink: '#231d16', accent: '#b8542f',
      radius: 0, border: 5, tilt: 7, texture: 'newspaper', deco: true,
    },
  },
  {
    id: 'macaron-cream',
    name: '奶油马卡龙',
    subtitle: 'Cream Macaron',
    category: '青春',
    desc: '淡粉奶黄薄荷浅紫渐变，圆润贴纸，软乎乎少女感',
    emoji: '🍬',
    color: '#e39fb2',
    aiPrompt: '奶油马卡龙青春拼贴，柔和马卡龙配色：淡粉、奶黄、薄荷绿、浅紫，柔和渐变，圆润贴纸边框，小蝴蝶结、糖果、小花、星星贴纸，人像、甜品、可爱小物件，轻盈治愈，少女感，软乎乎，低对比柔光，细腻纸张，随性手写，清新活泼。',
    aiNegative: '暗沉，高对比，暗黑，粗硬线条，破旧撕纸。',
    theme: {
      background: 'linear-gradient(140deg,#fce9ee 0%,#fdf5d9 33%,#e6f3e4 66%,#eee7f7 100%)', paper: '#fffafc', ink: '#8a6a75', accent: '#e39fb2',
      radius: 26, border: 9, tilt: 4, texture: 'dot', deco: true,
    },
  },
  {
    id: 'frosted-tech',
    name: '清透 AI 科技磨砂',
    subtitle: 'Frosted Tech',
    category: '科技',
    desc: '半透明磨砂玻璃，冰灰浅青淡蓝，虚实叠加未来感',
    emoji: '🔷',
    color: '#4f9fd6',
    aiPrompt: '清透科技磨砂拼贴，半透明磨砂玻璃质感，冰灰、浅青、淡蓝，朦胧渐变，柔和几何圆环、曲面，细腻磨砂颗粒，虚实叠加，光影轻柔，实拍和虚拟几何融合，干净冷调，未来感，数字幻境，通透，低对比度，极简图形，高级数字拼贴。',
    aiNegative: '刺眼荧光，粗糙噪点，杂乱，厚重阴影，复古旧纸。',
    theme: {
      background: 'linear-gradient(150deg,#e7eef3,#d7e6ee 60%,#e3eef4)', paper: 'rgba(255,255,255,.5)', ink: '#2f4b5e', accent: '#5aa4cf',
      radius: 18, border: 5, tilt: 0, texture: 'glass', deco: true,
    },
  },
  {
    id: 'rice-paper',
    name: '文艺宣纸书香',
    subtitle: 'Rice Paper',
    category: '文艺',
    desc: '宣纸纤维、古籍碎片、毛笔书法、水墨花枝，东方诗意',
    emoji: '📖',
    color: '#9a8f7a',
    aiPrompt: '文艺宣纸书香拼贴，米黄、浅赭石宣纸底色，宣纸纤维纹理，蜡染旧纸，古籍碎片，毛笔书法、古诗、拓片、水墨花枝，火漆印章，边缘自然晕染、轻微灼烧撕裂，东方诗意，书卷气，安静雅致，淡淡的墨色，手账拼贴，温润复古。',
    aiNegative: '高饱和彩色，现代涂鸦，粗大字，卡通贴纸，强烈撞色。',
    theme: {
      background: '#eee6d4', paper: '#faf5e8', ink: '#4f4838', accent: '#9a8f7a',
      radius: 6, border: 11, tilt: 2, texture: 'paper', deco: false,
    },
  },
  {
    id: 'street-graffiti',
    name: '街头极简涂鸦',
    subtitle: 'Street Graffiti',
    category: '潮流',
    desc: '利落粗线条涂鸦，黑荧光撞色，松弛酷感，克制不堆砌',
    emoji: '⚡',
    color: '#3a3a3a',
    aiPrompt: '街头极简潮流涂鸦拼贴，都市街头背景，黑、荧光、高饱和撞色，利落粗线条涂鸦，随性手绘，闪电、星星、小卡通，元素精简，线条干脆，松弛酷感，青年潮流，都市活力，贴纸白边，轻微喷漆质感，不密密麻麻，克制涂鸦，时尚海报。',
    aiNegative: '堆砌繁杂，模糊，褪色，柔和低饱和，复古旧报纸。',
    theme: {
      background: '#e6e6e3', paper: '#ffffff', ink: '#151515', accent: '#2b2b2b',
      radius: 4, border: 7, tilt: 10, texture: 'graffiti', deco: true,
    },
  },
  {
    id: 'calendar-diary',
    name: '时光日历日记',
    subtitle: 'Calendar Diary',
    category: '文艺',
    desc: '方格日历骨架，拍立得邮票便签，温暖私人记录感',
    emoji: '📅',
    color: '#c08a5a',
    aiPrompt: '时光日历日记拼贴，方格日历作为骨架，日期印章、手写日记、拍立得、邮票、复古便签穿插，细碎手写字，邮戳、小贴纸，温暖私人，记录日常小事，手账，时间流动感，柔和暖调，轻微纸张纹理，随性摆放，松弛自然。',
    aiNegative: '强烈撞色，夸张涂鸦，大量粗标题，拥挤杂乱。',
    theme: {
      background: '#f6efe0', paper: '#fffdf5', ink: '#5b4c39', accent: '#c08a5a',
      radius: 6, border: 10, tilt: 3, texture: 'calendar', deco: true,
    },
  },
  {
    id: 'travel-journal',
    name: '旅行复古手账',
    subtitle: 'Travel Journal',
    category: '复古',
    desc: '旧明信片机票地图碎片，牛皮纸撕边，怀旧旅途记忆',
    emoji: '🧳',
    color: '#b07b43',
    aiPrompt: '旅行复古手账拼贴海报，旧明信片、机票、地图碎片、城市风景快照，牛皮纸底色，撕边，复古邮戳，手写旅途文字，自由排布城市建筑、街景，怀旧旅途记忆，票根、贴纸，复古印刷质感，大幅海报，温暖复古，多层剪贴，像旅行纪念册。',
    aiNegative: '冰冷科技感，荧光，极简留白，卡通。',
    theme: {
      background: '#c9a877', paper: '#e7d3ae', ink: '#46331f', accent: '#8a5a33',
      radius: 2, border: 11, tilt: 8, texture: 'paper', deco: true,
    },
  },
  {
    id: 'fresh-green',
    name: '清新绿调手账',
    subtitle: 'Fresh Green',
    category: '青春',
    desc: '鼠尾草绿薄荷绿，绿植嫩叶食物快照，干净治愈',
    emoji: '🌿',
    color: '#6fa87c',
    aiPrompt: '清新绿调生活手账拼贴，主色调鼠尾草绿、薄荷绿、嫩草绿，绿植、嫩叶、食物、日常快照，格纹纸、细胶带，可爱手绘小字，星星花朵贴纸，干净治愈，记录早餐、散步，生活碎片，柔和渐变背景，手账 Plog，清爽温柔。',
    aiNegative: '暗沉，高饱和红橙，复古旧纸，强烈撞色涂鸦。',
    theme: {
      background: 'linear-gradient(150deg,#eaf3e8,#d4e8d6)', paper: '#ffffff', ink: '#33513c', accent: '#6fa87c',
      radius: 14, border: 9, tilt: 5, texture: 'grid', deco: true,
    },
  },
  {
    id: 'four-seasons',
    name: '四季叙事长卷',
    subtitle: 'Four Seasons',
    category: '文艺',
    desc: '春夏秋冬分段横向长卷，流动叙事，仪式感排版',
    emoji: '🌸',
    color: '#c98aa0',
    aiPrompt: '四季叙事手账，横向长卷时间轴拼贴，按春夏秋冬分段，春粉、夏绿、秋橙、冬灰，对应季节照片、落叶、花朵、便签，手写笔记，贴纸，手账，流动叙事，仪式感，松弛排版，柔和自然色调，像一整年的生活记录，参考小红书 Plog，多图组合，细线条手绘装饰。',
    aiNegative: '色彩杂乱，强对比，粗大字，密集爆炸图案。',
    theme: {
      background: 'linear-gradient(180deg,#f9e2e6 0%,#dcefd6 33%,#f6e0c4 66%,#dfe3e6 100%)', paper: '#ffffff', ink: '#5a4a45', accent: '#c98aa0',
      radius: 12, border: 8, tilt: 4, texture: 'grid', deco: true,
    },
  },
  {
    id: 'pop-art',
    name: '波普城市海报',
    subtitle: 'Pop Art City',
    category: '潮流',
    desc: '亮黄大红宝蓝荧光橙，半色调网点，粗黑轮廓，冲击力强',
    emoji: '💥',
    color: '#e5432f',
    aiPrompt: '波普城市拼贴海报，经典波普高对比配色：亮黄、大红、宝蓝、荧光橙，手工撕边剪贴、老杂志拼贴、半色调网点（本戴点）、影印噪点、油墨错位，城市摩天楼、街道、人像，叠加网点、粗黑轮廓、爆炸对话框，夸张有冲击力，活力热烈，复古都市海报，半色调网点，剪贴拼贴，粗体艺术字，大胆色块，时髦张扬。',
    aiNegative: '低饱和，柔和，留白，安静，盐系，褪色胶片。',
    theme: {
      background: '#f7d94b', paper: '#ffffff', ink: '#111111', accent: '#e5432f',
      radius: 0, border: 7, tilt: 8, texture: 'dot', deco: true,
    },
  },
  {
    id: 'retro-montage',
    name: '复古蒙太奇',
    subtitle: 'Retro Montage',
    category: '复古',
    desc: '剪报碎片拼接、撕碎报刊底纹、版画印刷质感，细节满满',
    emoji: '✂️',
    color: '#8c6b4f',
    aiPrompt: '复古纸质蒙太奇拼贴画，collage 剪贴艺术，海报版式，剪切的杂志老照片，撕碎的报刊书页底纹，碎片化拼接，裁剪分离的人物肢体，多元素拼贴叠加，复古印刷噪点，剪报边缘毛边撕裂效果，混合插画与纪实人像，平面构成，高饱和度复古色彩，版画印刷质感，排版丰富，细节满满的拼贴元素，平面二维，无 3D 渲染。',
    aiNegative: '现代平滑，极简留白，3D 渲染，卡通，低细节。',
    theme: {
      background: '#ded0b8', paper: '#f0e6d2', ink: '#2e261c', accent: '#8c6b4f',
      radius: 0, border: 3, tilt: 9, texture: 'newspaper', deco: true,
    },
  },
];

/** 按 id 查找模板，找不到时回退到第一套 */
export const findTemplate = (id: string): CollageTemplate =>
  COLLAGE_TEMPLATES.find((t) => t.id === id) || COLLAGE_TEMPLATES[0];

/** 按照片数量查找布局，找不到时回退到 4 张 */
export const findLayout = (count: number): PhotoLayout =>
  PHOTO_LAYOUTS.find((l) => l.count === count) || PHOTO_LAYOUTS[2];

/** 分类去重列表（弹窗筛选栏使用） */
export const COLLAGE_CATEGORIES: Array<CollageCategory | '全部'> = [
  '全部', '极简', '胶片', '复古', '青春', '科技', '文艺', '潮流',
];
