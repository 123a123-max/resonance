/**
 * 生活拼贴 —— 14 种风格模板配置。
 *
 * 每个风格包含：
 *  - id / name / desc：用于设置条按钮与说明
 *  - image：模板底图（public/assets/collage/ 下的成品 JPG，9:16）
 *  - slots：照片空位坐标数组（基于 900×1600 画布）
 *    每项 { x, y, w, h, angle, shape }
 *      x,y  = 空位中心点
 *      w,h  = 空位尺寸
 *      angle = 倾斜角度（度，正为顺时针）
 *      shape = 蒙版形状：'torn' 撕边 | 'polaroid' 拍立得 | 'rounded' 圆角 | 'frame' 细框 | 'frost' 磨砂玻璃
 *
 * 设计约定（用户强约定）：照片位要大、摆放随意自由。
 * 模板成图由 tools/make_*.py 生成，坐标与脚本中 photos 列表一致。
 */

export type SlotShape = 'torn' | 'polaroid' | 'rounded' | 'frame' | 'frost';

export interface PhotoSlot {
  x: number;
  y: number;
  w: number;
  h: number;
  angle: number;
  shape: SlotShape;
}

export interface TemplateStyle {
  id: string;
  name: string;
  desc: string;
  image: string;
  slots: PhotoSlot[];
}

/** 统一资源前缀，Vite 会原样服务 public 目录 */
const ASSET = '/assets/collage/';

/**
 * 默认的大照片位布局（4 张，随性错落）。
 * 无自定义坐标的风格使用此布局；模板脚本生成时会按同一组坐标出图。
 */
const DEFAULT_SLOTS: PhotoSlot[] = [
  { x: 245, y: 560, w: 340, h: 320, angle: -8, shape: 'torn' },
  { x: 655, y: 700, w: 350, h: 285, angle: 7, shape: 'polaroid' },
  { x: 258, y: 1045, w: 330, h: 330, angle: 6, shape: 'rounded' },
  { x: 660, y: 1135, w: 345, h: 310, angle: -7, shape: 'frame' },
];

/** 14 种风格。id 与模板文件名一一对应。 */
export const TEMPLATE_STYLES: TemplateStyle[] = [
  {
    id: 'ins-minimal',
    name: 'INS极简留白',
    desc: '莫兰迪低饱和 · 大量留白 · 高级哑光',
    image: ASSET + 'template-ins-minimal.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'japanese-salt',
    name: '日系盐系胶片',
    desc: '灰蓝草绿 · 胶片褪色 · 和纸暗角',
    image: ASSET + 'template-japanese-salt.jpg',
    // 不规则手撕纸边：坐标/角度与 DEFAULT_SLOTS 一致，形状统一为撕边
    slots: [
      { x: 245, y: 560, w: 340, h: 320, angle: -8, shape: 'torn' },
      { x: 655, y: 700, w: 350, h: 285, angle: 7, shape: 'torn' },
      { x: 258, y: 1045, w: 330, h: 330, angle: 6, shape: 'torn' },
      { x: 660, y: 1135, w: 345, h: 310, angle: -7, shape: 'torn' },
    ],
  },
  {
    id: 'american-retro',
    name: '美式复古杂志',
    desc: '焦糖正红宝蓝 · 泛黄做旧 · 多层剪贴',
    image: ASSET + 'template-american-retro.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'macaron',
    name: '奶油马卡龙',
    desc: '粉黄薄荷浅紫 · 圆润柔和 · 少女感',
    image: ASSET + 'template-macaron.jpg',
    // 圆润无棱角：坐标/角度与 DEFAULT_SLOTS 一致，形状统一为圆角贴纸
    slots: [
      { x: 245, y: 560, w: 340, h: 320, angle: -8, shape: 'rounded' },
      { x: 655, y: 700, w: 350, h: 285, angle: 7, shape: 'rounded' },
      { x: 258, y: 1045, w: 330, h: 330, angle: 6, shape: 'rounded' },
      { x: 660, y: 1135, w: 345, h: 310, angle: -7, shape: 'rounded' },
    ],
  },
  {
    id: 'tech-frost',
    name: '清透AI科技磨砂',
    desc: '冰灰浅青淡蓝 · 磨砂玻璃 · 虚实叠加',
    image: ASSET + 'template-tech-frost.jpg',
    // 与 tools/make_tech_template.py 中 photos 列表一致
    slots: [
      { x: 245, y: 555, w: 340, h: 320, angle: -9, shape: 'frost' },
      { x: 655, y: 700, w: 355, h: 285, angle: 7, shape: 'frost' },
      { x: 255, y: 1040, w: 330, h: 330, angle: 6, shape: 'frame' },
      { x: 665, y: 1135, w: 350, h: 310, angle: -8, shape: 'frost' },
    ],
  },
  {
    id: 'xuan-paper',
    name: '文艺宣纸书香',
    desc: '米白赭石淡墨 · 宣纸纤维 · 国风书卷',
    image: ASSET + 'template-xuan-paper.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'street-graffiti',
    name: '街头极简涂鸦',
    desc: '黑底荧光撞色 · 利落线条 · 街头潮流',
    image: ASSET + 'template-street-graffiti.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'calendar-diary',
    name: '时光日历日记',
    desc: '暖米浅杏 · 方格日历 · 邮戳便签',
    image: ASSET + 'template-calendar-diary.jpg',
    // 拍立得照片位，错落倾斜；坐标/角度与脚本一致
    slots: [
      { x: 245, y: 520, w: 350, h: 330, angle: -7, shape: 'polaroid' },
      { x: 658, y: 630, w: 340, h: 315, angle: 6, shape: 'polaroid' },
      { x: 252, y: 1035, w: 340, h: 320, angle: 5, shape: 'polaroid' },
      { x: 650, y: 1150, w: 352, h: 325, angle: -6, shape: 'polaroid' },
    ],
  },
  {
    id: 'travel-journal',
    name: '旅行复古手账',
    desc: '牛皮纸暖咖 · 机票地图 · 旅途碎片',
    image: ASSET + 'template-travel-journal.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'forest-green',
    name: '清新绿调手账',
    desc: '鼠尾草薄荷绿 · 植物标本 · 生活Plog',
    image: ASSET + 'template-forest-green.jpg',
    // 与 tools/make_collage_template.py 中 photos 列表一致
    slots: [
      { x: 228, y: 555, w: 345, h: 410, angle: -16, shape: 'torn' },
      { x: 672, y: 520, w: 380, h: 280, angle: 14, shape: 'polaroid' },
      { x: 245, y: 910, w: 365, h: 385, angle: 10, shape: 'rounded' },
      { x: 668, y: 905, w: 350, h: 415, angle: -16, shape: 'frame' },
    ],
  },
  {
    id: 'four-seasons',
    name: '四季叙事长卷',
    desc: '春夏秋冬四段 · 低饱和柔色 · 时间长卷',
    image: ASSET + 'template-four-seasons.jpg',
    // 纵向四段时间轴（左右交错流动叙事），与 make_four_seasons_template.py 一致
    slots: [
      { x: 280, y: 430, w: 340, h: 300, angle: -6, shape: 'polaroid' },
      { x: 620, y: 750, w: 350, h: 285, angle: 5, shape: 'rounded' },
      { x: 280, y: 1075, w: 340, h: 300, angle: -5, shape: 'torn' },
      { x: 620, y: 1400, w: 350, h: 280, angle: 6, shape: 'frame' },
    ],
  },
  {
    id: 'popart-city',
    name: '波普城市海报',
    desc: '亮黄正红宝蓝 · 半色调网点 · 爆炸框',
    image: ASSET + 'template-popart-city.jpg',
    // 与 tools/make_popart_template.py 中 photos 列表一致
    slots: [
      { x: 195, y: 690, w: 290, h: 305, angle: -13, shape: 'torn' },
      { x: 595, y: 895, w: 330, h: 255, angle: 11, shape: 'polaroid' },
      { x: 298, y: 1045, w: 305, h: 325, angle: 9, shape: 'frame' },
      { x: 685, y: 1295, w: 290, h: 310, angle: -12, shape: 'torn' },
    ],
  },
  {
    id: 'vintage-montage',
    name: '复古蒙太奇',
    desc: '高饱和复古 · 剪报毛边 · 平面蒙太奇',
    image: ASSET + 'template-vintage-montage.jpg',
    slots: DEFAULT_SLOTS,
  },
  {
    id: 'minimal-photo',
    name: '极简风格',
    desc: '米白浅灰暖棕 · 整齐网格 · 细白边框',
    image: ASSET + 'template-minimal-photo.jpg',
    // 整齐网格 + 错落大小，角度归零，统一间距；与脚本坐标一致
    slots: [
      { x: 245, y: 510, w: 380, h: 400, angle: 0, shape: 'frame' },
      { x: 655, y: 510, w: 350, h: 365, angle: 0, shape: 'frame' },
      { x: 245, y: 945, w: 350, h: 365, angle: 0, shape: 'frame' },
      { x: 655, y: 945, w: 380, h: 400, angle: 0, shape: 'frame' },
    ],
  },
];

export const findStyle = (id: string): TemplateStyle =>
  TEMPLATE_STYLES.find((s) => s.id === id) || TEMPLATE_STYLES[0];
